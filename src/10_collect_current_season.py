
import pandas as pd
import requests
import re

from bs4 import BeautifulSoup
from io import StringIO
from pathlib import Path
from urllib.parse import urljoin, urlparse

# Season configuration
season = "2026-27"
season_file = season.replace("-", "_")

base_url = (
    "https://msubobcats.com/sports/mens-basketball"
)

stats_url = f"{base_url}/stats/{season}"

# Download current season statistics
response = requests.get(stats_url, timeout=30)
response.raise_for_status()

tables = pd.read_html(StringIO(response.text))

print("CURRENT SEASON DATA COLLECTION")
print("=" * 50)

print("\nSeason:", season)
print("Tables discovered:", len(tables))

# Inspect available tables
for i, table in enumerate(tables):
    print(f"Table {i}: {table.shape}")

# Identify game-by-game statistics
game_stats = next(
    table for table in tables
    if {"Opponent", "Date", "Score", "W/L"}
    .issubset(table.columns)
)

# Identify player statistics
player_stats = next(
    table for table in tables
    if ("Player name", "Player") in table.columns
)

# Identify team statistics
team_stats = next(
    table for table in tables
    if {"Montana St.", "Opponents"}
    .issubset(table.columns)
)

# Remove summary rows for inspection
completed = game_stats.dropna(
    subset=["Date", "W/L"]
).copy()

# Standardize game results
completed["Result"] = completed["W/L"].str[0]

# Confirm valid games
completed = completed[
    completed["Result"].isin(["W", "L"])
].copy()


# Identify completed game box score links
# Use the schedule page instead of the statistics page

schedule_url = f"{base_url}/schedule/{season}"

schedule_response = requests.get(
    schedule_url, timeout=30
)

schedule_response.raise_for_status()

soup = BeautifulSoup(
    schedule_response.text, "html.parser"
)

box_score_links = []

for link in soup.find_all("a", href=True):

    full_url = urljoin(schedule_url, link["href"])
    path = urlparse(full_url).path

    if re.search(
        r"/boxscore/\d+/?$",
        path,
        re.IGNORECASE
    ):

        if full_url not in box_score_links:
            box_score_links.append(full_url)

# Create output folder
output = Path("data/raw")
output.mkdir(parents=True, exist_ok=True)

# Save raw datasets
game_stats.to_csv(
    output / f"game_stats_{season_file}.csv",
    index=False
)

player_stats.to_csv(
    output / f"player_stats_{season_file}.csv",
    index=False
)

team_stats.to_csv(
    output / f"team_stats_{season_file}.csv",
    index=False
)

# Save box score links
pd.DataFrame({
    "Box_Score_URL": box_score_links
}).to_csv(
    output / f"box_score_links_{season_file}.csv",
    index=False
)

# Display current season information
print("\nCompleted games:", len(completed))

print("\nCurrent record:")
print(completed["Result"].value_counts())

print("\nGame results:")
print(
    completed[[
        "Date",
        "Opponent",
        "Score",
        "W/L"
    ]].to_string(index=False)
)

print("\nBox scores discovered:")
print(len(box_score_links))

for link in box_score_links:
    print(link)

print("\nDataset dimensions:")
print("Game statistics:", game_stats.shape)
print("Player statistics:", player_stats.shape)
print("Team statistics:", team_stats.shape)

# Check box score coverage
if len(box_score_links) == len(completed):

    print("\nBox score count matches game count.")

else:

    print("\nWARNING: Box score count mismatch.")
    print("Further inspection required.")

print("\nCurrent season collection complete!")
print("All datasets saved to data/raw.")
