"""Guards for the consumer's whole disc-art registry.

``art_registry`` publishes every family and every card renderer the art
tournament produced -- the 4 classic families, the 3 promoted, the 9 retained,
and all 8 studio card renderers -- as addressed Calculations. The owner's rule
for this pass is that nothing is deleted and everything is reachable, so these
tests hold the registry to being *complete* and *honest* rather than small:

  * every one of the 16 families renders at 42/96/220 and is deterministic;
  * every render is lint-clean under the tournament's own harness checks,
    imported from ``harness/lint_svg.py`` rather than restated here;
  * a retained family's bytes equal its studio source module's bytes, and a
    classic or promoted family's bytes equal ``paint_components.render``'s --
    so registering a family never forks its implementation;
  * every card renderer draws all four ``harness/fixtures.py`` sample cards;
  * ``register_all`` populates a PxC's Calculation registry and *not* its Part
    store, so no PQL can see a Calculation (``src/pyto/pql.py`` selects over
    produced values only), while a PCR still fans one art result out to a
    studio's Single and Battle renderers;
  * the status counts and the tally attached to each entry match RESULTS.md.

Unlike ``test_paint_families``, this module does reach outside the consumer
directory: it imports the tournament harness and loads the studio sources, on
purpose, because "identical to the source it was copied from" is exactly the
claim being tested. Every such reach is recorded in ``PATH_REACHES`` and
printed, and one test asserts they all stay inside this repository.
"""

import hashlib
import importlib.util
import os
import re
import sys
import unittest
import xml.etree.ElementTree as ET

CONSUMER_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CONSUMER_DIR)

REPO = os.path.dirname(os.path.dirname(os.path.dirname(CONSUMER_DIR)))
TOURNAMENT_DIR = os.path.join(REPO, "pyto", "experiments", "art-tournament")
HARNESS_DIR = os.path.join(TOURNAMENT_DIR, "harness")
STUDIOS_DIR = os.path.join(TOURNAMENT_DIR, "studios")
RESULTS_MD = os.path.join(TOURNAMENT_DIR, "RESULTS.md")

# Every reach outside the consumer directory, logged: (path, how, why).
PATH_REACHES = []


def _log_reach(path, how, why):
    """Record and print one intra-repo reach; refuse anything outside the repo."""
    resolved = os.path.realpath(path)
    if not (resolved == REPO or resolved.startswith(REPO + os.sep)):
        raise RuntimeError("test_art_registry refuses to reach outside %s: %r" % (REPO, resolved))
    PATH_REACHES.append((resolved, how, why))
    print("[test_art_registry] %s %s  (%s)" % (how, os.path.relpath(resolved, REPO), why),
          file=sys.stderr)
    return resolved


# The harness is imported by name, so its directory goes on sys.path.
_log_reach(HARNESS_DIR, "sys.path.insert", "tournament lint checks and card fixtures")
if HARNESS_DIR not in sys.path:
    sys.path.insert(0, HARNESS_DIR)

import fixtures  # noqa: E402  the tournament's shared palettes, seeds and sample cards
import lint_svg  # noqa: E402  the tournament's own SVG hygiene checks

from pyto import Calculation, PCR, PQL, Part, PxC  # noqa: E402

import art_registry  # noqa: E402
import card_render  # noqa: E402
import paint_components  # noqa: E402

COOL = fixtures.PALETTES["cool"]
SEED = 7
LABEL = "warm mako"
WIDTH = 400

CLASSIC_NAMES = {
    "orbit-foundry": "Orbit Foundry",
    "petal-press": "Petal Press",
    "signal-stamp": "Signal Stamp",
    "tessellated-flight": "Tessellated Flight",
}


def _load_studio_families(studio):
    """Load one studio's families.py under a unique module name.

    All four studios name the module `families`, so a bare `import families`
    after a sys.path insert could only ever reach one of them -- and putting
    `studios/` on sys.path would shadow the standard library's `signal` with
    the studio of that name. The file is therefore loaded directly, under a
    per-studio name, and the reach is logged the same way a path insert is.
    """
    path = os.path.join(STUDIOS_DIR, studio, "families.py")
    name = "tournament_%s_families" % studio
    if name in sys.modules:
        return sys.modules[name]
    _log_reach(path, "load_source", "byte-equality check for studio %s" % studio)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _studio_family_function(studio, slug):
    module = _load_studio_families(studio)
    table = getattr(module, "RENDERERS", None) or module.FAMILY_FUNCTIONS
    return table[slug]


