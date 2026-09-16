"""
Climate-Aware Hospital Resource Planning DSS
Self-contained forecast simulator - replaces the fragile live-API approach.

WHY: the live Open-Meteo integration kept breaking on deployment (wrong
file locations, incomplete uploads, coordinate lookup issues) and is hard
to debug through screenshots alone. This version needs NO live internet
call and NO external file dependency beyond data already in the repo, so
it cannot fail on deployment the way the live version did.

METHOD (this is the "simulated scenario" your faculty approved): for a
chosen region and a chosen number of days ahead, sample tmax/tmin for
each of those days from THAT REGION'S OWN REAL historical distribution
of temperatures for the matching time of year (bootstrap resampling from
real observed days in the same +/-7 day window across all real years in
the dataset). This is a legitimate, standard simulation technique - the
values are simulated, but the DISTRIBUTION they are drawn from is 100%
real, not invented.
"""

import numpy as np
import pandas as pd


def simulate_forward_scenario(region: str, regional_daily_climate: pd.DataFrame,
                               start_date: pd.Timestamp, n_days: int = 7,
                               seed: int | None = None) -> pd.DataFrame:
    """
    regional_daily_climate: the REAL daily regional climate dataframe
        (region, Date, tmax, tmin, tmoy, region_tmax_p90, region_tmin_p90).
    Returns a dataframe of `n_days` simulated future days for `region`,
    each day's tmax/tmin bootstrapped from real historical days within a
    +/-7 day window of the matching calendar date.
    """
    rng = np.random.default_rng(seed)
    sub = regional_daily_climate[regional_daily_climate["region"] == region].copy()
    sub["doy"] = sub["Date"].dt.dayofyear
    p90_tmax = sub["region_tmax_p90"].iloc[0]
    p90_tmin = sub["region_tmin_p90"].iloc[0]

    rows = []
    for i in range(n_days):
        target_date = start_date + pd.Timedelta(days=i)
        target_doy = target_date.dayofyear
        window = sub[(sub["doy"] - target_doy).abs() <= 7]
        if window.empty:
            window = sub  # fallback: whole-region distribution
        sampled = window.sample(1, random_state=rng.integers(0, 1_000_000)).iloc[0]

        is_hot = sampled["tmax"] >= p90_tmax
        is_trop_night = sampled["tmin"] >= p90_tmin
        rows.append({
            "region": region, "date": target_date,
            "simulated_tmax": round(float(sampled["tmax"]), 1),
            "simulated_tmin": round(float(sampled["tmin"]), 1),
            "is_hot_day": bool(is_hot),
            "is_tropical_night": bool(is_trop_night),
            "is_compound_heat_day": bool(is_hot and is_trop_night),
            "sampled_from_real_date": sampled["Date"].date(),
        })
    return pd.DataFrame(rows)
