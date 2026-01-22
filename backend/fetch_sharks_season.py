#!/usr/bin/env python3
"""
Fetch all San Jose Sharks games for the 2025-26 season and populate the database.
Also fetches YouTube videos (NHL Official + Professor Hockey) for each completed game.
"""
import sys
import requests
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.youtube import search_game_highlights
from app.models.game import Game
from app.models.video import Video
from app.crud.game import get_game_by_id, create_game, update_game
from app.crud.video import create_video, video_exists


def fetch_sharks_season_games(db: Session, season: str = "20252026"):
    """
    Fetch all Sharks games for a season and store in database.
    Uses official NHL API: https://api-web.nhle.com/

    Args:
        db: Database session
        season: Season in format YYYYYYYY (e.g., "20252026" for 2025-26)
    """
    print(f"🏒 Fetching Sharks schedule for {season[:4]}-{season[4:6]} season...")

    # Use official NHL Web API
    url = f"https://api-web.nhle.com/v1/club-schedule-season/SJS/{season}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        games_data = data.get('games', [])
        print(f"✓ Found {len(games_data)} games")

        games_created = 0
        games_updated = 0

        for game_data in games_data:
            # Skip preseason games (gameType=1), only process regular season (gameType=2)
            if game_data.get('gameType') != 2:
                continue

            game_id = game_data.get('id')

            # Parse game date
            game_date_str = game_data.get('startTimeUTC')
            if game_date_str:
                game_date = datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
            else:
                # Fallback to gameDate
                game_date = datetime.strptime(game_data.get('gameDate', ''), '%Y-%m-%d')

            # Check if game already exists
            existing_game = get_game_by_id(db, game_id)

            if existing_game:
                # Update existing game
                update_data = {
                    'status': game_data.get('gameState', 'SCHEDULED'),
                    'away_score': game_data.get('awayTeam', {}).get('score') or 0,  # Default to 0 for future games
                    'home_score': game_data.get('homeTeam', {}).get('score') or 0,  # Default to 0 for future games
                }
                update_game(db, game_id, update_data)
                games_updated += 1
            else:
                # Create new game
                new_game = {
                    'game_id': game_id,
                    'game_date_utc': game_date,
                    'away_team': game_data.get('awayTeam', {}).get('abbrev', 'UNK'),
                    'home_team': game_data.get('homeTeam', {}).get('abbrev', 'UNK'),
                    'away_score': game_data.get('awayTeam', {}).get('score') or 0,  # Default to 0 for future games
                    'home_score': game_data.get('homeTeam', {}).get('score') or 0,  # Default to 0 for future games
                    'status': game_data.get('gameState', 'SCHEDULED'),
                    'scorers': [],
                    'raw': game_data,
                }
                create_game(db, new_game)
                games_created += 1

        print(f"✓ Created {games_created} new games")
        print(f"✓ Updated {games_updated} existing games")

        return games_created + games_updated

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching schedule from NHL API: {e}")
        import traceback
        traceback.print_exc()
        return 0
    except Exception as e:
        print(f"❌ Error processing schedule: {e}")
        import traceback
        traceback.print_exc()
        return 0


def fetch_videos_for_completed_games(db: Session, limit: int = 10):
    """
    Fetch YouTube videos for completed Sharks games that don't have videos yet.

    Args:
        db: Database session
        limit: Maximum number of games to process
    """
    print(f"\n🎥 Fetching videos for completed games...")

    # Get completed games without videos
    games = db.query(Game).filter(
        Game.status.in_(['FINAL', 'OFF']),
        Game.videos_fetched == False
    ).order_by(Game.game_date_utc.desc()).limit(limit).all()

    if not games:
        print("✓ No games need video processing")
        return 0

    print(f"✓ Found {len(games)} games needing videos")

    videos_found = 0

    for idx, game in enumerate(games):
        print(f"\n  Processing game {game.game_id}: {game.away_team} @ {game.home_team}")

        try:
            # Calculate Sharks game number for the season
            # Get all Sharks games up to this date, ordered by date
            sharks_games_before = db.query(Game).filter(
                ((Game.away_team == 'SJS') | (Game.home_team == 'SJS')),
                Game.game_date_utc <= game.game_date_utc,
                Game.status.in_(['FINAL', 'OFF', 'LIVE', 'SCHEDULED', 'FUT'])
            ).order_by(Game.game_date_utc).all()

            sharks_game_number = len(sharks_games_before)

            # Search for videos
            videos = search_game_highlights(
                away_team=game.away_team,
                home_team=game.home_team,
                game_date=game.game_date_utc,
                max_results=3,
                sharks_game_number=sharks_game_number
            )

            print(f"    Sharks game #{sharks_game_number} of season")

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
                    print(f"    ✓ Added NHL Official video: {video_data['video_id']}")
                    videos_found += 1

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
                    print(f"    ✓ Added Professor Hockey video: {video_data['video_id']}")
                    videos_found += 1

            # Mark game as videos fetched
            game.videos_fetched = True
            db.commit()

        except Exception as e:
            print(f"    ❌ Error fetching videos: {e}")
            continue

    print(f"\n✓ Found and stored {videos_found} videos")
    return videos_found


def main():
    """Main function."""
    print("=" * 70)
    print("🦈 San Jose Sharks - Season Data Fetcher")
    print("=" * 70)

    db = SessionLocal()

    try:
        # Fetch 2025-26 season games
        total_games = fetch_sharks_season_games(db, season="20252026")

        # Fetch videos for completed games
        if total_games > 0:
            videos_found = fetch_videos_for_completed_games(db, limit=20)

        print("\n" + "=" * 70)
        print("✅ Season data fetch complete!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
