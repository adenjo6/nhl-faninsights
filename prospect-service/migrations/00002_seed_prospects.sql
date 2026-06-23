-- +goose Up
-- +goose StatementBegin

-- Curated Sharks prospect seed. Roster + leagues are user-verified; HockeyTech
-- player_ids were confirmed by name+team in each league's live feed.
--
-- Skaters are HOCKEYTECH (live current-season stats via the ingestion cron).
-- Goalies are LINKOUT for now: the bulk scorers feed is skaters-only and the
-- stats schema holds G/A/P, not GAA/SV% — live goalie stats are a fast follow.

INSERT INTO prospects
    (full_name, position, league, source, hockeytech_client_code, hockeytech_player_id, eliteprospects_url, team_name)
VALUES
    -- OHL
    ('Haoxi (Simon) Wang', 'D',  'OHL',   'HOCKEYTECH', 'ohl',   '9293',
        'https://www.eliteprospects.com/search/player?q=Haoxi+Wang',     'Niagara IceDogs'),
    ('Christian Kirsch',   'G',  'OHL',   'LINKOUT',    NULL,    NULL,
        'https://www.eliteprospects.com/search/player?q=Christian+Kirsch', 'Kitchener Rangers'),
    -- WHL
    ('Carson Wetsch',      'RW', 'WHL',   'HOCKEYTECH', 'whl',   '29129',
        'https://www.eliteprospects.com/search/player?q=Carson+Wetsch',  'Kelowna Rockets'),
    ('Max Heise',          'C',  'WHL',   'HOCKEYTECH', 'whl',   '30258',
        'https://www.eliteprospects.com/search/player?q=Max+Heise',      'Prince Albert Raiders'),
    ('Joshua Ravensbergen','G',  'WHL',   'LINKOUT',    NULL,    NULL,
        'https://www.eliteprospects.com/search/player?q=Joshua+Ravensbergen', 'Prince George Cougars'),
    -- QMJHL
    ('Teddy Mutryn',       'F',  'QMJHL', 'HOCKEYTECH', 'lhjmq', '20414',
        'https://www.eliteprospects.com/search/player?q=Teddy+Mutryn',   'Moncton Wildcats');

-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DELETE FROM prospects WHERE full_name IN (
    'Haoxi (Simon) Wang', 'Christian Kirsch', 'Carson Wetsch',
    'Max Heise', 'Joshua Ravensbergen', 'Teddy Mutryn'
);
-- +goose StatementEnd
