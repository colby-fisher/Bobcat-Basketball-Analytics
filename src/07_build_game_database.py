
import pandas as pd
import requests
import time
import re

from io import StringIO
from pathlib import Path

# Load existing game data
games = pd.read_csv(
    "data/cleaned/classified_games_2025_26.csv"
)

# Load discovered box score links
links = pd.read_csv(
    "data/raw/box_score_links_2025_26.csv"
)

records = []
errors = []

session = requests.Session()


# Separate combined statistics
def split_stat(value):

    parts = str(value).split("-")

    if len(parts) != 2:
        raise ValueError(f"Invalid statistic: {value}")

    return int(parts[0]), int(parts[1])


# Extract team totals
def extract_totals(table):

    totals = table[
        table["#"].astype(str).str.strip().str.lower()
        == "totals"
    ]

    if len(totals) != 1:
        raise ValueError("Team totals row not found.")

    row = totals.iloc[0]

    fgm, fga = split_stat(row["fg"])
    three_pm, three_pa = split_stat(row["3pt"])
    ftm, fta = split_stat(row["ft"])
    oreb, dreb = split_stat(row["orb-drb"])

    stats = {
        "FGM": fgm,
        "FGA": fga,
        "3PM": three_pm,
        "3PA": three_pa,
        "FTM": ftm,
        "FTA": fta,
        "OREB": oreb,
        "DREB": dreb,
        "REB": int(row["reb"]),
        "AST": int(row["a"]),
        "TOV": int(row["to"]),
        "STL": int(row["stl"]),
        "BLK": int(row["blk"]),
        "PF": int(row["pf"]),
        "PTS": int(row["pts"])
    }

    # Validate scoring
    assert (
        2 * stats["FGM"]
        + stats["3PM"]
        + stats["FTM"]
        == stats["PTS"]
    )

    return stats


print("BUILDING COMPLETE GAME DATABASE")
print("=" * 50)

# Collect all game box scores
for i, url in enumerate(links["Box_Score_URL"]):

    try:

        response = session.get(url, timeout=30)
        response.raise_for_status()

        tables = pd.read_html(
            StringIO(response.text)
        )

        # Identify the scoreboard
        scoreboard = next(
            table for table in tables
            if {"Team", "Total"}.issubset(table.columns)
            and len(table) == 2
        )

        # Identify both player statistics tables
        player_tables = [
            table for table in tables
            if {"#", "Player", "fg", "3pt",
                "ft", "orb-drb", "pts"}
            .issubset(table.columns)
        ]

        if len(player_tables) != 2:
            raise ValueError(
                "Expected two player statistics tables."
            )

        team_a = extract_totals(player_tables[0])
        team_b = extract_totals(player_tables[1])

        # Identify Montana State on the scoreboard
        msu_mask = (
            scoreboard["Team"]
            .astype(str)
            .str.strip()
            .str.fullmatch(
                r"Montana\s+(St\.?|State)(\s+Bobcats)?",
                case=False,
                na=False
            )
        )

        if msu_mask.sum() != 1:
            raise ValueError(
                "Could not identify Montana State."
            )

        msu_score = int(
            scoreboard.loc[msu_mask, "Total"].iloc[0]
        )

        opponent_score = int(
            scoreboard.loc[~msu_mask, "Total"].iloc[0]
        )

        opponent_name = (
            scoreboard.loc[~msu_mask, "Team"].iloc[0]
        )

        # Match team totals to the final scores
        if (
            team_a["PTS"] == msu_score
            and team_b["PTS"] == opponent_score
        ):
            msu = team_a
            opponent = team_b

        elif (
            team_b["PTS"] == msu_score
            and team_a["PTS"] == opponent_score
        ):
            msu = team_b
            opponent = team_a

        else:
            raise ValueError(
                "Box score totals do not match scoreboard."
            )

        # Match the box score to our existing game data
        match = games[
            (games["MSU_Points"] == msu_score)
            & (games["Opponent_Points"] == opponent_score)
            & (games["FGM"] == msu["FGM"])
            & (games["FGA"] == msu["FGA"])
            & (games["3PM"] == msu["3PM"])
            & (games["3PA"] == msu["3PA"])
            & (games["FTM"] == msu["FTM"])
            & (games["FTA"] == msu["FTA"])
        ]

        if len(match) != 1:
            raise ValueError(
                "Could not uniquely match the game."
            )

        game = match.iloc[0]

        # Save game identifiers
        record = {
            "Date": game["Date"],
            "Opponent_Box_Name": opponent_name,
            "Box_Score_URL": url
        }

        # Add opponent statistics
        for stat, value in opponent.items():
            record["Opp_" + stat] = value

        records.append(record)

        print(
            f"[{i + 1}/{len(links)}] "
            f"{game['Opponent']} | "
            f"{msu_score}-{opponent_score} | SUCCESS"
        )

    except Exception as error:

        errors.append({
            "URL": url,
            "Error": str(error)
        })

        print(
            f"[{i + 1}/{len(links)}] ERROR: {error}"
        )

    # Avoid sending excessive website requests
    time.sleep(1)


# Stop if any games failed
if errors:

    print("\nFAILED BOX SCORES:")
    print(pd.DataFrame(errors).to_string(index=False))

    raise RuntimeError(
        "Some games failed. Resolve errors before saving."
    )

# Create opponent DataFrame
opponents = pd.DataFrame(records)

assert len(opponents) == 32
assert opponents["Date"].is_unique

# Merge both datasets
df = games.merge(
    opponents,
    on="Date",
    how="left",
    validate="one_to_one"
)

# Validate complete database
assert len(df) == 32
assert df["Opp_PTS"].notna().all()

assert (
    df["Opp_PTS"] == df["Opponent_Points"]
).all()

assert (
    df["Opp_FGM"] <= df["Opp_FGA"]
).all()

assert (
    df["Opp_3PM"] <= df["Opp_3PA"]
).all()

assert (
    df["Opp_FTM"] <= df["Opp_FTA"]
).all()

# Save complete dataset
output = Path("data/cleaned")
output.mkdir(parents=True, exist_ok=True)

df.to_csv(
    output / "complete_game_database_2025_26.csv",
    index=False
)

opponents.to_csv(
    output / "opponent_stats_2025_26.csv",
    index=False
)

print("\nDATABASE VALIDATION")
print("=" * 50)

print("Games collected:", len(records))
print("Failed games:", len(errors))
print("Database shape:", df.shape)

print("\nOpponent season totals:")

print(
    df[[
        "Opp_PTS",
        "Opp_FGM",
        "Opp_FGA",
        "Opp_3PM",
        "Opp_3PA",
        "Opp_FTM",
        "Opp_FTA",
        "Opp_OREB",
        "Opp_DREB",
        "Opp_TOV"
    ]].sum()
)

print("\nFirst five games:")

print(
    df[[
        "Date",
        "Opponent",
        "MSU_Points",
        "Opponent_Points",
        "Opp_FGM",
        "Opp_FGA",
        "Opp_OREB",
        "Opp_TOV"
    ]].head().to_string(index=False)
)

print("\nComplete game database successfully saved!")
