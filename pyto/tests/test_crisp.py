"""Executable spec of crisp (task 74): template gen required to import into
PxC-ore, tunable to imply or force decomposition; variation through PxC.
"""

from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import tempfile
import unittest

PYTO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.dirname(os.path.abspath(__file__))
if TESTS not in sys.path:
    print(f"[tests/test_crisp] sys.path.insert(0, {TESTS!r})", file=sys.stderr)
    sys.path.insert(0, TESTS)
if PYTO_ROOT not in sys.path:
    print(f"[tests/test_crisp] sys.path.insert(0, {PYTO_ROOT!r})", file=sys.stderr)
    sys.path.insert(0, PYTO_ROOT)

SRC = os.path.join(PYTO_ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from pyto.crisp import (  # noqa: E402
    CrispRefusal,
    _address_for,
    _binding_options,
    _calculation_options,
    _check_pins,
    _digest_of,
    add_digests,
    build_astar_proposal,
    build_pql_proposal,
    build_skeleton_proposal,
    find_slot,
    is_part,
)

VIEWER_TEST_DIR = os.path.join(PYTO_ROOT, "viewer", "test")
if VIEWER_TEST_DIR not in sys.path:
    print(f"[tests/test_crisp] sys.path.insert(0, {VIEWER_TEST_DIR!r})", file=sys.stderr)
    sys.path.insert(0, VIEWER_TEST_DIR)

from record_schema import validate as validate_record  # noqa: E402

from tests.fixtures.crisp.registry import REGISTRY  # noqa: E402

FIXTURES = os.path.join(TESTS, "fixtures", "crisp")
STORE_PATH = os.path.join(FIXTURES, "store.json")
ROOT_PQL_PATH = os.path.join(FIXTURES, "root.pql.json")
ASTAR_PATH = os.path.join(FIXTURES, "astar-blok.json")
REGISTRY_SPEC = "tests.fixtures.crisp.registry:REGISTRY"
NEAT_SH = os.path.join(PYTO_ROOT, "scripts", "neat.sh")

SENTENCE = "Derive the coordinates for the anchor swatch."


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_store():
    return load_json(STORE_PATH)


def load_root_pql():
    return load_json(ROOT_PQL_PATH)


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "pyto.crisp", *args],
        cwd=PYTO_ROOT,
        capture_output=True,
        text=True,
    )


# --------------------------------------------------------------------------- (a) skeleton, imply mode


class TestSkeletonImplyMode(unittest.TestCase):
    def setUp(self):
        self.store = load_store()

    def build(self):
        return build_skeleton_proposal(SENTENCE, self.store, REGISTRY, "blok", "imply")

    def test_names_existing_parts_and_calculations(self):
        value = self.build()
        self.assertEqual([p["address"] for p in value["existingParts"]], ["px.color.swatch.anchor"])
        self.assertEqual(
            [c["address"] for c in value["existingCalculations"]], ["fn.colorStudy.coordinates"]
        )
        self.assertEqual(value["proposedParts"], [])
        self.assertEqual(value["proposedCalculations"], [])
        self.assertEqual(value["capabilityDelta"], SENTENCE)

    def test_pql_has_one_tick_named_after_the_set_with_the_binding_filled(self):
        value = self.build()
        ticks = value["PQL"]["Ticks"]
        self.assertEqual(len(ticks), 1)
        self.assertEqual(ticks[0]["name"], "blok")
        calcs = ticks[0]["Calculations"]
        self.assertEqual(len(calcs), 1)
        self.assertEqual(calcs[0]["call"], "fn.colorStudy.coordinates")
        self.assertEqual(calcs[0]["with"], {"hex": "px.color.swatch.anchor"})

    def test_prose_fields_carry_a_slot_placeholder(self):
        value = self.build()
        for field in ("inspection", "verification", "decisions", "limits"):
            self.assertEqual(len(value[field]), 1)
            self.assertIn("{?}", value[field][0])
            self.assertTrue(value[field][0].startswith("{?} "))

    def test_same_inputs_same_bytes(self):
        first = self.build()
        second = self.build()
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )

    def test_address_carries_the_digest(self):
        value = self.build()
        address, digest = _address_for("blok", "root", value)
        self.assertTrue(address.startswith("proposal.neat.composition.blok.root."))
        self.assertTrue(address.endswith(digest[:12]))
        self.assertEqual(len(digest), 64)

    def test_sentence_naming_nothing_yields_an_empty_but_valid_skeleton(self):
        value = build_skeleton_proposal("a sentence about nothing here", self.store, REGISTRY, "blok", "imply")
        self.assertEqual(value["existingParts"], [])
        self.assertEqual(value["existingCalculations"], [])
        self.assertEqual(value["PQL"]["Ticks"][0]["Calculations"], [])


