from __future__ import annotations

from uk_leisure_intel.config import PipelineConfig
from uk_leisure_intel.schemas import PAYMENT_COLUMNS
from uk_leisure_intel.utils.io import collect_files, read_csv_rows
from uk_leisure_intel.utils.text import fy_from_date, match_alias, normalize_supplier, parse_date_guess

SOURCE_TYPE = "procurement"


def run(cfg: PipelineConfig) -> list[dict]:
    source_cfg = cfg.sources.get("procurement")
    if not source_cfg or not source_cfg.enabled:
        return []

    files = collect_files(source_cfg.local_globs)
    records: list[dict] = []

    for p in files:
        if p.suffix.lower() != ".csv":
            continue
        try:
            rows = read_csv_rows(p)
        except Exception:
            continue
        for row in rows:
            supplier = row.get("awarded supplier", row.get("supplier", row.get("contractor", "")))
            matched, score, alias = match_alias(str(supplier), cfg.operator_aliases + cfg.operators, cfg.min_fuzzy_score)
            if not matched:
                continue
            dt = parse_date_guess(str(row.get("award date", row.get("date", ""))))
            try:
                amount = float(str(row.get("contract value", row.get("value", "0"))).replace("£", "").replace(",", ""))
            except ValueError:
                amount = 0.0
            desc = str(row.get("description", row.get("title", "")))
            record = {
                "source_type": SOURCE_TYPE,
                "source_name": "Tender/Award Disclosure",
                "source_url": str(p),
                "document_name": p.name,
                "supplier_raw": supplier,
                "supplier_normalized": normalize_supplier(str(supplier)),
                "payment_date": dt.date().isoformat() if dt else "",
                "financial_year": fy_from_date(dt) if dt else "Unknown",
                "amount_gbp": amount,
                "description": desc,
                "matched_alias": alias or "",
                "alias_score": score,
                "classification": "Capital / One-off",
                "classification_reason": "Procurement notice value is often whole-contract disclosure",
                "confidence": 0.6,
            }
            records.append({k: record.get(k, "") for k in PAYMENT_COLUMNS})

    return records