def _load_studio_cards(studio):
    """Load one studio's cards.py under a unique module name.

    Two of the four (`cartography`, `signal`) open with `from families import
    ...`, so the studio's own families module is bound to that name for the
    duration of this one import and unbound again straight after -- the same
    dependency the consumer copies resolve by inlining the helper verbatim.
    """
    path = os.path.join(STUDIOS_DIR, studio, "cards.py")
    name = "tournament_%s_cards" % studio
    if name in sys.modules:
        return sys.modules[name]
    _log_reach(path, "load_source", "byte-equality check for studio %s cards" % studio)
    families = _load_studio_families(studio)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    saved = sys.modules.get("families")
    sys.modules["families"] = families
    try:
        spec.loader.exec_module(module)
    finally:
        if saved is None:
            sys.modules.pop("families", None)
        else:
            sys.modules["families"] = saved
    return module


def _by_slug(entry):
    """Sort key for a FamilyEntry -- named, so this module has no anonymous ones either."""
    return entry.slug


def lint(svg_text):
    """Tournament hygiene failures for one SVG document; empty means clean."""
    return lint_svg.lint_bytes(svg_text.encode("utf-8"), "<registry render>")


def sample_art():
    """presentationId -> a 220px disc-art SVG, covering every sample card."""
    out = {}
    for card in fixtures.SAMPLE_CARDS.values():
        for index, participant in enumerate(card["participants"]):
            pid = participant["presentationId"]
            if pid not in out:
                out[pid] = paint_components.render(
                    "pressed-fern", SEED + 5 * index, COOL[0], COOL[1], 220,
                    participant.get("name", "disc"))
    return out


# ------------------------------------------------------------ PCR adapters
#
# PCR hands a Calculation one mapping of arguments, so these three module-level
# functions adapt that shape onto the registry's positional render signatures.
# They are what the fan-out test registers; the registry's own Calculations
# keep the plain signatures a caller uses directly.

def render_art_calculation(args):
    """fn.discArt.render -- one art result, shared by both card renderers."""
    request = args["request"]
    out = {}
    for index, participant in enumerate(request["participants"]):
        out[participant["presentationId"]] = art_registry.family_render(
            request["family"], SEED + 5 * index, request["base"], request["accent"], 220,
            participant.get("name", "disc"))
    return out


def render_single_calculation(args):
    entry = art_registry.card_renderer("single", args["studio"])
    return entry.render(args["card"], args["art"], args["width"])


def render_battle_calculation(args):
    entry = art_registry.card_renderer("battle", args["studio"])
    return entry.render(args["card"], args["art"], args["width"])


class EveryFamilyRendersTest(unittest.TestCase):
    def test_all_sixteen_families_render_at_every_target_and_are_deterministic(self):
        self.assertEqual(len(art_registry.ALL_FAMILIES), 16)
        for slug, entry in sorted(art_registry.ALL_FAMILIES.items()):
            for target in paint_components.TARGETS:
                with self.subTest(slug=slug, target=target):
                    first = entry.render(SEED, COOL[0], COOL[1], target, LABEL)
                    second = entry.render(SEED, COOL[0], COOL[1], target, LABEL)
                    self.assertEqual(first, second, "%s/%d is not deterministic" % (slug, target))
                    root = ET.fromstring(first)
                    self.assertEqual(root.attrib["width"], str(target))
                    self.assertEqual(root.attrib["height"], str(target))
                    self.assertEqual(root.attrib["viewBox"], "0 0 512 512")
                    self.assertTrue(root.attrib.get("aria-label"))

    def test_every_family_render_is_lint_clean_under_the_harness_checks(self):
        for slug, entry in sorted(art_registry.ALL_FAMILIES.items()):
            for target in paint_components.TARGETS:
                with self.subTest(slug=slug, target=target):
                    svg = entry.render(SEED, COOL[0], COOL[1], target, LABEL)
                    self.assertEqual(lint(svg), [])

    def test_family_render_entry_point_agrees_with_every_entry(self):
        for slug, entry in sorted(art_registry.ALL_FAMILIES.items()):
            with self.subTest(slug=slug):
                self.assertEqual(art_registry.family_render(slug, SEED, COOL[0], COOL[1], 96, LABEL),
                                 entry.render(SEED, COOL[0], COOL[1], 96, LABEL))
        with self.assertRaises(ValueError):
            art_registry.family_render("no-such-family", SEED, COOL[0], COOL[1], 42, LABEL)


