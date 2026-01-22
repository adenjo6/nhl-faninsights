"""
Pydantic schemas for Game API.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class VideoResponse(BaseModel):
    """Video embedded in game response."""
    id: int
    youtube_id: str
    title: str
    video_type: str
    channel_name: Optional[str] = None
    thumbnail_url: Optional[str] = None

    class Config:
        from_attributes = True


class GameSummary(BaseModel):
    """Summary for game list view."""
    game_id: int
    game_date: str
    away_team: str
    home_team: str
    away_score: Optional[int] = None
    home_score: Optional[int] = None
    status: str
    has_videos: bool

    class Config:
        from_attributes = True


class GameDetail(BaseModel):
    """Detailed game information."""
    game_id: int
    game_date_utc: datetime
    status: str
    away_team: str
    home_team: str
    away_score: Optional[int] = None
    home_score: Optional[int] = None
    scorers: Optional[List] = None
    recap_text: Optional[str] = None
    summary_line: Optional[str] = None

    # Video URLs
    nhl_video_id: Optional[str] = None
    professor_hockey_video_id: Optional[str] = None

    # All videos
    videos: List[VideoResponse] = []

    class Config:
        from_attributes = True


class GameCreate(BaseModel):
    """Create a new game."""
    game_id: int
    game_date_utc: datetime
    away_team: str
    home_team: str
    away_score: Optional[int] = None
    home_score: Optional[int] = None
    status: str = "SCHEDULED"


class GameUpdate(BaseModel):
    """Update game fields."""
    away_score: Optional[int] = None
    home_score: Optional[int] = None
    status: Optional[str] = None
    recap_text: Optional[str] = None
    summary_line: Optional[str] = None
