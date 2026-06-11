import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import random
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.data_loader import load_historical_stats, load_teams

st.set_page_config(page_title="Stats & Trivia", page_icon="📈", layout="wide")
st.title("📈 Stats & Trivia Corner")

stats = load_historical_stats()
teams = load_teams()

# Random trivia generator
st.subheader("🎲 Did You Know?")

if st.button("🔀 Random Trivia", type="primary"):
    st.session_state["trivia_idx"] = random.randint(0, len(stats) - 1)

if "trivia_idx" not in st.session_state:
    st.session_state["trivia_idx"] = 0

trivia = stats.iloc[st.session_state["trivia_idx"]]
st.info(f"**{trivia['CATEGORY']}**\n\n{trivia['STAT_VALUE']} ({trivia['YEAR']})")

st.markdown("---")

# World Cup titles chart
st.subheader("🏆 World Cup Titles by Country")

titles_data = pd.DataFrame({
    "Country": ["Brazil", "Germany", "Italy", "Argentina", "France", "Uruguay", "England", "Spain"],
    "Titles": [5, 4, 4, 3, 2, 2, 1, 1],
    "Years": [
        "1958, 62, 70, 94, 02",
        "1954, 74, 90, 2014",
        "1934, 38, 82, 2006",
        "1978, 86, 2022",
        "1998, 2018",
        "1930, 1950",
        "1966",
        "2010",
    ],
})

fig = px.bar(
    titles_data,
    x="Country",
    y="Titles",
    color="Titles",
    color_continuous_scale=["#29B5E8", "#FFD700"],
    text="Titles",
    hover_data=["Years"],
)
fig.update_layout(
    paper_bgcolor="#0E1117",
    plot_bgcolor="#1A1F2B",
    font=dict(color="#FAFAFA"),
    showlegend=False,
    coloraxis_showscale=False,
)
fig.update_traces(textposition="outside")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Goals per tournament trend
st.subheader("⚽ Goals Per Tournament (Historical Trend)")

goals_data = pd.DataFrame({
    "Year": [1930, 1934, 1938, 1950, 1954, 1958, 1962, 1966, 1970, 1974,
             1978, 1982, 1986, 1990, 1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022],
    "Total Goals": [70, 70, 84, 88, 140, 126, 89, 89, 95, 97,
                    102, 146, 132, 115, 141, 171, 161, 147, 145, 171, 169, 172],
    "Matches": [18, 17, 18, 22, 26, 35, 32, 32, 32, 38,
                38, 52, 52, 52, 52, 64, 64, 64, 64, 64, 64, 64],
})
goals_data["Goals per Match"] = (goals_data["Total Goals"] / goals_data["Matches"]).round(2)

fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=goals_data["Year"],
    y=goals_data["Goals per Match"],
    mode="lines+markers",
    line=dict(color="#29B5E8", width=3),
    marker=dict(size=8),
    name="Goals per Match",
))
fig2.update_layout(
    paper_bgcolor="#0E1117",
    plot_bgcolor="#1A1F2B",
    font=dict(color="#FAFAFA"),
    xaxis_title="Tournament Year",
    yaxis_title="Goals per Match",
    height=400,
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# Team stats from 2026 data
st.subheader("📊 2026 Team Stats")

tab1, tab2, tab3 = st.tabs(["By Squad Value", "By FIFA Ranking", "By Qualifier Goals"])

with tab1:
    top_value = teams.nlargest(10, "SQUAD_VALUE_M")
    fig3 = px.bar(
        top_value,
        x="TEAM_NAME",
        y="SQUAD_VALUE_M",
        color="CONFEDERATION",
        text="SQUAD_VALUE_M",
        labels={"SQUAD_VALUE_M": "Squad Value ($M)", "TEAM_NAME": ""},
    )
    fig3.update_layout(paper_bgcolor="#0E1117", plot_bgcolor="#1A1F2B", font=dict(color="#FAFAFA"))
    fig3.update_traces(texttemplate="$%{text:.0f}M", textposition="outside")
    st.plotly_chart(fig3, use_container_width=True)

with tab2:
    top_ranked = teams.nsmallest(15, "FIFA_RANKING")
    fig4 = px.bar(
        top_ranked,
        x="TEAM_NAME",
        y="FIFA_RANKING",
        color="CONFEDERATION",
        text="FIFA_RANKING",
        labels={"FIFA_RANKING": "FIFA Ranking", "TEAM_NAME": ""},
    )
    fig4.update_layout(
        paper_bgcolor="#0E1117", plot_bgcolor="#1A1F2B", font=dict(color="#FAFAFA"),
        yaxis=dict(autorange="reversed"),
    )
    fig4.update_traces(textposition="outside")
    st.plotly_chart(fig4, use_container_width=True)

with tab3:
    top_goals = teams.nlargest(15, "QUALIFIER_GOALS")
    fig5 = px.bar(
        top_goals,
        x="TEAM_NAME",
        y="QUALIFIER_GOALS",
        color="CONFEDERATION",
        text="QUALIFIER_GOALS",
        labels={"QUALIFIER_GOALS": "Goals in Qualifiers", "TEAM_NAME": ""},
    )
    fig5.update_layout(paper_bgcolor="#0E1117", plot_bgcolor="#1A1F2B", font=dict(color="#FAFAFA"))
    fig5.update_traces(textposition="outside")
    st.plotly_chart(fig5, use_container_width=True)

st.markdown("---")

# All historical records
st.subheader("📖 All Historical Records")
for _, row in stats.iterrows():
    with st.expander(f"**{row['CATEGORY']}** ({row['YEAR']})"):
        st.write(row["STAT_VALUE"])
        if row["TEAM_NAME"]:
            st.caption(f"Team: {row['TEAM_NAME']}")
