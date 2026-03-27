from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SourceConfig:
    enabled: bool = True
    mode: str = "local_or_live"
    urls: list[str] = field(default_factory=list)
    local_globs: list[str] = field(default_factory=list)


@dataclass
class PipelineConfig:
    council: str
    operators: list[str]
    operator_aliases: list[str]
    start_date: str
    end_date: str
    min_fuzzy_score: int = 86
    output_dir: str = "reports/output"
    data_dir: str = "data"
    sources: dict[str, SourceConfig] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineConfig":
        source_cfgs = {
            name: SourceConfig(**cfg) for name, cfg in data.get("sources", {}).items()
        }
        return cls(
            council=data["council"],
            operators=data.get("operators", []),
            operator_aliases=data.get("operator_aliases", []),
            start_date=data["start_date"],
            end_date=data["end_date"],
            min_fuzzy_score=int(data.get("min_fuzzy_score", 86)),
            output_dir=data.get("output_dir", "reports/output"),
            data_dir=data.get("data_dir", "data"),
            sources=source_cfgs,
        )


def load_config(path: str | Path) -> PipelineConfig:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    return PipelineConfig.from_dict(data)
