import streamlit as st
import sys, os
from datetime import datetime
import pytz
from pytz import timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.snowflake_conn import run_query
from utils.football_api import get_live_matches, get_upcoming_matches, get_all_results
from utils.footer import render_footer
from utils.analytics import log_page_view

log_page_view("Home")

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


# Load R32 qualified teams for status indicators


def _render_live_match(match, _mi):
    """Render a single live match card with stats."""
    import streamlit.components.v1 as components

    if match["status"] == "HALFTIME":
        badge_html = '<span style="background:#FFD700; color:#000; padding:4px 16px; border-radius:16px; font-size:1rem; font-weight:700;">HALF TIME</span>'
    else:
        badge_html = '<span class="live-badge">● LIVE</span>'

    info_parts = []
    _stage = match.get("stage", "")
    if _stage == "Group Stage":
        group_name = _get_group(match)
        if group_name:
            info_parts.append(group_name)
    else:
        info_parts.append(_stage)
    if match.get("venue"):
        venue_str = match["venue"]
        if match.get("city"):
            venue_str += f', {match["city"]}'
        info_parts.append(venue_str)

    _period = match.get("period", 1)
    _is_halftime = match["status"] == "HALFTIME"
    _display_clock = match.get("display_clock", "")

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
        <div class="live-card" style="background:rgba(17,86,117,0.25); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px); border-radius:20px; padding:2rem 3rem; margin:0; border:1px solid rgba(41,181,232,0.25); font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
        <div style="text-align:center; margin-bottom:0.8rem;">{badge_html}</div>
        <!-- Desktop: 3-column spread -->
        <div class="desktop-layout" style="justify-content:space-between; align-items:center;">
        <div style="text-align:center; flex:1;">
        <img src="{match["team_1_logo"]}" style="height:3rem; margin-bottom:0.5rem;"><br>
        <span style="font-size:1.3rem; font-weight:700; color:#ffffff;">{match["team_1_name"]}</span><br>
        </div>
        <div style="text-align:center; flex:1;">
        <p class="score" style="font-size:4rem; font-weight:900; color:#ffffff; margin:0; line-height:1;">{match["team_1_score"]} – {match["team_2_score"]}</p>
        <p id="match-clock-{_mi}" style="font-size:1.1rem; font-weight:700; color:#FFD700; margin:0.3rem 0 0 0; font-variant-numeric:tabular-nums;"></p>
        <p style="font-size:0.85rem; color:#e0e0e0; margin:0.3rem 0 0 0;">{" &nbsp;|&nbsp; ".join(info_parts)}</p></div>
        <div style="text-align:center; flex:1;">
        <img src="{match["team_2_logo"]}" style="height:3rem; margin-bottom:0.5rem;"><br>
        <span style="font-size:1.3rem; font-weight:700; color:#ffffff;">{match["team_2_name"]}</span><br>
        </div>
        </div>
        <!-- Mobile: flag+name row, scores below -->
        <div class="mobile-layout" style="text-align:center;">
        <div style="display:flex; justify-content:center; align-items:center; gap:0.5rem; margin-bottom:0.4rem;">
        <img src="{match["team_1_logo"]}" style="height:1.8rem;">
        <span style="font-size:0.9rem; font-weight:700; color:#fff;">{match["team_1_name"]}</span>
        <span style="font-size:0.75rem; color:#e0e0e0;">vs</span>
        <img src="{match["team_2_logo"]}" style="height:1.8rem;">
        <span style="font-size:0.9rem; font-weight:700; color:#fff;">{match["team_2_name"]}</span>
        </div>
        <p style="font-size:2.5rem; font-weight:900; color:#fff; margin:0; line-height:1;">{match["team_1_score"]} – {match["team_2_score"]}</p>
        <p id="match-clock-m-{_mi}" style="font-size:1rem; font-weight:700; color:#FFD700; margin:0; font-variant-numeric:tabular-nums;"></p>
        <p style="font-size:0.7rem; color:#e0e0e0; margin:0.2rem 0 0 0;">{" &nbsp;|&nbsp; ".join(info_parts)}</p>
        </div>
        </div>
        <script>
        (function(){{
            var displayClock="{_display_clock}";
            var halftime={'true' if _is_halftime else 'false'};
            var period={_period};
            var els=[document.getElementById("match-clock-{_mi}"),document.getElementById("match-clock-m-{_mi}")];
            var halfLabel=period===1?"1st Half":"2nd Half";
            function show(txt){{ els.forEach(function(e){{if(e)e.textContent=txt;}}); }}
            if(halftime){{ show("HT"); }}
            else {{ show(displayClock+" \u2022 "+halfLabel); }}
        }})();
        </script>''',
        height=220,
    )

    # --- Live Match Stats ---
    _s1 = match.get("team_1_stats", {})
    _s2 = match.get("team_2_stats", {})
    _events = match.get("match_events", [])

    if _s1.get("possession", 0) > 0 or _s2.get("possession", 0) > 0:
        _poss1 = _s1.get("possession", 0)
        _poss2 = _s2.get("possession", 0)
        _shots1 = _s1.get("shots", 0)
        _shots2 = _s2.get("shots", 0)
        _sot1 = _s1.get("shots_on_target", 0)
        _sot2 = _s2.get("shots_on_target", 0)
        _corners1 = _s1.get("corners", 0)
        _corners2 = _s2.get("corners", 0)
        _fouls1 = _s1.get("fouls", 0)
        _fouls2 = _s2.get("fouls", 0)

        _events_html = ""
        if _events:
            _event_items = []
            for ev in _events:
                if ev["type"] == "goal":
                    icon = "⚽"
                elif ev["type"] == "own_goal":
                    icon = "⚽🔴"
                elif ev["type"] == "red":
                    icon = "🟥"
                else:
                    icon = "🟨"
                side_color = "#ffffff" if ev["side"] == 1 else "#e0e0e0"
                _flag_url = match["team_1_logo"] if ev["side"] == 1 else match["team_2_logo"]
                _flag_img = f'<img src="{_flag_url}" style="height:0.75rem; vertical-align:middle; margin-right:2px;">'
                _event_items.append(
                    f'<span style="display:inline-block; margin:0.15rem 0.3rem; padding:0.2rem 0.5rem; '
                    f'background:rgba(17,86,117,0.4); border-radius:6px; font-size:0.7rem; color:{side_color};">'
                    f'{icon} {ev["minute"]} {_flag_img}{ev["player"]}</span>'
                )
            _events_html = f'<div style="text-align:center; margin-top:0.6rem;">{"".join(_event_items)}</div>'

        st.markdown(
            f'<style>'
            f'@keyframes statPop {{ from {{ opacity:0; transform:scale(0.8); }} to {{ opacity:1; transform:scale(1); }} }}'
            f'@keyframes barGrow {{ from {{ width:0%; }} to {{ width:{_poss1}%; }} }}'
            f'.stat-pill {{ display:inline-block; background:rgba(17,86,117,0.4); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px); '
            f'border:1px solid rgba(41,181,232,0.2); border-radius:20px; padding:0.4rem 0.8rem; margin:0.2rem; text-align:center; '
            f'animation:statPop 0.5s ease backwards; width:90px; white-space:nowrap; }}'
            f'.stat-pill:nth-child(1) {{ animation-delay:0.1s; }}'
            f'.stat-pill:nth-child(2) {{ animation-delay:0.2s; }}'
            f'.stat-pill:nth-child(3) {{ animation-delay:0.3s; }}'
            f'.stat-pill:nth-child(4) {{ animation-delay:0.4s; }}'
            f'.stat-pill .val {{ font-size:1.2rem; font-weight:900; color:#FFD700; }}'
            f'.stat-pill .lbl {{ font-size:0.6rem; color:#e0e0e0; text-transform:uppercase; letter-spacing:0.5px; }}'
            f'@media(max-width:768px){{ .stat-row .stat-left {{ justify-content:flex-end!important; }} .stat-row .stat-right {{ justify-content:flex-start!important; }} }}'
            f'</style>'
            f'<div style="background:rgba(17,86,117,0.2); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px); '
            f'border-radius:14px; padding:1rem 1.5rem; margin:0.5rem 0; border:1px solid rgba(41,181,232,0.15);">'
            f'<div style="display:flex; justify-content:center; align-items:center; gap:0.5rem; margin-bottom:0.8rem;">'
            f'<div class="stat-pill"><div class="val">{_poss1:.0f}%</div><div class="lbl">Possession</div></div>'
            f'<div style="display:flex; flex:1; height:8px; border-radius:4px; overflow:hidden; box-shadow:0 0 10px rgba(41,181,232,0.2);">'
            f'<div style="width:{_poss1}%; background:linear-gradient(90deg, #29B5E8, #115675); transition:width 1s ease;"></div>'
            f'<div style="width:{_poss2}%; background:rgba(255,255,255,0.2);"></div>'
            f'</div>'
            f'<div class="stat-pill"><div class="val">{_poss2:.0f}%</div><div class="lbl">Possession</div></div>'
            f'</div>'
            f'<div class="stat-row" style="display:flex; justify-content:center; align-items:center; gap:0.5rem;">'
            f'<div class="stat-left" style="display:flex; gap:0.3rem; flex-wrap:wrap; justify-content:center;">'
            f'<div class="stat-pill"><div class="val">{_shots1}</div><div class="lbl">Shots</div></div>'
            f'<div class="stat-pill"><div class="val">{_sot1}</div><div class="lbl">On Target</div></div>'
            f'<div class="stat-pill"><div class="val">{_corners1}</div><div class="lbl">Corners</div></div>'
            f'<div class="stat-pill"><div class="val">{_fouls1}</div><div class="lbl">Fouls</div></div>'
            f'</div>'
            f'<div class="stat-divider" style="width:2px; height:50px; background:rgba(255,215,0,0.5); border-radius:1px; flex-shrink:0;"></div>'
            f'<div class="stat-right" style="display:flex; gap:0.3rem; flex-wrap:wrap; justify-content:center;">'
            f'<div class="stat-pill"><div class="val">{_shots2}</div><div class="lbl">Shots</div></div>'
            f'<div class="stat-pill"><div class="val">{_sot2}</div><div class="lbl">On Target</div></div>'
            f'<div class="stat-pill"><div class="val">{_corners2}</div><div class="lbl">Corners</div></div>'
            f'<div class="stat-pill"><div class="val">{_fouls2}</div><div class="lbl">Fouls</div></div>'
            f'</div>'
            f'</div>'
            f'{_events_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # --- Live Win Probability ---
    try:
        from utils.predictions import live_win_probability
        _lwp = live_win_probability(match)
        _p1 = _lwp["team1_pct"]
        _p2 = _lwp["team2_pct"]
        _dp = _lwp["draw_pct"]
        _reasoning = _lwp.get("reasoning", "")
        _reasoning_escaped = _reasoning.replace('"', '&quot;')
        _reasoning_html = f'<p title="{_reasoning_escaped}" style="text-align:center; font-size:0.7rem; color:rgba(255,255,255,0.7); margin:0.3rem 0 0 0; cursor:default; font-style:italic;">{_reasoning}</p>' if _reasoning else ''
        st.markdown(
            f'<div style="background:rgba(17,86,117,0.2); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px); '
            f'border-radius:14px; padding:0.8rem 1.5rem; margin:0.3rem 0; border:1px solid rgba(41,181,232,0.15);">'
            f'<p style="text-align:center; font-size:0.6rem; color:rgba(255,255,255,0.5); text-transform:uppercase; letter-spacing:1.5px; margin:0 0 0.4rem 0;">🤖 Live Win Probability</p>'
            f'<div style="display:flex; align-items:center; gap:0.5rem;">'
            f'<span style="font-size:0.85rem; font-weight:800; color:#29B5E8; min-width:3rem; text-align:right;">{_p1}%</span>'
            f'<div style="flex:1; display:flex; height:10px; border-radius:5px; overflow:hidden;">'
            f'<div style="width:{_p1}%; background:linear-gradient(90deg, #29B5E8, #115675); transition:width 1s ease;"></div>'
            f'<div style="width:{_dp}%; background:rgba(255,255,255,0.15);"></div>'
            f'<div style="width:{_p2}%; background:linear-gradient(90deg, #FFD700, #B8860B); transition:width 1s ease;"></div>'
            f'</div>'
            f'<span style="font-size:0.85rem; font-weight:800; color:#FFD700; min-width:3rem;">{_p2}%</span>'
            f'</div>'
            f'{_reasoning_html}'
            f'</div>',
            unsafe_allow_html=True,
        )
    except Exception:
        pass


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

    # Teams still in contention — 32 qualified for R32 minus knockout losers
    _ko_results = [r for r in _all_results if r.get("stage") not in ("Group Stage", "")]
    _ko_losers = set()
    for _r in _ko_results:
        _winner = _r.get("winner")
        if _winner:
            _loser = _r["team_2_name"] if _winner == _r["team_1_name"] else _r["team_1_name"]
            _ko_losers.add(_loser)
    _teams_left = 32 - len(_ko_losers)

    # Tournament stats — metric pills (hidden on mobile via CSS)
    _pill = 'display:inline-block; background:rgba(17,86,117,0.35); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px); border:1px solid rgba(41,181,232,0.2); border-radius:20px; padding:0.4rem 1.2rem; margin:0.2rem 0.3rem; width:180px; text-align:center; white-space:nowrap;'
    _pill_val = 'font-size:1.4rem; font-weight:900; color:#FFD700;'
    _pill_lbl = 'font-size:0.75rem; color:#e0e0e0; text-transform:uppercase; letter-spacing:1px;'

    st.markdown(
        f'<style>@media(max-width:768px){{.desktop-pills{{display:none!important}}}}</style>'
        f'<div class="desktop-pills" style="text-align:center; margin:0.5rem 0;">'
        f'<p style="font-size:1.2rem; color:#FFD700; font-weight:800; margin:0 0 0.5rem 0; letter-spacing:1px;">11 June – 19 July 2026</p>'
        f'<span style="{_pill}"><span class="countup" data-target="{_days_left}" style="{_pill_val}">0</span> <span style="{_pill_lbl}">days left</span></span>'
        f'<span style="{_pill}"><span class="countup" data-target="{_games_remaining}" style="{_pill_val}">0</span> <span style="{_pill_lbl}">games left</span></span>'
        f'<span style="{_pill}"><span class="countup" data-target="{_teams_left}" style="{_pill_val}">0</span> <span style="{_pill_lbl}">teams left</span></span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Count-up animation JS — injected via zero-height iframe targeting parent document
    import streamlit.components.v1 as components
    components.html(
        '''<script>
        (function(){
            var doc=window.parent.document;
            var els=doc.querySelectorAll(".countup");
            if(!els.length)return;
            var duration=1500,stagger=1000;
            els.forEach(function(el,i){
                var target=parseInt(el.getAttribute("data-target"));
                setTimeout(function(){
                    var start=performance.now();
                    function tick(now){
                        var t=Math.min((now-start)/duration,1);
                        var ease=1-Math.pow(1-t,4);
                        el.textContent=Math.round(ease*target);
                        if(t<1){ el.style.color="#ffffff"; requestAnimationFrame(tick); }
                        else { el.style.color="#FFD700"; }
                    }
                    requestAnimationFrame(tick);
                }, i*stagger);
            });
        })();
        </script>''',
        height=0,
    )

    # Live match display (via ESPN API — real-time)
    live_matches = get_live_matches()

    # Persist last known live matches to avoid flicker on API gaps
    if live_matches:
        st.session_state["_last_live"] = live_matches
    elif st.session_state.get("_last_live"):
        # Check if all cached matches actually finished
        _finished = {(r["team_1_name"], r["team_2_name"]) for r in get_all_results()}
        _still_live = []
        for _cached in st.session_state["_last_live"]:
            if (_cached["team_1_name"], _cached["team_2_name"]) not in _finished and \
               (_cached["team_2_name"], _cached["team_1_name"]) not in _finished:
                _still_live.append(_cached)
        if _still_live:
            live_matches = _still_live
        else:
            del st.session_state["_last_live"]

    if live_matches:
        _stage_label = live_matches[0].get("stage", "")
        _stage_short = {"Round of 32": "R32 ", "Round of 16": "R16 ", "Quarter-finals": "QF ", "Semi-finals": "SF ", "Final": "Final "}.get(_stage_label, "")
        _header_text = f"Current {_stage_short}Matches" if len(live_matches) > 1 else f"Current {_stage_short}Match"
        st.markdown(f'<h3 style="text-align:center; margin:0.5rem 0 0.3rem 0;">{_header_text}</h3>', unsafe_allow_html=True)

        for _mi, match in enumerate(live_matches):
            if _mi > 0:
                st.markdown('<hr style="border:none; border-top:1px solid rgba(41,181,232,0.2); margin:0.8rem 0;">', unsafe_allow_html=True)
            _render_live_match(match, _mi)

    else:
        # --- NEXT MATCH COUNTDOWN (Stadium Card) ---
        _upcoming = get_upcoming_matches()
        if _upcoming:
            # Group matches starting at the same time as the first upcoming
            _first_time = _upcoming[0].get("utc_iso", "")
            _next_matches = [m for m in _upcoming if m.get("utc_iso") == _first_time] if _first_time else [_upcoming[0]]

            _next_match_time = None
            if _first_time:
                try:
                    _next_match_time = datetime.fromisoformat(_first_time).astimezone(_et)
                except Exception:
                    _next_match_time = None

            _stage_label = _next_matches[0].get("stage", "")
            _stage_short = {"Round of 32": "R32 ", "Round of 16": "R16 ", "Quarter-finals": "QF ", "Semi-finals": "SF ", "Final": "Final "}.get(_stage_label, "")
            _header_text = f"Next {_stage_short}Matches" if len(_next_matches) > 1 else f"Next {_stage_short}Match"
            st.markdown(f'<h3 style="text-align:center; margin:0.5rem 0 0.3rem 0;">{_header_text}</h3>', unsafe_allow_html=True)

            _target_iso = ""
            _countdown_active = False
            if _next_match_time:
                _target_iso = _next_match_time.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                _countdown_active = _next_match_time > _now

            import streamlit.components.v1 as components

            # Build all match rows into one unified card with shared countdown
            _match_rows_html = ""
            for _ni, next_match in enumerate(_next_matches):
                _info_parts = []
                _match_stage = next_match.get("stage", "")
                if _match_stage == "Group Stage":
                    group_name = _get_group(next_match)
                    if group_name:
                        _info_parts.append(group_name)
                else:
                    _info_parts.append(_match_stage)
                if next_match.get("venue"):
                    venue_str = next_match["venue"]
                    if next_match.get("city"):
                        venue_str += f', {next_match["city"]}'
                    _info_parts.append(venue_str)
                _info_line = " | ".join(_info_parts)
                _divider = '<hr style="border:none; border-top:1px solid rgba(41,181,232,0.2); margin:0.8rem 0;">' if _ni > 0 else ''
                _match_rows_html += (
                    f'{_divider}'
                    f'<div class="desktop-layout" style="justify-content:space-between; align-items:center;">'
                    f'<div style="text-align:center; flex:1;">'
                    f'<img src="{next_match["team_1_logo"]}" style="height:3rem; margin-bottom:0.3rem;"><br>'
                    f'<span style="font-size:1.2rem; font-weight:700; color:#ffffff;">{next_match["team_1_name"]}</span><br>'
                    f'</div>'
                    f'<div style="text-align:center; flex:0.8;">'
                    f'<p style="font-size:2.5rem; color:rgba(255,255,255,0.3); font-weight:900; margin:0 0 0.2rem 0; letter-spacing:3px;">VS</p>'
                    f'<p style="font-size:0.75rem; color:#e0e0e0; margin:0;">{_info_line}</p></div>'
                    f'<div style="text-align:center; flex:1;">'
                    f'<img src="{next_match["team_2_logo"]}" style="height:3rem; margin-bottom:0.3rem;"><br>'
                    f'<span style="font-size:1.2rem; font-weight:700; color:#ffffff;">{next_match["team_2_name"]}</span><br>'
                    f'</div>'
                    f'</div>'
                    f'<div class="mobile-layout" style="text-align:center;">'
                    f'<div style="display:flex; justify-content:center; align-items:center; gap:0.5rem; margin-bottom:0.2rem;">'
                    f'<img src="{next_match["team_1_logo"]}" style="height:1.6rem;">'
                    f'<span style="font-size:0.9rem; font-weight:700; color:#fff;">{next_match["team_1_name"]}</span>'
                    f'<span style="font-size:0.85rem; color:#FFD700; font-weight:700;">vs</span>'
                    f'<img src="{next_match["team_2_logo"]}" style="height:1.6rem;">'
                    f'<span style="font-size:0.9rem; font-weight:700; color:#fff;">{next_match["team_2_name"]}</span>'
                    f'</div>'
                    f'<p style="font-size:0.65rem; color:#e0e0e0; margin:0;">{_info_line}</p>'
                    f'</div>'
                )

            _time_display = _next_matches[0].get("time_et", "")
            _date_display = _next_matches[0].get("date", "")
            _countdown_html = ""
            if _countdown_active:
                _countdown_html = (
                    f'<p style="font-size:0.7rem; color:#e0e0e0; text-transform:uppercase; letter-spacing:2px; margin:0 0 0.2rem 0;">Kickoff in</p>'
                    f'<p id="cd-unified" style="font-size:3rem; font-weight:900; color:#FFD700; margin:0; line-height:1; font-variant-numeric:tabular-nums;">--:--:--</p>'
                    f'<p style="font-size:0.75rem; color:#e0e0e0; margin:0.2rem 0 0.8rem 0;">{_date_display} at {_time_display}</p>'
                )
            else:
                _countdown_html = (
                    f'<p style="font-size:2rem; font-weight:900; color:#FFD700; margin:0 0 0.5rem 0; animation:kickPulse 1.5s infinite;">&#9917; KICKOFF</p>'
                )

            _card_height = 280 + (len(_next_matches) - 1) * 120
            components.html(
                f'''<style>
                @keyframes kickPulse {{ 0%{{opacity:1}} 50%{{opacity:0.5}} 100%{{opacity:1}} }}
                .unified-card .desktop-layout {{ display:flex; }}
                .unified-card .mobile-layout {{ display:none; }}
                @media(max-width:768px){{
                    .unified-card{{padding:1rem!important}}
                    .unified-card .desktop-layout {{ display:none; }}
                    .unified-card .mobile-layout {{ display:block; }}
                }}
                </style>
                <div class="unified-card" style="background:linear-gradient(180deg, rgba(17,86,117,0.4) 0%, rgba(41,181,232,0) 100%); border-radius:20px; padding:2rem 3rem; margin:0; border:1px solid rgba(41,181,232,0.25); font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; text-align:center;">
                {_countdown_html}
                {_match_rows_html}
                </div>
                <script>
                (function(){{
                    var target=new Date("{_target_iso}").getTime();
                    var el=document.getElementById("cd-unified");
                    if(!el)return;
                    function tick(){{
                        var diff=Math.max(0,Math.floor((target-Date.now())/1000));
                        var d=Math.floor(diff/86400),h=Math.floor((diff%86400)/3600),m=Math.floor((diff%3600)/60),s=diff%60;
                        var t=d>0?d+"d "+String(h).padStart(2,"0")+":"+String(m).padStart(2,"0")+":"+String(s).padStart(2,"0"):String(h).padStart(2,"0")+":"+String(m).padStart(2,"0")+":"+String(s).padStart(2,"0");
                        el.textContent=t;
                    }}
                    tick();setInterval(tick,1000);
                }})();
                </script>''',
                height=_card_height,
            )


# Render the auto-refreshing fragment
_live_section()

# --- R32 Bracket Preview ---
_BRACKET_PREVIEW = "vertical"  # "vertical", "full", "mini", "grid", or None

if _BRACKET_PREVIEW == "vertical":
    st.markdown('<h3 style="text-align:center; margin:1rem 0 0.5rem 0;">🏆 Road to the Final</h3>', unsafe_allow_html=True)
    from utils.bracket_seeding import get_r32_seedings
    from utils.bracket_vertical import generate_vertical_bracket
    from utils.football_api import get_all_results as _get_results_vb, get_knockout_matchups as _get_ko
    from utils.predictions import get_predictions
    import streamlit.components.v1 as _components
    _seedings = get_r32_seedings()
    _r32 = _seedings["r32_matchups"]
    while len(_r32) < 16:
        _r32.append(("TBD", "TBD"))
    _ko_data = _get_ko()
    _all_results_vb = _get_results_vb()
    # Collect all unplayed matchups for predictions
    _unplayed = []
    for _round in [_ko_data["qf"], _ko_data["sf"], _ko_data["final"], _ko_data["3rd_place"]]:
        _unplayed.extend(_round)
    try:
        _predictions = get_predictions(len(_all_results_vb), tuple(_unplayed))
    except Exception:
        _predictions = {}
    _vb_html = generate_vertical_bracket(
        r32_matchups=_r32,
        results=_all_results_vb,
        team_flags=_seedings["team_flags"],
        confirmed_teams=_seedings["confirmed_r32"],
        r16_matchups=_ko_data["r16"],
        qf_matchups=_ko_data["qf"],
        sf_matchups=_ko_data["sf"],
        final_matchups=_ko_data["final"],
        third_place_matchups=_ko_data["3rd_place"],
        match_dates=_ko_data.get("dates", {}),
        predictions=_predictions,
    )
    _components.html(_vb_html, height=650, scrolling=True)

if _BRACKET_PREVIEW == "full":
    st.markdown('<h3 style="text-align:center; margin:1rem 0 0.5rem 0;">🏆 Round of 32</h3>', unsafe_allow_html=True)
    from utils.bracket_seeding import get_r32_seedings
    from utils.bracket_html import generate_interactive_bracket
    from utils.football_api import get_all_results as _get_results_for_bracket
    import streamlit.components.v1 as _components
    _seedings = get_r32_seedings()
    _r32 = _seedings["r32_matchups"]
    while len(_r32) < 16:
        _r32.append(("TBD", "TBD"))
    # Build locked winners from results
    _br_results = _get_results_for_bracket()
    _br_locked = {}
    for _r in _br_results:
        _w = _r.get("winner")
        if not _w:
            if _r["team_1_score"] > _r["team_2_score"]:
                _w = _r["team_1_name"]
            elif _r["team_2_score"] > _r["team_1_score"]:
                _w = _r["team_2_name"]
        if _w:
            _br_locked[(_r["team_1_name"], _r["team_2_name"])] = _w
            _br_locked[(_r["team_2_name"], _r["team_1_name"])] = _w
    _bracket_html = generate_interactive_bracket(
        r32_matchups=_r32,
        locked_winners=_br_locked,
        current_picks=[None] * 31,
        team_flags=_seedings["team_flags"],
        team_list=_seedings["team_list"],
        confirmed_teams=_seedings["confirmed_r32"],
    )
    _components.html(_bracket_html, height=1190, scrolling=True)
    st.markdown(
        '<p style="text-align:center; margin:0.3rem 0;"><a href="/Bracket_Builder" target="_self" '
        'style="color:#FFD700; text-decoration:none; font-size:0.85rem; font-weight:700;">Build Your Full Bracket →</a></p>',
        unsafe_allow_html=True,
    )

if _BRACKET_PREVIEW in ("mini", "both"):
    st.markdown('<h3 style="text-align:center; margin:1rem 0 0.5rem 0;">🏆 Round of 32 Preview</h3>', unsafe_allow_html=True)
    from utils.bracket_seeding import get_r32_seedings
    from utils.bracket_mini import generate_mini_bracket
    import streamlit.components.v1 as _components
    _seedings = get_r32_seedings()
    _mini_html = generate_mini_bracket(
        r32_matchups=_seedings["r32_matchups"],
        confirmed_teams=_seedings["confirmed_r32"],
        team_flags=_seedings["team_flags"],
    )
    _mini_height = max(280, len(_seedings["r32_matchups"]) * 52 + 40)
    _components.html(_mini_html, height=_mini_height, scrolling=False)
    st.markdown(
        '<p style="text-align:center; margin:0.3rem 0;"><a href="/Bracket_Builder" target="_self" '
        'style="color:#FFD700; text-decoration:none; font-size:0.85rem; font-weight:700;">Build Your Full Bracket →</a></p>',
        unsafe_allow_html=True,
    )

if _BRACKET_PREVIEW in ("grid", "both"):
    if _BRACKET_PREVIEW == "both":
        st.markdown("---")
    st.markdown('<h3 style="text-align:center; margin:1rem 0 0.5rem 0;">🏆 Round of 32</h3>', unsafe_allow_html=True)
    from utils.bracket_seeding import get_r32_seedings
    _seedings = get_r32_seedings()
    _matchups = _seedings["r32_matchups"]
    _flags = _seedings["team_flags"]
    _confirmed = _seedings["confirmed_r32"]

    _col1, _col2 = st.columns(2)
    for _i, (_t1, _t2) in enumerate(_matchups):
        _col = _col1 if _i < len(_matchups) // 2 else _col2
        _match_num = _i + 1
        _both_confirmed = _t1 != "TBD" and _t2 != "TBD"

        # Team display
        if _t1 == "TBD":
            _d1 = '<span style="color:rgba(255,255,255,0.35); font-style:italic; font-size:0.85rem;">TBD</span>'
        else:
            _d1 = f'<span style="color:#ffffff; font-weight:700; font-size:0.85rem;">{_flags.get(_t1, "")} {_t1}</span>'

        if _t2 == "TBD":
            _d2 = '<span style="color:rgba(255,255,255,0.35); font-style:italic; font-size:0.85rem;">TBD</span>'
        else:
            _d2 = f'<span style="color:#ffffff; font-weight:700; font-size:0.85rem;">{_flags.get(_t2, "")} {_t2}</span>'

        _border_color = "rgba(0,230,118,0.4)" if _both_confirmed else "rgba(41,181,232,0.15)"
        _glow = "box-shadow:0 2px 12px rgba(0,230,118,0.08);" if _both_confirmed else ""

        with _col:
            st.markdown(
                f'<div style="background:linear-gradient(135deg, rgba(17,86,117,0.4) 0%, rgba(13,61,82,0.6) 100%); '
                f'border-radius:12px; padding:0.7rem 1rem; margin:0.3rem 0; '
                f'border:1px solid {_border_color}; {_glow} '
                f'backdrop-filter:blur(6px); -webkit-backdrop-filter:blur(6px); '
                f'display:flex; align-items:center; justify-content:space-between; gap:0.4rem;">'
                f'<div style="flex:1; text-align:left;">{_d1}</div>'
                f'<div style="flex-shrink:0; text-align:center;">'
                f'<span style="font-size:0.6rem; color:rgba(255,215,0,0.7); font-weight:800; letter-spacing:1px;">VS</span>'
                f'</div>'
                f'<div style="flex:1; text-align:right;">{_d2}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        '<p style="text-align:center; margin:0.5rem 0;"><a href="/Bracket_Builder" target="_self" '
        'style="color:#FFD700; text-decoration:none; font-size:0.85rem; font-weight:700;">Build Your Full Bracket →</a></p>',
        unsafe_allow_html=True,
    )

st.markdown("---")


@st.fragment(run_every=60)
def _schedule_section():
    """Auto-refreshing schedule/results — updates when matches start or finish."""
    import pandas as pd

    # Past Matches section (all results as dataframe in expander)
    _all_results = get_all_results()
    if _all_results:
        with st.expander("📋 Past Match Results"):
            results_data = []
            for m in reversed(_all_results):  # most recent first
                stage = m.get("stage", "")
                if stage == "Group Stage":
                    stage = _get_group(m) or "Group Stage"
                date_str = m.get("date", "")
                _goals = [e for e in m.get("match_events", []) if e["type"] in ("goal", "own_goal")]
                _scorer_str = ", ".join(f'{g["player"]} {g["minute"]}' for g in _goals) if _goals else ""
                results_data.append({
                    "Date": date_str,
                    "Result": f"{m['team_1_name']} {m['team_1_score']} – {m['team_2_score']} {m['team_2_name']}",
                    "Scorers": _scorer_str,
                    "Stage": stage,
                })
            df = pd.DataFrame(results_data)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                height=400,
            )


_schedule_section()

render_footer()
