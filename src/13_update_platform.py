
import subprocess
import sys
import time
import shutil
import pandas as pd

from pathlib import Path
from datetime import datetime

# Project directories
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DATA = ROOT / "data"

SEASON = "2026-27"

DATABASE = DATA / "bobcat_analytics.db"

BACKUP = DATA / "bobcat_analytics.backup.db"

GAME_FILE = (
    DATA / "cleaned" / "season_analysis_2026_27.csv"
)

PLAYER_FILE = (
    DATA / "cleaned" / "advanced_player_stats_2026_27.csv"
)

LINK_FILE = (
    DATA / "raw" / "box_score_links_2026_27.csv"
)


# ==========================================
# SCRIPT EXECUTION HELPER
# ==========================================

def run_step(title, script, *args):

    print("\n" + "=" * 60, flush=True)
    print(title, flush=True)
    print("=" * 60, flush=True)

    start = time.perf_counter()

    subprocess.run(
        [
            sys.executable,
            str(SRC / script),
            *args
        ],
        cwd=ROOT,
        check=True
    )

    elapsed = time.perf_counter() - start

    print(f"\nStep completed in {elapsed:.2f} seconds.")


# ==========================================
# PLATFORM UPDATE
# ==========================================

def main():

    start = time.perf_counter()

    print("=" * 60)
    print("BOBCAT BASKETBALL ANALYTICS LAB")
    print("AUTOMATED PLATFORM UPDATE")
    print("=" * 60)

    print(
        "Update started:",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    print("Season:", SEASON)

    previous_games = 0

    if GAME_FILE.exists():
        previous_games = len(pd.read_csv(GAME_FILE))

    print("Previous game count:", previous_games)

    # Back up existing database
    if DATABASE.exists():

        shutil.copy2(DATABASE, BACKUP)

        print("Database backup created.")

    database_rebuild_started = False

    try:

        # STEP 1: Collect new data
        run_step(
            "STEP 1: Collect current-season data",
            "10_collect_current_season.py"
        )

        # STEP 2: Process game data
        run_step(
            "STEP 2: Process game statistics",
            "11_process_season.py",
            SEASON
        )

        # STEP 3: Process player data
        run_step(
            "STEP 3: Update player analytics",
            "05_player_analysis.py",
            SEASON
        )

        # STEP 4: Validate updated data
        print("\n" + "=" * 60)
        print("STEP 4: Validate updated datasets")
        print("=" * 60)

        games = pd.read_csv(GAME_FILE)
        players = pd.read_csv(PLAYER_FILE)
        links = pd.read_csv(LINK_FILE)

        if games.empty or players.empty:

            raise ValueError(
                "An updated dataset is empty."
            )

        if len(games) < previous_games:

            raise ValueError(
                "Updated dataset contains fewer games."
            )

        if len(games) != len(links):

            raise ValueError(
                "Game count does not match box-score count."
            )

        if games["Date"].duplicated().any():

            raise ValueError(
                "Duplicate game dates detected."
            )

        if games["MSU_Points"].sum() != players["PTS"].sum():

            raise ValueError(
                "Player and team scoring totals do not match."
            )

        print("Game validation passed.")
        print("Player validation passed.")
        print("Scoring totals matched.")

        # Identify unverified opponents
        division_status = (
            games["Division_I"]
            .astype(str)
            .str.lower()
        )

        known_values = [
            "true", "false", "1", "0", "1.0", "0.0"
        ]

        unverified = games[
            ~division_status.isin(known_values)
        ]

        if not unverified.empty:

            print("\nWARNING: Unverified opponents:")

            print(
                unverified[["Date", "Opponent"]]
                .to_string(index=False)
            )

        # STEP 5: Rebuild the database
        database_rebuild_started = True

        run_step(
            "STEP 5: Rebuild SQLite database",
            "12_build_database.py"
        )

        # ==================================
        # FINAL UPDATE SUMMARY
        # ==================================

        wins = (games["Result"] == "W").sum()
        losses = (games["Result"] == "L").sum()

        new_games = len(games) - previous_games

        latest_game = games.loc[
            pd.to_datetime(games["Date"]).idxmax()
        ]

        elapsed = time.perf_counter() - start

        print("\n" + "=" * 60)
        print("PLATFORM UPDATE SUCCESSFUL")
        print("=" * 60)

        print("Season:", SEASON)
        print("Total games:", len(games))
        print("New games added:", new_games)
        print("Record:", f"{wins}-{losses}")
        print("Players:", len(players))

        print("\nLatest game:")
        print("Date:", latest_game["Date"])
        print("Opponent:", latest_game["Opponent"])
        print("Result:", latest_game["Result"])

        print(
            "Score:",
            f"{latest_game['MSU_Points']}-"
            f"{latest_game['Opponent_Points']}"
        )

        print(
            "Average points:",
            round(games["MSU_Points"].mean(), 2)
        )

        print(
            "Average net rating:",
            round(games["Net_Rating"].mean(), 2)
        )

        print(f"\nTotal update time: {elapsed:.2f} seconds")

        print("\nDashboard data is ready.")
        print("Click 'Reload local data' in Streamlit.")

    except Exception as error:

        print("\n" + "=" * 60)
        print("PLATFORM UPDATE FAILED")
        print("=" * 60)

        print("Error:", error)

        if database_rebuild_started and BACKUP.exists():

            shutil.copy2(BACKUP, DATABASE)

            print("Previous database restored.")

        print("Intermediate CSV files may have changed.")
        print("Resolve the error before running again.")

        sys.exit(1)


if __name__ == "__main__":
    main()
