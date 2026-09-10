"""Executable spec of fn.neat.diff.candidates (task 66): the difference between two
PQL documents, computed before it is shown, and never mined before it is counted.
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
    print(f"[tests/test_neat_diff] sys.path.insert(0, {TESTS!r})", file=sys.stderr)
    sys.path.insert(0, TESTS)

SRC = os.path.join(PYTO_ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from pyto.neat.diff import (  # noqa: E402
    ADDRESS_TEMPLATE,
    candidates,
    run_document,
    structural_digest,
)

VIEWER_TEST_DIR = os.path.join(PYTO_ROOT, "viewer", "test")
if VIEWER_TEST_DIR not in sys.path:
    print(f"[tests/test_neat_diff] sys.path.insert(0, {VIEWER_TEST_DIR!r})", file=sys.stderr)
    sys.path.insert(0, VIEWER_TEST_DIR)

from record_schema import validate as validate_record  # noqa: E402

from fixtures.blok.registry import HSL, REGISTRY, RGB  # noqa: E402

CARDS = os.path.join(TESTS, "fixtures", "blok", "cards.json")


def load_cards():
    with open(CARDS, encoding="utf-8") as handle:
        return json.load(handle)


def without_labels(document):
    return {key: value for key, value in document.items() if key != "labels"}


class TestStructuralDigest(unittest.TestCase):
    def setUp(self):
        cards = load_cards()
        self.root = cards["root"]
        self.variant = cards["variant"]

    def test_labels_are_not_structural(self):
        self.assertEqual(structural_digest(self.root), structural_digest(without_labels(self.root)))

    def test_variant_digests_differently(self):
        self.assertNotEqual(structural_digest(self.root), structural_digest(self.variant))


class TestCandidates(unittest.TestCase):
    def setUp(self):
        cards = load_cards()
        self.root = cards["root"]
        self.variant = cards["variant"]
        self.store = cards["store"]
        self.registry = REGISTRY

    def _candidates(self, doc_a, doc_b):
        return candidates(
            {"doc_a": doc_a, "doc_b": doc_b, "store": self.store, "registry": self.registry}
        )

    def test_root_against_unlabelled_self_is_structural_same(self):
        value = self._candidates(self.root, without_labels(self.root))
        self.assertEqual(value["structural"], "same")
        self.assertEqual(value["outputs"], {RGB: "same", HSL: "same"})
        self.assertEqual(value["remainder"], ["One color, two representations"])

    def test_root_against_variant_is_structural_different(self):
        value = self._candidates(self.root, self.variant)
        self.assertEqual(value["structural"], "different")
        self.assertEqual(value["outputs"], {RGB: "changed", HSL: "changed"})

    def test_a_document_with_an_oc_call_is_not_run(self):
        oc_doc = {
            "Ticks": [
                {
                    "name": "Read",
                    "Calculations": [
                        {
                            "call": "oc.blok.readSwatch",
                            "with": {},
                            "args": {},
                            "into": RGB,
                        }
                    ]
                }
            ]
        }
        value = self._candidates(self.root, oc_doc)
        self.assertEqual(value["outputs"], {RGB: "unknown", HSL: "unknown"})
        self.assertIn("not run: oc.blok.readSwatch is oc.", value["remainder"])

    def test_address_uses_first_16_hex_of_each_structural_digest(self):
        value = self._candidates(self.root, self.variant)
        self.assertEqual(value["a"][:16], structural_digest(self.root)[:16])
        self.assertEqual(value["b"][:16], structural_digest(self.variant)[:16])
        address = ADDRESS_TEMPLATE.format(a=value["a"][:16], b=value["b"][:16])
        self.assertTrue(address.startswith("px.exp.blok.diff."))

    def test_same_inputs_same_bytes(self):
        first = self._candidates(self.root, self.variant)
        second = self._candidates(self.root, self.variant)
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )


class TestRunDocumentRecords(unittest.TestCase):
    """The run records `run_document` produces are the shared schema, checked by
    the second, independent reader (viewer/test/record_schema.py), not only by the
    producer that wrote them."""

    def test_records_of_both_runs_validate(self):
        cards = load_cards()
        run_a, pxc_a = run_document(cards["root"], cards["store"], REGISTRY, "neat.diff.a")
        run_b, pxc_b = run_document(cards["variant"], cards["store"], REGISTRY, "neat.diff.b")
        from pyto.materialize import run_record

        preexisting = set(cards["store"])
        record_a = run_record(run_a, pxc_a, preexisting=preexisting)
        record_b = run_record(run_b, pxc_b, preexisting=preexisting)
        validate_record(record_a)
        validate_record(record_b)


class TestCLI(unittest.TestCase):
    def setUp(self):
        cards = load_cards()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.a_path = os.path.join(self.tmp.name, "root.json")
        self.b_path = os.path.join(self.tmp.name, "variant.json")
        self.store_path = os.path.join(self.tmp.name, "store.json")
        with open(self.a_path, "w", encoding="utf-8") as handle:
            json.dump(cards["root"], handle)
        with open(self.b_path, "w", encoding="utf-8") as handle:
            json.dump(cards["variant"], handle)
        with open(self.store_path, "w", encoding="utf-8") as handle:
            json.dump(cards["store"], handle)
        # Never the tree under test: a landing runs this suite on MAIN and the child
        # process writes wherever the pyto it imports lives (task 68 was refused for it).
        self.diffs_dir = os.path.join(self.tmp.name, "diffs")

    def run_cli(self):
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "pyto.neat.diff",
                self.a_path,
                self.b_path,
                "--store",
                self.store_path,
                "--registry",
                "tests.fixtures.blok.registry:REGISTRY",
                "--diffs-dir",
                self.diffs_dir,
            ],
            cwd=PYTO_ROOT,
            capture_output=True,
            text=True,
        )

    def test_cli_writes_the_part_and_both_run_records(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        stem = f"{value['a'][:16]}-{value['b'][:16]}"
        part_path = os.path.join(self.diffs_dir, f"{stem}.json")
        record_a_path = os.path.join(self.diffs_dir, f"{stem}.a.record.json")
        record_b_path = os.path.join(self.diffs_dir, f"{stem}.b.record.json")
        self.addCleanup(lambda: os.path.exists(part_path) and os.remove(part_path))
        self.addCleanup(lambda: os.path.exists(record_a_path) and os.remove(record_a_path))
        self.addCleanup(lambda: os.path.exists(record_b_path) and os.remove(record_b_path))

        self.assertTrue(os.path.exists(part_path))
        with open(part_path, encoding="utf-8") as handle:
            part = json.load(handle)
        self.assertEqual(part["address"], f"px.exp.blok.diff.{stem.replace('-', '.')}")
        self.assertEqual(part["value"], value)
        expected_sha256 = __import__("hashlib").sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        self.assertEqual(part["sha256"], expected_sha256)

        for path in (record_a_path, record_b_path):
            self.assertTrue(os.path.exists(path))
            with open(path, encoding="utf-8") as handle:
                validate_record(json.load(handle))

    def test_two_runs_of_the_cli_give_identical_part_bytes(self):
        first = self.run_cli()
        self.assertEqual(first.returncode, 0, first.stderr)
        value = json.loads(first.stdout)
        stem = f"{value['a'][:16]}-{value['b'][:16]}"
        part_path = os.path.join(self.diffs_dir, f"{stem}.json")
        self.addCleanup(lambda: os.path.exists(part_path) and os.remove(part_path))
        self.addCleanup(
            lambda: os.path.exists(
                os.path.join(self.diffs_dir, f"{stem}.a.record.json")
            )
            and os.remove(os.path.join(self.diffs_dir, f"{stem}.a.record.json"))
        )
        self.addCleanup(
            lambda: os.path.exists(
                os.path.join(self.diffs_dir, f"{stem}.b.record.json")
            )
            and os.remove(os.path.join(self.diffs_dir, f"{stem}.b.record.json"))
        )
        with open(part_path, "rb") as handle:
            first_bytes = handle.read()

        second = self.run_cli()
        self.assertEqual(second.returncode, 0, second.stderr)
        with open(part_path, "rb") as handle:
            second_bytes = handle.read()

        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(first.stdout, second.stdout)


if __name__ == "__main__":
    unittest.main()
