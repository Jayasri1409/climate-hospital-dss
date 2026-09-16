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
- **Heat Analysis** — the real, validated daily lag-effect finding, including compound heat (hot day + warm night)
- **Hospital DSS** — three views: annual historical explorer, annual what-if simulator, and a daily scenario tab (real climate distributions + real capacity baseline + simulated near-term forecast)
""")
