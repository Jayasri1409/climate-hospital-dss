"""
Climate-Aware Hospital Resource Planning DSS
Simulated daily regional capacity.

WHY THIS IS SIMULATED (not real): no public dataset anywhere (French or
otherwise) publishes daily, department/region-level hospital bed occupancy.
This was confirmed repeatedly during this project's data search. Per
explicit faculty guidance, simulated/dummy data is an acceptable input
where real data does not exist - so this module generates a realistic
DAILY capacity series, calibrated to the REAL annual regional bed count
(Eurostat, via annual_panel.csv), rather than the real historical
climate/ED data, which stays genuine throughout this project.

Method: each day's AVAILABLE capacity = real total beds x a simulated
occupancy fraction, drawn from a normal distribution around a realistic
baseline occupancy rate (French hospitals typically run ~80-85% average
occupancy - a commonly cited range in hospital capacity literature),
with added noise on weekends (lower elective admissions) and a downward
pressure specifically on days flagged as compound-heat days (representing
the real, validated +2.33% ED demand signal translating into reduced
headroom).
"""

import numpy as np
import pandas as pd

BASE_OCCUPANCY_MEAN = 0.82   # realistic average occupancy for French hospitals
BASE_OCCUPANCY_STD = 0.04
WEEKEND_OCCUPANCY_DELTA = -0.03  # slightly lower routine occupancy on weekends
COMPOUND_HEAT_OCCUPANCY_DELTA = 0.05  # real validated ED surge -> less available headroom


def simulate_daily_capacity(region: str, dates: pd.DatetimeIndex, total_beds: float,
                             is_compound_heat: np.ndarray | None = None,
                             seed: int | None = None) -> pd.DataFrame:
    """
    Generate a SIMULATED daily capacity series for one region.
    total_beds: REAL value from the annual panel (not simulated).
    is_compound_heat: optional real/derived boolean array aligning with `dates`,
        from the real climate data - nudges simulated occupancy up on those days.
    """
    rng = np.random.default_rng(seed)
    n = len(dates)
    occupancy = rng.normal(BASE_OCCUPANCY_MEAN, BASE_OCCUPANCY_STD, size=n)

    is_weekend = pd.Series(dates).dt.dayofweek.isin([5, 6]).values
    occupancy = occupancy + np.where(is_weekend, WEEKEND_OCCUPANCY_DELTA, 0)

    if is_compound_heat is not None:
        occupancy = occupancy + np.where(is_compound_heat, COMPOUND_HEAT_OCCUPANCY_DELTA, 0)

    occupancy = np.clip(occupancy, 0.55, 0.99)  # keep within a realistic range

    occupied_beds = total_beds * occupancy
    available_beds = total_beds - occupied_beds

    return pd.DataFrame({
        "region": region, "date": dates,
        "total_beds_real": total_beds,
        "simulated_occupancy_pct": (occupancy * 100).round(1),
        "simulated_available_beds": available_beds.round(0),
        "is_compound_heat_day": is_compound_heat if is_compound_heat is not None else False,
    })
