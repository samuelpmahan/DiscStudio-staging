#!/usr/bin/env python3
"""Demonstrate the whole disc-art registry through pyto's own PCR/PQL seams.

The owner's rule for the art tournament pass is that nothing gets deleted and
everything stays reachable until it can be tried in a browser
(``pyto/consumers/discstudio-card/art_registry.py``,
``pyto/experiments/art-tournament/RESULTS.md``). This script is the smallest
runnable proof of that: it registers all 26 Calculations the tournament
produced -- 16 ``fn.discArt.<slug>`` families and 10 card-renderer addresses --
on one ``PxC``, then runs one ``PCR`` that renders a single family and fans the
result out to **both promoted** card renderers (``single/botanical``,
``battle/signal``), the same shared-result pattern
``examples/shared_result_fanout.py`` demonstrates and
``test_art_registry.py::test_one_art_result_fans_out_to_each_studios_single_and_battle``
holds every studio to.

``register_all`` puts Calculations on the PxC's Calculation registry, not its
Part store, so a PQL query cannot see any of them
(``src/pyto/pql.py`` selects over produced Parts only) -- this script proves
that too, the same invariant ``test_art_registry.py`` pins.

Prints one line of JSON to stdout: the fan-out testimony (which invocations
consumed the shared art result, in execution order) plus the full list of
registered ``fn.discArt.*`` addresses, read from ``art_registry.CALCULATIONS``
because PQL cannot enumerate them. With ``--out DIR`` it additionally writes
the rendered SVGs and this same summary under ``DIR`` -- and nowhere else;
omit ``--out`` and the script writes no file at all.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# consumers/discstudio-card is not on sys.path by default; this is the one
# directory this example reaches into, the same way test_art_registry.py and
# the tournament harness's fixtures.py do.
EXAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))
PYTO_DIR = os.path.dirname(EXAMPLES_DIR)
CONSUMER_DIR = os.path.join(PYTO_DIR, "consumers", "discstudio-card")
if CONSUMER_DIR not in sys.path:
    sys.path.insert(0, CONSUMER_DIR)

import art_registry  # noqa: E402
import card_composition  # noqa: E402
from test_card_composition import recipe as _recipe  # noqa: E402

from pyto import Calculation, PCR, PQL, Part, PxC  # noqa: E402

FAMILY = "pressed-fern"  # promoted; tally 68/72, RESULTS.md section 1
SEED = 7
BASE, ACCENT = "#4c9bc6", "#0d3558"
WIDTH = 400

# ------------------------------------------------------------------ PCR seam
#
# PCR hands a Calculation one mapping of arguments, so these three module-level
# functions adapt that shape onto the registry's positional render signatures
# -- the same pattern test_art_registry.py's PCR fan-out test uses. Each one
# calls straight into art_registry, so this really is "the registered family
# and the registered card renderers", not a second implementation of them.
# Addressed "fn.demo.*", distinct from the registry's own "fn.discArt.*" /
# "fn.card.*" addresses so they can be declared as PCR calculations on the
# very same PxC that art_registry.register_all already populated, without
# PxC.register's already-registered-under-a-different-function check firing.
# No lambdas: every Calculation in this file names a real, inspectable
# function.

def render_art_calculation(args):
    """fn.demo.render-art -- one art result, shared by both card renderers."""
    request = args["request"]
    out = {}
    for index, participant in enumerate(request["participants"]):
        out[participant["presentationId"]] = art_registry.family_render(
            FAMILY, SEED + 5 * index, BASE, ACCENT, 220, participant.get("name", "disc"))
    return out


def render_single_calculation(args):
    entry = art_registry.CARD_RENDERERS["single"]["botanical"]
    return entry.render(args["card"], args["art"], args["width"])


def render_battle_calculation(args):
    entry = art_registry.CARD_RENDERERS["battle"]["signal"]
    return entry.render(args["card"], args["art"], args["width"])


def build_program():
    """Register everything, then run one PCR -- on that same PxC -- that fans
    one art result out to both promoted card renderers. Returns
    (pxc, run, parts, registered)."""
    pxc = PxC()
    registered = art_registry.register_all(pxc)  # every family + card renderer

    composed = card_composition.compose(_recipe())
    single_card = composed["cards"]["single"]
    battle_card = composed["cards"]["battle"]

    request = Part("input.card.request")
    art_part = Part("px.disc.art.map")
    single_part = Part("px.card.single.svg")
    battle_part = Part("px.card.battle.svg")

    pxc.set(request, {"participants": battle_card["participants"]})

    program = PCR("art-registry-demo")
    program.calc("Art", Calculation("fn.demo.render-art", render_art_calculation),
                 id="render-art", request=request, into=art_part)
    program.calc("Cards", Calculation("fn.demo.card.single", render_single_calculation),
                 id="single-card", art=art_part,
                 args={"card": single_card, "width": WIDTH}, into=single_part)
    program.calc("Cards", Calculation("fn.demo.card.battle", render_battle_calculation),
                 id="battle-card", art=art_part,
                 args={"card": battle_card, "width": WIDTH}, into=battle_part)

    run = program.run(pxc)
    parts = {"art": art_part, "single": single_part, "battle": battle_part}
    return pxc, run, parts, registered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", metavar="DIR", default=None,
                         help="write the rendered SVGs and the summary JSON here; "
                              "omit to write nothing at all")
    args = parser.parse_args()

    pxc, run, parts, registered = build_program()

    # Fan-out testimony: both card calculations consumed the one art result,
    # in declaration order, via execution testimony rather than a direct call.
    consumers = [
        calculation.id
        for tick in run.ticks
        for calculation in tick.calculations
        if calculation.inputs.get("art") == "fn:render-art"
    ]

    # register_all puts Calculations on the Calculation registry, never on the
    # Part store, so PQL cannot see a single one of them.
    pql_addresses = [match.address for match in PQL.prefix("fn.").matches(pxc)]

    disc_art_addresses = sorted(
        address for address in art_registry.CALCULATIONS if address.startswith("fn.discArt.")
    )

    summary = {
        "sharedResult": "fn:render-art",
        "consumers": consumers,
        "registeredCalculations": len(registered),
        "pqlVisibleCalculations": pql_addresses,
        "discArtAddresses": disc_art_addresses,
    }
    print(json.dumps(summary, sort_keys=True))

    if args.out:
        out_dir = args.out
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "art.svg"), "w", encoding="utf-8", newline="\n") as handle:
            handle.write(next(iter(pxc.get(parts["art"]).values())))
        with open(os.path.join(out_dir, "single.svg"), "w", encoding="utf-8", newline="\n") as handle:
            handle.write(pxc.get(parts["single"]))
        with open(os.path.join(out_dir, "battle.svg"), "w", encoding="utf-8", newline="\n") as handle:
            handle.write(pxc.get(parts["battle"]))
        with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8", newline="\n") as handle:
            json.dump(summary, handle, sort_keys=True, indent=2)
            handle.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
