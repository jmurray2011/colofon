#!/usr/bin/env bash
set -euo pipefail

WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$WS"

python3 -m ruff check tools tests
shellcheck tools/colofon tools/check.sh build.sh examples/larkspur/build.sh .githooks/pre-commit
actionlint .github/workflows/*.yml
