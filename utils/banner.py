import streamlit as st
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh


def render_tournament_banner():
    """Compact tournament header with FIFA title and live/next match for sub-pages."""
    st_autorefresh(interval=60000, key="banner_refresh")

    et = pytz.timezone("US/Eastern")
    now = datetime.now(et)

    from utils.football_api import get_live_matches, get_upcoming_matches

    header = '<p style="text-align:center; margin:0 0 0.1rem 0; font-size:1.4rem; font-weight:800;">⚽ FIFA World Cup 2026</p>'

    # --- Build match HTML ---
    match_html = ""
    live_matches = get_live_matches()
    if live_matches:
        match = live_matches[0]
        if match["status"] == "HALFTIME":
            badge = '<span style="background:#FFD700; color:#000; padding:0.1rem 0.5rem; border-radius:4px; font-size:0.7rem; font-weight:700;">HALF TIME</span>'
        else:
            badge = '<span style="background:#e53935; color:#fff; padding:0.1rem 0.5rem; border-radius:4px; font-size:0.7rem; font-weight:700; animation:pulse 1.5s infinite;">● LIVE</span>'

        match_html = (
            f'<div style="text-align:center; margin:0.2rem 0;">{badge}</div>'
            f'<div style="display:flex; justify-content:center; align-items:center; gap:0.8rem; margin-bottom:0.2rem;">'
            f'<img src="{match["team_1_logo"]}" style="height:1.3rem;">'
            f'<span style="font-size:0.95rem; font-weight:600; color:#fff;">{match["team_1_name"]}</span>'
            f'<span style="font-size:0.85rem; color:#e0e0e0;">vs</span>'
            f'<img src="{match["team_2_logo"]}" style="height:1.3rem;">'
            f'<span style="font-size:0.95rem; font-weight:600; color:#fff;">{match["team_2_name"]}</span>'
            f'</div>'
            f'<div style="text-align:center;">'
            f'<span style="font-size:1.6rem; font-weight:900; color:#FFD700; font-variant-numeric:tabular-nums;">{match["team_1_score"]} – {match["team_2_score"]}</span>'
            f'</div>'
        )
    else:
        upcoming = get_upcoming_matches()
        if upcoming:
            nxt = upcoming[0]
            nxt_time = None
            if nxt.get("utc_iso"):
                try:
                    nxt_time = datetime.fromisoformat(nxt["utc_iso"]).astimezone(et)
                except Exception:
                    nxt_time = None

            if nxt_time and nxt_time > now:
                cd_secs = int((nxt_time - now).total_seconds())
                cd_h = cd_secs // 3600
                cd_m = (cd_secs % 3600) // 60
                time_label = f'{cd_h}h {cd_m:02d}m'
            else:
                time_label = nxt.get("time_et", "")

            info_parts = []
            if nxt.get("date"):
                info_parts.append(nxt["date"])
            if nxt.get("time_et"):
                info_parts.append(f'at {nxt["time_et"]}')
            if nxt.get("venue"):
                venue_str = nxt["venue"]
                if nxt.get("city"):
                    venue_str += f', {nxt["city"]}'
                info_parts.append(venue_str)
            info_line = " | ".join(info_parts)

            match_html = (
                f'<p style="text-align:center; font-size:0.7rem; color:#e0e0e0; text-transform:uppercase; letter-spacing:1px; margin:0 0 0.2rem 0;">Next Match</p>'
                f'<div style="display:flex; justify-content:center; align-items:center; gap:0.8rem; margin-bottom:0.2rem;">'
                f'<img src="{nxt["team_1_logo"]}" style="height:1.3rem;">'
                f'<span style="font-size:0.95rem; font-weight:600; color:#fff;">{nxt["team_1_name"]}</span>'
                f'<span style="font-size:0.85rem; color:#e0e0e0;">vs</span>'
                f'<img src="{nxt["team_2_logo"]}" style="height:1.3rem;">'
                f'<span style="font-size:0.95rem; font-weight:600; color:#fff;">{nxt["team_2_name"]}</span>'
                f'</div>'
                f'<div style="text-align:center;">'
                f'<span style="font-size:1.6rem; font-weight:900; color:#FFD700; font-variant-numeric:tabular-nums;">{time_label}</span>'
                f'</div>'
                f'<p style="text-align:center; font-size:0.75rem; color:#e0e0e0; margin:0.2rem 0 0 0;">{info_line}</p>'
            )

    # --- Render with gradient band (Option B) ---
    st.markdown(
        f'<div style="background:linear-gradient(180deg, rgba(17,86,117,0.4) 0%, rgba(41,181,232,0) 100%); border-radius:14px; padding:0.8rem 1.5rem; margin:0.2rem 0;">'
        f'{header}{match_html}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
