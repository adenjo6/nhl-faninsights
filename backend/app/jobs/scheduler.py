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
        from app.services.youtube import search_game_highlights
        from app.crud.video import create_video, video_exists

        videos_added = 0

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
                    # Always mark as fetched so we don't keep retrying
                    mark_highlights_fetched(db, game.game_id)
                except Exception as e:
                    logger.error(f"    ❌ Error fetching highlights for {game.game_id}: {e}")

        # Fetch Professor Hockey for games missing them
        prof_games = get_games_needing_professor_hockey(db, status="FINAL")
        prof_games += get_games_needing_professor_hockey(db, status="OFF")

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
                        # Only mark fetched if we found it
                        mark_professor_hockey_fetched(db, game.game_id)
                except Exception as e:
                    logger.error(f"    ❌ Error fetching Professor Hockey for {game.game_id}: {e}")

        if not highlight_games and not prof_games:
            logger.info("✓ No games need video processing")

        logger.info(f"✓ Video fetch complete: Added {videos_added} videos")

    except Exception as e:
        logger.error(f"❌ Error in video fetch job: {e}", exc_info=True)
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