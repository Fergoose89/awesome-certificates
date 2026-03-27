from __future__ import annotations

from uk_leisure_intel.config import PipelineConfig
from uk_leisure_intel.schemas import PAYMENT_COLUMNS
from uk_leisure_intel.utils.io import collect_files, read_csv_rows
from uk_leisure_intel.utils.text import normalize_supplier

SOURCE_TYPE = "operator_financials"


def run(cfg: PipelineConfig) -> list[dict]:
    source_cfg = cfg.sources.get("operator_financials")
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
            entity = str(row.get("entity", row.get("operator", cfg.operators[0] if cfg.operators else "operator")))
            period = str(row.get("period", "Unknown"))
            metric = str(row.get("metric", "unknown_metric"))
            value = row.get("value", "0")
            try:
                amount = float(str(value).replace(",", ""))
            except ValueError:
                amount = 0.0
            record = {
                "source_type": SOURCE_TYPE,
                "source_name": "Operator Financial Filing",
                "source_url": str(p),
                "document_name": p.name,
                "supplier_raw": entity,
                "supplier_normalized": normalize_supplier(entity),
                "payment_date": "",
                "financial_year": period,
                "amount_gbp": amount,
                "description": f"{metric} from filing",
                "matched_alias": entity,
                "alias_score": 100,
                "classification": "Unknown",
                "classification_reason": "Context metric from Companies House/charity filing",
                "confidence": 0.5,
            }
            records.append({k: record.get(k, "") for k in PAYMENT_COLUMNS})

    return records
