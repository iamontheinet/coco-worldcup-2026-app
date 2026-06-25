import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import pytz
from utils.data_loader import run_query

# Load team-to-group mapping for group labels
try:
    _teams_df = run_query("SELECT TEAM_NAME, GROUP_LETTER FROM TEAMS")
    _group_map = dict(zip(_teams_df["TEAM_NAME"], _teams_df["GROUP_LETTER"]))
except Exception:
    _group_map = {}


def _get_group(match):
    """Resolve group name from team names."""
    g = _group_map.get(match.get("team_1_name"))
    if not g:
        g = _group_map.get(match.get("team_2_name"))
    return f"Group {g}" if g else ""


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
            # Build HTML for all live matches
            matches_html = ""
            for i, match in enumerate(live_matches):
                if match["status"] == "HALFTIME":
                    badge = '<span style="background:#FFD700; color:#000; padding:0.1rem 0.5rem; border-radius:4px; font-size:0.7rem; font-weight:700;">HALF TIME</span>'
                else:
                    badge = '<span style="background:#e53935; color:#fff; padding:0.1rem 0.5rem; border-radius:4px; font-size:0.7rem; font-weight:700; animation:pulse 1.5s infinite;">● LIVE</span>'

                _display_clock = match.get("display_clock", "")
                _period = match.get("period", 1)
                if match["status"] == "HALFTIME":
                    _clock_str = "HT"
                elif _display_clock:
                    _half_label = "1st Half" if _period == 1 else "2nd Half"
                    _clock_str = f'{_display_clock} • {_half_label}'
                else:
                    _clock_str = ""

                _info_parts = []
                _group = _get_group(match)
                if _group:
                    _info_parts.append(_group)
                if match.get("venue"):
                    _v = match["venue"]
                    if match.get("city"):
                        _v += f', {match["city"]}'
                    _info_parts.append(_v)
                _info_line = " | ".join(_info_parts)

                _divider = '<hr style="border:none; border-top:1px solid rgba(41,181,232,0.2); margin:0.4rem 0;">' if i > 0 else ''
                matches_html += (
                    f'{_divider}'
                    f'<div style="text-align:center; margin:0.2rem 0;">{badge}</div>'
                    f'<div style="display:flex; justify-content:center; align-items:center; gap:0.6rem; margin-bottom:0.1rem;">'
                    f'<img src="{match["team_1_logo"]}" style="height:1.1rem;">'
                    f'<span style="font-size:0.85rem; font-weight:600; color:#fff;">{match["team_1_name"]}</span>'
                    f'<span style="font-size:1.3rem; font-weight:900; color:#FFD700; margin:0 0.2rem; font-variant-numeric:tabular-nums;">{match["team_1_score"]} – {match["team_2_score"]}</span>'
                    f'<img src="{match["team_2_logo"]}" style="height:1.1rem;">'
                    f'<span style="font-size:0.85rem; font-weight:600; color:#fff;">{match["team_2_name"]}</span>'
                    f'</div>'
                    f'<p style="text-align:center; font-size:0.7rem; font-weight:700; color:#FFD700; margin:0;">{_clock_str}</p>'
                )

            st.markdown(
                f'<style>@keyframes pulse {{ 0%{{opacity:1}} 50%{{opacity:0.5}} 100%{{opacity:1}} }}</style>'
                f'<div style="background:linear-gradient(180deg, rgba(17,86,117,0.4) 0%, rgba(41,181,232,0) 100%); border-radius:14px; padding:0.8rem 1.5rem; margin:0.2rem 0;">'
                f'{header}{matches_html}</div>',
                unsafe_allow_html=True,
            )
        else:
            upcoming = get_upcoming_matches()
            if upcoming:
                # Group matches at the same kickoff time
                _first_time = upcoming[0].get("utc_iso", "")
                _next_matches = [m for m in upcoming if m.get("utc_iso") == _first_time] if _first_time else [upcoming[0]]

                nxt_time = None
                if _first_time:
                    try:
                        nxt_time = datetime.fromisoformat(_first_time).astimezone(et)
                    except Exception:
                        nxt_time = None

                target_iso = ""
                if nxt_time:
                    target_iso = nxt_time.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

                _label = "Next Matches" if len(_next_matches) > 1 else "Next Match"

                # Build match rows
                _match_rows = ""
                for i, nxt in enumerate(_next_matches):
                    _info_parts = []
                    group_name = _get_group(nxt)
                    if group_name:
                        _info_parts.append(group_name)
                    if nxt.get("venue"):
                        _v = nxt["venue"]
                        if nxt.get("city"):
                            _v += f', {nxt["city"]}'
                        _info_parts.append(_v)
                    _info_line = " | ".join(_info_parts)
                    _divider = '<hr style="border:none; border-top:1px solid rgba(41,181,232,0.15); margin:0.3rem 0;">' if i > 0 else ''
                    _match_rows += (
                        f'{_divider}'
                        f'<div style="display:flex; justify-content:center; align-items:center; gap:0.6rem; margin-bottom:0.1rem;">'
                        f'<img src="{nxt["team_1_logo"]}" style="height:1.1rem;">'
                        f'<span style="font-size:0.85rem; font-weight:600; color:#fff;">{nxt["team_1_name"]}</span>'
                        f'<span style="font-size:0.8rem; color:#e0e0e0;">vs</span>'
                        f'<img src="{nxt["team_2_logo"]}" style="height:1.1rem;">'
                        f'<span style="font-size:0.85rem; font-weight:600; color:#fff;">{nxt["team_2_name"]}</span>'
                        f'</div>'
                        f'<p style="text-align:center; font-size:0.6rem; color:#e0e0e0; margin:0;">{_info_line}</p>'
                    )

                _time_display = _next_matches[0].get("time_et", "")
                _date_display = _next_matches[0].get("date", "")

                components.html(
                    f'''<div style="background:linear-gradient(180deg, rgba(17,86,117,0.4) 0%, rgba(41,181,232,0) 100%); border-radius:14px; padding:0.8rem 1.5rem; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
                    {header}
                    <p style="text-align:center; font-size:0.65rem; color:#e0e0e0; text-transform:uppercase; letter-spacing:1px; margin:0 0 0.1rem 0;">{_label}</p>
                    <div style="text-align:center; margin-bottom:0.3rem;">
                    <span id="bcd" style="font-size:1.4rem; font-weight:900; color:#FFD700; font-variant-numeric:tabular-nums;">--:--:--</span>
                    </div>
                    <p style="text-align:center; font-size:0.65rem; color:#e0e0e0; margin:0 0 0.3rem 0;">{_date_display} at {_time_display}</p>
                    {_match_rows}
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
                    height=min(160 + (len(_next_matches) - 1) * 50, 260),
                )
            else:
                st.markdown(
                    f'<div style="background:linear-gradient(180deg, rgba(17,86,117,0.4) 0%, rgba(41,181,232,0) 100%); border-radius:14px; padding:0.8rem 1.5rem; margin:0.2rem 0;">'
                    f'{header}</div>',
                    unsafe_allow_html=True,
                )

    _banner_fragment()
    st.markdown("---")
