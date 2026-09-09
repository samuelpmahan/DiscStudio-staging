#!/usr/bin/env python3
"""Render studio *signal* previews: every family x palette x seed x target,
both card kinds x layouts x widths, then the contact sheets judges look at.

    python3 build_preview.py [--families] [--cards] [--sheets]

With no flags it does everything.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
HARNESS = ROOT / "harness"
for extra in (str(HERE), str(HARNESS)):
    if extra not in sys.path:
        sys.path.insert(0, extra)

import fixtures  # noqa: E402
from families import RENDERERS  # noqa: E402
from cards import render_battle, render_single  # noqa: E402

SVG_DIR = HERE / "preview" / "svg"
PNG_DIR = HERE / "preview" / "png"
SHEET_DIR = HERE / "preview"
TARGETS = (42, 96, 220)
CARD_WIDTHS = (400, 700)
LABELS = dict(zip(fixtures.SEEDS, fixtures.LABELS))


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def build_family_svgs() -> list[Path]:
    made = []
    for slug, fam in RENDERERS.items():
        for pal, (base, accent) in fixtures.PALETTES.items():
            for seed in fixtures.SEEDS:
                for target in TARGETS:
                    svg = fam(seed, base, accent, target, LABELS[seed])
                    made.append(write(SVG_DIR / f"{slug}_{pal}_s{seed}_{target}.svg", svg))
    return made


def art_pack(slug: str, pal: str, seed: int, target: int) -> dict[str, str]:
    base, accent = fixtures.PALETTES[pal]
    fam = RENDERERS[slug]
    return {
        "active": fam(seed, base, accent, target, LABELS[seed]),
        "rival": fam(seed + 11, accent, base, target, "Rival"),
    }


def build_card_svgs() -> list[Path]:
    made = []
    art = art_pack("chevron-run", "cool", 7, 220)
    art_b = {"active": RENDERERS["sweep-clock"](3, "#4c9bc6", "#0d3558", 220, "MAKO"),
             "rival": RENDERERS["score-bug"](42, "#1e1e24", "#f2c14e", 220, "Rival")}
    for width in CARD_WIDTHS:
        for layout in ("standard", "gallery"):
            card = fixtures.SAMPLE_CARDS[f"single_{layout}"]
            made.append(write(SVG_DIR / f"card_single_{layout}_{width}.svg",
                              render_single(card, art, width)))
        for layout in ("standard", "stacked"):
            card = dict(fixtures.SAMPLE_CARDS[f"battle_{layout}"])
            scored = dict(card)
            scored["scores"] = {"active": 7, "rival": 4}
            scored["winner"] = "active"
            made.append(write(SVG_DIR / f"card_battle_{layout}_{width}.svg",
                              render_battle(scored, art_b, width)))
            made.append(write(SVG_DIR / f"cardplain_battle_{layout}_{width}.svg",
                              render_battle(card, art_b, width)))
    # details=False variants at 400
    for layout in ("standard", "gallery"):
        card = dict(fixtures.SAMPLE_CARDS[f"single_{layout}"])
        card["details"] = False
        made.append(write(SVG_DIR / f"cardlean_single_{layout}_400.svg",
                          render_single(card, art, 400)))
    for layout in ("standard", "stacked"):
        card = dict(fixtures.SAMPLE_CARDS[f"battle_{layout}"])
        card["details"] = False
        card["scores"] = {"active": 12, "rival": 9}
        made.append(write(SVG_DIR / f"cardlean_battle_{layout}_400.svg",
                          render_battle(card, art_b, 400)))
    return made


def rasterize(paths: list[Path], scale: float = 2.0) -> None:
    from playwright.sync_api import sync_playwright
    from render_svg import launch, render_one

    PNG_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = launch(pw)
        page = browser.new_page(device_scale_factor=scale)
        for svg_path in paths:
            out = PNG_DIR / (svg_path.stem + ".png")
            render_one(page, svg_path, out, None)
        browser.close()
    print(f"rasterized {len(paths)} svg -> {PNG_DIR}")


def sheet(title: str, out: Path, tiles: list[Path], cols: int = 3, width: int = 240) -> None:
    cmd = [sys.executable, str(HARNESS / "contact_sheet.py"), "--title", title,
           "--out", str(out), "--cols", str(cols), "--width", str(width)]
    cmd += [str(t) for t in tiles]
    subprocess.run(cmd, check=True)


def build_sheets() -> None:
    def png(name: str) -> Path:
        return PNG_DIR / f"{name}.png"

    for slug in RENDERERS:
        tiles = [png(f"{slug}_{pal}_s{seed}_{t}")
                 for pal in fixtures.PALETTES for seed in (7,) for t in TARGETS]
        tiles += [png(f"{slug}_cool_s{seed}_220") for seed in fixtures.SEEDS]
        sheet(slug, SHEET_DIR / f"{slug}-palettes.png", tiles, cols=3, width=250)
    squint = [png(f"{slug}_{pal}_s{seed}_42")
              for slug in RENDERERS for pal in fixtures.PALETTES for seed in fixtures.SEEDS]
    sheet("42px squint", SHEET_DIR / "squint-42.png", squint, cols=9, width=120)
    ninetysix = [png(f"{slug}_{pal}_s{seed}_96")
                 for slug in RENDERERS for pal in fixtures.PALETTES for seed in fixtures.SEEDS]
    sheet("96px", SHEET_DIR / "grid-96.png", ninetysix, cols=9, width=150)
    sheet("cards 400", SHEET_DIR / "cards-400.png",
          [png("card_single_standard_400"), png("card_single_gallery_400"),
           png("cardlean_single_standard_400"), png("card_battle_standard_400"),
           png("card_battle_stacked_400"), png("cardplain_battle_standard_400"),
           png("cardlean_battle_standard_400"), png("cardlean_battle_stacked_400"),
           png("cardplain_battle_stacked_400")], cols=3, width=380)
    sheet("cards 700", SHEET_DIR / "cards-700.png",
          [png("card_single_standard_700"), png("card_single_gallery_700"),
           png("card_battle_standard_700"), png("card_battle_stacked_700"),
           png("cardplain_battle_standard_700"), png("cardplain_battle_stacked_700")],
          cols=2, width=520)


def determinism() -> str:
    lines = []
    for slug, fam in RENDERERS.items():
        for pal, (base, accent) in fixtures.PALETTES.items():
            for seed in fixtures.SEEDS:
                for target in TARGETS:
                    a = fam(seed, base, accent, target, LABELS[seed])
                    b = fam(seed, base, accent, target, LABELS[seed])
                    assert a == b, f"{slug} not deterministic"
                    lines.append(hashlib.sha256(a.encode()).hexdigest()[:12])
    return f"{len(lines)} art renders, all byte-identical on re-render"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--families", action="store_true")
    p.add_argument("--cards", action="store_true")
    p.add_argument("--sheets", action="store_true")
    a = p.parse_args()
    do_all = not (a.families or a.cards or a.sheets)
    made: list[Path] = []
    if do_all or a.families:
        made += build_family_svgs()
    if do_all or a.cards:
        made += build_card_svgs()
    if made:
        rasterize(made)
    if do_all or a.sheets:
        build_sheets()
    print(determinism())


if __name__ == "__main__":
    main()
