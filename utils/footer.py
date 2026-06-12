import streamlit as st
import base64
import os


def render_footer():
    img_path = os.path.join(os.path.dirname(__file__), "..", "dash_boarding.png")
    with open(img_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <div style="text-align:center; color:#e0e0e0; margin-top:2rem; margin-bottom:-0.5rem;">————————————————————————————————</div>
        <div style="text-align:center; padding:0.5rem 0;">
            <span style="font-size:1rem; color:#ffffff;">
                Data powered by Snowflake | Built with ❤️ by CoCo | Designed and Orchestrated by <a href="https://www.linkedin.com/in/dash-desai/" target="_blank" style="color:#ffffff; text-decoration:underline; font-weight:600;">Dash</a>
            </span>
            <br>
            <a href="https://www.linkedin.com/in/dash-desai/" target="_blank">
                <img src="data:image/png;base64,{img_data}" 
                     style="width:75px; height:75px; border-radius:8px; margin-top:0.5rem;">
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )
