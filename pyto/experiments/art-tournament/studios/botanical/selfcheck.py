#!/usr/bin/env python3
"""Contract self-check for studio *botanical*.

    python3 selfcheck.py

Proves, for all three families and both card renderers:
  * determinism      — two independent renders are byte-identical (sha256)
  * RNG discipline   — the seeded draw sequence is identical at 42/96/220, so
                       rendering another target consumes no extra randomness
  * document shape   — width/height == target, 512 viewBox, r=220 disc clip,
                       a rim, aria-label, <title>, label text only at 220
  * hygiene          — harness lint (well-formed XML, xmlns, viewBox, no
                       external/data href, no <image>, no @font-face, <= 64KB)
                       on every artifact, including the worst-case battle plate
                       carrying two 220px arts
  * card contract    — every layout x details combination renders the name, the
                       maker/mold line, all four flight figures and a score
                       slot, honours card['layout'] and card['details'], keeps
                       element ids unique across two embedded arts, and degrades
                       rather than raising when the art is missing
  * distinctness     — no slug collides with the four paint_components families
"""
from __future__ import annotations

import copy
import hashlib
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HARNESS = HERE.parents[1] / "harness"
for extra in (str(HERE), str(HARNESS)):
    if extra not in sys.path:
        sys.path.insert(0, extra)

import families  # noqa: E402
import cards  # noqa: E402
from fixtures import PALETTES, SEEDS, LABELS, SAMPLE_CARDS  # noqa: E402
from lint_svg import lint_bytes  # noqa: E402

TARGETS = (42, 96, 220)
FAILURES: list[str] = []
CHECKS = 0


def check(condition: bool, message: str) -> None:
    global CHECKS
    CHECKS += 1
    if not condition:
        FAILURES.append(message)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class _Recorder(random.Random):
    """A Random that logs every draw, so RNG use can be compared per target."""

    def __init__(self, seed):
        super().__init__(seed)
        self.log: list = []

    def uniform(self, a, b):
        value = super().uniform(a, b)
        self.log.append(("uniform", a, b, value))
        return value

    def randrange(self, *a, **k):
        value = super().randrange(*a, **k)
        self.log.append(("randrange", a, value))
        return value

    def random(self):
        value = super().random()
        self.log.append(("random", value))
        return value

    def choice(self, seq):
        value = super().choice(seq)
        self.log.append(("choice", tuple(seq), value))
        return value


def rng_log(slug: str, seed: int, target: int) -> list:
    seen: list[_Recorder] = []

    def factory(s):
        rec = _Recorder(s)
        seen.append(rec)
        return rec

    original = families.random.Random
    families.random.Random = factory
    try:
        families.render(slug, seed, "#e8d8b0", "#7a3b1e", target, "Warm Mako")
    finally:
        families.random.Random = original
    return seen[0].log if seen else []