# --------------------------------------------------------------------------- (b) force mode


class TestForceMode(unittest.TestCase):
    def setUp(self):
        self.store = load_store()
        self.root = load_root_pql()

    def test_accepts_the_blok_root_document(self):
        value = build_pql_proposal(SENTENCE, self.root, self.store, REGISTRY, "force")
        self.assertEqual([p["address"] for p in value["existingParts"]], ["px.color.swatch.anchor"])
        self.assertEqual(
            [c["address"] for c in value["existingCalculations"]], ["fn.colorStudy.coordinates"]
        )
        self.assertEqual(value["proposedParts"], [])
        self.assertEqual(value["proposedCalculations"], [])
        self.assertIsNone(find_slot(value))

    def test_skeleton_without_pql_is_refused_in_force_mode(self):
        with self.assertRaises(CrispRefusal):
            build_skeleton_proposal(SENTENCE, self.store, REGISTRY, "blok", "force")

    def test_refuses_an_unknown_part_by_name(self):
        doc = {
            "Ticks": [
                {
                    "name": "T",
                    "Calculations": [
                        {
                            "call": "fn.colorStudy.coordinates",
                            "with": {"hex": "px.color.swatch.nonexistent"},
                            "args": {},
                            "into": ["a", "b"],
                        }
                    ],
                }
            ]
        }
        with self.assertRaises(CrispRefusal) as caught:
            build_pql_proposal(SENTENCE, doc, self.store, REGISTRY, "force")
        self.assertIn("px.color.swatch.nonexistent", str(caught.exception))

    def test_refuses_a_backwards_read(self):
        doc = {
            "Ticks": [
                {
                    "name": "T",
                    "Calculations": [
                        {
                            "call": "fn.colorStudy.coordinates",
                            "with": {"hex": "px.later.thing"},
                            "args": {},
                            "into": ["a", "b"],
                        },
                        {
                            "call": "fn.colorStudy.luma",
                            "with": {"hex": "px.color.swatch.anchor"},
                            "args": {},
                            "into": "px.later.thing",
                        },
                    ],
                }
            ]
        }
        with self.assertRaises(CrispRefusal) as caught:
            build_pql_proposal(SENTENCE, doc, self.store, REGISTRY, "force")
        self.assertIn("chain rule", str(caught.exception))
        self.assertIn("px.later.thing", str(caught.exception))

    def test_refuses_a_call_not_in_the_registry(self):
        doc = {
            "Ticks": [
                {"name": "T", "Calculations": [{"call": "fn.nope.thing", "with": {}, "args": {}, "into": "a"}]}
            ]
        }
        with self.assertRaises(CrispRefusal) as caught:
            build_pql_proposal(SENTENCE, doc, self.store, REGISTRY, "force")
        self.assertIn("fn.nope.thing", str(caught.exception))

    def test_refuses_a_proposal_with_a_slot_left(self):
        doc = {
            "Ticks": [
                {
                    "name": "T",
                    "Calculations": [
                        {
                            "call": "fn.colorStudy.coordinates",
                            "with": {"hex": "px.color.swatch.anchor"},
                            "args": {"threshold": "{?}"},
                            "into": ["a", "b"],
                        }
                    ],
                }
            ]
        }
        with self.assertRaises(CrispRefusal) as caught:
            build_pql_proposal(SENTENCE, doc, self.store, REGISTRY, "force")
        self.assertIn("unresolved slot", str(caught.exception))


