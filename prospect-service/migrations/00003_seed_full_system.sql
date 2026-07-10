-- +goose Up
-- +goose StatementBegin

-- Full Sharks-system seed, curated from the Elite Prospects "in the system"
-- page (user-provided, 2026-07-09) down to drafted prospects + young
-- signings/acquisitions. AHL veterans / depth signings are intentionally
-- excluded (Barré-Boulet, Leason, Huntington, Felhaber, Giles, Hájek, Kaut,
-- Keyser).
--
-- Draft year/overall verified against records.nhl.com. Three players were
-- drafted by other clubs and acquired young — Allan (CHI 2021 #32),
-- Ostapchuk (OTT 2021 #39), Gasseau (BOS 2021 #213) — their real draft
-- slots are recorded.
--
-- HockeyTech player_ids confirmed by name+team in each league's live
-- 2025-26 top-scorers feed (ahl/whl/ohl). Goalies and NCAA/European players
-- are LINKOUT (the scorers feed is skaters-only and CHL/AHL-scoped).
-- Pohlkamp signed out of Denver too late to appear in the 2025-26 AHL
-- regular-season feed, so he's LINKOUT until next season's feed picks him up.

-- Backfill verified draft info for the slice-1 seed rows.
UPDATE prospects SET draft_year = 2024, draft_overall = 82  WHERE full_name = 'Carson Wetsch';
UPDATE prospects SET draft_year = 2025, draft_overall = 150 WHERE full_name = 'Max Heise';
UPDATE prospects SET draft_year = 2025, draft_overall = 95  WHERE full_name = 'Teddy Mutryn';
UPDATE prospects SET draft_year = 2025, draft_overall = 33  WHERE full_name = 'Haoxi (Simon) Wang';
UPDATE prospects SET draft_year = 2024, draft_overall = 116 WHERE full_name = 'Christian Kirsch';
UPDATE prospects SET draft_year = 2025, draft_overall = 30  WHERE full_name = 'Joshua Ravensbergen';

INSERT INTO prospects
    (full_name, position, draft_year, draft_overall, league, source, hockeytech_client_code, hockeytech_player_id, eliteprospects_url, team_name)
VALUES
    -- AHL (San Jose Barracuda) — live stats via the 'ahl' HockeyTech feed
    ('Michael Misa',          'C',  2025, 2,    'AHL',   'HOCKEYTECH', 'ahl', '10693',
        'https://www.eliteprospects.com/search/player?q=Michael+Misa',          'San Jose Barracuda'),
    ('Quentin Musty',         'LW', 2023, 26,   'AHL',   'HOCKEYTECH', 'ahl', '10234',
        'https://www.eliteprospects.com/search/player?q=Quentin+Musty',         'San Jose Barracuda'),
    ('Filip Bystedt',         'C',  2022, 27,   'AHL',   'HOCKEYTECH', 'ahl', '10086',
        'https://www.eliteprospects.com/search/player?q=Filip+Bystedt',         'San Jose Barracuda'),
    ('Cameron Lund',          'C',  2022, 34,   'AHL',   'HOCKEYTECH', 'ahl', '10692',
        'https://www.eliteprospects.com/search/player?q=Cameron+Lund',          'San Jose Barracuda'),
    ('Igor Chernyshov',       'LW', 2024, 33,   'AHL',   'HOCKEYTECH', 'ahl', '10494',
        'https://www.eliteprospects.com/search/player?q=Igor+Chernyshov',       'San Jose Barracuda'),
    ('Luca Cagnoni',          'D',  2023, 123,  'AHL',   'HOCKEYTECH', 'ahl', '10226',
        'https://www.eliteprospects.com/search/player?q=Luca+Cagnoni',          'San Jose Barracuda'),
    ('Mattias Hävelid',       'D',  2022, 45,   'AHL',   'HOCKEYTECH', 'ahl', '10699',
        'https://www.eliteprospects.com/search/player?q=Mattias+Havelid',       'San Jose Barracuda'),
    ('Ethan Cardwell',        'RW', 2021, 121,  'AHL',   'HOCKEYTECH', 'ahl', '9251',
        'https://www.eliteprospects.com/search/player?q=Ethan+Cardwell',        'San Jose Barracuda'),
    ('Zack Ostapchuk',        'C',  2021, 39,   'AHL',   'HOCKEYTECH', 'ahl', '9832',
        'https://www.eliteprospects.com/search/player?q=Zack+Ostapchuk',        'San Jose Barracuda'),
    ('Nolan Allan',           'D',  2021, 32,   'AHL',   'HOCKEYTECH', 'ahl', '9153',
        'https://www.eliteprospects.com/search/player?q=Nolan+Allan',           'San Jose Barracuda'),
    ('Eric Pohlkamp',         'D',  2023, 132,  'AHL',   'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Eric+Pohlkamp',         'San Jose Barracuda'),
    -- CHL
    ('Ryan Lin',              'D',  2026, 21,   'WHL',   'HOCKEYTECH', 'whl', '29532',
        'https://www.eliteprospects.com/search/player?q=Ryan+Lin',              'Vancouver Giants'),
    ('Jake Gustafson',        'F',  2026, 174,  'WHL',   'HOCKEYTECH', 'whl', '30280',
        'https://www.eliteprospects.com/search/player?q=Jake+Gustafson',        'Portland Winterhawks'),
    ('Alexander Karmanov',    'D',  2026, 201,  'OHL',   'HOCKEYTECH', 'ohl', '9480',
        'https://www.eliteprospects.com/search/player?q=Alexander+Karmanov',    'North Bay Battalion'),
    -- NCAA / USports
    ('Cole McKinney',         'C',  2025, 53,   'NCAA',  'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Cole+McKinney',         'Univ. of Michigan'),
    ('Keaton Verhoeff',       'D',  2026, 9,    'NCAA',  'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Keaton+Verhoeff',       'Univ. of North Dakota'),
    ('Joey Muldowney',        'RW', 2022, 172,  'NCAA',  'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Joey+Muldowney',        'Univ. of Connecticut'),
    ('Reese Laubach',         'C',  2022, 217,  'NCAA',  'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Reese+Laubach',         'Penn State Univ.'),
    ('Richard Gallant',       'LW', 2025, 210,  'NCAA',  'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Richard+Gallant',       'Harvard Univ.'),
    ('Colton Roberts',        'D',  2024, 131,  'NCAA',  'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Colton+Roberts',        'Colorado College'),
    ('Nate Misskey',          'D',  2024, 143,  'NCAA',  'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Nate+Misskey',          'UMass-Lowell'),
    ('Michael Fisher',        'D',  2022, 76,   'NCAA',  'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Michael+Fisher',        'Cornell Univ.'),
    ('David Klee',            'F',  2023, 196,  'NCAA',  'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=David+Klee',            'Univ. of North Dakota'),
    ('Andre Gasseau',         'C',  2021, 213,  'NCAA',  'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Andre+Gasseau',         'Boston College'),
    ('Eli Barnett',           'D',  2022, 195,  'USports', 'LINKOUT',  NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Eli+Barnett',           'Univ. of New Brunswick'),
    -- Europe
    ('Ivar Stenberg',         'LW', 2026, 2,    'SHL',   'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Ivar+Stenberg',         'Frölunda HC'),
    ('Leo Sahlin Wallenius',  'D',  2024, 53,   'SHL',   'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Leo+Sahlin+Wallenius',  'Växjö Lakers HC'),
    ('Axel Landén',           'D',  2023, 130,  'Liiga', 'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Axel+Landen',           'TPS'),
    ('Yegor Rimashevsky',     'RW', 2023, 203,  'KHL',   'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Yegor+Rimashevsky',     'Dynamo Moskva'),
    ('Ilyas Magomedsultanov', 'D',  2025, 115,  'MHL',   'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Ilyas+Magomedsultanov', 'Loko Yaroslavl'),
    ('Yegor Spiridonov',      'C',  2019, 108,  'VHL',   'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Yegor+Spiridonov',      'Yugra Khanty-Mansiysk'),
    ('Phillip Sinn',          'D',  NULL, NULL, 'DEL',   'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Phillip+Sinn',          'EHC München'),
    -- Goalies (LINKOUT until goalie stats land)
    ('Yaroslav Korostelyov',  'G',  2024, 194,  'MHL',   'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Yaroslav+Korostelyov',  'SKA-1946 St. Petersburg'),
    ('Brady Knowling',        'G',  2026, 127,  'NTDP',  'LINKOUT',    NULL,  NULL,
        'https://www.eliteprospects.com/search/player?q=Brady+Knowling',        'U.S. National U18 Team');

-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DELETE FROM prospects WHERE full_name IN (
    'Michael Misa', 'Quentin Musty', 'Filip Bystedt', 'Cameron Lund',
    'Igor Chernyshov', 'Luca Cagnoni', 'Mattias Hävelid', 'Ethan Cardwell',
    'Zack Ostapchuk', 'Nolan Allan', 'Eric Pohlkamp',
    'Ryan Lin', 'Jake Gustafson', 'Alexander Karmanov',
    'Cole McKinney', 'Keaton Verhoeff', 'Joey Muldowney', 'Reese Laubach',
    'Richard Gallant', 'Colton Roberts', 'Nate Misskey', 'Michael Fisher',
    'David Klee', 'Andre Gasseau', 'Eli Barnett',
    'Ivar Stenberg', 'Leo Sahlin Wallenius', 'Axel Landén', 'Yegor Rimashevsky',
    'Ilyas Magomedsultanov', 'Yegor Spiridonov', 'Phillip Sinn',
    'Yaroslav Korostelyov', 'Brady Knowling'
);
UPDATE prospects SET draft_year = NULL, draft_overall = NULL WHERE full_name IN (
    'Carson Wetsch', 'Max Heise', 'Teddy Mutryn', 'Haoxi (Simon) Wang',
    'Christian Kirsch', 'Joshua Ravensbergen'
);
-- +goose StatementEnd
