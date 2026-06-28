import streamlit as st
import streamlit.components.v1 as components
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.data_loader import load_teams
from utils.football_api import get_all_results
from utils.banner import render_tournament_banner
from utils.bracket_html import generate_interactive_bracket
from utils.bracket_seeding import get_r32_seedings
from utils.footer import render_footer
from utils.analytics import log_page_view

log_page_view("Bracket Builder")

render_tournament_banner()
st.markdown('<h2 style="text-align:center; margin:0.3rem 0;">🏆 Knockout Bracket Builder</h2>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; font-size:0.75rem; color:#ffffff; margin-top:-0.3rem; text-transform:uppercase; letter-spacing:2px;">Click a team to advance them. Gold = your pick. <span style="background:rgba(0,200,83,0.15); border:1px solid #00c853; border-radius:4px; padding:0 4px; color:#0d3d52; font-weight:900;">✓</span> = Qualified for R32. ✔ = ESPN result (locked).</p>', unsafe_allow_html=True)

# --- Use shared seeding logic ---
_seedings = get_r32_seedings()
teams = load_teams()
team_list = _seedings["team_list"]
team_flags = _seedings["team_flags"]
r32_matchups = _seedings["r32_matchups"]
# Pad to 16 matchups (bracket requires exactly 16 R32 slots)
while len(r32_matchups) < 16:
    r32_matchups.append(("TBD", "TBD"))
_confirmed_r32 = _seedings["confirmed_r32"]

# --- Build locked results from ESPN ---
_results = get_all_results()
locked_winners = {}
for r in _results:
    t1, t2 = r["team_1_name"], r["team_2_name"]
    winner = r.get("winner")
    if not winner:
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
