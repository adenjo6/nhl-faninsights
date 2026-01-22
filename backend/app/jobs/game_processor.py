"""Game data processing jobs - handles staggered fetching and processing."""

from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
import logging

from app.config import settings
from app.models import Game, Video
from app import services
from app.services.youtube import search_game_highlights, get_video_details
from app.services.claude import generate_game_recap

logger = logging.getLogger(__name__)


def check_upcoming_games(db: Session) -> int:
    """
    Check NHL API for upcoming Sharks games and create/update Game records.

    Returns: Number of games scheduled for processing
    """
    from app.scheduler import schedule_post_game_processing

    # Fetch Sharks schedule from today forward
    today = date.today()
    games = services.fetch_team_schedule(settings.SHARKS_TEAM_ID, start_date=today)

    games_scheduled = 0

    for game_data in games:
        game_id = game_data["id"]
        game_status = game_data["gameState"]  # "FUT", "LIVE", "FINAL", "OFF"
        game_date = datetime.fromisoformat(game_data["gameDate"].replace("Z", "+00:00"))

        # Check if game exists in DB
        game = db.query(Game).filter(Game.game_id == game_id).first()

        if not game:
            # Create new game record
            game = Game(
                game_id=game_id,
                game_date_utc=game_date,
                status="SCHEDULED" if game_status == "FUT" else game_status,
                away_team=game_data["awayTeam"]["abbrev"],
                home_team=game_data["homeTeam"]["abbrev"],
            )
            db.add(game)
            db.commit()
            logger.info(f"Created new game record: {game_id} - {game.away_team} @ {game.home_team}")

        # If game just finished and not yet processed, schedule processing
        if game_status in ["FINAL", "OFF"] and game.status != "ARCHIVED":
            if not game.basic_stats_fetched:
                # Game finished but not processed yet
                # Estimate end time (games usually ~2.5 hours after start)
                estimated_end = game_date + timedelta(hours=2, minutes=30)

                # If game ended in the past, start processing immediately
                if estimated_end < datetime.now(game_date.tzinfo):
                    estimated_end = datetime.now(game_date.tzinfo)

                schedule_post_game_processing(game_id, estimated_end)
                games_scheduled += 1

                # Update game status
                game.status = "FINAL"
                game.status_updated_at = datetime.utcnow()
                db.commit()

    return games_scheduled


def process_game_immediate(db: Session, game_id: int):
    """
    T+0: Fetch basic game data immediately after game ends.

    - Final score
    - Goal scorers
    - Basic team stats
    - Store raw boxscore JSON
    """
    logger.info(f"[T+0] Fetching basic stats for game {game_id}")

    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        logger.error(f"Game {game_id} not found in database")
        return

    try:
        # Fetch boxscore
        boxscore = services.fetch_boxscore(game_id)

        # Extract basic info
        game.away_team = boxscore["awayTeam"]["abbrev"]
        game.home_team = boxscore["homeTeam"]["abbrev"]
        game.away_score = boxscore["awayTeam"]["score"]
        game.home_score = boxscore["homeTeam"]["score"]

        # Extract goal scorers
        scorers = []
        stats = boxscore.get("playerByGameStats", {})
        for side in ("awayTeam", "homeTeam"):
            for role in ("forwards", "defense"):
                for player in stats.get(side, {}).get(role, []):
                    if player.get("goals", 0) > 0:
                        name = player.get("name", {}).get("default")
                        if name:
                            scorers.append(name)

        game.scorers = scorers
        game.raw = boxscore  # Store full JSON

        # Mark as fetched
        game.basic_stats_fetched = True
        game.status = "FINAL"
        game.status_updated_at = datetime.utcnow()

        db.commit()
        logger.info(f"✓ [T+0] Game {game_id}: {game.away_team} {game.away_score} @ {game.home_team} {game.home_score}")

    except Exception as e:
        logger.error(f"Error fetching basic stats for game {game_id}: {e}")
        raise


def process_game_detailed_stats(db: Session, game_id: int):
    """
    T+30min: Fetch detailed stats and play-by-play.

    - Play-by-play data with goal times
    - Individual player stats
    - Save to players table
    """
    logger.info(f"[T+30min] Fetching detailed stats for game {game_id}")

    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        logger.error(f"Game {game_id} not found")
        return

    try:
        # Fetch play-by-play
        pbp = services.fetch_play_by_play(game_id)

        # Extract goal details
        goals = services.extract_goal_details(pbp)

        # Update game record with structured goal data
        if game.raw:
            game.raw["goals"] = goals
        else:
            game.raw = {"goals": goals}

        db.commit()
        logger.info(f"✓ [T+30min] Game {game_id}: Stored {len(goals)} goal details")

    except Exception as e:
        logger.error(f"Error fetching detailed stats for game {game_id}: {e}")
        # Non-critical, continue


def process_game_reddit(db: Session, game_id: int):
    """
    T+2h: Fetch Reddit posts and comments (placeholder for now).

    This will use your existing Reddit integration from the frontend.
    For now, we just mark it as fetched.
    """
    logger.info(f"[T+2h] Fetching Reddit data for game {game_id}")

    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        return

    # TODO: Implement Reddit fetching and sentiment analysis
    # For MVP, the frontend will handle Reddit fetching client-side

    game.reddit_fetched = True
    db.commit()
    logger.info(f"✓ [T+2h] Game {game_id}: Reddit marked as fetched")


