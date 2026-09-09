#!/usr/bin/env python3
"""Rasterize SVG documents to PNG via headless Chromium (Playwright).

Single-file mode:
    render_svg.py --svg disc.svg --out disc.png [--width N] [--scale F]

Batch mode (every *.svg in a directory, sibling *.png next to each):
    render_svg.py --dir svgs/ [--width N] [--scale F]

The SVG's own width/height attributes (falling back to its viewBox) set the
render size unless --width overrides it (height scales proportionally from
the SVG's intrinsic aspect ratio). device_scale_factor defaults to 2 so
raster tiles hold up under judge zoom; override with --scale.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

CHROMIUM_PATH = "/opt/pw-browsers/chromium"

_DIM_RE = re.compile(r'width="([0-9.]+)"\s+height="([0-9.]+)"')
_VIEWBOX_RE = re.compile(r'viewBox="[^"]*?\s([0-9.]+)\s+([0-9.]+)"')


def intrinsic_size(svg_text: str) -> tuple[float, float]:
    m = _DIM_RE.search(svg_text)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = _VIEWBOX_RE.search(svg_text)
    if m:
        return float(m.group(1)), float(m.group(2))
    raise ValueError("SVG has neither width/height nor a viewBox to size from")


def render_one(page, svg_path: Path, out_path: Path, width: int | None) -> None:
    svg_text = svg_path.read_text(encoding="utf-8")
    natural_w, natural_h = intrinsic_size(svg_text)
    if width:
        render_w = width
        render_h = max(1, round(natural_h * (width / natural_w)))
    else:
        render_w, render_h = round(natural_w), round(natural_h)
    page.set_viewport_size({"width": render_w, "height": render_h})
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<style>html,body{margin:0;padding:0;background:transparent;}"
        f"svg{{display:block;width:{render_w}px;height:{render_h}px;}}</style></head>"
        f"<body>{svg_text}</body></html>"
    )
    page.set_content(html, wait_until="load")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out_path), omit_background=True)


def main() -> None:
    p = argparse.ArgumentParser(description="Rasterize SVG to PNG via headless Chromium")
    p.add_argument("--svg", type=Path, help="single SVG file to render")
    p.add_argument("--out", type=Path, help="output PNG path (single-file mode)")
    p.add_argument("--dir", type=Path, help="directory of *.svg files to render (batch mode)")
    p.add_argument("--width", type=int, default=None, help="override render width in px")
    p.add_argument("--scale", type=float, default=2.0, help="device_scale_factor (default 2)")
    args = p.parse_args()

    if bool(args.svg) == bool(args.dir):
        p.error("pass exactly one of --svg or --dir")
    if args.svg and not args.out:
        p.error("--svg requires --out")

    jobs: list[tuple[Path, Path]] = []
    if args.svg:
        jobs.append((args.svg, args.out))
    else:
        svgs = sorted(args.dir.glob("*.svg"))
        if not svgs:
            print(f"no *.svg files found in {args.dir}", file=sys.stderr)
            sys.exit(1)
        for svg_path in svgs:
            jobs.append((svg_path, svg_path.with_suffix(".png")))

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROMIUM_PATH)
        page = browser.new_page(device_scale_factor=args.scale)
        for svg_path, out_path in jobs:
            render_one(page, svg_path, out_path, args.width)
            print(f"rendered {svg_path} -> {out_path}")
        browser.close()


if __name__ == "__main__":
    main()
