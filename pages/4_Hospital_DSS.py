import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Hospital DSS", page_icon="🏥", layout="wide")
st.title("Hospital Capacity Planning")
st.caption("Two timescales: annual/regional (seasonal, real data) and daily/regional (short-term, real climate distribution + simulated capacity)")

from risk_engine import panel, recommend, TARGET, model, FEATURES  # noqa: E402
from forecast_simulator import simulate_forward_scenario  # noqa: E402
from simulated_capacity import simulate_daily_capacity  # noqa: E402

tab1, tab2, tab3 = st.tabs(["Historical Explorer (Annual)", "What-If Scenario (Annual)", "Daily Scenario Recommendation"])

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
            f"increase (~{result['extra_beds_recommended']:,} beds, illustrative — total regional "
            f"bed stock, not ED-specific). {result['note']}"
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

with tab3:
    st.markdown("""
    Combines the annual model's real regional bed baseline with a **self-contained scenario
    simulator** for near-term planning — no live internet call, so this cannot fail on
    deployment the way an external API integration can.

    - **Climate values**: simulated, but sampled from that region's REAL historical
      temperature distribution for the matching time of year (not invented).
    - **Capacity baseline**: REAL (Eurostat, from the annual panel).
    - **Daily occupancy**: simulated and calibrated to the real baseline, since no public
      daily bed-occupancy data exists anywhere in France (confirmed during this project).
    """)

    clim = pd.read_csv("data/regional_daily_climate.csv", parse_dates=["Date"])
    region = st.selectbox("Region", sorted(clim["region"].unique()), key="daily_region")
    n_days = st.slider("Days ahead", 3, 14, 7, key="daily_days")
    start_date = st.date_input("Scenario start date", pd.Timestamp.today() + pd.Timedelta(days=1), key="daily_start")

    if st.button("Run daily scenario"):
        scenario = simulate_forward_scenario(region, clim, pd.Timestamp(start_date), n_days=n_days)
        total_beds = panel[panel["region"] == region].sort_values("year")["hospital_beds"].dropna().iloc[-1]
        cap = simulate_daily_capacity(region, pd.to_datetime(scenario["date"]), total_beds,
                                       is_compound_heat=scenario["is_compound_heat_day"].values)
        combined = scenario.merge(cap[["date", "simulated_occupancy_pct", "simulated_available_beds"]], on="date")

        n_compound = int(combined["is_compound_heat_day"].sum())
        c1, c2, c3 = st.columns(3)
        c1.metric("Baseline beds (real)", f"{total_beds:,.0f}")
        c2.metric("Compound heat days", f"{n_compound} / {n_days}")
        c3.metric("Min available beds (simulated)", f"{combined['simulated_available_beds'].min():,.0f}")

        if n_compound > 0:
            st.warning(
                f"{n_compound} compound heat day(s) in this scenario — the strongest validated "
                f"demand signal found in this project (+2.33% ED demand, p<0.00001, real "
                f"2018-2023 data). Expect reduced available capacity on those days."
            )
        st.dataframe(combined, use_container_width=True)
