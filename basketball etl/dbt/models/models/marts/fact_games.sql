SELECT
    game_id,
    league,
    home_team,
    away_team,
    home_score,
    away_score,
    CASE
        WHEN home_score > away_score THEN home_team
        ELSE away_team
    END AS winner
FROM {{ ref('stg_games') }}
