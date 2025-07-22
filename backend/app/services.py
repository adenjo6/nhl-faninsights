import requests

def fetch_boxscore(game_id: int) -> dict:
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore"
    response = requests.get(url)
    response.raise_for_status()
    return response.json() 