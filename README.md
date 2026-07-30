# Climate-Aware Hospital Resource Planning DSS — project scaffold

## What's in here

```
app.py              Streamlit dashboard (the DSS itself)
requirements.txt     Python dependencies
data/                Seed CSVs — swap for your real cleaned/merged dataset
website/index.html   Standalone presentation site (project overview, links to the live dashboard)
```

## 1. Push this to GitHub

```bash
git init
git add .
git commit -m "Initial DSS scaffold"
gh repo create climate-hospital-dss --public --source=. --push
# or create the repo on github.com and:
# git remote add origin https://github.com/<you>/climate-hospital-dss.git
# git push -u origin main
```

## 2. Deploy the dashboard (Streamlit Community Cloud — free)

1. Go to https://share.streamlit.io and sign in with GitHub.
2. Click "New app", pick this repo, branch `main`, main file `app.py`.
3. Deploy. You'll get a public URL like `https://<you>-climate-hospital-dss.streamlit.app`.
4. Update the "Open dashboard" button link in `website/index.html` to that URL.

## 3. Deploy the website (GitHub Pages — free)

1. In the repo, go to Settings → Pages.
2. Source: "Deploy from a branch", branch `main`, folder `/website` (or move `index.html` to repo root if GitHub Pages doesn't offer a subfolder option on your plan — in that case set folder to `/root` and keep index.html at the top level instead of inside `website/`).
3. Save. Your site will be live at `https://<you>.github.io/climate-hospital-dss/`.

## 4. Swap in your real data

Once you've cleaned your downloaded datasets:

1. Replace the files in `data/` with your real merged climate + demand + capacity CSVs.
2. Update `load_demand_climate()`, `load_capacity()` in `app.py` to match your real column names.
3. Replace `REGION_SUMMARY` and `estimate_requirements()` with your trained model's actual output
   (or have the app call your model directly if it's fast enough to run live).
4. Re-deploy — Streamlit Cloud auto-redeploys on every GitHub push.

## Notes

- The dashboard currently uses a placeholder scaling rule for resource needs, not a trained regression model — this is flagged in the app itself and should be replaced once your methodology (Step 2 of the project) is done.
- The website's data-source links and stat cards use real, sourced figures gathered during project research — update the GitHub/dashboard links once deployed.
