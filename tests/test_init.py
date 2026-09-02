"""Tests for the safe, deterministic Colofon project initializer."""

import importlib.util
import os
import tempfile
import unittest

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    path = os.path.join(WS, "tools", name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


colofon_init = load("colofon_init")
make_doc = load("make_doc")


class ProjectInit(unittest.TestCase):
    def test_default_project_contains_document_book_and_notice(self):
        with tempfile.TemporaryDirectory() as parent:
            target = os.path.join(parent, "starter")
            root, files = colofon_init.initialize(target, colofon_init.plan())
            with open(os.path.join(root, "documents", "example-report.md"), encoding="utf-8") as source:
                document = source.read()
            with open(os.path.join(root, "book", "chapters", "01-welcome.md"), encoding="utf-8") as source:
                chapter = source.read()
        self.assertIn("documents/example-report.md", files)
        self.assertIn("book/book.yaml", files)
        self.assertIn("fictional", document.lower())
        self.assertIn("ai-generated", chapter.lower())

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as parent:
            target = os.path.join(parent, "starter")
            root, files = colofon_init.initialize(target, colofon_init.plan(), dry_run=True)
            self.assertFalse(os.path.exists(target))
        self.assertEqual(root, os.path.abspath(target))
        self.assertIn("README.md", files)

    def test_existing_file_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as target:
            readme = os.path.join(target, "README.md")
            with open(readme, "w", encoding="utf-8") as existing:
                existing.write("keep me\n")
            with self.assertRaises(colofon_init.InitError):
                colofon_init.initialize(target, colofon_init.plan())
            with open(readme, encoding="utf-8") as existing:
                self.assertEqual(existing.read(), "keep me\n")

    def test_brand_package_is_consumer_local_and_declared(self):
        files = colofon_init.plan(brand="example-studio")
        self.assertIn("packages/local/example-studio/0.1.0/lib.typ", files)
        self.assertIn("brand: example-studio", files["documents/example-report.md"])
        self.assertIn("brand: example-studio", files["book/book.yaml"])

    def test_book_only_readme_does_not_name_an_absent_document(self):
        files = colofon_init.plan(kind="book")
        self.assertNotIn("documents/", files["README.md"])
        self.assertIn("book/book.yaml", files["README.md"])

    def test_invalid_brand_name_is_rejected(self):
        with self.assertRaises(ValueError):
            colofon_init.plan(brand="../../private")

    def test_every_doctype_starter_passes_front_matter_validation(self):
        for doctype in make_doc.DOCTYPES:
            with self.subTest(doctype=doctype):
                source = colofon_init.document_source(doctype)
                meta, _ = make_doc.split_front_matter(source, "starter.md")
                make_doc.validate_meta(meta, doctype, "starter.md")
