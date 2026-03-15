#!/usr/bin/env python3
"""
watermark.py — Urban Wildlife India
====================================
Batch-processes raw photos:
  1. Adds a semi-transparent watermark (bottom-right corner).
  2. Converts to WebP at configurable quality.
  3. Drops output into content/gallery/<slug>/ as a page bundle
     so Hugo can pick them up as image resources.

Usage
-----
  ~/venv/bin/python3 scripts/watermark.py

Folder layout expected:
  raw_photos/
      leopard-on-boundary-wall.jpg
      peacock-in-parking-lot.png
      ...

Generates:
  content/gallery/
      leopard-on-boundary-wall/
          index.md          ← stub front matter (edit manually)
          cover.webp        ← watermarked, web-ready image
      ...

Shared venv: /Users/a0s10ik/ExternalSoftware/GenrativeModels/shared_venv
             Activate: source ~/Personal\ Repos/ContentVideoGenrator/activate_shared_venv.sh
"""

import os
import sys
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Configuration ─────────────────────────────────────────────────────────────
INPUT_DIR      = Path("raw_photos")
GALLERY_DIR    = Path("content/gallery")
WATERMARK_TEXT = "@urbanwildlifeindia"   # change to your handle
WEBP_QUALITY   = 85
FONT_RATIO     = 1 / 35                  # font size = image_width / 35
MARGIN         = 24                      # px from edges
# ──────────────────────────────────────────────────────────────────────────────

SUPPORTED = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}


def load_font(size: int) -> ImageFont.FreeTypeFont:
    """Try system fonts in priority order, fall back to PIL default."""
    candidates = [
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        # Linux CI
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def add_watermark(img: Image.Image, text: str) -> Image.Image:
    """Overlay semi-transparent watermark at bottom-right."""
    img = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_size = max(14, int(img.width * FONT_RATIO))
    font = load_font(font_size)

    # Measure text using textbbox (Pillow ≥ 9.2; avoids deprecated textsize)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = img.width  - text_w - MARGIN
    y = img.height - text_h - MARGIN

    # Subtle drop shadow
    draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0, 140))
    # Main text — white at 55% opacity
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 140))

    combined = Image.alpha_composite(img, overlay)
    return combined.convert("RGB")


def slug(filename: str) -> str:
    stem = Path(filename).stem
    return (
        stem.lower()
            .replace(" ", "-")
            .replace("_", "-")
    )


def write_stub_frontmatter(output_dir: Path, title: str) -> None:
    index = output_dir / "index.md"
    if index.exists():
        return  # don't overwrite manual edits
    index.write_text(
        textwrap.dedent(f"""\
            ---
            title: "{title}"
            date: ""
            location: ""
            species: ""
            camera: ""
            lens: ""
            settings: ""
            caption: ""
            categories: []
            draft: false
            ---

            <!-- Add your story / observation notes here -->
        """),
        encoding="utf-8",
    )


def process(input_path: Path, gallery_dir: Path) -> None:
    name = slug(input_path.name)
    output_dir = gallery_dir / name
    output_dir.mkdir(parents=True, exist_ok=True)

    cover_path = output_dir / "cover.webp"

    with Image.open(input_path) as img:
        # Preserve EXIF orientation
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        watermarked = add_watermark(img, WATERMARK_TEXT)
        # exif=b"" explicitly strips all EXIF/GPS metadata from the saved file
        watermarked.save(cover_path, "WEBP", quality=WEBP_QUALITY, method=6, exif=b"")

    title = input_path.stem.replace("-", " ").replace("_", " ").title()
    write_stub_frontmatter(output_dir, title)

    print(f"  ✓  {input_path.name}  →  {cover_path}")


def main() -> None:
    if not INPUT_DIR.exists():
        print(f"[error] Input folder '{INPUT_DIR}' not found.")
        print("        Create it and place your RAW/high-res photos inside.")
        sys.exit(1)

    images = [p for p in INPUT_DIR.iterdir() if p.suffix.lower() in SUPPORTED]
    if not images:
        print(f"[warn]  No supported images found in '{INPUT_DIR}'.")
        sys.exit(0)

    GALLERY_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Processing {len(images)} image(s)…\n")

    errors = []
    for img_path in sorted(images):
        try:
            process(img_path, GALLERY_DIR)
        except Exception as exc:
            errors.append((img_path.name, exc))
            print(f"  ✗  {img_path.name}  →  ERROR: {exc}")

    print(f"\nDone. {len(images) - len(errors)} succeeded, {len(errors)} failed.")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
