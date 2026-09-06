#!/usr/bin/env bash
# Run the backend test suite.
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pytest -q
