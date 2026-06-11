import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.data_loader import load_teams, load_matches

st.set_page_config(page_title="Group Simulator", page_icon="📊", layout="wide")
st.title("📊 Group Stage Simulator")
st.caption("Set match scores and see which teams advance from each group!")

teams = load_teams()
matches = load_matches()

groups = sorted(teams["GROUP_LETTER"].unique())
selected_group = st.selectbox("Select Group", groups, format_func=lambda g: f"Group {g}")

group_teams = teams[teams["GROUP_LETTER"] == selected_group].reset_index(drop=True)
group_matches = matches[matches["STAGE"] == f"Group {selected_group}"].reset_index(drop=True)

st.markdown("---")
st.subheader(f"⚽ Group {selected_group} Matches")

scores = {}
for idx, match in group_matches.iterrows():
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
    with col1:
        st.markdown(f"**{match['TEAM_1_FLAG']} {match['TEAM_1_NAME']}**")
    with col2:
        s1 = st.number_input(
            "Goals",
            min_value=0,
            max_value=10,
            value=0,
            key=f"m{match['MATCH_ID']}_t1",
            label_visibility="collapsed",
        )
    with col3:
        st.markdown("<p style='text-align:center; font-size:1.2rem; padding-top:5px;'>vs</p>", unsafe_allow_html=True)
    with col4:
        s2 = st.number_input(
            "Goals",
            min_value=0,
            max_value=10,
            value=0,
            key=f"m{match['MATCH_ID']}_t2",
            label_visibility="collapsed",
        )
    with col5:
        st.markdown(f"**{match['TEAM_2_NAME']} {match['TEAM_2_FLAG']}**")

    scores[match["MATCH_ID"]] = (match["TEAM_1_ID"], s1, match["TEAM_2_ID"], s2)

# Calculate standings
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

for match_id, (t1_id, s1, t2_id, s2) in scores.items():
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

display_df = standings_df[["Flag", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]]

def highlight_rows(row):
    if row.name <= 2:
        return ["background-color: rgba(0, 200, 83, 0.2)"] * len(row)
    elif row.name == 3:
        return ["background-color: rgba(255, 215, 0, 0.15)"] * len(row)
    else:
        return ["background-color: rgba(255, 75, 75, 0.15)"] * len(row)

styled = display_df.style.apply(highlight_rows, axis=1)
st.dataframe(styled, use_container_width=True, height=200)

st.markdown("""
**Legend:**  
🟢 Top 2 — Advance to Round of 32  
🟡 3rd Place — May advance as best 3rd-place team  
🔴 4th Place — Eliminated
""")
