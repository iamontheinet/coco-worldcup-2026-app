import streamlit as st
import pydeck as pdk
import pandas as pd
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.data_loader import load_venues, load_matches

st.set_page_config(page_title="Venue Map", page_icon="🗺️", layout="wide")
st.title("🗺️ World Cup 2026 Venue Map")

venues = load_venues()
matches = load_matches()

COUNTRY_COLORS = {
    "United States": [41, 181, 232, 200],
    "Mexico": [0, 200, 83, 200],
    "Canada": [255, 75, 75, 200],
}

venues["color"] = venues["COUNTRY"].map(lambda c: COUNTRY_COLORS.get(c, [255, 255, 255, 200]))

col1, col2 = st.columns([3, 1])

with col1:
    view_state = pdk.ViewState(
        latitude=37.0,
        longitude=-95.0,
        zoom=3,
        pitch=45,
    )

    column_layer = pdk.Layer(
        "ColumnLayer",
        data=venues,
        get_position=["LONGITUDE", "LATITUDE"],
        get_elevation="CAPACITY",
        elevation_scale=0.5,
        radius=25000,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
    )

    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=venues,
        get_position=["LONGITUDE", "LATITUDE"],
        get_radius=20000,
        get_fill_color="color",
        pickable=True,
    )

    tooltip = {
        "html": "<b>{VENUE_NAME}</b><br/>{CITY}, {COUNTRY}<br/>Capacity: {CAPACITY:,}<br/>Hosting: {HOSTING_ROLE}",
        "style": {"backgroundColor": "#1A1F2B", "color": "#FAFAFA", "fontSize": "13px"},
    }

    deck = pdk.Deck(
        layers=[column_layer, scatter_layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/dark-v11",
    )

    st.pydeck_chart(deck)

with col2:
    st.markdown("### 🏟️ Stadiums")
    st.markdown("**Color Legend:**")
    st.markdown("- 🔵 United States (11)")
    st.markdown("- 🟢 Mexico (3)")
    st.markdown("- 🔴 Canada (2)")
    st.markdown("---")

    for _, v in venues.iterrows():
        st.markdown(f"**{v['VENUE_NAME']}**")
        st.caption(f"{v['CITY']} • {v['CAPACITY']:,} seats")


st.markdown("---")
st.subheader("📅 Matches by Venue")

selected_venue = st.selectbox(
    "Select a venue to see its match schedule:",
    venues["VENUE_NAME"].tolist(),
)

venue_id = venues[venues["VENUE_NAME"] == selected_venue]["VENUE_ID"].iloc[0]
venue_matches = matches[matches["VENUE_ID"] == venue_id]

if not venue_matches.empty:
    for _, m in venue_matches.iterrows():
        st.markdown(
            f"**{m['MATCH_DATE']}** {m['MATCH_TIME_ET']} — "
            f"{m['TEAM_1_FLAG']} {m['TEAM_1_NAME']} vs {m['TEAM_2_NAME']} {m['TEAM_2_FLAG']} "
            f"({m['STAGE']})"
        )
else:
    st.info("No group stage matches scheduled at this venue (may host knockout rounds).")
