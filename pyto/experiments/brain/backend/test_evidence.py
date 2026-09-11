"""the evidence build, in a temporary store: every oracle passes, and every Part
the contract asks for is where PQL can find it.

the store and records these tests write go to a `TemporaryDirectory`, never into
the repository: a committed run record holds a wall-clock duration, so a test
that rewrote one would dirty MAIN and refuse the next landing.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from pyto import PQL

from experiments.brain import harness
from experiments.brain.backend import cases as case_module
from experiments.brain.backend import evidence, ops


def fresh():
    tmp = tempfile.TemporaryDirectory(prefix="brain-backend-evidence-")
    store = harness.Store(store_dir=os.path.join(tmp.name, "store"), records_dir=os.path.join(tmp.name, "records"))
    return store, tmp


class TheEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store, cls.tmp = fresh()
        cls.produced = evidence.build_results(cls.store)
        cls.verdicts = evidence.build_oracles(cls.store, cls.produced)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_engine_of_every_case_has_an_oracle_part_and_passes(self):
        expected = sum(len(ops.engines_of(case["op"])) for case in case_module.cases())
        self.assertEqual(len(self.verdicts), expected)
        failed = [key for key, ok in self.verdicts.items() if not ok]
        self.assertEqual(failed, [], "a backend that changes semantics is a failed backend")
        parts = PQL.prefix("px.exp.brain.oracle.backend.").matches(self.store.pxc)
        self.assertEqual(len(parts), expected)
        for match in parts:
            self.assertTrue(match.value["reference"], match.address)
            self.assertIn("for", match.value)

    def test_every_op_has_an_oracle_for_all_three_engines(self):
        for op in ops.ops():
            for engine in ("py", "np", "sp"):
                found = PQL.prefix(f"px.exp.brain.oracle.backend.{op}.").where(
                    lambda match, engine=engine: match.address.endswith("_" + engine)
                ).addresses(self.store.pxc)
                self.assertTrue(found, f"{op}/{engine} has no oracle Part")

    def test_the_inputs_went_in_as_dataset_parts_not_as_literals(self):
        datasets = PQL.prefix("px.exp.brain.data.backend_").matches(self.store.pxc)
        self.assertTrue(datasets)
        for match in datasets:
            self.assertIn("rows", match.value)
            self.assertIn("for", match.value)

    def test_one_observed_record_per_op(self):
        for op in ops.ops():
            path = os.path.join(self.store.records_dir, f"brain_backend_{op}.json")
            self.assertTrue(os.path.exists(path), path)
        self.assertTrue(PQL.prefix("px.receipt.brain_backend_matmul.").addresses(self.store.pxc))

    def test_benchmarks_write_a_part_per_engine_with_a_comparable_digest(self):
        store, tmp = fresh()
        self.addCleanup(tmp.cleanup)
        built = evidence.build_benchmarks(store, ops_to_bench=["cumsum"])
        self.assertEqual(len(built), 3 * len(case_module.sizes_for("cumsum")))
        by_size = {}
        for match in PQL.prefix("px.exp.brain.bench.backend.cumsum.").matches(store.pxc):
            by_size.setdefault(match.value["size"], set()).add(match.value["inputs_sha256"])
            self.assertGreaterEqual(match.value["wall_ms_median"], match.value["wall_ms_min"])
            self.assertGreaterEqual(match.value["n"], 3)
        for size, digests in by_size.items():
            self.assertEqual(len(digests), 1, f"the three engines at size {size} must be measured on the same input")

    def test_bench_inputs_are_the_same_inputs_every_run(self):
        for op in ("matmul", "cumsum", "fft"):
            first = case_module.bench_inputs(op, case_module.sizes_for(op)[0])
            again = case_module.bench_inputs(op, case_module.sizes_for(op)[0])
            self.assertEqual(harness.digest(first), harness.digest(again), op)


if __name__ == "__main__":
    unittest.main()
