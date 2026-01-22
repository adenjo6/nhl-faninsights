"""
CRUD operations for Game model.
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from datetime import datetime
from typing import Optional
from app.models.game import Game
from app.models.video import Video


def get_game_by_id(db: Session, game_id: int) -> Optional[Game]:
    """Get a single game by ID with all related data."""
    return db.query(Game).options(
        joinedload(Game.videos),
        joinedload(Game.comments),
        joinedload(Game.quotes)
    ).filter(Game.game_id == game_id).first()


def get_recent_games(db: Session, limit: int = 10, team: Optional[str] = None) -> list[Game]:
    """Get recent completed games, optionally filtered by team."""
    query = db.query(Game).options(joinedload(Game.videos))

    # Only show completed games (FINAL or OFF status)
    query = query.filter(Game.status.in_(['FINAL', 'OFF']))

    if team:
        query = query.filter(
            (Game.home_team == team) | (Game.away_team == team)
        )

    return query.order_by(desc(Game.game_date_utc)).limit(limit).all()


def create_game(db: Session, game_data: dict) -> Game:
    """Create a new game."""
    game = Game(**game_data)
    db.add(game)
    db.commit()
    db.refresh(game)
    return game


def update_game(db: Session, game_id: int, update_data: dict) -> Optional[Game]:
    """Update a game."""
    game = get_game_by_id(db, game_id)
    if not game:
        return None

    for key, value in update_data.items():
        if hasattr(game, key):
            setattr(game, key, value)

    game.status_updated_at = datetime.utcnow()
    db.commit()
    db.refresh(game)
    return game


def delete_game(db: Session, game_id: int) -> bool:
    """Delete a game."""
    game = get_game_by_id(db, game_id)
    if not game:
        return False

    db.delete(game)
    db.commit()
    return True


def get_games_needing_processing(db: Session, status: str = "FINAL") -> list[Game]:
    """Get games that need video/data processing."""
    return db.query(Game).filter(
        Game.status == status,
        Game.videos_fetched == False
    ).all()


def mark_videos_fetched(db: Session, game_id: int) -> bool:
    """Mark that videos have been fetched for a game."""
    game = get_game_by_id(db, game_id)
    if not game:
        return False

    game.videos_fetched = True
    game.status_updated_at = datetime.utcnow()
    db.commit()
    return True
