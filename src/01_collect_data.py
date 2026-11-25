
import pandas as pd
import requests
from io import StringIO
from pathlib import Path

# Official Montana State basketball statistics
url = "https://msubobcats.com/sports/mens-basketball/stats/2025-26"

# Download webpage
response = requests.get(url, timeout=30)
response.raise_for_status()

# Extract HTML tables
tables = pd.read_html(StringIO(response.text))

# Assign each table to a DataFrame
player_stats = tables[0]
team_stats = tables[1]
game_stats = tables[2]
season_highs = tables[3]

# Create raw data folder
output_folder = Path("data/raw")
output_folder.mkdir(parents=True, exist_ok=True)

# Save all four datasets
player_stats.to_csv(output_folder / "player_stats_2025_26.csv", index=False)
team_stats.to_csv(output_folder / "team_stats_2025_26.csv", index=False)
game_stats.to_csv(output_folder / "game_stats_2025_26.csv", index=False)
season_highs.to_csv(output_folder / "season_highs_2025_26.csv", index=False)

# Confirm successful collection
print("Data collection complete!")

print("\nDataset dimensions:")
print("Player statistics:", player_stats.shape)
print("Team statistics:", team_stats.shape)
print("Game statistics:", game_stats.shape)
print("Season highs:", season_highs.shape)

# Inspect game statistics
print("\nFirst five games:")
print(game_stats.head().to_string(index=False))

print("\nLast five rows:")
print(game_stats.tail().to_string(index=False))

print("\nGame results:")
print(game_stats["W/L"].value_counts(dropna=False))

print("\nAll datasets saved to data/raw.")
