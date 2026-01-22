from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Index, DateTime
from datetime import datetime
from app.db.session import Base


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)

    # Player reference
    player_id = Column(Integer, ForeignKey("player_info.nhl_player_id", ondelete="CASCADE"), nullable=False, index=True)
    player_name = Column(String, nullable=False)

    # Game where milestone occurred or is being tracked
    game_id = Column(Integer, ForeignKey("games.game_id", ondelete="CASCADE"), nullable=False, index=True)

    # Milestone details
    milestone_type = Column(String, nullable=False)  # "goal", "assist", "point", "game_played", etc.
    milestone_value = Column(Integer, nullable=False)  # e.g., 100, 500, 1000
    description = Column(String, nullable=False)  # "100th career goal", "500th career point"

    # Status
    achieved = Column(Boolean, default=False)  # True if achieved in this game, False if approaching
    current_value = Column(Integer, nullable=True)  # e.g., player at 498 points, milestone is 500

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        # Index for fetching milestones for a game
        Index("ix_milestones_game", "game_id"),
        # Index for player milestone history
        Index("ix_milestones_player", "player_id", "milestone_type"),
    )