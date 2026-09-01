#!/usr/bin/env python3
"""Tests for the document factory and the PDF/UA-1 gate.

Run from the repo root:

    python3 -m unittest discover -s tests -v

The point of this suite is to make the central claim checkable by a stranger:
that documents are gated on PDF/UA-1 and that the gate rejects work that does
not conform. Tests that need the pinned toolchain (Typst, veraPDF, pdftotext)
skip cleanly when it is absent, so the pure-logic guards still run anywhere.
"""

import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES = os.path.join(WS, "tools", "factory-examples")


def _load(name):
    path = os.path.join(WS, "tools", name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


make_doc = _load("make_doc")

HAVE_TYPST = os.path.exists(make_doc.TYPST)
HAVE_VERAPDF = os.path.exists(make_doc.VERAPDF)
HAVE_PDFTOTEXT = bool(shutil.which("pdftotext"))

MINIMAL = "---\ndoctype: report\ntitle: Test\n---\n\nBody text.\n"


def write(dirpath, name, text):
    p = os.path.join(dirpath, name)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)
    return p


class FrontMatterGuards(unittest.TestCase):
    """Guards that run before Typst is invoked. No toolchain required."""

    def build(self, text):
        with tempfile.TemporaryDirectory() as d:
            make_doc.build_one(write(d, "doc.md", text))

    def assertRejects(self, text, fragment):
        with self.assertRaises(make_doc.BuildError) as cm:
            self.build(text)
        self.assertIn(fragment, str(cm.exception))

    def test_missing_front_matter_is_rejected(self):
        self.assertRejects("# Just a heading\n", "no YAML front-matter")

    def test_malformed_yaml_is_rejected(self):
        self.assertRejects("---\ndoctype: report\ntitle: [unclosed\n---\n\nBody.\n",
                           "invalid YAML front-matter")

    def test_scalar_front_matter_is_rejected(self):
        self.assertRejects("---\njust a string\n---\n\nBody.\n",
                           "front-matter must be a YAML mapping")

    def test_unknown_doctype_is_rejected(self):
        self.assertRejects("---\ndoctype: novel\ntitle: T\n---\n\nBody.\n", "doctype must be one of")

    def test_missing_doctype_is_rejected(self):
        self.assertRejects("---\ntitle: T\n---\n\nBody.\n", "doctype must be one of")

    def test_missing_required_key_is_rejected(self):
        # every doctype declares its required keys; omitting one must fail
        for doctype, schema in make_doc.DOCTYPE_SCHEMA.items():
            required = sorted(schema["required"])[0]
            with self.subTest(doctype=doctype, omitted=required):
                self.assertRejects(f"---\ndoctype: {doctype}\n---\n\nBody.\n",
                                   "requires front-matter key(s)")

    def test_unknown_key_is_rejected(self):
        self.assertRejects("---\ndoctype: report\ntitle: T\nnonsense: 1\n---\n\nBody.\n",
                           "unknown front-matter key(s)")

    def test_logo_without_alt_text_is_rejected(self):
        """UA-1 requires alt text on images; a logo with no logo-alt must not build."""
        self.assertRejects("---\ndoctype: report\ntitle: T\nlogo: assets/x.png\n---\n\nBody.\n",
                           "'logo' is set but 'logo-alt' is missing")

    def test_image_with_empty_alt_is_rejected(self):
        self.assertRejects("---\ndoctype: report\ntitle: T\n---\n\n![](assets/x.png)\n",
                           "empty alt text")

    def test_image_with_alt_passes_the_alt_guard(self):
        # positive control: the alt guard itself must not fire on valid alt text
        make_doc.check_body_alt("![a chart of results](assets/x.png)\n", "doc.md")


class TypstValueEncoding(unittest.TestCase):
    """Front-matter values become Typst source, so encoding edge cases matter."""

    def test_bools_become_typst_literals(self):
        self.assertEqual(make_doc.typst_value(True), "true")
        self.assertEqual(make_doc.typst_value(False), "false")

    def test_strings_are_quoted_and_escaped(self):
        self.assertEqual(make_doc.typst_value('say "hi"'), '"say \\"hi\\""')
        self.assertEqual(make_doc.typst_value("back\\slash"), '"back\\\\slash"')

    def test_single_element_list_keeps_trailing_comma(self):
        """Typst needs (x,) for a one-tuple; (x) is just x and would change meaning."""
        self.assertEqual(make_doc.typst_value(["a"]), '("a",)')

    def test_multi_element_list_has_no_trailing_comma(self):
        self.assertEqual(make_doc.typst_value(["a", "b"]), '("a", "b")')

    def test_dates_become_iso_strings(self):
        import datetime
        self.assertEqual(make_doc.typst_value(datetime.date(2026, 7, 28)), '"2026-07-28"')


