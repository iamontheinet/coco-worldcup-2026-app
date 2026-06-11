import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.data_loader import load_teams

st.set_page_config(page_title="Bracket Builder", page_icon="🏆", layout="wide")
st.title("🏆 Knockout Bracket Builder")
st.caption("Pick your winners from the Round of 32 all the way to the Final!")

teams = load_teams()
team_list = teams["TEAM_NAME"].tolist()
team_flags = dict(zip(teams["TEAM_NAME"], teams["FLAG_EMOJI"]))


def team_display(name):
    return f"{team_flags.get(name, '')} {name}" if name else "TBD"


# Seed the bracket: top 2 from each group as placeholders
# Using current FIFA ranking order within each group as default seeding
groups = sorted(teams["GROUP_LETTER"].unique())
group_winners = []
group_runners = []

for g in groups:
    g_teams = teams[teams["GROUP_LETTER"] == g].sort_values("FIFA_RANKING")
    group_winners.append(g_teams.iloc[0]["TEAM_NAME"])
    group_runners.append(g_teams.iloc[1]["TEAM_NAME"])

# Round of 32 matchups (simplified: winner of group vs runner of another)
r32_matchups = [
    (group_winners[0], group_runners[3]),   # A1 vs D2
    (group_winners[1], group_runners[2]),   # B1 vs C2
    (group_winners[2], group_runners[1]),   # C1 vs B2
    (group_winners[3], group_runners[0]),   # D1 vs A2
    (group_winners[4], group_runners[7]),   # E1 vs H2
    (group_winners[5], group_runners[6]),   # F1 vs G2
    (group_winners[6], group_runners[5]),   # G1 vs F2
    (group_winners[7], group_runners[4]),   # H1 vs E2
    (group_winners[8], group_runners[11]),  # I1 vs L2
    (group_winners[9], group_runners[10]),  # J1 vs K2
    (group_winners[10], group_runners[9]),  # K1 vs J2
    (group_winners[11], group_runners[8]),  # L1 vs I2
    (group_winners[0], group_runners[5]),   # Extra R32 slots
    (group_winners[4], group_runners[1]),
    (group_winners[8], group_runners[3]),
    (group_winners[2], group_runners[11]),
]

st.markdown("---")

# Round of 16
st.subheader("🔵 Round of 32 → Round of 16")
st.caption("Select winners for each matchup")

r32_winners = []
cols = st.columns(4)
for i, (t1, t2) in enumerate(r32_matchups):
    with cols[i % 4]:
        options = [t1, t2]
        choice = st.radio(
            f"Match {i+1}",
            options,
            format_func=team_display,
            key=f"r32_{i}",
            horizontal=True,
        )
        r32_winners.append(choice)

# Round of 16
st.markdown("---")
st.subheader("🟢 Round of 16 → Quarter-finals")

r16_matchups = [(r32_winners[i], r32_winners[i + 1]) for i in range(0, 16, 2)]
r16_winners = []
cols = st.columns(4)
for i, (t1, t2) in enumerate(r16_matchups):
    with cols[i % 4]:
        options = [t1, t2]
        choice = st.radio(
            f"R16 Match {i+1}",
            options,
            format_func=team_display,
            key=f"r16_{i}",
            horizontal=True,
        )
        r16_winners.append(choice)

# Quarter-finals
st.markdown("---")
st.subheader("🟡 Quarter-finals → Semi-finals")

qf_matchups = [(r16_winners[i], r16_winners[i + 1]) for i in range(0, 8, 2)]
qf_winners = []
cols = st.columns(4)
for i, (t1, t2) in enumerate(qf_matchups):
    with cols[i % 4]:
        options = [t1, t2]
        choice = st.radio(
            f"QF {i+1}",
            options,
            format_func=team_display,
            key=f"qf_{i}",
            horizontal=True,
        )
        qf_winners.append(choice)

# Semi-finals
st.markdown("---")
st.subheader("🟠 Semi-finals → Final")

sf_matchups = [(qf_winners[i], qf_winners[i + 1]) for i in range(0, 4, 2)]
sf_winners = []
cols = st.columns(2)
for i, (t1, t2) in enumerate(sf_matchups):
    with cols[i]:
        options = [t1, t2]
        choice = st.radio(
            f"Semi-final {i+1}",
            options,
            format_func=team_display,
            key=f"sf_{i}",
            horizontal=True,
        )
        sf_winners.append(choice)

# Final
st.markdown("---")
st.subheader("🏆 THE FINAL — MetLife Stadium, New Jersey")

if len(sf_winners) == 2:
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        st.markdown(f"### {team_display(sf_winners[0])}")
    with col2:
        st.markdown("<h3 style='text-align:center;'>⚡ vs ⚡</h3>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"### {team_display(sf_winners[1])}")

    champion = st.radio(
        "👑 Pick your World Cup Champion!",
        sf_winners,
        format_func=team_display,
        key="final",
        horizontal=True,
    )

    if champion:
        st.markdown("---")
        st.balloons()
        st.markdown(
            f"""
            <div style="text-align:center; padding: 2rem;">
                <h1 style="font-size: 4rem;">{team_flags.get(champion, '🏆')}</h1>
                <h2 style="color: #FFD700;">🏆 {champion} are World Cup Champions! 🏆</h2>
                <p style="font-size: 1.2rem; color: #888;">Your predicted winner of the 2026 FIFA World Cup</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