def art_checks() -> tuple[dict[str, str], int]:
    digests: dict[str, str] = {}
    biggest = 0
    for slug in families.FAMILIES:
        for pname, (base, accent) in PALETTES.items():
            for seed, label in zip(SEEDS, LABELS):
                logs = [rng_log(slug, seed, t) for t in TARGETS]
                check(logs[0] == logs[1] == logs[2],
                      f"{slug} s{seed}: RNG draws differ between targets")
                check(bool(logs[0]), f"{slug} s{seed}: no seeded draws at all")
                for target in TARGETS:
                    a = families.render(slug, seed, base, accent, target, label)
                    b = families.render(slug, seed, base, accent, target, label)
                    key = f"{slug}/{pname}/{seed}/{target}"
                    check(a == b, f"{key}: two renders differ")
                    digests[key] = sha(a)
                    biggest = max(biggest, len(a.encode("utf-8")))
                    check(f'width="{target}" height="{target}"' in a, f"{key}: wrong intrinsic size")
                    check('viewBox="0 0 512 512"' in a, f"{key}: wrong viewBox")
                    check('<circle cx="256" cy="256" r="220"/>' in a, f"{key}: no r=220 disc clip")
                    check('id="rim"' in a, f"{key}: no rim group")
                    check('clip-path="url(#disc)"' in a, f"{key}: art is not clipped to the disc")
                    check("aria-label=" in a and "<title>" in a, f"{key}: missing aria-label/title")
                    check(("<text" in a) == (target == 220), f"{key}: text present at {target}px")
                    if target == 220:
                        check(label.strip()[:13] in a, f"{key}: label not drawn at 220")
                    problems = lint_bytes(a.encode("utf-8"), key)
                    check(not problems, f"{key}: lint {problems}")
                # a seed change must change the drawing at every tier
                other = families.render(slug, seed + 1, base, accent, 220, label)
                check(other != families.render(slug, seed, base, accent, 220, label),
                      f"{slug}/{seed}: seed does not change the art")
    # every family differs from every other at 42px, on the same seed and palette
    for target in (42, 220):
        marks = {slug: families.render(slug, 7, *PALETTES["warm"], target, "Warm Mako")
                 for slug in families.FAMILIES}
        check(len(set(marks.values())) == len(marks), f"two families render alike at {target}px")
    return digests, biggest


def card_checks() -> tuple[dict[str, str], int]:
    digests: dict[str, str] = {}
    arts = {slug: {pid: families.render(slug, seed, *PALETTES["warm"], 220, "Warm Mako")
                   for pid, seed in (("active", 3), ("rival", 7))}
            for slug in families.FAMILIES}
    for key, card in SAMPLE_CARDS.items():
        kind = card["type"]
        render = cards.render_single if kind == "single" else cards.render_battle
        for slug, art in arts.items():
            for width in (400, 700):
                for details in (True, False):
                    value = copy.deepcopy(card)
                    value["details"] = details
                    if kind == "battle":
                        value["scores"] = {"active": 7, "rival": 4}
                        value["winner"] = "active"
                    a = render(value, art, width)
                    b = render(value, art, width)
                    tag = f"{key}/{slug}/{width}/details={details}"
                    check(a == b, f"{tag}: two renders differ")
                    digests[tag] = sha(a)
                    check(f'width="{width}"' in a, f"{tag}: wrong width")
                    check(card["participants"][0]["name"] in a, f"{tag}: name missing")
                    for figure in ("5", "4", "-1", "1"):
                        check(f">{figure}<" in a, f"{tag}: flight figure {figure} missing")
                    check("UNRECORDED MOLD" in a, f"{tag}: maker/mold line missing")
                    if kind == "battle":
                        check("SCORE" in a and ">7<" in a and ">4<" in a, f"{tag}: score slot missing")
                        check(card["participants"][1]["name"] in a, f"{tag}: rival name missing")
                    if details:
                        check("SPEED" in a and "GLIDE" in a and "TURN" in a and "FADE" in a,
                              f"{tag}: legend captions missing")
                        check("first run" in a, f"{tag}: the note is dropped with details on")
                    else:
                        check("SPEED" not in a, f"{tag}: details=False still draws legend captions")
                        check("first run" not in a, f"{tag}: details=False still draws the note")
                    check(card["layout"].upper() in a, f"{tag}: layout is not named on the plate")
                    problems = lint_bytes(a.encode("utf-8"), tag)
                    check(not problems, f"{tag}: lint {problems}")
    # layout actually changes the plate
    art = arts["block-print"]
    check(cards.render_single(SAMPLE_CARDS["single_standard"], art, 400)
          != cards.render_single(SAMPLE_CARDS["single_gallery"], art, 400),
          "single: standard and gallery render identically")
    check(cards.render_battle(SAMPLE_CARDS["battle_standard"], art, 400)
          != cards.render_battle(SAMPLE_CARDS["battle_stacked"], art, 400),
          "battle: standard and stacked render identically")
    # scores accept a dict, an index map and a list
    for scores in ({"active": 7, "rival": 4}, {"0": 7, "1": 4}, [7, 4]):
        value = dict(SAMPLE_CARDS["battle_standard"], scores=scores)
        plate = cards.render_battle(value, art, 700)
        check(">7<" in plate and ">4<" in plate, f"battle: scores {scores!r} not read")
    # worst case for the 64KB cap: the heaviest art, twice, on one plate
    heavy_slug = max(families.FAMILIES,
                     key=lambda s: len(families.render(s, 42, *PALETTES["dark"], 220, "Warm Mako")))
    heavy = {pid: families.render(heavy_slug, seed, *PALETTES["dark"], 220, "Warm Mako")
             for pid, seed in (("active", 42), ("rival", 3))}
    plate = cards.render_battle(dict(SAMPLE_CARDS["battle_standard"], scores=[7, 4]), heavy, 700)
    worst = len(plate.encode("utf-8"))
    check(worst <= 64 * 1024, f"worst-case battle plate is {worst}B ({heavy_slug})")
    check(not lint_bytes(plate.encode("utf-8"), "worst-case"), "worst-case battle plate fails lint")
    ids = re.findall(r'id="([^"]+)"', plate)
    check(len(ids) == len(set(ids)), "duplicate element ids on a two-disc plate")
    # missing art degrades instead of raising
    check("NO PLATE" in cards.render_single(SAMPLE_CARDS["single_standard"], {}, 400),
          "single: missing art is not handled")
    check("NO PLATE" in cards.render_battle(SAMPLE_CARDS["battle_stacked"], {}, 400),
          "battle: missing art is not handled")
    return digests, worst


