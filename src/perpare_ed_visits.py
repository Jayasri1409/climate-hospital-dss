
import pandas as pd
from pathlib import Path

# ----------------------------------------
# STEP 1: FIND THE PROJECT DATA FOLDER
# ----------------------------------------

# This file is inside src.
# The data folder is one level above src.

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"

ED_FILE = DATA_DIR / "ed_visits.csv"
MAPPING_FILE = DATA_DIR / "dept_to_region.csv"

OUTPUT_FILE = DATA_DIR / "regional_daily_ed_visits.csv"


# ----------------------------------------
# STEP 2: LOAD THE CSV FILES
# ----------------------------------------

ed = pd.read_csv(ED_FILE)
mapping = pd.read_csv(MAPPING_FILE)

print("ED data shape:", ed.shape)
print("Mapping data shape:", mapping.shape)

print("\nED columns:")
print(ed.columns.tolist())

print("\nMapping columns:")
print(mapping.columns.tolist())


# ----------------------------------------
# STEP 3: CLEAN COLUMN NAMES
# ----------------------------------------

ed.columns = ed.columns.str.strip()
mapping.columns = mapping.columns.str.strip()

# Remove extra spaces from department names/codes.
ed["dep"] = ed["dep"].astype(str).str.strip()
mapping["dep"] = mapping["dep"].astype(str).str.strip()

mapping["region"] = mapping["region"].astype(str).str.strip()


# ----------------------------------------
# STEP 4: CONVERT DEPARTMENT CODES
# ----------------------------------------

# Convert department codes to uppercase.
# This also handles codes such as 2A and 2B.

ed["dep"] = ed["dep"].str.upper()
mapping["dep"] = mapping["dep"].str.upper()


# ----------------------------------------
# STEP 5: CONVERT DATE AND VISITS
# ----------------------------------------

# Your example dates use day-month-year format.
ed["date"] = pd.to_datetime(
    ed["date"],
    dayfirst=True,
    errors="coerce"
)

ed["nb_passages"] = pd.to_numeric(
    ed["nb_passages"],
    errors="coerce"
)

# Remove rows with missing essential values.
ed = ed.dropna(
    subset=["date", "dep", "nb_passages"]
)


# ----------------------------------------
# STEP 6: CHECK DEPARTMENT MAPPING
# ----------------------------------------

# Each department should map to one region.

duplicate_deps = mapping[
    mapping.duplicated("dep", keep=False)
]

if not duplicate_deps.empty:
    raise ValueError(
        "Some departments appear more than once "
        "in dept_to_region.csv. Check the mapping."
    )

# Identify ED departments missing from the mapping.

ed_deps = set(ed["dep"].unique())
mapped_deps = set(mapping["dep"].unique())

unmapped_deps = sorted(ed_deps - mapped_deps)

print("\nUnmapped departments:", unmapped_deps)

if unmapped_deps:
    print(
        "WARNING: Some ED departments do not have "
        "a region mapping."
    )


# ----------------------------------------
# STEP 7: MERGE ED DATA WITH REGION MAPPING
# ----------------------------------------

merged = ed.merge(
    mapping[["dep", "region"]],
    on="dep",
    how="left",
    validate="many_to_one"
)

# Keep only records with a known region.
merged = merged.dropna(subset=["region"])


# ----------------------------------------
# STEP 8: AGGREGATE DAILY ED VISITS
# ----------------------------------------

# Add together all department visits belonging
# to the same region on the same date.

regional_daily = (
    merged.groupby(
        ["date", "region"],
        as_index=False
    )
    .agg(
        daily_ed_visits=("nb_passages", "sum"),
        departments_reporting=("dep", "nunique")
    )
)

# Round the total for readability.
regional_daily["daily_ed_visits"] = (
    regional_daily["daily_ed_visits"].round(0)
)

# Sort by region and date.
regional_daily = regional_daily.sort_values(
    ["region", "date"]
)


# ----------------------------------------
# STEP 9: SAVE THE REGIONAL DATASET
# ----------------------------------------

regional_daily.to_csv(
    OUTPUT_FILE,
    index=False,
    date_format="%Y-%m-%d"
)

print("\nRegional daily ED data created!")

print("Output file:", OUTPUT_FILE)

print("\nFirst 10 rows:")
print(regional_daily.head(10))

print("\nNumber of regions:")
print(regional_daily["region"].nunique())

print("\nNumber of regional daily records:")
print(len(regional_daily))

print("\nDate range:")
print(
    regional_daily["date"].min(),
    "to",
    regional_daily["date"].max()
)