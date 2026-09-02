"""Validate representative automation payloads against the published JSON Schemas."""

import importlib.util
import json
import os
import re
import sys
import tempfile
import unittest

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(WS, "schemas", "automation", "v1")
sys.path.insert(0, os.path.join(WS, "tools"))


def load_module(name):
    path = os.path.join(WS, "tools", name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


automation = load_module("automation")
colofon_info = load_module("colofon_info")
colofon_init = load_module("colofon_init")


def load_schema(name):
    with open(os.path.join(SCHEMA_DIR, name + ".schema.json"), encoding="utf-8") as source:
        return json.load(source)


def resolve(reference):
    filename, fragment = reference.split("#", 1)
    schema = load_schema(filename.removesuffix(".schema.json"))
    for component in fragment.removeprefix("/").split("/"):
        schema = schema[component]
    return schema


def validate(instance, schema, path="$"):
    """Validate the schema subset used by Colofon's dependency-free contract tests."""
    if "$ref" in schema:
        return validate(instance, resolve(schema["$ref"]), path)
    expected = schema.get("type")
    types = {
        "array": list,
        "boolean": bool,
        "integer": int,
        "object": dict,
        "string": str,
    }
    if expected and (not isinstance(instance, types[expected]) or
                     expected == "integer" and isinstance(instance, bool)):
        raise AssertionError(f"{path}: expected {expected}, got {type(instance).__name__}")
    if "const" in schema and instance != schema["const"]:
        raise AssertionError(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        raise AssertionError(f"{path}: {instance!r} is not in {schema['enum']!r}")
    if "minimum" in schema and instance < schema["minimum"]:
        raise AssertionError(f"{path}: value is below {schema['minimum']}")
    if "pattern" in schema and not re.search(schema["pattern"], instance):
        raise AssertionError(f"{path}: value does not match {schema['pattern']}")
    if isinstance(instance, dict):
        for required in schema.get("required", []):
            if required not in instance:
                raise AssertionError(f"{path}: missing required property {required!r}")
        properties = schema.get("properties", {})
        for name, value in instance.items():
            if name in properties:
                validate(value, properties[name], f"{path}.{name}")
            elif isinstance(schema.get("additionalProperties"), dict):
                validate(value, schema["additionalProperties"], f"{path}.{name}")
    if isinstance(instance, list) and "items" in schema:
        for index, value in enumerate(instance):
            validate(value, schema["items"], f"{path}[{index}]")


class AutomationSchemas(unittest.TestCase):
    def test_every_advertised_schema_exists_and_is_json(self):
        description = colofon_info.description()
        for path in description["schema_paths"].values():
            with self.subTest(path=path):
                with open(os.path.join(WS, path), encoding="utf-8") as source:
                    schema = json.load(source)
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_representative_payloads_conform(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = os.path.join(directory, "example.pdf")
            with open(artifact, "wb") as output:
                output.write(b"example")
            book = automation.artifact_result(
                "book-build", "book.yaml", artifact, True, True
            )
            document_result = automation.artifact_result(
                "document-build", "report.md", artifact, True, True
            )
            payloads = {
                "book-build": book,
                "describe": colofon_info.description(),
                "doctor": colofon_info.diagnostics(),
                "document-build": {
                    "api_version": "1", "errors": [], "kind": "document-build",
                    "ok": True, "results": [document_result],
                },
                "failure": automation.failure("book-build", "example failure", "book.yaml"),
                "lint": {
                    "api_version": "1", "defined_ids": ["overview"],
                    "kind": "markdown-lint", "ok": True, "problems": [],
                },
                "project-init": {
                    "api_version": "1", "dry_run": True,
                    "files": sorted(colofon_init.plan()), "kind": "project-init",
                    "ok": True, "target": directory,
                },
            }
        for name, payload in payloads.items():
            with self.subTest(schema=name):
                validate(payload, load_schema(name))

    def test_schema_rejects_missing_digest(self):
        payload = {
            "api_version": "1", "artifact": {"bytes": 1, "path": "/tmp/a.pdf"},
            "checks": {
                "copy_safe": "pass", "pdfua1": "pass",
                "typst_pdfua1": "pass", "verified": True,
            },
            "kind": "book-build", "ok": True, "source": "/tmp/book.yaml",
        }
        with self.assertRaisesRegex(AssertionError, "sha256"):
            validate(payload, load_schema("book-build"))
