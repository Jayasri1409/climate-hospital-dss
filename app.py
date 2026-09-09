"""
Climate-Aware Hospital Resource Planning DSS - entry point.
Streamlit auto-lists pages/ in the sidebar; this file is just the landing page.
"""
import streamlit as st

st.set_page_config(page_title="Climate-Aware Hospital DSS", page_icon="⛅", layout="wide")

st.title("Climate-Aware Hospital Resource Planning DSS")
st.caption("France — real data, real model, real validation")

st.markdown("""
This system helps hospital administrators translate expected heatwave conditions into
concrete resource-preparation decisions.

**Use the sidebar to navigate:**
- **Overview** — project problem statement and motivation
- **Heat Analysis** — the real, validated daily lag-effect finding (event-study on 2018-2023 data)
- **Live Forecast** — a real 7-day weather forecast run through the validated lag model
- **Hospital DSS** — the annual regional model: historical explorer and what-if scenario simulator
- **Model Performance** — every model tested, and why the final choices were made
""")
