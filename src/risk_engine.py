"""
Climate-Aware Hospital Resource Planning DSS
Step C — Capacity gap logic

What this does, in order:
  1. Load the trained demand model from Step B.
  2. Use it to predict attrib_deaths_heatwave_pct for a region/scenario.
  3. Convert that prediction into a RISK TIER, by comparing it against the
     real historical distribution of the target in our own 117-row panel
     (not an arbitrary cutoff — it's "how does this compare to what this
     region-year panel has actually seen").
  4. Convert the risk tier into a recommended CAPACITY INCREASE (%), using
     published hospital surge-capacity benchmarks (see SOURCES below) —
     NOT a heat-specific hospitalization ratio, because the literature
     review in Step B/C discussion showed that ratio isn't reliably
     established for heatwaves specifically.
  5. Apply that % increase to the region's real hospital_beds figure to
     get a concrete "beds to prepare" number. The same % is applied as a
     staffing proxy, flagged as an assumption (no regional nurse/doctor
     data exists at the granularity needed — see README limitations).

SOURCES for the capacity-increase bands:
  - Einav et al. 2014 (CHEST consensus statement) / Israeli hospital
    surge planning standards: ~20% surge capacity accommodates most
    acute incidents.
  - Domestic Preparedness (2010), reporting on H1N1: some hospitals saw
    ED patient surges of 50-100% above normal volumes during a severe
    but non-catastrophic event.
  These anchor the High and Severe bands below; Low/Moderate are
  interpolated conservatively beneath the published 20% "most incidents"
  benchmark.
"""

import pandas as pd
import numpy as np
import pickle
import os

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_THIS_DIR)
MODEL_PATH = os.path.join(_REPO_ROOT, "models", "annual_model.pkl")
PANEL_PATH = os.path.join(_REPO_ROOT, "data", "annual_panel.csv")
OUT = os.path.join(_REPO_ROOT, "data")

# ---------------------------------------------------------------------------
# 1. Load model + panel
# ---------------------------------------------------------------------------

with open(MODEL_PATH, "rb") as f:
    bundle = pickle.load(f)
model = bundle["model"]
FEATURES = bundle["features"]
TARGET = bundle["target"]

panel = pd.read_csv(PANEL_PATH)
panel["log_population_exposed"] = np.log1p(panel["population_exposed"])

# ---------------------------------------------------------------------------
# 2. Define risk tiers from the REAL historical distribution of the target
#    (quartile-based — defensible, not arbitrary)
# ---------------------------------------------------------------------------

q25, q50, q75, q90 = panel[TARGET].quantile([0.25, 0.50, 0.75, 0.90])
print("Risk tier cutoffs (from real historical attrib_deaths_heatwave_pct):")
print(f"  Low      : < {q25:.3f}")
print(f"  Moderate : {q25:.3f} - {q75:.3f}")
print(f"  High     : {q75:.3f} - {q90:.3f}")
print(f"  Severe   : > {q90:.3f}")


def risk_tier(predicted_value: float) -> str:
    if predicted_value < q25:
        return "Low"
    elif predicted_value < q75:
        return "Moderate"
    elif predicted_value < q90:
        return "High"
    else:
        return "Severe"


# ---------------------------------------------------------------------------
# 3. Risk tier -> recommended capacity increase (%)
#    Anchored to published surge-capacity literature, see module docstring.
# ---------------------------------------------------------------------------

CAPACITY_INCREASE_PCT = {
    "Low": 0.00,
    "Moderate": 0.10,
    "High": 0.20,       # matches the published "20% accommodates most acute incidents" benchmark
    "Severe": 0.35,     # conservative point inside the published 50-100% H1N1 surge range,
                         # kept below it deliberately since heatwaves are typically less acute
                         # than a pandemic surge event
}


def recommend(region: str, year: int) -> dict:
    """Run the full Step C pipeline for one region-year in the panel."""
    row = panel[(panel["region"] == region) & (panel["year"] == year)]
    if row.empty:
        raise ValueError(f"No data for {region}, {year}")
    row = row.iloc[0]

    X = row[FEATURES].values.reshape(1, -1)
    predicted = model.predict(X)[0]
    tier = risk_tier(predicted)
    pct_increase = CAPACITY_INCREASE_PCT[tier]

    baseline_beds = row["hospital_beds"]
    extra_beds = round(baseline_beds * pct_increase) if pd.notna(baseline_beds) else None

    return {
        "region": region,
        "year": year,
        "predicted_attrib_deaths_heatwave_pct": round(float(predicted), 3),
        "risk_tier": tier,
        "recommended_capacity_increase_pct": round(pct_increase * 100, 1),
        "baseline_beds": baseline_beds,
        "extra_beds_recommended": extra_beds,
        "note": "Staffing recommendation uses the same % increase as beds "
                "(no regional nurse/doctor dataset exists at this granularity — documented assumption).",
    }


# ---------------------------------------------------------------------------
# 4. Run it for every region-year in the panel and save a results table
#    (this is your "analysis" output — one row of DSS recommendation per
#    real historical region-year, useful for the dashboard and report)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    results = []
    for _, r in panel.iterrows():
        results.append(recommend(r["region"], r["year"]))

    results_df = pd.DataFrame(results)
    results_df.to_csv(f"{OUT}/dss_recommendations_2016_2024.csv", index=False)

    print("\nSample output (first 8 rows):")
    print(results_df.head(8).to_string(index=False))

    print(f"\nRisk tier counts across all region-years:")
    print(results_df["risk_tier"].value_counts())
