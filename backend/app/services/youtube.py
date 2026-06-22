"""YouTube API service for fetching game highlight videos."""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Only import if API key is configured
if settings.YOUTUBE_API_KEY:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)
else:
    youtube = None
    HttpError = Exception  # fallback for type checking


class YouTubeQuotaExceeded(Exception):
    """Raised when YouTube API quota is exceeded."""
    pass


# Channel IDs
NHL_CHANNEL_ID = "UCqFMzb-4AUf6WAIbl132QKA"
SPORTSNET_CHANNEL_ID = "UCVhibwHk4WKw4leUt6JfRLg"
PROFESSOR_HOCKEY_CHANNEL_ID = "UCpSAxcOssY_Ul57opYBcWVw"

# Upload playlist IDs (replace UC -> UU in channel ID)
NHL_UPLOADS_PLAYLIST = "UUqFMzb-4AUf6WAIbl132QKA"
SPORTSNET_UPLOADS_PLAYLIST = "UUVhibwHk4WKw4leUt6JfRLg"
PROFESSOR_HOCKEY_UPLOADS_PLAYLIST = "UUpSAxcOssY_Ul57opYBcWVw"

# In-memory cache for channel upload lists
_channel_video_cache: Dict[str, dict] = {}

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


def _format_date_no_leading_zero(dt: datetime) -> str:
    """Format date as 'Month D, YYYY' without leading zero on day."""
    return f"{dt.strftime('%B')} {dt.day}, {dt.year}"


def _check_quota_error(e: Exception):
    """Raise YouTubeQuotaExceeded if it's a quota error."""
    if isinstance(e, HttpError) and e.resp.status == 403:
        raise YouTubeQuotaExceeded("YouTube API quota exceeded") from e


# ============================================================================
# Playlist-based video fetching (1 quota unit per 50 videos)
# ============================================================================

def _fetch_channel_uploads(playlist_id: str, max_pages: int = 20) -> List[dict]:
    """
    Fetch recent uploads from a channel's uploads playlist.
    Uses playlistItems.list() at 1 quota unit per call (vs 100 for search).
    """
    if not youtube:
        return []

    videos = []
    page_token = None

    for _ in range(max_pages):
        try:
            request = youtube.playlistItems().list(
                playlistId=playlist_id,
                part="snippet",
                maxResults=50,
                pageToken=page_token
            )
            response = request.execute()
        except HttpError as e:
            _check_quota_error(e)
            logger.error(f"Error fetching playlist {playlist_id}: {e}")
            break

        for item in response.get("items", []):
            snippet = item["snippet"]
            thumbnails = snippet.get("thumbnails", {})
            thumb_url = (thumbnails.get("high") or thumbnails.get("default", {})).get("url", "")
            videos.append({
                "video_id": snippet["resourceId"]["videoId"],
                "title": snippet["title"],
                "channel_name": snippet.get("channelTitle", ""),
                "thumbnail_url": thumb_url,
                "published_at": snippet["publishedAt"],
            })

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    logger.info(f"Fetched {len(videos)} videos from playlist {playlist_id}")
    return videos


def _get_cached_uploads(playlist_id: str, max_age_hours: int = 6, max_pages: int = 20) -> List[dict]:
    """Get channel uploads from cache, or fetch and cache them."""
    cached = _channel_video_cache.get(playlist_id)
    if cached:
        age = datetime.now() - cached["fetched_at"]
        if age < timedelta(hours=max_age_hours):
            return cached["videos"]

    videos = _fetch_channel_uploads(playlist_id, max_pages=max_pages)
    _channel_video_cache[playlist_id] = {
        "fetched_at": datetime.now(),
        "videos": videos,
    }
    return videos


def _match_video_to_game(
    videos: List[dict],
    away_team: str,
    home_team: str,
    game_date: datetime,
    match_type: str = "highlights",
    sharks_game_number: int = None,
) -> Optional[dict]:
    """
    Match a game to a video from a pre-fetched list by parsing titles.

    match_type:
        "highlights" - match NHL/Sportsnet highlight videos (team names + date)
        "professor_hockey" - match Professor Hockey videos (game number or team + date)
    """
    away_name = TEAM_NAMES.get(away_team, away_team).lower()
    home_name = TEAM_NAMES.get(home_team, home_team).lower()
    date_str = _format_date_no_leading_zero(game_date).lower()

    for video in videos:
        title = video["title"].lower()

        if match_type == "highlights":
            # Must contain "highlights" and BOTH team names and the date
            if "highlights" not in title:
                continue
            has_both_teams = away_name in title and home_name in title
            has_date = date_str in title
            if has_both_teams and has_date:
                return video

        elif match_type == "professor_hockey":
            if "sharks" not in title:
                continue
            # Try matching by game number first
            if sharks_game_number:
                # Match patterns like "Game 42" or "Game #42"
                pattern = rf"game\s*#?\s*{sharks_game_number}\b"
                if re.search(pattern, title):
                    return video
            # Fallback: match by date
            if date_str in title:
                return video

    return None


def _build_video_result(video: dict) -> dict:
    """Convert a playlist video dict to the standard result format."""
    published = video["published_at"]
    if isinstance(published, str):
        published = datetime.fromisoformat(published.replace("Z", "+00:00"))
    return {
        "video_id": video["video_id"],
        "title": video["title"],
        "channel_name": video["channel_name"],
        "thumbnail_url": video["thumbnail_url"],
        "published_at": published,
    }


# ============================================================================
# Main public API
# ============================================================================

