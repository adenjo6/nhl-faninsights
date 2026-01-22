from sqlalchemy import Column, Integer, String, JSON, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.db.session import Base

class Player(Base):
    __tablename__ = "players"

    # Local row id (auto-increment)
    id = Column(Integer, primary_key=True, index=True)

    # Stable NHL player id for joining across games
    nhl_player_id = Column(Integer, nullable=False, index=True)

    name = Column(String, nullable=False)
    team = Column(String, nullable=False, index=True)
    position = Column(String, nullable=True)
    stats = Column(JSON, nullable=True)  # per-game statistics blob

    game_id = Column(Integer, ForeignKey("games.game_id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationship back to Game
    game = relationship("Game", back_populates="players")

    __table_args__ = (
        # Ensure one row per player per game
        UniqueConstraint("game_id", "nhl_player_id", name="uq_player_per_game"),
        # Common lookup by (game, team)
        Index("ix_players_game_team", "game_id", "team"),
    )