"""Services for external API integrations."""

# NHL API services
from .nhl import (
    fetch_team_schedule,
    fetch_boxscore,
    fetch_play_by_play,
    fetch_current_roster,
    fetch_player_stats,
    fetch_standings,
    transform_boxscore,
    extract_goal_details,
)

# YouTube services
from .youtube import (
    search_game_highlights,
    get_video_details,
    search_individual_goal_clips,
)

# Claude AI services
from .claude import generate_game_recap

__all__ = [
    # NHL
    "fetch_team_schedule",
    "fetch_boxscore",
    "fetch_play_by_play",
    "fetch_current_roster",
    "fetch_player_stats",
    "fetch_standings",
    "transform_boxscore",
    "extract_goal_details",
    # YouTube
    "search_game_highlights",
    "get_video_details",
    "search_individual_goal_clips",
    # Claude
    "generate_game_recap",
]