def process_game_videos_and_recap(db: Session, game_id: int):
    """
    T+4h: THE MAIN PROCESSING JOB

    - Search YouTube for highlight videos
    - Generate Claude AI recap
    - Mark game as COMPLETE
    """
    logger.info(f"[T+4h] MAIN PROCESSING for game {game_id}")

    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        logger.error(f"Game {game_id} not found")
        return

    try:
        # Step 1: Search for YouTube videos
        logger.info(f"[T+4h] Searching for videos...")

        # Calculate Sharks game number for Professor Hockey search
        sharks_games_before = db.query(Game).filter(
            ((Game.away_team == 'SJS') | (Game.home_team == 'SJS')),
            Game.game_date_utc <= game.game_date_utc
        ).order_by(Game.game_date_utc).count()

        video_results = search_game_highlights(
            away_team=game.away_team,
            home_team=game.home_team,
            game_date=game.game_date_utc,
            max_results=3,
            sharks_game_number=sharks_games_before
        )

        # Save NHL official video
        if video_results.get("nhl_official"):
            video_data = video_results["nhl_official"]
            video_id = video_data["video_id"]
            if not db.query(Video).filter_by(game_id=game_id, youtube_id=video_id).first():
                video = Video(
                    game_id=game_id,
                    youtube_id=video_id,
                    title=video_data["title"],
                    channel_name=video_data.get("channel_name", "NHL"),
                    thumbnail_url=video_data.get("thumbnail_url"),
                    video_type="nhl_official",
                    published_at=video_data.get("published_at"),
                )
                db.add(video)
                logger.info(f"✓ Saved NHL official video: {video_id}")

        # Save Professor Hockey video
        if video_results.get("professor_hockey"):
            video_data = video_results["professor_hockey"]
            video_id = video_data["video_id"]
            if not db.query(Video).filter_by(game_id=game_id, youtube_id=video_id).first():
                video = Video(
                    game_id=game_id,
                    youtube_id=video_id,
                    title=video_data["title"],
                    channel_name=video_data.get("channel_name", "Professor Hockey"),
                    thumbnail_url=video_data.get("thumbnail_url"),
                    video_type="professor_hockey",
                    published_at=video_data.get("published_at"),
                )
                db.add(video)
                logger.info(f"✓ Saved Professor Hockey video: {video_id}")

        game.videos_fetched = True

        # Step 2: Generate Claude recap
        logger.info(f"[T+4h] Generating AI recap...")

        # Prepare data for Claude
        goals = game.raw.get("goals", []) if game.raw else []
        top_performers = []  # TODO: Extract from boxscore

        recap_result = generate_game_recap(
            game_data={
                "away_team": game.away_team,
                "home_team": game.home_team,
                "away_score": game.away_score,
                "home_score": game.home_score,
                "game_date": game.game_date_utc.strftime("%B %d, %Y"),
            },
            goal_details=goals,
            top_performers=top_performers,
        )

        game.summary_line = recap_result["summary_line"]
        game.recap_text = recap_result["recap_text"]
        game.next_game_storyline = recap_result.get("next_game_storyline")
        game.recap_generated = True

        # Mark as COMPLETE
        game.status = "COMPLETE"
        game.completed_at = datetime.utcnow()
        game.status_updated_at = datetime.utcnow()

        db.commit()
        logger.info(f"✓ [T+4h] Game {game_id} MAIN PROCESSING COMPLETE")
        logger.info(f"  Summary: {game.summary_line}")

    except Exception as e:
        logger.error(f"Error in main processing for game {game_id}: {e}")
        raise  # Re-raise to trigger retry


def process_game_quotes(db: Session, game_id: int):
    """
    T+12h: Fetch post-game quotes (placeholder for MVP).

    In Phase 2, this will scrape team website / media for quotes.
    """
    logger.info(f"[T+12h] Fetching quotes for game {game_id}")

    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        return

    # TODO: Implement quote scraping in Phase 2
    game.quotes_fetched = True
    db.commit()
    logger.info(f"✓ [T+12h] Game {game_id}: Quotes marked as fetched")


def archive_game(db: Session, game_id: int):
    """
    T+24h: Final check and archive game.

    - Verify all data is present
    - Retry any missing videos
    - Mark as ARCHIVED
    """
    logger.info(f"[T+24h] Archiving game {game_id}")

    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        return

    # Check for missing videos and retry once
    if not game.videos_fetched:
        logger.info(f"Videos not fetched, retrying...")
        try:
            process_game_videos_and_recap(db, game_id)
        except:
            logger.warning(f"Failed to fetch videos on archive retry")

    # Mark as archived
    game.status = "ARCHIVED"
    game.archived_at = datetime.utcnow()
    game.status_updated_at = datetime.utcnow()

    db.commit()
    logger.info(f"✓ [T+24h] Game {game_id} ARCHIVED")