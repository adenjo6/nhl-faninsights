"""
CRUD operations for Game model.
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import Optional
from app.models.game import Game
from app.models.video import Video
from app.services.redis_cache import cache


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

    # Only show finished games. COMPLETE is the terminal status set once a game
    # has been fully processed (videos + recap); without it, processed games
    # would silently drop off the list.
    query = query.filter(Game.status.in_(['FINAL', 'OFF', 'COMPLETE']))

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


def get_games_needing_basic_stats(db: Session, status: str = "FINAL") -> list[Game]:
    """Get games that need basic stats (boxscore, scorers) processing."""
    return db.query(Game).filter(
        Game.status == status,
        Game.basic_stats_fetched == False
    ).all()


def get_games_needing_highlights(db: Session, status: str = "FINAL") -> list[Game]:
    """Get games that need highlight video processing."""
    return db.query(Game).filter(
        Game.status == status,
        Game.highlights_fetched == False
    ).all()


def get_games_needing_professor_hockey(db: Session, status: str = "FINAL") -> list[Game]:
    """Get games that need Professor Hockey video processing."""
    return db.query(Game).filter(
        Game.status == status,
        Game.professor_hockey_fetched == False
    ).all()


def mark_highlights_fetched(db: Session, game_id: int) -> bool:
    """Mark that highlight videos have been fetched for a game."""
    game = get_game_by_id(db, game_id)
    if not game:
        return False

    game.highlights_fetched = True
    game.status_updated_at = datetime.utcnow()
    db.commit()
    return True


def mark_professor_hockey_fetched(db: Session, game_id: int) -> bool:
    """Mark that Professor Hockey video has been fetched for a game."""
    game = get_game_by_id(db, game_id)
    if not game:
        return False

    game.professor_hockey_fetched = True
    game.status_updated_at = datetime.utcnow()
    db.commit()
    return True


def get_games_needing_reddit(db: Session, status: str = "FINAL") -> list[Game]:
    """Get completed games that need Reddit sentiment analysis."""
    return db.query(Game).filter(
        Game.status == status,
        Game.reddit_fetched == False
    ).all()


def get_games_needing_thread_discovery(db: Session) -> list[Game]:
    """Games that are FINAL/OFF, have no thread_id yet, and where the
    PGT-creation window has opened (game_date_utc + 2h <= now)."""
    cutoff = datetime.utcnow() - timedelta(hours=2)
    return (
        db.query(Game)
        .filter(
            Game.status.in_(["FINAL", "OFF"]),
            Game.reddit_thread_id.is_(None),
            Game.game_date_utc <= cutoff,
        )
        .order_by(Game.game_date_utc.desc())
        .all()
    )


def get_games_needing_sentiment(db: Session) -> list[Game]:
    """Games where discovery succeeded, sentiment hasn't run, and the
    thread is at least 3 hours old (comments have had time to accumulate)."""
    cutoff = datetime.utcnow() - timedelta(hours=3)
    return (
        db.query(Game)
        .filter(
            Game.status.in_(["FINAL", "OFF"]),
            Game.reddit_thread_id.isnot(None),
            Game.reddit_fetched.is_(False),
            Game.reddit_thread_created_at <= cutoff,
        )
        .order_by(Game.game_date_utc.desc())
        .all()
    )


def mark_thread_discovered(
    db: Session,
    game_id: int,
    thread_id: str,
    thread_created_at: datetime,
) -> bool:
    """Record a discovered Reddit Post-Game Thread for a game."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        return False
    game.reddit_thread_id = thread_id
    game.reddit_thread_created_at = thread_created_at
    game.status_updated_at = datetime.utcnow()
    db.commit()
    return True


def save_reddit_sentiment(db: Session, game_id: int, sentiment: dict) -> bool:
    """Save Reddit sentiment analysis results, mark fetched, invalidate caches."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        return False

    now = datetime.utcnow()
    game.reddit_sentiment = sentiment
    game.reddit_fetched = True
    game.reddit_analyzed_at = now
    game.status_updated_at = now
    db.commit()

    cache.invalidate(f"game:{game_id}")
    cache.invalidate_pattern("games:*")
    return True
