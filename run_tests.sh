#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
python -m pytest tests/ -v \
    --cov=qdf_bom \
    --cov-branch \
    --cov-report=term-missing \
    --cov-report=xml:coverage/coverage.xml \
    "$@"
