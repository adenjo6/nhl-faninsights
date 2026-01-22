#!/usr/bin/env python3
"""Check video fetch progress in real-time."""
import time
from app.db.session import SessionLocal
from app.models.video import Video
from app.models.game import Game

while True:
    db = SessionLocal()

    # Quick stats
    total_games = db.query(Game).filter(Game.status.in_(['FINAL', 'OFF'])).count()
    games_with_videos = db.query(Game).filter(Game.videos_fetched == True).count()
    total_videos = db.query(Video).count()

    print(f'\rProgress: {games_with_videos}/{total_games} games | {total_videos} videos', end='', flush=True)

    db.close()

    if games_with_videos >= total_games:
        print('\n\n✅ ALL GAMES HAVE VIDEOS!')
        break

    time.sleep(5)
