#!/usr/bin/env python3
"""Describe the Colofon automation API and diagnose its local toolchain."""

import argparse
import importlib.util
import os
import platform
import shutil
import subprocess
import sys

import automation
import make_doc

BOOK_SCHEMA = {
    "required": ["parts", "title"],
    "optional": [
        "brand", "date", "draft", "logo", "logo-alt", "logo-width", "subtitle",
        "vars", "vars-from", "version", "watermark",
    ],
    "part_required": ["chapters", "title"],
    "part_optional": ["appendix", "blurb"],
}


def description():
    doctypes = {}
    for name, schema in make_doc.DOCTYPE_SCHEMA.items():
        optional = set(schema["optional"])
        if "logo" in optional:
            optional.add("logo-alt")
        doctypes[name] = {
            "optional": sorted(optional | {"brand"}),
            "required": sorted(schema["required"]),
        }
    return {
        "api_version": automation.API_VERSION,
        "book_schema": BOOK_SCHEMA,
        "capabilities": {
            "book": True,
            "document": True,
            "fillable_form": importlib.util.find_spec("pymupdf") is not None,
            "lint": True,
            "mcp": True,
        },
        "document_schemas": doctypes,
        "factory_version": automation.FACTORY_VERSION,
        "kind": "description",
        "ok": True,
    }


def probe(name, configured, args):
    resolved = automation.executable(configured)
    result = {"configured": configured, "name": name, "present": resolved is not None}
    if not resolved:
        return result
    result["path"] = os.path.abspath(resolved)
    try:
        process = subprocess.run(
            [resolved, *args], capture_output=True, text=True, check=False, timeout=10
        )
        output = (process.stdout or process.stderr).strip().splitlines()
        result["ok"] = process.returncode == 0
        result["version"] = output[0] if output else "unknown"
    except (OSError, subprocess.TimeoutExpired) as e:
        result["ok"] = False
        result["error"] = str(e)
    return result


def diagnostics():
    tools = [
        probe("typst", make_doc.TYPST, ["--version"]),
        probe("verapdf", make_doc.VERAPDF, ["--version"]),
        probe("pdftotext", shutil.which("pdftotext") or "pdftotext", ["-v"]),
        probe("python", sys.executable, ["--version"]),
    ]
    return {
        "api_version": automation.API_VERSION,
        "configuration": {
            "allow_unverified": make_doc.ALLOW_UNVERIFIED,
            "fonts": os.path.abspath(make_doc.FONTS),
            "packages": os.path.abspath(make_doc.PACKAGES),
        },
        "factory_version": automation.FACTORY_VERSION,
        "kind": "diagnostics",
        "ok": all(tool.get("present") and tool.get("ok") for tool in tools),
        "platform": platform.platform(),
        "tools": tools,
    }


def human(payload):
    if payload["kind"] == "description":
        print(f"Colofon {payload['factory_version']} (automation API {payload['api_version']})")
        print("Document types: " + ", ".join(payload["document_schemas"]))
        return
    print(f"Colofon {payload['factory_version']} diagnostics")
    for tool in payload["tools"]:
        status = "ok" if tool.get("present") and tool.get("ok") else "missing/broken"
        print(f"  {tool['name']}: {status} ({tool.get('version', tool['configured'])})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("describe", "doctor"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    payload = description() if a.command == "describe" else diagnostics()
    automation.emit(payload) if a.json else human(payload)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
