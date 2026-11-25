
import pandas as pd
import requests
import time
import re
import sys

from io import StringIO
from pathlib import Path

# Season configuration
season = sys.argv[1] if len(sys.argv) > 1 else "2026-27"
season_file = season.replace("-", "_")

raw = Path("data/raw")
output = Path("data/cleaned")
output.mkdir(parents=True, exist_ok=True)

print(f"BOBCAT ANALYTICS | {season}")
print("=" * 50)


# ==========================================
# 1. CLEAN GAME DATA
# ==========================================

df = pd.read_csv(
    raw / f"game_stats_{season_file}.csv"
)

df = df.dropna(subset=["Date", "W/L"]).copy()

df["Result"] = df["W/L"].str[0]
df = df[df["Result"].isin(["W", "L"])].copy()

df["Date"] = pd.to_datetime(
    df["Date"], format="%m/%d/%y"
).dt.strftime("%Y-%m-%d")

df["Season"] = season

df["Overtime"] = df["W/L"].str.contains(
    "OT", na=False
)

df["Opponent_Raw"] = df["Opponent"]

df["Away"] = df["Opponent"].str.startswith("at ")

df["Opponent"] = df["Opponent"].str.replace(
    r"^(at|vs)\s+", "", regex=True
)


# Separate combined statistics
def split_pair(value):

    parts = re.split(r"\s*[-–]\s*", str(value))

    if len(parts) != 2:
        raise ValueError(f"Invalid statistic: {value}")

    return int(parts[0]), int(parts[1])


pairs = {
    "Score": ["MSU_Points", "Opponent_Points"],
    "FGM/A": ["FGM", "FGA"],
    "3FG/A": ["3PM", "3PA"],
    "FTM/A": ["FTM", "FTA"]
}

for source, columns in pairs.items():

    df[columns] = pd.DataFrame(
        df[source].map(split_pair).tolist(),
        index=df.index
    )

df = df.rename(columns={
    "PCT": "FG_PCT",
    "PCT.1": "3P_PCT",
    "PCT.2": "FT_PCT",
    "OFF": "OREB",
    "DEF": "DREB",
    "TOT": "REB",
    "TO": "TOV"
})

df["Point_Differential"] = (
    df["MSU_Points"] - df["Opponent_Points"]
)

# Validate scores and game results
assert len(df) > 0
assert df["Date"].is_unique

assert (
    2 * df["FGM"] + df["3PM"] + df["FTM"]
    == df["MSU_Points"]
).all()

assert (
    (df["Point_Differential"] > 0)
    == (df["Result"] == "W")
).all()

print("\nGames cleaned:", len(df))
print("Record:")
print(df["Result"].value_counts())


# ==========================================
# 2. COLLECT OPPONENT BOX SCORES
# ==========================================

links = pd.read_csv(
    raw / f"box_score_links_{season_file}.csv"
)

assert links["Box_Score_URL"].is_unique
assert len(links) == len(df), "Box score count mismatch."


def extract_totals(table):

    totals = table[
        table["#"].astype(str).str.strip().str.lower()
        == "totals"
    ]

    if len(totals) != 1:
        raise ValueError("Missing team totals.")

    row = totals.iloc[0]

    fgm, fga = split_pair(row["fg"])
    three_pm, three_pa = split_pair(row["3pt"])
    ftm, fta = split_pair(row["ft"])
    oreb, dreb = split_pair(row["orb-drb"])

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

    assert (
        2 * fgm + three_pm + ftm == stats["PTS"]
    )

    return stats


records = []

session = requests.Session()

print("\nCollecting opponent statistics:")

