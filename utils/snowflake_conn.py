import streamlit as st
import snowflake.connector
import pandas as pd


@st.cache_data(ttl=120)
def run_query(query):
    conn = snowflake.connector.connect(
        account=st.secrets["snowflake"]["account"],
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
    )
    try:
        return pd.read_sql(query, conn)
    finally:
        conn.close()
