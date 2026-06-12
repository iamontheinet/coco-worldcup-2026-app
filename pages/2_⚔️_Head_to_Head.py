import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.data_loader import load_teams
from utils.football_api import get_all_results
from utils.footer import render_footer

st.title("⚔️ Team Head-to-Head Comparison")

teams = load_teams()
team_options = sorted(teams["TEAM_NAME"].tolist())

# Read query params for deep linking
_qp = st.query_params


def _find_team_idx(name, options, fallback):
    """Find team index, handling mismatches between ESPN and Snowflake names."""
    if not name:
        return fallback
    if name in options:
        return options.index(name)
    # Known ESPN → Snowflake name mappings
    _name_map = {
        "Bosnia-Herzegovina": "Bosnia and Herzegovina",
        "South Korea": "Korea Republic",
        "Türkiye": "Turkey",
    }
    mapped = _name_map.get(name)
    if mapped and mapped in options:
        return options.index(mapped)
    # Fallback: match on first word
    first_word = name.split("-")[0].split(" ")[0].lower()
    for i, opt in enumerate(options):
        if opt.lower().startswith(first_word):
            return i
    return fallback


_idx_t1 = _find_team_idx(_qp.get("team1"), team_options, 0)
_idx_t2 = _find_team_idx(_qp.get("team2"), team_options, min(4, len(team_options) - 1))

col1, col2 = st.columns(2)

with col1:
    team1_name = st.selectbox(
        "Select Team 1",
        team_options,
        index=_idx_t1,
    )

with col2:
    team2_name = st.selectbox(
        "Select Team 2",
        team_options,
        index=_idx_t2,
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
        hovertemplate=f"{team1['FLAG_EMOJI']} {team1_name}<br>%{{theta}}: %{{r:.0f}}/100<extra></extra>",
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
        hovertemplate=f"{team2['FLAG_EMOJI']} {team2_name}<br>%{{theta}}: %{{r:.0f}}/100<extra></extra>",
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
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="#1A1F2B",
        font_size=14,
        font_color="#ffffff",
        font_family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
    ),
)
fig.update_traces(hoveron="points")

st.plotly_chart(fig, use_container_width=True)

# Side-by-side comparison cards
st.markdown("---")

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

# 2026 World Cup match results
_results = get_all_results()

# Check if either team has played
_any_team1 = any(r["team_1_name"] == team1_name or r["team_2_name"] == team1_name for r in _results)
_any_team2 = any(r["team_1_name"] == team2_name or r["team_2_name"] == team2_name for r in _results)

if _any_team1 or _any_team2:
    st.markdown("---")
    st.subheader("⚽ 2026 World Cup Results")

    # Direct encounter between the two teams
    h2h_matches = [
        r for r in _results
        if (r["team_1_name"] == team1_name and r["team_2_name"] == team2_name)
        or (r["team_1_name"] == team2_name and r["team_2_name"] == team1_name)
    ]

    if h2h_matches:
        st.markdown("#### Head-to-Head")
        for m in h2h_matches:
            st.markdown(
                f'<div style="text-align:center; padding:0.5rem 0;">'
                f'<img src="{m["team_1_logo"]}" style="height:1.4rem; vertical-align:middle; margin-right:0.3rem;">'
                f'<b>{m["team_1_name"]} {m["team_1_score"]} – {m["team_2_score"]} </b>'
                f'<img src="{m["team_2_logo"]}" style="height:1.4rem; vertical-align:middle; margin-right:0.3rem;">'
                f'<b>{m["team_2_name"]}</b>'
                f'<br><span style="font-size:0.85rem; color:#e0e0e0;">{m["date"]} | {m["venue"]}, {m["city"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Each team's OTHER results (exclude the direct h2h match already shown above)
    h2h_pairs = set()
    for m in h2h_matches:
        h2h_pairs.add((m["team_1_name"], m["team_2_name"]))
        h2h_pairs.add((m["team_2_name"], m["team_1_name"]))

    team1_results = [
        r for r in _results
        if (r["team_1_name"] == team1_name or r["team_2_name"] == team1_name)
        and (r["team_1_name"], r["team_2_name"]) not in h2h_pairs
    ]
    team2_results = [
        r for r in _results
        if (r["team_1_name"] == team2_name or r["team_2_name"] == team2_name)
        and (r["team_1_name"], r["team_2_name"]) not in h2h_pairs
    ]

    if team1_results or team2_results:
        st.markdown("#### Other Matches")
        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.markdown(f"**{team1['FLAG_EMOJI']} {team1_name}:**")
            if team1_results:
                for m in team1_results:
                    st.markdown(f"- {m['team_1_name']} **{m['team_1_score']}–{m['team_2_score']}** {m['team_2_name']}")
            else:
                st.caption("No other matches played yet.")

        with col_r2:
            st.markdown(f"**{team2['FLAG_EMOJI']} {team2_name}:**")
            if team2_results:
                for m in team2_results:
                    st.markdown(f"- {m['team_1_name']} **{m['team_1_score']}–{m['team_2_score']}** {m['team_2_name']}")
            else:
                st.caption("No other matches played yet.")

render_footer()
