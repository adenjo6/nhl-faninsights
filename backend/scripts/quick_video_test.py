#!/usr/bin/env python3
"""Quick test: Fetch videos for ONE game to verify it works"""
from app.db.session import SessionLocal
from app.services.youtube import search_game_highlights
from app.models.game import Game
from app.crud.video import create_video, video_exists

db = SessionLocal()

# Get ONE completed game
game = db.query(Game).filter(
    Game.status.in_(['FINAL', 'OFF']),
    Game.videos_fetched == False
).order_by(Game.game_date_utc.desc()).first()

if not game:
    print("❌ No games found needing videos")
    db.close()
    exit(1)

print(f"Testing video fetch for game: {game.away_team} @ {game.home_team}")
print(f"Game ID: {game.game_id}")
print(f"Date: {game.game_date_utc}")

# Calculate game number
sharks_game_num = db.query(Game).filter(
    ((Game.away_team == 'SJS') | (Game.home_team == 'SJS')),
    Game.game_date_utc <= game.game_date_utc
).order_by(Game.game_date_utc).count()

print(f"Sharks game #{sharks_game_num} of season\n")

# Search for videos
print("Searching YouTube...")
videos = search_game_highlights(
    away_team=game.away_team,
    home_team=game.home_team,
    game_date=game.game_date_utc,
    sharks_game_number=sharks_game_num,
    max_results=3
)

videos_added = 0

# Save NHL video
if videos.get('nhl_official'):
    print("\n✅ Found NHL Official video!")
    video_data = videos['nhl_official']
    print(f"   Title: {video_data['title']}")
    print(f"   Video ID: {video_data['video_id']}")

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
        videos_added += 1
        print("   ✓ Saved to database")
else:
    print("\n❌ No NHL Official video found")

# Save Professor Hockey video
if videos.get('professor_hockey'):
    print("\n✅ Found Professor Hockey video!")
    video_data = videos['professor_hockey']
    print(f"   Title: {video_data['title']}")
    print(f"   Video ID: {video_data['video_id']}")

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
        videos_added += 1
        print("   ✓ Saved to database")
else:
    print("\n❌ No Professor Hockey video found")

# Mark as fetched
game.videos_fetched = True
db.commit()

print(f"\n{'='*60}")
print(f"✅ Test complete! Added {videos_added} videos")
print(f"{'='*60}")

db.close()
