"""Shared bracket seeding logic — fetches actual R32 matchups from ESPN."""

from utils.data_loader import load_teams
from utils.football_api import get_knockout_matchups


def get_r32_seedings():
    """Fetch R32 matchups from ESPN and build confirmed qualifiers set.

    Returns:
        dict with keys: r32_matchups, confirmed_r32, team_flags, team_list
    """
    teams = load_teams()
    team_list = sorted(teams["TEAM_NAME"].tolist())
    team_flags = dict(zip(teams["TEAM_NAME"], teams["FLAG_EMOJI"]))

    ko = get_knockout_matchups()
    r32_matchups = ko["r32"]  # list of (team1, team2) tuples from ESPN

    # Confirmed = all named teams (not "TBD") in R32 matchups
    confirmed_r32 = set()
    for t1, t2 in r32_matchups:
        if t1 != "TBD":
            confirmed_r32.add(t1)
        if t2 != "TBD":
            confirmed_r32.add(t2)

    return {
        "r32_matchups": r32_matchups,
        "confirmed_r32": confirmed_r32,
        "team_flags": team_flags,
        "team_list": team_list,
    }
