import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Hospital DSS", page_icon="🏥", layout="wide")
st.title("Annual Regional Capacity Planning")
st.caption("Real 2016-2024 region-year panel, trained demand model, capacity gap logic")

from risk_engine import panel, recommend, TARGET, model, FEATURES  # noqa: E402

tab1, tab2 = st.tabs(["Historical Explorer", "What-If Scenario"])

with tab1:
    col_a, col_b = st.columns(2)
    region = col_a.selectbox("Region", sorted(panel["region"].unique()))
    year = col_b.selectbox("Year", sorted(panel[panel["region"] == region]["year"].unique(), reverse=True))

    result = recommend(region, int(year))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Predicted heat-death %", f"{result['predicted_attrib_deaths_heatwave_pct']}%")
    c2.metric("Risk tier", result["risk_tier"])
    c3.metric("Capacity increase", f"{result['recommended_capacity_increase_pct']}%")
    c4.metric("Baseline beds", f"{result['baseline_beds']:,.0f}")

    if result["recommended_capacity_increase_pct"] > 0:
        st.warning(
            f"{region}, {year}: recommend {result['recommended_capacity_increase_pct']}% capacity "
            f"increase (~{result['extra_beds_recommended']:,} beds, illustrative — this is total "
            f"regional bed stock, not ED-specific). {result['note']}"
        )
    else:
        st.success(f"{region}, {year}: expected demand fits within baseline capacity.")

    region_trend = panel[panel["region"] == region].sort_values("year").set_index("year")
    st.subheader(f"{region}: trend, 2016-2024")
    st.line_chart(region_trend[[TARGET]])

with tab2:
    st.caption("Hypothetical inputs, run through the real trained model — not invented outputs.")
    region_for_beds = st.selectbox("Base region (for bed baseline)", sorted(panel["region"].unique()), key="wif_region")
    baseline_beds = panel[panel["region"] == region_for_beds]["hospital_beds"].dropna().iloc[-1]

    severity = st.slider("Hypothetical heatwave severity", float(panel["heatwave_severity"].min()),
                          float(panel["heatwave_severity"].max()) * 1.5, float(panel["heatwave_severity"].median()))
    population = st.slider("Hypothetical population exposed", float(panel["population_exposed"].min()),
                            float(panel["population_exposed"].max()) * 1.2, float(panel["population_exposed"].median()))

    X = np.array([[severity, np.log1p(population)]])
    pred = float(model.predict(X)[0])
    st.metric("Predicted heat-death %", f"{pred:.2f}%")
