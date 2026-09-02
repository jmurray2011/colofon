import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

import release_assets
import release_notes

WS = Path(os.environ.get("COLOFON_ROOT", Path(__file__).resolve().parent.parent))


class ReleaseAssetTests(unittest.TestCase):
    def test_manifest_matches_compliance_and_form_dependency(self):
        manifest = release_assets.load_manifest()
        compliance = (WS / "AGPL-COMPLIANCE.md").read_text(encoding="utf-8")
        requirements = (WS / "tools" / "requirements-form-container.txt").read_text(
            encoding="utf-8"
        )

        self.assertIn("PyMuPDF==1.28.2", requirements)
        for source in manifest.values():
            self.assertIn(source["filename"], compliance)
            self.assertEqual(len(source["sha256"]), 64)

    def test_existing_asset_is_verified_without_network(self):
        payload = b"corresponding source fixture\n"
        digest = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "assets"
            destination.mkdir()
            (destination / "fixture.tar.gz").write_bytes(payload)
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "fixture": {
                            "filename": "fixture.tar.gz",
                            "sha256": digest,
                            "url": "https://example.invalid/fixture.tar.gz",
                        }
                    }
                ),
                encoding="utf-8",
            )

            paths = release_assets.fetch(destination, manifest)

        self.assertEqual([path.name for path in paths], ["fixture.tar.gz"])

    def test_invalid_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "manifest.json"
            manifest.write_text(
                '{"bad":{"filename":"../bad","sha256":"x","url":"http://example.com"}}',
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                release_assets.load_manifest(manifest)


class ReleaseNotesTests(unittest.TestCase):
    def test_notes_include_changelog_images_and_source_hashes(self):
        notes = release_notes.render("v0.2.1")
        self.assertIn("Confine book chapters", notes)
        self.assertIn("ghcr.io/jmurray2011/colofon:0.2.1", notes)
        for source in release_assets.load_manifest().values():
            self.assertIn(source["filename"], notes)
            self.assertIn(source["sha256"], notes)

    def test_unknown_release_is_rejected(self):
        with self.assertRaises(ValueError):
            release_notes.render("99.99.99")


if __name__ == "__main__":
    unittest.main()
