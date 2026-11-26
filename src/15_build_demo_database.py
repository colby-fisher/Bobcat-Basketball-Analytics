
import sqlite3
import random
import pandas as pd

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "demo"
DEMO.mkdir(exist_ok=True)

DATABASE = DEMO / "bobcat_demo.db"

rng = random.Random(42)

DATA_TYPE = "SYNTHETIC DEMONSTRATION DATA"


# ==========================================
# GENERATE FICTIONAL TEAM STATISTICS
# ==========================================

def team_stats():

    two_made = rng.randint(15, 24)
    two_attempts = two_made + rng.randint(14, 23)

    three_made = rng.randint(5, 13)
    three_attempts = three_made + rng.randint(12, 20)

    ftm = rng.randint(7, 19)
    fta = ftm + rng.randint(2, 7)

    return {
        "FGM": two_made + three_made,
        "FGA": two_attempts + three_attempts,
        "3PM": three_made,
        "3PA": three_attempts,
        "FTM": ftm,
        "FTA": fta,
        "OREB": rng.randint(5, 14),
        "DREB": rng.randint(18, 30),
        "AST": rng.randint(8, 18),
        "TOV": rng.randint(8, 19),
        "STL": rng.randint(3, 8),
        "BLK": rng.randint(1, 5),
        "PF": rng.randint(12, 22)
    }


def possessions(team):

    return (
        team["FGA"]
        - team["OREB"]
        + team["TOV"]
        + 0.475 * team["FTA"]
    )


def points(team):

    return (
        2 * team["FGM"]
        + team["3PM"]
        + team["FTM"]
    )


# ==========================================
# GENERATE DEMONSTRATION GAMES
# ==========================================

game_rows = []

opponents = [
    f"Demo University {letter}"
    for letter in "ABCDEFGHI"
]

seasons = {
    "2025-26": ("2025-11-03", 18),
    "2026-27": ("2026-11-02", 6)
}