def search_game_highlights(
    away_team: str,
    home_team: str,
    game_date: datetime,
    max_results: int = 5,
    sharks_game_number: int = None
) -> Dict[str, Optional[str]]:
    """
    Search for game highlight videos using playlist-based matching.
    Falls back to search API only if playlist matching fails.

    Raises YouTubeQuotaExceeded if the API quota is exhausted.
    """
    if not youtube:
        return {
            "nhl_official": None,
            "professor_hockey": None,
            "other_highlights": []
        }

    results = {
        "nhl_official": None,
        "professor_hockey": None,
        "other_highlights": []
    }

    # Step 1: Try NHL channel uploads (playlist API - 1 unit per 50 videos, cached)
    try:
        nhl_videos = _get_cached_uploads(NHL_UPLOADS_PLAYLIST, max_pages=80)
        match = _match_video_to_game(nhl_videos, away_team, home_team, game_date)
        if match:
            results["nhl_official"] = _build_video_result(match)
    except YouTubeQuotaExceeded:
        raise
    except Exception as e:
        logger.error(f"Error matching NHL uploads: {e}")

    # Step 2: If no NHL match, try Sportsnet uploads
    if not results["nhl_official"]:
        try:
            sn_videos = _get_cached_uploads(SPORTSNET_UPLOADS_PLAYLIST, max_pages=80)
            match = _match_video_to_game(sn_videos, away_team, home_team, game_date)
            if match:
                results["nhl_official"] = _build_video_result(match)
        except YouTubeQuotaExceeded:
            raise
        except Exception as e:
            logger.error(f"Error matching Sportsnet uploads: {e}")

    # Step 3: Try Professor Hockey uploads
    try:
        prof_videos = _get_cached_uploads(PROFESSOR_HOCKEY_UPLOADS_PLAYLIST, max_pages=5)
        match = _match_video_to_game(
            prof_videos, away_team, home_team, game_date,
            match_type="professor_hockey",
            sharks_game_number=sharks_game_number,
        )
        if match:
            results["professor_hockey"] = _build_video_result(match)
    except YouTubeQuotaExceeded:
        raise
    except Exception as e:
        logger.error(f"Error matching Professor Hockey uploads: {e}")

    # Step 4: Fallback to search API if playlist matching found nothing
    if not results["nhl_official"]:
        try:
            results["nhl_official"] = _search_fallback_highlights(
                away_team, home_team, game_date
            )
        except YouTubeQuotaExceeded:
            raise
        except Exception as e:
            logger.error(f"Error in search fallback: {e}")

    return results


def _search_fallback_highlights(
    away_team: str,
    home_team: str,
    game_date: datetime,
) -> Optional[dict]:
    """Fallback: use search API for games not matched by playlist. Costs 100 units."""
    away_name = TEAM_NAMES.get(away_team, away_team)
    home_name = TEAM_NAMES.get(home_team, home_team)
    date_str = _format_date_no_leading_zero(game_date)
    published_after = game_date - timedelta(hours=6)

    try:
        response = youtube.search().list(
            q=f"{away_name} vs {home_name} NHL Highlights {date_str}",
            channelId=NHL_CHANNEL_ID,
            type="video",
            part="id,snippet",
            maxResults=3,
            order="relevance",
            publishedAfter=published_after.strftime('%Y-%m-%dT%H:%M:%SZ')
        ).execute()

        for item in response.get("items", []):
            title = item["snippet"]["title"].lower()
            if "highlights" in title:
                return _extract_video_data(item)
    except HttpError as e:
        _check_quota_error(e)
        logger.error(f"Search fallback NHL error: {e}")

    # Try Sportsnet as second fallback
    try:
        response = youtube.search().list(
            q=f"NHL Highlights {away_name} vs {home_name} {date_str}",
            channelId=SPORTSNET_CHANNEL_ID,
            type="video",
            part="id,snippet",
            maxResults=3,
            order="relevance",
            publishedAfter=published_after.strftime('%Y-%m-%dT%H:%M:%SZ')
        ).execute()

        for item in response.get("items", []):
            title = item["snippet"]["title"].lower()
            if "highlights" in title:
                return _extract_video_data(item)
    except HttpError as e:
        _check_quota_error(e)
        logger.error(f"Search fallback Sportsnet error: {e}")

    return None


def _extract_video_data(item: dict) -> dict:
    """Extract standardized video data from a YouTube search result item."""
    snippet = item["snippet"]
    thumbnails = snippet.get("thumbnails", {})
    thumb_url = (thumbnails.get("high") or thumbnails.get("default", {})).get("url", "")
    return {
        "video_id": item["id"]["videoId"],
        "title": snippet["title"],
        "channel_name": snippet["channelTitle"],
        "thumbnail_url": thumb_url,
        "published_at": datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
    }


def get_video_details(video_id: str) -> Optional[Dict]:
    """Fetch metadata for a specific YouTube video."""
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
    except HttpError as e:
        _check_quota_error(e)
        logger.error(f"Error fetching video details for {video_id}: {e}")
        return None


def search_individual_goal_clips(
    scorer_name: str,
    team: str,
    game_date: datetime,
    max_results: int = 3
) -> List[str]:
    """Search for individual goal highlight clips for a specific scorer."""
    if not youtube:
        return []

    query = f"{scorer_name} goal {team} {_format_date_no_leading_zero(game_date)}"

    try:
        response = youtube.search().list(
            q=query,
            type="video",
            part="id",
            maxResults=max_results,
            order="relevance",
            publishedAfter=(game_date - timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:%SZ')
        ).execute()

        return [item["id"]["videoId"] for item in response.get("items", [])]
    except HttpError as e:
        _check_quota_error(e)
        logger.error(f"Error fetching goal clips for {scorer_name}: {e}")
        return []
