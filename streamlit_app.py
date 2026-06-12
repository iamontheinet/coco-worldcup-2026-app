import streamlit as st

st.set_page_config(
    page_title="World Cup 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

with open("app.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Navigation
home_page = st.Page("pages/0_home.py", title="Home", icon="⚽", default=True)
venue_map_page = st.Page("pages/1_🗺️_Venue_Map.py", title="Venue Map", icon="🗺️")
head_to_head_page = st.Page("pages/2_⚔️_Head_to_Head.py", title="Head to Head", icon="⚔️")
group_simulator_page = st.Page("pages/3_📊_Group_Simulator.py", title="Group Simulator", icon="📊")
bracket_builder_page = st.Page("pages/4_🏆_Bracket_Builder.py", title="Bracket Builder", icon="🏆")
quiz_page = st.Page("pages/5_🧠_Quiz.py", title="Quiz", icon="🧠")

pg = st.navigation([
    home_page,
    venue_map_page,
    head_to_head_page,
    group_simulator_page,
    bracket_builder_page,
    quiz_page,
])

pg.run()
