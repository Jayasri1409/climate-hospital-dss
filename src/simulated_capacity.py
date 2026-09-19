
"""
Climate-Aware Hospital Resource Planning DSS
Simulated daily regional capacity and staffing recommendations.

Occupancy and staffing are simulated planning estimates.
They are not real daily hospital staffing observations.

Recommendations depend on:
1. Daily hospital occupancy.
2. Compound heat-day conditions.

Planning assumptions:
- Normal occupancy baseline: 82%
- High-occupancy planning threshold: 85%
- Compound heat demand increase: 2.33%
- Nurse staffing ratio: 0.3 nurses per additional bed
- Doctor staffing ratio: 0.08 doctors per additional bed
"""

import numpy as np
import pandas as pd


# -------------------------------
# 1. SIMULATION SETTINGS
# -------------------------------

BASE_OCCUPANCY_MEAN = 0.82
BASE_OCCUPANCY_STD = 0.04

WEEKEND_OCCUPANCY_DELTA = -0.03

COMPOUND_HEAT_OCCUPANCY_DELTA = 0.05

# Occupancy level used for staffing planning
OCCUPANCY_THRESHOLD = 0.85

# Assumed additional demand on compound heat days
HEAT_DEMAND_SURGE_PCT = 2.33

# Staffing ratios (project assumptions)
NURSES_PER_EXTRA_BED = 0.3
DOCTORS_PER_EXTRA_BED = 0.08


# -------------------------------
# 2. DAILY CAPACITY SIMULATION
# -------------------------------

def simulate_daily_capacity(
    region: str,
    dates: pd.DatetimeIndex,
    total_beds: float,
    is_compound_heat: np.ndarray | None = None,
    seed: int | None = None
) -> pd.DataFrame:

    """
    Simulate daily hospital capacity and staffing recommendations.

    Staffing recommendations depend on daily occupancy
    and compound heat-day conditions.

    Parameters
    ----------
    region:
        Region name.

    dates:
        Dates for the simulation.

    total_beds:
        Real annual regional bed count.

    is_compound_heat:
        Boolean array indicating compound heat days.

    seed:
        Random seed for reproducibility.
    """

    # -------------------------------
    # STEP 1: INITIALIZE SIMULATION
    # -------------------------------

    rng = np.random.default_rng(seed)

    n = len(dates)

    if total_beds <= 0:
        raise ValueError("total_beds must be greater than zero.")

    # If compound heat flags are not provided,
    # treat all days as non-compound days.
    if is_compound_heat is None:
        is_compound_heat = np.zeros(n, dtype=bool)
    else:
        is_compound_heat = np.asarray(
            is_compound_heat, dtype=bool
        )

        if len(is_compound_heat) != n:
            raise ValueError(
                "is_compound_heat must have the same "
                "length as dates."
            )

    # -------------------------------
    # STEP 2: SIMULATE OCCUPANCY
    # -------------------------------

    occupancy = rng.normal(
        BASE_OCCUPANCY_MEAN,
        BASE_OCCUPANCY_STD,
        size=n
    )

    # Reduce routine occupancy slightly on weekends.
    is_weekend = (
        pd.Series(dates)
        .dt.dayofweek
        .isin([5, 6])
        .values
    )

    occupancy += np.where(
        is_weekend,
        WEEKEND_OCCUPANCY_DELTA,
        0
    )

    # Increase occupancy on compound heat days.
    occupancy += np.where(
        is_compound_heat,
        COMPOUND_HEAT_OCCUPANCY_DELTA,
        0
    )

    # Keep occupancy within realistic simulation limits.
    occupancy = np.clip(
        occupancy,
        0.55,
        0.99
    )

    # -------------------------------
    # STEP 3: CALCULATE BEDS
    # -------------------------------

    occupied_beds = total_beds * occupancy

    available_beds = total_beds - occupied_beds

    # -------------------------------
    # STEP 4: CALCULATE OCCUPANCY-BASED
    #         ADDITIONAL BED REQUIREMENT
    # -------------------------------

    # Beds corresponding to the 85% planning threshold.
    threshold_beds = (
        total_beds * OCCUPANCY_THRESHOLD
    )

    # If occupied beds exceed the threshold,
    # calculate the number of beds above that threshold.
    occupancy_extra_beds = np.maximum(
        occupied_beds - threshold_beds,
        0
    )

    # -------------------------------
    # STEP 5: CALCULATE HEAT-BASED
    #         ADDITIONAL BED REQUIREMENT
    # -------------------------------

    # Additional demand is applied only on compound heat days.
    demand_surge_pct = np.where(
        is_compound_heat,
        HEAT_DEMAND_SURGE_PCT,
        0.0
    )

    heat_extra_beds = (
        total_beds * demand_surge_pct / 100
    )

    # -------------------------------
    # STEP 6: COMBINE BOTH CONDITIONS
    # -------------------------------

    # Combined planning estimate:
    # occupancy-based beds + heat-related beds.
    extra_beds_needed = np.ceil(
        occupancy_extra_beds + heat_extra_beds
    )

    # -------------------------------
    # STEP 7: CALCULATE NURSES
    # -------------------------------

    extra_nurses_needed = np.ceil(
        extra_beds_needed * NURSES_PER_EXTRA_BED
    )

    # -------------------------------
    # STEP 8: CALCULATE DOCTORS
    # -------------------------------

    extra_doctors_needed = np.ceil(
        extra_beds_needed * DOCTORS_PER_EXTRA_BED
    )

    # -------------------------------
    # STEP 9: RETURN RESULTS
    # -------------------------------

    return pd.DataFrame({
        "region": region,
        "date": dates,

        "total_beds_real": total_beds,

        "simulated_occupancy_pct": (
            occupancy * 100
        ).round(1),

        "simulated_occupied_beds": (
            occupied_beds
        ).round(0),

        "simulated_available_beds": (
            available_beds
        ).round(0),

        "is_compound_heat_day": is_compound_heat,

        "occupancy_extra_beds": (
            occupancy_extra_beds
        ).round(0),

        "heat_extra_beds": (
            heat_extra_beds
        ).round(0),

        "recommended_extra_beds": (
            extra_beds_needed
        ),

        "recommended_extra_nurses": (
            extra_nurses_needed
        ),

        "recommended_extra_doctors": (
            extra_doctors_needed
        ),
    })