#!/usr/bin/env python3
"""Delete only preseason games from database."""
from app.db.session import SessionLocal
from app.models.game import Game
from app.models.video import Video

db = SessionLocal()

print("=" * 70)
print("🗑️  DELETING PRESEASON GAMES ONLY")
print("=" * 70)

# Find preseason games
preseason_games = []
for game in db.query(Game).all():
    if game.raw and game.raw.get('gameType') == 1:
        preseason_games.append(game)

print(f"\nFound {len(preseason_games)} preseason games:")
for game in preseason_games:
    print(f"  - {game.game_id}: {game.away_team} @ {game.home_team} on {game.game_date_utc.date()}")

if not preseason_games:
    print("\n✅ No preseason games to delete!")
    db.close()
    exit(0)

# Delete videos for these games first
game_ids = [g.game_id for g in preseason_games]
video_count = db.query(Video).filter(Video.game_id.in_(game_ids)).count()
if video_count > 0:
    db.query(Video).filter(Video.game_id.in_(game_ids)).delete(synchronize_session=False)
    print(f"\n✓ Deleted {video_count} videos associated with preseason games")

# Delete the games
for game in preseason_games:
    db.delete(game)

db.commit()

print(f"\n✅ Deleted {len(preseason_games)} preseason games")
print("=" * 70)

# Show remaining games
remaining = db.query(Game).count()
completed = db.query(Game).filter(Game.status.in_(['FINAL', 'OFF'])).count()

print(f"\nRemaining games: {remaining}")
print(f"Completed games: {completed}")
print("\n✅ Database cleaned - only regular season games remain!\n")

db.close()
