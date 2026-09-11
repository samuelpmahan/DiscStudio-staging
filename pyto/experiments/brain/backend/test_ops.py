"""the facade's semantics, pinned: every engine answers the same question.

three things are checked for every op: each engine agrees with the numpy or
scipy call named as the reference, the engines agree with each other, and what
leaves an op is json. the refusals are checked too: a stub that says why beats a
stub that answers wrongly.
"""

from __future__ import annotations

import json
import math
import unittest

from pyto import PQL, Part, PxC

from experiments.brain import harness
from experiments.brain.backend import cases as case_module
from experiments.brain.backend import ops


class TheFacade(unittest.TestCase):
    def test_every_op_has_the_three_engines(self):
        self.assertEqual(
            ops.ops(),
            ("argsort", "cholesky", "cumsum", "eig", "fft", "histogram", "inv", "lstsq", "matmul", "norm",
             "pairwise", "select_k", "solve", "sort", "svd", "trace"),
        )
        for op in ops.ops():
            self.assertEqual(ops.engines_of(op), ("np", "py", "sp"), op)
            self.assertEqual(ops.calculation(op).address, f"fn.brain.backend.{op}")

    def test_an_unknown_op_or_engine_is_refused_by_name(self):
        with self.assertRaises(ValueError) as refused:
            ops.call("inverse", {"backend": "np"})
        self.assertIn("no op named 'inverse'", str(refused.exception))
        with self.assertRaises(ValueError) as refused:
            ops.call("matmul", {"a": [[1.0]], "b": [[1.0]], "backend": "cuda"})
        self.assertIn("has no 'cuda' engine", str(refused.exception))

    def test_a_dataset_part_of_either_shape_goes_in_whole(self):
        table = {"for": "x", "columns": ["a", "b"], "rows": [[1.0, 2.0], [3.0, 4.0]]}
        drawn = {"for": "x", "shape": [2, 2], "values": [[1.0, 2.0], [3.0, 4.0]]}
        for part in (table, drawn):
            self.assertEqual(ops.matrix(part), [[1.0, 2.0], [3.0, 4.0]])
        self.assertEqual(ops.vector({"for": "x", "columns": ["a"], "rows": [[1.0], [2.0]]}), [1.0, 2.0])


class EveryEngineAgrees(unittest.TestCase):
    """the one rule the whole vertical rests on: a backend that changes semantics
    is a failed backend. here it is, as an assertion, for every op and engine."""

    def test_each_engine_matches_the_named_reference(self):
        checked = set()
        for case in case_module.cases():
            expected = case["expected"]()
            for backend in ops.engines_of(case["op"]):
                with self.subTest(op=case["op"], case=case["case"], backend=backend):
                    got = ops.call(case["op"], dict(case["args"], backend=backend))
                    passed, worst = harness.close(got, expected, case["tolerance"])
                    self.assertTrue(passed, f"{case['op']}/{backend} vs {case['reference']}: worst relative error {worst}")
                    json.dumps(harness.jsonable(got))
            checked.add(case["op"])
        self.assertEqual(checked, set(ops.ops()), "every op has at least one case")

    def test_the_engines_agree_with_each_other_and_not_only_with_numpy(self):
        for case in case_module.cases():
            answers = {backend: ops.call(case["op"], dict(case["args"], backend=backend)) for backend in ops.engines_of(case["op"])}
            for backend, got in answers.items():
                passed, worst = harness.close(got, answers["py"], case["tolerance"])
                self.assertTrue(passed, f"{case['op']}: {backend} and py disagree by {worst}")


class ThePinnedSemantics(unittest.TestCase):
    def test_ties_are_broken_by_index_in_every_engine(self):
        tied = case_module.TIED
        for backend in ("py", "np", "sp"):
            self.assertEqual(
                ops.call("argsort", {"values": tied, "backend": backend}),
                [7, 1, 4, 3, 6, 0, 2, 5],
                backend,
            )
            top = ops.call("select_k", {"values": tied, "k": 4, "backend": backend})
            self.assertEqual(top["indices"], [0, 2, 5, 3], backend)
            self.assertEqual(top["values"], [3.0, 3.0, 3.0, 2.0], backend)
            bottom = ops.call("select_k", {"values": tied, "k": 3, "largest": False, "backend": backend})
            self.assertEqual(bottom["indices"], [7, 1, 4], backend)

    def test_select_k_at_and_past_the_length(self):
        for backend in ("py", "np"):
            whole = ops.call("select_k", {"values": [2.0, 1.0, 3.0], "k": 3, "backend": backend})
            self.assertEqual(whole["indices"], [2, 0, 1], backend)

    def test_eigenvectors_leave_with_a_positive_first_component(self):
        for backend in ("py", "np", "sp"):
            vectors = ops.call("eig", {"a": case_module.S6, "backend": backend})["eigenvectors"]
            for column in range(len(vectors[0])):
                first = next(vectors[row][column] for row in range(len(vectors)) if abs(vectors[row][column]) > 1e-12)
                self.assertGreater(first, 0.0, f"{backend} column {column}")

    def test_eigenvalues_come_back_ascending(self):
        values = ops.call("eig", {"a": case_module.S6, "backend": "py"})["eigenvalues"]
        self.assertEqual(values, sorted(values))

    def test_the_eigenvectors_actually_are_eigenvectors(self):
        got = ops.call("eig", {"a": case_module.S6, "backend": "py"})
        for column, value in enumerate(got["eigenvalues"]):
            vector = [row[column] for row in got["eigenvectors"]]
            product = [math.fsum(cell * x for cell, x in zip(row, vector)) for row in case_module.S6]
            for left, x in zip(product, vector):
                self.assertAlmostEqual(left, value * x, places=6)

    def test_a_complex_spectrum_leaves_as_two_real_lists(self):
        got = ops.call("fft", {"values": [1.0, 0.0, 0.0, 0.0], "backend": "py"})
        self.assertEqual(got, {"real": [1.0, 1.0, 1.0, 1.0], "imag": [0.0, 0.0, 0.0, 0.0]})
        json.dumps(got)


