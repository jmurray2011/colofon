#!/usr/bin/env bash
set -euo pipefail

WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$WS"

python3 -m ruff check tools tests
shellcheck tools/colofon tools/check.sh build.sh examples/larkspur/build.sh .githooks/pre-commit
actionlint .github/workflows/*.yml

unformatted=$(gofmt -l cmd internal)
if [[ -n "$unformatted" ]]; then
  printf 'gofmt required:\n%s\n' "$unformatted" >&2
  exit 1
fi
go vet ./...
