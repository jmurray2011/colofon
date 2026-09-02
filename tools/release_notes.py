#!/usr/bin/env python3
"""Render deterministic GitHub release notes from the changelog and source manifest."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from release_assets import DEFAULT_MANIFEST, load_manifest

ROOT = Path(__file__).resolve().parent.parent


def changelog_entry(version: str, changelog: Path = ROOT / "CHANGELOG.md") -> str:
    normalized = version.removeprefix("v")
    text = changelog.read_text(encoding="utf-8")
    match = re.search(
        rf"^## {re.escape(normalized)}(?: - [^\n]+)?\n(?P<body>.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise ValueError(f"CHANGELOG.md has no release section for {normalized}")
    return match.group("body").strip()


def render(version: str) -> str:
    normalized = version.removeprefix("v")
    sources = load_manifest(DEFAULT_MANIFEST)
    source_lines = "\n".join(
        f"- `{source['filename']}` — SHA-256 `{source['sha256']}`"
        for source in sources.values()
    )
    return f"""# Colofon v{normalized}

{changelog_entry(normalized)}

### Container images

- `ghcr.io/jmurray2011/colofon:{normalized}` — core MIT-oriented image
- `ghcr.io/jmurray2011/colofon-form:{normalized}` — optional AGPL-3.0-only form image

### Form-image corresponding source

The attached archives are the exact upstream sources corresponding to the PyMuPDF and
MuPDF versions bundled in the optional form image:

{source_lines}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate release notes for a Colofon tag")
    parser.add_argument("version", help="release version, with or without a leading v")
    args = parser.parse_args()
    try:
        print(render(args.version), end="")
    except (OSError, ValueError) as error:
        print(f"release notes error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
