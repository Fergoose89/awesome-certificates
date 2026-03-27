from __future__ import annotations

from dataclasses import asdict

from uk_leisure_intel.analysis.classification import apply_classification
from uk_leisure_intel.analysis.patterns import detect_patterns, reconstruct_contract_model
from uk_leisure_intel.config import PipelineConfig
from uk_leisure_intel.output.reporting import build_evidence_log, build_financial_summary, write_outputs
from uk_leisure_intel.sources import council_docs, operator_financials, procurement, transparency


def run_pipeline(cfg: PipelineConfig) -> dict:
    combined = []
    combined.extend(transparency.run(cfg))
    combined.extend(council_docs.run(cfg))
    combined.extend(procurement.run(cfg))
    combined.extend(operator_financials.run(cfg))

    combined = apply_classification(combined) if combined else []
    combined = sorted(combined, key=lambda x: (x.get("financial_year", ""), x.get("payment_date", "")))

    patterns = detect_patterns(combined)
    model = reconstruct_contract_model(combined, patterns)
    financial_summary = build_financial_summary(combined)
    evidence = build_evidence_log(combined)
    outputs = write_outputs(combined, financial_summary, evidence, model, patterns, cfg.output_dir)

    return {
        "config": asdict(cfg),
        "rows": len(combined),
        "outputs": {k: str(v) for k, v in outputs.items()},
        "model": model,
        "patterns": patterns,
    }
