import streamlit as st
from collections import defaultdict


def _aggregate_team_stats(results):
    """Build per-team tournament stats from all finished matches."""
    stats = defaultdict(lambda: {
        'played': 0, 'wins': 0, 'draws': 0, 'losses': 0,
        'gf': 0, 'ga': 0, 'possession_sum': 0,
        'shots_sum': 0, 'sot_sum': 0, 'clean_sheets': 0,
        'opponents_beaten': [],
    })

    for r in results:
        t1, t2 = r['team_1_name'], r['team_2_name']
        s1, s2 = r['team_1_score'], r['team_2_score']
        stats1 = r.get('team_1_stats') or {}
        stats2 = r.get('team_2_stats') or {}

        for team, opp, gs, gc, mstats in [(t1, t2, s1, s2, stats1), (t2, t1, s2, s1, stats2)]:
            stats[team]['played'] += 1
            stats[team]['gf'] += gs
            stats[team]['ga'] += gc
            if gs > gc:
                stats[team]['wins'] += 1
                stats[team]['opponents_beaten'].append(opp)
            elif gs == gc:
                stats[team]['draws'] += 1
            else:
                stats[team]['losses'] += 1
            if gc == 0:
                stats[team]['clean_sheets'] += 1
            stats[team]['possession_sum'] += mstats.get('possession', 50)
            stats[team]['shots_sum'] += mstats.get('shots', 0)
            stats[team]['sot_sum'] += mstats.get('shots_on_target', 0)

    return dict(stats)


def _compute_rating(team_stats):
    """Compute composite rating (0-100) from tournament stats."""
    p = team_stats['played']
    if p == 0:
        return 50.0

    # Win rate (0-1) — 3 pts/win, 1 pt/draw
    max_pts = p * 3
    pts = team_stats['wins'] * 3 + team_stats['draws'] * 1
    win_rate = pts / max_pts

    # Goal difference per game (-3 to +3 typical, normalize to 0-1)
    gd_pg = (team_stats['gf'] - team_stats['ga']) / p
    gd_norm = min(1.0, max(0.0, (gd_pg + 3) / 6))

    # Avg possession (30-70 typical, normalize to 0-1)
    avg_poss = team_stats['possession_sum'] / p
    poss_norm = min(1.0, max(0.0, (avg_poss - 30) / 40))

    # Shots on target per game (0-8 typical, normalize to 0-1)
    sot_pg = team_stats['sot_sum'] / p
    sot_norm = min(1.0, max(0.0, sot_pg / 8))

    # Clean sheet rate (0-1)
    cs_rate = team_stats['clean_sheets'] / p

    # Weighted composite
    rating = (
        win_rate * 35 +
        gd_norm * 20 +
        poss_norm * 15 +
        sot_norm * 15 +
        cs_rate * 15
    )
    return rating


def _get_cortex_reasoning(t1, t2, stats1, stats2):
    """Call Snowflake Cortex AI_COMPLETE for a one-sentence prediction."""
    try:
        from utils.snowflake_conn import run_query

        p1, p2 = stats1['played'], stats2['played']
        summary = (
            f"{t1}: {p1} played, {stats1['wins']}W {stats1['draws']}D {stats1['losses']}L, "
            f"{stats1['gf']} goals scored, {stats1['ga']} conceded, "
            f"avg possession {stats1['possession_sum']/max(1,p1):.0f}%, "
            f"{stats1['sot_sum']/max(1,p1):.1f} shots on target/game, "
            f"{stats1['clean_sheets']} clean sheets. "
            f"Beat: {', '.join(stats1['opponents_beaten'][:5]) or 'none'}.\n"
            f"{t2}: {p2} played, {stats2['wins']}W {stats2['draws']}D {stats2['losses']}L, "
            f"{stats2['gf']} goals scored, {stats2['ga']} conceded, "
            f"avg possession {stats2['possession_sum']/max(1,p2):.0f}%, "
            f"{stats2['sot_sum']/max(1,p2):.1f} shots on target/game, "
            f"{stats2['clean_sheets']} clean sheets. "
            f"Beat: {', '.join(stats2['opponents_beaten'][:5]) or 'none'}."
        )

        prompt = (
            f"Based on these FIFA World Cup 2026 tournament stats, predict the winner "
            f"of {t1} vs {t2} in exactly one short sentence (max 15 words). "
            f"Focus on the key differentiator.\n\n{summary}"
        )

        # Escape single quotes in prompt for SQL
        prompt_escaped = prompt.replace("'", "''")
        query = f"SELECT SNOWFLAKE.CORTEX.AI_COMPLETE('mistral-large2', '{prompt_escaped}') AS prediction"
        df = run_query(query)
        if df is not None and len(df) > 0:
            result = str(df.iloc[0, 0]).strip().strip('"').strip()
            # Truncate if too long
            if len(result) > 80:
                result = result[:77] + "..."
            return result
    except Exception:
        pass
    return ""


@st.cache_data(ttl=300)
def get_predictions(_results_hash, unplayed_matchups):
    """Get predictions for unplayed matchups.

    _results_hash is used for cache invalidation (changes when new results come in).
    unplayed_matchups: tuple of (team1, team2) tuples.
    Returns dict: "team1|team2" → {"favored": str, "pct": int, "reasoning": str}
    """
    from utils.football_api import get_all_results
    results = get_all_results()
    all_stats = _aggregate_team_stats(results)
    predictions = {}

    for t1, t2 in unplayed_matchups:
        if t1 == "TBD" or t2 == "TBD":
            continue
        s1 = all_stats.get(t1)
        s2 = all_stats.get(t2)
        if not s1 or not s2:
            continue

        r1 = _compute_rating(s1)
        r2 = _compute_rating(s2)
        total = r1 + r2
        if total == 0:
            continue

        pct1 = round(r1 / total * 100)
        pct2 = 100 - pct1

        if pct1 >= pct2:
            favored, pct = t1, pct1
        else:
            favored, pct = t2, pct2

        # Get AI reasoning
        reasoning = _get_cortex_reasoning(t1, t2, s1, s2)

        predictions[f"{t1}|{t2}"] = {
            "favored": favored,
            "pct": pct,
            "reasoning": reasoning,
        }

    return predictions


