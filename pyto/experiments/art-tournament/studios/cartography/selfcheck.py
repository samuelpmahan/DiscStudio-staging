#!/usr/bin/env python3
"""Contract self-check for studio *cartography*.

    python3 selfcheck.py

Proves, for every family and both card renderers:
  * determinism      — two independent renders are byte-identical (sha256)
  * RNG discipline   — the seeded draw sequence is identical at 42/96/220, so
                       rendering another target consumes no extra randomness
  * document shape   — width/height == target, 512 viewBox, r=220 disc clip,
                       rim, aria-label, <title>, label text only at 220
  * hygiene          — harness lint (XML, xmlns, viewBox, no external refs,
                       no @font-face, <= 64KB) on every artifact, including a
                       worst-case battle card carrying two 220px arts
  * card contract    — every layout x details combination renders the name,
                       the maker/mold line, all four flight figures and a
                       score slot, and honours card['layout'] / card['details']
"""
from __future__ import annotations

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
    recorders: list[_Recorder] = []

    def factory(s):
        rec = _Recorder(s)
        recorders.append(rec)
        return rec

    original = families.random.Random
    families.random.Random = factory
    try:
        families.render(slug, seed, "#4c9bc6", "#0d3558", target, "Warm Mako")
    finally:
        families.random.Random = original
    return recorders[0].log if recorders else []


def art_hashes() -> dict[str, str]:
    digests = {}
    for slug in families.FAMILIES:
        for pname, (base, accent) in PALETTES.items():
            for seed, label in zip(SEEDS, LABELS):
                # RNG discipline: identical draw sequence at every target.
                logs = [rng_log(slug, seed, t) for t in TARGETS]
                check(logs[0] == logs[1] == logs[2],
                      f"{slug} s{seed}: RNG draws differ between targets")
                for target in TARGETS:
                    a = families.render(slug, seed, base, accent, target, label)
                    b = families.render(slug, seed, base, accent, target, label)
                    key = f"{slug}/{pname}/{seed}/{target}"
                    check(a == b, f"{key}: two renders differ")
                    digests[key] = sha(a)
                    check(f'width="{target}" height="{target}"' in a, f"{key}: wrong intrinsic size")
                    check('viewBox="0 0 512 512"' in a, f"{key}: wrong viewBox")
                    check('<circle cx="256" cy="256" r="220"/>' in a, f"{key}: no r=220 disc clip")
                    check('id="rim"' in a, f"{key}: no rim group")
                    check("aria-label=" in a and "<title>" in a, f"{key}: missing aria-label/title")
                    has_text = "<text" in a
                    check(has_text == (target == 220), f"{key}: text present at {target}px")
                    if target == 220:
                        check(label.strip()[:12] in a, f"{key}: label not drawn at 220")
                    problems = lint_bytes(a.encode("utf-8"), key)
                    check(not problems, f"{key}: lint {problems}")
    return digests


