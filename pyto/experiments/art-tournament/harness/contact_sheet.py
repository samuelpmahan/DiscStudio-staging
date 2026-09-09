#!/usr/bin/env python3
"""Build a titled contact sheet from PNG tiles, in the pyto.neon LAB style.

    contact_sheet.py --title X --out sheet.png tile1.png tile2.png ...
        [--cols N] [--width N] [--grid 64]

Each PNG becomes one panel (its own filename stem as the panel title) laid
out on a dark sheet grid. --grid draws a labelled coordinate overlay (in
image pixels, spaced every N px) on top of every panel body so judges can
reference exact positions when leaving notes, matching the annotation-grid
convention used elsewhere in the lab.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

from pyto.neon import FONT, fit_width, panel, sheet


def with_grid(image: Image.Image, spacing: int) -> Image.Image:
    """Overlay faint gridlines every `spacing` px with axis coordinate labels."""
    out = image.convert("RGBA")
    draw = ImageDraw.Draw(out)
    line = (0, 255, 255, 90)
    label_bg = (0, 0, 0, 170)
    label_fg = (0, 255, 255, 255)
    for x in range(0, out.width, spacing):
        draw.line([(x, 0), (x, out.height)], fill=line, width=1)
        text = str(x)
        draw.rectangle([x + 1, 0, x + 1 + 6 * len(text), 11], fill=label_bg)
        draw.text((x + 2, 0), text, fill=label_fg, font=FONT)
    for y in range(0, out.height, spacing):
        draw.line([(0, y), (out.width, y)], fill=line, width=1)
        text = str(y)
        draw.rectangle([0, y + 1, 6 * len(text) + 2, y + 12], fill=label_bg)
        draw.text((1, y + 1), text, fill=label_fg, font=FONT)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Compose PNG tiles into a titled contact sheet")
    p.add_argument("tiles", nargs="+", type=Path, help="PNG files to include, one panel each")
    p.add_argument("--title", required=True, help="sheet title (used as filename stem prefix, not drawn)")
    p.add_argument("--out", required=True, type=Path, help="output PNG path")
    p.add_argument("--cols", type=int, default=3, help="panels per row (default 3)")
    p.add_argument("--width", type=int, default=260, help="per-panel body width (default 260)")
    p.add_argument("--grid", type=int, default=0, help="if set, overlay a coordinate grid every N px")
    args = p.parse_args()

    panels = []
    for tile_path in args.tiles:
        image = Image.open(tile_path).convert("RGBA")
        body = fit_width(image, args.width)
        if args.grid:
            body = with_grid(body, args.grid)
        panels.append(panel(tile_path.stem, body, width=args.width))

    out = sheet(panels, cols=args.cols)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.convert("RGB").save(args.out)
    print(f"{args.title}: wrote {args.out} ({out.width}x{out.height}, {len(panels)} panels)")


if __name__ == "__main__":
    main()
