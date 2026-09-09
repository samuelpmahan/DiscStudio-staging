#!/usr/bin/env python3
"""Foundry studio self-check: contract, determinism, RNG discipline, lint.

    python3 self_check.py

Exits non-zero on any failure. Checks, in order:

  contract     every family returns a full SVG document with the right width /
               height / viewBox / aria-label / <title> / disc clip at r=220, and
               draws the label text only at 220.
  rng          rendering a family at 42, 96 and 220 consumes exactly the same
               number of random draws, so a second target never shifts identity.
  determinism  every family (3 palettes x 3 seeds x 3 targets) and every card
               (4 layouts x 2 widths x details on/off) hashes the same twice in
               this process and again in a fresh interpreter.
  cards        both renderers accept card_composition.compose() output, honour
               layout + details, and put the flight numbers and score on the card.
  lint         harness/lint_svg.py passes on every SVG under preview/svg.
"""
from __future__ import annotations

import hashlib
import random
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HARNESS = ROOT / "harness"
sys.path.insert(0, str(HARNESS))
sys.path.insert(0, str(HERE))

import cards as cardmod  # noqa: E402
import families  # noqa: E402
from fixtures import LABELS, PALETTES, SAMPLE_CARDS, SEEDS  # noqa: E402

TARGETS = (42, 96, 220)
FAILURES: list[str] = []
LINES: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        FAILURES.append(message)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #

def check_contract() -> None:
    for slug, fn in families.FAMILY_FUNCTIONS.items():
        for target in TARGETS:
            svg = fn(7, "#e8d8b0", "#7a3b1e", target, "Warm Mako")
            check(svg.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<svg '),
                  f"{slug}@{target}: not a full SVG document")
            check(f'width="{target}" height="{target}"' in svg,
                  f"{slug}@{target}: width/height do not match the target")
            check('viewBox="0 0 512 512"' in svg, f"{slug}@{target}: wrong viewBox")
            check('aria-label="Warm Mako"' in svg, f"{slug}@{target}: missing aria-label")
            check("<title>Warm Mako</title>" in svg, f"{slug}@{target}: missing title")
            check('<clipPath id="disc"><circle cx="256" cy="256" r="220"/></clipPath>' in svg,
                  f"{slug}@{target}: missing r=220 disc clip")
            check('id="rim"' in svg, f"{slug}@{target}: missing rim")
            has_label = "WARM MAKO</text>" in svg
            check(has_label == (target == 220),
                  f"{slug}@{target}: label text present={has_label}, expected {target == 220}")
        # An empty label must not leave an empty plate behind at 220.
        check('id="text"' not in fn(7, "#e8d8b0", "#7a3b1e", 220, "   "),
              f"{slug}: blank label still drew a label plate")
        try:
            fn(7, "#e8d8b0", "#7a3b1e", 64, "x")
        except ValueError:
            pass
        else:
            FAILURES.append(f"{slug}: accepted an unsupported target")
    LINES.append(f"contract     ok  {len(families.FAMILY_FUNCTIONS)} families x {len(TARGETS)} targets")


class CountingRandom(random.Random):
    """random.Random that records how many draws a render performed."""

    draws = 0

    def random(self):  # noqa: D102
        CountingRandom.draws += 1
        return super().random()

    def getrandbits(self, k):  # noqa: D102
        CountingRandom.draws += 1
        return super().getrandbits(k)


def check_rng() -> None:
    original = families.random.Random
    families.random.Random = CountingRandom
    try:
        for slug, fn in families.FAMILY_FUNCTIONS.items():
            counts = []
            for target in TARGETS:
                CountingRandom.draws = 0
                fn(3, "#4c9bc6", "#0d3558", target, "MAKO")
                counts.append(CountingRandom.draws)
            check(len(set(counts)) == 1,
                  f"{slug}: RNG draws differ per target {dict(zip(TARGETS, counts))}")
    finally:
        families.random.Random = original
    LINES.append("rng          ok  identical draw counts at 42/96/220 for every family")


