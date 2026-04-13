from __future__ import annotations

from typing import Dict, List, Tuple


CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "procurement signal": [
        "tender",
        "procurement",
        "contract award",
        "invitation to tender",
        "framework",
        "find a tender",
        "pin notice",
    ],
    "capital investment signal": [
        "capex",
        "capital programme",
        "capital investment",
        "redevelopment",
        "refurbishment",
        "planning application",
        "business case",
    ],
    "financial distress signal": [
        "deficit",
        "overspend",
        "section 114",
        "insolvency",
        "cost pressure",
        "savings requirement",
        "budget gap",
        "cashflow",
    ],
    "political risk signal": [
        "judicial review",
        "call-in",
        "election",
        "cabinet decision",
        "scrutiny",
        "opposition",
        "consultation backlash",
    ],
    "decarbonisation or energy signal": [
        "decarbonisation",
        "net zero",
        "solar",
        "heat pump",
        "energy performance",
        "retrofit",
        "carbon reduction",
    ],
}


def classify_snippet(text: str) -> Tuple[str, List[str], List[str], float]:
    lowered = text.lower()
    matched_categories: List[str] = []
    matched_keywords: List[str] = []

    for category, keywords in CATEGORY_KEYWORDS.items():
        local_hits = [kw for kw in keywords if kw in lowered]
        if local_hits:
            matched_categories.append(category)
            matched_keywords.extend(local_hits)

    if not matched_categories:
        return "unclassified", [], [], 0.2

    primary = matched_categories[0]
    confidence = min(0.95, 0.4 + 0.1 * len(set(matched_keywords)) + 0.1 * len(matched_categories))
    return primary, matched_categories, sorted(set(matched_keywords)), round(confidence, 2)