def registry_checks() -> None:
    check(set(families.CALCULATIONS) == {f"fn.discArt.{slug}" for slug in families.FAMILIES},
          "families.CALCULATIONS keys are wrong")
    check(set(cards.CALCULATIONS) == {"fn.card.single.render", "fn.card.battle.render"},
          "cards.CALCULATIONS keys are wrong")
    for name, fn in {**families.CALCULATIONS, **cards.CALCULATIONS}.items():
        check(callable(fn) and fn.__name__ != "<lambda>", f"{name} is not a named callable")
    check(set(families.FAMILY_PARAMS) == set(families.FAMILIES), "FAMILY_PARAMS keys are wrong")
    for slug, params in families.FAMILY_PARAMS.items():
        check({"name", "seed", "base", "accent", "label", "target"} <= set(params),
              f"FAMILY_PARAMS[{slug}] is missing a documented input")
    existing = {"orbit foundry", "petal press", "signal stamp", "tessellated flight"}
    check(not ({slug.replace("-", " ") for slug in families.FAMILIES} & existing),
          "a family slug collides with a paint_components family")
    for slug in families.FAMILIES:
        check(slug == slug.lower() and " " not in slug and "_" not in slug,
              f"{slug} is not a kebab-case slug")


def main() -> int:
    art_digests, biggest = art_checks()
    card_digests, worst = card_checks()
    registry_checks()
    art_print = sha("".join(f"{k}:{v}" for k, v in sorted(art_digests.items())))
    card_print = sha("".join(f"{k}:{v}" for k, v in sorted(card_digests.items())))
    print(f"checks run:              {CHECKS}")
    print(f"art renders compared:    {len(art_digests)} (3 families x 3 palettes x 3 seeds x 3 targets)")
    print(f"card renders compared:   {len(card_digests)} (4 fixtures x 3 arts x 2 widths x details on/off)")
    print(f"largest art document:    {biggest}B of 65536B")
    print(f"worst-case battle plate: {worst}B of 65536B")
    print(f"art sha256 fingerprint:  {art_print}")
    print(f"card sha256 fingerprint: {card_print}")
    if FAILURES:
        print(f"FAIL ({len(FAILURES)}):")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("PASS: determinism, RNG discipline, document shape, lint and card contract all hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
