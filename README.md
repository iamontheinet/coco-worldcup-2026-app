# ⚽ FIFA World Cup 2026 Interactive Explorer

A visually rich, interactive Streamlit app for exploring the 2026 FIFA World Cup — the first tri-nation tournament hosted by the United States 🇺🇸, Mexico 🇲🇽, and Canada 🇨🇦.

## Features

- **🗺️ Venue Map** — Interactive 3D pydeck map showing all 16 stadiums with match schedules
- **⚔️ Head-to-Head** — Compare any two teams with radar charts and detailed stats
- **📊 Group Simulator** — Set match scores and see real-time group standings
- **🏆 Bracket Builder** — Pick your knockout bracket winners all the way to the Final
- **📈 Stats & Trivia** — Historical World Cup records, fun facts, and data visualizations

## Tech Stack

- **Frontend:** Streamlit
- **Data:** Snowflake (WORLDCUP_2026 database)
- **Visualizations:** Plotly, PyDeck
- **Deployment:** Streamlit Community Cloud

## Local Development

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Create `.streamlit/secrets.toml` with your Snowflake credentials:

```toml
[snowflake]
account = "your-account"
user = "your-user"
password = "your-password"
warehouse = "your-warehouse"
database = "WORLDCUP_2026"
schema = "PUBLIC"
```

## Data

All data is stored in Snowflake's `WORLDCUP_2026` database:
- **TEAMS** — 48 qualified nations with rankings, squad values, and key players
- **VENUES** — 16 stadiums with coordinates and capacities
- **MATCHES** — Full group stage schedule (72 matches)
- **HISTORICAL_STATS** — 30 historical World Cup records and trivia

---

*Built with Streamlit ❤️ and Snowflake ❄️*
