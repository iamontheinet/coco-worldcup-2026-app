"""Shared bracket seeding logic — fetches actual R32 matchups from ESPN."""

from utils.data_loader import load_teams
from utils.football_api import get_knockout_matchups, get_all_results


def get_r32_seedings():
    """Fetch R32 matchups from ESPN and build confirmed qualifiers set.

    Returns:
        dict with keys: r32_matchups, confirmed_r32, team_flags, team_list
    """
    teams = load_teams()
    team_list = sorted(teams["TEAM_NAME"].tolist())
    team_flags = dict(zip(teams["TEAM_NAME"], teams["FLAG_EMOJI"]))
    group_map = dict(zip(teams["TEAM_NAME"], teams["GROUP_LETTER"]))

    ko = get_knockout_matchups()
    r32_matchups = ko["r32"]  # list of (team1, team2) tuples from ESPN

    # Confirmed = teams named in ESPN R32 matchups + teams with 6+ group pts (clinched)
    confirmed_r32 = set()
    for t1, t2 in r32_matchups:
        if t1 != "TBD":
            confirmed_r32.add(t1)
        if t2 != "TBD":
            confirmed_r32.add(t2)

    # Also add teams that clinched via points (4+ pts after 2 group games = effectively guaranteed top 3)
    results = get_all_results()
    pts = {}
    played = {}
    for r in results:
        t1, t2 = r["team_1_name"], r["team_2_name"]
        if group_map.get(t1) == group_map.get(t2):
            played[t1] = played.get(t1, 0) + 1
            played[t2] = played.get(t2, 0) + 1
            s1, s2 = r["team_1_score"], r["team_2_score"]
            if s1 > s2:
                pts[t1] = pts.get(t1, 0) + 3
            elif s2 > s1:
                pts[t2] = pts.get(t2, 0) + 3
            else:
                pts[t1] = pts.get(t1, 0) + 1
                pts[t2] = pts.get(t2, 0) + 1
    for t, p in pts.items():
        if p >= 4 and played.get(t, 0) >= 2:
            confirmed_r32.add(t)

    return {
        "r32_matchups": r32_matchups,
        "confirmed_r32": confirmed_r32,
        "team_flags": team_flags,
        "team_list": team_list,
    }
