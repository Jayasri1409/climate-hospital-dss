"""
Climate-Aware Hospital Resource Planning DSS — Streamlit dashboard
Now running on the REAL trained model and REAL 117-row region-year panel
(replaces the earlier placeholder version).

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

import pickle
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Climate-Aware Hospital Resource Planning DSS", page_icon="⛅", layout="wide")

# ---------------------------------------------------------------------------
# Load real model + real data
# ---------------------------------------------------------------------------

@st.cache_resource
def load_model():
    with open("model/demand_model.pkl", "rb") as f:
        return pickle.load(f)

@st.cache_data
def load_panel():
    df = pd.read_csv("data/modeling_panel_2016_2024.csv")
    df["log_population_exposed"] = np.log1p(df["population_exposed"])
    return df

@st.cache_data
def load_recommendations():
    return pd.read_csv("model/dss_recommendations_2016_2024.csv")

bundle = load_model()
model = bundle["model"]
FEATURES = bundle["features"]
TARGET = bundle["target"]

panel = load_panel()
recs = load_recommendations()

Q25, Q75, Q90 = panel[TARGET].quantile([0.25, 0.75, 0.90])
CAPACITY_INCREASE_PCT = {"Low": 0.00, "Moderate": 0.10, "High": 0.20, "Severe": 0.35}
TIER_COLOR = {"Low": "green", "Moderate": "orange", "High": "orange", "Severe": "red"}


def risk_tier(value: float) -> str:
    if value < Q25:
        return "Low"
    elif value < Q75:
        return "Moderate"
    elif value < Q90:
        return "High"
    return "Severe"


def run_dss(severity: float, population_exposed: float, baseline_beds: float | None):
    X = np.array([[severity, np.log1p(population_exposed)]])
    predicted = float(model.predict(X)[0])
    tier = risk_tier(predicted)
    pct = CAPACITY_INCREASE_PCT[tier]
    extra_beds = round(baseline_beds * pct) if baseline_beds else None
    return predicted, tier, pct, extra_beds


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.title("Climate-Aware Hospital DSS")
st.sidebar.caption("France — real model, real data")
page = st.sidebar.radio("Section", ["Historical explorer", "What-if scenario", "Underlying data"])

# ---------------------------------------------------------------------------
# Page 1: Historical explorer — real region-years, real predictions
# ---------------------------------------------------------------------------

if page == "Historical explorer":
    st.title("Historical region-year explorer")
    st.caption("Real climate/health panel (2016-2024) run through the trained demand model.")

    col_a, col_b = st.columns(2)
    region = col_a.selectbox("Region", sorted(panel["region"].unique()))
    year = col_b.selectbox("Year", sorted(panel[panel["region"] == region]["year"].unique(), reverse=True))

    row = panel[(panel["region"] == region) & (panel["year"] == year)].iloc[0]
    predicted, tier, pct, extra_beds = run_dss(row["heatwave_severity"], row["population_exposed"], row["hospital_beds"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Heatwave severity (real)", f"{row['heatwave_severity']:.1f}")
    c2.metric("Predicted heat-death %", f"{predicted:.2f}%")
    c3.metric("Risk tier", tier)
    c4.metric("Recommended capacity increase", f"{pct*100:.0f}%")

    st.markdown(f"**Risk level:** :{TIER_COLOR[tier]}[{tier}]")

    st.subheader("What this means")
    if pct > 0:
        st.warning(
            f"{region}, {year}: predicted heat-mortality burden falls in the **{tier}** tier, "
            f"relative to this panel's real historical distribution. "
            f"Recommend flexing regional hospital capacity up by **{pct*100:.0f}%** above baseline "
            f"(baseline: {row['hospital_beds']:,.0f} total regional beds; illustrative flex: {extra_beds:,} beds). "
            "Note: baseline_beds is total regional bed stock across all specialties, not ED-specific — "
            "treat the percentage as the primary recommendation, the bed count as illustrative only."
        )
    else:
        st.success(f"{region}, {year}: risk tier **Low** — expected demand fits within baseline capacity.")

    with st.expander("See real underlying values used for this prediction"):
        st.write(row[["region", "year", "heatwave_severity", "population_exposed",
                       "attrib_deaths_heatwave_pct", "hospital_beds"]])

# ---------------------------------------------------------------------------
# Page 2: What-if scenario simulator (the course's required "what-if simulation")
# ---------------------------------------------------------------------------

elif page == "What-if scenario":
    st.title("What-if scenario simulator")
    st.caption(
        "Explore hypothetical future conditions — inputs here are simulated, "
        "but they run through the real trained model, not invented outputs."
    )

    region_for_beds = st.selectbox("Base region (for bed baseline)", sorted(panel["region"].unique()))
    baseline_beds = panel[panel["region"] == region_for_beds]["hospital_beds"].dropna().iloc[-1]

    sev_min, sev_max = float(panel["heatwave_severity"].min()), float(panel["heatwave_severity"].max())
    pop_min, pop_max = float(panel["population_exposed"].min()), float(panel["population_exposed"].max())

    severity = st.slider("Hypothetical heatwave severity", sev_min, sev_max * 1.5, float(panel["heatwave_severity"].median()))
    population_exposed = st.slider("Hypothetical population exposed", pop_min, pop_max * 1.2, float(panel["population_exposed"].median()))

    predicted, tier, pct, extra_beds = run_dss(severity, population_exposed, baseline_beds)

    c1, c2, c3 = st.columns(3)
    c1.metric("Predicted heat-death %", f"{predicted:.2f}%")
    c2.metric("Risk tier", tier)
    c3.metric("Recommended capacity increase", f"{pct*100:.0f}%")

    st.info(
        f"Scenario result: severity={severity:.1f}, population exposed={population_exposed:,.0f} "
        f"→ **{tier}** risk → recommend **{pct*100:.0f}%** capacity flex "
        f"(≈{extra_beds:,} beds relative to {region_for_beds}'s baseline of {baseline_beds:,.0f})."
    )

# ---------------------------------------------------------------------------
# Page 3: Underlying data
# ---------------------------------------------------------------------------

else:
    st.title("Underlying data")
    st.subheader("Real region-year panel (2016-2024)")
    st.dataframe(panel, use_container_width=True)
    st.subheader("Full DSS recommendations, all region-years")
    st.dataframe(recs, use_container_width=True)
