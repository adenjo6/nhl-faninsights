from sqlalchemy.orm import Session
from app.models.game import Game
from app.schemas.recap import Recap

def get_cached(db: Session, game_id: int) -> Game | None:
    return db.query(Game).filter(Game.game_id == game_id).first()

def create_recap(db: Session, game_id: int, recap: Recap, raw: dict) -> Game:
    db_obj = Game(
        game_id=game_id,
        away_team=recap.away_team,
        home_team=recap.home_team,
        away_score=recap.away_score,
        home_score=recap.home_score,
        scorers=recap.scorers,
        raw=raw,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def list_all(db: Session) -> list[Game]:
    return db.query(Game).all()

