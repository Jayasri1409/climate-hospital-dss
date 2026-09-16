# Data Dictionary

| File | Rows | Source | Description |
|---|---|---|---|
| `annual_panel.csv` | 117 | Santé publique France + Eurostat | Region-year panel, 2016-2024, used for the annual demand model |
| `temperature.csv` | ~298k | Météo-France | Daily min/max/avg temperature, 96 mainland departments |
| `ed_visits.csv` | ~248k | Santé publique France (séries longues) | Daily total ED visits ("passages urgences"), 98 departments, 2017-2023 |
| `dept_heatwave_thresholds.csv` | 96 | Derived | Each department's own 90th-percentile summer tmax, used to define "heatwave day" |
| `heat_analysis_summary.csv` | 5 | Derived | Validated event-study results (heatwave day / lag effects) |
| `sample_daily_series_paris_2022.csv` | 92 | Derived | Small real sample for the Heat Analysis chart |
| `dss_recommendations_2016_2024.csv` | 117 | Derived | Full annual model output, all region-years |
| `model_comparison.csv`, `model_comparison_extended.csv`, `daily_model_comparison.csv` | - | Derived | All model validation results, reported honestly including what didn't work |

Note: `temperature.csv` and `ed_visits.csv` are large (~19MB combined) but are the real
underlying data — the daily lag-effect finding cannot be reproduced without them.
