"""NHL API service - fetches data from NHL Stats API."""

import requests
from datetime import datetime, date
from app.schemas.recap import Recap


def fetch_team_schedule(team_abbr: str, start_date: date | None = None) -> list[dict]:
    """
    Fetch schedule for a team starting from a specific date.
    If start_date is None, fetches current season schedule.

    Returns list of game objects with: game_id, date, opponent, status, etc.
    """
    # Determine season (e.g., 20242025 for 2024-25 season)
    if start_date:
        year = start_date.year if start_date.month >= 10 else start_date.year - 1
    else:
        today = date.today()
        year = today.year if today.month >= 10 else today.year - 1

    season = f"{year}{year + 1}"

    url = f"https://api-web.nhle.com/v1/club-schedule-season/{team_abbr}/{season}"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    games = data.get("games", [])

    # Filter by start_date if provided
    if start_date:
        games = [
            g for g in games
            if datetime.fromisoformat(g["gameDate"].replace("Z", "+00:00")).date() >= start_date
        ]

    return games


def fetch_boxscore(game_id: int) -> dict:
    """Fetch detailed boxscore for a specific game."""
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def fetch_play_by_play(game_id: int) -> dict:
    """Fetch play-by-play data including goal times and assists."""
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def fetch_current_roster(team_abbr: str) -> dict:
    """Fetch current roster for a team."""
    url = f"https://api-web.nhle.com/v1/roster/{team_abbr}/current"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def fetch_player_stats(player_id: int) -> dict:
    """Fetch player profile and career stats."""
    url = f"https://api-web.nhle.com/v1/player/{player_id}/landing"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def fetch_standings() -> dict:
    """Fetch current NHL standings."""
    url = "https://api-web.nhle.com/v1/standings/now"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def transform_boxscore(raw: dict, game_id: int) -> Recap:
    """Transform raw boxscore JSON into Recap schema."""
    away = raw["awayTeam"]["commonName"]["default"]
    home = raw["homeTeam"]["commonName"]["default"]
    away_score = raw["awayTeam"]["score"]
    home_score = raw["homeTeam"]["score"]

    scorers: list[str] = []
    stats = raw.get("playerByGameStats", {})
    for side in ("awayTeam", "homeTeam"):
        for role in ("forwards", "defense", "goalies"):
            for p in stats.get(side, {}).get(role, []):
                if p.get("goals", 0) > 0:
                    name = p.get("name", {}).get("default")
                    if name:
                        scorers.append(name)

    return Recap(
        game_id=game_id,
        away_team=away,
        home_team=home,
        away_score=away_score,
        home_score=home_score,
        scorers=scorers,
    )


def extract_goal_details(play_by_play: dict) -> list[dict]:
    """
    Extract goal information from play-by-play data.

    Returns list of dicts with: period, time, scorer, assists, team, etc.
    """
    goals = []

    for play in play_by_play.get("plays", []):
        if play.get("typeDescKey") == "goal":
            details = play.get("details", {})
            goals.append({
                "period": play.get("periodDescriptor", {}).get("number"),
                "time": play.get("timeInPeriod"),
                "scorer": details.get("scoringPlayerName"),
                "scorer_id": details.get("scoringPlayerId"),
                "assists": [
                    details.get("assist1PlayerName"),
                    details.get("assist2PlayerName")
                ],
                "team": play.get("teamAbbrev"),
                "strength": details.get("strength"),  # "ev", "pp", "sh"
                "empty_net": details.get("emptyNet", False),
            })

    return goals
