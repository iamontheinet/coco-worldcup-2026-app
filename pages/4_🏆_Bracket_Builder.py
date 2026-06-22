import streamlit as st
import streamlit.components.v1 as components
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.data_loader import load_teams
from utils.football_api import get_all_results, get_live_matches
from utils.banner import render_tournament_banner
from utils.bracket_html import generate_interactive_bracket
from utils.footer import render_footer
from utils.analytics import log_page_view

log_page_view("Bracket Builder")

render_tournament_banner()
st.markdown('<h2 style="text-align:center; margin:0.3rem 0;">🏆 Knockout Bracket Builder</h2>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; font-size:0.75rem; color:#ffffff; margin-top:-0.3rem; text-transform:uppercase; letter-spacing:2px;">Click a team to advance them. Gold = your pick. <span style="background:rgba(0,200,83,0.15); border:1px solid #00c853; border-radius:4px; padding:0 4px; color:#0d3d52; font-weight:900;">✓</span> = Qualified for R32. ✔ = ESPN result (locked).</p>', unsafe_allow_html=True)

teams = load_teams()
team_list = sorted(teams["TEAM_NAME"].tolist())
team_flags = dict(zip(teams["TEAM_NAME"], teams["FLAG_EMOJI"]))

# --- Group seeding logic (same as before) ---
groups = sorted(teams["GROUP_LETTER"].unique())
group_winners = []
group_runners = []
group_thirds = []

_results = get_all_results()
_live = get_live_matches()
# Combine finished + live matches so standings reflect in-progress scores
_all_match_data = _results + _live
_team_group = dict(zip(teams["TEAM_NAME"], teams["GROUP_LETTER"]))


def _get_group_standings(group_letter):
    g_teams = teams[teams["GROUP_LETTER"] == group_letter]
    team_names = set(g_teams["TEAM_NAME"].tolist())
    group_results = [
        r for r in _all_match_data
        if r["team_1_name"] in team_names and r["team_2_name"] in team_names
    ]
    if not group_results:
        return None, False
    points = {t: 0 for t in team_names}
    gd = {t: 0 for t in team_names}
    gf = {t: 0 for t in team_names}
    for r in group_results:
        t1, t2 = r["team_1_name"], r["team_2_name"]
        s1, s2 = r["team_1_score"], r["team_2_score"]
        gf[t1] = gf.get(t1, 0) + s1
        gf[t2] = gf.get(t2, 0) + s2
        gd[t1] = gd.get(t1, 0) + (s1 - s2)
        gd[t2] = gd.get(t2, 0) + (s2 - s1)
        if s1 > s2:
            points[t1] += 3
        elif s2 > s1:
            points[t2] += 3
        else:
            points[t1] += 1
            points[t2] += 1
    sorted_teams = sorted(
        team_names,
        key=lambda t: (points[t], gd[t], gf[t]),
        reverse=True,
    )
    # Group is complete when all 6 matches are played (4 teams, each plays 3)
    is_complete = len(group_results) >= 6
    return sorted_teams, is_complete


# Track which teams are confirmed qualifiers
_confirmed_r32 = set()

# Also compute per-group points to identify clinched teams
_group_pts = {}  # {team: points}
_group_played = {}  # {team: games_played}
for g in groups:
    g_team_names = set(teams[teams["GROUP_LETTER"] == g]["TEAM_NAME"].tolist())
    g_results = [r for r in _all_match_data if r["team_1_name"] in g_team_names and r["team_2_name"] in g_team_names]
    for r in g_results:
        t1, t2 = r["team_1_name"], r["team_2_name"]
        _group_played[t1] = _group_played.get(t1, 0) + 1
        _group_played[t2] = _group_played.get(t2, 0) + 1
        s1, s2 = r["team_1_score"], r["team_2_score"]
        if s1 > s2:
            _group_pts[t1] = _group_pts.get(t1, 0) + 3
        elif s2 > s1:
            _group_pts[t2] = _group_pts.get(t2, 0) + 3
        else:
            _group_pts[t1] = _group_pts.get(t1, 0) + 1
            _group_pts[t2] = _group_pts.get(t2, 0) + 1

for g in groups:
    standings, complete = _get_group_standings(g)
    if standings and len(standings) >= 3:
        group_winners.append(standings[0])
        group_runners.append(standings[1])
        group_thirds.append(standings[2])
        if complete:
            _confirmed_r32.add(standings[0])
            _confirmed_r32.add(standings[1])
            _confirmed_r32.add(standings[2])
        else:
            # Teams with 6+ pts after 2 games have clinched top 3
            for t in standings[:3]:
                if _group_pts.get(t, 0) >= 6 and _group_played.get(t, 0) >= 2:
                    _confirmed_r32.add(t)
    elif standings and len(standings) >= 2:
        group_winners.append(standings[0])
        group_runners.append(standings[1])
        group_thirds.append(None)
    else:
        g_teams_df = teams[teams["GROUP_LETTER"] == g].sort_values("FIFA_RANKING")
        group_winners.append(g_teams_df.iloc[0]["TEAM_NAME"])
        group_runners.append(g_teams_df.iloc[1]["TEAM_NAME"])
        group_thirds.append(g_teams_df.iloc[2]["TEAM_NAME"] if len(g_teams_df) >= 3 else None)

