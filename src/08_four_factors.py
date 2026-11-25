
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Load complete game database
df = pd.read_csv(
    "data/cleaned/complete_game_database_2025_26.csv"
)

# Estimate opponent possessions
df["Opp_Possessions"] = (
    df["Opp_FGA"]
    - df["Opp_OREB"]
    + df["Opp_TOV"]
    + 0.475 * df["Opp_FTA"]
)

# Shared estimate of game possessions
df["Game_Possessions"] = (
    df["Possessions"] + df["Opp_Possessions"]
) / 2

# Calculate offensive and defensive ratings
df["Off_Rating"] = (
    df["MSU_Points"] / df["Game_Possessions"]
) * 100

df["Def_Rating"] = (
    df["Opponent_Points"] / df["Game_Possessions"]
) * 100

df["Net_Rating"] = (
    df["Off_Rating"] - df["Def_Rating"]
)

# FOUR FACTORS

# Factor 1: Shooting efficiency
df["Opp_eFG_PCT"] = (
    (df["Opp_FGM"] + 0.5 * df["Opp_3PM"])
    / df["Opp_FGA"]
) * 100

# Factor 2: Turnover percentage
df["Opp_TOV_PCT"] = (
    df["Opp_TOV"] / df["Opp_Possessions"]
) * 100

# Factor 3: Offensive rebounding percentage
df["ORB_PCT"] = (
    df["OREB"] /
    (df["OREB"] + df["Opp_DREB"])
) * 100

df["Opp_ORB_PCT"] = (
    df["Opp_OREB"] /
    (df["Opp_OREB"] + df["DREB"])
) * 100

# Defensive rebounding percentage
df["DRB_PCT"] = (
    df["DREB"] /
    (df["DREB"] + df["Opp_OREB"])
) * 100

# Factor 4: Free throw scoring rate
df["FT_Rate"] = (
    df["FTM"] / df["FGA"]
) * 100

df["Opp_FT_Rate"] = (
    df["Opp_FTM"] / df["Opp_FGA"]
) * 100

# Additional defensive statistics
df["Opp_FG_PCT"] = (
    df["Opp_FGM"] / df["Opp_FGA"]
) * 100

df["Opp_3P_PCT"] = (
    df["Opp_3PM"] /
    df["Opp_3PA"].replace(0, float("nan"))
) * 100

df["Opp_3PAr"] = (
    df["Opp_3PA"] / df["Opp_FGA"]
) * 100

# Calculate Four Factors advantages
# Positive values always favor Montana State

df["Shooting_Advantage"] = (
    df["eFG_PCT"] - df["Opp_eFG_PCT"]
)

df["Turnover_Advantage"] = (
    df["Opp_TOV_PCT"] - df["TOV_PCT"]
)

df["Rebounding_Advantage"] = (
    df["ORB_PCT"] - df["Opp_ORB_PCT"]
)

df["Free_Throw_Advantage"] = (
    df["FT_Rate"] - df["Opp_FT_Rate"]
)

factors = [
    "Shooting_Advantage",
    "Turnover_Advantage",
    "Rebounding_Advantage",
    "Free_Throw_Advantage"
]

# Count how many factors MSU wins
df["Factors_Won"] = (
    df[factors] > 0
).sum(axis=1)

# Validate calculations
assert len(df) == 32
assert (df["Game_Possessions"] > 0).all()
assert df[factors].notna().all().all()

assert (
    (df["Net_Rating"] > 0)
    == (df["Result"] == "W")
).all()

assert (
    df["ORB_PCT"].between(0, 100)
).all()

assert (
    df["DRB_PCT"].between(0, 100)
).all()

# Filter Division I opponents
d1 = df[df["Division_I"]].copy()

assert len(d1) == 29

# Select efficiency statistics
metrics = [
    "Off_Rating",
    "Def_Rating",
    "Net_Rating",
    "eFG_PCT",
    "Opp_eFG_PCT",
    "TOV_PCT",
    "Opp_TOV_PCT",
    "ORB_PCT",
    "Opp_ORB_PCT",
    "DRB_PCT",
    "FT_Rate",
    "Opp_FT_Rate",
    "Opp_3P_PCT"
]

print("MONTANA STATE FOUR FACTORS ANALYSIS")
print("=" * 50)

