import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.data_loader import load_teams, load_matches
from utils.football_api import get_all_results, get_live_matches
from utils.banner import render_tournament_banner
from utils.footer import render_footer

render_tournament_banner()
st.markdown('<h2 style="text-align:center; margin:0.3rem 0;">📊 Group Stage Simulator</h2>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; font-size:0.75rem; color:#ffffff; margin-top:-0.3rem; text-transform:uppercase; letter-spacing:2px;">Set match scores and see which teams advance from each group.</p>', unsafe_allow_html=True)

teams = load_teams()
matches = load_matches()

if "sim_version" not in st.session_state:
    st.session_state.sim_version = 0
_sv = st.session_state.sim_version

groups = sorted(teams["GROUP_LETTER"].unique())
selected_group = st.selectbox("Select Group", groups, format_func=lambda g: f"Group {g}")

group_teams = teams[teams["GROUP_LETTER"] == selected_group].reset_index(drop=True)
_group_team_names = set(group_teams["TEAM_NAME"].tolist())
group_matches = matches[
    (matches["TEAM_1_NAME"].isin(_group_team_names)) & (matches["TEAM_2_NAME"].isin(_group_team_names))
].reset_index(drop=True)

st.markdown("---")
st.subheader(f"⚽ Group {selected_group} Matches")

_results = get_all_results()
_live = get_live_matches()
# Include live matches in results lookup so standings reflect in-progress scores
_all_match_data = _results + _live
_results_lookup = {}
for r in _all_match_data:
    _results_lookup[(r["team_1_name"], r["team_2_name"])] = (r["team_1_score"], r["team_2_score"])
    _results_lookup[(r["team_2_name"], r["team_1_name"])] = (r["team_2_score"], r["team_1_score"])

# Build lookup for live match teams to show different indicator
_live_pairs = set()
for r in _live:
    _live_pairs.add((r["team_1_name"], r["team_2_name"]))
    _live_pairs.add((r["team_2_name"], r["team_1_name"]))

scores = {}
for idx, match in group_matches.iterrows():
    actual = _results_lookup.get((match["TEAM_1_NAME"], match["TEAM_2_NAME"]))
    is_played = actual is not None
    is_live = (match["TEAM_1_NAME"], match["TEAM_2_NAME"]) in _live_pairs

    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
    with col1:
        st.markdown(f'<p style="text-align:right; font-weight:700; margin:0; padding-top:5px;">{match["TEAM_1_FLAG"]} {match["TEAM_1_NAME"]}</p>', unsafe_allow_html=True)
    with col2:
        s1 = st.number_input(
            "Goals",
            min_value=0,
            max_value=10,
            value=actual[0] if is_played else 0,
            key=f"v{_sv}_m{match['MATCH_ID']}_t1",
            label_visibility="collapsed",
            disabled=is_played,
        )
    with col3:
        if is_live:
            label = "🔴"
        elif is_played:
            label = "✅"
        else:
            label = "vs"
        st.markdown(f'<p style="text-align:center; font-size:1.2rem; padding-top:5px;">{label}</p>', unsafe_allow_html=True)
    with col4:
        s2 = st.number_input(
            "Goals",
            min_value=0,
            max_value=10,
            value=actual[1] if is_played else 0,
            key=f"v{_sv}_m{match['MATCH_ID']}_t2",
            label_visibility="collapsed",
            disabled=is_played,
        )
    with col5:
        st.markdown(f'<p style="text-align:left; font-weight:700; margin:0; padding-top:5px;">{match["TEAM_2_FLAG"]} {match["TEAM_2_NAME"]}</p>', unsafe_allow_html=True)

    scores[match["MATCH_ID"]] = (match["TEAM_1_ID"], s1, match["TEAM_2_ID"], s2, is_played)

st.markdown("---")
st.subheader(f"📋 Group {selected_group} Standings")

standings = {}
for _, t in group_teams.iterrows():
    standings[t["TEAM_ID"]] = {
        "team": t["TEAM_NAME"],
        "flag": t["FLAG_EMOJI"],
        "played": 0,
        "won": 0,
        "drawn": 0,
        "lost": 0,
        "gf": 0,
        "ga": 0,
        "gd": 0,
        "points": 0,
    }

for match_id, (t1_id, s1, t2_id, s2, played) in scores.items():
    if not played and s1 == 0 and s2 == 0:
        continue
    standings[t1_id]["played"] += 1
    standings[t2_id]["played"] += 1
    standings[t1_id]["gf"] += s1
    standings[t1_id]["ga"] += s2
    standings[t2_id]["gf"] += s2
    standings[t2_id]["ga"] += s1
    standings[t1_id]["gd"] = standings[t1_id]["gf"] - standings[t1_id]["ga"]
    standings[t2_id]["gd"] = standings[t2_id]["gf"] - standings[t2_id]["ga"]

    if s1 > s2:
        standings[t1_id]["won"] += 1
        standings[t1_id]["points"] += 3
        standings[t2_id]["lost"] += 1
    elif s2 > s1:
        standings[t2_id]["won"] += 1
        standings[t2_id]["points"] += 3
        standings[t1_id]["lost"] += 1
    else:
        standings[t1_id]["drawn"] += 1
        standings[t2_id]["drawn"] += 1
        standings[t1_id]["points"] += 1
        standings[t2_id]["points"] += 1

standings_df = pd.DataFrame(standings.values())
standings_df = standings_df.sort_values(
    by=["points", "gd", "gf"], ascending=[False, False, False]
).reset_index(drop=True)

standings_df.index += 1
standings_df.columns = ["Team", "Flag", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]

# Determine if group is complete (all 6 matches played)
_played_count = sum(1 for _, (_, _, _, _, played) in scores.items() if played)
_group_complete = _played_count >= 6

# Add status column for completed groups
if _group_complete:
    _status = []
    for pos in standings_df.index:
        if pos <= 2:
            _status.append("✅ Qualified")
        elif pos == 3:
            _status.append("⏳ 3rd Place")
        else:
            _status.append("❌ Eliminated")
    standings_df["Status"] = _status

display_df = standings_df[["Flag", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"] + (["Status"] if _group_complete else [])]

def highlight_rows(row):
    if row.name <= 2:
        return ["background-color: rgba(0, 200, 83, 0.2)"] * len(row)
    elif row.name == 3:
        return ["background-color: rgba(255, 215, 0, 0.15)"] * len(row)
    else:
        return ["background-color: rgba(255, 75, 75, 0.15)"] * len(row)

styled = display_df.style.apply(highlight_rows, axis=1)
st.dataframe(styled, use_container_width=True, height=200)

st.markdown(
    '<p style="text-align:center; font-size:0.9rem; margin-top:0.5rem;">'
    '🟢 Top 2 — Advance to Round of 32 &nbsp;&nbsp;|&nbsp;&nbsp; '
    '🟡 3rd Place — May advance as best 3rd-place &nbsp;&nbsp;|&nbsp;&nbsp; '
    '🔴 4th Place — Eliminated</p>',
    unsafe_allow_html=True,
)

if st.button("🔄 Reset predictions"):
    st.session_state.sim_version += 1
    st.rerun()

render_footer()
