from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .models import SourceItem

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def load_sources(config_path: str) -> List[SourceItem]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
    elif yaml is not None:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    else:
        data = _parse_simple_yaml(path.read_text(encoding="utf-8"))

    raw_sources = data.get("sources", [])
    sources: List[SourceItem] = []
    for item in raw_sources:
        sources.append(
            SourceItem(
                name=item.get("name", "unnamed"),
                type=item.get("type", "").strip().lower(),
                value=item.get("value", "").strip(),
                enabled=bool(item.get("enabled", True)),
            )
        )
    return sources


def _parse_simple_yaml(raw: str) -> dict:
    """Very small YAML fallback parser for the expected `sources` structure."""
    sources: list[dict] = []
    current: dict | None = None

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "sources:":
            continue
        if stripped.startswith("-"):
            if current:
                sources.append(current)
            current = {}
            stripped = stripped[1:].strip()
            if stripped and ":" in stripped:
                key, value = stripped.split(":", 1)
                current[key.strip()] = _clean_value(value)
            continue
        if current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = _clean_value(value)

    if current:
        sources.append(current)

    return {"sources": sources}


def _clean_value(value: str):
    v = value.strip().strip('"').strip("'")
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    return v