# Compare all games with Division I games
season_summary = pd.DataFrame({
    "All Games": df[metrics].mean(),
    "Division I": d1[metrics].mean()
})

print("\nSeason efficiency summary:")
print(season_summary.round(2))

# Compare offensive and defensive performance
print("\nDivision I wins vs. losses:")

comparison = (
    d1.groupby("Result")[metrics]
    .mean().T
)

print(comparison.round(2))

# Compare Four Factors advantages
factor_comparison = (
    d1.groupby("Result")[factors]
    .mean().T
)

print("\nFour Factors advantages:")
print(factor_comparison.round(2))

# Correlation with scoring margin
correlations = (
    d1[factors + ["Point_Differential"]]
    .corr()["Point_Differential"]
    .drop("Point_Differential")
    .sort_values(ascending=False)
)

print("\nFour Factors correlations:")
print(correlations.round(3))

# Analyze wins by number of factors won
d1["Win"] = (d1["Result"] == "W").astype(int)

factor_results = d1.groupby("Factors_Won").agg(
    Games=("Result", "count"),
    Wins=("Win", "sum")
)

factor_results["Losses"] = (
    factor_results["Games"]
    - factor_results["Wins"]
)

factor_results["Win_PCT"] = (
    factor_results["Wins"]
    / factor_results["Games"]
) * 100

print("\nWinning percentage by factors won:")
print(factor_results.round(2))

# Display best defensive performances
print("\nTop five Division I defensive games:")

print(
    d1.sort_values("Def_Rating")[
        [
            "Opponent",
            "Result",
            "Opponent_Points",
            "Opp_eFG_PCT",
            "Def_Rating"
        ]
    ].head(5).round(2).to_string(index=False)
)

# Display Colorado game for verification
print("\nColorado game verification:")

print(
    df[df["Opponent"] == "Colorado"][
        [
            "Opponent",
            "Game_Possessions",
            "Off_Rating",
            "Def_Rating",
            "Net_Rating",
            "Factors_Won"
        ]
    ].round(2).to_string(index=False)
)

# Create visualization folder
output = Path("visualizations")
output.mkdir(parents=True, exist_ok=True)

# Four Factors correlation chart
chart = correlations.copy()

chart.index = [
    name.replace("_Advantage", "")
    .replace("_", " ")
    for name in chart.index
]

chart.plot(
    kind="barh",
    figsize=(10, 6),
    color="#002D56",
    edgecolor="#B9975B"
)

plt.title(
    "Montana State Basketball | 2025-26\n"
    "Four Factors vs. Scoring Margin"
)

plt.xlabel("Pearson Correlation")
plt.ylabel("")
plt.xlim(-1, 1)
plt.axvline(0, color="gray")
plt.grid(axis="x", alpha=0.15)
plt.tight_layout()

plt.savefig(
    output / "four_factors_correlation.png",
    dpi=300
)

plt.close()

# Winning percentage by factors won
plt.figure(figsize=(10, 6))

bars = plt.bar(
    factor_results.index,
    factor_results["Win_PCT"],
    color="#002D56",
    edgecolor="#B9975B"
)

for bar, (_, row) in zip(
    bars, factor_results.iterrows()
):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 2,
        f"{int(row['Wins'])}/{int(row['Games'])}",
        ha="center"
    )

plt.title(
    "Montana State Basketball | 2025-26\n"
    "Winning Percentage by Four Factors Won"
)

plt.xlabel("Number of Factors Won")
plt.ylabel("Winning Percentage (%)")
plt.xticks(range(5))
plt.ylim(0, 115)
plt.grid(axis="y", alpha=0.15)
plt.tight_layout()

plt.savefig(
    output / "four_factors_win_percentage.png",
    dpi=300
)

plt.close()

# Save analytical datasets
df.to_csv(
    "data/cleaned/four_factors_games_2025_26.csv",
    index=False
)

season_summary.to_csv(
    "data/cleaned/four_factors_season_summary.csv"
)

factor_comparison.to_csv(
    "data/cleaned/four_factors_win_loss.csv"
)

factor_results.to_csv(
    "data/cleaned/four_factors_win_rates.csv"
)

correlations.to_csv(
    "data/cleaned/four_factors_correlations.csv"
)

print("\nFour Factors analysis complete!")
print("Datasets and visualizations saved.")
