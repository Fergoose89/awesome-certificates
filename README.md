# UK Leisure Contract Financial Intelligence Pipeline

A local, reproducible Python pipeline for reconstructing management fees, subsidies, and contract signals between UK councils and leisure operators.

## Architecture first (then build)

### v1 architecture

1. **Config layer** (`config/sample_config.json`)
2. **Source collectors** (modular):
   - `sources/transparency.py`
   - `sources/council_docs.py`
   - `sources/procurement.py`
   - `sources/operator_financials.py`
3. **Analysis layer**:
   - `analysis/classification.py`
   - `analysis/patterns.py`
4. **Output layer**:
   - `output/reporting.py`
5. **CLI entrypoint**:
   - `python -m uk_leisure_intel.cli --config ...`

This keeps each source isolated while using a shared record schema and traceability fields.

## First working version (included)

### Inputs supported
- Local CSV files (all modules)
- Local TXT documents for council-doc text extraction
- Optional live URL fetch for transparency files (uses stdlib URL download)

### Core logic delivered
- Supplier alias fuzzy matching (stdlib `difflib`)
- Aggregation and trend detection by month/year
- Payment classification:
  - Management Fee
  - Operating Subsidy
  - Emergency Support / Bailout
  - Energy Support
  - Capital / One-off
  - Unknown
- Contract model reconstruction:
  - direction of likely payment flow
  - subsidy estimate
  - stability signal

### Outputs delivered
- `reports/output/payments_classified.csv`
- `reports/output/financial_summary.csv`
- `reports/output/evidence_log.csv`
- `reports/output/intelligence_report.md`
- `reports/output/model_summary.json`

## Project structure

```
.
├── config/sample_config.json
├── data/raw/{transparency,council_docs,procurement,operator_financials}
├── reports/output
├── scripts/run_pipeline.sh
└── src/uk_leisure_intel/
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run

```bash
scripts/run_pipeline.sh
# or
python -m uk_leisure_intel.cli --config config/sample_config.json
```

## Extend

- Add new scrapers/parsers under `src/uk_leisure_intel/sources/`.
- Add council-specific table mappings where field names differ.
- Add manual review workflow for all `Unknown` classifications.

## Important caveats

- This is a decision-support tool, not an accounting truth source.
- Procurement value disclosures are not always annual management fees.
- Poor-quality source documents should be marked low confidence and reviewed.