for season, (start, count) in seasons.items():

    dates = pd.date_range(
        start=start,
        periods=count,
        freq="5D"
    )

    for i, date in enumerate(dates):

        msu = team_stats()
        opp = team_stats()

        score = points(msu)

        while points(opp) == score:
            opp = team_stats()

        opp_score = points(opp)

        msu["REB"] = msu["OREB"] + msu["DREB"]
        opp["REB"] = opp["OREB"] + opp["DREB"]

        msu_poss = possessions(msu)
        opp_poss = possessions(opp)

        game_poss = (msu_poss + opp_poss) / 2

        efg = (
            (msu["FGM"] + .5 * msu["3PM"])
            / msu["FGA"] * 100
        )

        opp_efg = (
            (opp["FGM"] + .5 * opp["3PM"])
            / opp["FGA"] * 100
        )

        tov = msu["TOV"] / msu_poss * 100
        opp_tov = opp["TOV"] / opp_poss * 100

        orb = (
            msu["OREB"]
            / (msu["OREB"] + opp["DREB"]) * 100
        )

        opp_orb = (
            opp["OREB"]
            / (opp["OREB"] + msu["DREB"]) * 100
        )

        ft_rate = msu["FTM"] / msu["FGA"] * 100

        opp_ft_rate = (
            opp["FTM"] / opp["FGA"] * 100
        )

        advantages = [
            efg - opp_efg,
            opp_tov - tov,
            orb - opp_orb,
            ft_rate - opp_ft_rate
        ]

        opponent = opponents[i % len(opponents)]

        row = {
            **msu,
            **{
                f"Opp_{key}": value
                for key, value in opp.items()
            },

            "Date": date.strftime("%Y-%m-%d"),
            "Season": season,
            "Opponent": opponent,
            "Opponent_Raw": opponent,
            "Opponent_Box_Name": opponent,
            "Box_Score_URL": "",
            "Away": i % 2,
            "Overtime": 0,
            "Division_I": 1,

            "Result": "W" if score > opp_score else "L",

            "MSU_Points": score,
            "Opponent_Points": opp_score,
            "Opp_PTS": opp_score,
            "Point_Differential": score - opp_score,

            "FG_PCT": msu["FGM"] / msu["FGA"],
            "3P_PCT": msu["3PM"] / msu["3PA"],
            "FT_PCT": msu["FTM"] / msu["FTA"],

            "Possessions": msu_poss,
            "Opp_Possessions": opp_poss,
            "Game_Possessions": game_poss,

            "ORtg": score / msu_poss * 100,
            "Off_Rating": score / game_poss * 100,
            "Def_Rating": opp_score / game_poss * 100,
            "Net_Rating": (
                (score - opp_score) / game_poss * 100
            ),

            "eFG_PCT": efg,
            "Opp_eFG_PCT": opp_efg,

            "TS_PCT": (
                score /
                (2 * (msu["FGA"] + .44 * msu["FTA"]))
                * 100
            ),

            "TOV_PCT": tov,
            "Opp_TOV_PCT": opp_tov,

            "ORB_PCT": orb,
            "Opp_ORB_PCT": opp_orb,
            "DRB_PCT": 100 - opp_orb,

            "FT_Rate": ft_rate,
            "Opp_FT_Rate": opp_ft_rate,

            "FTr": msu["FTA"] / msu["FGA"] * 100,
            "3PAr": msu["3PA"] / msu["FGA"] * 100,
            "AST_TO": msu["AST"] / msu["TOV"],
            "PPP": score / msu_poss,

            "2PM": msu["FGM"] - msu["3PM"],
            "2PA": msu["FGA"] - msu["3PA"],

            "2P_PCT": (
                (msu["FGM"] - msu["3PM"])
                / (msu["FGA"] - msu["3PA"]) * 100
            ),

            "Opp_FG_PCT": (
                opp["FGM"] / opp["FGA"] * 100
            ),

            "Opp_3P_PCT": (
                opp["3PM"] / opp["3PA"] * 100
            ),

            "Opp_3PAr": (
                opp["3PA"] / opp["FGA"] * 100
            ),

            "Shooting_Advantage": advantages[0],
            "Turnover_Advantage": advantages[1],
            "Rebounding_Advantage": advantages[2],
            "Free_Throw_Advantage": advantages[3],

            "Factors_Won": sum(
                value > 0 for value in advantages
            ),

            "Data_Type": DATA_TYPE
        }

        game_rows.append(row)

games = pd.DataFrame(game_rows)


# ==========================================
# GENERATE FICTIONAL PLAYER SEASONS
# ==========================================

player_rows = []

weights = [19, 17, 15, 14, 12, 10, 8, 5]


def distribute(total):

    allocation = [0] * len(weights)

    for index in rng.choices(
        range(len(weights)),
        weights=weights,
        k=int(total)
    ):

        allocation[index] += 1

    return allocation


def ratio(a, b):

    return a / b if b else None