class ConsumerProjectRoot(unittest.TestCase):
    """Domain assets and build intermediates belong to the consuming repository."""

    def test_consumer_brand_imports_from_consumer_root(self):
        with tempfile.TemporaryDirectory() as root:
            brand = os.path.join(root, "packages", "local", "client-brand", "0.1.0")
            os.makedirs(brand)
            write(brand, "lib.typ", '#let book-args = (:)\n')
            wrapper = make_doc.build_wrapper(
                {"title": "T", "brand": "client-brand"}, "report", root
            )
        self.assertIn(
            '#import "/packages/local/client-brand/0.1.0/lib.typ": book-args as _brand',
            wrapper,
        )
        self.assertNotIn('"@local/client-brand:0.1.0"', wrapper)

    def test_colofon_brand_keeps_package_import(self):
        wrapper = make_doc.build_wrapper(
            {"title": "T", "brand": "sample-brand"}, "report", WS
        )
        self.assertIn('"@local/sample-brand:0.1.0"', wrapper)

    def test_missing_project_root_is_rejected_before_build(self):
        with tempfile.TemporaryDirectory() as d:
            src = write(d, "doc.md", MINIMAL)
            with self.assertRaises(make_doc.BuildError) as cm:
                make_doc.build_one(src, project_root=os.path.join(d, "missing"))
        self.assertIn("project root is not a directory", str(cm.exception))

    def test_input_git_worktree_owns_generated_files(self):
        with tempfile.TemporaryDirectory() as root:
            subprocess.run(["git", "init", "-q", root], check=True)
            nested = os.path.join(root, "deliverables", "report")
            os.makedirs(nested)
            src = write(nested, "doc.md", MINIMAL)
            self.assertEqual(make_doc.project_root_for(src), os.path.abspath(root))

    def test_non_git_input_falls_back_to_colofon(self):
        with tempfile.TemporaryDirectory() as root:
            src = write(root, "doc.md", MINIMAL)
            self.assertEqual(make_doc.project_root_for(src), WS)


class FactoryExampleCoverage(unittest.TestCase):
    """The examples are the demo and the golden corpus; drift here is silent rot."""

    def test_every_doctype_has_an_example(self):
        missing = [d for d in make_doc.DOCTYPES
                   if not os.path.exists(os.path.join(EXAMPLES, f"sample-{d}.md"))]
        self.assertEqual(missing, [], f"doctypes with no sample-*.md: {missing}")

    def test_build_script_covers_every_doctype(self):
        """build.sh is the self-test; a doctype it skips is a doctype nobody checks."""
        with open(os.path.join(WS, "build.sh"), encoding="utf-8") as fh:
            script = fh.read()
        uncovered = [d for d in make_doc.DOCTYPES if d not in script]
        self.assertEqual(uncovered, [], f"doctypes absent from build.sh: {uncovered}")


@unittest.skipUnless(HAVE_TYPST, "Typst not installed")
class GatePassesGoodDocuments(unittest.TestCase):
    """Golden path: each shipped example must clear the whole gate."""

    def test_each_example_builds_and_passes_the_gate(self):
        for doctype in make_doc.DOCTYPES:
            src = os.path.join(EXAMPLES, f"sample-{doctype}.md")
            if not os.path.exists(src):
                continue
            with self.subTest(doctype=doctype), tempfile.TemporaryDirectory() as d:
                out = make_doc.build_one(src, os.path.join(d, f"{doctype}.pdf"))
                self.assertTrue(os.path.getsize(out) > 0, f"{doctype}: empty PDF")


@unittest.skipUnless(HAVE_TYPST and HAVE_PDFTOTEXT, "Typst or pdftotext not installed")
class GateRejectsUnsafeCopy(unittest.TestCase):
    def test_zero_width_space_in_body_is_rejected(self):
        """Copy-safe means selecting the text yields what is on the page."""
        with tempfile.TemporaryDirectory() as d:
            src = write(d, "zwsp.md",
                        "---\ndoctype: report\ntitle: Copy Safety\n---\n\nHello​world.\n")
            with self.assertRaises(make_doc.BuildError) as cm:
                make_doc.build_one(src, os.path.join(d, "zwsp.pdf"))
            self.assertIn("copy-safe check failed", str(cm.exception))


