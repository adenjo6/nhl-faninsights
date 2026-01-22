from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.recap import Recap
from app.crud.recap import get_cached, create_recap, list_all
from app.services import fetch_boxscore, transform_boxscore
from app.api.v1.deps import get_db

router = APIRouter()

@router.get("", response_model=Recap)
def read_recap(game_id: int, db: Session = Depends(get_db)):
    record = get_cached(db, game_id)
    if record:
        return record

    raw_boxscore_json = fetch_boxscore(game_id)
    recap = transform_boxscore(raw_boxscore_json,game_id)

    return create_recap(db, game_id, recap, raw_boxscore_json)

@router.get("/all", response_model = list[Recap])
def get_all_recaps(db: Session = Depends(get_db)):
    records = list_all(db)
    return records
