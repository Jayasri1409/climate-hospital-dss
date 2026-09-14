import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import streamlit as st
import pandas as pd

from forecast_simulator import simulate_forward_scenario
from simulated_capacity import simulate_daily_capacity

st.set_page_config(page_title="Daily Forecast", page_icon="📡", layout="wide")
st.title("Daily Regional Forecast")
st.caption(
    "Self-contained scenario simulator — no live internet call, so it cannot fail on "
    "deployment. Temperatures are simulated by resampling from each region's own REAL "
    "historical distribution (not invented values); capacity is simulated and calibrated "
    "to the region's REAL annual bed baseline, since no public daily bed-occupancy data "
    "exists anywhere in France (confirmed during this project's data search)."
)

clim = pd.read_csv("data/regional_daily_climate.csv", parse_dates=["Date"])
panel = pd.read_csv("data/annual_panel.csv")

region = st.selectbox("Region", sorted(clim["region"].unique()))
n_days = st.slider("Days ahead to simulate", 3, 14, 7)
start_date = st.date_input("Scenario start date", pd.Timestamp.today() + pd.Timedelta(days=1))

if st.button("Run scenario"):
    scenario = simulate_forward_scenario(region, clim, pd.Timestamp(start_date), n_days=n_days)
    total_beds = panel[panel["region"] == region].sort_values("year")["hospital_beds"].dropna().iloc[-1]
    cap = simulate_daily_capacity(region, pd.to_datetime(scenario["date"]), total_beds,
                                   is_compound_heat=scenario["is_compound_heat_day"].values)

    combined = scenario.merge(cap[["date", "simulated_occupancy_pct", "simulated_available_beds"]],
                               left_on="date", right_on="date")

    n_compound = int(combined["is_compound_heat_day"].sum())
    st.metric("Compound heat days in this scenario", f"{n_compound} / {n_days}")
    if n_compound > 0:
        st.warning(
            f"{n_compound} day(s) in this scenario are compound heat days (hot day + warm "
            f"night) — the strongest validated demand signal in this project (+2.33% ED "
            f"demand, p<0.00001 on real 2018-2023 data). Expect reduced available capacity "
            f"on these days."
        )
    else:
        st.success("No compound heat days in this scenario — normal capacity expected.")

    st.dataframe(combined, use_container_width=True)
    st.line_chart(combined.set_index("date")[["simulated_tmax", "simulated_tmin"]])
    st.bar_chart(combined.set_index("date")[["simulated_available_beds"]])

st.caption(
    "Real: climate distribution the scenario is drawn from, and the annual bed baseline. "
    "Simulated: the specific future dates' values and daily occupancy — per project scope, "
    "with faculty approval, since no real daily/future data exists for either."
)
