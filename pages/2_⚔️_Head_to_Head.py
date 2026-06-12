import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.data_loader import load_teams
from utils.football_api import get_all_results
from utils.banner import render_tournament_banner
from utils.footer import render_footer

render_tournament_banner()
st.markdown('<h2 style="text-align:center; margin:0.3rem 0;">⚔️ Team Head-to-Head Comparison</h2>', unsafe_allow_html=True)

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


def _render_team_card(team, team_name):
    """Render a styled stat card for a team."""
    badge = (
        f'<span style="display:inline-block; background:rgba(255,215,0,0.2); color:#FFD700; '
        f'border-radius:12px; padding:0.2rem 0.8rem; font-size:0.8rem; font-weight:700; '
        f'border:1px solid rgba(255,215,0,0.3);">Group {team["GROUP_LETTER"]}</span>'
    )
    row_style = 'display:flex; justify-content:space-between; padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.07);'
    label_style = 'font-size:0.85rem; color:#e0e0e0; font-weight:600;'
    value_style = 'font-size:0.9rem; font-weight:700; color:#ffffff;'
    gold_value = 'font-size:0.9rem; font-weight:700; color:#FFD700;'

    stats_html = ""
    stats = [
        ("FIFA Ranking", f'#{team["FIFA_RANKING"]}', True),
        ("Confederation", team["CONFEDERATION"], False),
        ("Captain", team["CAPTAIN"], False),
        ("Top Scorer", f'{team["TOP_SCORER"]} ({team["TOP_SCORER_GOALS"]})', False),
        ("Squad Value", f'${team["SQUAD_VALUE_M"]:.0f}M', True),
        ("Qualifier Goals", str(team["QUALIFIER_GOALS"]), False),
        ("Clean Sheets", str(team["QUALIFIER_CLEAN_SHEETS"]), False),
    ]
    for label, value, highlight in stats:
        vs = gold_value if highlight else value_style
        stats_html += (
            f'<div style="{row_style}">'
            f'<span style="{label_style}">{label}</span>'
            f'<span style="{vs}">{value}</span>'
            f'</div>'
        )

    st.markdown(
        f'<div style="background:rgba(17,86,117,0.3); border-radius:16px; padding:1.2rem 1.5rem; '
        f'border:1px solid rgba(41,181,232,0.2); height:100%;">'
        f'<h3 style="text-align:center; margin:0 0 0.5rem 0; font-size:1.3rem;">'
        f'{team["FLAG_EMOJI"]} {team_name}</h3>'
        f'<div style="text-align:center; margin-bottom:0.8rem;">{badge}</div>'
        f'{stats_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


col1, col2 = st.columns(2)

with col1:
    _render_team_card(team1, team1_name)

with col2:
    _render_team_card(team2, team2_name)

# 2026 World Cup match results
_results = get_all_results()

# Always show the results section
st.markdown("---")
st.markdown('<h3 style="text-align:center; color:rgb(17,86,117); margin-bottom:0.8rem;">⚽ 2026 World Cup Results</h3>', unsafe_allow_html=True)

# Direct encounter between the two teams
h2h_matches = [
    r for r in _results
    if (r["team_1_name"] == team1_name and r["team_2_name"] == team2_name)
    or (r["team_1_name"] == team2_name and r["team_2_name"] == team1_name)
]

if h2h_matches:
    for m in h2h_matches:
        st.markdown(
            f'<div style="background:rgba(17,86,117,0.3); border-radius:14px; padding:1rem 2rem; margin:0.5rem 0; border:1px solid rgba(41,181,232,0.2);">'
            f'<div style="display:flex; justify-content:center; align-items:center; gap:1rem;">'
            f'<img src="{m["team_1_logo"]}" style="height:2rem;">'
            f'<span style="font-size:1.1rem; font-weight:700; color:#fff;">{m["team_1_name"]}</span>'
            f'<span style="font-size:2rem; font-weight:900; color:#FFD700; margin:0 1rem;">{m["team_1_score"]} – {m["team_2_score"]}</span>'
            f'<img src="{m["team_2_logo"]}" style="height:2rem;">'
            f'<span style="font-size:1.1rem; font-weight:700; color:#fff;">{m["team_2_name"]}</span>'
            f'</div>'
            f'<p style="text-align:center; font-size:0.8rem; color:#e0e0e0; margin:0.4rem 0 0 0;">{m["date"]} | {m["venue"]}, {m["city"]}</p>'
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


def _render_result_card(m):
    return (
        f'<div style="background:rgba(17,86,117,0.3); border-radius:14px; padding:1rem 1.5rem; margin:0.3rem 0; border:1px solid rgba(41,181,232,0.2); min-height:100px; display:flex; flex-direction:column; justify-content:center;">'
        f'<div style="display:flex; justify-content:center; align-items:center; gap:0.5rem;">'
        f'<img src="{m["team_1_logo"]}" style="height:1.2rem;">'
        f'<span style="font-size:0.85rem; font-weight:600; color:#fff;">{m["team_1_name"]}</span>'
        f'<span style="font-size:1.1rem; font-weight:900; color:#FFD700; margin:0 0.3rem;">{m["team_1_score"]} – {m["team_2_score"]}</span>'
        f'<img src="{m["team_2_logo"]}" style="height:1.2rem;">'
        f'<span style="font-size:0.85rem; font-weight:600; color:#fff;">{m["team_2_name"]}</span>'
        f'</div>'
        f'<p style="text-align:center; font-size:0.7rem; color:#b0bec5; margin:0.2rem 0 0 0;">{m["date"]}</p>'
        f'</div>'
    )


def _render_no_match_card(team, team_name):
    return (
        f'<div style="background:rgba(17,86,117,0.3); border-radius:14px; padding:1rem 1.5rem; margin:0.3rem 0; border:1px solid rgba(41,181,232,0.2); min-height:100px; display:flex; flex-direction:column; justify-content:center; align-items:center;">'
        f'<p style="font-size:1rem; font-weight:700; color:#fff; margin:0 0 0.3rem 0;">{team["FLAG_EMOJI"]} {team_name}</p>'
        f'<p style="font-size:0.85rem; color:#b0bec5; margin:0;">No matches played yet.</p>'
        f'</div>'
    )


if team1_results or team2_results:
    col_r1, col_r2 = st.columns(2)

    with col_r1:
        if team1_results:
            for m in team1_results:
                st.markdown(_render_result_card(m), unsafe_allow_html=True)
        else:
            st.markdown(_render_no_match_card(team1, team1_name), unsafe_allow_html=True)

    with col_r2:
        if team2_results:
            for m in team2_results:
                st.markdown(_render_result_card(m), unsafe_allow_html=True)
        else:
            st.markdown(_render_no_match_card(team2, team2_name), unsafe_allow_html=True)
elif not h2h_matches:
    # Neither team has played at all — show both "no matches" cards
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown(_render_no_match_card(team1, team1_name), unsafe_allow_html=True)
    with col_r2:
        st.markdown(_render_no_match_card(team2, team2_name), unsafe_allow_html=True)

render_footer()
