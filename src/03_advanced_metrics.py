
import pandas as pd
from pathlib import Path

# Load cleaned game data
df = pd.read_csv(
    "data/cleaned/game_stats_2025_26_cleaned.csv"
)

# Effective field goal percentage
df["eFG_PCT"] = (
    (df["FGM"] + 0.5 * df["3PM"]) / df["FGA"]
) * 100

# True shooting percentage
df["TS_PCT"] = (
    df["MSU_Points"] /
    (2 * (df["FGA"] + 0.44 * df["FTA"]))
) * 100

# Estimated offensive possessions (college basketball)
df["Possessions"] = (
    df["FGA"]
    - df["OREB"]
    + df["TOV"]
    + 0.475 * df["FTA"]
)

# Estimated offensive rating
df["ORtg"] = (
    df["MSU_Points"] / df["Possessions"]
) * 100

# Turnover percentage
df["TOV_PCT"] = (
    df["TOV"] / df["Possessions"]
) * 100

# Free throw attempt rate
df["FTr"] = (
    df["FTA"] / df["FGA"]
) * 100

# Three-point attempt rate
df["3PAr"] = (
    df["3PA"] / df["FGA"]
) * 100

# Assist-to-turnover ratio
df["AST_TO"] = (
    df["AST"] / df["TOV"].replace(0, float("nan"))
)

# Points per possession
df["PPP"] = (
    df["MSU_Points"] / df["Possessions"]
)

# Two-point field goals made and attempted
df["2PM"] = df["FGM"] - df["3PM"]
df["2PA"] = df["FGA"] - df["3PA"]

# Two-point field goal percentage
df["2P_PCT"] = (
    df["2PM"] / df["2PA"].replace(0, float("nan"))
) * 100

# Select advanced statistics
metrics = [
    "eFG_PCT",
    "TS_PCT",
    "Possessions",
    "ORtg",
    "TOV_PCT",
    "FTr",
    "3PAr",
    "AST_TO",
    "PPP",
    "2P_PCT"
]

# Validate key calculations
assert len(df) == 32
assert (df["Possessions"] > 0).all()
assert (df["2PM"] >= 0).all()
assert (df["2PA"] >= df["2PM"]).all()

# Compare average metrics in wins and losses
comparison = df.groupby("Result")[metrics].mean()

print("ADVANCED BASKETBALL ANALYTICS")
print("=" * 40)

print("\nSeason averages (mean of game metrics):")
print(df[metrics].mean().round(2))

print("\nWins vs. losses:")
print(comparison.round(2).T)

# Compare the difference between wins and losses
difference = comparison.loc["W"] - comparison.loc["L"]

print("\nDifference in wins compared to losses:")
print(difference.round(2))

# Find the five most efficient offensive games
print("\nTop five offensive performances:")

print(
    df.sort_values("ORtg", ascending=False)[
        [
            "Opponent",
            "Result",
            "MSU_Points",
            "eFG_PCT",
            "TS_PCT",
            "ORtg"
        ]
    ].head(5).round(2).to_string(index=False)
)

# Save enhanced dataset
output_folder = Path("data/cleaned")
output_folder.mkdir(parents=True, exist_ok=True)

df.to_csv(
    output_folder / "advanced_game_stats_2025_26.csv",
    index=False
)

# Save wins vs. losses comparison
comparison.to_csv(
    output_folder / "win_loss_comparison_2025_26.csv"
)

print("\nAdvanced metrics successfully calculated!")
print("Files successfully saved.")
