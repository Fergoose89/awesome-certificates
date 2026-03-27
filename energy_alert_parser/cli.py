from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from parser import AlertParser, ParsedRecord


def collect_records(parser: AlertParser, input_paths: List[Path], as_text: bool) -> List[ParsedRecord]:
    records: List[ParsedRecord] = []
    for input_path in input_paths:
        if as_text:
            text = input_path.read_text(encoding="utf-8")
            records.append(parser.parse_text(text))
        else:
            records.append(parser.parse_eml(input_path))
    return records


def main() -> None:
    ap = argparse.ArgumentParser(description="Parse site energy alert emails into structured records.")
    ap.add_argument("inputs", nargs="+", type=Path, help="Input files (.eml by default, or plain text with --text)")
    ap.add_argument("--rules", type=Path, default=Path("rules.json"), help="Path to editable parser rules JSON")
    ap.add_argument("--text", action="store_true", help="Treat inputs as plain text files")
    ap.add_argument("--json-out", type=Path, default=Path("outputs/parsed_records.json"), help="Output JSON path")
    ap.add_argument("--csv-out", type=Path, default=Path("outputs/parsed_records.csv"), help="Output CSV path")
    args = ap.parse_args()

    parser = AlertParser(args.rules)
    records = collect_records(parser, args.inputs, as_text=args.text)

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.csv_out.parent.mkdir(parents=True, exist_ok=True)

    AlertParser.write_json(records, args.json_out)
    AlertParser.write_csv(records, args.csv_out)

    flagged = [r for r in records if r.needs_review]
    print(f"Parsed {len(records)} record(s).")
    print(f"Low-confidence records: {len(flagged)}")


if __name__ == "__main__":
    main()
