import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.data_loader import load_teams

st.set_page_config(page_title="Head to Head", page_icon="⚔️", layout="wide")
st.title("⚔️ Team Head-to-Head Comparison")

teams = load_teams()

col1, col2 = st.columns(2)

with col1:
    team1_name = st.selectbox(
        "Select Team 1",
        teams["TEAM_NAME"].tolist(),
        index=0,
    )

with col2:
    team2_options = [t for t in teams["TEAM_NAME"].tolist() if t != team1_name]
    team2_name = st.selectbox(
        "Select Team 2",
        team2_options,
        index=min(4, len(team2_options) - 1),
    )

team1 = teams[teams["TEAM_NAME"] == team1_name].iloc[0]
team2 = teams[teams["TEAM_NAME"] == team2_name].iloc[0]

st.markdown("---")

# Radar Chart
categories = [
    "FIFA Ranking\n(inverted)",
    "Qualifier\nGoals",
    "Clean\nSheets",
    "Squad Value\n($M)",
    "Top Scorer\nGoals",
]

max_ranking = teams["FIFA_RANKING"].max()
max_goals = teams["QUALIFIER_GOALS"].max()
max_cs = teams["QUALIFIER_CLEAN_SHEETS"].max()
max_value = teams["SQUAD_VALUE_M"].max()
max_scorer = teams["TOP_SCORER_GOALS"].max()


def normalize(val, max_val):
    return (val / max_val) * 100 if max_val > 0 else 0


team1_values = [
    normalize(max_ranking - team1["FIFA_RANKING"] + 1, max_ranking),
    normalize(team1["QUALIFIER_GOALS"], max_goals),
    normalize(team1["QUALIFIER_CLEAN_SHEETS"], max_cs),
    normalize(team1["SQUAD_VALUE_M"], max_value),
    normalize(team1["TOP_SCORER_GOALS"], max_scorer),
]

team2_values = [
    normalize(max_ranking - team2["FIFA_RANKING"] + 1, max_ranking),
    normalize(team2["QUALIFIER_GOALS"], max_goals),
    normalize(team2["QUALIFIER_CLEAN_SHEETS"], max_cs),
    normalize(team2["SQUAD_VALUE_M"], max_value),
    normalize(team2["TOP_SCORER_GOALS"], max_scorer),
]

fig = go.Figure()

fig.add_trace(
    go.Scatterpolar(
        r=team1_values + [team1_values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name=f"{team1['FLAG_EMOJI']} {team1_name}",
        line_color="#29B5E8",
        fillcolor="rgba(41, 181, 232, 0.3)",
    )
)

fig.add_trace(
    go.Scatterpolar(
        r=team2_values + [team2_values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name=f"{team2['FLAG_EMOJI']} {team2_name}",
        line_color="#FFD700",
        fillcolor="rgba(255, 215, 0, 0.3)",
    )
)

fig.update_layout(
    polar=dict(
        bgcolor="#1A1F2B",
        radialaxis=dict(visible=True, range=[0, 100], showticklabels=False),
        angularaxis=dict(color="#FAFAFA"),
    ),
    showlegend=True,
    legend=dict(font=dict(size=14, color="#FAFAFA")),
    paper_bgcolor="#0E1117",
    font=dict(color="#FAFAFA"),
    height=500,
    margin=dict(t=30, b=30),
)

st.plotly_chart(fig, use_container_width=True)

# Side-by-side comparison cards
st.markdown("---")
st.subheader("📋 Team Details")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"### {team1['FLAG_EMOJI']} {team1_name}")
    st.markdown(f"**Group:** {team1['GROUP_LETTER']}")
    st.markdown(f"**FIFA Ranking:** #{team1['FIFA_RANKING']}")
    st.markdown(f"**Confederation:** {team1['CONFEDERATION']}")
    st.markdown(f"**Captain:** {team1['CAPTAIN']}")
    st.markdown(f"**Top Scorer:** {team1['TOP_SCORER']} ({team1['TOP_SCORER_GOALS']} goals)")
    st.markdown(f"**Squad Value:** ${team1['SQUAD_VALUE_M']:.0f}M")
    st.markdown(f"**Qualifier Goals:** {team1['QUALIFIER_GOALS']}")
    st.markdown(f"**Clean Sheets:** {team1['QUALIFIER_CLEAN_SHEETS']}")

with col2:
    st.markdown(f"### {team2['FLAG_EMOJI']} {team2_name}")
    st.markdown(f"**Group:** {team2['GROUP_LETTER']}")
    st.markdown(f"**FIFA Ranking:** #{team2['FIFA_RANKING']}")
    st.markdown(f"**Confederation:** {team2['CONFEDERATION']}")
    st.markdown(f"**Captain:** {team2['CAPTAIN']}")
    st.markdown(f"**Top Scorer:** {team2['TOP_SCORER']} ({team2['TOP_SCORER_GOALS']} goals)")
    st.markdown(f"**Squad Value:** ${team2['SQUAD_VALUE_M']:.0f}M")
    st.markdown(f"**Qualifier Goals:** {team2['QUALIFIER_GOALS']}")
    st.markdown(f"**Clean Sheets:** {team2['QUALIFIER_CLEAN_SHEETS']}")
