from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

from uk_leisure_intel.schemas import PAYMENT_COLUMNS
from uk_leisure_intel.utils.io import ensure_dir, write_csv_rows


def build_financial_summary(rows: list[dict]) -> list[dict]:
    by_year = defaultdict(list)
    for row in rows:
        by_year[row.get("financial_year", "Unknown")].append(row)

    summaries = []
    all_totals = []
    for year, rs in sorted(by_year.items()):
        total = sum(float(r.get("amount_gbp", 0) or 0) for r in rs)
        mgmt = sum(float(r.get("amount_gbp", 0) or 0) for r in rs if r.get("classification") == "Management Fee")
        subsidy = sum(
            float(r.get("amount_gbp", 0) or 0)
            for r in rs
            if r.get("classification") in ["Operating Subsidy", "Emergency Support / Bailout", "Energy Support"]
        )
        all_totals.append(total)
        summaries.append(
            {
                "Year": year,
                "Total Paid": round(total, 2),
                "Avg Monthly": round(total / 12, 2),
                "Variance": 0.0,
                "Likely Management Fee": round(mgmt, 2),
                "Subsidy Estimate": round(subsidy, 2),
            }
        )

    variance = 0.0
    if len(all_totals) > 1:
        avg_total = mean(all_totals)
        variance = mean([(x - avg_total) ** 2 for x in all_totals])
    for row in summaries:
        row["Variance"] = round(variance, 2)

    return summaries


def build_evidence_log(rows: list[dict]) -> list[dict]:
    return [
        {
            "source": r.get("source_url", ""),
            "extract": str(r.get("description", ""))[:240],
            "interpretation": r.get("classification_reason", ""),
            "confidence_score": r.get("confidence", 0),
        }
        for r in rows
    ]


def write_outputs(
    payments: list[dict],
    financial_summary: list[dict],
    evidence_log: list[dict],
    model: dict,
    patterns: dict,
    output_dir: str,
) -> dict[str, Path]:
    out = ensure_dir(output_dir)
    files = {
        "payments": out / "payments_classified.csv",
        "financial_summary": out / "financial_summary.csv",
        "evidence_log": out / "evidence_log.csv",
        "report": out / "intelligence_report.md",
        "model_json": out / "model_summary.json",
    }

    write_csv_rows(files["payments"], payments, PAYMENT_COLUMNS)
    write_csv_rows(
        files["financial_summary"],
        financial_summary,
        ["Year", "Total Paid", "Avg Monthly", "Variance", "Likely Management Fee", "Subsidy Estimate"],
    )
    write_csv_rows(files["evidence_log"], evidence_log, ["source", "extract", "interpretation", "confidence_score"])
    files["model_json"].write_text(json.dumps({"model": model, "patterns": patterns}, indent=2), encoding="utf-8")

    confidence = round(mean([float(r.get("confidence", 0)) for r in payments]), 2) if payments else 0.0
    red_flags = []
    if patterns.get("inconsistency_flag"):
        red_flags.append("High payment volatility")
    if patterns.get("trend") == "increasing":
        red_flags.append("Rising payment trend")
    if patterns.get("spike_months"):
        red_flags.append(f"Spikes in {', '.join(patterns['spike_months'])}")

    report = f"""# Leisure Contract Financial Intelligence Report

## Payment Reality
- Total identified payments: £{model.get('total_paid', 0):,.2f}
- Likely management fee component: £{model.get('likely_management_fee', 0):,.2f}
- Subsidy/support estimate: £{model.get('subsidy_estimate', 0):,.2f}

## Commercial Model Interpretation
- Direction: **{model.get('direction', 'unknown')}**
- Subsidised: **{model.get('subsidised', 'unknown')}**
- Stability: **{model.get('stability', 'unknown')}**
- Interpretation note: {model.get('explanation', '')}

## Stability Assessment
- Recurring signal: **{patterns.get('recurring_signal', False)}**
- Trend: **{patterns.get('trend', 'insufficient_data')}**
- Spike months: **{', '.join(patterns.get('spike_months', [])) or 'None'}**

## Red Flags
- {chr(10).join(['- ' + flag for flag in red_flags]) if red_flags else 'No critical red flags detected from current evidence.'}

## Confidence Level
- Average evidence confidence score: **{confidence} / 1.0**

## Key Evidence
- See `evidence_log.csv` for source-by-source traceability.
"""
    files["report"].write_text(report, encoding="utf-8")
    return files
