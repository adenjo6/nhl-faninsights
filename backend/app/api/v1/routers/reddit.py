"""
Reddit discussion API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from app.api.v1.deps import get_db
from app.crud import game as game_crud
from app.services.reddit import get_game_reddit_discussion


router = APIRouter()


@router.get("/game/{game_id}/comments")
async def get_game_reddit_comments(
    game_id: int,
    limit: int = Query(50, ge=1, le=200, description="Number of comments to fetch"),
    db: Session = Depends(get_db)
):
    """
    Get Reddit comments for a game. Looks up game details from DB automatically.
    """
    game = game_crud.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    result = await get_game_reddit_discussion(
        away_team=game.away_team,
        home_team=game.home_team,
        game_date=game.game_date_utc,
        limit=limit
    )

    if not result.get("thread_id"):
        raise HTTPException(
            status_code=404,
            detail="No Reddit game thread found for this game"
        )

    return {
        "thread_url": result.get("thread_url"),
        "comment_count": result.get("comment_count", 0),
        "comments": result.get("comments", []),
    }


@router.get("/game/{game_id}")
async def get_game_reddit(
    game_id: int,
    away_team: str = Query(..., description="Away team abbreviation"),
    home_team: str = Query(..., description="Home team abbreviation"),
    game_date: str = Query(..., description="Game date (ISO format)"),
    limit: int = Query(50, ge=1, le=200, description="Number of comments to fetch")
):
    """
    Get Reddit discussion for a specific game (legacy endpoint with query params).
    """
    try:
        game_datetime = datetime.fromisoformat(game_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DD)")

    result = await get_game_reddit_discussion(
        away_team=away_team,
        home_team=home_team,
        game_date=game_datetime,
        limit=limit
    )

    if not result["thread_id"]:
        raise HTTPException(
            status_code=404,
            detail="No Reddit game thread found for this game"
        )

    return result
