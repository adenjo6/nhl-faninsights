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
    __slots__ = ("season", "games_played", "goals", "assists", "points", "plus_minus", "pim", "updated_at")
    SEASON_FIELD_NUMBER: _ClassVar[int]
    GAMES_PLAYED_FIELD_NUMBER: _ClassVar[int]
    GOALS_FIELD_NUMBER: _ClassVar[int]
    ASSISTS_FIELD_NUMBER: _ClassVar[int]
    POINTS_FIELD_NUMBER: _ClassVar[int]
    PLUS_MINUS_FIELD_NUMBER: _ClassVar[int]
    PIM_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    season: str
    games_played: int
    goals: int
    assists: int
    points: int
    plus_minus: int
    pim: int
    updated_at: str
    def __init__(self, season: _Optional[str] = ..., games_played: _Optional[int] = ..., goals: _Optional[int] = ..., assists: _Optional[int] = ..., points: _Optional[int] = ..., plus_minus: _Optional[int] = ..., pim: _Optional[int] = ..., updated_at: _Optional[str] = ...) -> None: ...

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
