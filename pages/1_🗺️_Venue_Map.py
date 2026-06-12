import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import date as date_today
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.data_loader import load_venues, load_matches
from utils.football_api import get_all_results
from utils.footer import render_footer

st.title("🗺️ World Cup 2026 Venue Map")

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
    tiles="CartoDB dark_matter",
)

for _, v in venues.iterrows():
    color = COUNTRY_COLORS.get(v["COUNTRY"], "gray")
    popup_html = (
        f"<b>{v['VENUE_NAME']}</b><br>"
        f"{v['CITY']}, {v['COUNTRY']}<br>"
        f"Capacity: {v['CAPACITY']:,}"
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
    '&nbsp;&nbsp;|&nbsp;&nbsp; Click a marker to see matches'
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
                st.markdown('<h3 style="text-align:center;">Upcoming Matches</h3>', unsafe_allow_html=True)
                for match in upcoming:
                    date_str = match["MATCH_DATE"]
                    if hasattr(date_str, "strftime"):
                        date_str = date_str.strftime("%b %d, %Y")
                    time_str = str(match["MATCH_TIME_ET"]) if match["MATCH_TIME_ET"] else ""

                    col_a, col_b, col_c = st.columns([2, 1, 2])
                    with col_a:
                        st.markdown(
                            f'<p style="font-size:1.6rem; font-weight:700; text-align:right; color:#FAFAFA; margin:0; white-space:nowrap;">'
                            f'{match["TEAM_1_FLAG"]} {match["TEAM_1_NAME"]}</p>',
                            unsafe_allow_html=True,
                        )
                    with col_b:
                        st.markdown(
                            '<p style="font-size:2rem; font-weight:800; text-align:center; color:#FAFAFA; margin:0; line-height:1;">vs</p>',
                            unsafe_allow_html=True,
                        )
                    with col_c:
                        st.markdown(
                            f'<p style="font-size:1.6rem; font-weight:700; text-align:left; color:#FAFAFA; margin:0; white-space:nowrap;">'
                            f'{match["TEAM_2_FLAG"]} {match["TEAM_2_NAME"]}</p>',
                            unsafe_allow_html=True,
                        )
                    st.markdown(
                        f'<p style="text-align:center; font-size:1rem; color:#ffffff; font-weight:700; margin-top:0.2rem;">'
                        f'{date_str} at {time_str} ET &nbsp;|&nbsp; {match["STAGE"]}</p>',
                        unsafe_allow_html=True,
                    )
                    st.markdown("")

            if past:
                st.markdown('<h3 style="text-align:center;">Past Matches</h3>', unsafe_allow_html=True)
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
                    else:
                        score_display = "vs"
                        t1 = match["TEAM_1_NAME"]
                        t2 = match["TEAM_2_NAME"]

                    col_a, col_b, col_c = st.columns([2, 1, 2])
                    with col_a:
                        st.markdown(
                            f'<p style="font-size:1.6rem; font-weight:700; text-align:right; color:#FAFAFA; margin:0; white-space:nowrap;">'
                            f'{match["TEAM_1_FLAG"]} {t1}</p>',
                            unsafe_allow_html=True,
                        )
                    with col_b:
                        st.markdown(
                            f'<p style="font-size:2rem; font-weight:800; text-align:center; color:#FAFAFA; margin:0; line-height:1;">{score_display}</p>',
                            unsafe_allow_html=True,
                        )
                    with col_c:
                        st.markdown(
                            f'<p style="font-size:1.6rem; font-weight:700; text-align:left; color:#FAFAFA; margin:0; white-space:nowrap;">'
                            f'{match["TEAM_2_FLAG"]} {t2}</p>',
                            unsafe_allow_html=True,
                        )
                    st.markdown(
                        f'<p style="text-align:center; font-size:0.9rem; color:#e0e0e0; margin-top:0.2rem;">'
                        f'{date_str} &nbsp;|&nbsp; {match["STAGE"]}</p>',
                        unsafe_allow_html=True,
                    )
                    st.markdown("")

            if not past and not upcoming:
                st.info("No group stage matches scheduled at this venue (may host knockout rounds).")
        else:
            st.info("No group stage matches scheduled at this venue (may host knockout rounds).")

render_footer()
