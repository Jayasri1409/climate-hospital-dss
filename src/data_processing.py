"""
Climate-Aware Hospital Resource Planning DSS
Data cleaning + merging pipeline — ANNUAL panel (data/annual_panel.csv)

NOTE: This script documents how data/annual_panel.csv was originally built, for
reproducibility. Its raw inputs (the 4 individual Santé publique France canicule
CSVs + the Eurostat beds spreadsheet) are NOT included in this repo to avoid
bloating it with intermediate files — data/annual_panel.csv is the final output
and is what the app actually uses. To re-run this script from scratch, re-download
the raw files from odisse.santepubliquefrance.fr (search "canicule") and Eurostat's
hlth_rs_bdsrg2 dataset, and update the RAW path below.

For the DAILY-resolution pipeline (temperature.csv + ed_visits.csv -> the event-study
analysis and lag_predictor.py), see the Heat Analysis page's precomputed summary in
data/heat_analysis_summary.csv - that merge logic is simpler and is documented inline
on the Heat Analysis page itself rather than as a separate script.

Original script, paths unchanged below (will not run as-is in this repo — see note above):
"""

import pandas as pd
import numpy as np
import os

RAW = "/mnt/user-data/uploads"
OUT = "/home/claude/hospital_dss/cleaned"
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. CLIMATE / HEALTH SURVEILLANCE DATA (Santé publique France, région level)
# ---------------------------------------------------------------------------

def load_csv(fname, year_col):
    df = pd.read_csv(os.path.join(RAW, fname), encoding="utf-8-sig")
    df = df.rename(columns={year_col: "year", "Région": "region", "Région Code": "region_code"})
    df["region"] = df["region"].str.strip()
    return df

severity = load_csv("canicules-severite-region.csv", "Année")
severity = severity.rename(columns={"Sévérité": "heatwave_severity"})

pop_exposed = load_csv("canicules-taille-de-la-population-concernee-par-une-canicule-region.csv", "Année")
pop_exposed = pop_exposed.rename(columns={"Population exposée": "population_exposed"})

excess_deaths = load_csv("canicules-exces-de-deces-pendant-les-vagues-de-chaleur-region.csv", "Année")
excess_deaths = excess_deaths.rename(columns={
    "Nombre de décès en excès": "excess_deaths",
    "Pourcentage de décès en excès": "excess_deaths_pct",
})

attrib_deaths = load_csv(
    "canicules-deces-attribuables-a-la-chaleur-pendant-lete-et-pendant-les-vagues-de-chaleur-region.csv",
    "Annee",
)
attrib_deaths = attrib_deaths.rename(columns={
    "Nombre de décès attribuable à la chaleur pendant la période de surveillance": "attrib_deaths_summer",
    "Nombre de décès attribuable à la chaleur pendant les canicules": "attrib_deaths_heatwave",
    "Fraction de décès attribuable à la chaleur pendant la période de surveillance": "attrib_deaths_summer_pct",
    "Fraction de décès attribuable  à la chaleur pendant les canicules": "attrib_deaths_heatwave_pct",
})

# excess_deaths and attrib_deaths are broken down by age class ("Classe d'âge").
# For a region+year panel we keep the "Tous Ages" (all-ages) rows — the age
# breakdown is retained separately in case a later, age-stratified model is wanted.
excess_deaths_all = excess_deaths[excess_deaths["Classe d'âge"] == "Tous Ages"].copy()
attrib_deaths_all = attrib_deaths[attrib_deaths["Classe d'âge"] == "Tous Ages"].copy()

excess_deaths_all.to_csv(f"{OUT}/excess_deaths_by_age_raw.csv", index=False)
attrib_deaths_all.to_csv(f"{OUT}/attrib_deaths_by_age_raw.csv", index=False)
# full age-stratified versions too, for reference
excess_deaths.to_csv(f"{OUT}/excess_deaths_all_ages_breakdown.csv", index=False)
attrib_deaths.to_csv(f"{OUT}/attrib_deaths_all_ages_breakdown.csv", index=False)

# Merge the four climate/health indicators on region + year
climate = severity[["year", "region", "region_code", "heatwave_severity"]].merge(
    pop_exposed[["year", "region", "population_exposed"]], on=["year", "region"], how="outer"
).merge(
    excess_deaths_all[["year", "region", "excess_deaths", "excess_deaths_pct"]],
    on=["year", "region"], how="outer"
).merge(
    attrib_deaths_all[["year", "region",
                        "attrib_deaths_summer", "attrib_deaths_summer_pct",
                        "attrib_deaths_heatwave", "attrib_deaths_heatwave_pct"]],
    on=["year", "region"], how="outer"
)

climate = climate.sort_values(["region", "year"]).reset_index(drop=True)
climate.to_csv(f"{OUT}/climate_health_region_year.csv", index=False)

print("=== Climate/health panel ===")
print(climate.shape)
print(climate["region"].value_counts())
print(climate.isna().sum())

