#!/usr/bin/env python3
"""Fetch and verify corresponding-source archives for the form image."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = ROOT / "tools" / "form-sources.json"


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data:
        raise ValueError("source manifest must be a non-empty object")

    filenames: set[str] = set()
    for name, source in data.items():
        if not isinstance(source, dict):
            raise ValueError(f"source {name!r} must be an object")
        if set(source) != {"filename", "sha256", "url"}:
            raise ValueError(f"source {name!r} has unexpected fields")
        filename = source["filename"]
        digest = source["sha256"]
        url = source["url"]
        if Path(filename).name != filename or filename in filenames:
            raise ValueError(f"source {name!r} has an unsafe or duplicate filename")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError(f"source {name!r} has an invalid SHA-256 digest")
        if not url.startswith("https://"):
            raise ValueError(f"source {name!r} must use HTTPS")
        filenames.add(filename)
    return data


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(path: Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"SHA-256 mismatch for {path.name}: expected {expected}, got {actual}")


def fetch(destination: Path, manifest_path: Path = DEFAULT_MANIFEST) -> list[Path]:
    manifest = load_manifest(manifest_path)
    destination.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []

    for source in manifest.values():
        target = destination / source["filename"]
        if target.exists():
            verify(target, source["sha256"])
            downloaded.append(target)
            continue

        temporary = target.with_suffix(target.suffix + ".part")
        try:
            request = urllib.request.Request(
                source["url"], headers={"User-Agent": "colofon-release-assets/1"}
            )
            with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
                with temporary.open("wb") as output:
                    shutil.copyfileobj(response, output, length=1024 * 1024)
            verify(temporary, source["sha256"])
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        downloaded.append(target)

    return downloaded


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download and SHA-256 verify form-image corresponding source"
    )
    parser.add_argument("destination", type=Path)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    try:
        paths = fetch(args.destination, args.manifest)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"release asset error: {error}", file=sys.stderr)
        return 1

    for path in paths:
        print(f"{sha256(path)}  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