class TheStubsSayWhy(unittest.TestCase):
    def test_the_py_engine_of_eig_refuses_a_non_symmetric_matrix(self):
        with self.assertRaises(ValueError) as refused:
            ops.call("eig", {"a": [[0.0, 1.0], [2.0, 0.0]], "backend": "py"})
        self.assertIn("symmetric-only", str(refused.exception))
        got = ops.call("eig", {"a": [[0.0, 1.0], [2.0, 0.0]], "backend": "np"})
        self.assertEqual(len(got["eigenvalues"]), 2, "np answers where py declines")

    def test_a_complex_spectrum_is_refused_rather_than_silently_made_real(self):
        with self.assertRaises(ValueError) as refused:
            ops.call("eig", {"a": [[0.0, -1.0], [1.0, 0.0]], "backend": "np"})
        self.assertIn("complex", str(refused.exception))

    def test_the_py_engine_of_fft_refuses_a_length_that_is_not_a_power_of_two(self):
        with self.assertRaises(ValueError) as refused:
            ops.call("fft", {"values": [1.0, 2.0, 3.0], "backend": "py"})
        self.assertIn("radix-2", str(refused.exception))
        self.assertEqual(len(ops.call("fft", {"values": [1.0, 2.0, 3.0], "backend": "np"})["real"]), 3)

    def test_cholesky_refuses_a_matrix_that_is_not_positive_definite(self):
        for backend in ("py", "np", "sp"):
            with self.subTest(backend=backend), self.assertRaises(ValueError) as refused:
                ops.call("cholesky", {"a": [[1.0, 2.0], [2.0, 1.0]], "backend": backend})
            self.assertIn("positive definite", str(refused.exception))

    def test_inv_refuses_a_singular_matrix_in_every_engine(self):
        for backend in ("py", "np", "sp"):
            with self.subTest(backend=backend), self.assertRaises(ValueError):
                ops.call("inv", {"a": [[1.0, 2.0], [2.0, 4.0]], "backend": backend})

    def test_norm_tells_a_vector_from_a_matrix_by_its_shape(self):
        column = {"for": "x", "columns": ["a"], "rows": [[3.0], [4.0]]}
        for backend in ("py", "np", "sp"):
            self.assertAlmostEqual(ops.call("norm", {"a": column, "backend": backend}), 5.0, places=12)
            self.assertAlmostEqual(
                ops.call("norm", {"a": [[3.0, 0.0], [0.0, 4.0]], "backend": backend}), 5.0, places=12)

    def test_every_engine_refuses_a_singular_matrix_the_same_way(self):
        """scipy raises nothing and numpy raises LinAlgError; the facade makes both
        a ValueError, because a refusal a caller must catch per engine is a
        semantics difference like any other."""
        for backend in ("py", "np", "sp"):
            with self.subTest(backend=backend), self.assertRaises(ValueError):
                ops.call("solve", {"a": [[1.0, 2.0], [2.0, 4.0]], "b": [1.0, 2.0], "backend": backend})


class ThroughAPcr(unittest.TestCase):
    def test_the_facade_runs_as_calculations_in_a_real_program(self):
        import os
        import tempfile

        tmp = tempfile.TemporaryDirectory(prefix="brain-backend-ops-")
        self.addCleanup(tmp.cleanup)
        store = harness.Store(store_dir=os.path.join(tmp.name, "store"), records_dir=os.path.join(tmp.name, "records"))
        data = harness.dataset(store, "ops_demo", "the facade in a program", ["a", "b", "c"], case_module.P12)
        distances = harness.result_address("backend", "pairwise", "demo")
        column = harness.result_address("backend", "cumsum", "demo")
        run = store.run(
            "brain_backend_ops",
            [
                ("distances", [{"id": "pairwise", "calc": ops.calculation("pairwise"), "into": distances, "args": {"backend": "np"}, "inputs": {"a": data}}]),
                ("order", [{"id": "cumsum", "calc": ops.calculation("cumsum"), "into": column, "args": {"backend": "py"}, "inputs": {"values": distances}}]),
            ],
        )
        self.assertEqual(run.results["pairwise"]["shape"], [12, 12])
        self.assertEqual(len(store.get(column)), 144, "the second tick read the first's result")
        self.assertEqual(
            run.ticks[1].calculations[0].inputs["values"], "fn:pairwise",
            "the facade chains through results, not through the store",
        )
        self.assertTrue(PQL.prefix("px.receipt.brain_backend_ops.").addresses(store.pxc))
        self.assertTrue(os.path.exists(os.path.join(store.records_dir, "brain_backend_ops.json")))


if __name__ == "__main__":
    unittest.main()
