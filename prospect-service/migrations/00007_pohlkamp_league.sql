-- +goose Up
-- +goose StatementBegin

-- Pohlkamp's displayed 2025-26 season is his Univ. of Denver year (backfilled
-- in 00005 with the team_name override), but his prospect row said league
-- 'AHL' — so the board labeled NCAA production as AHL and a League=NCAA
-- filter omitted him. Label the row NCAA to match the season being shown.
-- When he debuts with the Barracuda (he signed after the college season),
-- flip league back to 'AHL' and wire his HockeyTech id in the same migration.
UPDATE prospects
   SET league = 'NCAA', team_name = 'Univ. of Denver'
 WHERE full_name = 'Eric Pohlkamp';

-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
UPDATE prospects
   SET league = 'AHL', team_name = 'San Jose Barracuda'
 WHERE full_name = 'Eric Pohlkamp';
-- +goose StatementEnd
