import streamlit as st
import streamlit.components.v1 as components
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.football_api import get_all_results, get_knockout_matchups
from utils.bracket_seeding import get_r32_seedings
from utils.bracket_vertical import generate_vertical_bracket
from utils.banner import render_tournament_banner
from utils.footer import render_footer
from utils.analytics import log_page_view

log_page_view("Bracket Builder")

render_tournament_banner()
st.markdown('<h2 style="text-align:center; margin:0.3rem 0;">🏆 Knockout Bracket</h2>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; font-size:0.75rem; color:#e0e0e0; margin-top:-0.3rem; text-transform:uppercase; letter-spacing:2px;">Full knockout bracket · AI predictions on upcoming matches</p>', unsafe_allow_html=True)

# --- Build bracket ---
_seedings = get_r32_seedings()
_r32 = _seedings["r32_matchups"]
while len(_r32) < 16:
    _r32.append(("TBD", "TBD"))
_ko_data = get_knockout_matchups()
_all_results = get_all_results()

# Predictions
try:
    from utils.predictions import get_predictions
    _unplayed = []
    for _round in [_ko_data["qf"], _ko_data["sf"], _ko_data["final"], _ko_data["3rd_place"]]:
        _unplayed.extend(_round)
    _predictions = get_predictions(len(_all_results), tuple(_unplayed))
except Exception:
    _predictions = {}

_vb_html = generate_vertical_bracket(
    r32_matchups=_r32,
    results=_all_results,
    team_flags=_seedings["team_flags"],
    confirmed_teams=_seedings["confirmed_r32"],
    r16_matchups=_ko_data["r16"],
    qf_matchups=_ko_data["qf"],
    sf_matchups=_ko_data["sf"],
    final_matchups=_ko_data["final"],
    third_place_matchups=_ko_data["3rd_place"],
    match_dates=_ko_data.get("dates", {}),
    predictions=_predictions,
    show_all_rounds=True,
)

components.html(_vb_html, height=1200, scrolling=True)

render_footer()
