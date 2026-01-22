from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)

    # Content
    text = Column(Text, nullable=False)

    # Relationships
    game_id = Column(Integer, ForeignKey("games.game_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.clerk_id", ondelete="CASCADE"), nullable=False, index=True)

    # Threading support (for nested replies)
    parent_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)

    # Moderation
    is_deleted = Column(Boolean, default=False)
    is_flagged = Column(Boolean, default=False)
    deleted_by = Column(String, ForeignKey("users.clerk_id"), nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    parent = relationship("Comment", remote_side=[id], backref="replies")

    __table_args__ = (
        # Index for fetching game comments ordered by time
        Index("ix_comments_game_created", "game_id", "created_at"),
        # Index for fetching flagged comments for moderation
        Index("ix_comments_flagged", "is_flagged", "created_at"),
    )