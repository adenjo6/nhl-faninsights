from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Prospect(_message.Message):
    __slots__ = ("id", "full_name", "position", "draft_year", "draft_overall", "league", "team_name", "eliteprospects_url", "has_live_stats", "current_season")
    ID_FIELD_NUMBER: _ClassVar[int]
    FULL_NAME_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    DRAFT_YEAR_FIELD_NUMBER: _ClassVar[int]
    DRAFT_OVERALL_FIELD_NUMBER: _ClassVar[int]
    LEAGUE_FIELD_NUMBER: _ClassVar[int]
    TEAM_NAME_FIELD_NUMBER: _ClassVar[int]
    ELITEPROSPECTS_URL_FIELD_NUMBER: _ClassVar[int]
    HAS_LIVE_STATS_FIELD_NUMBER: _ClassVar[int]
    CURRENT_SEASON_FIELD_NUMBER: _ClassVar[int]
    id: int
    full_name: str
    position: str
    draft_year: int
    draft_overall: int
    league: str
    team_name: str
    eliteprospects_url: str
    has_live_stats: bool
    current_season: SeasonStats
    def __init__(self, id: _Optional[int] = ..., full_name: _Optional[str] = ..., position: _Optional[str] = ..., draft_year: _Optional[int] = ..., draft_overall: _Optional[int] = ..., league: _Optional[str] = ..., team_name: _Optional[str] = ..., eliteprospects_url: _Optional[str] = ..., has_live_stats: _Optional[bool] = ..., current_season: _Optional[_Union[SeasonStats, _Mapping]] = ...) -> None: ...

class SeasonStats(_message.Message):
    __slots__ = ("season", "games_played", "goals", "assists", "points", "plus_minus", "pim", "updated_at", "goalie")
    SEASON_FIELD_NUMBER: _ClassVar[int]
    GAMES_PLAYED_FIELD_NUMBER: _ClassVar[int]
    GOALS_FIELD_NUMBER: _ClassVar[int]
    ASSISTS_FIELD_NUMBER: _ClassVar[int]
    POINTS_FIELD_NUMBER: _ClassVar[int]
    PLUS_MINUS_FIELD_NUMBER: _ClassVar[int]
    PIM_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    GOALIE_FIELD_NUMBER: _ClassVar[int]
    season: str
    games_played: int
    goals: int
    assists: int
    points: int
    plus_minus: int
    pim: int
    updated_at: str
    goalie: GoalieStats
    def __init__(self, season: _Optional[str] = ..., games_played: _Optional[int] = ..., goals: _Optional[int] = ..., assists: _Optional[int] = ..., points: _Optional[int] = ..., plus_minus: _Optional[int] = ..., pim: _Optional[int] = ..., updated_at: _Optional[str] = ..., goalie: _Optional[_Union[GoalieStats, _Mapping]] = ...) -> None: ...

class GoalieStats(_message.Message):
    __slots__ = ("wins", "losses", "ot_losses", "shutouts", "saves", "shots", "gaa", "sv_pct")
    WINS_FIELD_NUMBER: _ClassVar[int]
    LOSSES_FIELD_NUMBER: _ClassVar[int]
    OT_LOSSES_FIELD_NUMBER: _ClassVar[int]
    SHUTOUTS_FIELD_NUMBER: _ClassVar[int]
    SAVES_FIELD_NUMBER: _ClassVar[int]
    SHOTS_FIELD_NUMBER: _ClassVar[int]
    GAA_FIELD_NUMBER: _ClassVar[int]
    SV_PCT_FIELD_NUMBER: _ClassVar[int]
    wins: int
    losses: int
    ot_losses: int
    shutouts: int
    saves: int
    shots: int
    gaa: float
    sv_pct: float
    def __init__(self, wins: _Optional[int] = ..., losses: _Optional[int] = ..., ot_losses: _Optional[int] = ..., shutouts: _Optional[int] = ..., saves: _Optional[int] = ..., shots: _Optional[int] = ..., gaa: _Optional[float] = ..., sv_pct: _Optional[float] = ...) -> None: ...

class ListProspectsRequest(_message.Message):
    __slots__ = ("position", "league")
    POSITION_FIELD_NUMBER: _ClassVar[int]
    LEAGUE_FIELD_NUMBER: _ClassVar[int]
    position: str
    league: str
    def __init__(self, position: _Optional[str] = ..., league: _Optional[str] = ...) -> None: ...

class ListProspectsResponse(_message.Message):
    __slots__ = ("prospects",)
    PROSPECTS_FIELD_NUMBER: _ClassVar[int]
    prospects: _containers.RepeatedCompositeFieldContainer[Prospect]
    def __init__(self, prospects: _Optional[_Iterable[_Union[Prospect, _Mapping]]] = ...) -> None: ...

class GetProspectRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class GetProspectResponse(_message.Message):
    __slots__ = ("prospect",)
    PROSPECT_FIELD_NUMBER: _ClassVar[int]
    prospect: Prospect
    def __init__(self, prospect: _Optional[_Union[Prospect, _Mapping]] = ...) -> None: ...
