from pydantic import BaseModel

class Recap(BaseModel):
    game_id:   int
    away_team: str
    home_team: str
    away_score: int
    home_score: int
    scorers: list[str]

    class Config:
        orm_mode = True
