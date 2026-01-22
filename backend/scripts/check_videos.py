#!/usr/bin/env python3
"""
Quick script to check if videos were fetched and stored in the database.
"""
from app.db.session import SessionLocal
from app.models.game import Game
from app.models.video import Video

db = SessionLocal()

try:
    # Check how many completed games we have
    completed_games = db.query(Game).filter(Game.status.in_(['FINAL', 'OFF'])).count()
    print(f'✓ Completed games (FINAL or OFF): {completed_games}')

    # Check how many videos we have
    total_videos = db.query(Video).count()
    print(f'✓ Total videos in database: {total_videos}')

    # Check games with videos_fetched flag
    games_with_videos_fetched = db.query(Game).filter(Game.videos_fetched == True).count()
    print(f'✓ Games marked as videos_fetched: {games_with_videos_fetched}')

    # Check games that need video fetching
    games_need_videos = db.query(Game).filter(
        Game.status.in_(['FINAL', 'OFF']),
        Game.videos_fetched == False
    ).count()
    print(f'✓ Games that need video fetching: {games_need_videos}')

    # Sample a completed game and check for videos
    sample_game = db.query(Game).filter(Game.status.in_(['FINAL', 'OFF'])).first()
    if sample_game:
        print(f'\n📺 Sample game: {sample_game.game_id} ({sample_game.away_team} @ {sample_game.home_team})')
        print(f'   Status: {sample_game.status}')
        print(f'   Videos fetched flag: {sample_game.videos_fetched}')
        videos = db.query(Video).filter(Video.game_id == sample_game.game_id).all()
        print(f'   Videos for this game: {len(videos)}')
        for v in videos:
            print(f'     - {v.video_type}: {v.youtube_id} ("{v.title}")')
    else:
        print('\n❌ No completed games found')

    print('\n' + '='*70)
    if total_videos == 0 and games_need_videos > 0:
        print('⚠️  NO VIDEOS FOUND - The fetch_videos_for_completed_games() function')
        print('   likely did not run or encountered errors.')
        print(f'\n   Run: python3 fetch_sharks_season.py')
        print('   This will fetch videos for all {games_need_videos} completed games.')
    elif total_videos > 0:
        print(f'✅ SUCCESS - {total_videos} videos found in database!')
    print('='*70)

finally:
    db.close()
