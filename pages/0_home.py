import streamlit as st
import sys, os
from datetime import datetime
import pytz
from pytz import timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.snowflake_conn import run_query
from utils.football_api import get_live_matches, get_todays_matches, get_upcoming_matches, get_all_results
from utils.footer import render_footer

st.markdown('<h1 style="text-align:center; margin-top:0.5rem; margin-bottom:0; font-size:clamp(1.5rem, 5vw, 2.5rem);">⚽ FIFA World Cup 2026</h1>', unsafe_allow_html=True)

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


@st.fragment(run_every=10)
def _live_section():
    """Auto-refreshing section: stats pills + live match or countdown."""
    _et = timezone("US/Eastern")
    _now = datetime.now(_et)

    _wc_end = _et.localize(datetime(2026, 7, 19, 23, 59, 59))

    _remaining_seconds = max(0, int((_wc_end - _now).total_seconds()))
    _days_left = _remaining_seconds // 86400
    _all_results = get_all_results()
    _matches_played = len(_all_results)
    _games_remaining = 104 - _matches_played

    # Tournament stats — metric pills (hidden on mobile via CSS)
    _pill = 'display:inline-block; background:rgba(17,86,117,0.4); border-radius:20px; padding:0.4rem 1.2rem; margin:0.2rem 0.3rem; width:180px; text-align:center; white-space:nowrap;'
    _pill_val = 'font-size:1.4rem; font-weight:900; color:#FFD700;'
    _pill_lbl = 'font-size:0.75rem; color:#e0e0e0; text-transform:uppercase; letter-spacing:1px;'
    st.markdown(
        f'<style>@media(max-width:768px){{.desktop-pills{{display:none!important}}}}</style>'
        f'<div class="desktop-pills" style="text-align:center; margin:0.5rem 0;">'
        f'<p style="font-size:1.2rem; color:#FFD700; font-weight:800; margin:0 0 0.5rem 0; letter-spacing:1px;">11 June – 19 July 2026</p>'
        f'<span style="{_pill}"><span style="{_pill_val}">{_days_left}</span> <span style="{_pill_lbl}">days left</span></span>'
        f'<span style="{_pill}"><span style="{_pill_val}">{_games_remaining}</span> <span style="{_pill_lbl}">games left</span></span>'
        f'<span style="{_pill}"><span style="{_pill_val}">48</span> <span style="{_pill_lbl}">teams</span></span>'
        f'<span style="{_pill}"><span style="{_pill_val}">16</span> <span style="{_pill_lbl}">venues</span></span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Live match display (via ESPN API — real-time)
    live_matches = get_live_matches()

    # Persist last known live match to avoid flicker on API gaps
    if live_matches:
        st.session_state["_last_live"] = live_matches[0]
    elif st.session_state.get("_last_live"):
        # Check if match actually finished
        _finished = {(r["team_1_name"], r["team_2_name"]) for r in get_all_results()}
        _cached = st.session_state["_last_live"]
        if (_cached["team_1_name"], _cached["team_2_name"]) in _finished or \
           (_cached["team_2_name"], _cached["team_1_name"]) in _finished:
            del st.session_state["_last_live"]
        else:
            live_matches = [st.session_state["_last_live"]]

    if live_matches:
        match = live_matches[0]

        if match["status"] == "HALFTIME":
            badge_html = '<span style="background:#FFD700; color:#000; padding:4px 16px; border-radius:16px; font-size:1rem; font-weight:700;">HALF TIME</span>'
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

        # Use components.html for JS match clock
        _clock_secs = match.get("clock_seconds", 0)
        _period = match.get("period", 1)
        _is_halftime = match["status"] == "HALFTIME"

        import streamlit.components.v1 as components
        components.html(
            f'''<style>
            @keyframes pulse {{ 0%{{opacity:1}} 50%{{opacity:0.5}} 100%{{opacity:1}} }}
            .live-badge {{ display:inline-block; background:#FF4B4B; color:white; padding:4px 16px; border-radius:16px; font-size:1rem; font-weight:700; animation:pulse 1.5s infinite; letter-spacing:1px; }}
            .live-card .desktop-layout {{ display:flex; }}
            .live-card .mobile-layout {{ display:none; }}
            @media(max-width:768px){{
                .live-card{{padding:1rem!important}}
                .live-card .desktop-layout {{ display:none; }}
                .live-card .mobile-layout {{ display:block; }}
            }}
            </style>
            <div class="live-card" style="background:rgba(17,86,117,0.3); border-radius:20px; padding:2rem 3rem; margin:0; border:1px solid rgba(41,181,232,0.3); font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
            <div style="text-align:center; margin-bottom:0.8rem;">{badge_html}</div>
            <!-- Desktop: 3-column spread -->
            <div class="desktop-layout" style="justify-content:space-between; align-items:center;">
            <div style="text-align:center; flex:1;">
            <img src="{match["team_1_logo"]}" style="height:3rem; margin-bottom:0.5rem;"><br>
            <span style="font-size:1.3rem; font-weight:700; color:#ffffff;">{match["team_1_name"]}</span></div>
            <div style="text-align:center; flex:1;">
            <p class="score" style="font-size:4rem; font-weight:900; color:#ffffff; margin:0; line-height:1;">{match["team_1_score"]} – {match["team_2_score"]}</p>
            <p id="match-clock" style="font-size:1.1rem; font-weight:700; color:#FFD700; margin:0.3rem 0 0 0; font-variant-numeric:tabular-nums;"></p>
            <p style="font-size:0.85rem; color:#e0e0e0; margin:0.3rem 0 0 0;">{" &nbsp;|&nbsp; ".join(info_parts)}</p></div>
            <div style="text-align:center; flex:1;">
            <img src="{match["team_2_logo"]}" style="height:3rem; margin-bottom:0.5rem;"><br>
            <span style="font-size:1.3rem; font-weight:700; color:#ffffff;">{match["team_2_name"]}</span></div>
            </div>
            <!-- Mobile: stacked compact -->
            <div class="mobile-layout" style="text-align:center;">
            <div style="display:flex; justify-content:center; align-items:center; gap:0.5rem; margin-bottom:0.3rem;">
            <img src="{match["team_1_logo"]}" style="height:1.8rem;">
            <span style="font-size:0.95rem; font-weight:700; color:#fff;">{match["team_1_name"]}</span>
            <span style="font-size:2.2rem; font-weight:900; color:#fff;">{match["team_1_score"]} – {match["team_2_score"]}</span>
            <img src="{match["team_2_logo"]}" style="height:1.8rem;">
            <span style="font-size:0.95rem; font-weight:700; color:#fff;">{match["team_2_name"]}</span>
            </div>
            <p id="match-clock-m" style="font-size:1rem; font-weight:700; color:#FFD700; margin:0; font-variant-numeric:tabular-nums;"></p>
            <p style="font-size:0.7rem; color:#e0e0e0; margin:0.2rem 0 0 0;">{" &nbsp;|&nbsp; ".join(info_parts)}</p>
            </div>
            </div>
            <script>
            (function(){{
                var clockSecs={_clock_secs};
                var period={_period};
                var halftime={'true' if _is_halftime else 'false'};
                var els=[document.getElementById("match-clock"),document.getElementById("match-clock-m")];
                var halfLabel=period===1?"1st Half":"2nd Half";
                function fmt(){{
                    if(halftime){{ els.forEach(function(e){{if(e)e.textContent="HT";}}); return; }}
                    var mins=Math.floor(clockSecs/60);
                    var txt;
                    if(period===1 && mins>=45){{
                        txt="45+"+(mins-45)+"' \u2022 "+halfLabel;
                    }} else if(period===2 && mins>=90){{
                        txt="90+"+(mins-90)+"' \u2022 "+halfLabel;
                    }} else {{
                        txt=mins+"' \u2022 "+halfLabel;
                    }}
                    els.forEach(function(e){{if(e)e.textContent=txt;}});
                }}
                fmt();
                if(!halftime){{
                    setInterval(function(){{
                        clockSecs++;
                        fmt();
                    }}, 1000);
                }}
            }})();
            </script>''',
            height=220,
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
                    _next_match_time = datetime.fromisoformat(next_match["utc_iso"]).astimezone(_et)
                except Exception:
                    _next_match_time = None

            st.markdown("---")
            st.markdown('<h3 style="text-align:center;">Next Match</h3>', unsafe_allow_html=True)

            # Countdown — client-side JS ticker for smooth seconds
            _target_iso = ""
            _countdown_active = False
            if _next_match_time:
                _target_iso = _next_match_time.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                _countdown_active = _next_match_time > _now

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

            if _countdown_active:
                # Stadium Card with JS countdown via components.html
                import streamlit.components.v1 as components
                components.html(
                    f'''<style>
                    .cd-card .desktop-layout {{ display:flex; }}
                    .cd-card .mobile-layout {{ display:none; }}
                    @media(max-width:768px){{
                        .cd-card{{padding:1rem!important}}
                        .cd-card .desktop-layout {{ display:none; }}
                        .cd-card .mobile-layout {{ display:block; }}
                    }}
                    </style>
                    <div class="cd-card" style="background:rgba(17,86,117,0.3); border-radius:20px; padding:2rem 3rem; margin:0; border:1px solid rgba(41,181,232,0.3); font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
                    <!-- Desktop: 3-column spread -->
                    <div class="desktop-layout" style="justify-content:space-between; align-items:center;">
                    <div style="text-align:center; flex:1;">
                    <img src="{next_match["team_1_logo"]}" style="height:3rem; margin-bottom:0.5rem;"><br>
                    <span style="font-size:1.3rem; font-weight:700; color:#ffffff;">{next_match["team_1_name"]}</span></div>
                    <div style="text-align:center; flex:1;">
                    <p id="cd" style="font-size:3.5rem; font-weight:900; color:#FFD700; margin:0; line-height:1; font-variant-numeric:tabular-nums;">--:--:--</p>
                    <p style="font-size:0.85rem; color:#e0e0e0; margin:0.3rem 0 0 0;">{_info_line}</p></div>
                    <div style="text-align:center; flex:1;">
                    <img src="{next_match["team_2_logo"]}" style="height:3rem; margin-bottom:0.5rem;"><br>
                    <span style="font-size:1.3rem; font-weight:700; color:#ffffff;">{next_match["team_2_name"]}</span></div>
                    </div>
                    <!-- Mobile: stacked compact -->
                    <div class="mobile-layout" style="text-align:center;">
                    <div style="display:flex; justify-content:center; align-items:center; gap:0.5rem; margin-bottom:0.4rem;">
                    <img src="{next_match["team_1_logo"]}" style="height:1.8rem;">
                    <span style="font-size:0.95rem; font-weight:700; color:#fff;">{next_match["team_1_name"]}</span>
                    <span style="font-size:0.8rem; color:#e0e0e0;">vs</span>
                    <img src="{next_match["team_2_logo"]}" style="height:1.8rem;">
                    <span style="font-size:0.95rem; font-weight:700; color:#fff;">{next_match["team_2_name"]}</span>
                    </div>
                    <p id="cd-m" style="font-size:2.2rem; font-weight:900; color:#FFD700; margin:0; line-height:1.2; font-variant-numeric:tabular-nums;">--:--:--</p>
                    <p style="font-size:0.7rem; color:#e0e0e0; margin:0.2rem 0 0 0;">{_info_line}</p>
                    </div>
                    </div>
                    <script>
                    (function(){{
                        var target=new Date("{_target_iso}").getTime();
                        var els=[document.getElementById("cd"),document.getElementById("cd-m")];
                        function tick(){{
                            var diff=Math.max(0,Math.floor((target-Date.now())/1000));
                            var d=Math.floor(diff/86400),h=Math.floor((diff%86400)/3600),m=Math.floor((diff%3600)/60),s=diff%60;
                            var t=d>0?d+"d "+String(h).padStart(2,"0")+":"+String(m).padStart(2,"0")+":"+String(s).padStart(2,"0"):String(h).padStart(2,"0")+":"+String(m).padStart(2,"0")+":"+String(s).padStart(2,"0");
                            els.forEach(function(e){{if(e)e.textContent=t;}});
                        }}
                        tick();setInterval(tick,1000);
                    }})();
                    </script>''',
                    height=180,
                )
            else:
                # Match time has passed but ESPN hasn't reported it as live yet
                st.markdown(
                    f'<div style="background:rgba(17,86,117,0.3); border-radius:20px; padding:2rem 3rem; margin:0.5rem 0; border:1px solid rgba(41,181,232,0.3);">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                    f'<div style="text-align:center; flex:1;">'
                    f'<img src="{next_match["team_1_logo"]}" style="height:3rem; margin-bottom:0.5rem;"><br>'
                    f'<span style="font-size:1.3rem; font-weight:700; color:#ffffff;">{next_match["team_1_name"]}</span></div>'
                    f'<div style="text-align:center; flex:1;">'
                    f'<p style="font-size:2rem; font-weight:900; color:#FFD700; margin:0; line-height:1;">⚽ KICKOFF</p>'
                    f'<p style="font-size:0.85rem; color:#e0e0e0; margin:0.3rem 0 0 0;">{_info_line}</p></div>'
                    f'<div style="text-align:center; flex:1;">'
                    f'<img src="{next_match["team_2_logo"]}" style="height:3rem; margin-bottom:0.5rem;"><br>'
                    f'<span style="font-size:1.3rem; font-weight:700; color:#ffffff;">{next_match["team_2_name"]}</span></div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )


# Render the auto-refreshing fragment
_live_section()

# --- Static content below (only reruns on full page load) ---

# Full schedule expander
_upcoming_static = get_upcoming_matches()
if _upcoming_static and len(_upcoming_static) > 1:
    _schedule = [m for m in _upcoming_static[1:] if "Winner" not in m["team_1_name"] and "Winner" not in m["team_2_name"]]
    if _schedule:
        with st.expander("📅 Full Upcoming Schedule"):
            import streamlit.components.v1 as components
            rows_html = ""
            for m in _schedule:
                g = _get_group(m) or ""
                date_str = m.get("date", "")
                time_str = m.get("time_et", "").replace(" ET", "")
                if time_str:
                    date_str += f" {time_str}"
                rows_html += (
                    f'<div class="match-row">'
                    f'<div class="row-left">'
                    f'<img src="{m.get("team_1_logo", "")}" class="flag">'
                    f'<span class="team">{m["team_1_name"]}</span>'
                    f'</div>'
                    f'<div class="row-center">'
                    f'<span class="vs">vs</span>'
                    f'</div>'
                    f'<div class="row-right">'
                    f'<span class="team">{m["team_2_name"]}</span>'
                    f'<img src="{m.get("team_2_logo", "")}" class="flag">'
                    f'</div>'
                    f'<div class="row-meta">{date_str}<span class="group-tag">{g}</span></div>'
                    f'</div>'
                )
            components.html(
                f'''<style>
                * {{ margin:0; padding:0; box-sizing:border-box; }}
                body {{ background:transparent; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
                .match-row {{
                    display:grid;
                    grid-template-columns:1fr auto 1fr;
                    grid-template-rows:auto auto;
                    align-items:center;
                    padding:0.5rem 0.8rem;
                    border-bottom:1px solid rgba(255,255,255,0.06);
                }}
                .match-row:hover {{ background:rgba(41,181,232,0.08); }}
                .row-left {{ display:flex; align-items:center; gap:0.4rem; }}
                .row-center {{ text-align:center; padding:0 0.6rem; }}
                .row-right {{ display:flex; align-items:center; gap:0.4rem; justify-content:flex-end; }}
                .row-meta {{ grid-column:1/-1; text-align:center; font-size:0.7rem; color:#999; margin-top:0.15rem; }}
                .flag {{ width:1.2rem; height:1.2rem; object-fit:contain; }}
                .team {{ font-size:0.82rem; font-weight:600; color:#e0e0e0; }}
                .vs {{ font-size:0.7rem; color:#888; }}
                .group-tag {{ margin-left:0.5rem; background:rgba(41,181,232,0.15); color:#29b5e8; padding:1px 6px; border-radius:8px; font-size:0.65rem; }}
                @media(max-width:768px){{
                    .team {{ font-size:0.75rem; }}
                    .flag {{ width:1rem; height:1rem; }}
                    .match-row {{ padding:0.4rem 0.5rem; }}
                }}
                </style>
                {rows_html}''',
                height=min(len(_schedule) * 52 + 10, 450),
                scrolling=True,
            )

st.markdown("---")

# Past Matches section
all_todays = get_todays_matches()
finished_matches = [m for m in all_todays if m["status"] == "FINISHED"]
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
