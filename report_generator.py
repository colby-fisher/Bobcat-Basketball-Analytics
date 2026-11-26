
from io import BytesIO
from math import isfinite
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

NAVY = colors.HexColor("#002D56")
GOLD = colors.HexColor("#B9975B")
INK = colors.HexColor("#18283B")
MUTED = colors.HexColor("#516378")
PALE = colors.HexColor("#F0F4F8")
GREEN = colors.HexColor("#16714E")
RED = colors.HexColor("#A83239")

FACTORS = [
    (
        "Shooting", "Shooting_Advantage",
        "eFG_PCT", "Opp_eFG_PCT",
        "Review shot selection, finishing and defensive shot contests."
    ),
    (
        "Turnovers", "Turnover_Advantage",
        "TOV_PCT", "Opp_TOV_PCT",
        "Review ball security, passing decisions and defensive pressure."
    ),
    (
        "Rebounding", "Rebounding_Advantage",
        "ORB_PCT", "Opp_ORB_PCT",
        "Review box-outs, positioning and second-chance opportunities."
    ),
    (
        "Free throws", "Free_Throw_Advantage",
        "FT_Rate", "Opp_FT_Rate",
        "Review foul discipline, foul drawing and free throw conversion."
    )
]


def build_game_report(game, season):

    demo = (
        game.get("Data_Type", "") ==
        "SYNTHETIC DEMONSTRATION DATA"
    )

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    c.setTitle("Bobcat Analytics Lab | Postgame Report")
    c.setAuthor("Bobcat Analytics Lab - Independent Project")

    width, height = letter
    left, right = 38, width - 38
    span = right - left

    # Text helper
    def text(x, y, value, size=10, color=INK,
             bold=False, align="left"):

        c.setFillColor(color)

        c.setFont(
            "Helvetica-Bold" if bold else "Helvetica",
            size
        )

        draw = {
            "left": c.drawString,
            "right": c.drawRightString,
            "center": c.drawCentredString
        }[align]

        draw(x, y, str(value))

    # Paragraph helper
    def para(x, y, value, max_width,
             size=9, color=MUTED):

        style = ParagraphStyle(
            "report",
            fontName="Helvetica",
            fontSize=size,
            leading=size + 3,
            textColor=color
        )

        p = Paragraph(escape(str(value)), style)

        _, h = p.wrap(max_width, 100)

        p.drawOn(c, x, y - h)

        return h

    # Rounded rectangle helper
    def rect(x, y, w, h, color):

        c.setFillColor(color)

        c.roundRect(
            x, y, w, h, 7,
            stroke=0,
            fill=1
        )

    # Number formatting
    def fmt(value, suffix="", signed=False):

        try:

            n = float(value)

            if isfinite(n):

                return (
                    f"{n:+.2f}" if signed
                    else f"{n:.2f}"
                ) + suffix

        except (TypeError, ValueError):

            pass

        return "N/A"

    opponent = str(game["Opponent"])
    date = str(game["Date"])[:10]
    won = game["Result"] == "W"

    # =====================================
    # REPORT HEADER
    # =====================================

    c.setFillColor(NAVY)
    c.rect(0, 690, width, 102, fill=1, stroke=0)

    c.setFillColor(GOLD)
    c.rect(0, 686, width, 4, fill=1, stroke=0)

    text(
        left, 761,
        "BOBCAT ANALYTICS LAB",
        11, GOLD, True
    )

    text(
        left, 730,
        "DEMO | Postgame report" if demo else "Postgame performance report",
        24, colors.white, True
    )

    text(
        left, 708,
        f"Men's basketball | {season} | {date}",
        10, colors.white
    )

    # =====================================
    # FINAL SCORE
    # =====================================

    rect(left, 590, span, 81, PALE)

    teams = [
        (
            left + span * .25,
            "Demo Team" if demo else "Montana State",
            game["MSU_Points"]
        ),
        (
            left + span * .75,
            opponent,
            game["Opponent_Points"]
        )
    ]

    for x, name, score in teams:

        label_size = 12

        while (
            c.stringWidth(
                name, "Helvetica-Bold", label_size
            ) > span * .43
            and label_size > 7
        ):
            label_size -= .5

        text(
            x, 650, name,
            label_size, NAVY, True, "center"
        )

        text(
            x, 618, int(score),
            29, NAVY, True, "center"
        )

    result = "WIN" if won else "LOSS"

    text(
        width / 2,
        603,
        f"{result} | "
        f"{float(game['Point_Differential']):+.0f} points",
        10,
        GREEN if won else RED,
        True,
        "center"
    )

    # =====================================
    # EFFICIENCY METRICS
    # =====================================

    metrics = [
        ("OFFENSIVE RTG", fmt(game["Off_Rating"])),
        ("DEFENSIVE RTG", fmt(game["Def_Rating"])),
        (
            "NET RATING",
            fmt(game["Net_Rating"], signed=True)
        ),
        (
            "FACTORS WON",
            f"{int(game['Factors_Won'])}/4"
        )
    ]

    gap = 8
    card_w = (span - 3 * gap) / 4

    for i, (label, value) in enumerate(metrics):

        x = left + i * (card_w + gap)

        rect(x, 522, card_w, 57, PALE)

        text(x + 10, 559, label, 8, MUTED, True)

        text(x + 10, 536, value, 19, NAVY, True)

    # =====================================
    # FOUR FACTORS
    # =====================================

    text(
        left, 501,
        "Four Factors matchup",
        15, NAVY, True
    )

    text(
        left, 485,
        ("Positive differential favors Demo Team; " if demo else "Positive differential favors Montana State; ") +
        "lower turnover rate is better.",
        9, MUTED
    )

    text(left, 462, "FACTOR", 8, MUTED, True)
    text(233, 462, "MSU", 8, MUTED, True, "right")
    text(299, 462, "OPP", 8, MUTED, True, "right")

    text(
        right, 462,
        "ADVANTAGE (pp)",
        8, MUTED, True, "right"
    )

    scale = max(
        10,
        max(
            abs(float(game[key]))
            for _, key, *_ in FACTORS
        )
    )

    center = 408

    for i, (name, key, own, opp, _) in enumerate(FACTORS):

        y = 439 - i * 29
        value = float(game[key])

        if i % 2 == 0:
            rect(left, y - 9, span, 24, PALE)

        text(left + 7, y, name, 10, INK, True)

        text(
            233, y, fmt(game[own], "%"),
            10, INK, align="right"
        )

        text(
            299, y, fmt(game[opp], "%"),
            10, INK, align="right"
        )

        c.setStrokeColor(
            colors.HexColor("#BCC9D6")
        )

        c.line(center, y - 5, center, y + 10)

        color = (
            GREEN if value > 0
            else RED if value < 0
            else MUTED
        )

        bar = abs(value) / scale * 83

        c.setFillColor(color)

        if bar:

            c.rect(
                center if value > 0 else center - bar,
                y - 1,
                bar,
                8,
                stroke=0,
                fill=1
            )

        text(
            right - 7,
            y,
            fmt(value, signed=True),
            10, color, True, "right"
        )

    # =====================================
    # COACHING INTELLIGENCE
    # =====================================

    text(
        left, 321,
        "Coaching review priorities",
        15, NAVY, True
    )

    negatives = sorted(
        (
            f for f in FACTORS
            if float(game[f[1]]) < 0
        ),
        key=lambda f: float(game[f[1]])
    )

    positives = sorted(
        (
            f for f in FACTORS
            if float(game[f[1]]) > 0
        ),
        key=lambda f: float(game[f[1]]),
        reverse=True
    )

    y = 303

    # Display the two largest disadvantages
    for factor in negatives[:2]:

        name, key, _, _, prompt = factor

        text(
            left, y,
            f"{name} | {fmt(game[key], ' pp', True)}",
            11, RED, True
        )

        h = para(left, y - 5, prompt, span)

        y -= h + 24

    if not negatives:

        text(
            left, y,
            "No negative Four Factors differentials.",
            10, GREEN, True
        )

        y -= 33

    if positives:

        name, key, _, _, _ = positives[0]

        text(
            left, y,
            f"Strongest advantage: {name} "
            f"({fmt(game[key], ' pp', True)})",
            11, GREEN, True
        )

    else:

        text(
            left, y,
            "No positive Four Factors differentials.",
            10, MUTED
        )

    # =====================================
    # BOX SCORE SNAPSHOT
    # =====================================

    text(
        left, 177,
        "Box score snapshot",
        15, NAVY, True
    )

    stats = [
        ("FG", "FGM", "FGA"),
        ("3PT", "3PM", "3PA"),
        ("FT", "FTM", "FTA"),
        ("REB", "REB", None),
        ("AST", "AST", None),
        ("TO", "TOV", None)
    ]

    col_w = (span - 55) / len(stats)

    rect(left, 103, span, 62, PALE)

    for i, (label, a, b) in enumerate(stats):

        x = left + 55 + col_w * (i + .5)

        text(
            x, 150, label,
            8, MUTED, True, "center"
        )

        for prefix, row_y in [
            ("", 132),
            ("Opp_", 115)
        ]:

            value = str(int(game[prefix + a]))

            if b:
                value += "-" + str(int(game[prefix + b]))

            text(
                x, row_y, value,
                10, INK, False, "center"
            )

    text(left + 8, 132, "MSU", 9, NAVY, True)
    text(left + 8, 115, "OPP", 9, MUTED, True)

    # =====================================
    # METHODOLOGY AND SOURCE
    # =====================================

    c.setStrokeColor(
        colors.HexColor("#D2DCE6")
    )

    c.line(left, 87, right, 87)

    para(
        left, 79,
        "Ratings use estimated possessions. "
        "Free throw rate = FTM/FGA. "
        "Review topics are descriptive prompts, "
        "not causal findings. "
        "Not adjusted for opponent strength.",
        span, 8
    )

    text(
        left, 43,
        ("SYNTHETIC DATA - Not actual MSU statistics | "
     if demo else
     "Source: Montana State Athletics | ") +
        "Independent project, not affiliated with MSU.",
        8, MUTED
    )

    url = str(game.get("Box_Score_URL", ""))

    if url.startswith("https://msubobcats.com/"):

        text(
            left, 28,
            "Official box score (click to open)",
            8, NAVY, True
        )

        c.linkURL(
            url,
            (left, 25, left + 160, 38),
            relative=0
        )

    text(right, 28, "01", 9, MUTED, True, "right")

    c.showPage()
    c.save()

    return buffer.getvalue()
