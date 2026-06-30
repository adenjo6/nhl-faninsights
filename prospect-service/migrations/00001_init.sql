-- +goose Up
-- +goose StatementBegin

-- The curated Sharks prospect roster (mirrors Elite Prospects' "in the system"
-- page). One row per player. CHL/AHL players carry a HockeyTech client_code +
-- player_id so the ingestion job can fetch live stats; NCAA/European players are
-- LINKOUT-only and just carry an Elite Prospects URL.
CREATE TABLE prospects (
    id                     BIGSERIAL PRIMARY KEY,
    full_name              TEXT NOT NULL,
    position               TEXT NOT NULL,             -- C, LW, RW, D, G
    draft_year             INT,
    draft_overall          INT,
    league                 TEXT NOT NULL,             -- OHL, WHL, QMJHL, AHL, NCAA, EUROPE
    source                 TEXT NOT NULL,             -- 'HOCKEYTECH' | 'LINKOUT'
    hockeytech_client_code TEXT,                      -- e.g. 'ohl','whl','lhjmq','ahl'
    hockeytech_player_id   TEXT,                      -- per-league HockeyTech id
    eliteprospects_url     TEXT,
    team_name              TEXT,
    active                 BOOLEAN NOT NULL DEFAULT true,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT prospects_source_chk CHECK (source IN ('HOCKEYTECH', 'LINKOUT')),
    -- a HOCKEYTECH row must have the ids needed to fetch stats
    CONSTRAINT prospects_hockeytech_ids_chk CHECK (
        source <> 'HOCKEYTECH'
        OR (hockeytech_client_code IS NOT NULL AND hockeytech_player_id IS NOT NULL)
    )
);

-- Ingested season totals. Separate table (not columns on prospects) so we can
-- keep multi-season history later without a schema change.
CREATE TABLE prospect_season_stats (
    id            BIGSERIAL PRIMARY KEY,
    prospect_id   BIGINT NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    season        TEXT NOT NULL,                      -- '2025-26'
    team_name     TEXT,
    games_played  INT NOT NULL DEFAULT 0,
    goals         INT NOT NULL DEFAULT 0,
    assists       INT NOT NULL DEFAULT 0,
    points        INT NOT NULL DEFAULT 0,
    plus_minus    INT NOT NULL DEFAULT 0,
    pim           INT NOT NULL DEFAULT 0,
    fetched_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (prospect_id, season)
);

CREATE INDEX idx_prospects_active ON prospects (active);
CREATE INDEX idx_season_stats_prospect ON prospect_season_stats (prospect_id);

-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE IF EXISTS prospect_season_stats;
DROP TABLE IF EXISTS prospects;
-- +goose StatementEnd
