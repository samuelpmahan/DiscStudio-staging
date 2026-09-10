"""Executable spec of crisp (task 74): template gen required to import into
PxC-ore, tunable to imply or force decomposition; variation through PxC.
"""

from __future__ import annotations

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
    build_pql_proposal,
    build_skeleton_proposal,
    find_slot,
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
        candidates = sorted(candidate for candidate, _change, _mutated in _binding_options(self.pql, self.store))
        self.assertEqual(candidates, ["px.color.swatch.ink", "px.color.swatch.paper"])

    def test_canvas_width_is_not_a_binding_option(self):
        candidates = [candidate for candidate, _change, _mutated in _binding_options(self.pql, self.store)]
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


if __name__ == "__main__":
    unittest.main()
