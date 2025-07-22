from fastapi import FastAPI
from pydantic import BaseModel
from .services import fetch_boxscore

app = FastAPI()

class Recap(BaseModel):
    awayTeam: str
    homeTeam: str
    awayScore: int
    homeScore: int
    scorers: list[str]

@app.get("/api/recap", response_model=Recap)
async def get_recap(game_id: int):
    raw_boxscore_json = fetch_boxscore(game_id)

    away_team = raw_boxscore_json["awayTeam"]["commonName"]["default"]
    home_team = raw_boxscore_json["homeTeam"]["commonName"]["default"]
    away_score = raw_boxscore_json["awayTeam"]["score"]
    home_score = raw_boxscore_json["homeTeam"]["score"]

    scorers: list[str] = []
    stats = raw_boxscore_json.get("playerByGameStats", {})
    for side in ("awayTeam", "homeTeam"):
        team_stats = stats.get(side, {})
        for position in ("forwards", "defense", "goalies"):
            for player in team_stats.get(position, []):
                if player.get("goals",0) > 0:
                    #extract this player
                    name = player.get("name", {}).get("default")
                    if name:
                        scorers.append(name)

    return {
        "awayTeam":  away_team,
        "homeTeam":  home_team,
        "awayScore": away_score,
        "homeScore": home_score,
        "scorers":   scorers,
    }


