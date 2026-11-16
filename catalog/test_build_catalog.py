#!/usr/bin/env python3
"""Unit tests for build_catalog.py."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build_catalog  # noqa: E402


def _make_phvtt(path: Path, setup_obj: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("setup.json", json.dumps(setup_obj or {"name": "Test"}))


class BuildCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "catalog" / "i18n").mkdir(parents=True)
        (self.root / "assets" / "adventures" / "files").mkdir(parents=True)
        (self.root / "assets" / "images").mkdir(parents=True)

        (self.root / "catalog" / "languages.json").write_text(
            json.dumps(["pt", "zh"]), encoding="utf-8"
        )
        (self.root / "assets" / "images" / "test.png").write_bytes(b"png")
        _make_phvtt(self.root / "assets" / "adventures" / "files" / "Test.phvtt")

        self.base_entry = {
            "id": "test_adv",
            "source": "en",
            "title": "Test Title",
            "description": "Test Description",
            "bundle": "Test.phvtt",
            "previewImageUrl": "https://assets.phroller.com/images/test.png",
            "tags": ["map", "cave"],
            "artistUrls": {},
            "version": 1.0,
        }
        self._write_adventures([self.base_entry])

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_adventures(self, entries: list[dict]) -> None:
        (self.root / "catalog" / "adventures.json").write_text(
            json.dumps(entries, indent=2), encoding="utf-8"
        )

    def test_no_i18n_file_falls_back_to_source(self) -> None:
        rc = build_catalog.run(self.root)
        self.assertEqual(rc, 0)
        pt = json.loads(
            (self.root / "assets" / "adventures" / "manifest.pt.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(len(pt), 1)
        self.assertEqual(pt[0]["title"], "Test Title")
        self.assertEqual(pt[0]["description"], "Test Description")
        self.assertEqual(pt[0]["language"], "en")
        self.assertEqual(pt[0]["languages"], ["en"])
        self.assertFalse(pt[0]["live"])
        self.assertEqual(pt[0]["tagNames"], {})

    def test_translated_title_sets_language_and_keeps_english_description(self) -> None:
        (self.root / "catalog" / "i18n" / "adventures.pt.json").write_text(
            json.dumps({"test_adv": {"title": "Título de Teste"}}),
            encoding="utf-8",
        )
        rc = build_catalog.run(self.root)
        self.assertEqual(rc, 0)
        pt = json.loads(
            (self.root / "assets" / "adventures" / "manifest.pt.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(pt[0]["title"], "Título de Teste")
        self.assertEqual(pt[0]["description"], "Test Description")
        self.assertEqual(pt[0]["language"], "pt")

    def test_variant_updates_bundle_url_for_that_tag_only(self) -> None:
        _make_phvtt(self.root / "assets" / "adventures" / "files" / "pt" / "Test.phvtt")
        entry = dict(self.base_entry, variants={"pt": "pt/Test.phvtt"})
        self._write_adventures([entry])

        rc = build_catalog.run(self.root)
        self.assertEqual(rc, 0)
        pt = json.loads(
            (self.root / "assets" / "adventures" / "manifest.pt.json").read_text(
                encoding="utf-8"
            )
        )
        zh = json.loads(
            (self.root / "assets" / "adventures" / "manifest.zh.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            pt[0]["bundleUrl"],
            "https://assets.phroller.com/adventures/files/pt/Test.phvtt",
        )
        self.assertEqual(
            zh[0]["bundleUrl"],
            "https://assets.phroller.com/adventures/files/Test.phvtt",
        )
        self.assertEqual(pt[0]["languages"], ["en", "pt"])
        self.assertEqual(zh[0]["languages"], ["en", "pt"])

    def test_live_bundle_tables_detected(self) -> None:
        _make_phvtt(
            self.root / "assets" / "adventures" / "files" / "Test.phvtt",
            {"i18n": {"source": "en", "tables": {"pt": "local://i18n/pt.json"}}},
        )
        entry = dict(self.base_entry, world=True)
        self._write_adventures([entry])
        rc = build_catalog.run(self.root)
        self.assertEqual(rc, 0)
        pt = json.loads(
            (self.root / "assets" / "adventures" / "manifest.pt.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(pt[0]["live"])
        self.assertTrue(pt[0]["world"])
        self.assertEqual(pt[0]["languages"], ["en", "pt"])

    def test_non_english_source_entry_excluded_from_base_manifest(self) -> None:
        _make_phvtt(self.root / "assets" / "adventures" / "files" / "ZhOnly.phvtt")
        zh_entry = {
            "id": "zh_only",
            "source": "zh",
            "title": "中文冒险",
            "description": "描述",
            "bundle": "ZhOnly.phvtt",
            "previewImageUrl": "https://assets.phroller.com/images/test.png",
            "tags": ["map"],
            "artistUrls": {},
            "version": 1.0,
        }
        self._write_adventures([self.base_entry, zh_entry])
        rc = build_catalog.run(self.root)
        self.assertEqual(rc, 0)

        en = json.loads(
            (self.root / "assets" / "adventures" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        pt = json.loads(
            (self.root / "assets" / "adventures" / "manifest.pt.json").read_text(
                encoding="utf-8"
            )
        )
        zh = json.loads(
            (self.root / "assets" / "adventures" / "manifest.zh.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual([e["id"] for e in en], ["test_adv"])
        self.assertEqual([e["id"] for e in pt], ["test_adv", "zh_only"])
        self.assertEqual([e["id"] for e in zh], ["test_adv", "zh_only"])

    def test_tags_preserved_and_tag_names_populated(self) -> None:
        (self.root / "catalog" / "i18n" / "tags.pt.json").write_text(
            json.dumps({"map": "mapa", "unused": "não usado"}), encoding="utf-8"
        )
        rc = build_catalog.run(self.root)
        self.assertEqual(rc, 0)
        pt = json.loads(
            (self.root / "assets" / "adventures" / "manifest.pt.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(pt[0]["tags"], ["map", "cave"])
        self.assertEqual(pt[0]["tagNames"], {"map": "mapa"})

    def test_validation_rule_1_duplicate_id_fails(self) -> None:
        self._write_adventures([self.base_entry, dict(self.base_entry)])
        rc = build_catalog.run(self.root)
        self.assertEqual(rc, 1)
        self.assertFalse((self.root / "assets" / "adventures" / "manifest.json").exists())

    def test_validation_rule_2_missing_bundle_or_variant_fails(self) -> None:
        bad = dict(self.base_entry, bundle="Missing.phvtt")
        self._write_adventures([bad])
        self.assertEqual(build_catalog.run(self.root), 1)
        self.assertFalse((self.root / "assets" / "adventures" / "manifest.json").exists())

        bad_variant = dict(self.base_entry, variants={"pt": "pt/Missing.phvtt"})
        self._write_adventures([bad_variant])
        self.assertEqual(build_catalog.run(self.root), 1)
        self.assertFalse((self.root / "assets" / "adventures" / "manifest.json").exists())

    def test_validation_rule_3_unknown_id_in_i18n_fails(self) -> None:
        (self.root / "catalog" / "i18n" / "adventures.pt.json").write_text(
            json.dumps({"nonexistent": {"title": "Nope"}}), encoding="utf-8"
        )
        self.assertEqual(build_catalog.run(self.root), 1)
        self.assertFalse((self.root / "assets" / "adventures" / "manifest.json").exists())

    def test_validation_rule_4_unlisted_language_or_source_variant_fails(self) -> None:
        bad_variant_lang = dict(self.base_entry, variants={"fr": "Test.phvtt"})
        self._write_adventures([bad_variant_lang])
        self.assertEqual(build_catalog.run(self.root), 1)
        self.assertFalse((self.root / "assets" / "adventures" / "manifest.json").exists())

        # Variant in the entry's own source language
        (self.root / "catalog" / "languages.json").write_text(
            json.dumps(["en", "pt", "zh"]), encoding="utf-8"
        )
        same_source_variant = dict(self.base_entry, variants={"en": "Test.phvtt"})
        self._write_adventures([same_source_variant])
        self.assertEqual(build_catalog.run(self.root), 1)
        self.assertFalse((self.root / "assets" / "adventures" / "manifest.json").exists())

    def test_validation_rule_5_missing_preview_image_fails(self) -> None:
        bad_preview = dict(
            self.base_entry,
            previewImageUrl="https://assets.phroller.com/images/missing%20file.png",
        )
        self._write_adventures([bad_preview])
        self.assertEqual(build_catalog.run(self.root), 1)
        self.assertFalse((self.root / "assets" / "adventures" / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
