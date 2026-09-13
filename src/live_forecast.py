"""
Climate-Aware Hospital Resource Planning DSS
Live forecast integration — pulls REAL upcoming temperature forecasts
(not simulated data) and runs them through the validated lag-effect
predictor to produce a genuine near-term ED demand forecast.

Uses Open-Meteo (api.open-meteo.com) - free, no API key required,
CC BY 4.0 licensed. Two endpoints used:
  1. Geocoding API - converts a department name to lat/lon
  2. Forecast API  - returns up to 16 days of daily max temperature

NOTE: This calls the live internet and cannot be executed inside the
sandboxed build environment used to develop this project (network access
there is restricted to a fixed allowlist that does not include weather
APIs). It WILL work correctly once deployed on Streamlit Community Cloud,
which has full internet access. Test this specific function after deploying,
before relying on it in a live demo.
"""

import requests

from lag_predictor import classify_and_predict


def get_department_coordinates(department_name: str) -> tuple[float, float]:
    """Look up a French department's approximate coordinates by name."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": f"{department_name}, France", "count": 1, "language": "fr", "format": "json"}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    results = resp.json().get("results")
    if not results:
        raise ValueError(f"No coordinates found for '{department_name}'")
    return results[0]["latitude"], results[0]["longitude"]


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


def get_live_dss_forecast(department_name: str, dept_p90_threshold: float) -> dict:
    """
    End-to-end: real department name -> real coordinates -> real weather
    forecast -> validated lag-effect model -> DSS risk forecast.
    Requires internet access (works when deployed, not in the dev sandbox).
    """
    lat, lon = get_department_coordinates(department_name)
    forecast_tmax = get_live_forecast_tmax(lat, lon, days=7)

    # classify_and_predict needs exactly 4 days [day-3, day-2, day-1, today];
    # for a forward forecast we slide this window across the coming week
    daily_results = []
    for i in range(3, len(forecast_tmax)):
        window = forecast_tmax[i - 3:i + 1]
        pred = classify_and_predict(window, dept_p90_threshold)
        daily_results.append({"forecast_day_index": i, "tmax": forecast_tmax[i], **pred})

    return {"department": department_name, "coordinates": (lat, lon),
            "raw_forecast_tmax": forecast_tmax, "daily_predictions": daily_results}


if __name__ == "__main__":
    # This block requires live internet and will only succeed when run in an
    # environment with unrestricted network access (e.g., after deployment).
    import sys
    try:
        result = get_live_dss_forecast("Rhône", dept_p90_threshold=30.0)
        print(result)
    except Exception as e:
        print(f"Live forecast test failed (expected in sandboxed dev environment): {e}", file=sys.stderr)
