"""First-class checks for pyto 0.1.0, as a unittest module.

The three original assertions (PxC fail-loud + PQL composition, PCR direct-result
and publication semantics, duplicate-writer rejection) are preserved verbatim.
The module also pins the fan-out example (examples/shared_result_fanout.py) and
the PCR/Pcr Mermaid equality that ULTRACODE-WEEK.md gap 16 asks to retain.

Calculations are module-level functions held in an explicit REGISTRY; no anonymous functions.
"""

import unittest

from pyto import Calculation, Match, Part, PCR, Pcr, PQL, PxC


# --- Calculations (module-level functions, explicit registry) ------------------


def double(args):
    return args["value"] * 2


def add(args):
    return args["left"] + args["right"]


def identity(args):
    return args["value"]


def render_disc(args):
    return f"<svg data-disc='{args['request']['disc']}' />"


def compose_single(args):
    return {"layout": args["layout"], "art": args["art"]}


def compose_battle(args):
    return {"layout": args["layout"], "leftArt": args["art"]}


REGISTRY = {
    "fn.double": Calculation("fn.double", double),
    "fn.add": Calculation("fn.add", add),
    "fn.identity": Calculation("fn.identity", identity),
    "fn.disc.render": Calculation("fn.disc.render", render_disc),
    "fn.card.single.compose": Calculation("fn.card.single.compose", compose_single),
    "fn.card.battle.compose": Calculation("fn.card.battle.compose", compose_battle),
}


def address_mentions_badges(match: Match) -> bool:
    return "badges" in match.address


# --- Fan-out fixture (examples/shared_result_fanout.py:10-48) -------------------

DISC_REQUEST = Part("input.disc.request")
DISC_ART = Part("px.disc.art.svg")
SINGLE_CARD = Part("px.card.single")
BATTLE_CARD = Part("px.card.battle")
SINGLE_LAYOUT = {"layout": "art-above-numbers"}
BATTLE_LAYOUT = {"layout": "side-by-side"}


def build_fanout_pcr() -> PCR:
    """The executable fan-out program, authored through pyto.PCR (pcr.py:98-133)."""
    program = PCR("disc-cards")
    program.calc(
        "Art",
        REGISTRY["fn.disc.render"],
        id="render-disc",
        request=DISC_REQUEST,
        into=DISC_ART,
    )
    program.calc(
        "Cards",
        REGISTRY["fn.card.single.compose"],
        id="single-card",
        art=DISC_ART,
        args=dict(SINGLE_LAYOUT),
        into=SINGLE_CARD,
    )
    program.calc(
        "Cards",
        REGISTRY["fn.card.battle.compose"],
        id="battle-card",
        art=DISC_ART,
        args=dict(BATTLE_LAYOUT),
        into=BATTLE_CARD,
    )
    return program


def build_fanout_graph() -> Pcr:
    """The same fan-out, authored through the graph-only pyto.Pcr (graph.py:45-87)."""
    graph = Pcr("disc-cards")
    graph.calc(
        "Art",
        "fn.disc.render",
        id="render-disc",
        request=graph.part(DISC_REQUEST.address),
        into=DISC_ART.address,
    )
    graph.calc(
        "Cards",
        "fn.card.single.compose",
        id="single-card",
        art=graph.part(DISC_ART.address),
        args=dict(SINGLE_LAYOUT),
        into=SINGLE_CARD.address,
    )
    graph.calc(
        "Cards",
        "fn.card.battle.compose",
        id="battle-card",
        art=graph.part(DISC_ART.address),
        args=dict(BATTLE_LAYOUT),
        into=BATTLE_CARD.address,
    )
    return graph


def run_fanout():
    pxc = PxC()
    pxc.set(DISC_REQUEST, {"disc": "mako", "color": "blue"})
    program = build_fanout_pcr()
    return pxc, program, program.run(pxc)


