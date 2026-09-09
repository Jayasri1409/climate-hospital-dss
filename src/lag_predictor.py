"""
Climate-Aware Hospital Resource Planning DSS
Daily lag-effect predictor — formalizes the validated event-study finding into
a usable prediction function.

Validated finding (from build_daily_model.py event-study test, real data,
2018-2023, p<0.00001):
  - Heatwave day (dept's own top 10% hottest days): +1.43% ED visit deviation
  - 1 day after a heatwave day:  +2.00% deviation  (largest effect)
  - 2 days after: +1.81%
  - 3 days after: +1.82%
  - Normal days: -0.44%

This is used as a rule-based predictor (not a black-box regression), since
the event-study approach is what actually worked, and rule-based logic is
more transparent/auditable for a DSS than a regression that a reviewer can't
easily verify by eye.
"""

import pandas as pd
import numpy as np

# Effect sizes from the validated event-study (see docstring above)
LAG_EFFECTS_PCT = {
    "today": 1.43,
    "day+1": 2.00,
    "day+2": 1.81,
    "day+3": 1.82,
}
BASELINE_PCT = -0.44  # normal-day average, for comparison


def classify_and_predict(dept_recent_tmax: list[float], dept_p90_threshold: float) -> dict:
    """
    Given a department's last 4 days of max temperature (oldest to newest,
    i.e. [day-3, day-2, day-1, today]) and that department's own 90th
    percentile summer temperature threshold, predict expected ED demand
    deviation for today through day+3.
    """
    if len(dept_recent_tmax) != 4:
        raise ValueError("Provide exactly 4 days of tmax: [day-3, day-2, day-1, today]")

    is_hw = [t >= dept_p90_threshold for t in dept_recent_tmax]  # day-3 .. today
    # today's prediction depends on whether TODAY is a heatwave day
    # day+1..day+3 predictions depend on whether the LAST 1-3 days included a heatwave day
    forecast = {}
    forecast["today"] = LAG_EFFECTS_PCT["today"] if is_hw[3] else BASELINE_PCT
    forecast["day+1"] = LAG_EFFECTS_PCT["day+1"] if is_hw[3] else BASELINE_PCT
    forecast["day+2"] = LAG_EFFECTS_PCT["day+2"] if (is_hw[3] or is_hw[2]) else BASELINE_PCT
    forecast["day+3"] = LAG_EFFECTS_PCT["day+3"] if (is_hw[3] or is_hw[2] or is_hw[1]) else BASELINE_PCT

    peak_pct = max(forecast.values())
    if peak_pct >= 1.8:
        risk = "Elevated"
    elif peak_pct >= 1.0:
        risk = "Watch"
    else:
        risk = "Normal"

    return {"daily_forecast_pct": forecast, "peak_pct": peak_pct, "risk_level": risk}


if __name__ == "__main__":
    # Quick sanity check using the real Paris 2022 sample data included in this repo.
    import os
    sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "data", "sample_daily_series_paris_2022.csv")
    df = pd.read_csv(sample_path, parse_dates=["Date"])
    sub = df.sort_values("Date").reset_index(drop=True)
    p90 = sub["tmax"].quantile(0.90)

    # Use a real hot stretch from the data as a test case
    hot_window = sub[sub["Date"].between("2022-07-15", "2022-07-19")]
    print("Real tmax values, Paris, mid-July 2022:", hot_window["tmax"].tolist())
    tmax_last4 = hot_window["tmax"].tolist()[-4:]
    result = classify_and_predict(tmax_last4, p90)
    print("Predicted forecast:", result)
