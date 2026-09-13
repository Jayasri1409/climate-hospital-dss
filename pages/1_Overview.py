import streamlit as st

st.set_page_config(page_title="Overview", page_icon="📋", layout="wide")
st.title("Project Overview")

st.header("Problem Statement")
st.markdown("""
Hospitals largely respond to heatwave-driven surges in emergency department demand after
they hit, despite heat being forecastable days in advance. No standardized mechanism
currently translates a heatwave forecast into a hospital capacity decision, since climate
data and hospital data are collected by entirely separate systems with no bridge between
them. The relationship between heat exposure and hospital demand is also not simple or
immediate; it is lagged and condition specific. As a result, hospitals face avoidable
resource mismatches during heat events, including emergency department overcrowding,
staffing shortages, and delayed patient care.
""")

st.header("Motivation")
st.markdown("""
France recorded 16,361 heat-attributable emergency department visits in the 2023 season
alone, and heatwaves are projected to grow more frequent and severe. Since heat is one of
the more forecastable climate hazards, a data-driven decision support system that bridges
climate and hospital data can help hospitals prepare proactively instead of reacting after
demand has already risen.
""")

st.header("Two-Tier System Design")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Annual / Regional Model")
    st.markdown("""
    - **Purpose:** seasonal, strategic capacity planning
    - **Data:** 117 region-years, 2016-2024 (Santé publique France + Eurostat)
    - **Output:** risk tier + % staffing/bed recommendation per region
    """)
with col2:
    st.subheader("Daily Lag-Effect Model")
    st.markdown("""
    - **Purpose:** short-term, operational forecasting
    - **Data:** 207,480 department-days, 2018-2023 (real daily temperature + ED visits)
    - **Output:** validated event-study finding — heatwave days show a real, lagged
      demand surge (peaking 1 day later), used to forecast the coming week
    """)
