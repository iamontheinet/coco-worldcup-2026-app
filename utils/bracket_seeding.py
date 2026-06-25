"""Shared bracket seeding logic — computes R32 matchups from group standings."""

from utils.data_loader import load_teams
from utils.football_api import get_all_results, get_live_matches


def get_r32_seedings():
    """Compute R32 matchups, confirmed qualifiers, and team flags.

    Returns:
        dict with keys: r32_matchups, confirmed_r32, team_flags, team_list
    """
    teams = load_teams()
    team_list = sorted(teams["TEAM_NAME"].tolist())
    team_flags = dict(zip(teams["TEAM_NAME"], teams["FLAG_EMOJI"]))

    groups = sorted(teams["GROUP_LETTER"].unique())
    group_winners = []
    group_runners = []
    group_thirds = []

    _results = get_all_results()
    _live = get_live_matches()
    _all_match_data = _results + _live

    def _get_group_standings(group_letter):
        g_teams = teams[teams["GROUP_LETTER"] == group_letter]
        team_names = set(g_teams["TEAM_NAME"].tolist())
        group_results = [
            r for r in _all_match_data
            if r["team_1_name"] in team_names and r["team_2_name"] in team_names
        ]
        if not group_results:
            return None, False
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
        is_complete = len(group_results) >= 6
        return sorted_teams, is_complete

    confirmed_r32 = set()
    _group_pts = {}
    _group_played = {}
    # Track contenders per position (teams that could still finish 1st/2nd/3rd)
    _winner_contenders = []  # list of lists per group
    _runner_contenders = []

    for g in groups:
        g_team_names = set(teams[teams["GROUP_LETTER"] == g]["TEAM_NAME"].tolist())
        g_results = [r for r in _all_match_data if r["team_1_name"] in g_team_names and r["team_2_name"] in g_team_names]
        for r in g_results:
            t1, t2 = r["team_1_name"], r["team_2_name"]
            _group_played[t1] = _group_played.get(t1, 0) + 1
            _group_played[t2] = _group_played.get(t2, 0) + 1
            s1, s2 = r["team_1_score"], r["team_2_score"]
            if s1 > s2:
                _group_pts[t1] = _group_pts.get(t1, 0) + 3
            elif s2 > s1:
                _group_pts[t2] = _group_pts.get(t2, 0) + 3
            else:
                _group_pts[t1] = _group_pts.get(t1, 0) + 1
                _group_pts[t2] = _group_pts.get(t2, 0) + 1

    for g in groups:
        standings, complete = _get_group_standings(g)
        if standings and len(standings) >= 3:
            group_winners.append(standings[0])
            group_runners.append(standings[1])
            group_thirds.append(standings[2])
            if complete:
                confirmed_r32.add(standings[0])
                confirmed_r32.add(standings[1])
                confirmed_r32.add(standings[2])
                _winner_contenders.append([standings[0]])
                _runner_contenders.append([standings[1]])
            else:
                # Non-eliminated teams could still finish in any top position
                # A team is "eliminated" if 0 pts after 2 games with 2+ teams at 3+ pts
                _alive = []
                g_team_names = list(set(teams[teams["GROUP_LETTER"] == g]["TEAM_NAME"].tolist()))
                for t in g_team_names:
                    pts = _group_pts.get(t, 0)
                    played = _group_played.get(t, 0)
                    if played >= 2 and pts == 0:
                        others_with_3plus = sum(1 for ot in g_team_names if ot != t and _group_pts.get(ot, 0) >= 3)
                        if others_with_3plus >= 2:
                            continue  # eliminated
                    _alive.append(t)
                # Confirmed winner: team with 6+ pts clinched
                if _group_pts.get(standings[0], 0) >= 6 and _group_played.get(standings[0], 0) >= 2:
                    confirmed_r32.add(standings[0])
                    _winner_contenders.append([standings[0]])
                else:
                    _winner_contenders.append(_alive)
                # Runner-up contenders: all alive except confirmed winner
                if standings[0] in confirmed_r32:
                    _runner_contenders.append([t for t in _alive if t != standings[0]])
                else:
                    _runner_contenders.append(_alive)
                # Check clinched for top 3
                for t in standings[:3]:
                    if _group_pts.get(t, 0) >= 6 and _group_played.get(t, 0) >= 2:
                        confirmed_r32.add(t)
        elif standings and len(standings) >= 2:
            group_winners.append(standings[0])
            group_runners.append(standings[1])
            group_thirds.append(None)
            _winner_contenders.append(list(set(teams[teams["GROUP_LETTER"] == g]["TEAM_NAME"].tolist())))
            _runner_contenders.append(list(set(teams[teams["GROUP_LETTER"] == g]["TEAM_NAME"].tolist())))
        else:
            g_teams_df = teams[teams["GROUP_LETTER"] == g].sort_values("FIFA_RANKING")
            group_winners.append(g_teams_df.iloc[0]["TEAM_NAME"])
            group_runners.append(g_teams_df.iloc[1]["TEAM_NAME"])
            group_thirds.append(g_teams_df.iloc[2]["TEAM_NAME"] if len(g_teams_df) >= 3 else None)
            _winner_contenders.append(g_teams_df["TEAM_NAME"].tolist())
            _runner_contenders.append(g_teams_df["TEAM_NAME"].tolist())

    _third_place_teams = [t for t in group_thirds if t]
    _best_thirds = _third_place_teams[:8]

    r32_matchups = [
        (group_winners[0], group_runners[5]),
        (group_winners[1], group_runners[4]),
        (group_winners[2], group_runners[3]),
        (group_winners[3], group_runners[2]),
        (group_winners[4], group_runners[1]),
        (group_winners[5], group_runners[0]),
        (group_winners[6], group_runners[11]),
        (group_winners[7], group_runners[10]),
        (group_winners[8], group_runners[9]),
        (group_winners[9], group_runners[8]),
        (group_winners[10], group_runners[7]),
        (group_winners[11], group_runners[6]),
        (_best_thirds[0] if len(_best_thirds) > 0 else "TBD", _best_thirds[7] if len(_best_thirds) > 7 else "TBD"),
        (_best_thirds[1] if len(_best_thirds) > 1 else "TBD", _best_thirds[6] if len(_best_thirds) > 6 else "TBD"),
        (_best_thirds[2] if len(_best_thirds) > 2 else "TBD", _best_thirds[5] if len(_best_thirds) > 5 else "TBD"),
        (_best_thirds[3] if len(_best_thirds) > 3 else "TBD", _best_thirds[4] if len(_best_thirds) > 4 else "TBD"),
    ]

    # Build contender lists per R32 slot (who could end up in each position)
    # Matchup indices: 0-5 use winner[i] vs runner[j], 6-11 same, 12-15 use thirds
    r32_contenders = []
    _matchup_indices = [
        (0, 5), (1, 4), (2, 3), (3, 2), (4, 1), (5, 0),
        (6, 11), (7, 10), (8, 9), (9, 8), (10, 7), (11, 6),
    ]
    for wi, ri in _matchup_indices:
        t1_options = _winner_contenders[wi] if wi < len(_winner_contenders) else [group_winners[wi]]
        t2_options = _runner_contenders[ri] if ri < len(_runner_contenders) else [group_runners[ri]]
        r32_contenders.append((t1_options, t2_options))
    # Third-place matchups — just use single team (too complex to enumerate all 3rd possibilities)
    for i in range(4):
        r32_contenders.append(([r32_matchups[12 + i][0]], [r32_matchups[12 + i][1]]))

    return {
        "r32_matchups": r32_matchups,
        "r32_contenders": r32_contenders,
        "confirmed_r32": confirmed_r32,
        "team_flags": team_flags,
        "team_list": team_list,
        "group_winners": group_winners,
        "group_runners": group_runners,
    }