class RegisteredCodeIsTheSourceCodeTest(unittest.TestCase):
    """A registered family must not be a fork of the code it came from."""

    def test_retained_families_render_exactly_as_their_studio_source_does(self):
        retained = [entry for entry in art_registry.ALL_FAMILIES.values()
                    if entry.status == "retained"]
        self.assertEqual(len(retained), 9)
        for entry in sorted(retained, key=_by_slug):
            source = _studio_family_function(entry.studio, entry.slug)
            for target in paint_components.TARGETS:
                with self.subTest(slug=entry.slug, target=target):
                    self.assertEqual(
                        entry.render(SEED, COOL[0], COOL[1], target, LABEL),
                        source(SEED, COOL[0], COOL[1], target, LABEL),
                        "%s drifted from studios/%s/families.py" % (entry.slug, entry.studio))

    def test_promoted_families_render_exactly_as_paint_components_does(self):
        promoted = sorted(entry.slug for entry in art_registry.ALL_FAMILIES.values()
                          if entry.status == "promoted")
        self.assertEqual(promoted, ["nodding-seedhead", "pressed-fern", "wind-rose"])
        self.assertEqual(tuple(promoted), tuple(sorted(paint_components.PROMOTED_FAMILIES)))
        for slug in promoted:
            entry = art_registry.ALL_FAMILIES[slug]
            for target in paint_components.TARGETS:
                with self.subTest(slug=slug, target=target):
                    self.assertEqual(
                        entry.render(SEED, COOL[0], COOL[1], target, LABEL),
                        paint_components.render(slug, SEED, COOL[0], COOL[1], target, LABEL))

    def test_promoted_families_are_the_promoted_function_not_a_second_copy(self):
        import paint_families
        for slug in ("pressed-fern", "nodding-seedhead", "wind-rose"):
            with self.subTest(slug=slug):
                self.assertIs(art_registry.ALL_FAMILIES[slug].render,
                              paint_families.RENDERERS[slug])

    def test_classic_families_render_exactly_as_paint_components_does(self):
        classic = sorted(entry.slug for entry in art_registry.ALL_FAMILIES.values()
                         if entry.status == "classic")
        self.assertEqual(classic, sorted(CLASSIC_NAMES))
        for slug in classic:
            entry = art_registry.ALL_FAMILIES[slug]
            for target in paint_components.TARGETS:
                with self.subTest(slug=slug, target=target):
                    self.assertEqual(
                        entry.render(SEED, COOL[0], COOL[1], target, LABEL),
                        paint_components.render(CLASSIC_NAMES[slug], SEED, COOL[0], COOL[1],
                                                target, LABEL))

    def test_every_paint_components_family_is_addressable_here(self):
        addressed = set()
        for entry in art_registry.ALL_FAMILIES.values():
            addressed.add(CLASSIC_NAMES.get(entry.slug, entry.slug))
        self.assertTrue(set(paint_components.FAMILIES) <= addressed)


