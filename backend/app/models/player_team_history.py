from sqlalchemy import Column, Integer, String, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class PlayerInfo(Base):
    """Master player information table"""
    __tablename__ = "player_info"

    # NHL API player ID (stable across career)
    nhl_player_id = Column(Integer, primary_key=True, index=True)

    # Basic info
    name = Column(String, nullable=False)
    position = Column(String, nullable=True)  # F, D, G or more specific
    jersey_number = Column(Integer, nullable=True)
    birthdate = Column(Date, nullable=True)

    # URLs
    nhl_profile_url = Column(String, nullable=True)
    headshot_url = Column(String, nullable=True)

    # Relationships
    team_history = relationship("PlayerTeamHistory", back_populates="player")


class PlayerTeamHistory(Base):
    """Track player team changes over time"""
    __tablename__ = "player_team_history"

    id = Column(Integer, primary_key=True, index=True)

    # Player reference
    player_id = Column(Integer, ForeignKey("player_info.nhl_player_id", ondelete="CASCADE"), nullable=False, index=True)

    # Team info (use abbreviations: "SJS", "SJB", etc.)
    team_id = Column(String, nullable=False, index=True)
    team_name = Column(String, nullable=False)

    # Time period
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # NULL = currently on this team

    # Relationship
    player = relationship("PlayerInfo", back_populates="team_history")

    __table_args__ = (
        # Index for fast "current roster" queries
        Index("ix_current_roster", "team_id", "end_date"),
        # Index for player history lookups
        Index("ix_player_history", "player_id", "start_date"),
    )