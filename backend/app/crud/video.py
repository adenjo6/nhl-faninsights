"""
CRUD operations for Video model.
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.models.video import Video


def create_video(db: Session, video_data: dict) -> Video:
    """Create a new video."""
    video = Video(**video_data)
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


def get_videos_by_game(db: Session, game_id: int) -> List[Video]:
    """Get all videos for a specific game."""
    return db.query(Video).filter(Video.game_id == game_id).all()


def get_video_by_type(db: Session, game_id: int, video_type: str) -> Optional[Video]:
    """Get a specific type of video for a game."""
    return db.query(Video).filter(
        Video.game_id == game_id,
        Video.video_type == video_type
    ).first()


def video_exists(db: Session, game_id: int, youtube_id: str) -> bool:
    """Check if a video already exists."""
    return db.query(Video).filter(
        Video.game_id == game_id,
        Video.youtube_id == youtube_id
    ).first() is not None


def delete_video(db: Session, video_id: int) -> bool:
    """Delete a video."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        return False

    db.delete(video)
    db.commit()
    return True
