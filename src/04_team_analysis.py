
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Load advanced basketball statistics
df = pd.read_csv(
    "data/cleaned/advanced_game_stats_2025_26.csv"
)

# Identify non-Division I opponents
# Source: Montana State Athletics, December 21, 2025
non_d1 = [
    "Northwest Indian",
    "Nobel",
    "Northwest (WA)"
]

# Classify opponents
df["Division_I"] = ~df["Opponent"].isin(non_d1)

# Create Division I dataset
d1 = df[df["Division_I"]].copy()

# Validate game counts
assert len(df) == 32
assert len(d1) == 29
assert (d1["Result"] == "W").sum() == 15
assert (d1["Result"] == "L").sum() == 14

# Select important performance metrics
metrics = [
    "MSU_Points",
    "Opponent_Points",
    "Point_Differential",
    "eFG_PCT",
    "TS_PCT",
    "Possessions",
    "ORtg",
    "TOV_PCT",
    "FTr",
    "3PAr",
    "AST_TO",
    "2P_PCT"
]

# Compare full season and Division I performance
season_comparison = pd.DataFrame({
    "All Games": df[metrics].mean(),
    "Division I Only": d1[metrics].mean()
})

print("MONTANA STATE TEAM ANALYSIS")
print("=" * 45)

print("\nNon-Division I games:")
print(
    df[~df["Division_I"]][
        ["Opponent", "MSU_Points",
         "Opponent_Points", "ORtg"]
    ].round(2).to_string(index=False)
)

print("\nSeason comparison:")
print(season_comparison.round(2))

# Compare Division I wins and losses
comparison = d1.groupby("Result")[metrics].mean().T

comparison["Difference"] = (
    comparison["W"] - comparison["L"]
)

print("\nDivision I wins vs. losses:")
print(comparison.round(2))

# Investigate statistical relationships
correlation_metrics = [
    "Point_Differential",
    "eFG_PCT",
    "TS_PCT",
    "Possessions",
    "ORtg",
    "TOV_PCT",
    "FTr",
    "3PAr",
    "AST_TO",
    "2P_PCT",
    "OREB",
    "DREB",
    "AST",
    "STL",
    "BLK",
    "PF"
]

correlations = (
    d1[correlation_metrics]
    .corr()["Point_Differential"]
    .drop("Point_Differential")
    .sort_values(ascending=False)
)

print("\nCorrelations with point differential:")
print(correlations.round(3))

# Create visualization folder
output = Path("visualizations")
output.mkdir(parents=True, exist_ok=True)

# Montana State-inspired colors
navy = "#002D56"
gold = "#B9975B"

# Separate wins and losses
wins = d1[d1["Result"] == "W"]
losses = d1[d1["Result"] == "L"]

# Create shooting efficiency scatter plot
plt.figure(figsize=(10, 6))

plt.scatter(
    wins["eFG_PCT"],
    wins["Point_Differential"],
    color=navy,
    label="Wins",
    s=80,
    alpha=0.8
)

plt.scatter(
    losses["eFG_PCT"],
    losses["Point_Differential"],
    color=gold,
    label="Losses",
    s=80,
    alpha=0.8
)

plt.axhline(
    y=0,
    color="gray",
    linestyle="--"
)

plt.title(
    "Montana State Basketball | 2025-26\n"
    "Shooting Efficiency vs. Scoring Margin"
)

plt.xlabel("Effective Field Goal Percentage (%)")
plt.ylabel("Point Differential")
plt.legend()
plt.grid(alpha=0.15)
plt.tight_layout()

plt.savefig(
    output / "shooting_efficiency_vs_margin.png",
    dpi=300
)

plt.close()

# Create wins vs. losses comparison chart
chart_metrics = [
    "eFG_PCT",
    "TS_PCT",
    "2P_PCT",
    "3PAr",
    "FTr",
    "TOV_PCT"
]

chart_data = d1.groupby("Result")[chart_metrics].mean().T

chart_data = chart_data[["W", "L"]]

chart_data.index = [
    "Effective FG%",
    "True Shooting%",
    "Two-Point FG%",
    "Three-Point Attempt Rate",
    "Free Throw Attempt Rate",
    "Turnover Rate"
]

chart_data.plot(
    kind="barh",
    figsize=(11, 7),
    color=[navy, gold]
)

plt.title(
    "Montana State Basketball | 2025-26\n"
    "Division I Wins vs. Losses"
)

plt.xlabel("Percentage (%)")
plt.ylabel("")
plt.legend(["Wins", "Losses"])
plt.grid(axis="x", alpha=0.15)
plt.tight_layout()

plt.savefig(
    output / "division1_wins_vs_losses.png",
    dpi=300
)

plt.close()

# Save analysis datasets
df.to_csv(
    "data/cleaned/classified_games_2025_26.csv",
    index=False
)

d1.to_csv(
    "data/cleaned/division1_games_2025_26.csv",
    index=False
)

season_comparison.to_csv(
    "data/cleaned/season_comparison_2025_26.csv"
)

comparison.to_csv(
    "data/cleaned/division1_win_loss_comparison.csv"
)

correlations.to_csv(
    "data/cleaned/performance_correlations.csv"
)

print("\nTeam analysis complete!")
print("Datasets and visualizations successfully saved.")
