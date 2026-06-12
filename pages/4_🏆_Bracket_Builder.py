import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.data_loader import load_teams
from utils.football_api import get_all_results
from utils.banner import render_tournament_banner
from utils.footer import render_footer

render_tournament_banner()
st.markdown('<h2 style="text-align:center; margin:0.3rem 0;">🏆 Knockout Bracket Builder</h2>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; font-size:0.75rem; color:#ffffff; margin-top:-0.3rem; text-transform:uppercase; letter-spacing:2px;">Pick your winners from the Round of 32 all the way to the Final. Your selections are saved in your session.</p>', unsafe_allow_html=True)

teams = load_teams()
team_list = teams["TEAM_NAME"].tolist()
team_flags = dict(zip(teams["TEAM_NAME"], teams["FLAG_EMOJI"]))


def team_display(name):
    return f"{team_flags.get(name, '')} {name}" if name else "TBD"


# Initialize bracket state
if "bracket" not in st.session_state:
    st.session_state.bracket = {}
if "bracket_version" not in st.session_state:
    st.session_state.bracket_version = 0

_v = st.session_state.bracket_version

# Seed the bracket using actual results where available, FIFA ranking as fallback
groups = sorted(teams["GROUP_LETTER"].unique())
group_winners = []
group_runners = []

_results = get_all_results()

_team_group = dict(zip(teams["TEAM_NAME"], teams["GROUP_LETTER"]))


def _get_group_standings(group_letter):
    g_teams = teams[teams["GROUP_LETTER"] == group_letter]
    team_names = set(g_teams["TEAM_NAME"].tolist())

    group_results = [
        r for r in _results
        if r["team_1_name"] in team_names and r["team_2_name"] in team_names
    ]

    if not group_results:
        return None

    points = {t: 0 for t in team_names}
    gd = {t: 0 for t in team_names}
    gf = {t: 0 for t in team_names}

    for r in group_results:
        t1, t2 = r["team_1_name"], r["team_2_name"]
        s1, s2 = r["team_1_score"], r["team_2_score"]
        gf[t1] = gf.get(t1, 0) + s1
        gf[t2] = gf.get(t2, 0) + s2
        gd[t1] = gd.get(t1, 0) + (s1 - s2)
        gd[t2] = gd.get(t2, 0) + (s2 - s1)
        if s1 > s2:
            points[t1] += 3
        elif s2 > s1:
            points[t2] += 3
        else:
            points[t1] += 1
            points[t2] += 1

    sorted_teams = sorted(
        team_names,
        key=lambda t: (points[t], gd[t], gf[t]),
        reverse=True,
    )
    return sorted_teams


for g in groups:
    standings = _get_group_standings(g)
    if standings and len(standings) >= 2:
        group_winners.append(standings[0])
        group_runners.append(standings[1])
    else:
        g_teams = teams[teams["GROUP_LETTER"] == g].sort_values("FIFA_RANKING")
        group_winners.append(g_teams.iloc[0]["TEAM_NAME"])
        group_runners.append(g_teams.iloc[1]["TEAM_NAME"])

# Round of 32 matchups
r32_matchups = [
    (group_winners[0], group_runners[3]),
    (group_winners[1], group_runners[2]),
    (group_winners[2], group_runners[1]),
    (group_winners[3], group_runners[0]),
    (group_winners[4], group_runners[7]),
    (group_winners[5], group_runners[6]),
    (group_winners[6], group_runners[5]),
    (group_winners[7], group_runners[4]),
    (group_winners[8], group_runners[11]),
    (group_winners[9], group_runners[10]),
    (group_winners[10], group_runners[9]),
    (group_winners[11], group_runners[8]),
    (group_winners[0], group_runners[5]),
    (group_winners[4], group_runners[1]),
    (group_winners[8], group_runners[3]),
    (group_winners[2], group_runners[11]),
]


def get_saved(key):
    return st.session_state.bracket.get(key)


def save_choice(key):
    st.session_state.bracket[key] = st.session_state[key]


# Round of 32
st.markdown("---")
st.subheader("🔵 Round of 32 → Round of 16")

