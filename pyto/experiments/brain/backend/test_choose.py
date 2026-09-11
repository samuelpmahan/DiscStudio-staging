"""the plan: the benchmark Parts, folded into the thing that decides.

a benchmark nobody reads is decoration. these tests are what makes the benchmark
Parts load-bearing: the plan is built from them through PQL, `backend="auto"`
reads the plan, and what comes back is the same answer the reference engine gives.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from pyto import PQL

from experiments.brain import harness
from experiments.brain.backend import cases as case_module
from experiments.brain.backend import choose, evidence, ops


class ThePlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="brain-plan-")
        cls.store = harness.Store(store_dir=os.path.join(cls.tmp.name, "store"), records_dir=os.path.join(cls.tmp.name, "records"))
        evidence.build_benchmarks(cls.store, ops_to_bench=["cumsum", "pairwise", "matmul"])
        cls.address = choose.build(cls.store)
        cls.plan = cls.store.get(cls.address)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_the_plan_is_a_part_at_the_contract_address(self):
        self.assertEqual(self.address, "px.exp.brain.result.backend.plan")
        self.assertEqual(PQL.part(self.address).one(self.store.pxc)["rule"], choose.RULE)
        self.assertIn("for", self.plan)
        self.assertEqual(sorted(self.plan["ops"]), ["cumsum", "matmul", "pairwise"])

    def test_every_step_names_an_engine_that_exists_and_the_time_that_chose_it(self):
        for op, steps in self.plan["by_op"].items():
            self.assertTrue(steps, op)
            sizes = [step[0] for step in steps]
            self.assertEqual(sizes, sorted(sizes), f"{op}: the plan reads in size order")
            for size, engine, median, spread in steps:
                self.assertIn(engine, ops.engines_of(op))
                self.assertGreater(size, 0)
                self.assertGreaterEqual(median, 0.0)
                self.assertGreaterEqual(spread, 1.0, f"{op}: the winner is not slower than the field")

    def test_the_plan_names_the_engine_the_benchmark_parts_actually_measured_fastest(self):
        for op, steps in self.plan["by_op"].items():
            for index, size in enumerate(case_module.sizes_for(op)):
                medians = {
                    engine: self.store.get(harness.bench_address("backend", op, engine, size))["wall_ms_median"]
                    for engine in ops.engines_of(op)
                }
                fastest = min(sorted(medians), key=lambda engine: medians[engine])
                self.assertEqual(steps[index][1], fastest, f"{op} at {size}")

    def test_auto_answers_what_the_reference_engine_answers(self):
        for op, args in (
            ("cumsum", {"values": case_module.V64}),
            ("pairwise", {"a": case_module.P12}),
            ("matmul", {"a": case_module.A6, "b": case_module.B64}),
        ):
            chosen = ops.call(op, dict(args, backend="auto", plan=self.plan))
            passed, worst = harness.close(chosen, ops.call(op, dict(args, backend="py")), 1e-9)
            self.assertTrue(passed, f"{op}: auto and py disagree by {worst}")

    def test_auto_picks_a_different_engine_at_a_different_size(self):
        """the point of the plan: the answer to 'which engine' depends on how much data."""
        small = ops.elements({"values": [0.0] * 8})
        large = ops.elements({"values": [0.0] * 10_000_000})
        picks = {choose.engine_for(self.plan, "cumsum", small), choose.engine_for(self.plan, "cumsum", large)}
        self.assertTrue(picks <= set(ops.ENGINES))
        self.assertEqual(choose.engine_for(self.plan, "cumsum", large), self.plan["by_op"]["cumsum"][-1][1])
        self.assertEqual(choose.engine_for(self.plan, "cumsum", 1), self.plan["by_op"]["cumsum"][0][1])

    def test_elements_counts_the_same_thing_for_a_call_and_for_a_benchmark(self):
        self.assertEqual(ops.elements({"values": [1.0, 2.0, 3.0]}), 3)
        self.assertEqual(ops.elements({"a": [[1.0, 2.0], [3.0, 4.0]]}), 4)
        self.assertEqual(ops.elements({"a": {"shape": [2, 2], "values": [[1.0, 2.0], [3.0, 4.0]]}}), 4)
        self.assertEqual(ops.elements({"packed": {"dtype": "float64", "shape": [4, 5], "b64": ""}}), 20)
        self.assertEqual(ops.elements({"values": [1.0], "backend": "np", "plan": {"anything": 1}}), 1)
        self.assertEqual(ops.elements(case_module.bench_inputs("cumsum", 1024)), 1024)

    def test_auto_without_a_plan_is_refused_by_name(self):
        with self.assertRaises(ValueError) as refused:
            ops.call("cumsum", {"values": [1.0], "backend": "auto"})
        self.assertIn("needs args['plan']", str(refused.exception))
        with self.assertRaises(ValueError) as refused:
            choose.engine_for(self.plan, "fft", 1024)
        self.assertIn("says nothing about 'fft'", str(refused.exception))

    def test_explain_reads_back_what_a_reader_can_check(self):
        line = choose.explain(self.plan, "pairwise")
        self.assertTrue(line.startswith("pairwise: "))
        self.assertIn("ms", line)


if __name__ == "__main__":
    unittest.main()