_third_place_teams = [t for t in group_thirds if t]
_best_thirds = _third_place_teams[:8]

# Round of 32 matchups
r32_matchups = [
    (group_winners[0], group_runners[5]),
    (group_winners[1], group_runners[4]),
    (group_winners[2], group_runners[3]),
    (group_winners[3], group_runners[2]),
    (group_winners[4], group_runners[1]),
    (group_winners[5], group_runners[0]),
    (group_winners[6], group_runners[11]),
    (group_winners[7], group_runners[10]),
    (group_winners[8], group_runners[9]),
    (group_winners[9], group_runners[8]),
    (group_winners[10], group_runners[7]),
    (group_winners[11], group_runners[6]),
    (_best_thirds[0] if len(_best_thirds) > 0 else "TBD", _best_thirds[7] if len(_best_thirds) > 7 else "TBD"),
    (_best_thirds[1] if len(_best_thirds) > 1 else "TBD", _best_thirds[6] if len(_best_thirds) > 6 else "TBD"),
    (_best_thirds[2] if len(_best_thirds) > 2 else "TBD", _best_thirds[5] if len(_best_thirds) > 5 else "TBD"),
    (_best_thirds[3] if len(_best_thirds) > 3 else "TBD", _best_thirds[4] if len(_best_thirds) > 4 else "TBD"),
]

# --- Build locked results from ESPN ---
locked_winners = {}
for r in _results:
    t1, t2 = r["team_1_name"], r["team_2_name"]
    # Use ESPN's winner flag (handles penalties/extra time correctly)
    winner = r.get("winner")
    if not winner:
        # Fallback: determine from score for regular-time wins
        s1, s2 = r["team_1_score"], r["team_2_score"]
        if s1 > s2:
            winner = t1
        elif s2 > s1:
            winner = t2
    if winner:
        locked_winners[(t1, t2)] = winner
        locked_winners[(t2, t1)] = winner

# --- Decode picks from query params ---
def decode_picks(encoded: str) -> list:
    """Decode bracket state from query param string."""
    if not encoded:
        return [None] * 31
    parts = encoded.split(",")
    picks = []
    for p in parts:
        if p == "_" or p == "":
            picks.append(None)
        else:
            try:
                idx = int(p)
                if 0 <= idx < len(team_list):
                    picks.append(team_list[idx])
                else:
                    picks.append(None)
            except ValueError:
                picks.append(p if p in team_list else None)
    while len(picks) < 31:
        picks.append(None)
    return picks[:31]


# Read current state from query params
_bracket_param = st.query_params.get("b", "")
current_picks = decode_picks(_bracket_param)

# --- Render interactive bracket ---
bracket_html = generate_interactive_bracket(
    r32_matchups=r32_matchups,
    locked_winners=locked_winners,
    current_picks=current_picks,
    team_flags=team_flags,
    team_list=team_list,
    confirmed_teams=_confirmed_r32,
)

components.html(bracket_html, height=1190, scrolling=True)

# --- Champion display ---
champion = current_picks[30] if len(current_picks) > 30 else None
if champion:
    st.markdown(
        f'<div style="text-align:center; padding:1.5rem; margin-top:1rem; '
        f'background:linear-gradient(135deg, #115675 0%, #0d3d52 100%); '
        f'border-radius:14px; border:2px solid #FFD700; box-shadow:0 0 20px rgba(255,215,0,0.2);">'
        f'<p style="font-size:3rem; margin:0;">{team_flags.get(champion, "🏆")}</p>'
        f'<p style="font-size:1.5rem; font-weight:800; color:#FFD700; margin:0.5rem 0 0 0;">🏆 {champion} 🏆</p>'
        f'<p style="font-size:0.9rem; color:#ffffff; margin:0.3rem 0 0 0;">Your predicted 2026 FIFA World Cup Champion</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

# --- Reset ---
st.markdown("---")
col_reset = st.columns([1, 2, 1])
with col_reset[1]:
    if st.button("🔄 Reset all bracket picks", type="secondary", use_container_width=True):
        # Write explicit empty state to URL — the JS will read this as all-null
        st.query_params["b"] = ""
        # Force full page navigation to clear any stale iframe state
        st.switch_page("pages/4_🏆_Bracket_Builder.py")

render_footer()
