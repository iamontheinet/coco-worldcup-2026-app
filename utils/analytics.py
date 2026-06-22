import streamlit as st
import snowflake.connector
import uuid


def log_page_view(page_name: str):
    """Log a page view to Snowflake. Deduplicates per session+page."""
    if "_session_id" not in st.session_state:
        st.session_state["_session_id"] = str(uuid.uuid4())

    # Only log once per session per page
    key = f"_logged_{page_name}"
    if st.session_state.get(key):
        return
    st.session_state[key] = True

    try:
        conn = snowflake.connector.connect(
            account=st.secrets["snowflake"]["account"],
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database=st.secrets["snowflake"]["database"],
            schema=st.secrets["snowflake"]["schema"],
        )
        conn.cursor().execute(
            "INSERT INTO PAGE_VIEWS (SESSION_ID, PAGE_NAME) VALUES (%s, %s)",
            (st.session_state["_session_id"], page_name),
        )
        conn.close()
    except Exception:
        pass  # Silent fail — analytics should never break the app
