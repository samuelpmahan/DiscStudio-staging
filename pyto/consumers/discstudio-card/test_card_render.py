"""Guards for the promoted card renderers.

``card_render.render_single`` came from studio *botanical* and
``card_render.render_battle`` from studio *signal* (see
``experiments/art-tournament/RESULTS.md``). Both take the JSON that
``card_composition.compose()`` produces plus a presentationId -> disc-art SVG
mapping, and both must be deterministic, lint-clean, honour ``layout`` and
``details``, and inline the art with no external reference of any kind.

The lint checks mirror ``experiments/art-tournament/harness/lint_svg.py``; they
are shared with ``test_paint_families`` rather than restated.
"""

import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyto import Calculation, PCR, Part, PxC

import card_render
import paint_components
from card_composition import compose
from test_paint_families import SVG_NS, lint

FAMILY = "pressed-fern"
BASE, ACCENT = "#4c9bc6", "#0d3558"
FLIGHT_LABELS = ("SPEED", "GLIDE", "TURN", "FADE")


def recipe(single_layout="standard", battle_layout="standard", details=True, populated=True):
    """A schema-3 recipe shaped like the one test_card_composition uses."""
    active = {
        "presentationId": "active", "physicalDiscId": "disc-1", "name": "Warm Mako",
        "note": "first run", "color": "#4c9bc6",
        "flightValues": {"flight1": 5, "flight2": 4, "flight3": -1, "flight4": 1},
    }
    rival = {**active, "presentationId": "rival", "physicalDiscId": "disc-2", "name": "Rival Buzzz",
             "color": "#c0563f",
             "flightValues": {"flight1": 5, "flight2": 4, "flight3": 0, "flight4": 2}}
    if populated:
        active.update({"manufacturer": "Innova", "mold": "Mako3"})
        rival.update({"manufacturer": "Discraft", "mold": "Buzzz"})
    return {
        "schemaVersion": 3, "presentationId": "active", "physicalDiscId": "disc-1",
        "cards": {
            "single": {"type": "single", "layout": single_layout, "details": details,
                       "discRecipeIds": ["active"]},
            "battle": {"type": "battle", "layout": battle_layout, "details": details,
                       "discRecipeIds": ["active", "rival"],
                       "scores": {"active": 7, "rival": 4}, "winner": "active"},
        },
        "presentations": {"active": active, "rival": rival},
    }


def art_for(cards):
    """presentationId -> a full disc-art SVG, one per participant across both cards."""
    out = {}
    for key in ("single", "battle"):
        for index, participant in enumerate(cards[key]["participants"]):
            pid = participant["presentationId"]
            if pid not in out:
                out[pid] = paint_components.render(
                    FAMILY, 7 + 5 * index, BASE, ACCENT, 220, participant.get("name", "disc"))
    return out


def render_art_calculation(args):
    """fn.discArt.render -- one art result, shared by both card renderers."""
    request = args["request"]
    out = {}
    for index, participant in enumerate(request["participants"]):
        out[participant["presentationId"]] = paint_components.render(
            request["family"], 7 + 5 * index, request["base"], request["accent"], 220,
            participant.get("name", "disc"))
    return out


def single_calculation(args):
    return card_render.render_single(args["card"], args["art"], args["width"])


def battle_calculation(args):
    return card_render.render_battle(args["card"], args["art"], args["width"])


