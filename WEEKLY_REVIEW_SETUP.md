# Weekly Energy Site Review App (Minimal Streamlit)

## What this is
A single-file Streamlit dashboard focused on weekly triage of the **top 10 highest-cost unresolved site issues**.

## Features
- Reads a master **CSV or Excel** file.
- Filters by **region**, **issue type**, and **status**.
- Shows top 10 sites by **estimated cost impact**.
- Calculates **unresolved age (days)** and **days since last update**.
- Highlights stale records:
  - **7+ days** since update (yellow)
  - **14+ days** since update (red)
- Shows **notes history** for each selected site.
- Exports:
  - Markdown weekly briefing (`.md`)
  - PowerPoint-friendly text summary (`.txt`)

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Then open the local URL shown by Streamlit (usually `http://localhost:8501`).

## Input schema (required columns)
Your CSV/Excel must include:
- `site_id`
- `site_name`
- `region`
- `issue_type`
- `status`
- `estimated_cost_impact`
- `opened_date` (e.g., `2026-03-20`)
- `last_update_date` (e.g., `2026-03-25`)
- `notes_history` (free text, optionally separated by `|`)

## Sample data
Use `data/sample_sites.csv` for a ready-to-run example.
- In the sidebar, keep **Use sample data** turned on.
- Or upload your own CSV/Excel.

## Keep it brutally simple
- No database required.
- No user accounts.
- No background jobs.
- One dashboard, one weekly workflow.
