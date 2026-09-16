import streamlit as st
import pandas as pd

st.set_page_config(page_title="Heat Analysis", page_icon="🌡️", layout="wide")
st.title("Daily Heat-ED Demand Analysis")
st.caption("Real daily data, 2018-2023, 95 French departments — event-study design")

st.markdown("""
Continuous regression on temperature failed to predict daily ED visit deviation (negative
R²), because most ED visits have nothing to do with heat. Treating heat as a threshold
**event** — a heatwave day either happened or didn't, per department's own 90th percentile
— revealed a real, statistically significant, lagged effect instead.
""")

summary = pd.read_csv("data/heat_analysis_summary.csv")
st.subheader("Validated Effect (p < 0.0001)")
st.dataframe(summary, use_container_width=True)

st.bar_chart(summary.set_index("period")["mean_pct_deviation"])

st.info(
    "The effect PEAKS one day after the heatwave day (+2.00%), not on the heatwave day "
    "itself (+1.43%) — an independent confirmation, on real French data, of the lagged "
    "heat-health relationship documented in Flower et al. (2026, BMJ Open)."
)

st.subheader("Enhancement: Compound Heat (hot day + warm night)")
st.caption("Adding TMin (overnight temperature) — 'tropical nights' prevent recovery and are a known stronger risk factor")
compound = pd.read_csv("data/compound_heat_summary.csv")
st.dataframe(compound, use_container_width=True)
st.bar_chart(compound.set_index("signal")["mean_pct_deviation"])
st.success(
    "Compound heat (+2.33%) is the STRONGEST validated signal in this project — stronger than "
    "hot-day-alone (+1.84%) or warm-night-alone (+1.79%). This directly supports using compound "
    "heat, not simple daytime temperature, as the primary daily risk flag (see Hospital DSS page)."
)

st.subheader("Example: Paris, Summer 2022")
try:
    sample = pd.read_csv("data/sample_daily_series_paris_2022.csv", parse_dates=["Date"])
    st.line_chart(sample.set_index("Date")[["tmax", "pct_deviation"]])
    st.caption("Real daily max temperature vs. real ED visit deviation, Paris, June-Aug 2022 "
               "(includes the real July 2022 French heatwave, peak 40.5°C).")
except FileNotFoundError:
    st.warning("Sample series file not found.")

st.subheader("Which Departments Are Most Heat-Sensitive?")
st.caption(
    "For each department, comparing ITS OWN hot days vs. ITS OWN normal days — this answers "
    "'which places need the most attention', not just 'does heat matter nationally'."
)
ranking = pd.read_csv("data/department_heat_sensitivity_ranking.csv")
top10 = ranking.head(10)
st.dataframe(top10[["libelle_dep", "sensitivity_gap_pct", "n_hot_days"]], use_container_width=True)
st.bar_chart(top10.set_index("libelle_dep")["sensitivity_gap_pct"])
st.info(
    "Notably, this isn't simply 'the hottest places' — northern departments like Ardennes and "
    "Meuse rank in the top 5, alongside Corsica. Likely explanation: sensitivity reflects how "
    "prepared a department is for ITS OWN hot days, not absolute temperature — a place that "
    "rarely gets hot has less AC and a less heat-acclimatized population."
)
st.caption(
    "Caveat: each department has only ~220 hot days (vs. ~20,600 pooled in the main finding "
    "above), so individual department rankings are noisier than the main pooled result — treat "
    "this as directional, not as statistically strong as the headline finding."
)
