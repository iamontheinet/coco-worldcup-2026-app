import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import date as date_today
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.data_loader import load_venues, load_matches
from utils.football_api import get_all_results
from utils.banner import render_tournament_banner
from utils.footer import render_footer

render_tournament_banner()
st.markdown('<h2 style="text-align:center; margin:0.3rem 0;">🗺️ World Cup 2026 Venue Map</h2>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; font-size:0.75rem; color:#ffffff; margin-top:-0.3rem; text-transform:uppercase; letter-spacing:2px;">Click a marker to see the scheduled matches at that venue.</p>', unsafe_allow_html=True)

venues = load_venues()
matches = load_matches()

COUNTRY_COLORS = {
    "United States": "blue",
    "Mexico": "green",
    "Canada": "red",
}

m = folium.Map(
    location=[37.0, -95.0],
    zoom_start=4,
    tiles="CartoDB Positron",
)

for _, v in venues.iterrows():
    color = COUNTRY_COLORS.get(v["COUNTRY"], "gray")
    popup_html = (
        f'<div style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica Neue,Arial,sans-serif;font-size:14px;">'
        f"<b>{v['VENUE_NAME']}</b><br>"
        f"{v['CITY']}, {v['COUNTRY']}<br>"
        f"Capacity: {v['CAPACITY']:,}"
        f"</div>"
    )
    folium.Marker(
        location=[v["LATITUDE"], v["LONGITUDE"]],
        popup=folium.Popup(popup_html, max_width=250),
        tooltip=v["VENUE_NAME"],
        icon=folium.Icon(color=color, icon="futbol", prefix="fa"),
    ).add_to(m)

map_data = st_folium(m, width=None, height=500, returned_objects=["last_object_clicked"])

st.markdown(
    '<p style="text-align:center; font-size:0.95rem; margin-top:0.5rem;">'
    '🔵 United States (11) &nbsp;&nbsp;|&nbsp;&nbsp; 🟢 Mexico (3) &nbsp;&nbsp;|&nbsp;&nbsp; 🔴 Canada (2)'
    '</p>',
    unsafe_allow_html=True,
)

