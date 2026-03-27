# Asset Taxonomy Workbook Generator

This repository now includes a Python utility to generate a structured Excel workbook for asset taxonomy and to validate raw site uploads.

## Files
- `scripts/asset_taxonomy_tool.py` — generator + validator CLI.
- `output/asset_taxonomy_workbook.xlsx` — generated workbook path (default).
- `output/asset_naming_rules.md` — generated rules document path (default).
- `output/validation_report.csv` — generated compliance report path (default).

## Install dependency
```bash
pip install openpyxl
```

## Generate workbook and naming rules
```bash
python scripts/asset_taxonomy_tool.py generate
```

## Validate a raw upload
```bash
python scripts/asset_taxonomy_tool.py validate \
  --taxonomy output/asset_taxonomy_workbook.xlsx \
  --raw your_raw_register.xlsx \
  --output output/validation_report.csv
```

## Workbook tabs generated
- Domains
- Categories
- Types
- Manufacturers
- Contractors
- Site Upload Template
- Mapping Review
- Data Validation Lists (hidden)

## Notes
The `Site Upload Template` tab includes list-based dropdown validations for domain, category, type, manufacturer, contractor, and status using named ranges from `Data Validation Lists`.
