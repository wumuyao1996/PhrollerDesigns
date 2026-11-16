#!/usr/bin/env python3
"""Build adventure manifests from catalog/ sources and validate all references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import urllib.parse
import zipfile

ASSETS_BASE_URL = "https://assets.phroller.com/"
BUNDLE_URL_PREFIX = "https://assets.phroller.com/adventures/files/"


class CatalogValidationError(Exception):
    """Raised when catalog validation fails."""


def _read_bundle_live_languages(bundle_path: Path) -> list[str]:
    if not bundle_path.is_file():
        raise CatalogValidationError(f"Missing bundle file: {bundle_path}")
    try:
        with zipfile.ZipFile(bundle_path, "r") as zf:
            try:
                raw_setup = zf.read("setup.json")
            except KeyError as exc:
                raise CatalogValidationError(
                    f"Bundle missing setup.json: {bundle_path}"
                ) from exc
    except zipfile.BadZipFile as exc:
        raise CatalogValidationError(
            f"Bundle is not a valid zip file: {bundle_path}"
        ) from exc

    try:
        setup = json.loads(raw_setup.decode("utf-8"))
    except Exception as exc:
        raise CatalogValidationError(
            f"Invalid setup.json in bundle: {bundle_path}"
        ) from exc

    if not isinstance(setup, dict):
        return []
    i18n = setup.get("i18n")
    if not isinstance(i18n, dict):
        return []
    tables = i18n.get("tables")
    if not isinstance(tables, dict):
        return []
    return [str(k) for k, v in tables.items() if isinstance(k, str) and v]


def _validate_preview_url(root: Path, url: str, context: str) -> None:
    if not isinstance(url, str):
        raise CatalogValidationError(f"Invalid previewImageUrl for {context}: {url!r}")
    if url.startswith(ASSETS_BASE_URL):
        rel = urllib.parse.unquote(url[len(ASSETS_BASE_URL) :])
        target = root / "assets" / rel
        if not target.is_file():
            raise CatalogValidationError(
                f"Missing previewImageUrl file for {context}: {target}"
            )


def build_manifests(root: Path) -> dict[Path, str]:
    """Validate catalog under `root` and return {output_path: json_content}."""
    catalog_dir = root / "catalog"
    i18n_dir = catalog_dir / "i18n"
    adventures_dir = root / "assets" / "adventures"
    files_dir = adventures_dir / "files"

    languages_path = catalog_dir / "languages.json"
    adventures_path = catalog_dir / "adventures.json"

    with languages_path.open("r", encoding="utf-8") as f:
        languages: list[str] = json.load(f)
    if not isinstance(languages, list) or not all(
        isinstance(t, str) for t in languages
    ):
        raise CatalogValidationError("catalog/languages.json must be a list of strings")
    language_set = set(languages)

    with adventures_path.open("r", encoding="utf-8") as f:
        source_entries: list[dict] = json.load(f)

    # Rule 1: ids are unique
    seen_ids: set[str] = set()
    for entry in source_entries:
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not entry_id:
            raise CatalogValidationError(f"Invalid or missing id in entry: {entry!r}")
        if entry_id in seen_ids:
            raise CatalogValidationError(f"Duplicate adventure id: {entry_id}")
        seen_ids.add(entry_id)

    # Rule 4 (part 1): every i18n file's tag is in languages.json
    if i18n_dir.is_dir():
        for p in sorted(i18n_dir.glob("*.json")):
            parts = p.name.split(".")
            # Expected: adventures.<tag>.json or tags.<tag>.json
            if len(parts) == 3 and parts[0] in ("adventures", "tags") and parts[2] == "json":
                tag = parts[1]
                if tag not in language_set:
                    raise CatalogValidationError(
                        f"i18n file {p.name} has tag '{tag}' not in languages.json"
                    )
            else:
                raise CatalogValidationError(f"Unexpected i18n file name: {p.name}")

    # Load i18n files per language
    adv_i18n_by_tag: dict[str, dict[str, dict]] = {}
    tags_i18n_by_tag: dict[str, dict[str, str]] = {}
    for tag in languages:
        adv_i18n_path = i18n_dir / f"adventures.{tag}.json"
        if adv_i18n_path.is_file():
            with adv_i18n_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise CatalogValidationError(f"{adv_i18n_path.name} must be a JSON object")
            # Rule 3: every id in an i18n file exists in the source
            for translated_id, fields in data.items():
                if translated_id not in seen_ids:
                    raise CatalogValidationError(
                        f"Unknown id '{translated_id}' in {adv_i18n_path.name}"
                    )
                if not isinstance(fields, dict):
                    raise CatalogValidationError(
                        f"Entry '{translated_id}' in {adv_i18n_path.name} must be an object"
                    )
                if "previewImageUrl" in fields:
                    _validate_preview_url(
                        root,
                        fields["previewImageUrl"],
                        f"{adv_i18n_path.name}:{translated_id}",
                    )
            adv_i18n_by_tag[tag] = data
        else:
            adv_i18n_by_tag[tag] = {}

        tags_i18n_path = i18n_dir / f"tags.{tag}.json"
        if tags_i18n_path.is_file():
            with tags_i18n_path.open("r", encoding="utf-8") as f:
                tag_data = json.load(f)
            if not isinstance(tag_data, dict):
                raise CatalogValidationError(f"{tags_i18n_path.name} must be a JSON object")
            tags_i18n_by_tag[tag] = {
                str(k): str(v) for k, v in tag_data.items() if isinstance(v, str)
            }
        else:
            tags_i18n_by_tag[tag] = {}

    # Validate each source entry: bundles, variants, previewImageUrl, live tables
    base_live_langs_by_id: dict[str, list[str]] = {}
    variant_live_langs_by_id_tag: dict[tuple[str, str], list[str]] = {}

    for entry in source_entries:
        entry_id = entry["id"]
        source_lang = entry.get("source", "en")
        bundle_rel = entry.get("bundle")
        if not isinstance(bundle_rel, str) or not bundle_rel:
            raise CatalogValidationError(f"Missing bundle for {entry_id}")

        # Rule 2 (base bundle) + zip/live check
        base_bundle_path = files_dir / bundle_rel
        base_live_langs_by_id[entry_id] = _read_bundle_live_languages(base_bundle_path)

        # Rule 5 (source previewImageUrl)
        _validate_preview_url(root, entry.get("previewImageUrl", ""), entry_id)

        # Variants validation (Rules 2 & 4)
        variants = entry.get("variants") or {}
        if not isinstance(variants, dict):
            raise CatalogValidationError(f"variants for {entry_id} must be an object")
        for v_tag, v_rel in variants.items():
            if v_tag not in language_set:
                raise CatalogValidationError(
                    f"Variant tag '{v_tag}' on {entry_id} is not in languages.json"
                )
            if v_tag == source_lang:
                raise CatalogValidationError(
                    f"Variant tag '{v_tag}' on {entry_id} matches its source language '{source_lang}'"
                )
            if not isinstance(v_rel, str) or not v_rel:
                raise CatalogValidationError(
                    f"Invalid variant path for {entry_id} ({v_tag})"
                )
            v_path = files_dir / v_rel
            variant_live_langs_by_id_tag[(entry_id, v_tag)] = (
                _read_bundle_live_languages(v_path)
            )

    outputs: dict[Path, str] = {}

    # 1. Base English manifest: assets/adventures/manifest.json
    en_manifest: list[dict] = []
    for entry in source_entries:
        if entry.get("source") != "en":
            continue
        en_manifest.append(
            {
                "id": entry["id"],
                "title": entry["title"],
                "description": entry["description"],
                "bundleUrl": BUNDLE_URL_PREFIX + entry["bundle"],
                "previewImageUrl": entry["previewImageUrl"],
                "tags": list(entry["tags"]),
                "artistUrls": dict(entry["artistUrls"]),
                "version": float(entry["version"]),
            }
        )
    outputs[adventures_dir / "manifest.json"] = (
        json.dumps(en_manifest, indent=2, ensure_ascii=False) + "\n"
    )

    # 2. Per-language manifests: assets/adventures/manifest.<tag>.json
    for tag in languages:
        adv_i18n = adv_i18n_by_tag[tag]
        tags_i18n = tags_i18n_by_tag[tag]
        lang_manifest: list[dict] = []

        for entry in source_entries:
            entry_id = entry["id"]
            source_lang = entry["source"]
            variants = entry.get("variants") or {}
            tr = adv_i18n.get(entry_id, {})

            has_translated_title = (
                isinstance(tr.get("title"), str) and bool(tr.get("title"))
            )
            title = tr["title"] if has_translated_title else entry["title"]
            description = (
                tr["description"]
                if isinstance(tr.get("description"), str) and bool(tr.get("description"))
                else entry["description"]
            )
            preview_url = (
                tr["previewImageUrl"]
                if isinstance(tr.get("previewImageUrl"), str)
                and bool(tr.get("previewImageUrl"))
                else entry["previewImageUrl"]
            )

            chosen_bundle_rel = variants.get(tag, entry["bundle"])
            if tag in variants:
                chosen_live_langs = variant_live_langs_by_id_tag[(entry_id, tag)]
            else:
                chosen_live_langs = base_live_langs_by_id[entry_id]

            all_languages = sorted(
                {source_lang, *variants.keys(), *base_live_langs_by_id[entry_id]}
            )
            tag_names = {
                t: tags_i18n[t] for t in entry["tags"] if t in tags_i18n
            }

            lang_manifest.append(
                {
                    "id": entry_id,
                    "title": title,
                    "description": description,
                    "bundleUrl": BUNDLE_URL_PREFIX + chosen_bundle_rel,
                    "previewImageUrl": preview_url,
                    "tags": list(entry["tags"]),
                    "artistUrls": dict(entry["artistUrls"]),
                    "version": float(entry["version"]),
                    "language": tag if has_translated_title else source_lang,
                    "languages": all_languages,
                    "world": bool(entry.get("world", False)),
                    "live": bool(chosen_live_langs),
                    "tagNames": tag_names,
                }
            )

        outputs[adventures_dir / f"manifest.{tag}.json"] = (
            json.dumps(lang_manifest, indent=2, ensure_ascii=False) + "\n"
        )

    return outputs


def run(root: Path, check: bool = False) -> int:
    try:
        outputs = build_manifests(root)
    except CatalogValidationError as exc:
        print(f"Catalog validation failed: {exc}", file=sys.stderr)
        return 1

    if check:
        for path, expected in outputs.items():
            if not path.is_file():
                print(f"Missing generated file: {path}", file=sys.stderr)
                return 1
            actual = path.read_text(encoding="utf-8")
            if actual != expected:
                print(f"Out-of-date generated file: {path}", file=sys.stderr)
                return 1
        return 0

    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify generated files match disk without writing anything.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Repository root directory.",
    )
    args = parser.parse_args(argv)
    return run(args.root, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