if map_data and map_data.get("last_object_clicked"):
    clicked = map_data["last_object_clicked"]
    clicked_lat = clicked.get("lat")
    clicked_lng = clicked.get("lng")

    if clicked_lat and clicked_lng:
        venues["_dist"] = (
            (venues["LATITUDE"] - clicked_lat) ** 2
            + (venues["LONGITUDE"] - clicked_lng) ** 2
        )
        closest = venues.loc[venues["_dist"].idxmin()]
        venues.drop(columns=["_dist"], inplace=True)

        st.markdown("---")
        st.markdown(
            f'<h3 style="text-align:center;">{closest["VENUE_NAME"]} — {closest["CITY"]}, {closest["COUNTRY"]}</h3>'
            f'<p style="text-align:center; font-weight:700;">Capacity: {closest["CAPACITY"]:,} seats</p>',
            unsafe_allow_html=True,
        )

        venue_matches = matches[matches["VENUE_ID"] == closest["VENUE_ID"]]

        _results = get_all_results()
        _finished_teams = set()
        for r in _results:
            _finished_teams.add((r["team_1_name"], r["team_2_name"]))
            _finished_teams.add((r["team_2_name"], r["team_1_name"]))

        if not venue_matches.empty:
            past = []
            upcoming = []
            for _, match in venue_matches.iterrows():
                pair = (match["TEAM_1_NAME"], match["TEAM_2_NAME"])
                if pair in _finished_teams:
                    past.append(match)
                else:
                    upcoming.append(match)

            if upcoming:
                st.markdown('<h3 style="text-align:center; color:rgb(17,86,117);">Upcoming Matches</h3>', unsafe_allow_html=True)
                for match in upcoming:
                    date_str = match["MATCH_DATE"]
                    if hasattr(date_str, "strftime"):
                        date_str = date_str.strftime("%b %d, %Y")
                    time_str = str(match["MATCH_TIME_ET"]) if match["MATCH_TIME_ET"] else ""

                    st.markdown(
                        f'<div style="background:rgba(17,86,117,0.3); border-radius:14px; padding:0.8rem 1.5rem; margin:0.4rem auto; max-width:600px; border:1px solid rgba(41,181,232,0.2);">'
                        f'<div style="display:flex; justify-content:center; align-items:center; gap:0.8rem;">'
                        f'<span style="font-size:1rem; font-weight:700; color:#fff;">{match["TEAM_1_FLAG"]} {match["TEAM_1_NAME"]}</span>'
                        f'<span style="font-size:0.9rem; font-weight:700; color:#e0e0e0;">vs</span>'
                        f'<span style="font-size:1rem; font-weight:700; color:#fff;">{match["TEAM_2_FLAG"]} {match["TEAM_2_NAME"]}</span>'
                        f'</div>'
                        f'<p style="text-align:center; font-size:0.75rem; color:#e0e0e0; margin:0.2rem 0 0 0;">{date_str} at {time_str} ET &nbsp;|&nbsp; {match["STAGE"]}</p>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            if past:
                st.markdown('<h3 style="text-align:center; color:rgb(17,86,117);">Results</h3>', unsafe_allow_html=True)
                _results_lookup = {}
                for r in _results:
                    _results_lookup[(r["team_1_name"], r["team_2_name"])] = r

                for match in past:
                    result = _results_lookup.get((match["TEAM_1_NAME"], match["TEAM_2_NAME"]))
                    if not result:
                        result = _results_lookup.get((match["TEAM_2_NAME"], match["TEAM_1_NAME"]))

                    date_str = match["MATCH_DATE"]
                    if hasattr(date_str, "strftime"):
                        date_str = date_str.strftime("%b %d, %Y")

                    if result:
                        score_display = f'{result["team_1_score"]} – {result["team_2_score"]}'
                        t1 = result["team_1_name"]
                        t2 = result["team_2_name"]
                        _goals = [e for e in result.get("match_events", []) if e["type"] in ("goal", "own_goal")]
                        _scorers_html = ""
                        if _goals:
                            _parts = [f'⚽ <img src="{result["team_1_logo"] if g["side"] == 1 else result["team_2_logo"]}" style="height:0.65rem; vertical-align:middle;"> {g["player"]}{" (OG)" if g["type"] == "own_goal" else ""} {g["minute"]}' for g in _goals]
                            _scorers_html = f'<p style="text-align:center; font-size:0.7rem; color:#e0e0e0; margin:0.2rem 0 0 0;">{" • ".join(_parts)}</p>'
                    else:
                        score_display = "vs"
                        t1 = match["TEAM_1_NAME"]
                        t2 = match["TEAM_2_NAME"]
                        _scorers_html = ""

                    st.markdown(
                        f'<div style="background:rgba(17,86,117,0.3); border-radius:14px; padding:0.8rem 1.5rem; margin:0.4rem auto; max-width:600px; border:1px solid rgba(41,181,232,0.2);">'
                        f'<div style="display:flex; justify-content:center; align-items:center; gap:0.8rem;">'
                        f'<span style="font-size:1rem; font-weight:700; color:#fff;">{match["TEAM_1_FLAG"]} {t1}</span>'
                        f'<span style="font-size:1.5rem; font-weight:900; color:#FFD700;">{score_display}</span>'
                        f'<span style="font-size:1rem; font-weight:700; color:#fff;">{match["TEAM_2_FLAG"]} {t2}</span>'
                        f'</div>'
                        f'{_scorers_html}'
                        f'<p style="text-align:center; font-size:0.75rem; color:#e0e0e0; margin:0.2rem 0 0 0;">{date_str} &nbsp;|&nbsp; {match["STAGE"]}</p>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            if not past and not upcoming:
                st.info("No group stage matches scheduled at this venue (may host knockout rounds).")
        else:
            st.info("No group stage matches scheduled at this venue (may host knockout rounds).")

render_footer()
