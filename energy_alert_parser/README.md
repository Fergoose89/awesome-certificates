# Energy Alert Email Parser

A local parser that converts copied email text or `.eml` files into structured records with confidence scoring.

## Extracted fields
- Site code
- Site name
- MPAN or MPRN
- Issue type
- First observed date
- Daily cost
- Rank
- Narrative summary
- Source email subject
- Source email date

## Features
- Handles wording variations through editable regex rules (`rules.json`)
- Parses plain text and `.eml` files
- Exports CSV and JSON
- Flags low-confidence records for review (`needs_review = true`)
- Includes tests and sample input formats

## Quick start
```bash
cd energy_alert_parser
python3 cli.py --text samples/alert_format_a.txt samples/alert_format_b.txt
python3 cli.py samples/alert_email.eml
```

Outputs are written by default to:
- `outputs/parsed_records.json`
- `outputs/parsed_records.csv`

## Editable parsing rules
Edit `rules.json`:
- `field_patterns`: ordered regex patterns per field
- `subject_issue_hints`: fallback mapping from subject keywords to issue types
- `confidence_threshold`: records below this score are marked `needs_review`

## Run tests
```bash
cd energy_alert_parser
python3 -m pytest -q
```

## Connecting later to SharePoint / Power Automate
1. Keep parser output in JSON or CSV in a known folder.
2. Use Power Automate "When a file is created" (OneDrive/SharePoint folder).
3. Add a "Parse JSON" step using the parser JSON schema.
4. Route:
   - `needs_review = true` -> Planner task for analyst review
   - otherwise -> "Create item" in SharePoint list (or insert into SQL)
5. Recommended SharePoint columns:
   - Title (site code + issue type)
   - SiteCode, SiteName, MPAN_MPRN, IssueType
   - FirstObservedDate (date), DailyCost (number), Rank (text)
   - NarrativeSummary (multi-line)
   - SourceSubject, SourceDate
   - Confidence (number), NeedsReview (yes/no)

This design keeps parsing logic local and deterministic while making downstream automation low-code.