class EveryCardRendererDrawsTest(unittest.TestCase):
    def test_all_eight_renderers_draw_the_four_sample_cards_at_400(self):
        art = sample_art()
        drawn = 0
        for kind in ("single", "battle"):
            for studio, entry in sorted(art_registry.CARD_RENDERERS[kind].items()):
                for key, card in sorted(fixtures.SAMPLE_CARDS.items()):
                    if not key.startswith(kind):
                        continue
                    with self.subTest(kind=kind, studio=studio, card=key):
                        svg = entry.render(card, art, WIDTH)
                        self.assertEqual(lint(svg), [])
                        root = ET.fromstring(svg)
                        self.assertEqual(root.attrib["width"], str(WIDTH))
                        self.assertIn("viewBox", root.attrib)
                        self.assertEqual(svg, entry.render(card, art, WIDTH))
                        drawn += 1
        # 4 studios x 2 kinds x 2 layouts of that kind
        self.assertEqual(drawn, 16)

    def test_every_renderer_draws_exactly_what_its_studio_source_draws(self):
        """The copies beside this module must not have forked from the studios.

        _card_cartography.py is the only one carrying an edit -- the colour
        helper its studio imported from families.py, inlined verbatim, the same
        edit RESULTS.md section 3 records for the promoted _card_signal.py --
        so this is where that edit is proved to be behaviour-free.
        """
        art = sample_art()
        checked = 0
        for kind in ("single", "battle"):
            for studio, entry in sorted(art_registry.CARD_RENDERERS[kind].items()):
                source = getattr(_load_studio_cards(studio), "render_" + kind)
                for key, card in sorted(fixtures.SAMPLE_CARDS.items()):
                    if not key.startswith(kind):
                        continue
                    with self.subTest(kind=kind, studio=studio, card=key):
                        self.assertEqual(
                            entry.render(card, art, WIDTH), source(card, art, WIDTH),
                            "%s/%s drifted from studios/%s/cards.py" % (kind, studio, studio))
                        checked += 1
        self.assertEqual(checked, 16)

    def test_the_promoted_pair_is_card_render_itself_not_a_copy(self):
        self.assertIs(art_registry.CARD_RENDERERS["single"]["botanical"].render,
                      card_render.render_single)
        self.assertIs(art_registry.CARD_RENDERERS["battle"]["signal"].render,
                      card_render.render_battle)
        for address, function in card_render.CALCULATIONS.items():
            with self.subTest(address=address):
                self.assertIs(art_registry.CALCULATIONS[address].calculate, function)

    def test_retained_renderers_are_registered_under_a_studio_suffixed_address(self):
        for kind in ("single", "battle"):
            for studio, entry in art_registry.CARD_RENDERERS[kind].items():
                with self.subTest(kind=kind, studio=studio):
                    self.assertEqual(entry.calculation.address,
                                     "fn.card.%s.render.%s" % (kind, studio))


