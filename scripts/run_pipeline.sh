#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="${1:-config/sample_config.json}"
python -m uk_leisure_intel.cli --config "$CONFIG_PATH"
