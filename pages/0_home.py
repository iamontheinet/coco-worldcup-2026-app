import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.snowflake_conn import run_query
from utils.football_api import get_live_matches, get_todays_matches
from utils.footer import render_footer

st_autorefresh(interval=1000, key="auto_refresh")

st.markdown('<h1 style="text-align:center;">⚽ FIFA World Cup 2026</h1>', unsafe_allow_html=True)
st.markdown(
    '<p style="text-align:center; font-size:1.3rem; color:#ffffff; margin-top:-10px; letter-spacing:1px;">11 June – 19 July 2026</p>',
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

# Live countdown — Days remaining & Matches played
from datetime import datetime
from pytz import timezone

_et = timezone("US/Eastern")
_wc_end = _et.localize(datetime(2026, 7, 19, 23, 59, 59))
_now = datetime.now(_et)

_remaining_seconds = max(0, int((_wc_end - _now).total_seconds()))
_days_left = _remaining_seconds // 86400
_hours_left = (_remaining_seconds % 86400) // 3600
_mins_left = (_remaining_seconds % 3600) // 60
_secs_left = _remaining_seconds % 60

_matches_played = len(finished_matches)

col_left, col_right = st.columns(2)

with col_left:
    st.markdown(
        f'<p style="font-size:3.5rem; font-weight:800; text-align:center; color:#115675; margin:0; line-height:1.1;">{_days_left}</p>'
        f'<p style="font-size:1rem; text-align:center; color:#e0e0e0; margin:0;">Days Remaining</p>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Hours", _hours_left)
    with c2:
        st.metric("Mins", _mins_left)
    with c3:
        st.metric("Secs", _secs_left)

with col_right:
    st.markdown(
        f'<p style="font-size:3.5rem; font-weight:800; text-align:center; color:#115675; margin:0; line-height:1.1;">{_matches_played} / 104</p>'
        f'<p style="font-size:1rem; text-align:center; color:#e0e0e0; margin:0;">Matches Played</p>',
        unsafe_allow_html=True,
    )
    c4, c5, c6 = st.columns(3)
    with c4:
        st.metric("Teams", "48")
    with c5:
        st.metric("Venues", "16")
    with c6:
        st.metric("Host Cities", "3")

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

elif todays:
    active_matches = [m for m in todays if m["status"] not in ("FINISHED",)]
    finished_matches = [m for m in todays if m["status"] == "FINISHED"]

    if active_matches:
        st.markdown("---")
        st.markdown('<h3 style="text-align:center;">Upcoming Matches</h3>', unsafe_allow_html=True)
        for m in active_matches[:4]:
            is_live = m["status"] in ("IN_PLAY", "HALFTIME")

            if is_live:
                badge = '<span class="live-badge">● LIVE</span>'
                st.markdown(
                    f'<div style="text-align:center; margin-bottom:0.3rem;">{badge}</div>',
                    unsafe_allow_html=True,
                )

            score_display = f"{m['team_1_score']} – {m['team_2_score']}" if is_live else "vs"

            col_a, col_b, col_c = st.columns([3, 2, 3])
            with col_a:
                st.markdown(
                    f'<p style="font-size:1.8rem; font-weight:700; text-align:right; color:#FAFAFA; margin:0; white-space:nowrap;">'
                    f'<img src="{m["team_1_logo"]}" style="height:1.6rem; vertical-align:middle; margin-right:0.3rem;">'
                    f'{m["team_1_name"]}</p>',
                    unsafe_allow_html=True,
                )
            with col_b:
                st.markdown(
                    f'<p style="font-size:2.5rem; font-weight:800; text-align:center; color:#FAFAFA; margin:0; line-height:1;">{score_display}</p>',
                    unsafe_allow_html=True,
                )
            with col_c:
                st.markdown(
                    f'<p style="font-size:1.8rem; font-weight:700; text-align:left; color:#FAFAFA; margin:0; white-space:nowrap;">'
                    f'<img src="{m["team_2_logo"]}" style="height:1.6rem; vertical-align:middle; margin-right:0.3rem;">'
                    f'{m["team_2_name"]}</p>',
                    unsafe_allow_html=True,
                )

            info_parts = []
            if m.get("date"):
                date_time = m["date"]
                if m.get("time_et"):
                    date_time += f' at {m["time_et"]}'
                info_parts.append(date_time)
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
                f'<p style="text-align:center; font-size:1rem; color:#ffffff; font-weight:700; margin-top:0.2rem;">{" &nbsp;|&nbsp; ".join(info_parts)}</p>',
                unsafe_allow_html=True,
            )
            st.markdown("")


else:
    try:
        upcoming_data = run_query("""
            SELECT m.MATCH_ID, m.MATCH_DATE, m.MATCH_TIME_ET, m.STAGE,
                   t1.TEAM_NAME as TEAM_1_NAME, t1.FLAG_EMOJI as TEAM_1_FLAG,
                   t2.TEAM_NAME as TEAM_2_NAME, t2.FLAG_EMOJI as TEAM_2_FLAG,
                   v.VENUE_NAME, v.CITY
            FROM MATCHES m
            JOIN TEAMS t1 ON m.TEAM_1_ID = t1.TEAM_ID
            JOIN TEAMS t2 ON m.TEAM_2_ID = t2.TEAM_ID
            JOIN VENUES v ON m.VENUE_ID = v.VENUE_ID
            WHERE m.MATCH_DATE >= CURRENT_DATE()
            ORDER BY m.MATCH_DATE, m.MATCH_TIME_ET
            LIMIT 3
        """)

        if not upcoming_data.empty:
            st.markdown("---")
            st.markdown(
                '<div style="text-align:center; margin-bottom:0.5rem;">'
                '<span style="display:inline-block; background:#115675; color:white; padding:4px 16px; '
                'border-radius:16px; font-size:1rem; font-weight:700; letter-spacing:1px;">UPCOMING</span></div>',
                unsafe_allow_html=True,
            )
            for _, row in upcoming_data.iterrows():
                match_date = row["MATCH_DATE"]
                if hasattr(match_date, "strftime"):
                    date_str = match_date.strftime("%b %d")
                else:
                    date_str = str(match_date)
                time_str = str(row["MATCH_TIME_ET"]) if row["MATCH_TIME_ET"] else "TBD"
                st.markdown(
                    f'<div style="text-align:center; padding:0.5rem 0;">'
                    f'<span style="font-size:1.4rem; font-weight:700; color:#FAFAFA;">'
                    f'{row["TEAM_1_FLAG"]} {row["TEAM_1_NAME"]} &nbsp;vs&nbsp; {row["TEAM_2_FLAG"]} {row["TEAM_2_NAME"]}</span><br>'
                    f'<span style="font-size:0.95rem; color:#ffffff; font-weight:600;">'
                    f'{date_str} &nbsp;|&nbsp; {time_str} ET &nbsp;|&nbsp; {row["STAGE"]} &nbsp;|&nbsp; '
                    f'{row["VENUE_NAME"]}, {row["CITY"]}</span></div>',
                    unsafe_allow_html=True,
                )
    except Exception:
        pass

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