class RegistrationTest(unittest.TestCase):
    def test_register_all_puts_all_twenty_six_addresses_on_a_fresh_pxc(self):
        pxc = PxC()
        addresses = art_registry.register_all(pxc)
        self.assertEqual(len(addresses), 26)
        self.assertEqual(addresses, tuple(sorted(art_registry.CALCULATIONS)))
        self.assertEqual(len([a for a in addresses if a.startswith("fn.discArt.")]), 16)
        self.assertEqual(len([a for a in addresses if a.startswith("fn.card.")]), 10)
        # Registering twice is not a conflict: same address, same function.
        self.assertEqual(art_registry.register_all(pxc), addresses)

    def test_pql_cannot_see_a_single_registered_calculation(self):
        pxc = PxC()
        art_registry.register_all(pxc)
        self.assertEqual(pxc.addresses(), ())
        self.assertEqual(PQL.prefix("fn.").matches(pxc), ())
        self.assertEqual(PQL.prefix("fn.discArt.").values(pxc), ())
        for address in art_registry.CALCULATIONS:
            with self.subTest(address=address):
                self.assertFalse(pxc.has(address))
                self.assertEqual(PQL.part(address).matches(pxc), ())
                self.assertIsNone(PQL.part(address).optional(pxc))
        # A Part named like a Calculation is still just a Part.
        pxc.set(Part("px.card.single.svg"), "<svg/>")
        self.assertEqual(PQL.prefix("px.").values(pxc), ("<svg/>",))
        self.assertEqual(PQL.prefix("fn.").matches(pxc), ())

    def test_one_art_result_fans_out_to_each_studios_single_and_battle(self):
        cards = fixtures.SAMPLE_CARDS
        battle = cards["battle_standard"]
        single = cards["single_standard"]
        for studio in sorted(art_registry.CARD_RENDERERS["single"]):
            with self.subTest(studio=studio):
                request = Part("input.card.request")
                art_part = Part("px.disc.art.map")
                single_part = Part("px.card.single.svg")
                battle_part = Part("px.card.battle.svg")

                pxc = PxC()
                pxc.set(request, {"family": "wind-rose", "base": COOL[0], "accent": COOL[1],
                                  "participants": battle["participants"]})

                program = PCR("art-registry-fan-out-%s" % studio)
                program.calc("Art", Calculation("fn.discArt.render", render_art_calculation),
                             id="render-art", request=request, into=art_part)
                program.calc("Cards",
                             Calculation("fn.card.single.render.%s" % studio,
                                         render_single_calculation),
                             id="single-card", art=art_part,
                             args={"card": single, "width": WIDTH, "studio": studio},
                             into=single_part)
                program.calc("Cards",
                             Calculation("fn.card.battle.render.%s" % studio,
                                         render_battle_calculation),
                             id="battle-card", art=art_part,
                             args={"card": battle, "width": WIDTH, "studio": studio},
                             into=battle_part)
                run = program.run(pxc)

                consumers = [calculation.id
                             for tick in run.ticks
                             for calculation in tick.calculations
                             if calculation.inputs.get("art") == "fn:render-art"]
                self.assertEqual(consumers, ["single-card", "battle-card"])

                art = pxc.get(art_part)
                self.assertEqual(sorted(art), ["active", "rival"])
                self.assertEqual(lint(pxc.get(single_part)), [])
                self.assertEqual(lint(pxc.get(battle_part)), [])
                self.assertEqual(
                    pxc.get(single_part),
                    art_registry.CARD_RENDERERS["single"][studio].render(single, art, WIDTH))
                self.assertEqual(
                    pxc.get(battle_part),
                    art_registry.CARD_RENDERERS["battle"][studio].render(battle, art, WIDTH))

    def test_no_anonymous_functions_in_the_registry_module(self):
        with open(os.path.join(CONSUMER_DIR, "art_registry.py"), encoding="utf-8") as handle:
            source = handle.read()
        self.assertNotIn("lambda", source, "art_registry must define no anonymous function")
        for address, calculation in sorted(art_registry.CALCULATIONS.items()):
            with self.subTest(address=address):
                self.assertIsInstance(calculation, Calculation)
                self.assertEqual(calculation.address, address)
                self.assertNotEqual(calculation.calculate.__name__, "<lambda>")
                self.assertTrue(calculation.calculate.__module__)


