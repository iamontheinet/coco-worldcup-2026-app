import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.snowflake_conn import run_query
from utils.football_api import get_live_matches, get_todays_matches, get_upcoming_matches, get_all_results
from utils.footer import render_footer

st_autorefresh(interval=1000, key="auto_refresh")

st.markdown('<h1 style="text-align:center; margin-bottom:0;">⚽ FIFA World Cup 2026</h1>', unsafe_allow_html=True)
st.markdown(
    '<p style="text-align:center; font-size:1.3rem; color:#ffffff; margin-top:-10px; margin-bottom:0; letter-spacing:1px;">11 June – 19 July 2026</p>',
    unsafe_allow_html=True,
)

# Live match display (via ESPN API — real-time)
live_matches = get_live_matches()
all_todays = get_todays_matches()
finished_matches = [m for m in all_todays if m["status"] == "FINISHED"]
todays = [] if live_matches else all_todays

# Load team-to-group mapping from Snowflake
try:
    _teams_df = run_query("SELECT TEAM_NAME, GROUP_LETTER FROM TEAMS")
    _group_map = dict(zip(_teams_df["TEAM_NAME"], _teams_df["GROUP_LETTER"]))
except Exception:
    _group_map = {}


def _get_group(match):
    g = _group_map.get(match.get("team_1_name"))
    if not g:
        g = _group_map.get(match.get("team_2_name"))
    return f"Group {g}" if g else ""


from datetime import datetime
from pytz import timezone

_et = timezone("US/Eastern")
_wc_end = _et.localize(datetime(2026, 7, 19, 23, 59, 59))
_now = datetime.now(_et)

_remaining_seconds = max(0, int((_wc_end - _now).total_seconds()))
_days_left = _remaining_seconds // 86400
_all_results = get_all_results()
_matches_played = len(_all_results)

# Compact tournament stats
st.markdown(
    f'<p style="text-align:center; font-size:1.1rem; color:#ffffff; margin:0.5rem 0 0 0; font-weight:600;">'
    f'{_days_left} days left &nbsp;|&nbsp; {_matches_played}/104 matches played &nbsp;|&nbsp; 48 teams &nbsp;|&nbsp; 16 venues</p>',
    unsafe_allow_html=True,
)