class CardRenderTest(unittest.TestCase):
    def cards(self, **kwargs):
        composed = compose(recipe(**kwargs))["cards"]
        return composed, art_for(composed)

    # ---------------------------------------------------------------- layouts

    def test_single_renders_both_layouts_from_compose_output(self):
        for layout in ("standard", "gallery"):
            cards, art = self.cards(single_layout=layout)
            svg = card_render.render_single(cards["single"], art, 400)
            with self.subTest(layout=layout):
                self.assertEqual(lint(svg), [])
                root = ET.fromstring(svg)
                self.assertEqual(root.attrib["width"], "400")
                self.assertIn("viewBox", root.attrib)
                self.assertIn("Warm Mako", svg)
                self.assertIn("INNOVA", svg.upper())
                self.assertIn("MAKO3", svg.upper())
                for label in FLIGHT_LABELS:
                    self.assertIn(label, svg.upper())
                for value in (">5<", ">4<", ">-1<", ">1<"):
                    self.assertIn(value, svg)
        standard = card_render.render_single(self.cards(single_layout="standard")[0]["single"],
                                             art_for(compose(recipe())["cards"]), 400)
        gallery = card_render.render_single(self.cards(single_layout="gallery")[0]["single"],
                                            art_for(compose(recipe())["cards"]), 400)
        self.assertNotEqual(standard, gallery, "layout must change the document, not just scale it")

    def test_battle_renders_both_layouts_with_a_score_slot(self):
        seen = {}
        for layout in ("standard", "stacked"):
            cards, art = self.cards(battle_layout=layout)
            svg = card_render.render_battle(cards["battle"], art, 400)
            seen[layout] = svg
            with self.subTest(layout=layout):
                self.assertEqual(lint(svg), [])
                self.assertEqual(ET.fromstring(svg).attrib["width"], "400")
                self.assertIn("Warm Mako", svg)
                self.assertIn("Rival Buzzz", svg)
                self.assertIn(">7<", svg)
                self.assertIn(">4<", svg)
                self.assertIn("SCORE", svg.upper())
                for label in FLIGHT_LABELS:
                    self.assertIn(label, svg.upper())
        self.assertNotEqual(seen["standard"], seen["stacked"])

    def test_missing_scores_still_render_a_slot(self):
        value = recipe()
        del value["cards"]["battle"]["scores"]
        del value["cards"]["battle"]["winner"]
        cards = compose(value)["cards"]
        svg = card_render.render_battle(cards["battle"], art_for(cards), 400)
        self.assertEqual(lint(svg), [])
        self.assertIn("SCORE", svg.upper())

    def test_details_flag_is_honoured_by_both_renderers(self):
        rich, art = self.cards(details=True)
        lean, _ = self.cards(details=False)
        single_rich = card_render.render_single(rich["single"], art, 400)
        single_lean = card_render.render_single(lean["single"], art, 400)
        battle_rich = card_render.render_battle(rich["battle"], art, 400)
        battle_lean = card_render.render_battle(lean["battle"], art, 400)
        self.assertNotEqual(single_rich, single_lean)
        self.assertNotEqual(battle_rich, battle_lean)
        for svg in (single_lean, battle_lean):
            self.assertEqual(lint(svg), [])
            self.assertIn("Warm Mako", svg)

    def test_an_unrecorded_mold_is_marked_not_papered_over_with_the_note(self):
        """The one defect the judges named by name in a runner-up renderer."""
        cards, art = self.cards(populated=False)
        single = card_render.render_single(cards["single"], art, 400)
        battle = card_render.render_battle(cards["battle"], art, 400)
        self.assertIn("UNRECORDED MOLD", single.upper())
        self.assertNotIn("FIRST RUN", single.upper().split("UNRECORDED MOLD")[0])
        self.assertIn("DISC-1", battle.upper())

    # ------------------------------------------------------------ determinism

    def test_render_is_deterministic_within_and_across_processes(self):
        digest = hashlib.sha256()
        for single_layout in ("standard", "gallery"):
            for battle_layout in ("standard", "stacked"):
                for details in (True, False):
                    for width in (320, 400, 700):
                        cards, art = self.cards(single_layout=single_layout,
                                                battle_layout=battle_layout, details=details)
                        single = card_render.render_single(cards["single"], art, width)
                        battle = card_render.render_battle(cards["battle"], art, width)
                        self.assertEqual(single, card_render.render_single(cards["single"], art, width))
                        self.assertEqual(battle, card_render.render_battle(cards["battle"], art, width))
                        digest.update(single.encode("utf-8"))
                        digest.update(battle.encode("utf-8"))
        here = os.path.dirname(os.path.abspath(__file__))
        script = (
            "import hashlib, sys; sys.path.insert(0, %r);"
            "import card_render as cr; from test_card_render import recipe, art_for;"
            "from card_composition import compose; d = hashlib.sha256();\n"
            "for sl in ('standard', 'gallery'):\n"
            "    for bl in ('standard', 'stacked'):\n"
            "        for det in (True, False):\n"
            "            for w in (320, 400, 700):\n"
            "                c = compose(recipe(sl, bl, det))['cards']; a = art_for(c)\n"
            "                d.update(cr.render_single(c['single'], a, w).encode())\n"
            "                d.update(cr.render_battle(c['battle'], a, w).encode())\n"
            "print(d.hexdigest())\n"
        ) % here
        env = dict(os.environ, PYTHONHASHSEED="1", PYTHONDONTWRITEBYTECODE="1")
        out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                             env=env, timeout=180)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), digest.hexdigest())

    def test_render_does_not_mutate_the_card_or_the_art(self):
        cards, art = self.cards()
        before_cards, before_art = copy.deepcopy(cards), copy.deepcopy(art)
        card_render.render_single(cards["single"], art, 400)
        card_render.render_battle(cards["battle"], art, 400)
        self.assertEqual(cards, before_cards)
        self.assertEqual(art, before_art)

    # ------------------------------------------------------------- embedding

    def test_art_is_inlined_with_no_external_or_data_reference(self):
        cards, art = self.cards()
        for svg in (card_render.render_single(cards["single"], art, 400),
                    card_render.render_battle(cards["battle"], art, 400)):
            self.assertEqual(lint(svg), [])
            self.assertNotIn("data:", svg)
            self.assertNotIn("http://", svg.replace("http://www.w3.org", ""))
            self.assertNotIn("@import", svg)
            self.assertNotIn("<image", svg)
            self.assertNotIn("<foreignObject", svg)
            fonts = set(re.findall(r'font-family="([^"]+)"', svg))
            self.assertTrue(fonts)
            self.assertTrue(fonts <= {"sans-serif", "serif", "monospace"},
                            "only generic font families may be named: %r" % sorted(fonts))

    def test_two_discs_on_one_battle_plate_do_not_share_ids(self):
        cards, art = self.cards()
        svg = card_render.render_battle(cards["battle"], art, 700)
        ids = ET.fromstring(svg).iter()
        seen = []
        for element in ids:
            value = element.attrib.get("id")
            if value is not None:
                seen.append(value)
        self.assertEqual(len(seen), len(set(seen)), "duplicate ids on one plate: %r" % seen)

    # --------------------------------------------------------------- reuse

    def test_calculations_surface_is_registrable(self):
        self.assertEqual(sorted(card_render.CALCULATIONS),
                         ["fn.card.battle.render", "fn.card.single.render"])
        self.assertIs(card_render.CALCULATIONS["fn.card.single.render"], card_render.render_single)
        self.assertIs(card_render.CALCULATIONS["fn.card.battle.render"], card_render.render_battle)
        for key, fn in card_render.CALCULATIONS.items():
            self.assertNotEqual(fn.__name__, "<lambda>", "%s must not be a lambda" % key)
            self.assertEqual(fn.__code__.co_varnames[:3], ("card", "art", "width"))

    def test_one_art_result_fans_out_to_both_card_renderers(self):
        """fn.discArt.render runs once; both card calculations name it in testimony."""
        cards, _ = self.cards()
        request = Part("input.card.request")
        art_part = Part("px.disc.art.map")
        single_part = Part("px.card.single.svg")
        battle_part = Part("px.card.battle.svg")

        pxc = PxC()
        pxc.set(request, {"family": FAMILY, "base": BASE, "accent": ACCENT,
                          "participants": cards["battle"]["participants"]})

        program = PCR("card-render")
        program.calc("Art", Calculation("fn.discArt.render", render_art_calculation),
                     id="render-art", request=request, into=art_part)
        program.calc("Cards", Calculation("fn.card.single.render", single_calculation),
                     id="single-card", art=art_part,
                     args={"card": cards["single"], "width": 400}, into=single_part)
        program.calc("Cards", Calculation("fn.card.battle.render", battle_calculation),
                     id="battle-card", art=art_part,
                     args={"card": cards["battle"], "width": 400}, into=battle_part)
        run = program.run(pxc)

        consumers = [calculation.id
                     for tick in run.ticks
                     for calculation in tick.calculations
                     if calculation.inputs.get("art") == "fn:render-art"]
        self.assertEqual(consumers, ["single-card", "battle-card"])
        self.assertEqual(run.pcr, "card-render")

        single_svg = pxc.get(single_part)
        battle_svg = pxc.get(battle_part)
        self.assertEqual(lint(single_svg), [])
        self.assertEqual(lint(battle_svg), [])
        art = pxc.get(art_part)
        self.assertEqual(sorted(art), ["active", "rival"])
        self.assertEqual(single_svg, card_render.render_single(cards["single"], art, 400))
        self.assertEqual(battle_svg, card_render.render_battle(cards["battle"], art, 400))
        self.assertEqual(json.loads(json.dumps(sorted(art))), ["active", "rival"])


if __name__ == "__main__":
    unittest.main()
