-- name: ListProspects :many
-- Roster for the public list, joined to the current season's stats (if any).
-- @season is the current season label; position/league are optional filters.
SELECT
    p.id,
    p.full_name,
    p.position,
    p.draft_year,
    p.draft_overall,
    p.league,
    p.source,
    p.eliteprospects_url,
    COALESCE(s.team_name, p.team_name) AS team_name,
    s.season,
    s.games_played,
    s.goals,
    s.assists,
    s.points,
    s.plus_minus,
    s.pim,
    s.fetched_at
FROM prospects p
LEFT JOIN prospect_season_stats s
       ON s.prospect_id = p.id AND s.season = sqlc.arg(season)
WHERE p.active = true
  AND (sqlc.narg(position)::text IS NULL OR p.position = sqlc.narg(position))
  AND (sqlc.narg(league)::text   IS NULL OR p.league   = sqlc.narg(league))
ORDER BY s.points DESC NULLS LAST, p.full_name ASC;

-- name: GetProspect :one
SELECT
    p.id,
    p.full_name,
    p.position,
    p.draft_year,
    p.draft_overall,
    p.league,
    p.source,
    p.eliteprospects_url,
    COALESCE(s.team_name, p.team_name) AS team_name,
    s.season,
    s.games_played,
    s.goals,
    s.assists,
    s.points,
    s.plus_minus,
    s.pim,
    s.fetched_at
FROM prospects p
LEFT JOIN prospect_season_stats s
       ON s.prospect_id = p.id AND s.season = sqlc.arg(season)
WHERE p.id = sqlc.arg(id);

-- name: ListIngestableProspects :many
-- HockeyTech-sourced active prospects the cron should refresh.
SELECT id, full_name, hockeytech_client_code, hockeytech_player_id
FROM prospects
WHERE active = true AND source = 'HOCKEYTECH'
ORDER BY id;

-- name: UpsertSeasonStats :exec
INSERT INTO prospect_season_stats (
    prospect_id, season, team_name,
    games_played, goals, assists, points, plus_minus, pim, fetched_at
) VALUES (
    sqlc.arg(prospect_id), sqlc.arg(season), sqlc.arg(team_name),
    sqlc.arg(games_played), sqlc.arg(goals), sqlc.arg(assists),
    sqlc.arg(points), sqlc.arg(plus_minus), sqlc.arg(pim), now()
)
ON CONFLICT (prospect_id, season) DO UPDATE SET
    team_name    = EXCLUDED.team_name,
    games_played = EXCLUDED.games_played,
    goals        = EXCLUDED.goals,
    assists      = EXCLUDED.assists,
    points       = EXCLUDED.points,
    plus_minus   = EXCLUDED.plus_minus,
    pim          = EXCLUDED.pim,
    fetched_at   = now();
