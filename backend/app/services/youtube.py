"""YouTube API service for fetching game highlight videos."""

from datetime import datetime
from typing import List, Dict, Optional
from app.config import settings

# Only import if API key is configured
if settings.YOUTUBE_API_KEY:
    from googleapiclient.discovery import build
    youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)
else:
    youtube = None

# Channel IDs
NHL_CHANNEL_ID = "UCqFMzb-4AUf6WAIbl132QKA"
SPORTSNET_CHANNEL_ID = "UCVhibwHk4WKw4leUt6JfRLg"

# Team abbreviation to name mapping
TEAM_NAMES = {
    "SJS": "Sharks", "VGK": "Golden Knights", "LAK": "Kings",
    "ANA": "Ducks", "SEA": "Kraken", "VAN": "Canucks",
    "EDM": "Oilers", "CGY": "Flames", "WPG": "Jets",
    "MIN": "Wild", "COL": "Avalanche", "DAL": "Stars",
    "STL": "Blues", "CHI": "Blackhawks", "NSH": "Predators",
    "DET": "Red Wings", "CBJ": "Blue Jackets", "TBL": "Lightning",
    "FLA": "Panthers", "CAR": "Hurricanes", "WSH": "Capitals",
    "NYR": "Rangers", "NYI": "Islanders", "NJD": "Devils",
    "PHI": "Flyers", "PIT": "Penguins", "BOS": "Bruins",
    "TOR": "Maple Leafs", "OTT": "Senators", "MTL": "Canadiens",
    "BUF": "Sabres", "UTA": "Utah Hockey Club", "ARI": "Coyotes",
}


