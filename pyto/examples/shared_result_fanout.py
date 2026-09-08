"""Characterize result reuse and dependency inspection in pyto-lab 0.1.0."""

from __future__ import annotations

import json

from pyto import Calculation, Part, PCR, PQL, PxC


disc_request = Part("input.disc.request")
disc_art = Part("px.disc.art.svg")
single_card = Part("px.card.single")
battle_card = Part("px.card.battle")

pxc = PxC()
pxc.set(disc_request, {"disc": "mako", "color": "blue"})

render_disc = Calculation(
    "fn.disc.render",
    lambda args: f"<svg data-disc='{args['request']['disc']}' />",
)
compose_single = Calculation(
    "fn.card.single.compose",
    lambda args: {"layout": args["layout"], "art": args["art"]},
)
compose_battle = Calculation(
    "fn.card.battle.compose",
    lambda args: {"layout": args["layout"], "leftArt": args["art"]},
)

program = PCR("disc-cards")
program.calc("Art", render_disc, id="render-disc", request=disc_request, into=disc_art)
program.calc(
    "Cards",
    compose_single,
    id="single-card",
    art=disc_art,
    args={"layout": "art-above-numbers"},
    into=single_card,
)
program.calc(
    "Cards",
    compose_battle,
    id="battle-card",
    art=disc_art,
    args={"layout": "side-by-side"},
    into=battle_card,
)

run = program.run(pxc)

# PQL finds produced results by semantic address. Dependency traversal is still
# ordinary Python over execution testimony; PQL does not provide graph traversal.
produced_cards = PQL.prefix("px.card.").matches(pxc)
art_consumers = [
    calculation.id
    for tick in run.ticks
    for calculation in tick.calculations
    if "fn:render-disc" in calculation.inputs.values()
]

assert art_consumers == ["single-card", "battle-card"]
assert [match.address for match in produced_cards] == ["px.card.battle", "px.card.single"]
assert pxc.get(single_card)["layout"] == "art-above-numbers"
assert pxc.get(battle_card)["layout"] == "side-by-side"

print(
    json.dumps(
        {
            "sharedResult": "fn:render-disc",
            "consumers": art_consumers,
            "producedParts": [match.address for match in produced_cards],
        },
        sort_keys=True,
    )
)
