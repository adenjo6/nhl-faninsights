#!/usr/bin/env python3
"""
Test the video fetching and database storage process.
"""
from app.db.session import SessionLocal
from app.models.game import Game
from app.models.video import Video
from app.services.youtube import search_game_highlights
from app.crud.video import create_video, video_exists
from datetime import datetime

print("="*70)
print("Video Fetch & Storage Test")
print("="*70)

db = SessionLocal()

try:
    # Step 1: Find a completed game
    print("\n1. Finding a completed game...")
    completed_game = db.query(Game).filter(
        Game.status.in_(['FINAL', 'OFF']),
        Game.videos_fetched == False
    ).order_by(Game.game_date_utc.desc()).first()

    if not completed_game:
        print("   ❌ No completed games found that need video fetching")

        # Check if ALL games have videos_fetched = True
        total_completed = db.query(Game).filter(
            Game.status.in_(['FINAL', 'OFF'])
        ).count()
        already_fetched = db.query(Game).filter(
            Game.status.in_(['FINAL', 'OFF']),
            Game.videos_fetched == True
        ).count()

        print(f"\n   Total completed games: {total_completed}")
        print(f"   Already fetched: {already_fetched}")
        print(f"   Need fetching: {total_completed - already_fetched}")

        if already_fetched > 0:
            print("\n   Some games are marked as fetched. Checking one...")
            sample = db.query(Game).filter(
                Game.status.in_(['FINAL', 'OFF']),
                Game.videos_fetched == True
            ).first()
            if sample:
                videos = db.query(Video).filter(Video.game_id == sample.game_id).all()
                print(f"   Game {sample.game_id}: {len(videos)} videos in DB")
        exit(0)

    print(f"   ✓ Found game: {completed_game.game_id}")
    print(f"     {completed_game.away_team} @ {completed_game.home_team}")
    print(f"     Date: {completed_game.game_date_utc}")
    print(f"     Status: {completed_game.status}")

    # Step 2: Search for videos
    print("\n2. Searching YouTube for videos...")
    videos = search_game_highlights(
        away_team=completed_game.away_team,
        home_team=completed_game.home_team,
        game_date=completed_game.game_date_utc,
        max_results=3
    )

    print(f"   NHL Official: {'✓ Found' if videos.get('nhl_official') else '✗ Not found'}")
    print(f"   Professor Hockey: {'✓ Found' if videos.get('professor_hockey') else '✗ Not found'}")

    # Step 3: Try to store NHL video
    if videos.get('nhl_official'):
        print("\n3. Storing NHL Official video...")
        video_data = videos['nhl_official']

        print(f"   Video data received:")
        for key, value in video_data.items():
            print(f"     {key}: {value}")

        # Check if already exists
        if video_exists(db, completed_game.game_id, video_data['video_id']):
            print(f"   ⚠️  Video already exists in database")
        else:
            try:
                # Prepare data for create_video
                video_create_data = {
                    'game_id': completed_game.game_id,
                    'youtube_id': video_data['video_id'],
                    'title': video_data['title'],
                    'channel_name': video_data.get('channel_name', 'NHL'),
                    'thumbnail_url': video_data.get('thumbnail_url'),
                    'video_type': 'nhl_official',
                    'published_at': video_data.get('published_at'),
                }

                print(f"\n   Attempting to create video with data:")
                for key, value in video_create_data.items():
                    print(f"     {key}: {value}")

                video = create_video(db, video_create_data)
                print(f"\n   ✅ Video created successfully!")
                print(f"     Video DB ID: {video.id}")
                print(f"     YouTube ID: {video.youtube_id}")

                # Verify it's in the database
                check = db.query(Video).filter(Video.id == video.id).first()
                if check:
                    print(f"   ✅ Verified: Video exists in database")
                else:
                    print(f"   ❌ ERROR: Video not found after creation!")

            except Exception as e:
                print(f"   ❌ Error creating video: {e}")
                import traceback
                traceback.print_exc()
    else:
        print("\n3. No NHL Official video found - skipping storage test")

    # Step 4: Check video count
    print("\n4. Checking database video count...")
    total_videos = db.query(Video).count()
    game_videos = db.query(Video).filter(Video.game_id == completed_game.game_id).count()
    print(f"   Total videos in database: {total_videos}")
    print(f"   Videos for this game: {game_videos}")

except Exception as e:
    print(f"\n❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

print("\n" + "="*70)
print("Test complete!")
print("="*70)
