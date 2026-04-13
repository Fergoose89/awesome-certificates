from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


SIGNAL_TYPES = [
    "procurement signal",
    "capital investment signal",
    "financial distress signal",
    "political risk signal",
    "decarbonisation or energy signal",
    "unclassified",
]


@dataclass
class SourceItem:
    name: str
    type: str  # url | file | glob
    value: str
    enabled: bool = True


@dataclass
class CollectedDocument:
    source_name: str
    source_type: str
    source_value: str
    title: str
    content: str
    source_url: str = ""
    local_path: str = ""
    collected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EvidenceFinding:
    finding_id: str
    collected_at: str
    source_name: str
    source_type: str
    source_url: str
    local_path: str
    document_title: str
    excerpt: str
    references: List[str]
    matched_keywords: List[str]
    primary_signal: str
    all_signals: List[str]
    confidence: float