def search_game_highlights(
    away_team: str,
    home_team: str,
    game_date: datetime,
    max_results: int = 5,
    sharks_game_number: int = None
) -> Dict[str, Optional[str]]:
    """
    Search for game highlight videos from official NHL and Professor Hockey.

    Args:
        away_team: Away team abbreviation
        home_team: Home team abbreviation
        game_date: Game date
        max_results: Max results for other highlights
        sharks_game_number: Sequential game number for the season (e.g., 1-82)

    Returns dict with:
        - nhl_official: YouTube video ID from NHL channel
        - professor_hockey: YouTube video ID from Professor Hockey
        - other_highlights: List of other relevant video IDs
    """
    if not youtube:
        return {
            "nhl_official": None,
            "professor_hockey": None,
            "other_highlights": []
        }

    away_name = TEAM_NAMES.get(away_team, away_team)
    home_name = TEAM_NAMES.get(home_team, home_team)
    date_str = game_date.strftime('%B %d, %Y')

    results = {
        "nhl_official": None,
        "professor_hockey": None,
        "other_highlights": []
    }

    # Search 1: Official NHL channel with exact title template
    # Template: "{Away} vs. {Home} | NHL Highlights | {Month} {DD}, {YYYY}"
    try:
        nhl_query = f"{away_name} vs. {home_name} | NHL Highlights | {date_str}"
        nhl_search = youtube.search().list(
            q=nhl_query,
            channelId=NHL_CHANNEL_ID,
            type="video",
            part="id,snippet",
            maxResults=1,
            order="relevance",
            publishedAfter=game_date.isoformat() + "Z"
        ).execute()

        if nhl_search.get("items"):
            item = nhl_search["items"][0]
            snippet = item["snippet"]
            # Only accept if title contains "NHL Highlights" to avoid wrong matches
            if "nhl highlights" in snippet["title"].lower():
                results["nhl_official"] = {
                    "video_id": item["id"]["videoId"],
                    "title": snippet["title"],
                    "channel_name": snippet["channelTitle"],
                    "thumbnail_url": snippet["thumbnails"]["high"]["url"] if "high" in snippet["thumbnails"] else snippet["thumbnails"]["default"]["url"],
                    "published_at": datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
                }
    except Exception as e:
        print(f"Error fetching NHL official highlights: {e}")

    # Search 1b: Fallback to Sportsnet if NHL channel had no results
    # Template: "NHL Highlights | {Away} vs {Home} - {Month} {DD}, {YYYY}"
    if not results["nhl_official"]:
        try:
            sportsnet_query = f"NHL Highlights | {away_name} vs. {home_name} - {date_str}"
            sn_search = youtube.search().list(
                q=sportsnet_query,
                channelId=SPORTSNET_CHANNEL_ID,
                type="video",
                part="id,snippet",
                maxResults=1,
                order="relevance",
                publishedAfter=game_date.isoformat() + "Z"
            ).execute()

            if sn_search.get("items"):
                item = sn_search["items"][0]
                snippet = item["snippet"]
                if "nhl highlights" in snippet["title"].lower():
                    results["nhl_official"] = {
                        "video_id": item["id"]["videoId"],
                        "title": snippet["title"],
                        "channel_name": snippet["channelTitle"],
                        "thumbnail_url": snippet["thumbnails"]["high"]["url"] if "high" in snippet["thumbnails"] else snippet["thumbnails"]["default"]["url"],
                        "published_at": datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
                    }
        except Exception as e:
            print(f"Error fetching Sportsnet highlights: {e}")

    # Search 2: Professor Hockey
    # Professor Hockey uses format: "San Jose Sharks 25-26 Regular Season Review: Game X"
    try:
        if sharks_game_number:
            # Use specific game number format
            prof_query = f"San Jose Sharks 25-26 Regular Season Review Game {sharks_game_number}"
        else:
            # Fallback to date-based search
            prof_query = f"San Jose Sharks {game_date.strftime('%B %d %Y')} professor hockey"

        prof_search = youtube.search().list(
            q=prof_query,
            type="video",
            part="id,snippet",
            maxResults=3,  # Get multiple results to find the right one
            order="relevance",
            publishedAfter=game_date.isoformat() + "Z"
        ).execute()

        if prof_search.get("items"):
            # Look through results for Professor Hockey channel
            for item in prof_search["items"]:
                snippet = item["snippet"]
                if "professor" in snippet["channelTitle"].lower() and "sharks" in snippet["title"].lower():
                    results["professor_hockey"] = {
                        "video_id": item["id"]["videoId"],
                        "title": snippet["title"],
                        "channel_name": snippet["channelTitle"],
                        "thumbnail_url": snippet["thumbnails"]["high"]["url"] if "high" in snippet["thumbnails"] else snippet["thumbnails"]["default"]["url"],
                        "published_at": datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
                    }
                    break  # Found it, stop looking
    except Exception as e:
        print(f"Error fetching Professor Hockey highlights: {e}")

    # Search 3: Other highlights
    try:
        other_query = f"{away_name} vs {home_name} highlights {game_date.strftime('%B %d %Y')}"
        other_search = youtube.search().list(
            q=other_query,
            type="video",
            part="id,snippet",
            maxResults=max_results,
            order="relevance",
            publishedAfter=game_date.isoformat() + "Z"
        ).execute()

        for item in other_search.get("items", []):
            video_id = item["id"]["videoId"]
            # Don't duplicate NHL official or Professor Hockey
            if video_id not in [results["nhl_official"], results["professor_hockey"]]:
                results["other_highlights"].append(video_id)
    except Exception as e:
        print(f"Error fetching other highlights: {e}")

    return results


def get_video_details(video_id: str) -> Optional[Dict]:
    """
    Fetch metadata for a specific YouTube video.

    Returns dict with title, channel, thumbnail, published_at, etc.
    """
    if not youtube:
        return None

    try:
        response = youtube.videos().list(
            part="snippet,contentDetails",
            id=video_id
        ).execute()

        if not response.get("items"):
            return None

        item = response["items"][0]
        snippet = item["snippet"]

        return {
            "video_id": video_id,
            "title": snippet["title"],
            "channel_name": snippet["channelTitle"],
            "channel_id": snippet["channelId"],
            "published_at": datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")),
            "thumbnail_url": snippet["thumbnails"]["high"]["url"],
            "description": snippet["description"],
        }
    except Exception as e:
        print(f"Error fetching video details for {video_id}: {e}")
        return None


def search_individual_goal_clips(
    scorer_name: str,
    team: str,
    game_date: datetime,
    max_results: int = 3
) -> List[str]:
    """
    Search for individual goal highlight clips for a specific scorer.

    Returns list of YouTube video IDs.
    """
    if not youtube:
        return []

    query = f"{scorer_name} goal {team} {game_date.strftime('%B %d %Y')}"

    try:
        response = youtube.search().list(
            q=query,
            type="video",
            part="id",
            maxResults=max_results,
            order="relevance",
            publishedAfter=game_date.isoformat() + "Z"
        ).execute()

        return [item["id"]["videoId"] for item in response.get("items", [])]
    except Exception as e:
        print(f"Error fetching goal clips for {scorer_name}: {e}")
        return []