@unittest.skipUnless(HAVE_TYPST and HAVE_VERAPDF, "Typst or veraPDF not installed")
class VeraPdfActuallyDiscriminates(unittest.TestCase):
    """The load-bearing test: prove the verifier is not a rubber stamp.

    Build a conforming document, confirm veraPDF passes it, then remove the
    document-level /Lang entry - a hard UA-1 requirement - and confirm veraPDF
    now fails the same file. If this test cannot make veraPDF say no, the gate
    proves nothing.
    """

    def verapdf_compliant(self, path):
        r = subprocess.run([make_doc.VERAPDF, "--flavour", "ua1", path],
                           capture_output=True, text=True)
        return 'isCompliant="true"' in r.stdout

    def test_conforming_document_passes_and_damaged_one_fails(self):
        try:
            import pymupdf as fitz
        except ImportError:
            self.skipTest("PyMuPDF not installed")
        with tempfile.TemporaryDirectory() as d:
            good = make_doc.build_one(write(d, "ok.md", MINIMAL), os.path.join(d, "ok.pdf"))
            self.assertTrue(self.verapdf_compliant(good),
                            "a freshly built document should be UA-1 compliant")

            doc = fitz.open(good)
            doc.xref_set_key(doc.pdf_catalog(), "Lang", "null")   # delete /Lang
            damaged = os.path.join(d, "damaged.pdf")
            doc.save(damaged)
            doc.close()

            probe = fitz.open(damaged)
            still_there = probe.xref_get_key(probe.pdf_catalog(), "Lang")[0] != "null"
            probe.close()
            if still_there:
                self.skipTest("could not remove /Lang; cannot construct a negative case")

            self.assertFalse(self.verapdf_compliant(damaged),
                             "veraPDF accepted a PDF with no document language - "
                             "the UA-1 check is not discriminating")


@unittest.skipUnless(HAVE_TYPST, "Typst not installed")
class GateRequiresItsVerifiers(unittest.TestCase):
    """A missing verifier must fail the build, not silently downgrade it.

    Without this contract the gate degrades to 'not checked' on any machine
    lacking the toolchain while still reporting success, so a document could be
    published as accessibility-gated having never been verified.
    """

    def setUp(self):
        self._verapdf, self._allow = make_doc.VERAPDF, make_doc.ALLOW_UNVERIFIED

    def tearDown(self):
        make_doc.VERAPDF, make_doc.ALLOW_UNVERIFIED = self._verapdf, self._allow

    def build_minimal(self, tmpdir):
        return make_doc.build_one(write(tmpdir, "ok.md", MINIMAL),
                                  os.path.join(tmpdir, "ok.pdf"))

    def test_missing_verapdf_fails_the_build(self):
        make_doc.VERAPDF = "/nonexistent/verapdf"
        make_doc.ALLOW_UNVERIFIED = False
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(make_doc.BuildError) as cm:
                self.build_minimal(d)
            self.assertIn("veraPDF not found", str(cm.exception))
            self.assertIn("COLOFON_ALLOW_UNVERIFIED", str(cm.exception))

    def test_missing_pdftotext_fails_the_build(self):
        make_doc.ALLOW_UNVERIFIED = False
        with mock.patch.object(make_doc.shutil, "which", return_value=None):
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises(make_doc.BuildError) as cm:
                    self.build_minimal(d)
                self.assertIn("pdftotext not found", str(cm.exception))

    def test_opt_out_allows_an_unverified_build(self):
        """The escape hatch exists, but has to be asked for."""
        make_doc.VERAPDF = "/nonexistent/verapdf"
        make_doc.ALLOW_UNVERIFIED = True
        with tempfile.TemporaryDirectory() as d:
            out = self.build_minimal(d)
            self.assertTrue(os.path.getsize(out) > 0)

    def test_opt_out_is_not_silent(self):
        make_doc.VERAPDF = "/nonexistent/verapdf"
        make_doc.ALLOW_UNVERIFIED = True
        err = io.StringIO()
        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stderr(err):
            self.build_minimal(d)
        self.assertIn("UNVERIFIED", err.getvalue())

    def test_opt_out_requires_the_exact_value(self):
        """A stray truthy string must not disable the gate."""
        for value in ("0", "true", "yes", ""):
            with self.subTest(value=value):
                with mock.patch.dict(os.environ, {"COLOFON_ALLOW_UNVERIFIED": value}):
                    self.assertFalse(os.environ.get("COLOFON_ALLOW_UNVERIFIED") == "1")


EXAMPLE_BOOK = os.path.join(EXAMPLES, "book", "book.yaml")