for i, url in enumerate(links["Box_Score_URL"]):

    response = session.get(url, timeout=30)
    response.raise_for_status()

    tables = pd.read_html(StringIO(response.text))

    scoreboard = next(
        table for table in tables
        if {"Team", "Total"}.issubset(table.columns)
        and len(table) == 2
    )

    player_tables = [
        table for table in tables
        if {"#", "Player", "fg", "3pt",
            "ft", "orb-drb", "pts"}
        .issubset(table.columns)
    ]

    assert len(player_tables) == 2

    team_a = extract_totals(player_tables[0])
    team_b = extract_totals(player_tables[1])

    msu_mask = scoreboard["Team"].astype(str).str.strip().str.fullmatch(
        r"Montana\s+(St\.?|State)(\s+Bobcats)?",
        case=False,
        na=False
    )

    assert msu_mask.sum() == 1

    msu_score = int(
        scoreboard.loc[msu_mask, "Total"].iloc[0]
    )

    opp_score = int(
        scoreboard.loc[~msu_mask, "Total"].iloc[0]
    )

    if (
        team_a["PTS"] == msu_score
        and team_b["PTS"] == opp_score
    ):
        msu = team_a
        opponent = team_b

    elif (
        team_b["PTS"] == msu_score
        and team_a["PTS"] == opp_score
    ):
        msu = team_b
        opponent = team_a

    else:
        raise ValueError(f"Score mismatch: {url}")

    # Match box score with existing game data
    match = df[
        (df["MSU_Points"] == msu_score)
        & (df["Opponent_Points"] == opp_score)
        & (df["FGM"] == msu["FGM"])
        & (df["FGA"] == msu["FGA"])
        & (df["3PM"] == msu["3PM"])
        & (df["3PA"] == msu["3PA"])
        & (df["FTM"] == msu["FTM"])
        & (df["FTA"] == msu["FTA"])
    ]

    if len(match) != 1:
        raise ValueError(f"Game matching failed: {url}")

    game = match.iloc[0]

    record = {
        "Date": game["Date"],
        "Box_Score_URL": url,
        "Opponent_Box_Name": scoreboard.loc[
            ~msu_mask, "Team"
        ].iloc[0]
    }

    for stat, value in opponent.items():
        record["Opp_" + stat] = value

    records.append(record)

    print(
        f"[{i + 1}/{len(links)}] "
        f"{game['Opponent']} | SUCCESS"
    )

    time.sleep(1)

opponents = pd.DataFrame(records)

df = df.merge(
    opponents,
    on="Date",
    how="left",
    validate="one_to_one"
)

assert df["Opp_PTS"].notna().all()
assert (df["Opp_PTS"] == df["Opponent_Points"]).all()


# ==========================================
# 3. ADVANCED BASKETBALL METRICS
# ==========================================

df["Possessions"] = (
    df["FGA"] - df["OREB"]
    + df["TOV"] + 0.475 * df["FTA"]
)

df["Opp_Possessions"] = (
    df["Opp_FGA"] - df["Opp_OREB"]
    + df["Opp_TOV"] + 0.475 * df["Opp_FTA"]
)

df["Game_Possessions"] = (
    df["Possessions"] + df["Opp_Possessions"]
) / 2

assert (df["Game_Possessions"] > 0).all()

df["ORtg"] = (
    df["MSU_Points"] / df["Possessions"]
) * 100

df["Off_Rating"] = (
    df["MSU_Points"] / df["Game_Possessions"]
) * 100

df["Def_Rating"] = (
    df["Opponent_Points"] / df["Game_Possessions"]
) * 100

df["Net_Rating"] = (
    df["Off_Rating"] - df["Def_Rating"]
)

df["eFG_PCT"] = (
    (df["FGM"] + 0.5 * df["3PM"])
    / df["FGA"]
) * 100

df["Opp_eFG_PCT"] = (
    (df["Opp_FGM"] + 0.5 * df["Opp_3PM"])
    / df["Opp_FGA"]
) * 100

df["TS_PCT"] = (
    df["MSU_Points"]
    / (2 * (df["FGA"] + 0.44 * df["FTA"]))
) * 100

df["TOV_PCT"] = (
    df["TOV"] / df["Possessions"]
) * 100

df["Opp_TOV_PCT"] = (
    df["Opp_TOV"] / df["Opp_Possessions"]
) * 100

df["3PAr"] = (
    df["3PA"] / df["FGA"]
) * 100

df["FTr"] = (
    df["FTA"] / df["FGA"]
) * 100

df["AST_TO"] = (
    df["AST"] / df["TOV"].replace(0, float("nan"))
)

df["PPP"] = df["MSU_Points"] / df["Possessions"]

df["2PM"] = df["FGM"] - df["3PM"]
df["2PA"] = df["FGA"] - df["3PA"]

df["2P_PCT"] = (
    df["2PM"] / df["2PA"].replace(0, float("nan"))
) * 100

df["Opp_3P_PCT"] = (
    df["Opp_3PM"] /
    df["Opp_3PA"].replace(0, float("nan"))
) * 100

