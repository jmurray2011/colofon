"""Contract tests for Colofon's structured automation interface."""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLOFON = os.path.join(WS, "tools", "colofon")
TYPST = os.environ.get("TYPST", os.path.expanduser("~/.local/bin/typst"))
VERAPDF = os.environ.get("VERAPDF", os.path.expanduser("~/.local/verapdf/verapdf"))


def run_json(*args, cwd=WS):
    result = subprocess.run(
        [COLOFON, *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    return result, json.loads(result.stdout)


class DescribeAndDoctor(unittest.TestCase):
    def test_describe_publishes_versioned_schemas(self):
        result, payload = run_json("describe", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["api_version"], "1")
        with open(os.path.join(WS, "VERSION"), encoding="utf-8") as version_file:
            self.assertEqual(payload["factory_version"], version_file.read().strip())
        self.assertEqual(
            sorted(payload["document_schemas"]),
            [
                "article", "bug-report", "kb-article", "memo", "minutes", "onepager",
                "release-notes", "report", "runbook",
            ],
        )
        self.assertNotIn("form", payload["document_schemas"])

    def test_doctor_reports_every_required_tool(self):
        _, payload = run_json("doctor", "--json")
        self.assertEqual(
            [tool["name"] for tool in payload["tools"]],
            ["typst", "verapdf", "pdftotext", "python"],
        )


class StructuredCommands(unittest.TestCase):
    def test_document_error_is_json(self):
        result, payload = run_json("doc", "missing.md", "--json")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["kind"], "document-build")
        self.assertIn("no such file", payload["errors"][0]["message"])

    def test_book_error_is_json(self):
        result, payload = run_json("book", "missing.yaml", "--json")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["kind"], "book-build")

    def test_lint_result_is_structured(self):
        with tempfile.TemporaryDirectory() as directory:
            source = os.path.join(directory, "chapter.md")
            with open(source, "w", encoding="utf-8") as chapter:
                chapter.write("# Start\n\nSee [nowhere](#missing).\n")
            result, payload = run_json("lint", "chapter.md", "--json", cwd=directory)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["problems"][0]["severity"], "error")
        self.assertEqual(payload["problems"][0]["line"], 3)

    @unittest.skipUnless(
        os.path.exists(TYPST) and os.path.exists(VERAPDF) and shutil.which("pdftotext"),
        "complete PDF gate is not installed",
    )
    def test_successful_build_reports_verification_and_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            source = os.path.join(directory, "report.md")
            output = os.path.join(directory, "build", "report.pdf")
            with open(source, "w", encoding="utf-8") as document:
                document.write(
                    "---\ndoctype: report\ntitle: Automation Test\ntoc: false\n---\n\n# Result\n\nTest.\n"
                )
            result, payload = run_json(
                "doc", "report.md", "--root", directory, "-o", output, "--json", cwd=directory
            )
            with open(output, "rb") as artifact:
                digest = hashlib.sha256(artifact.read()).hexdigest()
        self.assertEqual(result.returncode, 0, result.stderr)
        built = payload["results"][0]
        self.assertTrue(payload["ok"])
        self.assertTrue(built["checks"]["verified"])
        self.assertEqual(built["checks"]["pdfua1"], "pass")
        self.assertEqual(built["artifact"]["sha256"], digest)


if __name__ == "__main__":
    unittest.main()
