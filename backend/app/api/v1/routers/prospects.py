"""
Prospects API - Links to Elite Prospects.
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional


router = APIRouter()


class ProspectLink(BaseModel):
    """Prospect information with Elite Prospects link."""
    name: str
    position: str
    draft_year: Optional[int] = None
    elite_prospects_url: str
    description: Optional[str] = None


# San Jose Sharks top prospects (update this list as needed)
SHARKS_PROSPECTS = [
    ProspectLink(
        name="Quentin Musty",
        position="LW",
        draft_year=2023,
        elite_prospects_url="https://www.eliteprospects.com/player/586930/quentin-musty",
        description="2023 1st round pick (26th overall). Dynamic winger with scoring ability."
    ),
    ProspectLink(
        name="Kasper Halttunen",
        position="RW",
        draft_year=2022,
        elite_prospects_url="https://www.eliteprospects.com/player/534856/kasper-halttunen",
        description="2022 2nd round pick (52nd overall). Finnish sharpshooter."
    ),
    ProspectLink(
        name="David Edstrom",
        position="C",
        draft_year=2023,
        elite_prospects_url="https://www.eliteprospects.com/player/623249/david-edstrom",
        description="2023 2nd round pick (32nd overall). Two-way center from Sweden."
    ),
    ProspectLink(
        name="Filip Bystedt",
        position="C",
        draft_year=2022,
        elite_prospects_url="https://www.eliteprospects.com/player/534859/filip-bystedt",
        description="2022 2nd round pick (34th overall). Skilled Swedish center."
    ),
    ProspectLink(
        name="Luca Cagnoni",
        position="D",
        draft_year=2023,
        elite_prospects_url="https://www.eliteprospects.com/player/586924/luca-cagnoni",
        description="2023 4th round pick (118th overall). Offensive defenseman."
    ),
    ProspectLink(
        name="Brandon Svoboda",
        position="C",
        draft_year=2023,
        elite_prospects_url="https://www.eliteprospects.com/player/586938/brandon-svoboda",
        description="2023 5th round pick (139th overall). Two-way forward."
    ),
]


@router.get("", response_model=List[ProspectLink])
def get_prospects(
    position: Optional[str] = Query(None, description="Filter by position (C, LW, RW, D, G)"),
    draft_year: Optional[int] = Query(None, description="Filter by draft year")
):
    """
    Get San Jose Sharks prospects with Elite Prospects links.

    - **position**: Filter by position (C, LW, RW, D, G)
    - **draft_year**: Filter by draft year
    """
    prospects = SHARKS_PROSPECTS

    if position:
        prospects = [p for p in prospects if p.position == position.upper()]

    if draft_year:
        prospects = [p for p in prospects if p.draft_year == draft_year]

    return prospects


@router.get("/search", response_model=ProspectLink)
def search_prospect(name: str = Query(..., description="Player name to search")):
    """
    Search for a specific prospect by name.
    """
    for prospect in SHARKS_PROSPECTS:
        if name.lower() in prospect.name.lower():
            return prospect

    # If not found in our list, return a generic Elite Prospects search URL
    return ProspectLink(
        name=name,
        position="Unknown",
        elite_prospects_url=f"https://www.eliteprospects.com/search/player?q={name.replace(' ', '+')}",
        description="Search results on Elite Prospects"
    )
