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

# Compact tournament stats (plain text)
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

    st.markdown("---")
    st.markdown(
        f'<div style="text-align:center; margin-bottom:0.5rem;">{badge_html}</div>',
        unsafe_allow_html=True,
    )

    col_a, col_b, col_c = st.columns([3, 2, 3])

    with col_a:
        st.markdown(
            f'<p style="font-size:2.2rem; font-weight:700; text-align:right; color:#FAFAFA; margin:0; white-space:nowrap;">'
            f'<img src="{match["team_1_logo"]}" style="height:2rem; vertical-align:middle; margin-right:0.4rem;">'
            f'{match["team_1_name"]}</p>',
            unsafe_allow_html=True,
        )

    with col_b:
        st.markdown(
            f'<p style="font-size:3.5rem; font-weight:800; text-align:center; color:#FAFAFA; margin:0; line-height:1;">{match["team_1_score"]} – {match["team_2_score"]}</p>',
            unsafe_allow_html=True,
        )

    with col_c:
        st.markdown(
            f'<p style="font-size:2.2rem; font-weight:700; text-align:left; color:#FAFAFA; margin:0; white-space:nowrap;">'
            f'<img src="{match["team_2_logo"]}" style="height:2rem; vertical-align:middle; margin-right:0.4rem;">'
            f'{match["team_2_name"]}</p>',
            unsafe_allow_html=True,
        )

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

    st.markdown(
        f'<p style="text-align:center; color:#ffffff; font-size:1.15rem; font-weight:600; margin-top:0.5rem;">{" &nbsp;|&nbsp; ".join(info_parts)}</p>',
        unsafe_allow_html=True,
    )

else:
    # --- NEXT MATCH COUNTDOWN ---
    _upcoming = get_upcoming_matches()
    if _upcoming:
        next_match = _upcoming[0]

        # Calculate countdown to next match
        _next_match_time = None
        if next_match.get("date") and next_match.get("time_et"):
            try:
                from datetime import datetime as dt
                date_str = next_match["date"]  # "Jun 12, 2026"
                time_str = next_match["time_et"].replace(" ET", "")  # "10:00 PM"
                _next_match_time = _et.localize(
                    dt.strptime(f"{date_str} {time_str}", "%b %d, %Y %I:%M %p")
                )
            except Exception:
                _next_match_time = None

        st.markdown("---")

        # Show teams
        st.markdown('<h3 style="text-align:center;">Next Match</h3>', unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns([3, 2, 3])
        with col_a:
            st.markdown(
                f'<p style="font-size:1.8rem; font-weight:700; text-align:right; color:#FAFAFA; margin:0; white-space:nowrap;">'
                f'<img src="{next_match["team_1_logo"]}" style="height:1.6rem; vertical-align:middle; margin-right:0.3rem;">'
                f'{next_match["team_1_name"]}</p>',
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown(
                '<p style="font-size:2.5rem; font-weight:800; text-align:center; color:#FAFAFA; margin:0; line-height:1;">vs</p>',
                unsafe_allow_html=True,
            )
        with col_c:
            st.markdown(
                f'<p style="font-size:1.8rem; font-weight:700; text-align:left; color:#FAFAFA; margin:0; white-space:nowrap;">'
                f'<img src="{next_match["team_2_logo"]}" style="height:1.6rem; vertical-align:middle; margin-right:0.3rem;">'
                f'{next_match["team_2_name"]}</p>',
                unsafe_allow_html=True,
            )

        # Match info
        info_parts = []
        if next_match.get("date"):
            date_time = next_match["date"]
            if next_match.get("time_et"):
                date_time += f' at {next_match["time_et"]}'
            info_parts.append(date_time)
        group_name = _get_group(next_match)
        if group_name:
            info_parts.append(group_name)
        if next_match.get("venue"):
            venue_str = next_match["venue"]
            if next_match.get("city"):
                venue_str += f', {next_match["city"]}'
            info_parts.append(venue_str)
        st.markdown(
            f'<p style="text-align:center; font-size:1.1rem; color:#FAFAFA; font-weight:700; margin-top:0.2rem;">{" &nbsp;|&nbsp; ".join(info_parts)}</p>',
            unsafe_allow_html=True,
        )

        # Head-to-head link
        st.markdown(
            f'<p style="text-align:center; margin-top:0.3rem;">'
            f'<a href="/Head_to_Head?team1={next_match["team_1_name"]}&team2={next_match["team_2_name"]}" '
            f'target="_self" style="color:#ffffff; font-size:0.95rem;">⚔️ Head-to-Head</a></p>',
            unsafe_allow_html=True,
        )

        # Countdown timer using metric cards
        if _next_match_time and _next_match_time > _now:
            _countdown_secs = int((_next_match_time - _now).total_seconds())
            _cd_days = _countdown_secs // 86400
            _cd_hours = (_countdown_secs % 86400) // 3600
            _cd_mins = (_countdown_secs % 3600) // 60
            _cd_secs = _countdown_secs % 60

            st.markdown("")
            if _cd_days > 0:
                d1, d2, d3, d4 = st.columns(4)
                with d1:
                    st.metric("Days", _cd_days)
                with d2:
                    st.metric("Hours", _cd_hours)
                with d3:
                    st.metric("Mins", _cd_mins)
                with d4:
                    st.metric("Secs", _cd_secs)
            else:
                d1, d2, d3 = st.columns(3)
                with d1:
                    st.metric("Hours", _cd_hours)
                with d2:
                    st.metric("Mins", _cd_mins)
                with d3:
                    st.metric("Secs", _cd_secs)

        # Show remaining schedule in expander as a table
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
