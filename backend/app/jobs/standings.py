"""Standings update job - fetches and stores NHL standings."""

from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app import services

logger = logging.getLogger(__name__)


def update_standings(db: Session):
    """
    Fetch current NHL standings and store for context in game recaps.

    Stores standings snapshot to display:
    - Team's division rank
    - Points from playoff position
    - Recent form

    In future, this can be expanded to store in a dedicated table.
    For MVP, we'll just fetch and make available for game context.
    """
    logger.info("Fetching NHL standings...")

    try:
        standings_data = services.fetch_standings()

        # Extract Pacific Division for Sharks context
        pacific_division = None
        for standing in standings_data.get("standings", []):
            if standing.get("divisionName") == "Pacific":
                pacific_division = standing
                break

        if pacific_division:
            logger.info("✓ Standings updated - Pacific Division")

            # Log Sharks position for visibility
            sharks_data = None
            for team in pacific_division.get("teams", []):
                if team.get("teamAbbrev", {}).get("default") == "SJS":
                    sharks_data = team
                    break

            if sharks_data:
                logger.info(f"  Sharks: {sharks_data.get('divisionSequence')} in Pacific, "
                          f"{sharks_data.get('points')} pts, "
                          f"{sharks_data.get('wins')}-{sharks_data.get('losses')}-{sharks_data.get('otLosses')}")

        # TODO: Store in database if needed for historical tracking
        # For MVP, games will fetch standings on-demand via API

        return standings_data

    except Exception as e:
        logger.error(f"Error updating standings: {e}")
        raise