df["Opp_FG_PCT"] = (
    df["Opp_FGM"] / df["Opp_FGA"]
) * 100

df["Opp_3PAr"] = (
    df["Opp_3PA"] / df["Opp_FGA"]
) * 100


# ==========================================
# 4. FOUR FACTORS ANALYSIS
# ==========================================

df["ORB_PCT"] = (
    df["OREB"] /
    (df["OREB"] + df["Opp_DREB"])
) * 100

df["Opp_ORB_PCT"] = (
    df["Opp_OREB"] /
    (df["Opp_OREB"] + df["DREB"])
) * 100

df["DRB_PCT"] = (
    df["DREB"] /
    (df["DREB"] + df["Opp_OREB"])
) * 100

df["FT_Rate"] = (
    df["FTM"] / df["FGA"]
) * 100

df["Opp_FT_Rate"] = (
    df["Opp_FTM"] / df["Opp_FGA"]
) * 100

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

assert df[factors].notna().all().all()

df["Factors_Won"] = (
    df[factors] > 0
).sum(axis=1)


# ==========================================
# 5. OPPONENT CLASSIFICATION
# ==========================================

known_d1 = {
    "2025-26": [
        "Colorado", "Denver", "Stanford",
        "Boise St.", "Long Beach St.", "Utah St.",
        "St. Thomas (MN)", "Oral Roberts",
        "Oregon St.", "Cal Poly", "Montana",
        "Idaho", "Idaho St.", "Weber St.",
        "Portland St.", "Sacramento St.",
        "Eastern Wash.", "Northern Colo.",
        "Northern Ariz."
    ],
    "2026-27": [
        "Colorado St.", "Long Beach St.",
        "BYU", "Cal Poly", "Gonzaga", "High Point"
    ]
}

known_non_d1 = {
    "2025-26": [
        "Northwest Indian", "Nobel", "Northwest (WA)"
    ],
    "2026-27": []
}

df["Competition"] = "Unverified"

df.loc[
    df["Opponent"].isin(known_d1.get(season, [])),
    "Competition"
] = "Division I"

df.loc[
    df["Opponent"].isin(known_non_d1.get(season, [])),
    "Competition"
] = "Non-Division I"

df["Division_I"] = df["Competition"].map({
    "Division I": True,
    "Non-Division I": False
}).astype("boolean")

unverified = df.loc[
    df["Competition"] == "Unverified",
    "Opponent"
].unique()

if len(unverified) > 0:
    print("\nOpponents requiring classification:")
    print(unverified)


# ==========================================
# 6. SEASON ANALYSIS
# ==========================================

df = df.sort_values("Date").reset_index(drop=True)

assert len(df) == len(links)
assert df["Date"].is_unique

assert (
    (df["Net_Rating"] > 0)
    == (df["Result"] == "W")
).all()

metrics = [
    "MSU_Points",
    "Opponent_Points",
    "Point_Differential",
    "Off_Rating",
    "Def_Rating",
    "Net_Rating",
    "eFG_PCT",
    "Opp_eFG_PCT",
    "TS_PCT",
    "TOV_PCT",
    "Opp_TOV_PCT",
    "ORB_PCT",
    "Opp_ORB_PCT",
    "FT_Rate",
    "Opp_FT_Rate",
    "3PAr"
]

print("\nSEASON PERFORMANCE")
print("=" * 50)

print("\nGames:", len(df))
print("Wins:", (df["Result"] == "W").sum())
print("Losses:", (df["Result"] == "L").sum())

print("\nSeason averages:")
print(df[metrics].mean().round(2))

print("\nFour Factors by game:")

print(
    df[[
        "Opponent",
        "Result",
        "Shooting_Advantage",
        "Turnover_Advantage",
        "Rebounding_Advantage",
        "Free_Throw_Advantage",
        "Factors_Won"
    ]].round(2).to_string(index=False)
)

print("\nGame efficiency ratings:")

print(
    df[[
        "Opponent",
        "Result",
        "Off_Rating",
        "Def_Rating",
        "Net_Rating"
    ]].round(2).to_string(index=False)
)

# Save processed season
df.to_csv(
    output / f"season_analysis_{season_file}.csv",
    index=False
)

print("\nSeason processing complete!")
print(f"Saved: season_analysis_{season_file}.csv")
