
import pandas as pd
from pathlib import Path

# Load raw game statistics
df = pd.read_csv("data/raw/game_stats_2025_26.csv")

print("Original dataset shape:", df.shape)

# Remove season summary rows
df = df.dropna(subset=["Date"]).copy()

# Convert dates
df["Date"] = pd.to_datetime(
    df["Date"], format="%m/%d/%y"
)

# Identify overtime games
df["Overtime"] = df["W/L"].str.contains(
    "OT", na=False
)

# Standardize wins and losses
df["Result"] = df["W/L"].str[0]

# Identify listed game location
df["Away"] = df["Opponent"].str.startswith("at ")

# Preserve original opponent information
df["Opponent_Raw"] = df["Opponent"]

# Clean opponent names
df["Opponent"] = df["Opponent"].str.replace(
    r"^(at|vs)\s+", "", regex=True
)

# Separate final scores
df[["MSU_Points", "Opponent_Points"]] = (
    df["Score"].str.split("-", expand=True).astype(int)
)

# Calculate scoring margin
df["Point_Differential"] = (
    df["MSU_Points"] - df["Opponent_Points"]
)

# Separate field goals made and attempted
df[["FGM", "FGA"]] = (
    df["FGM/A"].str.split("-", expand=True).astype(int)
)

# Separate three-pointers made and attempted
df[["3PM", "3PA"]] = (
    df["3FG/A"].str.split("-", expand=True).astype(int)
)

# Separate free throws made and attempted
df[["FTM", "FTA"]] = (
    df["FTM/A"].str.split("-", expand=True).astype(int)
)

# Rename statistical columns
df = df.rename(columns={
    "PCT": "FG_PCT",
    "PCT.1": "3P_PCT",
    "PCT.2": "FT_PCT",
    "OFF": "OREB",
    "DEF": "DREB",
    "TOT": "REB",
    "TO": "TOV"
})

# Select cleaned columns
df = df[[
    "Date",
    "Opponent",
    "Opponent_Raw",
    "Away",
    "Result",
    "Overtime",
    "MSU_Points",
    "Opponent_Points",
    "Point_Differential",
    "FGM",
    "FGA",
    "FG_PCT",
    "3PM",
    "3PA",
    "3P_PCT",
    "FTM",
    "FTA",
    "FT_PCT",
    "OREB",
    "DREB",
    "REB",
    "AST",
    "TOV",
    "STL",
    "BLK",
    "PF"
]]

# Sort games chronologically
df = df.sort_values("Date").reset_index(drop=True)

# Validate the dataset
assert len(df) == 32, "Unexpected game count."

assert (df["Result"] == "W").sum() == 18
assert (df["Result"] == "L").sum() == 14

assert df.isnull().sum().sum() == 0
assert df.duplicated().sum() == 0

# Verify points against shooting statistics
calculated_points = (
    2 * df["FGM"] + df["3PM"] + df["FTM"]
)

assert (calculated_points == df["MSU_Points"]).all()

# Verify game results against final scores
assert (
    (df["Result"] == "W") ==
    (df["Point_Differential"] > 0)
).all()

# Create cleaned data folder
output_folder = Path("data/cleaned")
output_folder.mkdir(parents=True, exist_ok=True)

# Save cleaned dataset
df.to_csv(
    output_folder / "game_stats_2025_26_cleaned.csv",
    index=False
)

# Display results
print("\nCleaned dataset shape:", df.shape)

print("\nSeason record:")
print(df["Result"].value_counts())

print("\nOvertime games:")
print(df["Overtime"].value_counts())

print("\nMissing values:", df.isnull().sum().sum())
print("Duplicate rows:", df.duplicated().sum())

print("\nAverage points scored:")
print(df["MSU_Points"].mean())

print("\nAverage points allowed:")
print(df["Opponent_Points"].mean())

print("\nAverage point differential:")
print(df["Point_Differential"].mean())

print("\nFirst five cleaned games:")
print(df.head().to_string(index=False))

print("\nAll validation checks passed!")
print("Cleaned dataset successfully saved.")
