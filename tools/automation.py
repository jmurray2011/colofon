"""Shared helpers for Colofon's machine-facing automation contract."""

import hashlib
import json
import os
import shutil

API_VERSION = "1"
FACTORY_VERSION = "0.2.0"


def emit(payload):
    """Write one deterministic JSON object to stdout."""
    print(json.dumps(payload, indent=2, sort_keys=True))


def failure(kind, message, source=None):
    error = {"message": str(message)}
    if source is not None:
        error["source"] = os.path.abspath(source)
    return {
        "api_version": API_VERSION,
        "errors": [error],
        "kind": kind,
        "ok": False,
    }


def verification_status(verapdf, pdftotext):
    """Describe checks performed by a successful factory build."""
    return {
        "copy_safe": "pass" if pdftotext else "not-run",
        "pdfua1": "pass" if verapdf else "not-run",
        "typst_pdfua1": "pass",
        "verified": bool(verapdf and pdftotext),
    }


def artifact_result(kind, source, output, verapdf, pdftotext):
    output = os.path.abspath(output)
    digest = hashlib.sha256()
    with open(output, "rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "api_version": API_VERSION,
        "artifact": {
            "bytes": os.path.getsize(output),
            "path": output,
            "sha256": digest.hexdigest(),
        },
        "checks": verification_status(verapdf, pdftotext),
        "kind": kind,
        "ok": True,
        "source": os.path.abspath(source),
    }


def executable(path):
    """Resolve an executable configured as either a path or a command name."""
    if os.path.sep in path:
        return path if os.path.isfile(path) and os.access(path, os.X_OK) else None
    return shutil.which(path)
