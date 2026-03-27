# Energy Anomaly Tracker (UK Leisure Sites)

This project helps you combine messy CSV/Excel anomaly exports into a clean master dataset.

It is designed for non-developers and supports:
- Site name standardisation (including fuzzy matching)
- MPAN and MPRN formatting cleanup
- Issue classification into: **Waste, Times, Baseload, Data Gap, Other**
- A confidence score for fuzzy site name matching
- Easy-to-edit YAML config rules

---

## Project Structure

```text
energy_anomaly_tracker/
├── config.yaml
├── requirements.txt
├── README.md
├── src/
│   └── anomaly_tracker.py
└── data/
    ├── input/
    │   └── sample_anomalies.csv
    └── output/
```

---

## 1) Setup

From inside the `energy_anomaly_tracker` folder:

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 2) Add your files

Put your CSV/Excel files in:

- `data/input/`

Supported file types:
- `.csv`
- `.xlsx`
- `.xls`

---

## 3) Run the tool

```bash
python src/anomaly_tracker.py --input-dir data/input --output-dir data/output --config config.yaml
```

If successful, you will get:

1. `data/output/cleaned_master.csv`
2. `data/output/issues_needing_review.csv`
3. `data/output/data_quality_report.md`

---

## 4) What each output file means

### cleaned_master.csv
Main clean dataset with:
- raw and standardised site names
- raw and standardised MPAN/MPRN
- issue category
- fuzzy match confidence
- source file and source row number

### issues_needing_review.csv
Subset of rows likely needing human check, e.g.:
- low site match confidence
- issue category fell into `Other`
- missing site name

### data_quality_report.md
Simple markdown summary of:
- rows processed
- records flagged for review
- issue category counts
- file-level record counts

---

## 5) Edit business rules (no coding needed)

Open `config.yaml` and update:

- `canonical_site_names`: your official site names
- `manual_site_mappings`: known bad names to force-map
- `site_match_threshold`: fuzzy acceptance threshold (0-100)
- `column_aliases`: possible source column names
- `issue_category_rules`: keywords for each issue category

Tip:
- Increase threshold if you want stricter matching.
- Add more keywords to improve issue categorisation.

---

## Common Troubleshooting

- **No files found**
  - Check that your files are in `data/input/`.
- **Too many rows in review file**
  - Add more manual mappings and canonical names.
  - Lower threshold slightly (e.g., 85 to 80).
- **Issue categories not useful**
  - Add your own terms to `issue_category_rules` in `config.yaml`.

---

## Notes

- The script keeps raw values in separate columns so you always have auditability.
- This tool runs fully locally, so your data stays on your machine.
