from __future__ import annotations

from collections import Counter
from typing import Dict, List

from .models import EvidenceFinding


WEIGHTS = {
    "procurement signal": {"opportunity": 2, "risk": 0},
    "capital investment signal": {"opportunity": 2, "risk": 0},
    "financial distress signal": {"opportunity": 0, "risk": 3},
    "political risk signal": {"opportunity": 0, "risk": 2},
    "decarbonisation or energy signal": {"opportunity": 1, "risk": 0},
    "unclassified": {"opportunity": 0, "risk": 0},
}


def build_scorecard(findings: List[EvidenceFinding]) -> Dict[str, object]:
    counter = Counter(f.primary_signal for f in findings)
    weighted_risk = 0
    weighted_opportunity = 0

    for signal, count in counter.items():
        weighted_risk += WEIGHTS.get(signal, {"risk": 0})["risk"] * count
        weighted_opportunity += WEIGHTS.get(signal, {"opportunity": 0})["opportunity"] * count

    net = weighted_opportunity - weighted_risk
    if net >= 5:
        posture = "Opportunity-led"
    elif net <= -5:
        posture = "Risk-led"
    else:
        posture = "Mixed / monitor"

    return {
        "counts": dict(counter),
        "weighted_risk": weighted_risk,
        "weighted_opportunity": weighted_opportunity,
        "net_score": net,
        "posture": posture,
    }