r32_winners = []
cols = st.columns(4)
for i, (t1, t2) in enumerate(r32_matchups):
    with cols[i % 4]:
        options = [t1, t2]
        saved = get_saved(f"v{_v}_r32_{i}")
        idx = options.index(saved) if saved in options else None
        choice = st.radio(
            f"Match {i+1}",
            options,
            index=idx,
            format_func=team_display,
            key=f"v{_v}_r32_{i}",
            on_change=save_choice,
            args=(f"v{_v}_r32_{i}",),
            horizontal=True,
        )
        r32_winners.append(choice)

# Round of 16
st.markdown("---")
st.subheader("🟢 Round of 16 → Quarter-finals")

r16_matchups = [(r32_winners[i], r32_winners[i + 1]) for i in range(0, 16, 2)]
r16_winners = []
cols = st.columns(4)
for i, (t1, t2) in enumerate(r16_matchups):
    with cols[i % 4]:
        options = [t1, t2]
        saved = get_saved(f"v{_v}_r16_{i}")
        idx = options.index(saved) if saved and saved in options else None
        choice = st.radio(
            f"R16 Match {i+1}",
            options,
            index=idx,
            format_func=team_display,
            key=f"v{_v}_r16_{i}",
            on_change=save_choice,
            args=(f"v{_v}_r16_{i}",),
            horizontal=True,
        )
        r16_winners.append(choice)

# Quarter-finals
st.markdown("---")
st.subheader("🟡 Quarter-finals → Semi-finals")

qf_matchups = [(r16_winners[i], r16_winners[i + 1]) for i in range(0, 8, 2)]
qf_winners = []
cols = st.columns(4)
for i, (t1, t2) in enumerate(qf_matchups):
    with cols[i % 4]:
        options = [t1, t2]
        saved = get_saved(f"v{_v}_qf_{i}")
        idx = options.index(saved) if saved and saved in options else None
        choice = st.radio(
            f"QF {i+1}",
            options,
            index=idx,
            format_func=team_display,
            key=f"v{_v}_qf_{i}",
            on_change=save_choice,
            args=(f"v{_v}_qf_{i}",),
            horizontal=True,
        )
        qf_winners.append(choice)

# Semi-finals
st.markdown("---")
st.subheader("🟠 Semi-finals → Final")

sf_matchups = [(qf_winners[i], qf_winners[i + 1]) for i in range(0, 4, 2)]
sf_winners = []
cols = st.columns(2)
for i, (t1, t2) in enumerate(sf_matchups):
    with cols[i]:
        options = [t1, t2]
        saved = get_saved(f"v{_v}_sf_{i}")
        idx = options.index(saved) if saved and saved in options else None
        choice = st.radio(
            f"Semi-final {i+1}",
            options,
            index=idx,
            format_func=team_display,
            key=f"v{_v}_sf_{i}",
            on_change=save_choice,
            args=(f"v{_v}_sf_{i}",),
            horizontal=True,
        )
        sf_winners.append(choice)

# Final
st.markdown("---")
st.subheader("🏆 THE FINAL — MetLife Stadium, New Jersey")

if len(sf_winners) == 2 and sf_winners[0] and sf_winners[1]:
    options = sf_winners
    saved = get_saved(f"v{_v}_final")
    idx = options.index(saved) if saved and saved in options else None
    champion = st.radio(
        "Pick your World Cup Champion",
        options,
        index=idx,
        format_func=team_display,
        key=f"v{_v}_final",
        on_change=save_choice,
        args=(f"v{_v}_final",),
        horizontal=True,
    )

    if champion and st.session_state.bracket.get(f"v{_v}_final") is not None:
        st.markdown(
            f'<div style="text-align:center; padding:1.5rem; margin-top:1rem; background:#115675; border-radius:12px;">'
            f'<p style="font-size:3rem; margin:0;">{team_flags.get(champion, "🏆")}</p>'
            f'<p style="font-size:1.5rem; font-weight:800; color:#FFD700; margin:0.5rem 0 0 0;">🏆 {champion} are World Cup Champions! 🏆</p>'
            f'<p style="font-size:1rem; color:#ffffff; margin:0.3rem 0 0 0;">Your predicted winner of the 2026 FIFA World Cup</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

# Reset button
st.markdown("---")
if st.button("🔄 Reset all bracket picks", type="secondary"):
    st.session_state.bracket = {}
    st.session_state.bracket_version += 1
    st.rerun()

render_footer()
