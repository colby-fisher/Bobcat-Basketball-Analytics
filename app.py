
import streamlit as st
import pandas as pd
import plotly.express as px

from pathlib import Path

# ==========================================
# APPLICATION CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Bobcat Analytics Lab",
    page_icon="🏀",
    layout="wide"
)

NAVY = "#6499D0"
GOLD = "#D6B778"
RED = "#F87171"
GREEN = "#4ADE80"

DATA = Path(__file__).resolve().parent / "data" / "cleaned"


st.markdown("""
<style>

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1600px;
}

[data-testid="stMetric"] {
    background-color: #151E2D;
    border: 1px solid #29384D;
    border-top: 3px solid #B9975B;
    border-radius: 10px;
    padding: 18px;
}

[data-testid="stMetricLabel"] {
    color: #AAB5C5;
}

[data-testid="stMetricValue"] {
    font-size: 2rem;
    font-weight: 700;
}

.bobcat-header {
    background: linear-gradient(
        110deg, #002D56, #151E2D
    );
    padding: 18px 24px;
    border-radius: 10px;
    border-left: 5px solid #B9975B;
    margin-bottom: 12px;
}

.bobcat-header h1 {
    font-size: 2rem !important;
    letter-spacing: 1px;
    padding: 0 !important;
    margin: 5px 0 !important;
}

.bobcat-header p {
    font-size: 0.85rem;
    padding: 0 !important;
}

[data-testid="stSidebar"] {
    border-right: 1px solid #29384D;
}

h2, h3 {
    letter-spacing: -0.5px;
}

hr {
    border-color: #29384D;
    margin: 1.2rem 0;
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.title("BOBCAT ANALYTICS")
st.sidebar.caption("Basketball Intelligence Platform")
st.sidebar.caption("Data source: SQLite Database")

season = st.sidebar.selectbox(
    "Select season",
    ["2026-27", "2025-26"]
)

competition = st.sidebar.radio(
    "Competition",
    ["Division I only", "All opponents"]
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Executive Overview",
        "Team Analytics",
        "Game Analysis",
        "Player Evaluation",
        "Opponent Scouting",
        "Season Comparison"
    ]
)

if st.sidebar.button("Reload local data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()

st.sidebar.caption(
    "Independent analytics project using publicly "
    "available Montana State basketball statistics."
)

# ==========================================
# LOAD DATA
# ==========================================

DATA = Path(__file__).resolve().parent / "data" / "cleaned"


@st.cache_data
def load_csv(filename):

    import sqlite3
    from contextlib import closing

    database = DATA.parent / "bobcat_analytics.db"

    if not database.exists():
        raise FileNotFoundError(
            "Database missing. Run src/12_build_database.py"
        )

    queries = {
        "four_factors_games_2025_26.csv": (
            "SELECT * FROM games "
            "WHERE Season = ? ORDER BY Date",
            ("2025-26",)
        ),

        "season_analysis_2026_27.csv": (
            "SELECT * FROM games "
            "WHERE Season = ? ORDER BY Date",
            ("2026-27",)
        ),

        "advanced_player_stats_2025_26.csv": (
            "SELECT * FROM player_seasons "
            "WHERE Season = ? ORDER BY PPG DESC",
            ("2025-26",)
        ),

        "advanced_player_stats_2026_27.csv": (
            "SELECT * FROM player_seasons "
            "WHERE Season = ? ORDER BY PPG DESC",
            ("2026-27",)
        ),

        "big_sky_opponent_scouting.csv": (
            "SELECT * FROM opponent_scouting "
            "WHERE Season = ? ORDER BY Margin DESC",
            ("2025-26",)
        )
    }

    query, parameters = queries[filename]

    with closing(sqlite3.connect(
        database.as_uri() + "?mode=ro",
        uri=True
    )) as conn:

        df = pd.read_sql_query(
            query,
            conn,
            params=parameters
        )

    
    # Restore Boolean values from SQLite
    if "Division_I" in df.columns:
        df["Division_I"] = (
            df["Division_I"].astype(str).str.lower()
            .map({
                "1": True,
                "1.0": True,
                "true": True,
                "0": False,
                "0.0": False,
                "false": False
            })
            .astype("boolean")
        )

    return df




game_files = {
    "2025-26": "four_factors_games_2025_26.csv",
    "2026-27": "season_analysis_2026_27.csv"
}

player_files = {
    "2025-26": "advanced_player_stats_2025_26.csv",
    "2026-27": "advanced_player_stats_2026_27.csv"
}


games = load_csv(game_files[season]).copy()
players = load_csv(player_files[season]).copy()

games["Date"] = pd.to_datetime(games["Date"])
if not games.empty and games["Date"].notna().any():
    latest_game_date = games["Date"].max()

    st.sidebar.caption(
        f"Data through: {latest_game_date.strftime('%b %d, %Y')}"
    )
if competition == "Division I only":
    games = games[
        games["Division_I"].astype(str)
        .str.lower() == "true"
    ].copy()

games = games.sort_values("Date")

if games.empty:
    st.warning("No games match your selection.")
    st.stop()

wins = (games["Result"] == "W").sum()
losses = (games["Result"] == "L").sum()

factor_columns = [
    "Shooting_Advantage",
    "Turnover_Advantage",
    "Rebounding_Advantage",
    "Free_Throw_Advantage"
]

factor_labels = {
    "Shooting_Advantage": "Shooting",
    "Turnover_Advantage": "Turnovers",
    "Rebounding_Advantage": "Rebounding",
    "Free_Throw_Advantage": "Free Throws"
}


# ==========================================
# LOAD DATA
# ==========================================

@st.cache_data
def load_csv(filename):
    return pd.read_csv(DATA / filename)


game_files = {
    "2025-26": "four_factors_games_2025_26.csv",
    "2026-27": "season_analysis_2026_27.csv"
}

player_files = {
    "2025-26": "advanced_player_stats_2025_26.csv",
    "2026-27": "advanced_player_stats_2026_27.csv"
}

# ==========================================
# APPLICATION HEADER
# ==========================================

st.markdown(
    f"""
    <div class="bobcat-header">
        <p style="color:#D6B778; margin:0;">
            BASKETBALL INTELLIGENCE PLATFORM
        </p>
        <h1 style="color:white; margin:8px 0;">
            BOBCAT ANALYTICS LAB
        </h1>
        <p style="color:#D6B778; margin:0;">
            Montana State Basketball | {season}
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption(
    f"{len(games)} games in selected team dataset | "
    f"Latest included game: "
    f"{games['Date'].max().strftime('%B %d, %Y')}"
)


# ==========================================
# EXECUTIVE OVERVIEW
# ==========================================


if page == "Executive Overview":

    st.header("Season Overview")

    # Historical comparison baseline
    historical = load_csv(
        game_files["2025-26"]
    ).copy()

    if competition == "Division I only":
        historical = historical[
            historical["Division_I"].astype(str)
            .str.lower() == "true"
        ]

    # Calculate current efficiency ratings
    off = games["Off_Rating"].mean()
    defense = games["Def_Rating"].mean()
    net = games["Net_Rating"].mean()

    # Year-over-year changes
    off_delta = None
    def_delta = None
    net_delta = None

    if season == "2026-27":
        off_delta = off - historical["Off_Rating"].mean()
        def_delta = defense - historical["Def_Rating"].mean()
        net_delta = net - historical["Net_Rating"].mean()

    # KPI cards
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Record", f"{wins}-{losses}")

    c2.metric(
        "Win Percentage",
        f"{wins / len(games):.1%}"
    )

    c3.metric(
        "Offensive Rating",
        f"{off:.2f}",
        delta=(
            f"{off_delta:+.2f}"
            if off_delta is not None else None
        )
    )

    c4.metric(
        "Defensive Rating",
        f"{defense:.2f}",
        delta=(
            f"{def_delta:+.2f}"
            if def_delta is not None else None
        ),
        delta_color="inverse"
    )

    c5.metric(
        "Net Rating",
        f"{net:+.2f}",
        delta=(
            f"{net_delta:+.2f}"
            if net_delta is not None else None
        )
    )

    if season == "2026-27":
        st.caption(
            "Rating changes compared with the "
            "2025-26 season using the selected "
            "competition filter."
        )

    # ======================================
    # AUTOMATED COACHING INTELLIGENCE
    # ======================================

    st.subheader("Coaching Intelligence")

    averages = games[factor_columns].mean()

    explanations = {
        "Shooting_Advantage":
            "Compare shot quality, finishing and "
            "opponent shooting efficiency.",

        "Turnover_Advantage":
            "Review ball security, defensive "
            "pressure and forced turnovers.",

        "Rebounding_Advantage":
            "Review box-outs, offensive rebounding "
            "and second-chance opportunities.",

        "Free_Throw_Advantage":
            "Review foul discipline, foul drawing "
            "and free throw conversion."
    }

    priorities = averages.sort_values()

    # Largest disadvantages appear first
    for column, value in priorities.items():

        color = GREEN if value > 0 else (
            RED if value < 0 else "#AAB5C5"
        )

        if value > 0:
            status = "Statistical Advantage"
        elif value < 0:
            status = "Film Review Priority"
        else:
            status = "Even Matchup"

        st.markdown(
            f"""
            <div style="
                background:#151E2D;
                border:1px solid #29384D;
                border-left:4px solid {color};
                border-radius:8px;
                padding:14px 18px;
                margin-bottom:10px;
                display:flex;
                justify-content:space-between;
                align-items:center;
                gap:16px;
            ">
                <div>
                    <div style="
                        color:{color};
                        font-size:11px;
                        font-weight:700;
                        text-transform:uppercase;
                    ">
                        {status}
                    </div>
                    <div style="
                        font-size:17px;
                        font-weight:600;
                        margin:4px 0;
                    ">
                        {factor_labels[column]}
                    </div>
                    <div style="
                        color:#AAB5C5;
                        font-size:13px;
                    ">
                        {explanations[column]}
                    </div>
                </div>
                <div style="
                    color:{color};
                    font-size:24px;
                    font-weight:700;
                    white-space:nowrap;
                ">
                    {value:+.2f} pp
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.caption(
        "Automatically generated from selected games. "
        "These are descriptive findings and suggested "
        "film-review topics, not causal conclusions."
    )

    st.divider()

    # ======================================
    # PERFORMANCE VISUALIZATIONS
    # ======================================

    left, right = st.columns(2)

    chart = games.copy()

    chart["Matchup"] = (
        chart["Date"].dt.strftime("%m/%d")
        + " " + chart["Opponent"]
    )

    with left:

        st.subheader("Scoring Trends")

        scoring = chart[[
    "Matchup",
    "MSU_Points",
    "Opponent_Points"
]].rename(columns={
    "MSU_Points": "Montana State",
    "Opponent_Points": "Opponent"
})

        fig = px.line(
            scoring,
            x="Matchup",
            y=["Montana State", "Opponent"],
            markers=True,
            color_discrete_sequence=[GOLD, NAVY],
            labels={
                "value": "Points",
                "variable": "Team",
                "Matchup": "Game"
            }
        )

        fig.update_traces(
            line=dict(width=3),
            marker=dict(size=8)
        )

        fig.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(
                orientation="h",
                y=1.12
            )
        )

        st.plotly_chart(fig, width="stretch")

    with right:

        st.subheader("Game-by-Game Net Rating")

        fig = px.bar(
            chart,
            x="Matchup",
            y="Net_Rating",
            color="Result",
            text_auto=".1f",
            color_discrete_map={
                "W": GOLD,
                "L": RED
            },
            labels={
                "Net_Rating": "Net Rating",
                "Matchup": "Game"
            }
        )

        fig.add_hline(
            y=0,
            line_color="#AAB5C5"
        )

        fig.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=20, b=10),
            showlegend=False
        )

        st.plotly_chart(fig, width="stretch")

    # ======================================
    # GAME RESULTS
    # ======================================

    st.subheader("Game Results")

    display = games[[
        "Date",
        "Opponent",
        "Result",
        "MSU_Points",
        "Opponent_Points",
        "Off_Rating",
        "Def_Rating",
        "Net_Rating",
        "Factors_Won"
    ]].copy()

    display["Date"] = (
        display["Date"].dt.strftime("%m/%d/%Y")
    )

    display = display.rename(columns={
        "MSU_Points": "MSU",
        "Opponent_Points": "OPP",
        "Off_Rating": "ORtg",
        "Def_Rating": "DRtg",
        "Net_Rating": "Net Rating",
        "Factors_Won": "Factors Won"
    })

    st.dataframe(
        display.round(2),
        hide_index=True,
        width="stretch"
    )

    st.caption(
        "Ratings are unweighted averages of "
        "game-level possession estimates. "
        "Opponent strength is not adjusted."
    )


# ==========================================
# TEAM ANALYTICS
# ==========================================

elif page == "Team Analytics":

    st.header("Team Performance Analytics")

    st.subheader("Offense vs. Defense")

    fig = px.scatter(
        games,
        x="Off_Rating",
        y="Def_Rating",
        color="Result",
        hover_name="Opponent",
        color_discrete_map={
            "W": NAVY,
            "L": GOLD
        },
        labels={
            "Off_Rating": "Offensive Rating",
            "Def_Rating": "Defensive Rating"
        }
    )

    fig.update_traces(marker_size=12)

    low = min(
        games["Off_Rating"].min(),
        games["Def_Rating"].min()
    )

    high = max(
        games["Off_Rating"].max(),
        games["Def_Rating"].max()
    )

    fig.add_shape(
        type="line",
        x0=low, y0=low,
        x1=high, y1=high,
        line=dict(color="gray", dash="dash")
    )

    st.plotly_chart(fig, width="stretch")

    st.subheader("Four Factors by Game")

    heatmap = games[factor_columns].copy()

    heatmap.columns = [
        factor_labels[c] for c in factor_columns
    ]

    heatmap.index = (
        games["Date"].dt.strftime("%m/%d")
        + " " + games["Opponent"]
    )

    fig = px.imshow(
        heatmap,
        text_auto=".1f",
        color_continuous_scale="RdBu",
        color_continuous_midpoint=0,
        aspect="auto"
    )

    fig.update_layout(
        height=max(400, len(games) * 28)
    )

    st.plotly_chart(fig, width="stretch")

    st.subheader("Winning Percentage by Factors Won")

    analysis = games.copy()

    analysis["Win"] = (
        analysis["Result"] == "W"
    ).astype(int)

    factor_results = analysis.groupby(
        "Factors_Won"
    ).agg(
        Games=("Win", "count"),
        Wins=("Win", "sum")
    ).reset_index()

    factor_results["Win_PCT"] = (
        factor_results["Wins"]
        / factor_results["Games"]
    ) * 100

    fig = px.bar(
        factor_results,
        x="Factors_Won",
        y="Win_PCT",
        text="Games",
        hover_data=["Wins", "Games"],
        color_discrete_sequence=[NAVY],
        labels={
            "Factors_Won": "Four Factors Won",
            "Win_PCT": "Winning Percentage (%)"
        }
    )

    fig.update_yaxes(range=[0, 110])

    st.plotly_chart(fig, width="stretch")

    st.caption(
        "Bar labels show sample sizes. These are "
        "historical outcomes, not predictions."
    )

    st.subheader("Wins vs. Losses")

    metrics = [
        "Off_Rating",
        "Def_Rating",
        "eFG_PCT",
        "Opp_eFG_PCT",
        "TOV_PCT",
        "ORB_PCT",
        "FT_Rate"
    ]

    comparison = games.groupby(
        "Result"
    )[metrics].mean().T

    st.dataframe(
        comparison.round(2),
        width="stretch"
    )


# ==========================================
# PLAYER EVALUATION
# ==========================================

elif page == "Game Analysis":

    st.header("Individual Game Analysis")

    # Create game selection options
    game_options = games.copy()

    game_options["Game_Label"] = (
        game_options["Date"].dt.strftime("%m/%d/%Y")
        + " | "
        + game_options["Opponent"]
        + " | "
        + game_options["Result"]
    )

    selected_game = st.selectbox(
        "Select a game",
        game_options["Game_Label"].tolist()[::-1]
    )

    game = game_options[
        game_options["Game_Label"] == selected_game
    ].iloc[0]

    result = "WIN" if game["Result"] == "W" else "LOSS"

    result_color = (
        GREEN if game["Result"] == "W" else RED
    )

    
    # Scoreboard
    with st.container(border=True):

        st.markdown(
            "<p style='text-align:center; color:#AAB5C5;'>"
            "FINAL SCORE</p>",
            unsafe_allow_html=True
        )

        home, versus, away = st.columns([4, 1, 4])

        with home:
            st.markdown(
                f"""
<h4 style="text-align:center; color:#D6B778;">MONTANA STATE</h4>
<h1 style="text-align:center; font-size:60px;">{int(game['MSU_Points'])}</h1>
""",
                unsafe_allow_html=True
            )

        with versus:
            st.markdown(
                "<h3 style='text-align:center;'>VS</h3>",
                unsafe_allow_html=True
            )

        with away:
            st.markdown(
                f"""
<h4 style="text-align:center;">{game['Opponent'].upper()}</h4>
<h1 style="text-align:center; font-size:60px;">{int(game['Opponent_Points'])}</h1>
""",
                unsafe_allow_html=True
            )

        st.markdown(
            f"<h4 style='text-align:center; color:{result_color};'>"
            f"{result} | {game['Point_Differential']:+.0f} POINTS"
            f"</h4>",
            unsafe_allow_html=True
        )

    st.write("")


    # Efficiency metrics
    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Offensive Rating",
        f"{game['Off_Rating']:.2f}"
    )

    c2.metric(
        "Defensive Rating",
        f"{game['Def_Rating']:.2f}"
    )

    c3.metric(
        "Net Rating",
        f"{game['Net_Rating']:+.2f}"
    )

    c4.metric(
        "Four Factors Won",
        f"{int(game['Factors_Won'])}/4"
    )

    # Four Factors visualization
    st.subheader("Four Factors Matchup Breakdown")

    factors = pd.DataFrame({
        "Factor": [
            factor_labels[c]
            for c in factor_columns
        ],
        "Advantage": [
            game[c]
            for c in factor_columns
        ]
    })

    factors["Status"] = factors["Advantage"].apply(
        lambda x: "MSU Advantage" if x > 0
        else "Opponent Advantage" if x < 0
        else "Even"
    )

    fig = px.bar(
        factors,
        x="Advantage",
        y="Factor",
        orientation="h",
        color="Status",
        text_auto=".2f",
        color_discrete_map={
            "MSU Advantage": GREEN,
            "Opponent Advantage": RED,
            "Even": "#64748B"
        }
    )

    fig.add_vline(
        x=0,
        line_color="#AAB5C5"
    )

    fig.update_layout(
        height=350,
        xaxis_title="Advantage (Percentage Points)",
        yaxis_title="",
        legend_title=""
    )

    st.plotly_chart(fig, width="stretch")

    # Head-to-head box score
    st.subheader("Head-to-Head Statistics")

    comparison = pd.DataFrame({
        "Statistic": [
            "Field Goals",
            "Three-Pointers",
            "Free Throws",
            "Offensive Rebounds",
            "Defensive Rebounds",
            "Total Rebounds",
            "Assists",
            "Turnovers",
            "Steals",
            "Blocks",
            "Personal Fouls",
            "Effective FG%",
            "Turnover Rate",
            "Offensive Rebound %",
            "Free Throw Scoring Rate"
        ],

        "Montana State": [
            f"{game['FGM']}-{game['FGA']}",
            f"{game['3PM']}-{game['3PA']}",
            f"{game['FTM']}-{game['FTA']}",
            str(game["OREB"]),
            str(game["DREB"]),
            str(game["REB"]),
            str(game["AST"]),
            str(game["TOV"]),
            str(game["STL"]),
            str(game["BLK"]),
            str(game["PF"]),
            f"{game['eFG_PCT']:.2f}%",
            f"{game['TOV_PCT']:.2f}%",
            f"{game['ORB_PCT']:.2f}%",
            f"{game['FT_Rate']:.2f}%"
        ],

        game["Opponent"]: [
            f"{game['Opp_FGM']}-{game['Opp_FGA']}",
            f"{game['Opp_3PM']}-{game['Opp_3PA']}",
            f"{game['Opp_FTM']}-{game['Opp_FTA']}",
            str(game["Opp_OREB"]),
            str(game["Opp_DREB"]),
            str(game["Opp_REB"]),
            str(game["Opp_AST"]),
            str(game["Opp_TOV"]),
            str(game["Opp_STL"]),
            str(game["Opp_BLK"]),
            str(game["Opp_PF"]),
            f"{game['Opp_eFG_PCT']:.2f}%",
            f"{game['Opp_TOV_PCT']:.2f}%",
            f"{game['Opp_ORB_PCT']:.2f}%",
            f"{game['Opp_FT_Rate']:.2f}%"
        ]
    })

    st.dataframe(
        comparison,
        hide_index=True,
        width="stretch"
    )

    # Automated game insights
    st.subheader("Postgame Coaching Intelligence")

    explanations = {
        "Shooting":
            "Review shot selection, finishing "
            "and defensive shot contests.",

        "Turnovers":
            "Review ball security, passing "
            "decisions and defensive pressure.",

        "Rebounding":
            "Review box-outs, positioning "
            "and second-chance opportunities.",

        "Free Throws":
            "Review foul discipline, foul drawing "
            "and free throw conversion."
    }

    weaknesses = factors[
        factors["Advantage"] < 0
    ].sort_values("Advantage")

    strengths = factors[
        factors["Advantage"] > 0
    ].sort_values(
        "Advantage",
        ascending=False
    )

    left, right = st.columns(2)

    with left:

        st.markdown("#### Film Review Priorities")

        if weaknesses.empty:
            st.info(
                "No negative Four Factors differentials."
            )

        for _, row in weaknesses.iterrows():

            st.error(
                f"**{row['Factor']}** | "
                f"{row['Advantage']:+.2f} pp\n\n"
                f"{explanations[row['Factor']]}"
            )

    with right:

        st.markdown("#### Statistical Advantages")

        if strengths.empty:
            st.info(
                "No positive Four Factors differentials."
            )

        for _, row in strengths.iterrows():

            st.success(
                f"**{row['Factor']}** | "
                f"{row['Advantage']:+.2f} pp"
            )

    st.caption(
        "Insights are generated from box-score "
        "statistics. Film review is needed to "
        "establish the causes of these differences."
    )

    # Link to official source
    st.link_button(
        "View Official Game Box Score",
        game["Box_Score_URL"]
    )

    # PDF postgame report
    from report_generator import build_game_report

    st.subheader("Postgame Report")

    pdf_report = build_game_report(game, season)

    st.download_button(
        label="Download PDF Postgame Report",
        data=pdf_report,
        file_name=(
            f"MSU_Postgame_"
            f"{game['Date'].strftime('%Y_%m_%d')}.pdf"
        ),
        mime="application/pdf",
        type="primary"
    )


    # Download individual game data
    st.download_button(
        "Download Game Analysis",
        game.to_frame().T.to_csv(index=False),
        file_name=(
            f"game_analysis_"
            f"{game['Date'].strftime('%Y_%m_%d')}.csv"
        ),
        mime="text/csv"
    )



elif page == "Player Evaluation":

    st.header("Player Evaluation")

    st.info(
        "Player statistics include all opponents, "
        "regardless of the team competition filter."
    )

    minimum = st.slider(
        "Minimum field goal attempts",
        min_value=0,
        max_value=int(players["FGA"].max()),
        value=min(
            20 if season == "2026-27" else 50,
            int(players["FGA"].max())
        )
    )

    qualified = players[
        players["FGA"] >= minimum
    ].copy()

    st.subheader("Scoring Volume vs. Efficiency")

    chart = qualified.dropna(
        subset=["TS_PCT", "FGA_Per_Game"]
    )

    fig = px.scatter(
        chart,
        x="FGA_Per_Game",
        y="TS_PCT",
        text="Player",
        hover_name="Player",
        size="FGA",
        color_discrete_sequence=[NAVY],
        hover_data=["PPG", "GP"],
        labels={
            "FGA_Per_Game": "Attempts Per Game",
            "TS_PCT": "True Shooting (%)"
        }
    )

    fig.update_traces(textposition="top center")

    if not chart.empty:

        fig.add_hline(
            y=chart["TS_PCT"].mean(),
            line_dash="dash"
        )

        fig.add_vline(
            x=chart["FGA_Per_Game"].mean(),
            line_dash="dash"
        )

    st.plotly_chart(fig, width="stretch")

    st.subheader("Player Performance Leaderboard")

    sort_metric = st.selectbox(
        "Rank players by",
        [
            "PPG", "RPG", "APG",
            "TS_PCT", "eFG_PCT",
            "3P_PCT", "AST_TO"
        ]
    )

    leaderboard = qualified.sort_values(
        sort_metric, ascending=False
    )

    st.dataframe(
        leaderboard[[
            "Player", "GP", "PPG",
            "RPG", "APG", "FGA",
            "TS_PCT", "eFG_PCT",
            "3PA", "3P_PCT", "AST_TO"
        ]].round(2),
        hide_index=True,
        use_container_width=True
    )

    st.subheader("Individual Player Profile")

    selected = st.selectbox(
        "Select player",
        players["Player"].tolist()
    )

    player = players[
        players["Player"] == selected
    ].iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Points", f"{player['PPG']:.1f}")
    c2.metric("Rebounds", f"{player['RPG']:.1f}")
    c3.metric("Assists", f"{player['APG']:.1f}")

    ts = player["TS_PCT"]

    c4.metric(
        "True Shooting",
        f"{ts:.1f}%" if pd.notna(ts) else "N/A"
    )

    st.caption(
        f"Per-game counting statistics | "
        f"{player['GP']} games played | "
        f"{player['FGA']} field goal attempts"
    )

    st.download_button(
        "Download player statistics",
        players.to_csv(index=False),
        file_name=f"player_stats_{season}.csv",
        mime="text/csv"
    )


# ==========================================
# OPPONENT SCOUTING
# ==========================================

elif page == "Opponent Scouting":

    st.header("Opponent Scouting")

    st.caption(
        "Historical 2025-26 Big Sky regular-season "
        "matchups, independent of sidebar filters."
    )

    scouting = load_csv(
        "big_sky_opponent_scouting.csv"
    )

    opponent = st.selectbox(
        "Select Big Sky opponent",
        scouting["Opponent"].tolist()
    )

    profile = scouting[
        scouting["Opponent"] == opponent
    ].iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Historical Record",
        f"{int(profile['Wins'])}-"
        f"{int(profile['Losses'])}"
    )

    c2.metric(
        "Average Margin",
        f"{profile['Margin']:+.2f}"
    )

    c3.metric(
        "Offensive Rating",
        f"{profile['Off_Rating']:.2f}"
    )

    c4.metric(
        "Defensive Rating",
        f"{profile['Def_Rating']:.2f}"
    )

    st.subheader("Historical Four Factors Profile")

    factors = pd.DataFrame({
        "Factor": [
            "Shooting",
            "Turnovers",
            "Rebounding",
            "Free Throws"
        ],
        "Advantage": [
            profile["Shooting"],
            profile["Turnovers"],
            profile["Rebounding"],
            profile["Free_Throws"]
        ]
    })

    factors["Status"] = factors["Advantage"].apply(
        lambda x: "MSU Advantage" if x > 0
        else "Opponent Advantage" if x < 0
        else "Even"
    )

    fig = px.bar(
        factors,
        x="Advantage",
        y="Factor",
        orientation="h",
        color="Status",
        color_discrete_map={
            "MSU Advantage": NAVY,
            "Opponent Advantage": GOLD,
            "Even": "gray"
        },
        text_auto=".2f"
    )

    fig.update_layout(xaxis_title="Percentage Points")

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Potential Film Review Priorities")

    for _, row in factors.iterrows():

        if row["Advantage"] < 0:

            st.write(
                f"- {row['Factor']}: "
                f"{row['Advantage']:+.2f} pp"
            )

    st.warning(
        "These profiles are based on two historical "
        "games per opponent. They are not complete "
        "current-season scouting reports."
    )

    st.subheader("Conference Matchup Database")

    st.dataframe(
        scouting.round(2),
        hide_index=True,
        use_container_width=True
    )


# ==========================================
# SEASON COMPARISON
# ==========================================

elif page == "Season Comparison":

    st.header("Year-over-Year Performance")

    historical = load_csv(
        game_files["2025-26"]
    )

    current = load_csv(
        game_files["2026-27"]
    )

    historical = historical[
        historical["Division_I"].astype(str)
        .str.lower() == "true"
    ]

    current = current[
        current["Division_I"].astype(str)
        .str.lower() == "true"
    ]

    st.caption(
        f"Division I games only | "
        f"2025-26: {len(historical)} games | "
        f"2026-27: {len(current)} games"
    )

    metrics = [
        "MSU_Points",
        "Opponent_Points",
        "Off_Rating",
        "Def_Rating",
        "Net_Rating",
        "eFG_PCT",
        "Opp_eFG_PCT",
        "TOV_PCT",
        "Opp_TOV_PCT",
        "ORB_PCT",
        "Opp_ORB_PCT",
        "FT_Rate",
        "Opp_FT_Rate",
        "3PAr"
    ]

    comparison = pd.DataFrame({
        "2025-26": historical[metrics].mean(),
        "2026-27": current[metrics].mean()
    })

    comparison["Change"] = (
        comparison["2026-27"]
        - comparison["2025-26"]
    )

    st.dataframe(
        comparison.round(2),
        use_container_width=True
    )

    st.subheader("Four Factors Comparison")

    factor_comparison = pd.DataFrame({
        "2025-26": historical[factor_columns].mean(),
        "2026-27": current[factor_columns].mean()
    })

    factor_comparison.index = [
        factor_labels[c]
        for c in factor_comparison.index
    ]

    fig = px.bar(
        factor_comparison,
        barmode="group",
        color_discrete_sequence=[GOLD, NAVY],
        labels={
            "value": "Advantage (pp)",
            "variable": "Season"
        }
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Returning Player Development")

    old_players = load_csv(
        player_files["2025-26"]
    )

    new_players = load_csv(
        player_files["2026-27"]
    )

    returning = old_players[[
        "Player", "GP", "PPG", "TS_PCT"
    ]].merge(
        new_players[[
            "Player", "GP", "PPG", "TS_PCT"
        ]],
        on="Player",
        suffixes=("_25_26", "_26_27")
    )

    returning["PPG_Change"] = (
        returning["PPG_26_27"]
        - returning["PPG_25_26"]
    )

    returning["TS_Change"] = (
        returning["TS_PCT_26_27"]
        - returning["TS_PCT_25_26"]
    )

    st.dataframe(
        returning.sort_values(
            "PPG_Change",
            ascending=False
        ).round(2),
        hide_index=True,
        use_container_width=True
    )

    st.caption(
        "Player comparison includes all opponents. "
        "Differences in playing time, roster roles, "
        "schedule strength and sample size apply."
    )


# ==========================================
# DOWNLOADS AND FOOTER
# ==========================================

st.divider()

st.download_button(
    "Download selected game dataset",
    games.to_csv(index=False),
    file_name=f"bobcat_games_{season}.csv",
    mime="text/csv"
)

st.caption(
    "Data source: Montana State Athletics | "
    "Independent portfolio project | "
    "Not affiliated with Montana State University"
)