# --- LIVE MATCH ---
if live_matches:
    match = live_matches[0]

    if match["status"] == "HALFTIME":
        badge_html = '<span class="live-badge" style="background:#FFD700;color:#000;">HALF TIME</span>'
    else:
        badge_html = '<span class="live-badge">● LIVE</span>'

    info_parts = []
    group_name = _get_group(match)
    if group_name:
        info_parts.append(group_name)
    else:
        info_parts.append(match["stage"])
    if match.get("venue"):
        venue_str = match["venue"]
        if match.get("city"):
            venue_str += f', {match["city"]}'
        info_parts.append(venue_str)

    st.markdown("---")
    st.markdown('<h3 style="text-align:center;">Current Match</h3>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:rgba(17,86,117,0.3); border-radius:20px; padding:2rem 3rem; margin:0.5rem 0; border:1px solid rgba(41,181,232,0.3);">'
        f'<div style="text-align:center; margin-bottom:0.8rem;">{badge_html}</div>'
        f'<div style="display:flex; justify-content:space-between; align-items:center;">'
        f'<div style="text-align:center; flex:1;">'
        f'<img src="{match["team_1_logo"]}" style="height:3rem; margin-bottom:0.5rem;"><br>'
        f'<span style="font-size:1.3rem; font-weight:700; color:#ffffff;">{match["team_1_name"]}</span></div>'
        f'<div style="text-align:center; flex:1;">'
        f'<p style="font-size:4rem; font-weight:900; color:#ffffff; margin:0; line-height:1;">{match["team_1_score"]} – {match["team_2_score"]}</p>'
        f'<p style="font-size:0.85rem; color:#e0e0e0; margin:0.3rem 0 0 0;">{" &nbsp;|&nbsp; ".join(info_parts)}</p></div>'
        f'<div style="text-align:center; flex:1;">'
        f'<img src="{match["team_2_logo"]}" style="height:3rem; margin-bottom:0.5rem;"><br>'
        f'<span style="font-size:1.3rem; font-weight:700; color:#ffffff;">{match["team_2_name"]}</span></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

else:
    # --- NEXT MATCH COUNTDOWN (Stadium Card) ---
    _upcoming = get_upcoming_matches()
    if _upcoming:
        next_match = _upcoming[0]

        # Parse match time from UTC ISO stored by ESPN API
        _next_match_time = None
        if next_match.get("utc_iso"):
            try:
                from datetime import datetime as dt
                _next_match_time = dt.fromisoformat(next_match["utc_iso"]).astimezone(_et)
            except Exception:
                _next_match_time = None

        st.markdown("---")
        st.markdown('<h3 style="text-align:center;">Next Match</h3>', unsafe_allow_html=True)

        # Countdown values
        _cd_days = _cd_hours = _cd_mins = _cd_secs = 0
        if _next_match_time and _next_match_time > _now:
            _countdown_secs = int((_next_match_time - _now).total_seconds())
            _cd_days = _countdown_secs // 86400
            _cd_hours = (_countdown_secs % 86400) // 3600
            _cd_mins = (_countdown_secs % 3600) // 60
            _cd_secs = _countdown_secs % 60

        _time_str = f'{_cd_days}d {_cd_hours:02d}:{_cd_mins:02d}:{_cd_secs:02d}' if _cd_days > 0 else f'{_cd_hours:02d}:{_cd_mins:02d}:{_cd_secs:02d}'

        # Match info line
        _info_line = next_match.get("date", "")
        if next_match.get("time_et"):
            _info_line += f' at {next_match["time_et"]}'
        group_name = _get_group(next_match)
        if group_name:
            _info_line += f' | {group_name}'
        if next_match.get("venue"):
            _info_line += f' | {next_match["venue"]}'
            if next_match.get("city"):
                _info_line += f', {next_match["city"]}'

        # Stadium Card
        st.markdown(
            f'<div style="background:rgba(17,86,117,0.3); border-radius:20px; padding:2rem 3rem; margin:0.5rem 0; border:1px solid rgba(41,181,232,0.3);">'
            f'<div style="display:flex; justify-content:space-between; align-items:center;">'
            f'<div style="text-align:center; flex:1;">'
            f'<img src="{next_match["team_1_logo"]}" style="height:3rem; margin-bottom:0.5rem;"><br>'
            f'<span style="font-size:1.3rem; font-weight:700; color:#ffffff;">{next_match["team_1_name"]}</span></div>'
            f'<div style="text-align:center; flex:1;">'
            f'<p style="font-size:3.5rem; font-weight:900; color:#FFD700; margin:0; line-height:1; font-variant-numeric:tabular-nums;">{_time_str}</p>'
            f'<p style="font-size:0.85rem; color:#e0e0e0; margin:0.3rem 0 0 0;">{_info_line}</p></div>'
            f'<div style="text-align:center; flex:1;">'
            f'<img src="{next_match["team_2_logo"]}" style="height:3rem; margin-bottom:0.5rem;"><br>'
            f'<span style="font-size:1.3rem; font-weight:700; color:#ffffff;">{next_match["team_2_name"]}</span></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        # Full schedule expander
        if len(_upcoming) > 1:
            st.markdown("")
            _schedule = [m for m in _upcoming[1:] if "Winner" not in m["team_1_name"] and "Winner" not in m["team_2_name"]]
            if _schedule:
                with st.expander("📅 Full Upcoming Schedule"):
                    import pandas as pd
                    schedule_data = []
                    for m in _schedule:
                        g = _get_group(m)
                        schedule_data.append({
                            "Date": m.get("date", ""),
                            "Time (ET)": m.get("time_et", "").replace(" ET", ""),
                            "Team A": m["team_1_name"],
                            "Team B": m["team_2_name"],
                            "Group": g,
                            "H2H": f"/Head_to_Head?team1={m['team_1_name']}&team2={m['team_2_name']}",
                        })
                    df = pd.DataFrame(schedule_data)
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        height=400,
                        column_config={
                            "H2H": st.column_config.LinkColumn("H2H", display_text="⚔️"),
                        },
                    )

st.markdown("---")

# Past Matches section
if finished_matches:
    st.markdown('<h3 style="text-align:center;">Past Matches</h3>', unsafe_allow_html=True)
    for m in finished_matches:
        info_parts = []
        if m.get("date"):
            info_parts.append(m["date"])
        group_name = _get_group(m)
        if group_name:
            info_parts.append(group_name)
        else:
            info_parts.append(m["stage"])
        if m.get("venue"):
            venue_str = m["venue"]
            if m.get("city"):
                venue_str += f', {m["city"]}'
            info_parts.append(venue_str)

        st.markdown(
            f'<div style="text-align:center; padding:0.6rem 0;">'
            f'<img src="{m["team_1_logo"]}" style="height:1.4rem; vertical-align:middle; margin-right:0.3rem;">'
            f'<span style="font-size:1.3rem; font-weight:700; color:#FAFAFA;">'
            f'{m["team_1_name"]} &nbsp;{m["team_1_score"]} – {m["team_2_score"]}&nbsp; </span>'
            f'<img src="{m["team_2_logo"]}" style="height:1.4rem; vertical-align:middle; margin-right:0.3rem;">'
            f'<span style="font-size:1.3rem; font-weight:700; color:#FAFAFA;">{m["team_2_name"]}</span>'
            f'<span style="font-size:0.9rem; color:#ffffff; margin-left:0.5rem; background:#115675; padding:2px 8px; border-radius:8px;">FT</span><br>'
            f'<span style="font-size:0.85rem; color:#e0e0e0;">{" &nbsp;|&nbsp; ".join(info_parts)}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown("---")

render_footer()
