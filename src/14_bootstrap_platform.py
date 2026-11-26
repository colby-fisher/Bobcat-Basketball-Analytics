
import subprocess
import sys
import time

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

DATABASE = ROOT / "data" / "bobcat_analytics.db"

# Prevent accidental rebuilding of an existing platform
if DATABASE.exists():
    print("An existing database was found.")
    print("Use src/13_update_platform.py instead.")
    sys.exit(0)

# Create required project directories
directories = [
    "data/raw",
    "data/cleaned",
    "reports",
    "visualizations",
    "notebooks"
]

for directory in directories:
    (ROOT / directory).mkdir(
        parents=True,
        exist_ok=True
    )

# Complete initialization pipeline
steps = [
    (
        "Collect historical data",
        "01_collect_data.py"
    ),
    (
        "Clean historical data",
        "02_clean_data.py"
    ),
    (
        "Calculate advanced metrics",
        "03_advanced_metrics.py"
    ),
    (
        "Analyze team performance",
        "04_team_analysis.py"
    ),
    (
        "Analyze historical players",
        "05_player_analysis.py"
    ),
    (
        "Collect historical box scores",
        "06_collect_box_scores.py"
    ),
    (
        "Build historical game database",
        "07_build_game_database.py"
    ),
    (
        "Calculate Four Factors",
        "08_four_factors.py"
    ),
    (
        "Build opponent scouting profiles",
        "09_opponent_scouting.py"
    ),
    (
        "Update current season and SQLite database",
        "13_update_platform.py"
    )
]

start = time.perf_counter()

print("=" * 60, flush=True)
print("BOBCAT BASKETBALL ANALYTICS LAB", flush=True)
print("FULL PLATFORM INITIALIZATION", flush=True)
print("=" * 60, flush=True)

for i, (title, script) in enumerate(steps, 1):

    print("\n" + "=" * 60, flush=True)

    print(
        f"STEP {i}/{len(steps)}: {title}",
        flush=True
    )

    print("=" * 60, flush=True)

    try:

        subprocess.run(
            [sys.executable, str(SRC / script)],
            cwd=ROOT,
            check=True
        )

    except subprocess.CalledProcessError:

        print(f"\nInitialization failed: {script}")
        sys.exit(1)

    print("\nStep completed successfully.")

if not DATABASE.exists():
    raise FileNotFoundError("Database was not created.")

elapsed = time.perf_counter() - start

print("\n" + "=" * 60)
print("PLATFORM INITIALIZATION SUCCESSFUL")
print("=" * 60)

print(f"Total initialization time: {elapsed:.2f} seconds")
print("Database:", DATABASE)

print("\nLaunch the dashboard with:")
print("streamlit run app.py")
