#!/usr/bin/env python3
"""One-off migration script to create catalog/adventures.json from assets/adventures/manifest.json."""

import json
from pathlib import Path
import sys

BUNDLE_URL_PREFIX = "https://assets.phroller.com/adventures/files/"


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    manifest_path = repo_root / "assets" / "adventures" / "manifest.json"
    catalog_dir = repo_root / "catalog"
    i18n_dir = catalog_dir / "i18n"

    catalog_dir.mkdir(parents=True, exist_ok=True)
    i18n_dir.mkdir(parents=True, exist_ok=True)
    (i18n_dir / ".gitkeep").touch()

    languages_path = catalog_dir / "languages.json"
    with languages_path.open("w", encoding="utf-8") as f:
        json.dump(["pt", "zh"], f, ensure_ascii=False)
        f.write("\n")

    with manifest_path.open("r", encoding="utf-8") as f:
        entries = json.load(f)

    out_entries = []
    for entry in entries:
        out_entry = {}
        for k, v in entry.items():
            if k == "id":
                out_entry["id"] = v
                out_entry["source"] = "en"
            elif k == "bundleUrl":
                if not isinstance(v, str) or not v.startswith(BUNDLE_URL_PREFIX):
                    print(
                        f"Error: bundleUrl for {entry.get('id')} does not start with {BUNDLE_URL_PREFIX}: {v}",
                        file=sys.stderr,
                    )
                    return 1
                out_entry["bundle"] = v[len(BUNDLE_URL_PREFIX) :]
            elif k == "version":
                out_entry["version"] = float(v)
            else:
                out_entry[k] = v
        out_entries.append(out_entry)

    adventures_path = catalog_dir / "adventures.json"
    with adventures_path.open("w", encoding="utf-8") as f:
        json.dump(out_entries, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
