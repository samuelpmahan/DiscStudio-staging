#!/usr/bin/env python3
"""Studio *signal* self-check: contract, determinism, RNG discipline, lint.

    python3 selfcheck.py

Prints one line per check and exits non-zero on the first failure.
"""
from __future__ import annotations

import hashlib
import random
import re
import subprocess
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
HARNESS = ROOT / "harness"
for extra in (str(HERE), str(HARNESS)):
    if extra not in sys.path:
        sys.path.insert(0, extra)

import families  # noqa: E402
import fixtures  # noqa: E402
from cards import render_battle, render_single  # noqa: E402

TARGETS = (42, 96, 220)
LABELS = dict(zip(fixtures.SEEDS, fixtures.LABELS))
lines: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    lines.append("{} {}{}".format("PASS" if ok else "FAIL", name, (" — " + detail) if detail else ""))
    if not ok:
        print("\n".join(lines))
        sys.exit(1)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Spy(random.Random):
    """A Random that records every draw, so RNG use can be compared per target."""

    def __init__(self, seed):
        super().__init__(seed)
        self.draws: list[tuple] = []

    def uniform(self, a, b):
        value = super().uniform(a, b)
        self.draws.append(("uniform", a, b, value))
        return value

    def randrange(self, *args, **kwargs):
        value = super().randrange(*args, **kwargs)
        self.draws.append(("randrange", args, value))
        return value


# ---------------------------------------------------------------- art ------

art_hashes: dict[tuple, str] = {}
for slug, fam in families.RENDERERS.items():
    for pal, (base, accent) in fixtures.PALETTES.items():
        for seed in fixtures.SEEDS:
            for target in TARGETS:
                label = LABELS[seed]
                first = fam(seed, base, accent, target, label)
                second = fam(seed, base, accent, target, label)
                check("determinism {} {} s{} {}".format(slug, pal, seed, target),
                      first == second)
                art_hashes[(slug, pal, seed, target)] = sha(first)
                head = first.split("\n")[1]
                check("contract {} {} {}".format(slug, seed, target),
                      ('width="{t}" height="{t}"'.format(t=target) in head
                       and 'viewBox="0 0 512 512"' in head
                       and 'role="img"' in head and 'aria-label=' in head
                       and "<title>" in first
                       and '<clipPath id="disc"><circle cx="256" cy="256" r="220"/></clipPath>' in first
                       and '<g id="rim"' in first))
                check("label only at 220 {} {}".format(slug, target),
                      ('<g id="text">' in first) == (target == 220))
check("art renders deterministic", len(art_hashes) == 81, "{} renders x2".format(len(art_hashes)))

# identity is drawn once: the same seed must consume the same RNG at every target
real_random = families.random
try:
    families.random = types.SimpleNamespace(Random=Spy)
    for slug, fam in families.RENDERERS.items():
        for seed in fixtures.SEEDS:
            per_target = []
            for target in TARGETS:
                families.random.Random = Spy
                spy_holder: list[Spy] = []

                class Recorder(Spy):
                    def __init__(self, s):
                        super().__init__(s)
                        spy_holder.append(self)

                families.random.Random = Recorder
                fam(seed, "#4c9bc6", "#0d3558", target, LABELS[seed])
                per_target.append(spy_holder[-1].draws)
            check("no per-target RNG {} s{}".format(slug, seed),
                  per_target[0] == per_target[1] == per_target[2],
                  "{} draws".format(len(per_target[0])))
finally:
    families.random = real_random

# families must not collapse into one another at 42px
for pal in fixtures.PALETTES:
    base, accent = fixtures.PALETTES[pal]
    tiny = {slug: sha(fam(7, base, accent, 42, "MAKO")) for slug, fam in families.RENDERERS.items()}
    check("families distinct at 42 ({})".format(pal), len(set(tiny.values())) == 3)

# ---------------------------------------------------------------- cards ----