# --------------------------------------------------------------------------- (c) vary


class TestVary(unittest.TestCase):
    def setUp(self):
        self.store = load_store()
        self.root = load_root_pql()
        self.value = build_pql_proposal(SENTENCE, self.root, self.store, REGISTRY, "force")
        self.pql = self.value["PQL"]

    def test_binding_options_are_exactly_paper_and_ink(self):
        candidates = sorted(candidate for candidate, _change, _mutated, _address in _binding_options(self.pql, self.store))
        self.assertEqual(candidates, ["px.color.swatch.ink", "px.color.swatch.paper"])

    def test_canvas_width_is_not_a_binding_option(self):
        candidates = [candidate for candidate, _change, _mutated, _address in _binding_options(self.pql, self.store)]
        self.assertNotIn("px.canvas.width", candidates)

    def test_calculation_options_are_exactly_coordinates_inverted(self):
        candidates = [
            candidate for candidate, _change, _mutated in _calculation_options(self.pql, REGISTRY, self.store)
        ]
        self.assertEqual(candidates, ["fn.colorStudy.coordinatesInverted"])
        self.assertNotIn("fn.colorStudy.luma", candidates)


class TestVaryCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _template(self, out_dir):
        result = run_cli(
            "template", SENTENCE,
            "--store", STORE_PATH, "--registry", REGISTRY_SPEC,
            "--set", "blok", "--mode", "force", "--pql", ROOT_PQL_PATH,
            "--out", out_dir,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        address = result.stdout.splitlines()[0].removeprefix("address: ")
        digest = address.rsplit(".", 1)[-1]
        path = os.path.join(out_dir, f"blok.root.{digest}.json")
        return address, path, load_json(path)["sha256"]

    def test_vary_gives_exactly_the_three_options_byte_stable_and_new_digests(self):
        _address, proposal_path, root_digest = self._template(self.tmp.name)

        first = run_cli("vary", proposal_path, "--store", STORE_PATH, "--registry", REGISTRY_SPEC)
        self.assertEqual(first.returncode, 0, first.stderr)
        lines = first.stdout.splitlines()
        self.assertEqual(len(lines), 3)
        slugs = [line.split()[0].rsplit(".", 2)[-2] for line in lines]
        self.assertEqual(slugs, ["a1-ink", "a2-paper", "b1-coordinatesInverted"])
        for line in lines:
            digest = line.rsplit("digest=", 1)[-1]
            self.assertNotEqual(digest, root_digest)
            self.assertEqual(len(digest), 64)

        second = run_cli("vary", proposal_path, "--store", STORE_PATH, "--registry", REGISTRY_SPEC)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first.stdout, second.stdout)

    def test_max_caps_the_count_and_says_how_many_were_cut(self):
        _address, proposal_path, _digest = self._template(self.tmp.name)
        result = run_cli(
            "vary", proposal_path, "--store", STORE_PATH, "--registry", REGISTRY_SPEC, "--max", "1"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("cut", lines[-1])
        self.assertIn("2", lines[-1])


# --------------------------------------------------------------------------- (d) import


class TestImportCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _template(self, mode, out_dir, pql=None):
        args = [
            "template", SENTENCE,
            "--store", STORE_PATH, "--registry", REGISTRY_SPEC,
            "--set", "blok", "--mode", mode, "--out", out_dir,
        ]
        if pql:
            args += ["--pql", pql]
        result = run_cli(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        address = result.stdout.splitlines()[0].removeprefix("address: ")
        digest = address.rsplit(".", 1)[-1]
        return os.path.join(out_dir, f"blok.root.{digest}.json")

    def test_import_runs_the_root_proposal_and_writes_rgb_and_hsl(self):
        proposal_path = self._template("force", self.tmp.name, pql=ROOT_PQL_PATH)
        run_path = os.path.join(self.tmp.name, "run.json")

        result = run_cli(
            "import", proposal_path, "--store", STORE_PATH, "--registry", REGISTRY_SPEC, "--out", run_path
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        record = load_json(run_path)
        validate_record(record)

        store_after_path = os.path.join(self.tmp.name, "store-after.json")
        store_after = load_json(store_after_path)
        self.assertEqual(
            set(store_after), {"px.exp.astar.blok.color.rgb", "px.exp.astar.blok.color.hsl"}
        )
        for entry in store_after.values():
            self.assertIn("value", entry)
            self.assertEqual(len(entry["sha256"]), 64)

    def test_refuses_an_imply_mode_proposal_with_a_slot(self):
        proposal_path = self._template("imply", self.tmp.name)
        run_path = os.path.join(self.tmp.name, "run.json")

        result = run_cli(
            "import", proposal_path, "--store", STORE_PATH, "--registry", REGISTRY_SPEC, "--out", run_path
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("crisp:", result.stderr)
        self.assertFalse(os.path.exists(run_path))


# --------------------------------------------------------------------------- (e) neat.sh forwarding


class TestNeatShForwarding(unittest.TestCase):
    def test_neat_crisp_template_prints_the_address(self):
        with tempfile.TemporaryDirectory() as out_dir:
            result = subprocess.run(
                [
                    "bash", NEAT_SH, "crisp", "template", SENTENCE,
                    "--store", STORE_PATH, "--registry", REGISTRY_SPEC,
                    "--set", "blok", "--mode", "imply", "--out", out_dir,
                ],
                cwd=PYTO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            first_line = result.stdout.splitlines()[0]
            self.assertTrue(first_line.startswith("address: proposal.neat.composition.blok.root."))


# --------------------------------------------------------------------------- (f) pnc and review


class TestPncAndReview(unittest.TestCase):
    """Task 75 item 1: pnc is Parts and Calculations only; review is the whole
    value. A label lives inside PQL (the raw document's own "labels" list, as
    the fixtures already carry) so it is part of review and no part of pnc."""

    def setUp(self):
        self.store = load_store()
        self.root = load_root_pql()

    def build(self, document=None):
        return build_pql_proposal(SENTENCE, document or self.root, self.store, REGISTRY, "force")

    def test_pnc_and_review_are_both_present_and_different(self):
        value = self.build()
        self.assertEqual(len(value["pnc"]), 64)
        self.assertEqual(len(value["review"]), 64)
        self.assertNotEqual(value["pnc"], value["review"])

    def test_a_label_changes_review_and_never_pnc(self):
        first = self.build()
        labelled = json.loads(json.dumps(self.root))
        labelled["labels"] = list(labelled.get("labels") or []) + ["a second label"]
        second = self.build(labelled)
        self.assertEqual(first["pnc"], second["pnc"])
        self.assertNotEqual(first["review"], second["review"])

    def test_removing_a_label_changes_review_and_never_pnc(self):
        first = self.build()
        unlabelled = json.loads(json.dumps(self.root))
        unlabelled["labels"] = []
        second = self.build(unlabelled)
        self.assertEqual(first["pnc"], second["pnc"])
        self.assertNotEqual(first["review"], second["review"])

    def test_changing_one_binding_changes_both(self):
        first = self.build()
        rebound = json.loads(json.dumps(self.root))
        rebound["Ticks"][0]["Calculations"][0]["with"]["hex"] = "px.color.swatch.paper"
        second = self.build(rebound)
        self.assertNotEqual(first["pnc"], second["pnc"])
        self.assertNotEqual(first["review"], second["review"])

    def test_add_digests_is_idempotent(self):
        value = self.build()
        pnc, review = value["pnc"], value["review"]
        add_digests(value)
        self.assertEqual((pnc, review), (value["pnc"], value["review"]))

    def test_the_address_revision_is_the_first_12_hex_of_review(self):
        value = self.build()
        address, digest = _address_for("blok", "root", value)
        self.assertEqual(digest, value["review"])
        self.assertTrue(address.endswith(value["review"][:12]))


# --------------------------------------------------------------------------- (g) live and pinned bindings


class TestPinnedBindings(unittest.TestCase):
    def setUp(self):
        self.store = load_store()
        self.root = load_root_pql()
        self.anchor_digest = _digest_of(self.store["px.color.swatch.anchor"])

    def _pinned_document(self, sha256):
        document = json.loads(json.dumps(self.root))
        document["Ticks"][0]["Calculations"][0]["with"]["hex"] = {
            "address": "px.color.swatch.anchor", "sha256": sha256,
        }
        return document

    def test_template_and_force_accept_a_pinned_binding_and_keep_pql_plain(self):
        document = self._pinned_document(self.anchor_digest)
        value = build_pql_proposal(SENTENCE, document, self.store, REGISTRY, "force")
        self.assertEqual(
            value["PQL"]["Ticks"][0]["Calculations"][0]["with"]["hex"], "px.color.swatch.anchor"
        )
        self.assertEqual(value["pins"], {"px.color.swatch.anchor": self.anchor_digest})

    def test_check_pins_refuses_a_wrong_digest_by_name(self):
        with self.assertRaises(CrispRefusal) as caught:
            _check_pins({"px.color.swatch.anchor": "f" * 64}, self.store)
        message = str(caught.exception)
        self.assertIn("px.color.swatch.anchor", message)
        self.assertIn("expected", message)
        self.assertIn("got", message)

    def test_check_pins_accepts_a_short_prefix(self):
        _check_pins({"px.color.swatch.anchor": self.anchor_digest[:12]}, self.store)  # no raise

    def test_force_mode_accepts_a_wrong_pin_verification_is_import_s_job(self):
        """Template only has to carry the pin forward; `crisp import` is the door
        that checks it (task 75 item 3)."""
        document = self._pinned_document("f" * 64)
        value = build_pql_proposal(SENTENCE, document, self.store, REGISTRY, "force")
        self.assertEqual(value["pins"], {"px.color.swatch.anchor": "f" * 64})


class TestPinnedBindingCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = load_store()
        self.anchor_digest = _digest_of(self.store["px.color.swatch.anchor"])

    def _pinned_pql_path(self, sha256, name="pinned.pql.json"):
        document = load_root_pql()
        document["Ticks"][0]["Calculations"][0]["with"]["hex"] = {
            "address": "px.color.swatch.anchor", "sha256": sha256,
        }
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(document, handle)
        return path

    def _template(self, pql_path):
        result = run_cli(
            "template", SENTENCE, "--store", STORE_PATH, "--registry", REGISTRY_SPEC,
            "--set", "blok", "--mode", "force", "--pql", pql_path, "--out", self.tmp.name,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return glob.glob(os.path.join(self.tmp.name, "blok.root.*.json"))[-1]

    def test_import_succeeds_with_the_right_pin(self):
        proposal_path = self._template(self._pinned_pql_path(self.anchor_digest))
        run_path = os.path.join(self.tmp.name, "run.json")
        imported = run_cli(
            "import", proposal_path, "--store", STORE_PATH, "--registry", REGISTRY_SPEC, "--out", run_path
        )
        self.assertEqual(imported.returncode, 0, imported.stderr)

    def test_import_refuses_by_name_with_the_wrong_pin(self):
        proposal_path = self._template(self._pinned_pql_path("f" * 64, name="bad.pql.json"))
        run_path = os.path.join(self.tmp.name, "run2.json")
        refused = run_cli(
            "import", proposal_path, "--store", STORE_PATH, "--registry", REGISTRY_SPEC, "--out", run_path
        )
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("pinned px.color.swatch.anchor", refused.stderr)
        self.assertIn("expected", refused.stderr)
        self.assertFalse(os.path.exists(run_path))

    def test_vary_keeps_a_pinned_binding_pinned_when_it_substitutes_the_address(self):
        proposal_path = self._template(self._pinned_pql_path(self.anchor_digest))
        varied = run_cli(
            "vary", proposal_path, "--store", STORE_PATH, "--registry", REGISTRY_SPEC, "--bindings"
        )
        self.assertEqual(varied.returncode, 0, varied.stderr)
        option_paths = sorted(glob.glob(os.path.join(self.tmp.name, "blok.a*.json")))
        self.assertEqual(len(option_paths), 2)
        for option_path in option_paths:
            option = load_json(option_path)
            pins = option["value"].get("pins")
            self.assertIsNotNone(pins, option_path)
            self.assertEqual(len(pins), 1)
            (pinned_address, pinned_digest), = pins.items()
            self.assertNotEqual(pinned_address, "px.color.swatch.anchor")
            self.assertEqual(pinned_digest, _digest_of(self.store[pinned_address]))


# --------------------------------------------------------------------------- (h) A-Star intake


class TestAstarIntake(unittest.TestCase):
    def setUp(self):
        self.store = load_store()
        self.study = load_json(ASTAR_PATH)["value"]

    def test_imply_mode_writes_known_parts_and_decisions_and_limits(self):
        value = build_astar_proposal(SENTENCE, self.study, self.store, REGISTRY, "blok", "imply")
        self.assertEqual([p["address"] for p in value["existingParts"]], ["px.color.swatch.anchor"])
        self.assertEqual(
            [c["address"] for c in value["existingCalculations"]], ["fn.colorStudy.coordinates"]
        )
        self.assertEqual(value["decisions"], ["{?} which representation the site shows"])
        self.assertEqual(value["limits"], [self.study["return_when"]])
        self.assertNotIn("astar_extra", value)

    def test_force_mode_refuses_while_unresolved_entries_remain(self):
        with self.assertRaises(CrispRefusal) as caught:
            build_astar_proposal(SENTENCE, self.study, self.store, REGISTRY, "blok", "force")
        self.assertIn("unresolved slot", str(caught.exception))

    def test_force_mode_accepts_a_fully_resolved_study(self):
        resolved = dict(self.study, unresolved=[])
        value = build_astar_proposal(SENTENCE, resolved, self.store, REGISTRY, "blok", "force")
        self.assertEqual(value["decisions"], [])
        self.assertIsNone(find_slot(value))

    def test_unknown_fields_are_preserved_under_astar_extra(self):
        study = dict(self.study, notes="something extra")
        value = build_astar_proposal(SENTENCE, study, self.store, REGISTRY, "blok", "imply")
        self.assertEqual(value["astar_extra"], {"notes": "something extra"})


class TestAstarCLI(unittest.TestCase):
    def test_template_astar_imply_writes_a_proposal(self):
        with tempfile.TemporaryDirectory() as out_dir:
            result = run_cli(
                "template", SENTENCE, "--store", STORE_PATH, "--registry", REGISTRY_SPEC,
                "--set", "blok", "--mode", "imply", "--astar", ASTAR_PATH, "--out", out_dir,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('"{?} which representation the site shows"', result.stdout)

    def test_template_astar_force_refuses_while_unresolved(self):
        result = run_cli(
            "template", SENTENCE, "--store", STORE_PATH, "--registry", REGISTRY_SPEC,
            "--set", "blok", "--mode", "force", "--astar", ASTAR_PATH,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("crisp:", result.stderr)


# --------------------------------------------------------------------------- (i) partness propagates


class TestPartBinding(unittest.TestCase):
    def setUp(self):
        self.store = load_store()
        self.root = load_root_pql()

    def test_is_part(self):
        self.assertTrue(is_part("proposal.neat.composition.blok.root.abc"))
        self.assertTrue(is_part("px.exp.astar.blok.color.rgb"))
        self.assertFalse(is_part("px.color.swatch.anchor"))

    def test_force_mode_accepts_a_binding_to_a_part_not_in_the_store(self):
        document = json.loads(json.dumps(self.root))
        part_address = "proposal.neat.composition.blok.root.deadbeefcafe"
        document["Ticks"][0]["Calculations"][0]["with"]["hex"] = part_address
        value = build_pql_proposal(SENTENCE, document, self.store, REGISTRY, "force")
        self.assertEqual(value["basis"], [part_address])
        self.assertTrue(value["provisional"])
        self.assertEqual(value["existingParts"], [])

    def test_force_mode_still_refuses_a_binding_to_neither_store_nor_a_part(self):
        document = json.loads(json.dumps(self.root))
        document["Ticks"][0]["Calculations"][0]["with"]["hex"] = "px.color.swatch.nonexistent"
        with self.assertRaises(CrispRefusal):
            build_pql_proposal(SENTENCE, document, self.store, REGISTRY, "force")

    def test_a_binding_to_a_part_already_in_the_store_is_also_basis(self):
        store = dict(self.store)
        part_address = "px.exp.astar.other.something"
        store[part_address] = [1, 2, 3]
        document = json.loads(json.dumps(self.root))
        document["Ticks"][0]["Calculations"][0]["with"]["hex"] = part_address
        value = build_pql_proposal(SENTENCE, document, store, REGISTRY, "force")
        self.assertEqual(value["basis"], [part_address])
        self.assertTrue(value["provisional"])
        self.assertEqual([p["address"] for p in value["existingParts"]], [part_address])

    def test_a_normal_document_is_not_provisional(self):
        value = build_pql_proposal(SENTENCE, self.root, self.store, REGISTRY, "force")
        self.assertEqual(value["basis"], [])
        self.assertFalse(value["provisional"])


# --------------------------------------------------------------------------- (j) cards


class TestCards(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        result = run_cli(
            "template", SENTENCE, "--store", STORE_PATH, "--registry", REGISTRY_SPEC,
            "--set", "blok", "--mode", "force", "--pql", ROOT_PQL_PATH, "--out", self.tmp.name,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.root_path = glob.glob(os.path.join(self.tmp.name, "blok.root.*.json"))[0]
        varied = run_cli("vary", self.root_path, "--store", STORE_PATH, "--registry", REGISTRY_SPEC)
        self.assertEqual(varied.returncode, 0, varied.stderr)

    def test_cards_from_the_set_directory(self):
        out_path = os.path.join(self.tmp.name, "cards.json")
        result = run_cli(
            "cards", self.tmp.name, "--store", STORE_PATH,
            "--labels", "One color, two representations", "--out", out_path,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        document = load_json(out_path)
        self.assertTrue(document["address"].startswith("proposal.neat.cards.blok."))
        cards = document["value"]["cards"]
        self.assertEqual(len(cards), 5)  # root labelled, root unlabelled, a1, a2, b1
        labelled, unlabelled = cards[0], cards[1]
        self.assertEqual(labelled["labels"], ["One color, two representations"])
        self.assertEqual(unlabelled["labels"], [])
        self.assertEqual(labelled["pnc"], unlabelled["pnc"])
        self.assertNotEqual(labelled["review"], unlabelled["review"])
        self.assertEqual(labelled["PQL"], unlabelled["PQL"])
        for card in cards[2:]:
            self.assertNotEqual(card["whatChanged"], "")
            self.assertTrue(card["bindings"])

        html_path = os.path.join(self.tmp.name, "cards.html")
        self.assertTrue(os.path.exists(html_path))
        html_text = open(html_path, encoding="utf-8").read()
        self.assertIn("<title>blok cards</title>", html_text)
        self.assertNotIn("<script", html_text)
        self.assertIn("Approve must identify the exact candidate", html_text)
        for card in cards:
            self.assertIn(card["pnc"], html_text)
            self.assertIn(card["review"], html_text)

    def test_cards_from_a_single_proposal_file_has_only_the_root_pair(self):
        with tempfile.TemporaryDirectory() as solo:
            result = run_cli(
                "template", SENTENCE, "--store", STORE_PATH, "--registry", REGISTRY_SPEC,
                "--set", "blok", "--mode", "force", "--pql", ROOT_PQL_PATH, "--out", solo,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            root_path = glob.glob(os.path.join(solo, "blok.root.*.json"))[0]
            out_path = os.path.join(solo, "cards.json")
            result = run_cli("cards", root_path, "--store", STORE_PATH, "--out", out_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            cards = load_json(out_path)["value"]["cards"]
            self.assertEqual(len(cards), 2)


if __name__ == "__main__":
    unittest.main()
