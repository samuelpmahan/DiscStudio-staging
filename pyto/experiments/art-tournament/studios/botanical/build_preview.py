#!/usr/bin/env python3
"""Build every SVG, PNG and contact sheet for studio *botanical*.

    python3 build_preview.py [--only families|cards|sheets]

Writes preview/svg/*.svg, preview/png/*.png and preview/*.png contact sheets.
"""
from __future__ import annotations

import argparse
import copy
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
COMBOS = (
    ("single_standard", "pressed-fern", "warm"),
    ("single_gallery", "nodding-seedhead", "cool"),
    ("battle_standard", "block-print", "warm"),
    ("battle_stacked", "pressed-fern", "dark"),
)


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
        out[participant["presentationId"]] = families.render(
            slug, SEEDS[index % len(SEEDS)], base, accent, 220, participant.get("name", "disc"))
    return out


def write_card_svgs() -> None:
    SVG.mkdir(parents=True, exist_ok=True)
    for key, slug, palette in COMBOS:
        card = SAMPLE_CARDS[key]
        art = _art_for(card, slug, palette)
        render = cardmod.render_single if card["type"] == "single" else cardmod.render_battle
        for width in (400, 700):
            (SVG / f"card_{key}_{width}.svg").write_text(render(card, art, width), encoding="utf-8")
    # populated: maker/mold, scores and a winner, so every slot is visible
    for key, slug, palette in COMBOS:
        card = copy.deepcopy(SAMPLE_CARDS[key])
        for index, participant in enumerate(card["participants"]):
            participant["manufacturer"] = ("Innova", "Discraft")[index % 2]
            participant["mold"] = ("Mako3", "Buzzz")[index % 2]
            participant["color"] = ("#7a3b1e", "#4c9bc6")[index % 2]
        if card["type"] == "battle":
            card["scores"] = {p["presentationId"]: (7, 4)[i % 2] for i, p in enumerate(card["participants"])}
            card["winner"] = card["participants"][0]["presentationId"]
        art = _art_for(card, slug, palette)
        render = cardmod.render_single if card["type"] == "single" else cardmod.render_battle
        (SVG / f"cardfull_{key}_700.svg").write_text(render(card, art, 700), encoding="utf-8")
    # details=False, to prove the flag is honored
    for key in ("single_standard", "single_gallery", "battle_standard", "battle_stacked"):
        card = copy.deepcopy(SAMPLE_CARDS[key])
        card["details"] = False
        if card["type"] == "battle":
            card["scores"] = [7, 4]
        art = _art_for(card, "nodding-seedhead", "warm")
        render = cardmod.render_single if card["type"] == "single" else cardmod.render_battle
        (SVG / f"cardplain_{key}_700.svg").write_text(render(card, art, 700), encoding="utf-8")


def rasterize() -> None:
    PNG.mkdir(parents=True, exist_ok=True)
    for path in sorted(SVG.glob("*.svg")):
        scale = 4.0 if path.stem.endswith("_42") else 2.0
        subprocess.run([sys.executable, str(HARNESS / "render_svg.py"), "--svg", str(path),
                        "--out", str(PNG / (path.stem + ".png")), "--scale", str(scale)],
                       check=True, stdout=subprocess.DEVNULL)
    print(f"rasterized {len(list(SVG.glob('*.svg')))} files")


def sheet(title: str, out: str, tiles: list[Path], cols: int = 3, width: int = 240) -> None:
    tiles = [t for t in tiles if t.exists()]
    if not tiles:
        return
    subprocess.run([sys.executable, str(HARNESS / "contact_sheet.py"), "--title", title,
                    "--out", str(PREVIEW / out), "--cols", str(cols), "--width", str(width)]
                   + [str(t) for t in tiles], check=True)


def build_sheets() -> None:
    for slug in families.FAMILIES:
        sheet(f"{slug} tiers", f"{slug}-tiers.png",
              [PNG / f"{slug}_warm_s{seed}_{t}.png" for seed in SEEDS for t in TARGETS], cols=3)
        sheet(f"{slug} palettes", f"{slug}-palettes.png",
              [PNG / f"{slug}_{p}_s7_{t}.png" for p in PALETTES for t in TARGETS], cols=3)
    for target in (42, 96):
        sheet(f"{target}px legibility", f"all-{target}.png",
              [PNG / f"{slug}_{p}_s{seed}_{target}.png" for slug in families.FAMILIES
               for p in PALETTES for seed in SEEDS], cols=9, width=150)
    sheet("220 detail", "all-220.png",
          [PNG / f"{slug}_{p}_s7_220.png" for slug in families.FAMILIES for p in PALETTES],
          cols=3, width=300)
    sheet("cards 400", "cards-400.png", sorted(PNG.glob("card_*_400.png")), cols=2, width=430)
    sheet("cards 700", "cards-700.png", sorted(PNG.glob("card_*_700.png")), cols=2, width=480)
    sheet("cards populated", "cards-populated.png",
          sorted(PNG.glob("cardfull_*.png")) + sorted(PNG.glob("cardplain_*.png")), cols=2, width=480)


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
