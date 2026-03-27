"""Energy anomaly master dataset builder.

This script ingests CSV and Excel files from an input folder, standardizes core fields,
and writes three outputs:
1) cleaned_master.csv
2) issues_needing_review.csv
3) data_quality_report.md
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import yaml
from rapidfuzz import fuzz, process


@dataclass
class Config:
    site_match_threshold: int
    canonical_site_names: List[str]
    manual_site_mappings: Dict[str, str]
    column_aliases: Dict[str, List[str]]
    issue_category_rules: Dict[str, List[str]]


def normalize_text(value: object) -> str:
    """Normalize text for matching while preserving readability in outputs."""
    if pd.isna(value):
        return ""
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_for_key(value: object) -> str:
    """Normalize text aggressively for dictionary lookup/matching keys."""
    text = normalize_text(value).lower()
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def load_config(config_path: Path) -> Config:
    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return Config(
        site_match_threshold=int(raw.get("site_match_threshold", 85)),
        canonical_site_names=raw.get("canonical_site_names", []),
        manual_site_mappings={
            normalize_for_key(k): v
            for k, v in raw.get("manual_site_mappings", {}).items()
        },
        column_aliases={
            key: [normalize_for_key(v) for v in values]
            for key, values in raw.get("column_aliases", {}).items()
        },
        issue_category_rules=raw.get("issue_category_rules", {}),
    )


def standardize_mpan(raw_mpan: object) -> str:
    """Standardize MPAN to a readable grouped format where possible."""
    digits = re.sub(r"\D", "", normalize_text(raw_mpan))
    if not digits:
        return ""

    if len(digits) == 13:
        # MPAN core format: 2-4-4-3
        return f"{digits[:2]} {digits[2:6]} {digits[6:10]} {digits[10:13]}"

    if len(digits) == 21:
        # Full MPAN format: 2-3-3-2-4-4-3
        return (
            f"{digits[:2]} {digits[2:5]} {digits[5:8]} {digits[8:10]} "
            f"{digits[10:14]} {digits[14:18]} {digits[18:21]}"
        )

    # If length is unexpected, still keep a clean numeric value.
    return digits


def standardize_mprn(raw_mprn: object) -> str:
    """Standardize MPRN by keeping digits and grouping from the right in 3s."""
    digits = re.sub(r"\D", "", normalize_text(raw_mprn))
    if not digits:
        return ""

    groups = []
    while digits:
        groups.insert(0, digits[-3:])
        digits = digits[:-3]
    return " ".join(groups)


def classify_issue(issue_text: object, rules: Dict[str, List[str]]) -> str:
    """Assign issue category based on keyword rules; fallback to Other."""
    cleaned = normalize_for_key(issue_text)
    if not cleaned:
        return "Other"

    for category, keywords in rules.items():
        for keyword in keywords:
            if normalize_for_key(keyword) in cleaned:
                return category
    return "Other"


def map_columns(source_df: pd.DataFrame, aliases: Dict[str, List[str]]) -> pd.DataFrame:
    """Map messy incoming columns into canonical field names."""
    normalized_to_original = {
        normalize_for_key(column): column for column in source_df.columns
    }

    mapped = pd.DataFrame(index=source_df.index)

    for canonical_name, alias_list in aliases.items():
        found_col = None
        for alias in alias_list:
            if alias in normalized_to_original:
                found_col = normalized_to_original[alias]
                break
        mapped[canonical_name] = source_df[found_col] if found_col else ""

    return mapped


def match_site_name(
    raw_site_name: object,
    config: Config,
) -> Tuple[str, float, str]:
    """Return standardized site name, confidence [0-1], and method label."""
    raw_text = normalize_text(raw_site_name)
    if not raw_text:
        return "", 0.0, "missing"

    key = normalize_for_key(raw_text)

    if key in config.manual_site_mappings:
        return config.manual_site_mappings[key], 1.0, "manual_mapping"

    if not config.canonical_site_names:
        return raw_text, 0.0, "no_dictionary"

    matched = process.extractOne(
        raw_text,
        config.canonical_site_names,
        scorer=fuzz.WRatio,
    )

    if not matched:
        return raw_text, 0.0, "no_match"

    matched_name, score, _ = matched
    confidence = round(score / 100, 3)

    if score >= config.site_match_threshold:
        return matched_name, confidence, "fuzzy_match"

    return raw_text, confidence, "below_threshold"


def read_input_files(input_dir: Path) -> List[Tuple[str, pd.DataFrame]]:
    """Read all CSV/XLS/XLSX files from the input directory."""
    file_patterns = ["*.csv", "*.xlsx", "*.xls"]
    files = []
    for pattern in file_patterns:
        files.extend(sorted(input_dir.glob(pattern)))

    datasets: List[Tuple[str, pd.DataFrame]] = []
    for file_path in files:
        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        datasets.append((file_path.name, df))

    return datasets


def build_master_dataframe(input_datasets: List[Tuple[str, pd.DataFrame]], config: Config) -> pd.DataFrame:
    """Transform all source datasets into one standardized master table."""
    rows = []

    for source_name, source_df in input_datasets:
        mapped_df = map_columns(source_df, config.column_aliases)

        for idx, row in mapped_df.iterrows():
            site_raw = row.get("site_name", "")
            mpan_raw = row.get("mpan", "")
            mprn_raw = row.get("mprn", "")
            issue_raw = row.get("issue_description", "")

            site_clean, confidence, match_method = match_site_name(site_raw, config)

            rows.append(
                {
                    "source_file": source_name,
                    "source_row_number": int(idx) + 2,  # +2 to align with Excel-style row numbering
                    "site_name_raw": normalize_text(site_raw),
                    "site_name": site_clean,
                    "site_match_confidence": confidence,
                    "site_match_method": match_method,
                    "mpan_raw": normalize_text(mpan_raw),
                    "mpan": standardize_mpan(mpan_raw),
                    "mprn_raw": normalize_text(mprn_raw),
                    "mprn": standardize_mprn(mprn_raw),
                    "issue_description_raw": normalize_text(issue_raw),
                    "issue_type": classify_issue(issue_raw, config.issue_category_rules),
                }
            )

    return pd.DataFrame(rows)


def build_review_dataframe(master_df: pd.DataFrame, min_confidence: float) -> pd.DataFrame:
    """Create a subset of rows that should be checked by a human."""
    review_mask = (
        (master_df["site_match_confidence"] < min_confidence)
        | (master_df["issue_type"] == "Other")
        | (master_df["site_name"].str.strip() == "")
    )

    return master_df.loc[review_mask].copy()


def write_quality_report(
    report_path: Path,
    master_df: pd.DataFrame,
    review_df: pd.DataFrame,
    input_count: int,
) -> None:
    """Generate a markdown quality summary to support handover and QA."""
    total_rows = len(master_df)
    issue_counts = master_df["issue_type"].value_counts(dropna=False).to_dict()
    source_counts = master_df["source_file"].value_counts(dropna=False).to_dict()

    lines = [
        "# Data Quality Report",
        "",
        "## Run Summary",
        f"- Input files processed: **{input_count}**",
        f"- Total records in cleaned_master.csv: **{total_rows}**",
        f"- Records flagged in issues_needing_review.csv: **{len(review_df)}**",
        "",
        "## Site Name Matching",
        f"- High confidence matches (>= 0.85): **{(master_df['site_match_confidence'] >= 0.85).sum()}**",
        f"- Low confidence matches (< 0.85): **{(master_df['site_match_confidence'] < 0.85).sum()}**",
        "",
        "## Issue Category Distribution",
    ]

    for category, count in issue_counts.items():
        lines.append(f"- {category}: **{count}**")

    lines.extend(["", "## Records by Source File"])
    for source_file, count in source_counts.items():
        lines.append(f"- {source_file}: **{count}**")

    lines.extend(
        [
            "",
            "## Notes",
            "- Rows in issues_needing_review.csv usually need manual validation of site name or issue category.",
            "- You can tune matching behavior and keyword categories in config.yaml.",
        ]
    )

    report_path.write_text("\n".join(lines), encoding="utf-8")


def run(input_dir: Path, output_dir: Path, config_path: Path) -> None:
    config = load_config(config_path)
    datasets = read_input_files(input_dir)

    if not datasets:
        raise FileNotFoundError(
            f"No CSV/Excel files found in input directory: {input_dir}"
        )

    master_df = build_master_dataframe(datasets, config)
    min_confidence = config.site_match_threshold / 100
    review_df = build_review_dataframe(master_df, min_confidence=min_confidence)

    output_dir.mkdir(parents=True, exist_ok=True)

    master_path = output_dir / "cleaned_master.csv"
    review_path = output_dir / "issues_needing_review.csv"
    report_path = output_dir / "data_quality_report.md"

    master_df.to_csv(master_path, index=False)
    review_df.to_csv(review_path, index=False)
    write_quality_report(report_path, master_df, review_df, input_count=len(datasets))

    print(f"Created: {master_path}")
    print(f"Created: {review_path}")
    print(f"Created: {report_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a clean anomaly tracking master file from messy site-level energy exports."
    )
    parser.add_argument(
        "--input-dir",
        default="data/input",
        help="Folder containing CSV/XLS/XLSX files (default: data/input)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/output",
        help="Folder where output files will be written (default: data/output)",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to YAML config file (default: config.yaml)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        config_path=Path(args.config),
    )