class ProvenanceTest(unittest.TestCase):
    ROW = re.compile(
        r"^\|\s*(\d+)\s*\|\s*(\w+)\s*\|\s*(\w+)\s*\|\s*`([^`]+)`\s*\|"
        r"\s*(\d+) \+ (\d+) \+ (\d+)\s*\|\s*\*\*(\d+)\*\*\s*\|\s*(.+?)\s*\|\s*$")

    def results_rows(self):
        _log_reach(RESULTS_MD, "read", "the judge tally attached to every entry")
        rows = {}
        with open(RESULTS_MD, encoding="utf-8") as handle:
            lines = handle.read().splitlines()
        for line in lines:
            match = self.ROW.match(line)
            if not match:
                continue
            rank, kind, studio, item, j1, j2, j3, total, outcome = match.groups()
            rows["%s:%s/%s" % (kind, studio, item)] = (
                int(rank), (int(j1), int(j2), int(j3)), int(total),
                outcome.strip("*").lower())
        return rows

    def test_every_tally_matches_results_md_section_one(self):
        rows = self.results_rows()
        self.assertEqual(len(rows), 20)
        self.assertEqual(sorted(rows), sorted(art_registry.TALLIES))
        for key, (rank, judges, total, outcome) in sorted(rows.items()):
            tally = art_registry.TALLIES[key]
            with self.subTest(key=key):
                self.assertEqual((tally.rank, tally.judges, tally.total, tally.outcome),
                                 (rank, judges, total, outcome))
                self.assertEqual(tally.ceiling, 72)
                self.assertEqual(sum(tally.judges), tally.total)

    def test_every_scored_entry_carries_its_tally_and_the_classic_four_do_not(self):
        for slug, entry in sorted(art_registry.ALL_FAMILIES.items()):
            with self.subTest(slug=slug):
                if entry.status == "classic":
                    self.assertIsNone(entry.tally)
                else:
                    self.assertIsNotNone(entry.tally)
                    self.assertEqual(entry.tally.outcome, entry.status)
                    self.assertEqual(
                        art_registry.TALLIES["family:%s/%s" % (entry.studio, slug)], entry.tally)
        for kind in ("single", "battle"):
            for studio, entry in sorted(art_registry.CARD_RENDERERS[kind].items()):
                with self.subTest(kind=kind, studio=studio):
                    self.assertEqual(entry.tally.outcome, entry.status)
                    self.assertEqual(entry.tally,
                                     art_registry.TALLIES["%s:%s/render_%s" % (kind, studio, kind)])

    def test_status_counts_are_four_classic_three_and_two_promoted_nine_and_six_retained(self):
        self.assertEqual(art_registry.STATUS_COUNTS,
                         {"families": {"classic": 4, "promoted": 3, "retained": 9},
                          "cards": {"promoted": 2, "retained": 6}})
        self.assertEqual(sum(art_registry.STATUS_COUNTS["families"].values()), 16)
        self.assertEqual(sum(art_registry.STATUS_COUNTS["cards"].values()), 8)

    def test_every_evidence_path_points_at_a_file_that_still_exists(self):
        seen = 0
        for entry in art_registry.ALL_FAMILIES.values():
            self.assertTrue(entry.evidence)
            for relative in entry.evidence:
                with self.subTest(slug=entry.slug, evidence=relative):
                    path = os.path.join(TOURNAMENT_DIR, relative)
                    self.assertTrue(os.path.isfile(path), "missing evidence: %s" % relative)
                    seen += 1
        for kind in ("single", "battle"):
            for entry in art_registry.CARD_RENDERERS[kind].values():
                for relative in entry.evidence:
                    with self.subTest(kind=kind, studio=entry.studio, evidence=relative):
                        path = os.path.join(TOURNAMENT_DIR, relative)
                        self.assertTrue(os.path.isfile(path), "missing evidence: %s" % relative)
                        seen += 1
        self.assertEqual(seen, 4 * 4 + 12 * 2 + 8 * 3)

    def test_every_entry_carries_a_params_document(self):
        for slug, entry in sorted(art_registry.ALL_FAMILIES.items()):
            with self.subTest(slug=slug):
                for key in ("name", "seed", "base", "accent", "label"):
                    self.assertTrue(entry.params.get(key), "%s params lack %s" % (slug, key))
                self.assertTrue(entry.params.get("target") or entry.params.get("targets"),
                                "%s params lack a per-target note" % slug)
                self.assertEqual(entry.name, entry.params["name"])

    def test_the_promotion_policy_is_recorded_as_reversible(self):
        self.assertIn("reversible", art_registry.PROMOTION_POLICY)
        self.assertIn("not a stability claim", art_registry.PROMOTION_POLICY)
        self.assertIn("RESULTS.md", art_registry.PROMOTION_POLICY)

    def test_every_reach_outside_the_consumer_stays_inside_the_repository(self):
        self.assertTrue(PATH_REACHES)
        for path, how, why in PATH_REACHES:
            with self.subTest(path=path):
                self.assertTrue(path.startswith(REPO + os.sep), path)
                self.assertIn(how, ("sys.path.insert", "load_source", "read"))
                self.assertTrue(why)
        self.assertIn(os.path.realpath(HARNESS_DIR), [path for path, _, _ in PATH_REACHES])

    def test_the_frozen_classic_bytes_are_untouched_by_this_registry(self):
        """The registry must not have moved a byte of the four originals."""
        from test_paint_families import FROZEN_CLASSIC
        for (family, target), expected in sorted(FROZEN_CLASSIC.items()):
            slug = [s for s, name in CLASSIC_NAMES.items() if name == family][0]
            with self.subTest(family=family, target=target):
                svg = art_registry.ALL_FAMILIES[slug].render(7, "#4c9bc6", "#0d3558", target,
                                                             "warm mako")
                self.assertEqual(hashlib.sha256(svg.encode("utf-8")).hexdigest(), expected)


if __name__ == "__main__":
    unittest.main()
