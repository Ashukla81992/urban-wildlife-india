#!/usr/bin/env python3
"""
apply_metadata.py — Apply correct species/title/tags to gallery index.md from a
  per-slug mapping (no range-based logic). Only updates entries that appear in
  the mapping; leaves others as draft.

Slug must match watermark.py: stem.lower().replace(" ", "-").replace("_", "-")

Usage:
  python3 scripts/apply_metadata.py [--dry-run]
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GALLERY_DIR = REPO_ROOT / "content" / "gallery"


def slug_from_stem(stem: str) -> str:
    """Same as watermark.py slug: stem.lower().replace(' ', '-').replace('_', '-')."""
    return stem.lower().replace(" ", "-").replace("_", "-")


def read_frontmatter(md_path: Path):
    text = md_path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n?(.*)", text, re.DOTALL)
    if not match:
        return {}, text
    fm_raw, body = match.group(1), match.group(2)
    fm = {}
    for line in fm_raw.split("\n"):
        m = re.match(r"^(\w+):\s*(.*)", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                fm[key] = (
                    [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
                    if inner
                    else []
                )
            elif val.lower() in ("true", "false"):
                fm[key] = val.lower() == "true"
            else:
                fm[key] = val.strip('"').strip("'")
    return fm, body


def write_frontmatter(md_path: Path, fm: dict, body: str) -> None:
    def fmt_val(v):
        if isinstance(v, list):
            return "[" + ", ".join(f'"{x}"' for x in v) + "]"
        if isinstance(v, bool):
            return str(v).lower()
        if isinstance(v, str) and any(c in v for c in ":#{}[]|>&*"):
            return f'"{v}"'
        return str(v)

    lines = ["---"]
    for k, v in fm.items():
        lines.append(f"{k}: {fmt_val(v)}")
    lines.append("---")
    lines.append(body.strip() if body else "")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# Per-slug metadata. Key = gallery dir name (slug from raw filename).
# Only entries listed here get updated and set draft: false.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from scripts.metadata_mapping import MAPPING


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("Dry run — no files will be written.")

    updated = 0
    skipped = 0
    for gdir in sorted(GALLERY_DIR.iterdir()):
        if not gdir.is_dir() or gdir.name.startswith("_"):
            continue
        slug = gdir.name
        if slug not in MAPPING:
            skipped += 1
            continue

        md_path = gdir / "index.md"
        if not md_path.exists():
            print(f"  [skip] no index.md: {gdir.name}")
            continue

        meta = MAPPING[slug]
        fm, body = read_frontmatter(md_path)

        if meta.get("title") is not None:
            fm["title"] = meta["title"]
        if meta.get("species") is not None:
            fm["species"] = meta["species"]
        if meta.get("location") is not None:
            fm["location"] = meta["location"]
        if meta.get("categories") is not None:
            fm["categories"] = meta["categories"]
        if meta.get("tags") is not None:
            fm["tags"] = meta["tags"]
        if meta.get("caption") is not None:
            fm["caption"] = meta["caption"]
        if meta.get("description") is not None:
            fm["description"] = meta["description"]

        fm["draft"] = False

        if not dry_run:
            write_frontmatter(md_path, fm, body)
        updated += 1

    print(f"Updated {updated} entries, skipped {skipped} (not in mapping).")
    if dry_run and updated:
        print("Run without --dry-run to write files.")


if __name__ == "__main__":
    main()
