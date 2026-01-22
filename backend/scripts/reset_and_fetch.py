#!/usr/bin/env python3
"""
Reset database and fetch ONLY 2025-26 regular season games.
"""
import sys
import requests
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.game import Game
from app.models.video import Video
from app.crud.game import create_game

print("="*70)
print("🗑️  CLEARING DATABASE AND FETCHING 2025-26 SEASON")
print("="*70)

db = SessionLocal()

try:
    # Step 1: Delete all videos
    print("\n1. Deleting all videos...")
    video_count = db.query(Video).count()
    db.query(Video).delete()
    db.commit()
    print(f"   ✓ Deleted {video_count} videos")

    # Step 2: Delete all games
    print("\n2. Deleting all games...")
    game_count = db.query(Game).count()
    db.query(Game).delete()
    db.commit()
    print(f"   ✓ Deleted {game_count} games")

    # Step 3: Fetch ONLY regular season games (gameType=2)
    print("\n3. Fetching 2025-26 regular season games...")
    url = "https://api-web.nhle.com/v1/club-schedule-season/SJS/20252026"

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    games_data = data.get('games', [])
    print(f"   ✓ Found {len(games_data)} total games from API")

    # Filter for ONLY regular season (gameType = 2)
    regular_season_games = [g for g in games_data if g.get('gameType') == 2]
    print(f"   ✓ Filtered to {len(regular_season_games)} regular season games")

    games_created = 0

    for game_data in regular_season_games:
        game_id = game_data.get('id')

        # Parse game date
        game_date_str = game_data.get('startTimeUTC')
        if game_date_str:
            game_date = datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
        else:
            game_date = datetime.strptime(game_data.get('gameDate', ''), '%Y-%m-%d')

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

    print(f"   ✓ Created {games_created} regular season games")

    # Step 4: Show stats
    print("\n" + "="*70)
    print("DATABASE STATS:")
    print("="*70)

    total_games = db.query(Game).count()
    completed_games = db.query(Game).filter(Game.status.in_(['FINAL', 'OFF'])).count()
    future_games = db.query(Game).filter(Game.status.in_(['FUT', 'SCHEDULED'])).count()

    print(f"Total games: {total_games}")
    print(f"Completed games: {completed_games}")
    print(f"Upcoming games: {future_games}")

    # Show first and last game
    first_game = db.query(Game).order_by(Game.game_date_utc).first()
    last_game = db.query(Game).order_by(Game.game_date_utc.desc()).first()

    if first_game:
        print(f"\nFirst game: {first_game.away_team} @ {first_game.home_team} on {first_game.game_date_utc.strftime('%Y-%m-%d')}")
    if last_game:
        print(f"Last game:  {last_game.away_team} @ {last_game.home_team} on {last_game.game_date_utc.strftime('%Y-%m-%d')}")

    print("\n" + "="*70)
    print("✅ DATABASE RESET COMPLETE!")
    print("="*70)
    print("\nNow run: python3 fetch_sharks_season.py")
    print("This will fetch videos for all completed games.\n")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
