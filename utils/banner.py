import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import pytz


def render_tournament_banner():
    """Compact tournament header with FIFA title and live/next match for sub-pages."""

    @st.fragment(run_every=60)
    def _banner_fragment():
        et = pytz.timezone("US/Eastern")
        now = datetime.now(et)

        from utils.football_api import get_live_matches, get_upcoming_matches

        header = '<p style="text-align:center; margin:0 0 0.1rem 0; font-size:1.4rem; font-weight:800;">⚽ FIFA World Cup 2026</p>'

        # --- Build match HTML ---
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

            st.markdown(
                f'<div style="background:linear-gradient(180deg, rgba(17,86,117,0.4) 0%, rgba(41,181,232,0) 100%); border-radius:14px; padding:0.8rem 1.5rem; margin:0.2rem 0;">'
                f'{header}{match_html}</div>',
                unsafe_allow_html=True,
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

                target_iso = ""
                if nxt_time:
                    target_iso = nxt_time.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

                # Line 1: date + time
                _info_line1 = nxt.get("date", "")
                if nxt.get("time_et"):
                    _info_line1 += f' at {nxt["time_et"]}'
                # Line 2: group + venue
                _info_line2_parts = []
                if nxt.get("group"):
                    _info_line2_parts.append(nxt["group"])
                if nxt.get("venue"):
                    venue_str = nxt["venue"]
                    if nxt.get("city"):
                        venue_str += f', {nxt["city"]}'
                    _info_line2_parts.append(venue_str)
                _info_line2 = " | ".join(_info_line2_parts)

                # Banner with JS countdown ticker
                components.html(
                    f'''<div style="background:linear-gradient(180deg, rgba(17,86,117,0.4) 0%, rgba(41,181,232,0) 100%); border-radius:14px; padding:0.8rem 1.5rem; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
                    {header}
                    <p style="text-align:center; font-size:0.7rem; color:#e0e0e0; text-transform:uppercase; letter-spacing:1px; margin:0 0 0.2rem 0;">Next Match</p>
                    <div style="display:flex; justify-content:center; align-items:center; gap:0.8rem; margin-bottom:0.2rem;">
                    <img src="{nxt["team_1_logo"]}" style="height:1.3rem;">
                    <span style="font-size:0.95rem; font-weight:600; color:#fff;">{nxt["team_1_name"]}</span>
                    <span style="font-size:0.85rem; color:#e0e0e0;">vs</span>
                    <img src="{nxt["team_2_logo"]}" style="height:1.3rem;">
                    <span style="font-size:0.95rem; font-weight:600; color:#fff;">{nxt["team_2_name"]}</span>
                    </div>
                    <div style="text-align:center;">
                    <span id="bcd" style="font-size:1.6rem; font-weight:900; color:#FFD700; font-variant-numeric:tabular-nums;">--:--:--</span>
                    </div>
                    <p style="text-align:center; font-size:0.75rem; color:#e0e0e0; margin:0.2rem 0 0 0;">{_info_line1}</p>
                    <p style="text-align:center; font-size:0.75rem; color:#e0e0e0; margin:0.1rem 0 0 0;">{_info_line2}</p>
                    </div>
                    <script>
                    (function(){{
                        var target=new Date("{target_iso}").getTime();
                        var el=document.getElementById("bcd");
                        function tick(){{
                            var diff=Math.max(0,Math.floor((target-Date.now())/1000));
                            var h=Math.floor(diff/3600),m=Math.floor((diff%3600)/60),s=diff%60;
                            var t=String(h).padStart(2,"0")+":"+String(m).padStart(2,"0")+":"+String(s).padStart(2,"0");
                            if(el)el.textContent=t;
                        }}
                        tick();setInterval(tick,1000);
                    }})();
                    </script>''',
                    height=160,
                )
            else:
                st.markdown(
                    f'<div style="background:linear-gradient(180deg, rgba(17,86,117,0.4) 0%, rgba(41,181,232,0) 100%); border-radius:14px; padding:0.8rem 1.5rem; margin:0.2rem 0;">'
                    f'{header}</div>',
                    unsafe_allow_html=True,
                )

    _banner_fragment()
    st.markdown("---")
