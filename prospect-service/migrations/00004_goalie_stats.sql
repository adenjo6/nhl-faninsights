-- +goose Up
-- +goose StatementBegin

-- Goalie live stats. Nullable columns on the same season-stats table: a
-- prospect-season is one row whether skater or goalie, so no second table or
-- join. GAA/SV% are stored as the feed's own computed values (the league's
-- math is authoritative for empty-net/shootout edge cases); saves/shots kept
-- for context. Skater counters stay 0 on goalie rows and goalie columns stay
-- NULL on skater rows.
ALTER TABLE prospect_season_stats
    ADD COLUMN wins      INT,
    ADD COLUMN losses    INT,
    ADD COLUMN ot_losses INT,
    ADD COLUMN shutouts  INT,
    ADD COLUMN saves     INT,
    ADD COLUMN shots     INT,
    ADD COLUMN gaa       NUMERIC(5,2),
    ADD COLUMN sv_pct    NUMERIC(5,3);

-- Flip the two CHL goalies to live HockeyTech stats. player_ids confirmed by
-- name+team in each league's live 2025-26 topgoalies feed. Korostelyov (MHL,
-- no HockeyTech feed) and Knowling (USHL key not publicly exposed) remain
-- LINKOUT.
UPDATE prospects
   SET source = 'HOCKEYTECH', hockeytech_client_code = 'whl', hockeytech_player_id = '29467'
 WHERE full_name = 'Joshua Ravensbergen';
UPDATE prospects
   SET source = 'HOCKEYTECH', hockeytech_client_code = 'ohl', hockeytech_player_id = '9372'
 WHERE full_name = 'Christian Kirsch';

-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
UPDATE prospects
   SET source = 'LINKOUT', hockeytech_client_code = NULL, hockeytech_player_id = NULL
 WHERE full_name IN ('Joshua Ravensbergen', 'Christian Kirsch');
ALTER TABLE prospect_season_stats
    DROP COLUMN wins,
    DROP COLUMN losses,
    DROP COLUMN ot_losses,
    DROP COLUMN shutouts,
    DROP COLUMN saves,
    DROP COLUMN shots,
    DROP COLUMN gaa,
    DROP COLUMN sv_pct;
-- +goose StatementEnd
