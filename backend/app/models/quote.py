from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index
from datetime import datetime
from app.db.session import Base


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)

    # Game relationship
    game_id = Column(Integer, ForeignKey("games.game_id", ondelete="CASCADE"), nullable=False, index=True)

    # Quote content
    text = Column(Text, nullable=False)

    # Speaker info
    speaker_name = Column(String, nullable=False)  # "David Quinn", "Logan Couture", etc.
    speaker_role = Column(String, nullable=True)   # "Head Coach", "Captain", "Forward", etc.
    speaker_image_url = Column(String, nullable=True)

    # Source
    source = Column(String, nullable=True)  # "Post-game interview", "Pregame presser", etc.
    source_url = Column(String, nullable=True)

    __table_args__ = (
        # Index for fetching all quotes for a game
        Index("ix_quotes_game", "game_id"),
    )