for season in seasons:

    season_games = games[
        games["Season"] == season
    ]

    totals = season_games.sum(numeric_only=True)
    gp = len(season_games)

    made_twos = distribute(
        totals["FGM"] - totals["3PM"]
    )

    missed_twos = distribute(
        totals["FGA"] - totals["3PA"]
        - totals["FGM"] + totals["3PM"]
    )

    made_threes = distribute(totals["3PM"])

    missed_threes = distribute(
        totals["3PA"] - totals["3PM"]
    )

    made_ft = distribute(totals["FTM"])

    missed_ft = distribute(
        totals["FTA"] - totals["FTM"]
    )

    other_stats = {
        stat: distribute(totals[stat])
        for stat in [
            "OREB", "DREB", "AST",
            "TOV", "STL", "BLK", "PF"
        ]
    }

    minutes = [34, 32, 30, 28, 26, 20, 18, 12]

    for i in range(len(weights)):

        fgm = made_twos[i] + made_threes[i]

        fga = (
            fgm + missed_twos[i] + missed_threes[i]
        )

        three_pm = made_threes[i]

        three_pa = (
            made_threes[i] + missed_threes[i]
        )

        ftm = made_ft[i]
        fta = ftm + missed_ft[i]

        pts = 2 * fgm + three_pm + ftm

        stats = {
            key: values[i]
            for key, values in other_stats.items()
        }

        reb = stats["OREB"] + stats["DREB"]

        player_rows.append({
            **stats,

            "Jersey": i + 1,
            "Player": f"Demo Player {i + 1:02d}",
            "Season": season,

            "GP": gp,
            "GS": gp if i < 5 else 0,
            "MIN": minutes[i] * gp,

            "PTS": pts,
            "FGM": fgm,
            "FGA": fga,
            "3PM": three_pm,
            "3PA": three_pa,
            "FTM": ftm,
            "FTA": fta,
            "REB": reb,

            "PPG": pts / gp,
            "RPG": reb / gp,
            "APG": stats["AST"] / gp,
            "SPG": stats["STL"] / gp,
            "BPG": stats["BLK"] / gp,

            "eFG_PCT": ratio(
                (fgm + .5 * three_pm) * 100, fga
            ),

            "TS_PCT": ratio(
                pts * 100, 2 * (fga + .44 * fta)
            ),

            "3P_PCT": ratio(
                three_pm * 100, three_pa
            ),

            "3PAr": ratio(three_pa * 100, fga),

            "AST_TO": ratio(
                stats["AST"], stats["TOV"]
            ),

            "FTr": ratio(fta * 100, fga),
            "FGA_Per_Game": fga / gp,
            "Qualified": int(fga >= 50),
            "Data_Type": DATA_TYPE
        })

players = pd.DataFrame(player_rows)


# ==========================================
# GENERATE OPPONENT SCOUTING PROFILES
# ==========================================

scouting_rows = []

historical = games[
    games["Season"] == "2025-26"
]

for opponent, group in historical.groupby("Opponent"):

    wins = int((group["Result"] == "W").sum())

    scouting_rows.append({
        "Opponent": opponent,
        "Season": "2025-26",

        "Games": len(group),
        "Wins": wins,
        "Losses": len(group) - wins,
        "Win_PCT": wins / len(group) * 100,

        "PPG": group["MSU_Points"].mean(),
        "Opp_PPG": group["Opponent_Points"].mean(),
        "Margin": group["Point_Differential"].mean(),

        "Off_Rating": group["Off_Rating"].mean(),
        "Def_Rating": group["Def_Rating"].mean(),
        "Net_Rating": group["Net_Rating"].mean(),

        "Shooting": group["Shooting_Advantage"].mean(),
        "Turnovers": group["Turnover_Advantage"].mean(),
        "Rebounding": group["Rebounding_Advantage"].mean(),
        "Free_Throws": group["Free_Throw_Advantage"].mean(),

        "Avg_Factors_Won": group["Factors_Won"].mean(),

        "Data_Type": DATA_TYPE
    })

scouting = pd.DataFrame(scouting_rows)


# ==========================================
# VALIDATE AND SAVE DEMONSTRATION DATABASE
# ==========================================

for season in seasons:

    team_points = games.loc[
        games["Season"] == season,
        "MSU_Points"
    ].sum()

    player_points = players.loc[
        players["Season"] == season,
        "PTS"
    ].sum()

    assert team_points == player_points

assert not games.duplicated(
    ["Season", "Date"]
).any()

assert not players.duplicated(
    ["Season", "Player"]
).any()

with sqlite3.connect(DATABASE) as conn:

    games.to_sql(
        "games", conn,
        if_exists="replace", index=False
    )

    players.to_sql(
        "player_seasons", conn,
        if_exists="replace", index=False
    )

    scouting.to_sql(
        "opponent_scouting", conn,
        if_exists="replace", index=False
    )

    integrity = conn.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

    assert integrity == "ok"

print("=" * 50)
print("BOBCAT ANALYTICS LAB")
print("SYNTHETIC DEMONSTRATION DATABASE")
print("=" * 50)

print("Games:", len(games))
print("Player-season records:", len(players))
print("Scouting profiles:", len(scouting))
print("Database integrity:", integrity)
print("Player scoring totals: Verified")

print("\nDemo database successfully created!")
print("Location:", DATABASE)
print("Original MSU database was not modified.")
