
import sqlite3
import pandas as pd

from pathlib import Path

# Project directories
ROOT = Path(__file__).resolve().parent.parent

DATA = ROOT / "data" / "cleaned"

DATABASE = ROOT / "data" / "bobcat_analytics.db"

# ==========================================
# LOAD GAME DATA
# ==========================================

historical_games = pd.read_csv(
    DATA / "four_factors_games_2025_26.csv"
)

current_games = pd.read_csv(
    DATA / "season_analysis_2026_27.csv"
)

historical_games["Season"] = "2025-26"
current_games["Season"] = "2026-27"

# Keep columns shared by both seasons
common_columns = [
    column for column in historical_games.columns
    if column in current_games.columns
]

games = pd.concat(
    [
        historical_games[common_columns],
        current_games[common_columns]
    ],
    ignore_index=True
)

# ==========================================
# LOAD PLAYER DATA
# ==========================================

historical_players = pd.read_csv(
    DATA / "advanced_player_stats_2025_26.csv"
)

current_players = pd.read_csv(
    DATA / "advanced_player_stats_2026_27.csv"
)

historical_players["Season"] = "2025-26"
current_players["Season"] = "2026-27"

players = pd.concat(
    [historical_players, current_players],
    ignore_index=True
)

# ==========================================
# LOAD SCOUTING DATA
# ==========================================

scouting = pd.read_csv(
    DATA / "big_sky_opponent_scouting.csv"
)

scouting["Season"] = "2025-26"

# ==========================================
# VALIDATE DATA
# ==========================================

assert not games.duplicated(
    subset=["Season", "Date"]
).any()

assert not players.duplicated(
    subset=["Season", "Player"]
).any()

assert not scouting.duplicated(
    subset=["Season", "Opponent"]
).any()

assert (
    games["MSU_Points"] -
    games["Opponent_Points"]
    == games["Point_Differential"]
).all()

for season in games["Season"].unique():

    game_points = games.loc[
        games["Season"] == season,
        "MSU_Points"
    ].sum()

    player_points = players.loc[
        players["Season"] == season,
        "PTS"
    ].sum()

    assert game_points == player_points

print("Data validation passed.")

# ==========================================
# CREATE SQLITE DATABASE
# ==========================================

with sqlite3.connect(DATABASE) as conn:

    games.to_sql(
        "games",
        conn,
        if_exists="replace",
        index=False
    )

    players.to_sql(
        "player_seasons",
        conn,
        if_exists="replace",
        index=False
    )

    scouting.to_sql(
        "opponent_scouting",
        conn,
        if_exists="replace",
        index=False
    )

    # Create database indexes
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_games_season_date
        ON games (Season, Date)
    """)

    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_players_season_name
        ON player_seasons (Season, Player)
    """)

    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_scouting_season_opponent
        ON opponent_scouting (Season, Opponent)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_games_opponent
        ON games (Opponent)
    """)

    print("\nBOBCAT ANALYTICS DATABASE")
    print("=" * 50)

    # Verify database tables
    tables = pd.read_sql_query("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """, conn)

    print("\nDatabase tables:")
    print(tables.to_string(index=False))

    # SQL QUERY 1: Season performance
    season_summary = pd.read_sql_query("""
        SELECT
            Season,
            COUNT(*) AS Games,
            SUM(CASE
                WHEN Result = 'W' THEN 1
                ELSE 0
            END) AS Wins,
            SUM(CASE
                WHEN Result = 'L' THEN 1
                ELSE 0
            END) AS Losses,
            ROUND(AVG(MSU_Points), 2) AS PPG,
            ROUND(AVG(Net_Rating), 2) AS Net_Rating
        FROM games
        GROUP BY Season
        ORDER BY Season
    """, conn)

    print("\nSeason performance:")
    print(season_summary.to_string(index=False))

    # SQL QUERY 2: Current-season scoring leaders
    scoring_leaders = pd.read_sql_query("""
        SELECT
            Player,
            GP,
            ROUND(PPG, 2) AS PPG,
            ROUND(TS_PCT, 2) AS True_Shooting
        FROM player_seasons
        WHERE Season = '2026-27'
        ORDER BY PPG DESC
        LIMIT 5
    """, conn)

    print("\nCurrent-season scoring leaders:")
    print(scoring_leaders.to_string(index=False))

    # SQL QUERY 3: Division I Four Factors
    factor_results = pd.read_sql_query("""
        SELECT
            Factors_Won,
            COUNT(*) AS Games,
            SUM(CASE
                WHEN Result = 'W' THEN 1
                ELSE 0
            END) AS Wins,
            ROUND(
                100.0 * SUM(CASE
                    WHEN Result = 'W' THEN 1
                    ELSE 0
                END) / COUNT(*),
                2
            ) AS Win_PCT
        FROM games
        WHERE Season = '2025-26'
          AND Division_I = 1
        GROUP BY Factors_Won
        ORDER BY Factors_Won
    """, conn)

    print("\nHistorical Four Factors results:")
    print(factor_results.to_string(index=False))

    # Verify database integrity
    integrity = conn.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

    assert integrity == "ok"

print("\nDATABASE SUMMARY")
print("=" * 50)

print("Game records:", len(games))
print("Player-season records:", len(players))
print("Scouting profiles:", len(scouting))
print("Database integrity:", integrity)

print("\nSQLite database successfully created!")
print("Location:", DATABASE)
