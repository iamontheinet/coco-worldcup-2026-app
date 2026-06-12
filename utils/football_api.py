import streamlit as st
import requests


ESPN_API = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"


@st.cache_data(ttl=15)
def get_live_matches():
    """Fetch currently live World Cup matches from ESPN API."""
    try:
        resp = requests.get(ESPN_API, timeout=5)
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
                "STATUS_PENALTY_SHOOTOUT",
            ):
                matches.append(_normalize_espn(event, comp, status))
        return matches
    except Exception:
        return []


@st.cache_data(ttl=30)
def get_todays_matches():
    """Fetch all of today's World Cup matches from ESPN API."""
    try:
        resp = requests.get(ESPN_API, timeout=5)
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

    # Map ESPN status to our status
    if status_name in ("STATUS_FIRST_HALF", "STATUS_SECOND_HALF", "STATUS_EXTRA_TIME", "STATUS_PENALTY_SHOOTOUT"):
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
    if event_date:
        from datetime import datetime, timedelta
        try:
            utc_dt = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
            et_dt = utc_dt - timedelta(hours=4)
            date_display = et_dt.strftime("%b %d, %Y")
            time_et_display = et_dt.strftime("%-I:%M %p ET")
        except Exception:
            date_display = ""
            time_et_display = ""

    return {
        "status": mapped_status,
        "detail": detail,
        "date": date_display,
        "time_et": time_et_display,
        "team_1_name": home.get("team", {}).get("displayName", "TBD"),
        "team_1_short": home.get("team", {}).get("abbreviation", ""),
        "team_1_logo": home.get("team", {}).get("logo", ""),
        "team_1_score": int(home.get("score", 0)),
        "team_2_name": away.get("team", {}).get("displayName", "TBD"),
        "team_2_short": away.get("team", {}).get("abbreviation", ""),
        "team_2_logo": away.get("team", {}).get("logo", ""),
        "team_2_score": int(away.get("score", 0)),
        "stage": "Group Stage",
        "venue": competition.get("venue", {}).get("fullName", ""),
        "city": competition.get("venue", {}).get("address", {}).get("city", ""),
    }


@st.cache_data(ttl=60)
def get_all_results():
    """Fetch all finished World Cup matches from ESPN API."""
    try:
        resp = requests.get(
            ESPN_API,
            params={"dates": "20260611-20260719"},
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
