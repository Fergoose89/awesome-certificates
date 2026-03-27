from __future__ import annotations

import re
from collections import Counter

CLASS_RULES = [
    ("Emergency Support / Bailout", [r"emergency", r"support package", r"bailout", r"covid", r"rescue"]),
    ("Energy Support", [r"energy", r"utilities", r"gas", r"electric"]),
    ("Capital / One-off", [r"capital", r"refurb", r"plant", r"equipment", r"works"]),
    ("Operating Subsidy", [r"subsidy", r"deficit", r"shortfall", r"viability"]),
    ("Management Fee", [r"management fee", r"contract fee", r"monthly fee", r"service fee"]),
]


def apply_classification(rows: list[dict]) -> list[dict]:
    month_supplier_counts: Counter = Counter()
    for r in rows:
        month = str(r.get("payment_date", ""))[:7]
        month_supplier_counts[(r.get("supplier_normalized", ""), month)] += 1

    out = []
    for row in rows:
        desc = str(row.get("description", "")).lower()
        amount = float(row.get("amount_gbp", 0) or 0)
        month = str(row.get("payment_date", ""))[:7]
        recurring = month_supplier_counts[(row.get("supplier_normalized", ""), month)] >= 1 and bool(month)

        label = "Unknown"
        reason = "Positive payment without keyword match" if amount > 0 else "No amount or unclear context"
        conf = 0.5 if amount > 0 else 0.4

        for candidate, patterns in CLASS_RULES:
            if any(re.search(p, desc) for p in patterns):
                label = candidate
                reason = "Matched keyword rule"
                conf = 0.8
                break

        if label == "Unknown" and recurring and amount > 0:
            label = "Management Fee"
            reason = "Recurring monthly-like supplier pattern"
            conf = 0.7

        row = dict(row)
        row["classification"] = label
        row["classification_reason"] = reason
        row["confidence"] = max(float(row.get("confidence", 0.5)), conf)
        out.append(row)

    return out
