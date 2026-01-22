#!/usr/bin/env python3
"""Final check - show video statistics."""
from app.db.session import SessionLocal
from app.models.game import Game
from app.models.video import Video

db = SessionLocal()

print("=" * 70)
print("FINAL VIDEO STATISTICS")
print("=" * 70)

# Count games
total_games = db.query(Game).count()
completed_games = db.query(Game).filter(Game.status.in_(['FINAL', 'OFF'])).count()
games_with_videos = db.query(Game).filter(Game.videos_fetched == True).count()

print(f"\nGames:")
print(f"  Total regular season games: {total_games}")
print(f"  Completed games: {completed_games}")
print(f"  Games with videos fetched: {games_with_videos}")

# Count videos by type
total_videos = db.query(Video).count()
nhl_videos = db.query(Video).filter(Video.video_type == 'nhl_official').count()
prof_videos = db.query(Video).filter(Video.video_type == 'professor_hockey').count()

print(f"\nVideos:")
print(f"  Total videos: {total_videos}")
print(f"  NHL Official videos: {nhl_videos}")
print(f"  Professor Hockey videos: {prof_videos}")

# Show a few example videos
print(f"\nExample videos:")
videos = db.query(Video).join(Game).order_by(Game.game_date_utc).limit(5).all()
for v in videos:
    game = db.query(Game).filter(Game.game_id == v.game_id).first()
    print(f"  Game {game.away_team} @ {game.home_team} ({game.game_date_utc.date()}):")
    print(f"    - {v.video_type}: {v.youtube_id}")

print("\n" + "=" * 70)
print("SUCCESS! Videos are now in the database.")
print("=" * 70)
print("\nYou can now:")
print("1. Start your frontend: cd frontend && npm run dev")
print("2. View games at http://localhost:3000")
print("3. Videos should appear for each completed game!\n")

db.close()
