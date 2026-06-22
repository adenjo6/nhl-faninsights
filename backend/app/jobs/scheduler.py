"""
APScheduler background jobs for automated data fetching and processing.

Handles:
- Daily schedule checks for upcoming Sharks games
- Staggered post-game data fetching (T+0, T+2h, T+4h, T+12h, T+24h)
- Daily roster synchronization
- Standings updates
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone as pytz_timezone
import logging

from app.config import settings
from app.db.session import SessionLocal
from app.models.game import Game

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = BackgroundScheduler(timezone=settings.TIMEZONE)

# Timezone for scheduling
tz = pytz_timezone(settings.TIMEZONE)

# Per-run caps for the Reddit pipeline. Discovery is cheap (one listing scan per
# game) so its bound is just a safety rail; analysis hits the Claude API per game
# so its bound controls spend.
REDDIT_DISCOVERY_LIMIT = 10
REDDIT_SENTIMENT_LIMIT = 5


def start_scheduler():
    """
    Start the APScheduler background scheduler.

    Call this when the FastAPI app starts.

    MVP: Only checks for completed Sharks games and fetches videos.
    """
    logger.info("Starting APScheduler (MVP mode)...")

    # Job 1: Update game scores from NHL API every hour
    scheduler.add_job(
        func=update_game_scores_job,
        trigger=CronTrigger(minute=0, timezone=tz),  # Every hour on the hour
        id="update_game_scores",
        name="Update Sharks game scores from NHL API",
        replace_existing=True,
    )
    logger.info("✓ Scheduled: Update game scores (hourly)")

    # Job 2: Check for completed Sharks games and fetch videos every hour
    scheduler.add_job(
        func=check_and_fetch_videos_job,
        trigger=CronTrigger(minute=5, timezone=tz),  # 5 min past the hour (after scores update)
        id="check_and_fetch_videos",
        name="Check completed Sharks games and fetch videos",
        replace_existing=True,
    )
    logger.info("✓ Scheduled: Check completed games and fetch videos (hourly)")

    # Job 3: Fetch basic stats (boxscore, scorers) for completed games
    scheduler.add_job(
        func=fetch_basic_stats_job,
        trigger=CronTrigger(minute=10, timezone=tz),  # 10 min past the hour (after videos)
        id="fetch_basic_stats",
        name="Fetch basic stats for completed Sharks games",
        replace_existing=True,
    )
    logger.info("✓ Scheduled: Fetch basic stats (hourly)")

    # Job 4a: Discover the Reddit Post-Game Thread for completed games (Stage 1).
    # Cheap (listing scan only, no Claude); gated on game_date + 2h.
    scheduler.add_job(
        func=discover_reddit_threads_job,
        trigger=CronTrigger(minute=15, timezone=tz),  # 15 min past the hour
        id="discover_reddit_threads",
        name="Discover Reddit Post-Game Threads for Sharks games",
        replace_existing=True,
    )
    logger.info("✓ Scheduled: Discover Reddit threads (hourly)")

    # Job 4b: Analyze sentiment for games with a discovered thread (Stage 2).
    # Uses Claude; gated on thread creation + 3h so comments have accumulated.
    scheduler.add_job(
        func=analyze_reddit_sentiment_job,
        trigger=CronTrigger(minute=20, timezone=tz),  # 20 min past the hour (after discovery)
        id="analyze_reddit_sentiment",
        name="Analyze Reddit sentiment for Sharks games",
        replace_existing=True,
    )
    logger.info("✓ Scheduled: Analyze Reddit sentiment (hourly)")

    # Start the scheduler
    scheduler.start()
    logger.info("🚀 APScheduler started successfully (MVP mode)!")


def shutdown_scheduler():
    """
    Gracefully shutdown the scheduler.

    Call this when the FastAPI app shuts down.
    """
    logger.info("Shutting down APScheduler...")
    scheduler.shutdown(wait=True)
    logger.info("✓ APScheduler shut down")


# ============================================================================
# Job Wrapper Functions (with DB session management)
# ============================================================================

def update_game_scores_job():
    """
    Update Sharks game scores and statuses from the NHL API.

    Runs every hour. Fetches the full season schedule and updates all games.
    """
    db = SessionLocal()
    try:
        logger.info("🏒 Updating Sharks game scores from NHL API...")
        from app.scripts.fetch_season import fetch_sharks_season_games
        total = fetch_sharks_season_games(db)
        logger.info(f"✓ Updated {total} games from NHL API")
    except Exception as e:
        logger.error(f"❌ Error updating game scores: {e}", exc_info=True)
    finally:
        db.close()


def check_and_fetch_videos_job():
    """
    Check for completed Sharks games and fetch YouTube videos.

    Runs every hour. Fetches highlights and Professor Hockey videos independently.
    """
    db = SessionLocal()
    try:
        logger.info("🏒 Checking for completed Sharks games without videos...")

        from app.crud.game import (
            get_games_needing_highlights, get_games_needing_professor_hockey,
            mark_highlights_fetched, mark_professor_hockey_fetched
        )
        from app.services.youtube import search_game_highlights, YouTubeQuotaExceeded
        from app.crud.video import create_video, video_exists

        videos_added = 0
        quota_exceeded = False

        # Fetch highlights for games missing them
        highlight_games = get_games_needing_highlights(db, status="FINAL")
        highlight_games += get_games_needing_highlights(db, status="OFF")

        if highlight_games:
            logger.info(f"✓ Found {len(highlight_games)} games needing highlights")
            for game in highlight_games:
                try:
                    videos = search_game_highlights(
                        away_team=game.away_team,
                        home_team=game.home_team,
                        game_date=game.game_date_utc,
                        max_results=3,
                    )
                    if videos.get('nhl_official'):
                        video_data = videos['nhl_official']
                        if not video_exists(db, game.game_id, video_data['video_id']):
                            create_video(db, {
                                'game_id': game.game_id,
                                'youtube_id': video_data['video_id'],
                                'title': video_data['title'],
                                'channel_name': video_data.get('channel_name', 'NHL'),
                                'thumbnail_url': video_data.get('thumbnail_url'),
                                'video_type': 'nhl_official',
                                'published_at': video_data.get('published_at'),
                            })
                            logger.info(f"    ✓ Added highlight video for {game.game_id}")
                            videos_added += 1
                    # Mark as fetched (playlist matching succeeded without quota issues)
                    mark_highlights_fetched(db, game.game_id)
                except YouTubeQuotaExceeded:
                    logger.warning("⚠️ YouTube API quota exceeded! Stopping highlight fetch.")
                    quota_exceeded = True
                    break
                except Exception as e:
                    logger.error(f"    ❌ Error fetching highlights for {game.game_id}: {e}")

        # Fetch Professor Hockey for games missing them (skip if quota exceeded)
        if not quota_exceeded:
            prof_games = get_games_needing_professor_hockey(db, status="FINAL")
            prof_games += get_games_needing_professor_hockey(db, status="OFF")
        else:
            prof_games = []

        if prof_games:
            logger.info(f"✓ Found {len(prof_games)} games needing Professor Hockey")
            for game in prof_games:
                try:
                    sharks_games_before = db.query(Game).filter(
                        ((Game.away_team == 'SJS') | (Game.home_team == 'SJS')),
                        Game.game_date_utc <= game.game_date_utc
                    ).order_by(Game.game_date_utc).count()

                    videos = search_game_highlights(
                        away_team=game.away_team,
                        home_team=game.home_team,
                        game_date=game.game_date_utc,
                        max_results=3,
                        sharks_game_number=sharks_games_before
                    )
                    if videos.get('professor_hockey'):
                        video_data = videos['professor_hockey']
                        if not video_exists(db, game.game_id, video_data['video_id']):
                            create_video(db, {
                                'game_id': game.game_id,
                                'youtube_id': video_data['video_id'],
                                'title': video_data['title'],
                                'channel_name': video_data.get('channel_name', 'Professor Hockey'),
                                'thumbnail_url': video_data.get('thumbnail_url'),
                                'video_type': 'professor_hockey',
                                'published_at': video_data.get('published_at'),
                            })
                            logger.info(f"    ✓ Added Professor Hockey video for {game.game_id}")
                            videos_added += 1
                        mark_professor_hockey_fetched(db, game.game_id)
                except YouTubeQuotaExceeded:
                    logger.warning("⚠️ YouTube API quota exceeded! Stopping Professor Hockey fetch.")
                    quota_exceeded = True
                    break
                except Exception as e:
                    logger.error(f"    ❌ Error fetching Professor Hockey for {game.game_id}: {e}")

        if not highlight_games and not prof_games:
            logger.info("✓ No games need video processing")

        logger.info(f"✓ Video fetch complete: Added {videos_added} videos"
                     + (" (stopped early: quota exceeded)" if quota_exceeded else ""))

    except Exception as e:
        logger.error(f"❌ Error in video fetch job: {e}", exc_info=True)
    finally:
        db.close()


def fetch_basic_stats_job():
    """
    Fetch boxscore data (scorers, raw stats) for completed games.

    Runs every hour at :10. Finds games with basic_stats_fetched=False
    and calls process_game_immediate() for each.
    """
    db = SessionLocal()
    try:
        logger.info("🏒 Fetching basic stats for completed games...")
        from app.crud.game import get_games_needing_basic_stats
        from app.jobs.game_processor import process_game_immediate

        games = get_games_needing_basic_stats(db, status="FINAL")
        games += get_games_needing_basic_stats(db, status="OFF")

        if not games:
            logger.info("✓ No games need basic stats processing")
            return

        logger.info(f"✓ Found {len(games)} games needing basic stats")
        processed = 0
        for game in games:
            try:
                process_game_immediate(db, game.game_id)
                processed += 1
            except Exception as e:
                logger.error(f"    ❌ Error fetching basic stats for {game.game_id}: {e}")

        logger.info(f"✓ Basic stats fetch complete: processed {processed}/{len(games)} games")

    except Exception as e:
        logger.error(f"❌ Error in basic stats job: {e}", exc_info=True)
    finally:
        db.close()


def discover_reddit_threads_job():
    """
    Stage 1 of the Reddit pipeline: link each completed game to its r/SanJoseSharks
    Post-Game Thread.

    Runs hourly at :15. Cheap — a listing scan per game, no Claude. Gated by
    crud.get_games_needing_thread_discovery (game_date + 2h) so we don't scan
    before AutoMod has posted the PGT. Games whose thread isn't found yet are
    left untouched and retried next run.
    """
    db = SessionLocal()
    try:
        from app.crud.game import (
            get_games_needing_thread_discovery,
            mark_thread_discovered,
        )
        from app.services.reddit import find_post_game_thread

        games = get_games_needing_thread_discovery(db)
        if not games:
            logger.info("✓ No games need Reddit thread discovery")
            return

        logger.info(f"🔎 Discovering Reddit PGTs for {len(games)} game(s)...")
        discovered = 0

        for game in games[:REDDIT_DISCOVERY_LIMIT]:
            try:
                found = find_post_game_thread(
                    away_team=game.away_team,
                    home_team=game.home_team,
                    game_date_utc=game.game_date_utc,
                )
                if not found:
                    logger.info(f"    No PGT found yet for {game.game_id} (will retry next run)")
                    continue

                thread_id, thread_created_at = found
                mark_thread_discovered(db, game.game_id, thread_id, thread_created_at)
                discovered += 1
                logger.info(f"    ✓ Linked PGT {thread_id} to game {game.game_id}")
            except Exception as e:
                logger.error(f"    ❌ Discovery error for {game.game_id}: {e}")

        logger.info(f"✓ Reddit discovery complete: linked {discovered}/{len(games)} game(s)")

    except Exception as e:
        logger.error(f"❌ Error in Reddit discovery job: {e}", exc_info=True)
    finally:
        db.close()


def analyze_reddit_sentiment_job():
    """
    Stage 2 of the Reddit pipeline: pull comments from a discovered thread and run
    Claude sentiment analysis.

    Runs hourly at :20 (after discovery). Gated by crud.get_games_needing_sentiment
    (thread creation + 3h) so comments have had time to accumulate. Capped at
    REDDIT_SENTIMENT_LIMIT games/run to control Claude spend.

    analyze_game_sentiment returns a 'quiet' stub for a genuinely empty thread
    (saved and marked done) and None on a Claude API failure (left for retry).
    """
    db = SessionLocal()
    try:
        from app.crud.game import get_games_needing_sentiment, save_reddit_sentiment
        from app.services.reddit import fetch_thread_comments
        from app.services.sentiment import analyze_game_sentiment

        games = get_games_needing_sentiment(db)
        if not games:
            logger.info("✓ No games need Reddit sentiment analysis")
            return

        logger.info(f"🏒 Analyzing Reddit sentiment for {len(games)} game(s)...")
        processed = 0

        for game in games[:REDDIT_SENTIMENT_LIMIT]:
            try:
                comments = fetch_thread_comments(game.reddit_thread_id)

                game_context = (
                    f"{game.away_team} {game.away_score} - {game.home_team} {game.home_score}, "
                    f"{game.game_date_utc.strftime('%B %d, %Y')}"
                )

                sentiment = analyze_game_sentiment(
                    comments=comments,
                    game_context=game_context,
                )

                if sentiment is None:
                    logger.warning(f"    Sentiment analysis failed for {game.game_id} (will retry next run)")
                    continue

                sentiment["thread_url"] = (
                    f"https://www.reddit.com/r/{settings.REDDIT_SUBREDDIT}/comments/{game.reddit_thread_id}"
                )
                sentiment["comment_count"] = len(comments)
                save_reddit_sentiment(db, game.game_id, sentiment)
                processed += 1
                logger.info(f"    ✓ Sentiment analyzed for {game.game_id}: {sentiment.get('fan_mood', '?')}")
            except Exception as e:
                logger.error(f"    ❌ Sentiment error for {game.game_id}: {e}")

        logger.info(f"✓ Reddit sentiment complete: analyzed {processed}/{len(games)} game(s)")

    except Exception as e:
        logger.error(f"❌ Error in Reddit sentiment job: {e}", exc_info=True)
    finally:
        db.close()


# ============================================================================
# Utility Functions
# ============================================================================

def get_scheduled_jobs():
    """Get list of all scheduled jobs (for admin dashboard)."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        })
    return jobs