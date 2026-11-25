
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Load Four Factors database
df = pd.read_csv(
    "data/cleaned/four_factors_games_2025_26.csv"
)

df["Date"] = pd.to_datetime(df["Date"])

# 2025-26 Big Sky opponents
big_sky = [
    "Montana",
    "Idaho",
    "Idaho St.",
    "Weber St.",
    "Portland St.",
    "Sacramento St.",
    "Eastern Wash.",
    "Northern Colo.",
    "Northern Ariz."
]

# Filter Big Sky matchups
conference = df[
    df["Opponent"].isin(big_sky)
].copy()

# Identify postseason game
conference["Postseason"] = (
    conference["Date"] == pd.Timestamp("2026-03-08")
)

# Separate regular season and postseason
regular = conference[
    ~conference["Postseason"]
].copy()

postseason = conference[
    conference["Postseason"]
].copy()

# Create numerical win indicator
regular["Win"] = (
    regular["Result"] == "W"
).astype(int)

# Validate conference record
assert len(conference) == 19
assert len(regular) == 18
assert len(postseason) == 1
assert regular["Win"].sum() == 12
assert regular["Opponent"].nunique() == 9
assert (
    regular.groupby("Opponent").size() == 2
).all()

print("BIG SKY OPPONENT SCOUTING")
print("=" * 50)

print("\nRegular-season conference record:")
print(regular["Result"].value_counts())

# Summarize historical matchups
scouting = regular.groupby("Opponent").agg(
    Games=("Result", "count"),
    Wins=("Win", "sum"),
    PPG=("MSU_Points", "mean"),
    Opp_PPG=("Opponent_Points", "mean"),
    Margin=("Point_Differential", "mean"),
    Off_Rating=("Off_Rating", "mean"),
    Def_Rating=("Def_Rating", "mean"),
    Net_Rating=("Net_Rating", "mean"),
    Shooting=("Shooting_Advantage", "mean"),
    Turnovers=("Turnover_Advantage", "mean"),
    Rebounding=("Rebounding_Advantage", "mean"),
    Free_Throws=("Free_Throw_Advantage", "mean"),
    Avg_Factors_Won=("Factors_Won", "mean")
)

# Calculate losses and winning percentage
scouting["Losses"] = (
    scouting["Games"] - scouting["Wins"]
)

scouting["Win_PCT"] = (
    scouting["Wins"] / scouting["Games"]
) * 100

# Sort by historical scoring margin
scouting = scouting.sort_values(
    "Margin", ascending=False
)

print("\nConference matchup results:")

print(
    scouting[[
        "Games", "Wins", "Losses",
        "PPG", "Opp_PPG", "Margin",
        "Net_Rating"
    ]].round(2)
)

# Four Factors matchup profiles
factors = [
    "Shooting",
    "Turnovers",
    "Rebounding",
    "Free_Throws"
]

print("\nFour Factors matchup advantages:")
print(scouting[factors].round(2))

# Individual opponent scouting summaries
for opponent, row in scouting.iterrows():

    print("\n" + "=" * 50)
    print("OPPONENT:", opponent)

    print(
        f"Record: {int(row['Wins'])}"
        f"-{int(row['Losses'])}"
    )

    print(f"Average margin: {row['Margin']:+.2f}")
    print(f"Offensive rating: {row['Off_Rating']:.2f}")
    print(f"Defensive rating: {row['Def_Rating']:.2f}")
    print(f"Net rating: {row['Net_Rating']:+.2f}")

    print("\nFour Factors profile:")

    for factor in factors:

        value = row[factor]

        if value > 0:
            status = "MSU advantage"

        elif value < 0:
            status = "Opponent advantage"

        else:
            status = "Even"

        print(
            f"{factor}: {value:+.2f} pp "
            f"| {status}"
        )

# Montana rivalry analysis
montana = regular[
    regular["Opponent"] == "Montana"
]

print("\nBRAWL OF THE WILD ANALYSIS")
print("=" * 50)

print(
    montana[[
        "Date",
        "MSU_Points",
        "Opponent_Points",
        "Point_Differential",
        "Off_Rating",
        "Def_Rating",
        "Factors_Won"
    ]].round(2).to_string(index=False)
)

# Idaho postseason analysis
print("\nBIG SKY TOURNAMENT ANALYSIS")

print(
    postseason[[
        "Opponent",
        "MSU_Points",
        "Opponent_Points",
        "Off_Rating",
        "Def_Rating",
        "Shooting_Advantage",
        "Turnover_Advantage",
        "Rebounding_Advantage",
        "Free_Throw_Advantage",
        "Factors_Won"
    ]].round(2).to_string(index=False)
)

# Save scouting datasets
output = Path("data/cleaned")
output.mkdir(parents=True, exist_ok=True)

scouting.to_csv(
    output / "big_sky_opponent_scouting.csv"
)

regular.to_csv(
    output / "big_sky_regular_season_games.csv",
    index=False
)

postseason.to_csv(
    output / "big_sky_postseason_games.csv",
    index=False
)

# Create visualizations
visualizations = Path("visualizations")
visualizations.mkdir(parents=True, exist_ok=True)

# Conference scoring margin chart
chart = scouting["Margin"].sort_values()

colors = [
    "#002D56" if value >= 0 else "#B9975B"
    for value in chart
]

chart.plot(
    kind="barh",
    figsize=(11, 7),
    color=colors
)

plt.title(
    "Montana State Basketball | 2025-26\n"
    "Average Scoring Margin by Big Sky Opponent"
)

plt.xlabel("Average Point Differential")
plt.ylabel("")
plt.axvline(0, color="gray")
plt.grid(axis="x", alpha=0.15)
plt.tight_layout()

plt.savefig(
    visualizations / "big_sky_matchup_margins.png",
    dpi=300
)

plt.close()

# Four Factors scouting heatmap
heatmap = scouting[factors]

limit = max(
    abs(heatmap.min().min()),
    abs(heatmap.max().max())
)

if limit == 0:
    limit = 1

fig, ax = plt.subplots(figsize=(12, 8))

image = ax.imshow(
    heatmap.values,
    cmap="RdBu",
    vmin=-limit,
    vmax=limit,
    aspect="auto"
)

ax.set_xticks(range(len(factors)))

ax.set_xticklabels([
    "Shooting",
    "Turnovers",
    "Rebounding",
    "Free Throws"
])

ax.set_yticks(range(len(heatmap)))

ax.set_yticklabels(heatmap.index)

# Label each heatmap cell
for i in range(len(heatmap)):

    for j in range(len(factors)):

        value = heatmap.iloc[i, j]

        text_color = (
            "white"
            if abs(value) > limit * 0.6
            else "black"
        )

        ax.text(
            j, i,
            f"{value:+.1f}",
            ha="center",
            va="center",
            color=text_color
        )

fig.colorbar(
    image,
    ax=ax,
    label="MSU Advantage (Percentage Points)"
)

plt.title(
    "Montana State Basketball | 2025-26\n"
    "Big Sky Four Factors Matchup Heatmap"
)

plt.tight_layout()

plt.savefig(
    visualizations / "big_sky_scouting_heatmap.png",
    dpi=300
)

plt.close()

print("\nOpponent scouting analysis complete!")
print("Scouting datasets and visualizations saved.")
