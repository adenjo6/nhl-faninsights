"""Roster synchronization job - automatically tracks player team changes."""

from datetime import date, datetime
from sqlalchemy.orm import Session
import logging

from app.config import settings
from app.models import PlayerInfo, PlayerTeamHistory
from app import services

logger = logging.getLogger(__name__)


def sync_sharks_roster(db: Session) -> int:
    """
    Synchronize Sharks roster with NHL API.

    Automatically detects:
    - New players added to roster (trades, call-ups, signings)
    - Players removed from roster (trades, demotions, releases)
    - Jersey number changes
    - Position changes

    Returns: Number of changes made
    """
    logger.info(f"Syncing roster for {settings.SHARKS_TEAM_ID}...")

    try:
        # Fetch current roster from NHL API
        roster_data = services.fetch_current_roster(settings.SHARKS_TEAM_ID)

        # Get all players currently on Sharks (end_date = NULL)
        current_db_roster = db.query(PlayerTeamHistory).filter(
            PlayerTeamHistory.team_id == settings.SHARKS_TEAM_ID,
            PlayerTeamHistory.end_date == None
        ).all()

        # Build sets for comparison
        api_player_ids = set()
        api_players_map = {}

        # Process forwards, defensemen, and goalies
        for position_group in ["forwards", "defensemen", "goalies"]:
            for player_data in roster_data.get(position_group, []):
                player_id = player_data["id"]
                api_player_ids.add(player_id)
                api_players_map[player_id] = player_data

        db_player_ids = {record.player_id for record in current_db_roster}

        changes = 0

        # Find players removed from roster (traded/sent down)
        removed_players = db_player_ids - api_player_ids
        for player_id in removed_players:
            # Close their current stint with the Sharks
            history_record = db.query(PlayerTeamHistory).filter(
                PlayerTeamHistory.player_id == player_id,
                PlayerTeamHistory.team_id == settings.SHARKS_TEAM_ID,
                PlayerTeamHistory.end_date == None
            ).first()

            if history_record:
                history_record.end_date = date.today()
                changes += 1

                player_info = db.query(PlayerInfo).get(player_id)
                player_name = player_info.name if player_info else f"Player {player_id}"
                logger.info(f"  ↓ Removed: {player_name}")

        # Find players added to roster (trades/call-ups)
        added_players = api_player_ids - db_player_ids
        for player_id in added_players:
            player_data = api_players_map[player_id]

            # Create or update PlayerInfo
            player_info = db.query(PlayerInfo).get(player_id)
            if not player_info:
                player_info = PlayerInfo(
                    nhl_player_id=player_id,
                    name=player_data["firstName"]["default"] + " " + player_data["lastName"]["default"],
                    position=player_data.get("positionCode"),
                    jersey_number=player_data.get("sweaterNumber"),
                    nhl_profile_url=f"https://www.nhl.com/player/{player_id}",
                    headshot_url=player_data.get("headshot"),
                )
                db.add(player_info)
                logger.info(f"  ✨ Created player: {player_info.name}")
            else:
                # Update existing player info
                player_info.jersey_number = player_data.get("sweaterNumber")
                player_info.position = player_data.get("positionCode")
                player_info.headshot_url = player_data.get("headshot")

            # Add new team history record
            team_history = PlayerTeamHistory(
                player_id=player_id,
                team_id=settings.SHARKS_TEAM_ID,
                team_name="San Jose Sharks",
                start_date=date.today(),
                end_date=None  # Currently on team
            )
            db.add(team_history)
            changes += 1

            logger.info(f"  ↑ Added: {player_info.name} (#{player_info.jersey_number})")

        # Update info for existing players (jersey changes, etc.)
        for player_id in api_player_ids & db_player_ids:
            player_data = api_players_map[player_id]
            player_info = db.query(PlayerInfo).get(player_id)

            if player_info:
                old_number = player_info.jersey_number
                new_number = player_data.get("sweaterNumber")

                if old_number != new_number:
                    player_info.jersey_number = new_number
                    logger.info(f"  🔄 Updated: {player_info.name} (#{old_number} → #{new_number})")
                    changes += 1

                # Update other info
                player_info.position = player_data.get("positionCode")
                player_info.headshot_url = player_data.get("headshot")

        db.commit()
        logger.info(f"✓ Roster sync complete: {changes} changes")
        return changes

    except Exception as e:
        logger.error(f"Error syncing roster: {e}")
        db.rollback()
        raise


def get_current_roster(db: Session, team_id: str = None) -> list[dict]:
    """
    Get current roster from database.

    Args:
        db: Database session
        team_id: Team abbreviation (default: Sharks)

    Returns:
        List of player dicts with: id, name, position, jersey_number, etc.
    """
    if not team_id:
        team_id = settings.SHARKS_TEAM_ID

    # Query players currently on the team
    roster_records = (
        db.query(PlayerInfo, PlayerTeamHistory)
        .join(PlayerTeamHistory, PlayerInfo.nhl_player_id == PlayerTeamHistory.player_id)
        .filter(
            PlayerTeamHistory.team_id == team_id,
            PlayerTeamHistory.end_date == None
        )
        .all()
    )

    roster = []
    for player_info, team_history in roster_records:
        roster.append({
            "id": player_info.nhl_player_id,
            "name": player_info.name,
            "position": player_info.position,
            "jersey_number": player_info.jersey_number,
            "nhl_profile_url": player_info.nhl_profile_url,
            "headshot_url": player_info.headshot_url,
            "joined_team": team_history.start_date.isoformat() if team_history.start_date else None,
        })

    return roster


def get_player_team_history(db: Session, player_id: int) -> list[dict]:
    """
    Get team history for a specific player.

    Returns:
        List of team stints with start/end dates
    """
    history = (
        db.query(PlayerTeamHistory)
        .filter(PlayerTeamHistory.player_id == player_id)
        .order_by(PlayerTeamHistory.start_date.desc())
        .all()
    )

    result = []
    for record in history:
        result.append({
            "team_id": record.team_id,
            "team_name": record.team_name,
            "start_date": record.start_date.isoformat(),
            "end_date": record.end_date.isoformat() if record.end_date else None,
            "current": record.end_date is None,
        })

    return result