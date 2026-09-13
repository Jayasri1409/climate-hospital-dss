import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Hospital DSS", page_icon="🏥", layout="wide")
st.title("Hospital Capacity Planning")
st.caption("Two timescales: annual/regional (seasonal planning) and daily/department (short-term operational)")

from risk_engine import panel, recommend, TARGET, model, FEATURES  # noqa: E402

tab1, tab2, tab3 = st.tabs(["Historical Explorer (Annual)", "What-If Scenario (Annual)", "Daily-Informed Recommendation (New)"])

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

with tab3:
    st.markdown("""
    This combines the two validated pieces of this project into one recommendation:
    - **Demand signal**: the real, statistically validated daily lag-effect model (Heat Analysis
      page) — a live 7-day weather forecast for the selected department.
    - **Capacity baseline**: the region's real annual bed count (Eurostat) — since no daily,
      department-level bed data is publicly available, this baseline stays annual/regional.

    The result is a **short-term flex on top of the existing seasonal baseline**, not a
    replacement for the annual model — the two operate at different, complementary timescales.
    """)

    thresholds = pd.read_csv("data/dept_heatwave_thresholds.csv", dtype={"dep": str})
    dept_to_region = pd.read_csv("data/dept_to_region.csv", dtype={"dep": str})

    department_name = st.selectbox("Department", sorted(thresholds["dep_name"].tolist()), key="daily_dept")
    row = thresholds[thresholds["dep_name"] == department_name].iloc[0]
    dep_code, p90 = row["dep"], float(row["p90_tmax"])

    region_row = dept_to_region[dept_to_region["dep"] == dep_code]
    if region_row.empty:
        st.error(f"No region mapping found for department {department_name} ({dep_code}).")
    else:
        mapped_region = region_row.iloc[0]["region"]
        region_beds = panel[panel["region"] == mapped_region]["hospital_beds"].dropna().iloc[-1]
        st.caption(f"{department_name} (dept {dep_code}) → {mapped_region} — baseline {region_beds:,.0f} regional beds")

        if st.button("Get daily-informed recommendation"):
            try:
                from live_forecast import get_live_dss_forecast
                with st.spinner("Fetching real weather forecast..."):
                    result = get_live_dss_forecast(dep_code, dept_p90_threshold=p90)

                preds = pd.DataFrame(result["daily_predictions"])
                peak_pct = preds["peak_pct"].max()
                # Small-scale SHORT-TERM flex, distinct in magnitude from the annual model's
                # larger seasonal percentages — this is a few-day operational adjustment,
                # not a seasonal capacity plan.
                short_term_extra_beds = round(region_beds * (peak_pct / 100) * 0.1)

                c1, c2, c3 = st.columns(3)
                c1.metric("Peak forecast surge (next 7 days)", f"{peak_pct:.2f}%")
                c2.metric("Risk level", preds.loc[preds["peak_pct"].idxmax(), "risk_level"])
                c3.metric("Short-term bed flex (illustrative)", f"{short_term_extra_beds:,}")

                st.dataframe(preds, use_container_width=True)
                st.caption(
                    "Short-term bed flex is a small operational adjustment scaled from the "
                    "regional baseline — NOT on the same scale as the annual model's seasonal "
                    "percentage recommendation. Both figures are illustrative conversions of a "
                    "percentage signal, not literal per-hospital bed counts."
                )
            except Exception as e:
                st.error(
                    f"Live forecast failed: {e}\n\n"
                    "Requires internet access; will work once deployed on Streamlit Cloud."
                )
