"""
Game API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.api.v1.deps import get_db
from app.crud import game as game_crud
from app.crud import video as video_crud
from app.schemas.game import GameSummary, GameDetail, GameCreate, GameUpdate
from app.services.redis_cache import cache


router = APIRouter()


@router.get("/recent", response_model=List[GameSummary])
def get_recent_games(
    limit: int = Query(10, ge=1, le=100),
    team: Optional[str] = Query(None, description="Filter by team abbreviation (e.g., SJS)"),
    db: Session = Depends(get_db)
):
    """
    Get recent completed games.

    - **limit**: Number of games to return (1-100, default 10)
    - **team**: Optional team filter (e.g., "SJS")

    Only returns games with status FINAL or OFF (completed games).
    Uses Redis caching for improved performance.
    """
    # Try cache first
    cache_key = f"games:recent:limit={limit}:team={team}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    # Cache miss - query database
    games = game_crud.get_recent_games(db, limit=limit, team=team)

    # Transform to summary format with video availability
    summaries = []
    for game in games:
        # Check if videos exist
        nhl_video = video_crud.get_video_by_type(db, game.game_id, "nhl_official")
        prof_video = video_crud.get_video_by_type(db, game.game_id, "professor_hockey")

        summaries.append(GameSummary(
            game_id=game.game_id,
            game_date=game.game_date_utc.isoformat(),
            away_team=game.away_team,
            home_team=game.home_team,
            away_score=game.away_score,
            home_score=game.home_score,
            status=game.status,
            has_videos=bool(nhl_video or prof_video)
        ))

    # Cache the result for 5 minutes (300 seconds)
    cache.set(cache_key, summaries, ttl=300)

    return summaries


@router.get("/{game_id}", response_model=GameDetail)
def get_game(game_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific game.

    Includes:
    - Basic game info (teams, scores, date)
    - Videos (NHL official + Professor Hockey)
    - AI-generated recap (if available)

    Uses Redis caching for improved performance.
    """
    # Try cache first
    cache_key = f"game:{game_id}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    # Cache miss - query database
    game = game_crud.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get video IDs
    nhl_video = video_crud.get_video_by_type(db, game_id, "nhl_official")
    prof_video = video_crud.get_video_by_type(db, game_id, "professor_hockey")

    game_detail = GameDetail(
        game_id=game.game_id,
        game_date_utc=game.game_date_utc,
        status=game.status,
        away_team=game.away_team,
        home_team=game.home_team,
        away_score=game.away_score,
        home_score=game.home_score,
        scorers=game.scorers,
        recap_text=game.recap_text,
        summary_line=game.summary_line,
        nhl_video_id=nhl_video.youtube_id if nhl_video else None,
        professor_hockey_video_id=prof_video.youtube_id if prof_video else None,
        videos=[
            {
                "id": v.id,
                "youtube_id": v.youtube_id,
                "title": v.title,
                "video_type": v.video_type,
                "channel_name": v.channel_name,
                "thumbnail_url": v.thumbnail_url
            }
            for v in game.videos
        ]
    )

    # Cache the result for 5 minutes (300 seconds)
    cache.set(cache_key, game_detail, ttl=300)

    return game_detail


@router.post("", response_model=GameDetail, status_code=201)
def create_game(game_data: GameCreate, db: Session = Depends(get_db)):
    """
    Create a new game (admin only in production).
    """
    # Check if game already exists
    existing = game_crud.get_game_by_id(db, game_data.game_id)
    if existing:
        raise HTTPException(status_code=400, detail="Game already exists")

    game = game_crud.create_game(db, game_data.dict())

    # Invalidate game list caches since we added a new game
    cache.invalidate_pattern("games:*")

    return get_game(game.game_id, db)


@router.patch("/{game_id}", response_model=GameDetail)
def update_game(
    game_id: int,
    update_data: GameUpdate,
    db: Session = Depends(get_db)
):
    """
    Update game information (admin only in production).
    """
    game = game_crud.update_game(db, game_id, update_data.dict(exclude_unset=True))
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Invalidate cache after update (fixes stale data bug!)
    cache.invalidate(f"game:{game_id}")  # Clear specific game cache
    cache.invalidate_pattern("games:*")  # Clear all game list caches

    return get_game(game_id, db)


@router.delete("/{game_id}", status_code=204)
def delete_game(game_id: int, db: Session = Depends(get_db)):
    """
    Delete a game (admin only in production).
    """
    success = game_crud.delete_game(db, game_id)
    if not success:
        raise HTTPException(status_code=404, detail="Game not found")

    # Invalidate cache after deletion
    cache.invalidate(f"game:{game_id}")  # Clear specific game cache
    cache.invalidate_pattern("games:*")  # Clear all game list caches

    return None
