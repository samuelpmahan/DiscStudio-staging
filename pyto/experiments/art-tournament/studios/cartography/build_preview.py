#!/usr/bin/env python3
"""Build every SVG and contact sheet for studio *cartography*.

    python3 build_preview.py [--families] [--cards] [--sheets]

Writes preview/svg/*.svg, preview/png/*.png and preview/*.png contact sheets.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HARNESS = ROOT / "harness"
PREVIEW = HERE / "preview"
SVG = PREVIEW / "svg"
PNG = PREVIEW / "png"

for extra in (str(HERE), str(HARNESS)):
    if extra not in sys.path:
        sys.path.insert(0, extra)

import families  # noqa: E402
import cards as cardmod  # noqa: E402
from fixtures import PALETTES, SEEDS, LABELS, SAMPLE_CARDS  # noqa: E402

TARGETS = (42, 96, 220)


def write_family_svgs() -> None:
    SVG.mkdir(parents=True, exist_ok=True)
    for slug in families.FAMILIES:
        for pname, (base, accent) in PALETTES.items():
            for seed, label in zip(SEEDS, LABELS):
                for target in TARGETS:
                    text = families.render(slug, seed, base, accent, target, label)
                    (SVG / f"{slug}_{pname}_s{seed}_{target}.svg").write_text(text, encoding="utf-8")


def _art_for(card: dict, slug: str, palette: str) -> dict[str, str]:
    base, accent = PALETTES[palette]
    out = {}
    for index, participant in enumerate(card["participants"]):
        seed = SEEDS[index % len(SEEDS)]
        out[participant["presentationId"]] = families.render(
            slug, seed, base, accent, 220, participant.get("name", "disc"))
    return out


def write_card_svgs() -> None:
    SVG.mkdir(parents=True, exist_ok=True)
    combos = [
        ("single_standard", "contour-basin", "warm"),
        ("single_gallery", "fairway-plat", "cool"),
        ("battle_standard", "wind-rose", "dark"),
        ("battle_stacked", "fairway-plat", "warm"),
    ]
    for key, slug, palette in combos:
        card = SAMPLE_CARDS[key]
        art = _art_for(card, slug, palette)
        render = cardmod.render_single if card["type"] == "single" else cardmod.render_battle
        for width in (400, 700):
            (SVG / f"card_{key}_{width}.svg").write_text(render(card, art, width), encoding="utf-8")
    # A populated variant so the maker/mold line and score slot are visible.
    import copy
    for key, slug, palette in combos:
        card = copy.deepcopy(SAMPLE_CARDS[key])
        for index, participant in enumerate(card["participants"]):
            participant["manufacturer"] = ("Innova", "Discraft")[index % 2]
            participant["mold"] = ("Mako3", "Buzzz")[index % 2]
        if card["type"] == "battle":
            card["scores"] = {p["presentationId"]: (7, 4)[i % 2] for i, p in enumerate(card["participants"])}
            card["winner"] = card["participants"][0]["presentationId"]
        art = _art_for(card, slug, palette)
        render = cardmod.render_single if card["type"] == "single" else cardmod.render_battle
        (SVG / f"cardfull_{key}_700.svg").write_text(render(card, art, 700), encoding="utf-8")
    # details=False, to prove the flag is honored.
    for key in ("single_standard", "battle_standard"):
        card = copy.deepcopy(SAMPLE_CARDS[key])
        card["details"] = False
        art = _art_for(card, "wind-rose", "cool")
        render = cardmod.render_single if card["type"] == "single" else cardmod.render_battle
        (SVG / f"cardplain_{key}_700.svg").write_text(render(card, art, 700), encoding="utf-8")


def rasterize() -> None:
    PNG.mkdir(parents=True, exist_ok=True)
    groups: dict[float, list[Path]] = {}
    for path in sorted(SVG.glob("*.svg")):
        scale = 4.0 if path.stem.endswith("_42") else 2.0
        groups.setdefault(scale, []).append(path)
    for scale, paths in groups.items():
        for path in paths:
            out = PNG / (path.stem + ".png")
            subprocess.run([sys.executable, str(HARNESS / "render_svg.py"), "--svg", str(path),
                            "--out", str(out), "--scale", str(scale)], check=True,
                           stdout=subprocess.DEVNULL)
    print(f"rasterized {sum(len(v) for v in groups.values())} files")


def sheet(title: str, out: str, tiles: list[Path], cols: int = 3, width: int = 240) -> None:
    tiles = [t for t in tiles if t.exists()]
    if not tiles:
        return
    subprocess.run([sys.executable, str(HARNESS / "contact_sheet.py"), "--title", title,
                    "--out", str(PREVIEW / out), "--cols", str(cols), "--width", str(width)]
                   + [str(t) for t in tiles], check=True)


def build_sheets() -> None:
    for slug in families.FAMILIES:
        tiles = [PNG / f"{slug}_cool_s{seed}_{t}.png" for seed in SEEDS for t in TARGETS]
        sheet(f"{slug} tiers", f"{slug}-tiers.png", tiles, cols=3)
        tiles = [PNG / f"{slug}_{p}_s7_{t}.png" for p in PALETTES for t in TARGETS]
        sheet(f"{slug} palettes", f"{slug}-palettes.png", tiles, cols=3)
    tiles = [PNG / f"{slug}_{p}_s{seed}_42.png" for slug in families.FAMILIES
             for p in PALETTES for seed in SEEDS]
    sheet("42px legibility", "all-42.png", tiles, cols=9, width=150)
    tiles = [PNG / f"{slug}_{p}_s{seed}_96.png" for slug in families.FAMILIES
             for p in PALETTES for seed in SEEDS]
    sheet("96px legibility", "all-96.png", tiles, cols=9, width=150)
    tiles = sorted(PNG.glob("card_*_400.png"))
    sheet("cards 400", "cards-400.png", tiles, cols=2, width=430)
    tiles = sorted(PNG.glob("card_*_700.png"))
    sheet("cards 700", "cards-700.png", tiles, cols=2, width=470)
    tiles = sorted(PNG.glob("cardfull_*.png")) + sorted(PNG.glob("cardplain_*.png"))
    sheet("cards populated", "cards-populated.png", tiles, cols=2, width=470)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--only", choices=("families", "cards", "sheets"), default=None)
    args = p.parse_args()
    if args.only in (None, "families"):
        write_family_svgs()
    if args.only in (None, "cards"):
        write_card_svgs()
    if args.only != "sheets":
        rasterize()
    build_sheets()


if __name__ == "__main__":
    main()
