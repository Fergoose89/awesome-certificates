from __future__ import annotations

import re
from pathlib import Path

from uk_leisure_intel.config import PipelineConfig
from uk_leisure_intel.schemas import PAYMENT_COLUMNS
from uk_leisure_intel.utils.io import collect_files, read_csv_rows
from uk_leisure_intel.utils.text import fy_from_date, match_alias, normalize_supplier, parse_date_guess

SOURCE_TYPE = "council_documents"
AMOUNT_RE = re.compile(r"(?:£|GBP)?\s?([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)")


def run(cfg: PipelineConfig) -> list[dict]:
    source_cfg = cfg.sources.get("council_docs")
    if not source_cfg or not source_cfg.enabled:
        return []

    files = collect_files(source_cfg.local_globs)
    records: list[dict] = []

    for p in files:
        if p.suffix.lower() == ".csv":
            try:
                rows = read_csv_rows(p)
            except Exception:
                continue
            for row in rows:
                supplier = str(row.get("Supplier", row.get("supplier", "")))
                matched, score, alias = match_alias(supplier, cfg.operator_aliases + cfg.operators, cfg.min_fuzzy_score)
                if not matched:
                    continue
                dt = parse_date_guess(str(row.get("Date", row.get("date", ""))))
                try:
                    amount = float(str(row.get("Amount", row.get("amount", "0"))).replace("£", "").replace(",", ""))
                except ValueError:
                    amount = 0.0
                desc = str(row.get("Description", row.get("description", "")))
                record = {
                    "source_type": SOURCE_TYPE,
                    "source_name": "Council Cabinet/Budget Document",
                    "source_url": str(p),
                    "document_name": p.name,
                    "supplier_raw": supplier,
                    "supplier_normalized": normalize_supplier(supplier),
                    "payment_date": dt.date().isoformat() if dt else "",
                    "financial_year": fy_from_date(dt) if dt else "Unknown",
                    "amount_gbp": amount,
                    "description": desc,
                    "matched_alias": alias or "",
                    "alias_score": score,
                    "classification": "Unknown",
                    "classification_reason": "Potential financial mention in council document",
                    "confidence": 0.55,
                }
                records.append({k: record.get(k, "") for k in PAYMENT_COLUMNS})
        elif p.suffix.lower() == ".txt":
            text = p.read_text(encoding="utf-8", errors="ignore")
            for line in text.splitlines():
                matched, score, alias = match_alias(line, cfg.operator_aliases + cfg.operators, cfg.min_fuzzy_score)
                if not matched:
                    continue
                amount_m = AMOUNT_RE.search(line)
                if not amount_m:
                    continue
                amount = float(amount_m.group(1).replace(",", ""))
                record = {
                    "source_type": SOURCE_TYPE,
                    "source_name": "Council Text Report",
                    "source_url": str(p),
                    "document_name": p.name,
                    "supplier_raw": alias or "Operator Mention",
                    "supplier_normalized": normalize_supplier(alias or "Operator Mention"),
                    "payment_date": "",
                    "financial_year": "Unknown",
                    "amount_gbp": amount,
                    "description": line.strip(),
                    "matched_alias": alias or "",
                    "alias_score": score,
                    "classification": "Unknown",
                    "classification_reason": "Potential financial mention in council text document",
                    "confidence": 0.4,
                }
                records.append({k: record.get(k, "") for k in PAYMENT_COLUMNS})

    return records
