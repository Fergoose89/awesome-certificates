from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

from .models import EvidenceFinding


def write_evidence_log(findings: List[EvidenceFinding], output_dir: Path) -> Path:
    output_path = output_dir / "evidence_log.csv"
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "finding_id",
                "collected_at",
                "source_name",
                "source_type",
                "source_url",
                "local_path",
                "document_title",
                "excerpt",
                "references",
                "matched_keywords",
                "primary_signal",
                "all_signals",
                "confidence",
            ]
        )
        for item in findings:
            writer.writerow(
                [
                    item.finding_id,
                    item.collected_at,
                    item.source_name,
                    item.source_type,
                    item.source_url,
                    item.local_path,
                    item.document_title,
                    item.excerpt,
                    " | ".join(item.references),
                    " | ".join(item.matched_keywords),
                    item.primary_signal,
                    " | ".join(item.all_signals),
                    item.confidence,
                ]
            )
    return output_path


def write_summary_markdown(
    council: str,
    operators: List[str],
    findings: List[EvidenceFinding],
    scorecard: Dict[str, object],
    output_dir: Path,
) -> Path:
    output_path = output_dir / "summary_briefing.md"

    top_findings = sorted(findings, key=lambda f: f.confidence, reverse=True)[:20]
    by_signal: Dict[str, List[EvidenceFinding]] = {}
    for item in findings:
        by_signal.setdefault(item.primary_signal, []).append(item)

    lines = [
        f"# UK Leisure Intelligence Briefing: {council}",
        "",
        f"**Operators tracked:** {', '.join(operators)}",
        f"**Total findings:** {len(findings)}",
        f"**Posture:** {scorecard['posture']}",
        f"**Weighted opportunity:** {scorecard['weighted_opportunity']}",
        f"**Weighted risk:** {scorecard['weighted_risk']}",
        f"**Net score:** {scorecard['net_score']}",
        "",
        "## Top evidence",
        "",
    ]

    for finding in top_findings:
        trace = finding.source_url or finding.local_path
        lines.extend(
            [
                f"- **[{finding.primary_signal}]** {finding.document_title}",
                f"  - confidence: {finding.confidence}",
                f"  - trace: {trace}",
                f"  - references: {', '.join(finding.references) if finding.references else 'n/a'}",
                f"  - excerpt: {finding.excerpt[:280]}...",
            ]
        )

    lines.append("\n## Findings by signal\n")
    for signal, items in sorted(by_signal.items(), key=lambda kv: len(kv[1]), reverse=True):
        lines.append(f"### {signal} ({len(items)})")
        for item in items[:5]:
            trace = item.source_url or item.local_path
            lines.append(f"- {item.document_title} — {trace}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def write_scorecard(scorecard: Dict[str, object], output_dir: Path) -> tuple[Path, Path]:
    csv_path = output_dir / "risk_opportunity_scorecard.csv"
    md_path = output_dir / "risk_opportunity_scorecard.md"

    counts = scorecard.get("counts", {})
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for signal, value in counts.items():
            writer.writerow([f"count::{signal}", value])
        writer.writerow(["weighted_opportunity", scorecard["weighted_opportunity"]])
        writer.writerow(["weighted_risk", scorecard["weighted_risk"]])
        writer.writerow(["net_score", scorecard["net_score"]])
        writer.writerow(["posture", scorecard["posture"]])

    md_lines = [
        "# Risk / Opportunity Scorecard",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for signal, value in counts.items():
        md_lines.append(f"| count::{signal} | {value} |")
    md_lines.extend(
        [
            f"| weighted_opportunity | {scorecard['weighted_opportunity']} |",
            f"| weighted_risk | {scorecard['weighted_risk']} |",
            f"| net_score | {scorecard['net_score']} |",
            f"| posture | {scorecard['posture']} |",
        ]
    )

    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    return csv_path, md_path
