from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, UniqueConstraint
from datetime import datetime
from app.db.session import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)

    # Game relationship
    game_id = Column(Integer, ForeignKey("games.game_id", ondelete="CASCADE"), nullable=False, index=True)

    # YouTube info
    youtube_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    channel_name = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)

    # Video type: "nhl_official", "professor_hockey", "goal_highlight", "other"
    video_type = Column(String, nullable=False, index=True)

    # Optional: specific goal/moment this video relates to
    goal_time = Column(String, nullable=True)  # e.g., "5:23" for period 1
    scorer_name = Column(String, nullable=True)

    # Timestamps
    published_at = Column(DateTime, nullable=True)  # YouTube publish date
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        # Prevent duplicate videos for same game
        UniqueConstraint("game_id", "youtube_id", name="uq_game_video"),
        # Index for fetching videos by type
        Index("ix_videos_game_type", "game_id", "video_type"),
    )