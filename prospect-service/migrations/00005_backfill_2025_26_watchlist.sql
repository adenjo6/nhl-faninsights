-- +goose Up
-- +goose StatementBegin

-- One-time backfill of final 2025-26 season lines for the LINKOUT watch list
-- (NCAA / USports / SHL / Liiga / DEL / KHL / MHL / VHL). The season is over
-- everywhere, so these totals are final; the daily ingest only touches
-- HOCKEYTECH prospects and will never overwrite them. When the 2026-27 season
-- label takes over, these rows simply stop joining and any player still
-- without a live feed returns to the watch list.
--
-- Sources (fetched + verified 2026-07-10): NCAA from collegehockeynews.com
-- team season tables; UNB from goredsgo.ca; SHL from shl.se statistics-v2
-- API; Liiga from liiga.fi API; DEL from penny-del.org player details; KHL
-- from the official mobile JSON API; MHL/VHL from mhl.khl.ru / vhlru.ru
-- player pages. Cross-checked against independent reports where available.
--
-- Not covered: Brady Knowling (NTDP/USHL) — no accessible stats source; he
-- stays on the watch list.
--
-- Pohlkamp's line is his Univ. of Denver NCAA season (he signed with the
-- Barracuda after it ended); the row's team_name override shows Denver.
-- Korostelyov's MHL feed reports W/L only — one of his 20 GP was a
-- no-decision, and OT losses aren't broken out (NULL renders as 0).

INSERT INTO prospect_season_stats
    (prospect_id, season, team_name, games_played, goals, assists, points, plus_minus, pim)
VALUES
    -- NCAA
    ((SELECT id FROM prospects WHERE full_name = 'Cole McKinney'),        '2025-26', 'Univ. of Michigan',      40,  8, 12, 20,   2, 28),
    ((SELECT id FROM prospects WHERE full_name = 'Keaton Verhoeff'),      '2025-26', 'Univ. of North Dakota',  36,  6, 14, 20,   7, 29),
    ((SELECT id FROM prospects WHERE full_name = 'Joey Muldowney'),       '2025-26', 'Univ. of Connecticut',   34, 17, 12, 29,  11, 25),
    ((SELECT id FROM prospects WHERE full_name = 'Richard Gallant'),      '2025-26', 'Harvard Univ.',          34,  8, 10, 18,  -9, 21),
    ((SELECT id FROM prospects WHERE full_name = 'Andre Gasseau'),        '2025-26', 'Boston College',         23,  6, 17, 23,  -2, 12),
    ((SELECT id FROM prospects WHERE full_name = 'Colton Roberts'),       '2025-26', 'Colorado College',       29,  3,  8, 11,  -2, 16),
    ((SELECT id FROM prospects WHERE full_name = 'Michael Fisher'),       '2025-26', 'Cornell Univ.',          33,  1,  7,  8,  12, 14),
    ((SELECT id FROM prospects WHERE full_name = 'Eric Pohlkamp'),        '2025-26', 'Univ. of Denver',        43, 18, 21, 39,  24, 33),
    ((SELECT id FROM prospects WHERE full_name = 'Nate Misskey'),         '2025-26', 'UMass-Lowell',           35,  4,  6, 10,  -6, 14),
    ((SELECT id FROM prospects WHERE full_name = 'David Klee'),           '2025-26', 'Univ. of North Dakota',  24,  3,  3,  6,   4, 14),
    ((SELECT id FROM prospects WHERE full_name = 'Reese Laubach'),        '2025-26', 'Penn State Univ.',       37, 12, 16, 28,  -5, 30),
    -- USports
    ((SELECT id FROM prospects WHERE full_name = 'Eli Barnett'),          '2025-26', 'Univ. of New Brunswick', 28,  0,  8,  8,  17, 28),
    -- Europe
    ((SELECT id FROM prospects WHERE full_name = 'Ivar Stenberg'),        '2025-26', 'Frölunda HC',            43, 11, 22, 33,  10,  6),
    ((SELECT id FROM prospects WHERE full_name = 'Leo Sahlin Wallenius'), '2025-26', 'Växjö Lakers HC',        32,  3, 10, 13,   3, 14),
    ((SELECT id FROM prospects WHERE full_name = 'Axel Landén'),          '2025-26', 'TPS',                    57,  2,  6,  8,   6, 34),
    ((SELECT id FROM prospects WHERE full_name = 'Phillip Sinn'),         '2025-26', 'EHC München',            35,  1,  2,  3,   6, 18),
    ((SELECT id FROM prospects WHERE full_name = 'Yegor Rimashevsky'),    '2025-26', 'Dynamo Moskva',          61, 10,  2, 12,  -3,  6),
    ((SELECT id FROM prospects WHERE full_name = 'Ilyas Magomedsultanov'),'2025-26', 'Loko Yaroslavl',         27,  1, 10, 11,  22, 14),
    ((SELECT id FROM prospects WHERE full_name = 'Yegor Spiridonov'),     '2025-26', 'Yugra Khanty-Mansiysk',  56,  4,  6, 10,   5, 27);

INSERT INTO prospect_season_stats
    (prospect_id, season, team_name, games_played, wins, losses, ot_losses, shutouts, saves, shots, gaa, sv_pct)
VALUES
    ((SELECT id FROM prospects WHERE full_name = 'Yaroslav Korostelyov'), '2025-26', 'SKA-1946 St. Petersburg',
        20, 14, 5, NULL, 5, 433, 472, 2.22, 0.917);

-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DELETE FROM prospect_season_stats
 WHERE season = '2025-26'
   AND prospect_id IN (
       SELECT id FROM prospects WHERE full_name IN (
           'Cole McKinney', 'Keaton Verhoeff', 'Joey Muldowney', 'Richard Gallant',
           'Andre Gasseau', 'Colton Roberts', 'Michael Fisher', 'Eric Pohlkamp',
           'Nate Misskey', 'David Klee', 'Reese Laubach', 'Eli Barnett',
           'Ivar Stenberg', 'Leo Sahlin Wallenius', 'Axel Landén', 'Phillip Sinn',
           'Yegor Rimashevsky', 'Ilyas Magomedsultanov', 'Yegor Spiridonov',
           'Yaroslav Korostelyov'
       )
   );
-- +goose StatementEnd