# ---------------------------------------------------------------------------
# 2. HOSPITAL CAPACITY DATA (Eurostat, old NUTS2 -> new region mapping)
# ---------------------------------------------------------------------------

xl = pd.read_excel(f"{RAW}/hlth_rs_bdsrg2_defaultview_spreadsheet.xlsx", sheet_name="Sheet 1", header=None)
header_row = xl.iloc[7]
year_cols = {int(header_row[c]): c for c in range(1, xl.shape[1]) if pd.notna(header_row[c])}
data = xl.iloc[8:].reset_index(drop=True)
data = data.rename(columns={0: "geo"})
data["geo"] = data["geo"].astype(str).str.strip()

# Old (pre-2016) French NUTS2 regions -> new (post-2016) French regions
OLD_TO_NEW = {
    "Ile de France": "Île-de-France",
    "Centre — Val de Loire": "Centre-Val de Loire",
    "Bourgogne": "Bourgogne et Franche-Comté",
    "Franche-Comté": "Bourgogne et Franche-Comté",
    "Basse-Normandie": "Normandie",
    "Haute-Normandie": "Normandie",
    "Nord-Pas de Calais": "Hauts-de-France",
    "Picardie": "Hauts-de-France",
    "Alsace": "Grand Est",
    "Champagne-Ardenne": "Grand Est",
    "Lorraine": "Grand Est",
    "Pays de la Loire": "Pays de la Loire",
    "Bretagne": "Bretagne",
    "Aquitaine": "Nouvelle Aquitaine",
    "Limousin": "Nouvelle Aquitaine",
    "Poitou-Charentes": "Nouvelle Aquitaine",
    "Languedoc-Roussillon": "Occitanie",
    "Midi-Pyrénées": "Occitanie",
    "Auvergne": "Auvergne et Rhône-Alpes",
    "Rhône-Alpes": "Auvergne et Rhône-Alpes",
    "Provence-Alpes-Côte d\u2019Azur": "Provence-Alpes-Côte d'Azur",
    "Corse": "Corse",
}

data["new_region"] = data["geo"].map(OLD_TO_NEW)
france_rows = data[data["new_region"].notna()].copy()

records = []
for _, row in france_rows.iterrows():
    for yr, col in year_cols.items():
        val = row[col]
        if isinstance(val, str) and val.strip() == ":":
            val = np.nan
        records.append({"year": yr, "old_region": row["geo"], "new_region": row["new_region"], "beds": val})

beds_long = pd.DataFrame(records)
beds_long["beds"] = pd.to_numeric(beds_long["beds"], errors="coerce")

capacity = (
    beds_long.groupby(["new_region", "year"], as_index=False)["beds"]
    .sum(min_count=1)
    .rename(columns={"new_region": "region", "beds": "hospital_beds"})
)
capacity = capacity.sort_values(["region", "year"]).reset_index(drop=True)
capacity.to_csv(f"{OUT}/capacity_region_year.csv", index=False)

print("\n=== Capacity panel (mapped to new regions) ===")
print(capacity.shape)
print(capacity["region"].unique())
print(capacity.isna().sum())

# ---------------------------------------------------------------------------
# 3. MASTER PANEL — climate + capacity, with derived indicators
# ---------------------------------------------------------------------------

master = climate.merge(capacity, on=["region", "year"], how="left")

# Derived indicators useful for the demand-model / DSS logic
pop_safe = master["population_exposed"].replace(0, np.nan)
master["deaths_per_100k_exposed"] = master["attrib_deaths_heatwave"] / pop_safe * 100_000
master["beds_per_100k_exposed"] = master["hospital_beds"] / pop_safe * 100_000

master = master.sort_values(["region", "year"]).reset_index(drop=True)
master.to_csv(f"{OUT}/master_panel.csv", index=False)

print("\n=== Master panel ===")
print(master.shape)
print(master.head(10))
print("\nYear range with BOTH climate and capacity data:",
      master.dropna(subset=["heatwave_severity", "hospital_beds"])["year"].min(),
      "-",
      master.dropna(subset=["heatwave_severity", "hospital_beds"])["year"].max())
print("\nMissingness (%):")
print((master.isna().mean() * 100).round(1))

# ---------------------------------------------------------------------------
# 4. MODELING-READY SUBSET
#    Restricted to years where heatwave severity AND hospital beds both exist
#    (2016-2024) -- this is the panel to actually fit a demand model on.
# ---------------------------------------------------------------------------

modeling = master[(master["year"] >= 2016) & (master["year"] <= 2024)].copy()
modeling = modeling.sort_values(["region", "year"]).reset_index(drop=True)
modeling.to_csv(f"{OUT}/modeling_panel_2016_2024.csv", index=False)

print("\n=== Modeling-ready subset (2016-2024) ===")
print(modeling.shape)
print("Missingness (%):")
print((modeling.isna().mean() * 100).round(1))
