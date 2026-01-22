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

    # Job 1: Check for completed Sharks games and fetch videos every hour
    scheduler.add_job(
        func=check_and_fetch_videos_job,
        trigger=CronTrigger(minute=0, timezone=tz),  # Every hour on the hour
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

def check_and_fetch_videos_job():
    """
    MVP: Check for completed Sharks games and fetch YouTube videos.

    Runs every hour. Looks for games with status FINAL/OFF that don't have videos yet.
    """
    db = SessionLocal()
    try:
        logger.info("🏒 Checking for completed Sharks games without videos...")

        # Import here to avoid circular dependency
        from app.crud.game import get_games_needing_processing
        from app.services.youtube import search_game_highlights
        from app.crud.video import create_video, video_exists

        # Get games that are completed but don't have videos
        games = get_games_needing_processing(db, status="FINAL")
        games += get_games_needing_processing(db, status="OFF")

        if not games:
            logger.info("✓ No games need video processing")
            return

        logger.info(f"✓ Found {len(games)} completed games needing videos")

        videos_added = 0
        for game in games:
            try:
                logger.info(f"  Processing game {game.game_id}: {game.away_team} @ {game.home_team}")

                # Calculate Sharks game number for season
                sharks_games_before = db.query(Game).filter(
                    ((Game.away_team == 'SJS') | (Game.home_team == 'SJS')),
                    Game.game_date_utc <= game.game_date_utc
                ).order_by(Game.game_date_utc).count()

                # Search for videos
                videos = search_game_highlights(
                    away_team=game.away_team,
                    home_team=game.home_team,
                    game_date=game.game_date_utc,
                    max_results=3,
                    sharks_game_number=sharks_games_before
                )

                # Store NHL Official video
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
                        logger.info(f"    ✓ Added NHL Official video")
                        videos_added += 1

                # Store Professor Hockey video
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
                        logger.info(f"    ✓ Added Professor Hockey video")
                        videos_added += 1

                # Mark game as videos fetched
                from app.crud.game import mark_videos_fetched
                mark_videos_fetched(db, game.game_id)

            except Exception as e:
                logger.error(f"    ❌ Error processing game {game.game_id}: {e}")
                continue

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