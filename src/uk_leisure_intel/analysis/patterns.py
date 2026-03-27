from __future__ import annotations

from collections import defaultdict
from statistics import mean


def detect_patterns(rows: list[dict]) -> dict:
    monthly = defaultdict(float)
    for r in rows:
        date = str(r.get("payment_date", ""))
        if len(date) >= 7:
            monthly[date[:7]] += float(r.get("amount_gbp", 0) or 0)

    if not monthly:
        return {
            "recurring_signal": False,
            "spike_months": [],
            "trend": "insufficient_data",
            "inconsistency_flag": True,
            "monthly_series": {},
        }

    months = sorted(monthly.keys())
    vals = [monthly[m] for m in months]
    avg = mean(vals)
    variance = mean([(v - avg) ** 2 for v in vals]) if len(vals) > 1 else 0.0
    std = variance ** 0.5

    spikes = [m for m in months if monthly[m] > avg + 2 * std] if std > 0 else []
    trend = "increasing" if len(vals) > 1 and vals[-1] > vals[0] else "decreasing_or_flat"
    cv = (std / avg) if avg else 0

    return {
        "recurring_signal": len(vals) >= 6 and cv < 0.35,
        "spike_months": spikes,
        "trend": trend,
        "inconsistency_flag": cv > 0.65,
        "monthly_series": dict(monthly),
    }


def reconstruct_contract_model(rows: list[dict], pattern_summary: dict) -> dict:
    if not rows:
        return {
            "direction": "unknown",
            "subsidised": "unknown",
            "stability": "unknown",
            "total_paid": 0.0,
            "likely_management_fee": 0.0,
            "subsidy_estimate": 0.0,
            "explanation": "No usable financial records.",
        }

    total_paid = sum(float(r.get("amount_gbp", 0) or 0) for r in rows if float(r.get("amount_gbp", 0) or 0) > 0)
    mgmt = sum(float(r.get("amount_gbp", 0) or 0) for r in rows if r.get("classification") == "Management Fee")
    subsidy = sum(
        float(r.get("amount_gbp", 0) or 0)
        for r in rows
        if r.get("classification") in ["Operating Subsidy", "Emergency Support / Bailout", "Energy Support"]
    )

    stability = "stable"
    if pattern_summary.get("trend") == "increasing" and subsidy > 0:
        stability = "deteriorating"
    elif pattern_summary.get("inconsistency_flag"):
        stability = "volatile"

    return {
        "direction": "council_to_operator" if total_paid > 0 else "unclear",
        "subsidised": "yes" if subsidy > 0 else "likely_no",
        "stability": stability,
        "total_paid": total_paid,
        "likely_management_fee": mgmt,
        "subsidy_estimate": subsidy,
        "explanation": "Derived from classified rows and monthly payment pattern signals.",
    }
