-- +goose Up
-- +goose StatementBegin

-- Replace Elite Prospects search-page links with direct player-page URLs.
-- EP moved player search behind a login wall, so the seeded
-- /search/player?q=... links dead-end for visitors. Player ids + slugs
-- resolved via EP's public autocomplete endpoint (2026-07-10) and each match
-- verified against birth year, position, and current club (which also
-- confirmed several 2026-27 moves: Misa on the Sharks roster, Wang to Boston
-- Univ., Kirsch to Quinnipiac, Klee to Notre Dame, Knowling to Saginaw/OHL).

UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/885160/haoxi-wang'
 WHERE full_name = 'Haoxi (Simon) Wang';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/717311/christian-kirsch'
 WHERE full_name = 'Christian Kirsch';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/597550/carson-wetsch'
 WHERE full_name = 'Carson Wetsch';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/727567/max-heise'
 WHERE full_name = 'Max Heise';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/817695/joshua-ravensbergen'
 WHERE full_name = 'Joshua Ravensbergen';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/576994/teddy-mutryn'
 WHERE full_name = 'Teddy Mutryn';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/577184/michael-misa'
 WHERE full_name = 'Michael Misa';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/685701/quentin-musty'
 WHERE full_name = 'Quentin Musty';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/578760/filip-bystedt'
 WHERE full_name = 'Filip Bystedt';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/603638/cameron-lund'
 WHERE full_name = 'Cameron Lund';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/779993/igor-chernyshov'
 WHERE full_name = 'Igor Chernyshov';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/529803/luca-cagnoni'
 WHERE full_name = 'Luca Cagnoni';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/577575/mattias-havelid'
 WHERE full_name = 'Mattias Hävelid';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/201866/ethan-cardwell'
 WHERE full_name = 'Ethan Cardwell';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/476029/zack-ostapchuk'
 WHERE full_name = 'Zack Ostapchuk';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/482413/nolan-allan'
 WHERE full_name = 'Nolan Allan';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/656832/eric-pohlkamp'
 WHERE full_name = 'Eric Pohlkamp';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/628112/ryan-lin'
 WHERE full_name = 'Ryan Lin';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/888345/jake-gustafson'
 WHERE full_name = 'Jake Gustafson';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/1077286/alexander-karmanov'
 WHERE full_name = 'Alexander Karmanov';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/577022/cole-mckinney'
 WHERE full_name = 'Cole McKinney';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/878326/keaton-verhoeff'
 WHERE full_name = 'Keaton Verhoeff';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/674032/joey-muldowney'
 WHERE full_name = 'Joey Muldowney';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/481354/reese-laubach'
 WHERE full_name = 'Reese Laubach';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/748893/richard-gallant'
 WHERE full_name = 'Richard Gallant';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/671535/colton-roberts'
 WHERE full_name = 'Colton Roberts';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/647080/nate-misskey'
 WHERE full_name = 'Nate Misskey';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/655167/michael-fisher'
 WHERE full_name = 'Michael Fisher';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/746367/david-klee'
 WHERE full_name = 'David Klee';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/512184/andre-gasseau'
 WHERE full_name = 'Andre Gasseau';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/492134/eli-barnett'
 WHERE full_name = 'Eli Barnett';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/689912/ivar-stenberg'
 WHERE full_name = 'Ivar Stenberg';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/618999/leo-sahlin-wallenius'
 WHERE full_name = 'Leo Sahlin Wallenius';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/708476/axel-landen'
 WHERE full_name = 'Axel Landén';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/779987/yegor-rimashevsky'
 WHERE full_name = 'Yegor Rimashevsky';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/882911/ilyas-magomedsultanov'
 WHERE full_name = 'Ilyas Magomedsultanov';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/482887/yegor-spiridonov'
 WHERE full_name = 'Yegor Spiridonov';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/564061/phillip-sinn'
 WHERE full_name = 'Phillip Sinn';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/780015/yaroslav-korostelyov'
 WHERE full_name = 'Yaroslav Korostelyov';
UPDATE prospects SET eliteprospects_url = 'https://www.eliteprospects.com/player/987192/brady-knowling'
 WHERE full_name = 'Brady Knowling';
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
-- Restore the search-style links (previous seed convention).
UPDATE prospects
   SET eliteprospects_url =
       'https://www.eliteprospects.com/search/player?q='
       || replace(regexp_replace(full_name, '\s*\([^)]*\)\s*', ' ', 'g'), ' ', '+');
-- +goose StatementEnd
