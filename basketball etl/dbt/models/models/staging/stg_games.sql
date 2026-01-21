WITH raw AS (
    SELECT
        payload -> 'response' AS games
    FROM raw_games
)

SELECT
    game ->> 'id' AS game_id,
    game -> 'league' ->> 'name' AS league,
    game -> 'teams' -> 'home' ->> 'name' AS home_team,
    game -> 'teams' -> 'away' ->> 'name' AS away_team,
    (game -> 'scores' -> 'home' ->> 'total')::INT AS home_score,
    (game -> 'scores' -> 'away' ->> 'total')::INT AS away_score
FROM raw,
     jsonb_array_elements(games) AS game
