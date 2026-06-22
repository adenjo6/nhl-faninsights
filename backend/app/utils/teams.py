"""NHL team metadata helpers.

NHL_TEAM_NICKNAMES maps a team's NHL Stats API abbreviation (the value stored in
Game.away_team / Game.home_team) to the team's primary nickname — the form that
appears in r/SanJoseSharks Post-Game Thread titles. Used by the Reddit discovery
listing scan to match a candidate thread to the right game.
"""

NHL_TEAM_NICKNAMES: dict[str, str] = {
    "ANA": "Ducks",
    "BOS": "Bruins",
    "BUF": "Sabres",
    "CAR": "Hurricanes",
    "CBJ": "Blue Jackets",
    "CGY": "Flames",
    "CHI": "Blackhawks",
    "COL": "Avalanche",
    "DAL": "Stars",
    "DET": "Red Wings",
    "EDM": "Oilers",
    "FLA": "Panthers",
    "LAK": "Kings",
    "MIN": "Wild",
    "MTL": "Canadiens",
    "NJD": "Devils",
    "NSH": "Predators",
    "NYI": "Islanders",
    "NYR": "Rangers",
    "OTT": "Senators",
    "PHI": "Flyers",
    "PIT": "Penguins",
    "SEA": "Kraken",
    "SJS": "Sharks",
    "STL": "Blues",
    "TBL": "Lightning",
    "TOR": "Maple Leafs",
    "UTA": "Mammoth",
    "VAN": "Canucks",
    "VGK": "Golden Knights",
    "WPG": "Jets",
    "WSH": "Capitals",
}


def opponent_of(team: str, away_team: str, home_team: str) -> str:
    """Return the abbreviation of the team `team` is playing against."""
    return home_team if away_team == team else away_team


def opponent_nickname(team: str, away_team: str, home_team: str) -> str | None:
    """Return the opponent's nickname for matching PGT titles, or None if unknown."""
    return NHL_TEAM_NICKNAMES.get(opponent_of(team, away_team, home_team))