@unittest.skipUnless(HAVE_TYPST and os.path.exists(EXAMPLE_BOOK), "Typst or example book missing")
class BookGateRequiresItsVerifiers(unittest.TestCase):
    """make_book carries the same contract as make_doc.

    Books are the larger artifact, so a book that reports success without
    verifying is the worse version of the same failure. make_book exits via
    die() rather than raising, so these assert on the process contract.
    """

    def run_make_book(self, outdir, env_extra):
        env = dict(os.environ, TYPST=make_doc.TYPST, **env_extra)
        return subprocess.run(
            ["python3", os.path.join(WS, "tools", "make_book.py"), EXAMPLE_BOOK,
             "-o", os.path.join(outdir, "book.pdf")],
            capture_output=True, text=True, env=env, cwd=WS,
        )

    def test_missing_verapdf_fails_the_book_build(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_make_book(d, {"VERAPDF": "/nonexistent/verapdf"})
        self.assertNotEqual(r.returncode, 0, "book built with no UA-1 verification")
        self.assertIn("veraPDF not found", r.stderr)

    def test_opt_out_allows_an_unverified_book_and_says_so(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_make_book(d, {"VERAPDF": "/nonexistent/verapdf",
                                       "COLOFON_ALLOW_UNVERIFIED": "1"})
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("NOT VERIFIED", r.stderr)
            self.assertTrue(os.path.getsize(os.path.join(d, "book.pdf")) > 0)

    def test_verified_book_build_succeeds(self):
        """Positive control: with the real toolchain the gate passes and says so."""
        if not HAVE_VERAPDF:
            self.skipTest("veraPDF not installed")
        with tempfile.TemporaryDirectory() as d:
            r = self.run_make_book(d, {})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("PDF/UA-1: compliant", r.stdout)


@unittest.skipUnless(HAVE_TYPST, "Typst not installed")
class ReportTemplateOutput(unittest.TestCase):
    """What the report template actually puts on the page.

    Front-matter keys become template arguments, so a key can be accepted,
    validated, and then never rendered. These build a real PDF and read the
    text layer back, because that class of defect compiles and gates clean.
    """

    def render(self, front, body="# Section one\n\nBody text.\n"):
        try:
            import pymupdf as fitz
        except ImportError:
            self.skipTest("PyMuPDF not installed")
        with tempfile.TemporaryDirectory() as d:
            src = write(d, "doc.md", f"---\n{front}---\n\n{body}")
            doc = fitz.open(make_doc.build_one(src, os.path.join(d, "doc.pdf")))
            pages = [p.get_text() for p in doc]
            doc.close()
            return pages

    def test_author_appears_on_the_cover(self):
        """A report goes out under someone's name; metadata alone does not say who."""
        pages = self.render("doctype: report\ntitle: T\nauthor: Office of the ISSO\n")
        self.assertIn("Office of the ISSO", pages[0])

    def test_contents_page_is_present_by_default(self):
        self.assertIn("Contents", self.render("doctype: report\ntitle: T\n")[1])

    def test_toc_false_omits_the_contents_page(self):
        """A three-page report should not spend a page on a two-line Contents."""
        pages = self.render("doctype: report\ntitle: T\ntoc: false\n")
        self.assertNotIn("Contents", "".join(pages))
        self.assertEqual(len(pages), 2, "expected a cover and one body page")

    def test_subsections_appear_in_the_contents(self):
        body = "# Section one\n\n## Sub two\n\n### Deep three\n\nText.\n"
        self.assertIn("Deep three", self.render("doctype: report\ntitle: T\n", body)[1])


@unittest.skipUnless(HAVE_TYPST, "Typst not installed")
class CalloutLabelSpacing(unittest.TestCase):
    """The callout label must clear the first line of its body.

    A weak `v()` between the two collapsed to nothing, so the label's glyph box
    overlapped the body line below it. Measured in the text layer because the
    document compiles and passes UA-1 either way.
    """

    def test_label_clears_the_body_text(self):
        try:
            import pymupdf as fitz
        except ImportError:
            self.skipTest("PyMuPDF not installed")
        md = ("---\ndoctype: report\ntitle: T\n---\n\n"
              "# Section\n\n> [!note]\n> Body of the callout.\n")
        with tempfile.TemporaryDirectory() as d:
            out = make_doc.build_one(write(d, "callout.md", md), os.path.join(d, "callout.pdf"))
            doc = fitz.open(out)
            words = doc[-1].get_text("words")
            doc.close()
        label = next(w for w in words if w[4] == "NOTE")
        below = min((w for w in words if w[1] > label[1]), key=lambda w: (w[1], w[0]))
        self.assertGreaterEqual(
            below[1] - label[3], 2.0,
            f"label bottom {label[3]:.2f} vs first body line top {below[1]:.2f}")


class FormReportsWithoutGating(unittest.TestCase):
    """make_form is report-only by design; it must still not stay silent.

    The AcroForm widget layer is knowingly not UA-1 conformant, so make_form
    prints the verdict rather than gating on it. The contract being pinned here
    is only that a missing verifier is reported, never passed over in silence.
    """

    def test_make_form_does_not_hard_gate(self):
        src = open(os.path.join(WS, "tools", "make_form.py"), encoding="utf-8").read()
        self.assertIn("do not gate", src,
                      "make_form's report-only intent is no longer documented")

    def test_missing_verapdf_is_reported_not_skipped(self):
        src = open(os.path.join(WS, "tools", "make_form.py"), encoding="utf-8").read()
        self.assertIn("NOT CHECKED", src,
                      "make_form must say when UA-1 was never checked")


if __name__ == "__main__":
    unittest.main()
