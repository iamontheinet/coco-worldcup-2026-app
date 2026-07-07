# ⚽ FIFA World Cup 2026 Interactive Explorer

A real-time, interactive Streamlit app for the 2026 FIFA World Cup — the first 48-team tournament hosted across the United States 🇺🇸, Mexico 🇲🇽, and Canada 🇨🇦.

**Live app:** [coco-worldcup-2026.streamlit.app](https://coco-worldcup-2026.streamlit.app/)

## Features

- **Live Scores** — Real-time match scores, clock, and stats via ESPN API with auto-refresh
- **Knockout Bracket** — Interactive vertical bracket (R32 → R16 → QF → SF → Final). Click to pick winners, picks persist locally. ESPN results auto-lock as matches finish.
- **🗺️ Venue Map** — Interactive Folium map showing all 16 stadiums with match cards
- **⚔️ Head-to-Head** — Compare teams with radar charts and historical records
- **🧠 Quiz** — Test your World Cup knowledge

## How It Works

The app combines static reference data from Snowflake with real-time match data from ESPN:

- **Snowflake** stores team info (48 nations, groups, rankings, flags), venues (16 stadiums), and the group stage schedule
- **ESPN API** provides live scores, knockout bracket matchups, and finished match results — no API key needed
- **Auto-refresh** via `@st.fragment(run_every=...)` keeps scores and bracket current without manual reload

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit + custom HTML/JS components |
| Data | Snowflake (`WORLDCUP_2026.PUBLIC`) |
| Live Scores | ESPN free API (scoreboard endpoint) |
| Maps | Folium (CartoDB Positron tiles) |
| Charts | Plotly (radar charts) |
| Deployment | Streamlit Community Cloud |

## Local Development

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Create `.streamlit/secrets.toml` with your Snowflake connection:

```toml
[connections.snowflake]
account = "your-account"
user = "your-user"
password = "your-password"
warehouse = "your-warehouse"
database = "WORLDCUP_2026"
schema = "PUBLIC"
```

## Architecture

```
Streamlit Cloud (auto-deploys on push to main)
├── ESPN API (live scores, knockout matchups — polled every 10-60s)
├── Snowflake (WORLDCUP_2026.PUBLIC)
│   ├── TEAMS (48 rows: name, group, FIFA ranking, flag, captain)
│   ├── VENUES (16 rows: name, city, country, lat/lng, capacity)
│   ├── MATCHES (72 rows: group stage schedule)
│   ├── HISTORICAL_STATS (past WC records, head-to-head)
│   └── PAGE_VIEWS (analytics: session_id, page_name, timestamp)
└── Browser localStorage (bracket picks persistence)
```

---

*Built with [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code), Streamlit, and Snowflake.*