art_pack = {
    "active": families.sweep_clock(3, "#4c9bc6", "#0d3558", 220, "MAKO"),
    "rival": families.score_bug(42, "#1e1e24", "#f2c14e", 220, "Rival"),
}
card_hashes: dict[str, str] = {}
for width in (400, 700):
    for layout in ("standard", "gallery"):
        card = dict(fixtures.SAMPLE_CARDS["single_" + layout])
        a = render_single(card, art_pack, width)
        b = render_single(card, art_pack, width)
        check("determinism single {} {}".format(layout, width), a == b)
        card_hashes["single_{}_{}".format(layout, width)] = sha(a)
        check("single {} carries flight numbers".format(layout),
              all(k in a for k in ("SPEED", "GLIDE", "TURN", "FADE")))
        check("single {} carries the name".format(layout), "Warm Mako" in a)
        check("single {} embeds art without a nested viewport".format(layout),
              a.count("<svg") == 1 and "a0-disc" in a)
    for layout in ("standard", "stacked"):
        card = dict(fixtures.SAMPLE_CARDS["battle_" + layout])
        card["scores"] = {"active": 7, "rival": 4}
        card["winner"] = "active"
        a = render_battle(card, art_pack, width)
        b = render_battle(card, art_pack, width)
        check("determinism battle {} {}".format(layout, width), a == b)
        card_hashes["battle_{}_{}".format(layout, width)] = sha(a)
        check("battle {} carries both discs".format(layout),
              "a0-disc" in a and "a1-disc" in a and a.count("<svg") == 1)
        check("battle {} carries the score slot".format(layout),
              ">7<" in a and ">4<" in a and "SCORE" in a)
        check("battle {} carries flight numbers".format(layout),
              all(k in a for k in ("SPEED", "GLIDE", "TURN", "FADE")))

# layout and details actually change the drawing
std = render_single(fixtures.SAMPLE_CARDS["single_standard"], art_pack, 400)
gal = render_single(fixtures.SAMPLE_CARDS["single_gallery"], art_pack, 400)
check("single layouts differ", std != gal and 'viewBox="0 0 400 174"' in std
      and 'viewBox="0 0 320 402"' in gal)
bstd = render_battle(fixtures.SAMPLE_CARDS["battle_standard"], art_pack, 400)
bstk = render_battle(fixtures.SAMPLE_CARDS["battle_stacked"], art_pack, 400)
check("battle layouts differ", bstd != bstk and 'viewBox="0 0 660 300"' in bstd
      and 'viewBox="0 0 440 424"' in bstk)
lean = dict(fixtures.SAMPLE_CARDS["single_standard"])
lean["details"] = False
check("details flag honoured", "SPEED" not in render_single(lean, art_pack, 400))
lean_b = dict(fixtures.SAMPLE_CARDS["battle_standard"])
lean_b["details"] = False
check("battle details flag honoured", "SPEED" not in render_battle(lean_b, art_pack, 400))

# degenerate input still renders
check("missing art falls back to a stub", "<svg" in render_single(
    fixtures.SAMPLE_CARDS["single_standard"], {}, 400))
solo = dict(fixtures.SAMPLE_CARDS["battle_standard"])
solo["participants"] = solo["participants"][:1]
check("one-sided battle still renders", "AWAITING RIVAL" in render_battle(solo, art_pack, 400))
noscore = render_battle(fixtures.SAMPLE_CARDS["battle_standard"], art_pack, 400)
check("battle without scores still renders a slot", "LIVE" in noscore and "SCORE" in noscore)

# ----------------------------------------------------------------- lint ----

svgs = sorted((HERE / "preview" / "svg").glob("*.svg"))
check("preview svgs exist", len(svgs) >= 90, "{} files".format(len(svgs)))
proc = subprocess.run([sys.executable, str(HARNESS / "lint_svg.py")] + [str(p) for p in svgs],
                      capture_output=True, text=True)
check("lint_svg clean on {} files".format(len(svgs)), proc.returncode == 0,
      proc.stdout.strip().splitlines()[-1] if proc.stdout else "")
biggest = max(svgs, key=lambda p: p.stat().st_size)
check("largest svg under 64KB", biggest.stat().st_size <= 64 * 1024,
      "{} = {}B".format(biggest.name, biggest.stat().st_size))
check("no font/data/url leakage",
      not any(re.search(r"(data:|@font-face|https?://(?!www\.w3\.org))", p.read_text())
              for p in svgs))

digest = sha("".join(sorted(art_hashes.values()) + sorted(card_hashes.values())))
lines.append("PASS corpus digest {}".format(digest[:16]))
print("\n".join(lines))