def card_checks() -> dict[str, str]:
    digests = {}
    art_by_family = {
        slug: {pid: families.render(slug, seed, *PALETTES["cool"], 220, "art")
               for pid, seed in (("active", 3), ("rival", 7))}
        for slug in families.FAMILIES
    }
    for key, card in SAMPLE_CARDS.items():
        kind = card["type"]
        render = cards.render_single if kind == "single" else cards.render_battle
        for slug, art in art_by_family.items():
            for width in (400, 700):
                for details in (True, False):
                    value = dict(card, details=details)
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
                    for flight in ("5", "4", "-1", "1"):
                        check(f">{flight}<" in a, f"{tag}: flight figure {flight} missing")
                    if kind == "battle":
                        check("SCORE" in a and ">7<" in a, f"{tag}: score slot missing")
                        check(card["participants"][1]["name"] in a, f"{tag}: rival name missing")
                    check("UNRECORDED MOLD" in a or "INNOVA" in a,
                          f"{tag}: maker/mold line missing")
                    if details:
                        check("SPEED" in a and "FADE" in a, f"{tag}: legend labels missing")
                        if kind == "single":
                            # The note is a single-plate field; a match plate has no room for it.
                            check("first run" in a, f"{tag}: note missing with details on")
                    else:
                        check("SPEED" not in a, f"{tag}: details=False still draws legend captions")
                        check("first run" not in a, f"{tag}: details=False still draws the note")
                        check("SCALE" not in a, f"{tag}: unexpected scale caption")
                    check(card["layout"] in a, f"{tag}: layout not named in the label")
                    problems = lint_bytes(a.encode("utf-8"), tag)
                    check(not problems, f"{tag}: lint {problems}")
    # Layout actually changes the plate, and both layouts differ per kind.
    check(cards.render_single(SAMPLE_CARDS["single_standard"], art_by_family["wind-rose"], 400)
          != cards.render_single(SAMPLE_CARDS["single_gallery"], art_by_family["wind-rose"], 400),
          "single: standard and gallery render identically")
    check(cards.render_battle(SAMPLE_CARDS["battle_standard"], art_by_family["wind-rose"], 400)
          != cards.render_battle(SAMPLE_CARDS["battle_stacked"], art_by_family["wind-rose"], 400),
          "battle: standard and stacked render identically")
    # Worst case for the 64KB cap: a battle plate carrying two 220px basins.
    heavy = {pid: families.render("contour-basin", seed, *PALETTES["dark"], 220, "Warm Mako")
             for pid, seed in (("active", 3), ("rival", 7))}
    plate = cards.render_battle(SAMPLE_CARDS["battle_standard"], heavy, 700)
    size = len(plate.encode("utf-8"))
    check(size <= 64 * 1024, f"worst-case battle plate is {size}B")
    check(not lint_bytes(plate.encode("utf-8"), "worst-case"), "worst-case battle plate fails lint")
    # Two arts on one plate must not share element ids.
    ids = re.findall(r'id="([^"]+)"', plate)
    check(len(ids) == len(set(ids)), "duplicate element ids on a two-disc plate")
    # Missing art must degrade, not explode.
    check("NO PLATE" in cards.render_single(SAMPLE_CARDS["single_standard"], {}, 400),
          "single: missing art is not handled")
    return digests, size


def registry_checks() -> None:
    expected_art = {f"fn.discArt.{slug}" for slug in families.FAMILIES}
    check(set(families.CALCULATIONS) == expected_art, "families.CALCULATIONS keys are wrong")
    check(set(cards.CALCULATIONS) == {"fn.card.single.render", "fn.card.battle.render"},
          "cards.CALCULATIONS keys are wrong")
    for name, fn in {**families.CALCULATIONS, **cards.CALCULATIONS}.items():
        check(fn.__name__ != "<lambda>", f"{name} is a lambda")
        check(callable(fn), f"{name} is not callable")
    check(set(families.FAMILY_PARAMS) == set(families.FAMILIES), "FAMILY_PARAMS keys are wrong")
    for slug, params in families.FAMILY_PARAMS.items():
        check({"name", "seed", "base", "accent", "label", "target"} <= set(params),
              f"FAMILY_PARAMS[{slug}] is missing a documented input")
    existing = {"orbit foundry", "petal press", "signal stamp", "tessellated flight"}
    check(not (set(s.replace("-", " ") for s in families.FAMILIES) & existing),
          "a family slug collides with an existing family")


def main() -> int:
    digests = art_hashes()
    card_digests, worst = card_checks()
    registry_checks()
    art_fingerprint = sha("".join(f"{k}:{v}" for k, v in sorted(digests.items())))
    card_fingerprint = sha("".join(f"{k}:{v}" for k, v in sorted(card_digests.items())))
    print(f"checks run:            {CHECKS}")
    print(f"art renders compared:  {len(digests)} (3 families x 3 palettes x 3 seeds x 3 targets)")
    print(f"card renders compared: {len(card_digests)} (4 fixtures x 3 arts x 2 widths x details on/off)")
    print(f"worst-case battle plate: {worst}B of 65536B")
    print(f"art sha256 fingerprint:  {art_fingerprint}")
    print(f"card sha256 fingerprint: {card_fingerprint}")
    if FAILURES:
        print(f"FAIL ({len(FAILURES)}):")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("PASS: determinism, RNG discipline, document shape, lint and card contract all hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
