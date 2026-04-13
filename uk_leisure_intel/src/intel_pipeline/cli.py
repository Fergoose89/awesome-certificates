from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from .classifier import classify_snippet
from .collectors import collect_documents
from .config_loader import load_sources
from .extractors import extract_relevant_snippets
from .models import EvidenceFinding
from .reporters import write_evidence_log, write_scorecard, write_summary_markdown
from .scoring import build_scorecard


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UK leisure procurement OSINT pipeline")
    parser.add_argument("--council", required=True, help="Council name, e.g. 'Bristol City Council'")
    parser.add_argument("--operators", nargs="+", required=True, help="Operator names to track")
    parser.add_argument("--config", required=True, help="Path to YAML source config")
    parser.add_argument("--output-dir", default="data/output", help="Output directory")
    return parser.parse_args()


def run() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sources = load_sources(args.config)
    docs = collect_documents(sources)
    snippets = extract_relevant_snippets(docs, args.council, args.operators)

    findings: list[EvidenceFinding] = []
    for idx, row in enumerate(snippets, start=1):
        primary, all_signals, keywords, confidence = classify_snippet(row["snippet"])
        doc = row["document"]
        findings.append(
            EvidenceFinding(
                finding_id=f"F{idx:05d}",
                collected_at=datetime.utcnow().isoformat(timespec="seconds"),
                source_name=doc.source_name,
                source_type=doc.source_type,
                source_url=doc.source_url,
                local_path=doc.local_path,
                document_title=doc.title,
                excerpt=row["snippet"][:600],
                references=row["references"][:15],
                matched_keywords=keywords,
                primary_signal=primary,
                all_signals=all_signals,
                confidence=confidence,
            )
        )

    scorecard = build_scorecard(findings)
    evidence_path = write_evidence_log(findings, output_dir)
    summary_path = write_summary_markdown(args.council, args.operators, findings, scorecard, output_dir)
    scorecard_csv, scorecard_md = write_scorecard(scorecard, output_dir)

    print("Pipeline run complete")
    print(f"- Documents collected: {len(docs)}")
    print(f"- Findings extracted: {len(findings)}")
    print(f"- Evidence log: {evidence_path}")
    print(f"- Summary briefing: {summary_path}")
    print(f"- Scorecard CSV: {scorecard_csv}")
    print(f"- Scorecard MD: {scorecard_md}")


if __name__ == "__main__":
    run()
