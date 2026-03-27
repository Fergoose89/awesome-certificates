from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass
class ParsedRecord:
    site_code: Optional[str] = None
    site_name: Optional[str] = None
    mpan_or_mprn: Optional[str] = None
    issue_type: Optional[str] = None
    first_observed_date: Optional[str] = None
    daily_cost: Optional[float] = None
    rank: Optional[str] = None
    narrative_summary: Optional[str] = None
    source_email_subject: Optional[str] = None
    source_email_date: Optional[str] = None
    confidence: float = 0.0
    needs_review: bool = True


class AlertParser:
    def __init__(self, rules_path: Path):
        with rules_path.open("r", encoding="utf-8") as f:
            self.rules = json.load(f)

    def parse_text(
        self,
        text: str,
        source_subject: Optional[str] = None,
        source_date: Optional[str] = None,
    ) -> ParsedRecord:
        fields = {}
        pattern_hits = 0
        total_fields = len(self.rules["field_patterns"])

        for field_name, patterns in self.rules["field_patterns"].items():
            value, matched = self._extract_first(text, patterns)
            if matched:
                pattern_hits += 1
            fields[field_name] = self._normalize_field(field_name, value)

        issue_type = fields.get("issue_type")
        if not issue_type and source_subject:
            issue_type = self._infer_issue_from_subject(source_subject)
            if issue_type:
                pattern_hits += 0.5

        narrative_summary = self._narrative_summary(text)

        confidence = min(1.0, pattern_hits / total_fields)
        threshold = float(self.rules.get("confidence_threshold", 0.75))

        fields["issue_type"] = issue_type

        return ParsedRecord(
            **fields,
            narrative_summary=narrative_summary,
            source_email_subject=source_subject,
            source_email_date=source_date,
            confidence=round(confidence, 2),
            needs_review=confidence < threshold,
        )

    def parse_eml(self, eml_path: Path) -> ParsedRecord:
        with eml_path.open("rb") as f:
            msg = BytesParser(policy=policy.default).parse(f)

        subject = str(msg.get("Subject", "")).strip() or None
        date = str(msg.get("Date", "")).strip() or None

        if msg.is_multipart():
            parts = [
                part.get_content()
                for part in msg.walk()
                if part.get_content_type() == "text/plain"
            ]
            body = "\n".join(parts)
        else:
            body = msg.get_content()

        return self.parse_text(body, source_subject=subject, source_date=date)

    @staticmethod
    def write_json(records: Iterable[ParsedRecord], output_path: Path) -> None:
        payload = [asdict(r) for r in records]
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def write_csv(records: Iterable[ParsedRecord], output_path: Path) -> None:
        records = list(records)
        if not records:
            return

        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(records[0]).keys()))
            writer.writeheader()
            for record in records:
                writer.writerow(asdict(record))

    def _extract_first(self, text: str, patterns: List[str]) -> Tuple[Optional[str], bool]:
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                val = m.group(1).strip()
                if val:
                    return val, True
        return None, False

    @staticmethod
    def _normalize_field(field_name: str, value: Optional[str]):
        if value is None:
            return None

        value = value.strip()
        if field_name == "daily_cost":
            value = value.replace(",", "")
            try:
                return float(value)
            except ValueError:
                return None
        if field_name == "first_observed_date":
            parsed = AlertParser._try_parse_date(value)
            return parsed or value
        if field_name == "mpan_or_mprn":
            return re.sub(r"\s+", " ", value)
        return value

    @staticmethod
    def _try_parse_date(raw: str) -> Optional[str]:
        formats = [
            "%d/%m/%Y",
            "%d/%m/%y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d-%m-%y",
            "%d %b %Y",
            "%d %B %Y",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(raw.strip(), fmt).date().isoformat()
            except ValueError:
                continue
        return None

    def _infer_issue_from_subject(self, subject: str) -> Optional[str]:
        s = subject.lower()
        for needle, issue in self.rules.get("subject_issue_hints", {}).items():
            if needle in s:
                return issue
        return None

    @staticmethod
    def _narrative_summary(text: str, limit: int = 220) -> str:
        collapsed = re.sub(r"\s+", " ", text).strip()
        return collapsed[:limit] + ("..." if len(collapsed) > limit else "")