def live_win_probability(match):
    """Compute live win probability from in-match stats.

    Returns {"team1_pct": int, "team2_pct": int, "draw_pct": int, "favored": str, "reasoning": str}
    """
    t1, t2 = match["team_1_name"], match["team_2_name"]
    s1, s2 = match["team_1_score"], match["team_2_score"]
    stats1 = match.get("team_1_stats") or {}
    stats2 = match.get("team_2_stats") or {}
    events = match.get("match_events", [])

    # Base probability from score (dominant factor)
    goal_diff = s1 - s2
    # Sigmoid-like mapping: 0 diff = 50/50, each goal shifts ~18-20 points
    if goal_diff == 0:
        base1, base2 = 35, 35  # leaves 30% draw
    elif goal_diff > 0:
        shift = min(40, goal_diff * 18)
        base1 = 50 + shift
        base2 = max(5, 50 - shift - 15)
    else:
        shift = min(40, abs(goal_diff) * 18)
        base2 = 50 + shift
        base1 = max(5, 50 - shift - 15)

    # Time factor — later in match, score matters more (compress toward result)
    clock = match.get("clock_seconds", 0) or 0
    # Estimate minute (clock_seconds is within current period)
    period = match.get("period", 1) or 1
    minute = min(90, clock // 60 + (45 if period >= 2 else 0))
    time_factor = minute / 90  # 0 at start, 1 at 90'

    # Possession advantage (0-10 points swing)
    poss1 = stats1.get("possession", 50)
    poss2 = stats2.get("possession", 50)
    poss_adj = (poss1 - poss2) / 10  # ±5 points max

    # Shots on target advantage (0-8 points swing)
    sot1 = stats1.get("shots_on_target", 0)
    sot2 = stats2.get("shots_on_target", 0)
    sot_adj = min(8, max(-8, (sot1 - sot2) * 2))

    # Red cards (huge swing: -15 points per red card)
    red1 = sum(1 for e in events if e.get("type") == "red" and e.get("side") == 1)
    red2 = sum(1 for e in events if e.get("type") == "red" and e.get("side") == 2)
    red_adj = (red2 - red1) * 15  # positive = advantage to team1

    # Combine: base + adjustments scaled by inverse time (early = more uncertain)
    uncertainty = 1 - time_factor * 0.6  # adjustments matter less late in game when score dominates
    adj1 = (poss_adj + sot_adj + red_adj) * uncertainty

    raw1 = base1 + adj1
    raw2 = base2 - adj1

    # Normalize to 100
    draw_base = max(5, 30 - abs(goal_diff) * 12 - time_factor * 15)
    total = raw1 + raw2 + draw_base
    pct1 = max(2, round(raw1 / total * 100))
    pct2 = max(2, round(raw2 / total * 100))
    draw_pct = 100 - pct1 - pct2

    favored = t1 if pct1 >= pct2 else t2

    # Get AI reasoning (cached 60s separately)
    reasoning = _get_live_reasoning(t1, t2, s1, s2, stats1, stats2, events, minute)

    return {
        "team1_pct": pct1,
        "team2_pct": pct2,
        "draw_pct": max(0, draw_pct),
        "favored": favored,
        "reasoning": reasoning,
    }


@st.cache_data(ttl=60)
def _get_live_reasoning(t1, t2, s1, s2, stats1, stats2, _events_hash, minute):
    """Cortex AI reasoning for live match — cached 60s."""
    try:
        from utils.snowflake_conn import run_query

        events_summary = ""
        if isinstance(_events_hash, list):
            goals = [e for e in _events_hash if e.get("type") in ("goal", "own_goal")]
            reds = [e for e in _events_hash if e.get("type") == "red"]
            if goals:
                events_summary = "Goals: " + ", ".join(f'{e["player"]} {e["minute"]}' for e in goals) + ". "
            if reds:
                events_summary += "Red cards: " + ", ".join(f'{e["player"]} {e["minute"]}' for e in reds) + ". "

        prompt = (
            f"FIFA World Cup 2026 LIVE match at minute {minute}: "
            f"{t1} {s1} - {s2} {t2}. "
            f"{t1}: {stats1.get('possession', 50):.0f}% possession, {stats1.get('shots_on_target', 0)} shots on target. "
            f"{t2}: {stats2.get('possession', 50):.0f}% possession, {stats2.get('shots_on_target', 0)} shots on target. "
            f"{events_summary}"
            f"In exactly one sentence (max 12 words), describe who is more likely to win and why."
        )

        prompt_escaped = prompt.replace("'", "''")
        query = f"SELECT SNOWFLAKE.CORTEX.AI_COMPLETE('mistral-large2', '{prompt_escaped}') AS prediction"
        df = run_query(query)
        if df is not None and len(df) > 0:
            result = str(df.iloc[0, 0]).strip().strip('"').strip()
            if len(result) > 80:
                result = result[:77] + "..."
            return result
    except Exception:
        pass
    return ""