class FirstClassTest(unittest.TestCase):
    """The three original bare-function checks, unchanged in what they assert."""

    def test_pxc_is_fail_loud_and_pql_is_composable(self):
        """PxC.set/get (core.py:56-66); PQL.part/prefix/where (pql.py:27-58)."""
        pxc = PxC()
        badges = Part("px.badges")
        remaining = Part("px.remaining.afterBadges")
        pxc.set(badges, [1, 2, 3])
        pxc.set(remaining, {10, 11})

        assert PQL.part(badges).one(pxc) == [1, 2, 3]
        assert [
            m.address for m in PQL.prefix("px.").where(address_mentions_badges).matches(pxc)
        ] == ["px.badges"]

    def test_pcr_preserves_direct_result_and_publication_semantics(self):
        """Part-to-ResultRef rewrite (pcr.py:112-116); into publication (pcr.py:163-164)."""
        pxc = PxC()
        source = Part("px.source")
        doubled = Part("px.doubled")
        final = Part("px.final")
        pxc.set(source, 3)

        pcr = PCR("demo")
        first = pcr.calc("A", REGISTRY["fn.double"], id="double", value=source, into=doubled)
        pcr.calc("B", REGISTRY["fn.add"], id="add", left=doubled, right=first, into=final)

        run = pcr.run(pxc)

        assert pxc.get(final) == 12
        add_testimony = run.ticks[1].calculations[0]
        assert add_testimony.inputs == {"left": "fn:double", "right": "fn:double"}

    def test_duplicate_writer_rejected(self):
        """Multiple-writer rejection at declaration (pcr.py:118-123)."""
        pcr = PCR("bad")
        out = Part("px.out")
        source = Part("px.source")

        pcr.calc("A", REGISTRY["fn.identity"], id="one", value=source, into=out)

        try:
            pcr.calc("B", REGISTRY["fn.identity"], id="two", value=source, into=out)
        except ValueError as error:
            assert "multiple writers" in str(error)
        else:
            raise AssertionError("expected multiple-writer failure")


class SharedResultFanoutTest(unittest.TestCase):
    """Pins examples/shared_result_fanout.py against the PcrRun shape (pcr.py:59-78)."""

    def setUp(self):
        self.pxc, self.program, self.run = run_fanout()

    def test_results_keyed_by_invocation_id(self):
        """PcrRun.results holds one entry per invocation id (pcr.py:162, pcr.py:177)."""
        self.assertEqual(
            set(self.run.results), {"render-disc", "single-card", "battle-card"}
        )

    def test_card_testimonies_consume_render_disc_as_fn_ref(self):
        """Both cards record inputs {'art': 'fn:render-disc'} (pcr.py:112-116, 156-157)."""
        art_tick, cards_tick = self.run.ticks
        self.assertEqual(art_tick.name, "Art")
        self.assertEqual(cards_tick.name, "Cards")
        self.assertEqual(
            [calc.inputs for calc in cards_tick.calculations],
            [{"art": "fn:render-disc"}, {"art": "fn:render-disc"}],
        )
        self.assertEqual(
            art_tick.calculations[0].inputs, {"request": "px:input.disc.request"}
        )

    def test_testimony_into_values_are_published_addresses(self):
        """CalculationTestimony.into is the into Part's address (pcr.py:172)."""
        into_by_id = {
            calc.id: calc.into for tick in self.run.ticks for calc in tick.calculations
        }
        self.assertEqual(
            into_by_id,
            {
                "render-disc": "px.disc.art.svg",
                "single-card": "px.card.single",
                "battle-card": "px.card.battle",
            },
        )

    def test_render_disc_result_is_the_same_object_for_both_cards(self):
        """The fn: binding passes results[id] itself, not a copy (pcr.py:156, 161)."""
        art = self.run.results["render-disc"]
        self.assertIs(self.run.results["single-card"]["art"], art)
        self.assertIs(self.run.results["battle-card"]["leftArt"], art)
        self.assertIs(self.pxc.get(DISC_ART), art)
        self.assertEqual(art, "<svg data-disc='mako' />")

    def test_shared_mutable_result_is_not_copied_between_consumers(self):
        """Companion to the str-valued example: a dict fn: result is passed by identity
        (pcr.py:156, 161). deepcopy of a str is the same object, so only a mutable
        shared result can detect a copy inserted at pcr.py:156."""
        pxc = PxC()
        request = Part("input.disc.request")
        shared = Part("px.disc.request.echo")
        pxc.set(request, {"disc": "mako", "color": "blue"})
        program = PCR("shared-dict")
        program.calc("Art", REGISTRY["fn.identity"], id="echo", value=request, into=shared)
        program.calc(
            "Cards",
            REGISTRY["fn.card.single.compose"],
            id="single-card",
            art=shared,
            args=dict(SINGLE_LAYOUT),
        )
        program.calc(
            "Cards",
            REGISTRY["fn.card.battle.compose"],
            id="battle-card",
            art=shared,
            args=dict(BATTLE_LAYOUT),
        )
        run = program.run(pxc)
        echoed = run.results["echo"]
        self.assertIsInstance(echoed, dict)
        self.assertIs(run.results["single-card"]["art"], echoed)
        self.assertIs(run.results["battle-card"]["leftArt"], echoed)
        self.assertIs(pxc.get(request), echoed)

    def test_pcr_and_pcr_graph_emit_identical_mermaid(self):
        """Gap 16: PCR.mermaid() (pcr.py:179-219) == Pcr.to_mermaid() (graph.py:116-151)."""
        executable = build_fanout_pcr().mermaid()
        graph = build_fanout_graph().to_mermaid()
        self.assertEqual(executable, graph)
        self.assertIn("render-disc -->|art| single-card", executable)
        self.assertIn("render-disc -->|art| battle-card", executable)


if __name__ == "__main__":
    unittest.main()