def check_determinism() -> tuple[int, int]:
    art_hashes: dict[str, str] = {}
    for slug, fn in families.FAMILY_FUNCTIONS.items():
        for palette, (base, accent) in PALETTES.items():
            for seed, label in zip(SEEDS, LABELS):
                for target in TARGETS:
                    key = f"{slug}|{palette}|{seed}|{target}"
                    first = digest(fn(seed, base, accent, target, label))
                    second = digest(fn(seed, base, accent, target, label))
                    check(first == second, f"{key}: not deterministic in-process")
                    art_hashes[key] = first

    art = {"active": families.hot_foil(7, "#e8d8b0", "#7a3b1e", 220, "MAKO"),
           "rival": families.register_mark(42, "#4c9bc6", "#0d3558", 220, "RIVAL")}
    card_hashes: dict[str, str] = {}
    for name, card in SAMPLE_CARDS.items():
        render = cardmod.render_single if card["type"] == "single" else cardmod.render_battle
        for width in (400, 700):
            for details in (True, False):
                payload = dict(card, details=details)
                key = f"{name}|{width}|{details}"
                first = digest(render(payload, art, width))
                second = digest(render(payload, art, width))
                check(first == second, f"{key}: card not deterministic in-process")
                card_hashes[key] = first

    # Same again in a fresh interpreter: no import-order or hash-seed dependence.
    script = (
        "import hashlib,sys;sys.path[:0]=[%r,%r]\n"
        "import families,cards\n"
        "from fixtures import PALETTES,SEEDS,LABELS,SAMPLE_CARDS\n"
        "d=lambda t:hashlib.sha256(t.encode()).hexdigest()\n"
        "for s,f in families.FAMILY_FUNCTIONS.items():\n"
        "    for p,(b,a) in PALETTES.items():\n"
        "        for sd,lb in zip(SEEDS,LABELS):\n"
        "            for t in (42,96,220):\n"
        "                print('A',f'{s}|{p}|{sd}|{t}',d(f(sd,b,a,t,lb)))\n"
        "art={'active':families.hot_foil(7,'#e8d8b0','#7a3b1e',220,'MAKO'),"
        "'rival':families.register_mark(42,'#4c9bc6','#0d3558',220,'RIVAL')}\n"
        "for n,c in SAMPLE_CARDS.items():\n"
        "    r=cards.render_single if c['type']=='single' else cards.render_battle\n"
        "    for w in (400,700):\n"
        "        for de in (True,False):\n"
        "            print('C',f'{n}|{w}|{de}',d(r(dict(c,details=de),art,w)))\n"
    ) % (str(HARNESS), str(HERE))
    proc = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
    check(proc.returncode == 0, f"fresh interpreter failed: {proc.stderr[-400:]}")
    for line in proc.stdout.splitlines():
        kind, key, value = line.split()
        table = art_hashes if kind == "A" else card_hashes
        check(table.get(key) == value, f"{key}: hash differs across processes")
    LINES.append(f"determinism  ok  {len(art_hashes)} art + {len(card_hashes)} card renders, "
                 f"stable twice in-process and in a fresh interpreter")
    return len(art_hashes), len(card_hashes)


def check_cards() -> None:
    art = {"active": families.hot_foil(7, "#e8d8b0", "#7a3b1e", 220, "MAKO"),
           "rival": families.register_mark(42, "#4c9bc6", "#0d3558", 220, "RIVAL")}
    for name, card in SAMPLE_CARDS.items():
        kind = card["type"]
        render = cardmod.render_single if kind == "single" else cardmod.render_battle
        svg = render(card, art, 400)
        natural_w, natural_h = cardmod.GEOMETRY[(kind, card["layout"])]
        check(f'viewBox="0 0 {natural_w:g} {natural_h:g}"' in svg,
              f"{name}: layout {card['layout']} did not select its own geometry")
        check(f'width="400" height="{round(400 * natural_h / natural_w)}"' in svg,
              f"{name}: width did not scale the natural geometry")
        for label in ("SPEED", "GLIDE", "TURN", "FADE"):
            check(f">{label}</text>" in svg, f"{name}: missing {label}")
        check(">5</text>" in svg and ">-1</text>" in svg,
              f"{name}: flight values missing from the card")
        check(card["participants"][0]["name"] in svg, f"{name}: disc name missing")
        check("FIRST RUN" in svg, f"{name}: manufacturer/mold line missing")
        check(("SCORE" in svg) == (kind == "battle"),
              f"{name}: score slot presence does not match card type")
        for person in card["participants"]:
            check(f'id="well-p{card["participants"].index(person)}"' in svg,
                  f"{name}: participant art well missing")
        lean = render(dict(card, details=False), art, 400)
        check("SPEED" not in lean, f"{name}: details=False still drew flight numbers")
        check(card["participants"][0]["name"] in lean,
              f"{name}: details=False dropped the disc name")
        # ids stay unique once both arts are embedded
        ids = re.findall(r'\bid="([^"]+)"', svg)
        check(len(ids) == len(set(ids)), f"{name}: duplicate ids after embedding art")
        check("data:" not in svg and "<image" not in svg and "@font-face" not in svg,
              f"{name}: forbidden embedded resource")
    # a missing art entry must degrade, not explode
    empty = cardmod.render_single(SAMPLE_CARDS["single_standard"], {}, 400)
    check("NO PLATE" in empty, "single: missing art did not fall back to an empty plate")
    # scores and winners land on the battle card
    scored = dict(SAMPLE_CARDS["battle_standard"], scores={"active": 7, "rival": 4},
                  winner="active")
    svg = cardmod.render_battle(scored, art, 700)
    check(">7</text>" in svg and ">4</text>" in svg, "battle: scores not rendered")
    check("WINNER" in svg, "battle: winner not marked")
    LINES.append(f"cards        ok  {len(SAMPLE_CARDS)} composed layouts + score/winner/no-art paths")


def check_lint() -> None:
    svgs = sorted((HERE / "preview" / "svg").rglob("*.svg"))
    check(bool(svgs), "no SVGs under preview/svg to lint - run build_preview.py first")
    if not svgs:
        return
    proc = subprocess.run([sys.executable, str(HARNESS / "lint_svg.py"), *map(str, svgs)],
                          capture_output=True, text=True)
    check(proc.returncode == 0, "lint_svg.py failed:\n" + proc.stdout[-2000:])
    largest = max(svgs, key=lambda p: p.stat().st_size)
    LINES.append(f"lint         ok  {len(svgs)} SVGs clean, largest {largest.name} "
                 f"{largest.stat().st_size / 1024:.1f}KB (cap 64KB)")


def main() -> None:
    check_contract()
    check_rng()
    check_determinism()
    check_cards()
    check_lint()
    print("\n".join(LINES))
    if FAILURES:
        print(f"\nFAIL ({len(FAILURES)}):")
        for failure in FAILURES:
            print(f"  - {failure}")
        sys.exit(1)
    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()
