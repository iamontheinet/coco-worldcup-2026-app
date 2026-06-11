import streamlit as st

st.set_page_config(
    page_title="FIFA World Cup 2026 Explorer",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #29B5E8, #FFD700, #FF4B4B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0;
    }
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #888;
        margin-top: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-title">⚽ FIFA World Cup 2026</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">United States 🇺🇸 • Mexico 🇲🇽 • Canada 🇨🇦</p>',
    unsafe_allow_html=True,
)

st.markdown("---")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Teams", "48")
with col2:
    st.metric("Venues", "16")
with col3:
    st.metric("Matches", "104")
with col4:
    st.metric("Host Countries", "3")
with col5:
    st.metric("Duration", "39 Days")

st.markdown("---")

st.markdown(
    """
### Welcome to the World Cup 2026 Interactive Explorer!

Navigate using the sidebar to explore:

- 🗺️ **Venue Map** — Interactive 3D globe showing all 16 stadiums
- ⚔️ **Head to Head** — Compare any two teams with radar charts
- 📊 **Group Simulator** — Predict results and see who advances
- 🏆 **Bracket Builder** — Build your knockout bracket to the Final
- 📈 **Stats & Trivia** — Historical records and fun facts

---
*Data powered by Snowflake ❄️ • Built with Streamlit*
"""
)
