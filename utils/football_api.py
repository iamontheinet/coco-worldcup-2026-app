import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz


ESPN_API = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"


def _get_date_range():
    """Return a 3-day date range (yesterday-tomorrow ET) to catch midnight-boundary matches."""
    et = pytz.timezone("US/Eastern")
    now_et = datetime.now(et)
    yesterday = (now_et - timedelta(days=1)).strftime("%Y%m%d")
    tomorrow = (now_et + timedelta(days=1)).strftime("%Y%m%d")
    return f"{yesterday}-{tomorrow}"


@st.cache_data(ttl=15)
def get_live_matches():
    """Fetch currently live World Cup matches from ESPN API."""
    date_range = _get_date_range()
    for _attempt in range(3):
        try:
            resp = requests.get(ESPN_API, params={"dates": date_range}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            matches = []
            for event in data.get("events", []):
                comp = event.get("competitions", [{}])[0]
                status = comp.get("status", {}).get("type", {})
                status_name = status.get("name", "")
                # Only return in-progress matches
                if status_name in (
                    "STATUS_FIRST_HALF", "STATUS_SECOND_HALF",
                    "STATUS_HALFTIME", "STATUS_EXTRA_TIME",
                    "STATUS_PENALTY_SHOOTOUT", "STATUS_IN_PROGRESS",
                ):
                    matches.append(_normalize_espn(event, comp, status))
            return matches
        except Exception:
            continue
    return []


@st.cache_data(ttl=30)
def get_todays_matches():
    """Fetch today's World Cup matches (3-day window to avoid boundary issues)."""
    date_range = _get_date_range()
    try:
        resp = requests.get(ESPN_API, params={"dates": date_range}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        matches = []
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            status = comp.get("status", {}).get("type", {})
            matches.append(_normalize_espn(event, comp, status))
        return matches
    except Exception:
        return []


def _normalize_espn(event, competition, status):
    """Normalize ESPN competition data into a clean dict."""
    competitors = competition.get("competitors", [])
    home = next((c for c in competitors if c.get("homeAway") == "home"), {})
    away = next((c for c in competitors if c.get("homeAway") == "away"), {})

    status_name = status.get("name", "")
    detail = status.get("detail", "")

    # Match clock (seconds elapsed in current period)
    full_status = competition.get("status", {})
    clock_seconds = full_status.get("clock", 0)
    period = full_status.get("period", 1)

    # Map ESPN status to our status
    if status_name in ("STATUS_FIRST_HALF", "STATUS_SECOND_HALF", "STATUS_EXTRA_TIME", "STATUS_PENALTY_SHOOTOUT", "STATUS_IN_PROGRESS"):
        mapped_status = "IN_PLAY"
    elif status_name == "STATUS_HALFTIME":
        mapped_status = "HALFTIME"
    elif status_name == "STATUS_FULL_TIME":
        mapped_status = "FINISHED"
    elif status_name == "STATUS_SCHEDULED":
        mapped_status = "SCHEDULED"
    else:
        mapped_status = status_name

    # Parse event date for display
    event_date = event.get("date", "")
    date_display = ""
    time_et_display = ""
    utc_iso = ""
    if event_date:
        from datetime import datetime, timedelta
        from pytz import timezone as pytz_tz
        try:
            utc_dt = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
            utc_iso = utc_dt.isoformat()
            et_tz = pytz_tz("US/Eastern")
            et_dt = utc_dt.astimezone(et_tz)
            date_display = et_dt.strftime("%b %d, %Y")
            time_et_display = et_dt.strftime("%-I:%M %p ET")
        except Exception:
            date_display = ""
            time_et_display = ""

    # Extract per-team stats
    def _extract_stats(competitor):
        stats = {}
        for s in competitor.get("statistics", []):
            stats[s["name"]] = s.get("displayValue", "0")
        return {
            "possession": float(stats.get("possessionPct", 0)),
            "shots": int(stats.get("totalShots", 0)),
            "shots_on_target": int(stats.get("shotsOnTarget", 0)),
            "corners": int(stats.get("wonCorners", 0)),
            "fouls": int(stats.get("foulsCommitted", 0)),
        }

    team_1_stats = _extract_stats(home)
    team_2_stats = _extract_stats(away)

    # Extract match events (goals, cards)
    match_events = []
    for d in competition.get("details", []):
        event_type = d.get("type", {}).get("text", "")
        clock_val = d.get("clock", {}).get("displayValue", "")
        players = [a.get("shortName", "") for a in d.get("athletesInvolved", [])]
        is_goal = d.get("scoringPlay", False)
        is_yellow = d.get("yellowCard", False)
        is_red = d.get("redCard", False)
        is_own_goal = d.get("ownGoal", False)
        team_id = str(d.get("team", {}).get("id", ""))
        # Determine which team (1 or 2)
        home_id = str(home.get("team", {}).get("id", ""))
        side = 1 if team_id == home_id else 2
        if is_goal or is_yellow or is_red:
            match_events.append({
                "minute": clock_val,
                "type": "own_goal" if is_own_goal else "goal" if is_goal else "red" if is_red else "yellow",
                "player": players[0] if players else "",
                "side": side,
            })

    # Determine winner (handles penalties/extra time via ESPN's winner flag)
    home_name = home.get("team", {}).get("displayName", "TBD")
    away_name = away.get("team", {}).get("displayName", "TBD")
    if home.get("winner"):
        match_winner = home_name
    elif away.get("winner"):
        match_winner = away_name
    else:
        match_winner = None

    return {
        "status": mapped_status,
        "detail": detail,
        "date": date_display,
        "time_et": time_et_display,
        "utc_iso": utc_iso,
        "team_1_name": home_name,
        "team_1_short": home.get("team", {}).get("abbreviation", ""),
        "team_1_logo": home.get("team", {}).get("logo", ""),
        "team_1_score": int(home.get("score", 0)),
        "team_2_name": away_name,
        "team_2_short": away.get("team", {}).get("abbreviation", ""),
        "team_2_logo": away.get("team", {}).get("logo", ""),
        "team_2_score": int(away.get("score", 0)),
        "winner": match_winner,
        "stage": competition.get("type", {}).get("text", "Group Stage"),
        "venue": competition.get("venue", {}).get("fullName", ""),
        "city": competition.get("venue", {}).get("address", {}).get("city", ""),
        "clock_seconds": int(clock_seconds) if clock_seconds else 0,
        "period": period,
        "display_clock": full_status.get("displayClock", ""),
        "team_1_stats": team_1_stats,
        "team_2_stats": team_2_stats,
        "match_events": match_events,
    }


@st.cache_data(ttl=60)
def get_upcoming_matches():
    """Fetch upcoming scheduled World Cup matches from ESPN API.

    Uses a rolling window: today+6 days to reliably capture near-term matches,
    then extends to tournament end if needed.
    """
    et = pytz.timezone("US/Eastern")
    now_et = datetime.now(et)
    today = now_et.strftime("%Y%m%d")
    # Query today through 6 days out (ESPN reliably returns this window)
    end = (now_et + timedelta(days=6)).strftime("%Y%m%d")
    try:
        resp = requests.get(
            ESPN_API,
            params={"dates": f"{today}-{end}"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        upcoming = []
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            status = comp.get("status", {}).get("type", {})
            if status.get("name") == "STATUS_SCHEDULED":
                upcoming.append(_normalize_espn(event, comp, status))
        return upcoming
    except Exception:
        return []


@st.cache_data(ttl=60)
def get_all_results():
    """Fetch all finished World Cup matches from ESPN API.

    Queries from tournament start to today to keep the response size manageable.
    """
    et = pytz.timezone("US/Eastern")
    today = datetime.now(et).strftime("%Y%m%d")
    try:
        resp = requests.get(
            ESPN_API,
            params={"dates": f"20260611-{today}"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = []
        for event in data.get("events", []):
            comp = event.get("competitions", [{}])[0]
            status = comp.get("status", {}).get("type", {})
            if status.get("name") == "STATUS_FULL_TIME":
                results.append(_normalize_espn(event, comp, status))
        return results
    except Exception:
        return []
