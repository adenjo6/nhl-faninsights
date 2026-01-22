"""
Reddit discussion API endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from app.services.reddit import get_game_reddit_discussion


router = APIRouter()


@router.get("/game/{game_id}")
async def get_game_reddit(
    away_team: str = Query(..., description="Away team abbreviation"),
    home_team: str = Query(..., description="Home team abbreviation"),
    game_date: str = Query(..., description="Game date (ISO format)"),
    limit: int = Query(50, ge=1, le=200, description="Number of comments to fetch")
):
    """
    Get Reddit discussion for a specific game.

    Searches r/SanJoseSharks for the game thread and returns top comments.

    Returns:
    - thread_url: Link to Reddit game thread
    - comments: List of top comments with scores
    - comment_count: Number of comments
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
