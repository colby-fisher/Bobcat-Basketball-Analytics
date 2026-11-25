
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Season configuration
season = sys.argv[1] if len(sys.argv) > 1 else "2025-26"
season_file = season.replace("-", "_")
# Load player statistics with two header rows
df = pd.read_csv(
    f"data/raw/player_stats_{season_file}.csv",
    header=[0, 1],
    dtype=str
)

# Select and rename important columns
columns = {
    ("Player uniform", "#"): "Jersey",
    ("Player name", "Player"): "Player",
    ("GP", "GP"): "GP",
    ("GS", "GS"): "GS",
    ("MINUTES", "MIN"): "MIN",
    ("SCORING", "PTS"): "PTS",
    ("FG", "FGM"): "FGM",
    ("FG", "FGA"): "FGA",
    ("3PT", "3PT"): "3PM",
    ("3PT", "3PTA"): "3PA",
    ("FT", "FTM"): "FTM",
    ("FT", "FTA"): "FTA",
    ("REBOUNDS", "OFF"): "OREB",
    ("REBOUNDS", "DEF"): "DREB",
    ("REBOUNDS", "TOT"): "REB",
    ("PF", "PF"): "PF",
    ("AST", "AST"): "AST",
    ("TO", "TO"): "TOV",
    ("STL", "STL"): "STL",
    ("BLK", "BLK"): "BLK"
}

df = df[list(columns.keys())].copy()
df.columns = list(columns.values())

# Identify individual players by jersey number
player_mask = (
    df["Jersey"].str.strip()
    .str.fullmatch(r"\d+", na=False)
)

print("Excluded summary rows:")
print(df.loc[~player_mask, ["Jersey", "Player"]])

df = df[player_mask].copy()

# Convert counting statistics to numeric values
numeric_columns = [
    "GP", "GS", "PTS", "FGM", "FGA",
    "3PM", "3PA", "FTM", "FTA",
    "OREB", "DREB", "REB",
    "AST", "TOV", "STL", "BLK", "PF"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column], errors="raise"
    )

# Validate player statistics
assert len(df) > 0
assert df[numeric_columns].notna().all().all()
assert (df["GP"] > 0).all()
assert (df["FGM"] <= df["FGA"]).all()
assert (df["3PM"] <= df["3PA"]).all()
assert (df["FTM"] <= df["FTA"]).all()


# Verify scoring totals
assert (
    2 * df["FGM"] + df["3PM"] + df["FTM"]
    == df["PTS"]
).all()

# Verify player scoring totals against team scoring
games = pd.read_csv(
    f"data/raw/game_stats_{season_file}.csv"
)

games = games.dropna(subset=["Date", "W/L"])

games = games[
    games["W/L"].str[0].isin(["W", "L"])
]

team_points = pd.to_numeric(games["PTS"]).sum()

assert df["PTS"].sum() == team_points, (
    "Player and team scoring totals do not match."
)

print("Player and team scoring totals verified.")


# Traditional per-game statistics
df["PPG"] = df["PTS"] / df["GP"]
df["RPG"] = df["REB"] / df["GP"]
df["APG"] = df["AST"] / df["GP"]
df["SPG"] = df["STL"] / df["GP"]
df["BPG"] = df["BLK"] / df["GP"]

# Effective field goal percentage
df["eFG_PCT"] = (
    (df["FGM"] + 0.5 * df["3PM"])
    / df["FGA"].replace(0, float("nan"))
) * 100

# True shooting percentage
df["TS_PCT"] = (
    df["PTS"] /
    (2 * (df["FGA"] + 0.44 * df["FTA"]))
    .replace(0, float("nan"))
) * 100

# Three-point percentage
df["3P_PCT"] = (
    df["3PM"] /
    df["3PA"].replace(0, float("nan"))
) * 100

# Three-point attempt rate
df["3PAr"] = (
    df["3PA"] /
    df["FGA"].replace(0, float("nan"))
) * 100

# Assist-to-turnover ratio
df["AST_TO"] = (
    df["AST"] /
    df["TOV"].replace(0, float("nan"))
)

# Free throw attempt rate
df["FTr"] = (
    df["FTA"] /
    df["FGA"].replace(0, float("nan"))
) * 100

# Scoring volume
df["FGA_Per_Game"] = df["FGA"] / df["GP"]

# Minimum shooting sample for efficiency comparisons
df["Qualified"] = df["FGA"] >= 50

qualified = df[df["Qualified"]].copy()

print("\nMONTANA STATE PLAYER ANALYSIS")
print("=" * 45)

print("\nPlayers analyzed:", len(df))

print("\nTotal player points:", df["PTS"].sum())

print("\nPlayer scoring leaders:")

print(
    df.sort_values("PPG", ascending=False)[
        ["Player", "GP", "PPG", "RPG",
         "APG", "TS_PCT"]
    ].round(2).to_string(index=False)
)

print("\nMost efficient scorers:")
print("Minimum 50 field goal attempts")

print(
    qualified.sort_values(
        "TS_PCT", ascending=False
    )[
        ["Player", "FGA", "PPG",
         "eFG_PCT", "TS_PCT"]
    ].round(2).to_string(index=False)
)

print("\nThree-point shooting profiles:")

print(
    df.sort_values("3PA", ascending=False)[
        ["Player", "3PM", "3PA",
         "3P_PCT", "3PAr"]
    ].round(2).to_string(index=False)
)

print("\nPlaymaking profiles:")

print(
    df.sort_values("AST", ascending=False)[
        ["Player", "AST", "TOV",
         "APG", "AST_TO"]
    ].round(2).to_string(index=False)
)

# Save cleaned player statistics
output = Path("data/cleaned")
output.mkdir(parents=True, exist_ok=True)

df.to_csv(
    output / f"advanced_player_stats_{season_file}.csv",
    index=False
)

# Create scoring efficiency visualization
visualizations = Path("visualizations")
visualizations.mkdir(parents=True, exist_ok=True)

plt.figure(figsize=(12, 8))

plt.scatter(
    qualified["FGA_Per_Game"],
    qualified["TS_PCT"],
    color="#002D56",
    edgecolor="#B9975B",
    linewidth=2,
    s=150
)

# Add player labels
for _, player in qualified.iterrows():
    plt.annotate(
        player["Player"],
        (
            player["FGA_Per_Game"],
            player["TS_PCT"]
        ),
        xytext=(5, 5),
        textcoords="offset points",
        fontsize=9
    )

# Qualified-player averages
plt.axhline(
    qualified["TS_PCT"].mean(),
    color="gray",
    linestyle="--",
    alpha=0.6
)

plt.axvline(
    qualified["FGA_Per_Game"].mean(),
    color="gray",
    linestyle="--",
    alpha=0.6
)

plt.title(
    f"Montana State Basketball | {season}\n"
    "Player Scoring Volume vs. Efficiency"
)

plt.xlabel("Field Goal Attempts Per Game")
plt.ylabel("True Shooting Percentage (%)")
plt.grid(alpha=0.15)
plt.tight_layout()

plt.savefig(
    visualizations / f"player_scoring_efficiency_{season_file}.png",
    dpi=300
)

plt.close()

print("\nPlayer analysis complete!")
print("Dataset and visualization saved.")
