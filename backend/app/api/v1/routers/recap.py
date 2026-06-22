from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.v1.deps import get_db
from app.crud import game as game_crud
from app.services.nhl import fetch_boxscore, fetch_play_by_play, extract_goal_details
from app.services.claude import generate_game_recap

router = APIRouter()


@router.get("/{game_id}")
def get_recap(game_id: int, db: Session = Depends(get_db)):
    """
    Get AI-generated recap for a game.
    If no recap exists yet, generates one using Claude.
    """
    game = game_crud.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # If game isn't finished, can't generate recap
    if game.status not in ("FINAL", "OFF"):
        raise HTTPException(status_code=400, detail="Game not yet completed")

    # Return existing recap if already generated
    if game.recap_generated and game.recap_text:
        return {
            "game_id": game.game_id,
            "summary_line": game.summary_line,
            "recap_text": game.recap_text,
            "next_game_storyline": game.next_game_storyline,
        }

    # Fetch boxscore and play-by-play from NHL API
    try:
        boxscore = fetch_boxscore(game_id)
        pbp = fetch_play_by_play(game_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch NHL data: {e}")

    # Extract goal details from play-by-play
    goals = extract_goal_details(pbp)

    # Extract top performers from boxscore
    top_performers = _extract_top_performers(boxscore)

    # Build game data dict for Claude
    game_data = {
        "away_team": game.away_team,
        "home_team": game.home_team,
        "away_score": game.away_score,
        "home_score": game.home_score,
        "game_date": game.game_date_utc.strftime("%B %d, %Y") if game.game_date_utc else "Unknown",
    }

    # Generate recap with Claude
    result = generate_game_recap(game_data, goals, top_performers)

    # Save to database
    game.recap_text = result["recap_text"]
    game.summary_line = result["summary_line"]
    game.next_game_storyline = result.get("next_game_storyline")
    game.recap_generated = True
    db.commit()

    return {
        "game_id": game.game_id,
        "summary_line": result["summary_line"],
        "recap_text": result["recap_text"],
        "next_game_storyline": result.get("next_game_storyline"),
    }


def _extract_top_performers(boxscore: dict) -> list[dict]:
    """Extract top performers from boxscore data."""
    performers = []
    stats = boxscore.get("playerByGameStats", {})

    for side in ("awayTeam", "homeTeam"):
        # Skaters
        for role in ("forwards", "defense"):
            for p in stats.get(side, {}).get(role, []):
                goals = p.get("goals", 0)
                assists = p.get("assists", 0)
                points = goals + assists
                if points > 0:
                    performers.append({
                        "name": p.get("name", {}).get("default", "Unknown"),
                        "position": "F" if role == "forwards" else "D",
                        "goals": goals,
                        "assists": assists,
                    })

        # Goalies
        for p in stats.get(side, {}).get("goalies", []):
            saves = p.get("saves", 0)
            if saves > 0:
                performers.append({
                    "name": p.get("name", {}).get("default", "Unknown"),
                    "position": "G",
                    "saves": saves,
                    "save_percentage": p.get("savePctg"),
                })

    # Sort by points (skaters) then saves (goalies)
    performers.sort(key=lambda x: (x.get("goals", 0) + x.get("assists", 0), x.get("saves", 0)), reverse=True)
    return performers[:5]
