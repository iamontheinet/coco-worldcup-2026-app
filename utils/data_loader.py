from utils.snowflake_conn import run_query
import streamlit as st
import pandas as pd


@st.cache_data(ttl=300)
def load_teams():
    return run_query("SELECT * FROM TEAMS ORDER BY GROUP_LETTER, TEAM_NAME")


@st.cache_data(ttl=300)
def load_venues():
    return run_query("SELECT * FROM VENUES ORDER BY VENUE_ID")


@st.cache_data(ttl=300)
def load_matches():
    return run_query("""
        SELECT m.*, 
               t1.TEAM_NAME as TEAM_1_NAME, t1.FLAG_EMOJI as TEAM_1_FLAG,
               t2.TEAM_NAME as TEAM_2_NAME, t2.FLAG_EMOJI as TEAM_2_FLAG,
               v.VENUE_NAME, v.CITY
        FROM MATCHES m
        JOIN TEAMS t1 ON m.TEAM_1_ID = t1.TEAM_ID
        JOIN TEAMS t2 ON m.TEAM_2_ID = t2.TEAM_ID
        JOIN VENUES v ON m.VENUE_ID = v.VENUE_ID
        ORDER BY m.MATCH_DATE, m.MATCH_TIME_ET
    """)


@st.cache_data(ttl=300)
def load_historical_stats():
    return run_query("SELECT * FROM HISTORICAL_STATS ORDER BY STAT_ID")
