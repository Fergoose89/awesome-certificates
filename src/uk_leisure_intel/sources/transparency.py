from __future__ import annotations

from pathlib import Path

from uk_leisure_intel.config import PipelineConfig
from uk_leisure_intel.schemas import PAYMENT_COLUMNS
from uk_leisure_intel.sources.common import fetch_url
from uk_leisure_intel.utils.io import collect_files, read_csv_rows
from uk_leisure_intel.utils.text import fy_from_date, match_alias, normalize_supplier, parse_date_guess

SOURCE_TYPE = "council_transparency"


def _pick_key(row: dict, options: list[str]) -> str | None:
    lower_map = {k.lower().strip(): k for k in row.keys()}
    for option in options:
        if option in lower_map:
            return lower_map[option]
    return None


def run(cfg: PipelineConfig) -> list[dict]:
    source_cfg = cfg.sources.get("transparency")
    if not source_cfg or not source_cfg.enabled:
        return []

    files = collect_files(source_cfg.local_globs)
    raw_dir = Path(cfg.data_dir) / "raw" / "transparency"
    if source_cfg.mode in {"live", "local_or_live"}:
        for url in source_cfg.urls:
            try:
                files.append(fetch_url(url, raw_dir))
            except Exception:
                pass

    records: list[dict] = []
    for file_path in files:
        if file_path.suffix.lower() != ".csv":
            continue
        try:
            rows = read_csv_rows(file_path)
        except Exception:
            continue
        if not rows:
            continue

        supplier_col = _pick_key(rows[0], ["supplier", "creditor", "payee", "beneficiary"])
        amount_col = _pick_key(rows[0], ["amount", "amount paid", "net amount", "gross amount", "value"])
        date_col = _pick_key(rows[0], ["date", "payment date", "transaction date"])
        desc_col = _pick_key(rows[0], ["description", "expense area", "details", "narrative"])
        if not supplier_col or not amount_col:
            continue

        for row in rows:
            supplier = str(row.get(supplier_col, "")).strip()
            matched, score, alias = match_alias(supplier, cfg.operator_aliases + cfg.operators, cfg.min_fuzzy_score)
            if not matched:
                continue
            try:
                amount = float(str(row.get(amount_col, "0")).replace("£", "").replace(",", ""))
            except ValueError:
                continue
            dt = parse_date_guess(str(row.get(date_col, ""))) if date_col else None
            record = {
                "source_type": SOURCE_TYPE,
                "source_name": "Council Transparency Payment Export",
                "source_url": str(file_path),
                "document_name": file_path.name,
                "supplier_raw": supplier,
                "supplier_normalized": normalize_supplier(supplier),
                "payment_date": dt.date().isoformat() if dt else "",
                "financial_year": fy_from_date(dt) if dt else "Unknown",
                "amount_gbp": amount,
                "description": str(row.get(desc_col, "")) if desc_col else "",
                "matched_alias": alias or "",
                "alias_score": score,
                "classification": "Unknown",
                "classification_reason": "Unclassified on ingest",
                "confidence": 0.6,
            }
            records.append({k: record.get(k, "") for k in PAYMENT_COLUMNS})

    return records
