# UK Leisure Procurement OSINT Pipeline

A lightweight, local-first intelligence pipeline for tracking UK leisure procurement and risk signals across:

- council cabinet papers
- budget reports
- planning applications
- Find a Tender notices
- council payments data

## What this project does

Given a **council name** and one or more **operator names**, the pipeline:

1. Loads a configurable source list (`URLs`, file paths, and globs).
2. Collects documents and extracts references/evidence snippets.
3. Classifies each finding into one of these signal types:
   - procurement signal
   - capital investment signal
   - financial distress signal
   - political risk signal
   - decarbonisation or energy signal
4. Produces:
   - `evidence_log.csv`
   - `summary_briefing.md`
   - `risk_opportunity_scorecard.csv`
   - `risk_opportunity_scorecard.md`

All findings keep source URL/path and document title for traceability.

---

## Project structure

```text
uk_leisure_intel/
├── config/
│   └── sources.example.yaml
├── data/
│   ├── input/
│   │   └── saved/
│   └── output/
├── scripts/
│   └── run_pipeline.py
└── src/intel_pipeline/
    ├── automation_placeholders.py
    ├── classifier.py
    ├── cli.py
    ├── collectors.py
    ├── config_loader.py
    ├── extractors.py
    ├── models.py
    ├── reporters.py
    └── scoring.py
```

---

## Quickstart

### 1) Install dependencies

```bash
cd uk_leisure_intel
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure sources

Copy and edit the sample config:

```bash
cp config/sources.example.yaml config/sources.yaml
```

Then update URLs and file locations.

### 3) Add any saved documents

Put local files in `data/input/saved/` (or point to other paths/globs in config).

### 4) Run

```bash
python scripts/run_pipeline.py \
  --council "Birmingham City Council" \
  --operators "Places Leisure" "Everyone Active" \
  --config config/sources.yaml \
  --output-dir data/output
```

---

## Config schema

`config/sources.yaml` uses this shape:

```yaml
sources:
  - name: "Example council cabinet"
    type: "url"
    value: "https://www.example.gov.uk/cabinet"
    enabled: true

  - name: "Local saved docs"
    type: "glob"
    value: "data/input/saved/**/*"
    enabled: true

  - name: "Payments CSV"
    type: "file"
    value: "data/input/payments.csv"
    enabled: true
```

Supported types:

- `url`
- `file`
- `glob`

---

## Extensibility placeholders

See `src/intel_pipeline/automation_placeholders.py` for explicit hooks to add:

- Browser automation (Playwright/Selenium)
- Find a Tender API integration
- Planning portal API integration
- Council open-data API integration

---

## Notes

- This is intentionally lightweight and explainable.
- Keyword rules are in `classifier.py` and can be tuned for your region/council style.
- PDFs are optional via `pypdf`; if unavailable, the pipeline skips PDF text extraction gracefully.
