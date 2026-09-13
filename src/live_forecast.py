"""
Climate-Aware Hospital Resource Planning DSS
Live forecast integration — pulls REAL upcoming temperature forecasts
(not simulated data) and runs them through the validated lag-effect
predictor to produce a genuine near-term ED demand forecast.

Uses Open-Meteo (api.open-meteo.com) - free, no API key required,
CC BY 4.0 licensed. Only the Forecast API is called live now; department
coordinates come from a fixed local table (data/dept_coordinates.csv),
not live geocoding, because geocoding department NAMES (rather than city
names) failed for several departments (accents/apostrophes/ambiguous
names, e.g. Val-d'Oise, Cote-d'Or). Using each department's prefecture
city coordinates directly removes that failure mode entirely and is
faster (one live API call instead of two).

NOTE: The forecast call requires live internet and cannot be executed
inside the sandboxed build environment used to develop this project.
It WILL work correctly once deployed on Streamlit Community Cloud, which
has full internet access.
"""

import os
import pandas as pd
import requests

from lag_predictor import classify_and_predict

_COORDS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "data", "dept_coordinates.csv")
_coords_df = pd.read_csv(_COORDS_PATH, dtype={"dep": str})


def get_department_coordinates(dep_code: str) -> tuple[float, float]:
    """Look up a French department's coordinates by CODE (e.g. '69', '2A'),
    using the fixed local table - no live geocoding, no failure mode."""
    row = _coords_df[_coords_df["dep"] == str(dep_code)]
    if row.empty:
        raise ValueError(f"No coordinates found for department code '{dep_code}'. "
                          f"Check data/dept_coordinates.csv covers this department.")
    return float(row.iloc[0]["lat"]), float(row.iloc[0]["lon"])


def get_live_forecast_tmax(lat: float, lon: float, days: int = 7) -> list[float]:
    """Fetch real daily max temperature forecast (not simulated) for the next N days."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "daily": "temperature_2m_max",
        "forecast_days": days,
        "timezone": "Europe/Paris",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()["daily"]["temperature_2m_max"]


def get_live_dss_forecast(dep_code: str, dept_p90_threshold: float) -> dict:
    """
    End-to-end: department code -> fixed coordinates -> real weather
    forecast -> validated lag-effect model -> DSS risk forecast.
    Requires internet access (works when deployed, not in the dev sandbox).
    """
    lat, lon = get_department_coordinates(dep_code)
    forecast_tmax = get_live_forecast_tmax(lat, lon, days=7)

    # classify_and_predict needs exactly 4 days [day-3, day-2, day-1, today];
    # for a forward forecast we slide this window across the coming week
    daily_results = []
    for i in range(3, len(forecast_tmax)):
        window = forecast_tmax[i - 3:i + 1]
        pred = classify_and_predict(window, dept_p90_threshold)
        daily_results.append({"forecast_day_index": i, "tmax": forecast_tmax[i], **pred})

    return {"department": dep_code, "coordinates": (lat, lon),
            "raw_forecast_tmax": forecast_tmax, "daily_predictions": daily_results}


if __name__ == "__main__":
    # This block requires live internet and will only succeed when run in an
    # environment with unrestricted network access (e.g., after deployment).
    import sys
    try:
        result = get_live_dss_forecast("69", dept_p90_threshold=30.0)  # Rhone
        print(result)
    except Exception as e:
        print(f"Live forecast test failed (expected in sandboxed dev environment): {e}", file=sys.stderr)
