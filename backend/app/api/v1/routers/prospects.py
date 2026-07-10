"""Prospects API.

Thin REST facade over the prospect-service (Go gRPC microservice). This router
calls the service via app.services.prospect_client, caches the mapped result in
Redis, and re-exposes it as JSON. Browsers hit these endpoints; the gRPC hop is
internal only.

Replaces the previous hard-coded Elite Prospects link list: the curated roster
and live CHL/AHL stats now live in the Go service's database.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.prospect_client import (
    ProspectNotFound,
    ProspectServiceUnavailable,
    prospect_client,
)
from app.services.redis_cache import cache

logger = logging.getLogger(__name__)

router = APIRouter()

# Gateway cache TTL. The Go service refreshes stats once daily (6am PT cron), so
# a few hours of staleness is fine and most reads hit Redis.
PROSPECTS_CACHE_TTL = 6 * 60 * 60  # 6 hours

# Bump when the payload shape or the underlying prospect data changes in a
# deploy (e.g. a data migration): old cache entries otherwise keep serving
# stale rows for up to the TTL, since nothing else invalidates them.
PROSPECTS_CACHE_VERSION = "v2"


class GoalieStats(BaseModel):
    """A goalie's season line. GAA/SV% are the league feed's own computed
    values (e.g. 2.51 / 0.919), not rederived from the counters. ot_losses,
    gaa, and sv_pct are None when the source doesn't report them — the
    frontend renders unknown as an em dash, never as 0."""
    wins: int
    losses: int
    ot_losses: Optional[int] = None
    shutouts: int
    saves: int
    shots: int
    gaa: Optional[float] = None
    sv_pct: Optional[float] = None


class SeasonStats(BaseModel):
    """A prospect's current-season totals (CHL/AHL via HockeyTech). For
    goalies the skater counters are 0 and `goalie` is set."""
    season: str
    games_played: int
    goals: int
    assists: int
    points: int
    plus_minus: int
    pim: int
    updated_at: str  # ISO8601 UTC, when the Go ingest last fetched these
    goalie: Optional[GoalieStats] = None


class Prospect(BaseModel):
    """One Sharks prospect. `current_season` is null for LINKOUT players
    (NCAA/European) who carry only an Elite Prospects link, no live stats."""
    id: int
    full_name: str
    position: str
    draft_year: Optional[int] = None
    draft_overall: Optional[int] = None
    league: str
    team_name: Optional[str] = None
    elite_prospects_url: Optional[str] = None
    has_live_stats: bool
    current_season: Optional[SeasonStats] = None


def _to_model(p) -> Prospect:
    """Map a prospects.v1.Prospect proto to the REST Pydantic model.

    Proto int32 zero-values for draft_year/draft_overall mean "unset" (the
    columns are nullable in the DB), so 0 is normalized back to None.
    """
    season = None
    if p.HasField("current_season"):
        s = p.current_season
        goalie = None
        if s.HasField("goalie"):
            g = s.goalie
            goalie = GoalieStats(
                wins=g.wins,
                losses=g.losses,
                ot_losses=g.ot_losses if g.HasField("ot_losses") else None,
                shutouts=g.shutouts,
                saves=g.saves,
                shots=g.shots,
                gaa=g.gaa if g.HasField("gaa") else None,
                sv_pct=g.sv_pct if g.HasField("sv_pct") else None,
            )
        season = SeasonStats(
            season=s.season,
            games_played=s.games_played,
            goals=s.goals,
            assists=s.assists,
            points=s.points,
            plus_minus=s.plus_minus,
            pim=s.pim,
            updated_at=s.updated_at,
            goalie=goalie,
        )
    return Prospect(
        id=p.id,
        full_name=p.full_name,
        position=p.position,
        draft_year=p.draft_year or None,
        draft_overall=p.draft_overall or None,
        league=p.league,
        team_name=p.team_name or None,
        elite_prospects_url=p.eliteprospects_url or None,
        has_live_stats=p.has_live_stats,
        current_season=season,
    )


@router.get("", response_model=List[Prospect])
def list_prospects(
    position: Optional[str] = Query(None, description="Filter by position (C, LW, RW, D, G)"),
    league: Optional[str] = Query(None, description="Filter by league (OHL, WHL, QMJHL, AHL, NCAA, EUROPE)"),
):
    """List Sharks prospects, optionally filtered by position and/or league.

    If the prospect-service is unreachable, returns an empty list (soft-fail)
    rather than erroring, consistent with the platform's optional-integration
    pattern.
    """
    pos = position.upper() if position else None
    lg = league.upper() if league else None
    key = f"prospects:{PROSPECTS_CACHE_VERSION}:list:pos={pos or ''}:league={lg or ''}"

    cached = cache.get(key)
    if cached is not None:
        return cached

    protos = prospect_client.list_prospects(pos, lg)
    if protos is None:
        # service unavailable — soft-fail, and don't cache the empty result so
        # the next request retries once the service is back.
        return []

    result = [_to_model(p).model_dump() for p in protos]
    cache.set(key, result, ttl=PROSPECTS_CACHE_TTL)
    return result


@router.get("/{prospect_id}", response_model=Prospect)
def get_prospect(prospect_id: int):
    """Fetch a single prospect by its internal id.

    404 if no such prospect; 503 if the prospect-service is unavailable.
    """
    key = f"prospects:{PROSPECTS_CACHE_VERSION}:get:{prospect_id}"

    cached = cache.get(key)
    if cached is not None:
        return cached

    try:
        proto = prospect_client.get_prospect(prospect_id)
    except ProspectNotFound:
        raise HTTPException(status_code=404, detail=f"Prospect {prospect_id} not found")
    except ProspectServiceUnavailable:
        raise HTTPException(status_code=503, detail="Prospect service unavailable")

    result = _to_model(proto).model_dump()
    cache.set(key, result, ttl=PROSPECTS_CACHE_TTL)
    return result
