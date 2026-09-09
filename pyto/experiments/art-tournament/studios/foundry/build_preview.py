#!/usr/bin/env python3
"""Render every foundry family and card into preview/ and build contact sheets.

    python3 build_preview.py [--stage art|cards|all]

Writes SVGs + PNGs under preview/svg and preview/png, then contact sheets at
preview/sheet-*.png. Rasterising and sheet building shell out to the shared
tournament harness so judges see exactly what this script produced.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HARNESS = ROOT / "harness"
sys.path.insert(0, str(HARNESS))
sys.path.insert(0, str(HERE))

import families  # noqa: E402
import cards as cardmod  # noqa: E402
from fixtures import LABELS, PALETTES, SAMPLE_CARDS, SEEDS  # noqa: E402

PREVIEW = HERE / "preview"
SVG_DIR = PREVIEW / "svg"
PNG_DIR = PREVIEW / "png"


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def raster(svg: Path, png: Path, width: int | None = None) -> None:
    cmd = [sys.executable, str(HARNESS / "render_svg.py"), "--svg", str(svg), "--out", str(png)]
    if width:
        cmd += ["--width", str(width)]
    subprocess.run(cmd, check=True, capture_output=True)


def raster_dir(directory: Path) -> None:
    subprocess.run([sys.executable, str(HARNESS / "render_svg.py"), "--dir", str(directory)],
                   check=True, capture_output=True)


def sheet(title: str, out: Path, tiles: list[Path], cols: int = 3, width: int = 260) -> None:
    cmd = [sys.executable, str(HARNESS / "contact_sheet.py"), "--title", title,
           "--out", str(out), "--cols", str(cols), "--width", str(width)]
    cmd += [str(t) for t in tiles]
    print(subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip())


def build_art() -> list[Path]:
    written: list[Path] = []
    for slug, fn in families.FAMILY_FUNCTIONS.items():
        for pal, (base, accent) in PALETTES.items():
            for seed, label in zip(SEEDS, LABELS):
                for target in (42, 96, 220):
                    name = f"{slug}_{pal}_s{seed}_{target}"
                    svg = write(SVG_DIR / "art" / f"{name}.svg",
                                fn(seed, base, accent, target, label))
                    png = PNG_DIR / "art" / f"{name}.png"
                    # 42/96 tiles are upscaled 4x/2x so judges can see the pixels
                    # they would actually get, not a blurry thumbnail.
                    raster(svg, png, width={42: 168, 96: 192, 220: 220}[target])
                    written.append(svg)
    return written


def build_cards() -> list[Path]:
    art_by_pid: dict[str, str] = {}
    palette = PALETTES["cool"]
    art_by_pid["active"] = families.hot_foil(7, PALETTES["warm"][0], PALETTES["warm"][1], 220, "MAKO")
    art_by_pid["rival"] = families.register_mark(42, palette[0], palette[1], 220, "RIVAL")
    written: list[Path] = []
    for key, card in SAMPLE_CARDS.items():
        render = cardmod.render_single if card["type"] == "single" else cardmod.render_battle
        for width in (400, 700):
            svg = write(SVG_DIR / "cards" / f"{key}_{width}.svg", render(card, art_by_pid, width))
            raster(svg, PNG_DIR / "cards" / f"{key}_{width}.png")
            written.append(svg)
        # details=False variant, to prove the flag is honoured
        lean = json.loads(json.dumps(card))
        lean["details"] = False
        svg = write(SVG_DIR / "cards" / f"{key}_nodetails_700.svg", render(lean, art_by_pid, 700))
        raster(svg, PNG_DIR / "cards" / f"{key}_nodetails_700.png")
        written.append(svg)
    # a battle with scores + a winner, to show the score slot carrying real data
    scored = json.loads(json.dumps(SAMPLE_CARDS["battle_standard"]))
    scored["scores"] = {"active": 7, "rival": 4}
    scored["winner"] = "active"
    svg = write(SVG_DIR / "cards" / "battle_scored_700.svg",
                cardmod.render_battle(scored, art_by_pid, 700))
    raster(svg, PNG_DIR / "cards" / "battle_scored_700.png")
    written.append(svg)
    return written


def sheets() -> None:
    for slug in families.FAMILY_FUNCTIONS:
        tiles = sorted((PNG_DIR / "art").glob(f"{slug}_*.png"))
        if tiles:
            sheet(slug, PREVIEW / f"sheet-{slug}.png", tiles, cols=9, width=200)
    small = sorted(p for p in (PNG_DIR / "art").glob("*_42.png"))
    if small:
        sheet("42px", PREVIEW / "sheet-42px.png", small, cols=9, width=150)
    card_tiles = sorted((PNG_DIR / "cards").glob("*.png"))
    if card_tiles:
        sheet("cards", PREVIEW / "sheet-cards.png", card_tiles, cols=3, width=440)


def determinism(paths: list[Path]) -> str:
    lines = []
    for slug, fn in families.FAMILY_FUNCTIONS.items():
        a = hashlib.sha256(fn(7, "#e8d8b0", "#7a3b1e", 220, "MAKO").encode()).hexdigest()
        b = hashlib.sha256(fn(7, "#e8d8b0", "#7a3b1e", 220, "MAKO").encode()).hexdigest()
        lines.append(f"{slug}: {a[:16]} {'==' if a == b else '!='} {b[:16]}")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--stage", choices=("art", "cards", "all"), default="all")
    args = p.parse_args()
    written: list[Path] = []
    if args.stage in ("art", "all"):
        written += build_art()
    if args.stage in ("cards", "all"):
        written += build_cards()
    sheets()
    print(f"wrote {len(written)} svg")
    print(determinism(written))


if __name__ == "__main__":
    main()
