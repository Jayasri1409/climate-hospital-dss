import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Live Forecast", page_icon="📡", layout="wide")
st.title("Live 7-Day Forecast")
st.caption("Real weather forecast (Open-Meteo), run through the validated lag-effect model")

thresholds = pd.read_csv("data/dept_heatwave_thresholds.csv", dtype={"dep": str})

department_name = st.selectbox("Department", sorted(thresholds["dep_name"].tolist()))

if st.button("Get live forecast"):
    try:
        from live_forecast import get_live_dss_forecast

        row = thresholds[thresholds["dep_name"] == department_name]
        dep_code = row.iloc[0]["dep"]
        p90 = float(row.iloc[0]["p90_tmax"])

        with st.spinner("Fetching real weather forecast..."):
            result = get_live_dss_forecast(dep_code, dept_p90_threshold=p90)

        st.success(f"Live forecast retrieved for {department_name} (dept {dep_code})")
        preds = pd.DataFrame(result["daily_predictions"])
        st.dataframe(preds, use_container_width=True)

    except Exception as e:
        st.error(
            f"Live forecast failed: {e}\n\n"
            "This feature requires internet access and will work once deployed on "
            "Streamlit Community Cloud. It cannot be tested in a network-restricted "
            "development sandbox."
        )

st.caption(
    "Uses Open-Meteo (free, no API key) for real forecast data, and the validated "
    "event-study lag model from the Heat Analysis page — not simulated data. "
    "Coordinates come from each department's prefecture city (fixed lookup table), "
    "not live name-based geocoding, since department names were failing to resolve."
)
