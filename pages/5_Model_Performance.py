import streamlit as st
import pandas as pd

st.set_page_config(page_title="Model Performance", page_icon="📊", layout="wide")
st.title("Model Performance & Selection")
st.caption("Every model tested, with honest results — including the ones that didn't work")

st.header("1. Annual Demand Model (Step B)")
st.markdown("Target: `attrib_deaths_heatwave_pct` — 117 region-years, 2016-2024. "
            "Validated with leave-one-year-out and leave-one-region-out CV, not random splits.")
try:
    df1 = pd.read_csv("data/model_comparison.csv")
    st.dataframe(df1, use_container_width=True)
except FileNotFoundError:
    st.warning("model_comparison.csv not found in data/")

st.header("2. Extended Model Comparison (Enhancement Pass)")
st.markdown("Added Ridge Regression, Ridge with region fixed effects, and Gradient Boosting. "
            "**Finding:** Ridge + region fixed effects won on LOYO (matches real deployment "
            "scenario: same regions, new year); Random Forest won on LORO.")
try:
    df2 = pd.read_csv("data/model_comparison_extended.csv")
    st.dataframe(df2, use_container_width=True)
except FileNotFoundError:
    st.warning("model_comparison_extended.csv not found in data/")

st.header("3. Daily Regression Attempt (Did Not Work — Reported Honestly)")
st.markdown("""
Real daily department-level data (2018-2023). A continuous regression on temperature +
lags failed to beat a naive baseline (**negative R²**), even after fixing a department-size
leak and controlling for day-of-week. This is a genuine, informative finding: all-cause ED
visit volume is only weakly heat-sensitive, since most visits are unrelated to heat —
directly consistent with Flower et al.'s (2026) finding that heat's effect is
diagnosis-specific, not uniform.
""")
try:
    df3 = pd.read_csv("data/daily_model_comparison.csv")
    st.dataframe(df3, use_container_width=True)
except FileNotFoundError:
    st.warning("daily_model_comparison.csv not found in data/")

st.header("4. What Actually Worked: Event-Study Design")
st.markdown("See the **Heat Analysis** page — treating heat as a threshold event "
            "(heatwave day vs. not) instead of a continuous variable revealed a real, "
            "statistically significant, lagged effect (p < 0.0001).")
