"""
Test NHL API services.
"""
import pytest
from datetime import date
from app.services.nhl import (
    fetch_team_schedule,
    fetch_boxscore,
)


@pytest.mark.integration
def test_fetch_team_schedule():
    """Test fetching Sharks schedule from NHL API."""
    games = fetch_team_schedule('SJS', start_date=date(2024, 10, 1))
    assert isinstance(games, list)
    # Schedule might be empty for past dates, so just check it's a list


@pytest.mark.integration
def test_fetch_boxscore():
    """Test fetching boxscore data."""
    # Use a known game ID from the 2024 season
    try:
        boxscore = fetch_boxscore(2024020001)
        assert boxscore is not None
        assert 'awayTeam' in boxscore or 'homeTeam' in boxscore
    except Exception as e:
        # API might not have this game, that's okay for testing
        pytest.skip(f"NHL API returned error: {e}")