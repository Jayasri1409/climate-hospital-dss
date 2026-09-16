# Climate-Aware Hospital Resource Planning DSS

A two-tier decision support system: an annual/regional model for seasonal capacity
planning, and a validated daily lag-effect model for short-term operational forecasting
using real live weather data.

## Structure
- `app.py` + `pages/` — Streamlit multipage dashboard
- `src/` — core logic (lag predictor, live forecast, risk engine, data processing)
- `models/` — trained annual model (no daily model file — the daily approach is
  rule-based/transparent, not a fitted ML model; see Model Performance page for why)
- `data/` — see `data/README.md` for full data dictionary

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
Push to GitHub, connect the repo on share.streamlit.io, main file: `app.py`.
