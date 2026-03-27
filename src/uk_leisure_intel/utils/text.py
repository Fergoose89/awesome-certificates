from __future__ import annotations

import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Iterable


def normalize_supplier(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9 ]", " ", str(value).lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def parse_date_guess(value: str) -> datetime | None:
    if not value:
        return None
    candidates = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%b %Y"]
    for fmt in candidates:
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    return None


def fy_from_date(dt: datetime) -> str:
    return f"{dt.year}/{str(dt.year + 1)[-2:]}" if dt.month >= 4 else f"{dt.year - 1}/{str(dt.year)[-2:]}"


def _ratio(a: str, b: str) -> int:
    return int(100 * SequenceMatcher(None, a, b).ratio())


def match_alias(name: str, aliases: Iterable[str], min_score: int) -> tuple[bool, int, str | None]:
    norm_name = normalize_supplier(name)
    best_score = 0
    best_alias = None
    for alias in aliases:
        score = _ratio(norm_name, normalize_supplier(alias))
        if score > best_score:
            best_score = score
            best_alias = alias
    return (best_score >= min_score, best_score, best_alias)
