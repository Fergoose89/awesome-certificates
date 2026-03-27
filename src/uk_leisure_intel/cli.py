from __future__ import annotations

import argparse
import json

from uk_leisure_intel.config import load_config
from uk_leisure_intel.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="UK leisure contract financial intelligence pipeline")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    args = parser.parse_args()

    cfg = load_config(args.config)
    result = run_pipeline(cfg)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
