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
    Generate a SIMULATED daily capacity series for one region, with an
    ACTIONABLE recommendation (not just a descriptive occupancy number).
    total_beds: REAL value from the annual panel (not simulated).
    is_compound_heat: real/derived boolean array aligning with `dates`.
    """
    rng = np.random.default_rng(seed)
    n = len(dates)
    occupancy = rng.normal(BASE_OCCUPANCY_MEAN, BASE_OCCUPANCY_STD, size=n)

    is_weekend = pd.Series(dates).dt.dayofweek.isin([5, 6]).values
    occupancy = occupancy + np.where(is_weekend, WEEKEND_OCCUPANCY_DELTA, 0)

    if is_compound_heat is not None:
        occupancy = occupancy + np.where(is_compound_heat, COMPOUND_HEAT_OCCUPANCY_DELTA, 0)

    occupancy = np.clip(occupancy, 0.55, 0.99)
    occupied_beds = total_beds * occupancy
    available_beds = total_beds - occupied_beds

    # ACTIONABLE recommendation: on compound heat days, the validated real finding
    # (+2.33% ED demand) implies extra beds/staff needed ABOVE today's available
    # capacity, not just a description of how full things already are.
    demand_surge_pct = np.where(is_compound_heat, 2.33, 0.0) if is_compound_heat is not None else np.zeros(n)
    extra_beds_needed = np.round(total_beds * (demand_surge_pct / 100))
    # Staffing: no daily/regional staffing dataset exists anywhere in France (confirmed
    # during this project's search) - staffing recommendation uses the SAME percentage
    # as beds, applied to a nurse baseline estimated from real Eurostat national ratios
    # (documented assumption, same approach as the annual model's Step C).
    extra_nurses_needed = np.round(extra_beds_needed * 0.3)   # ~0.3 nurses per extra bed, typical ratio
    extra_doctors_needed = np.round(extra_beds_needed * 0.08)  # ~0.08 doctors per extra bed, typical ratio

    return pd.DataFrame({
        "region": region, "date": dates,
        "total_beds_real": total_beds,
        "simulated_occupancy_pct": (occupancy * 100).round(1),
        "simulated_available_beds": available_beds.round(0),
        "is_compound_heat_day": is_compound_heat if is_compound_heat is not None else False,
        "recommended_extra_beds": extra_beds_needed,
        "recommended_extra_nurses": extra_nurses_needed,
        "recommended_extra_doctors": extra_doctors_needed,
    })
