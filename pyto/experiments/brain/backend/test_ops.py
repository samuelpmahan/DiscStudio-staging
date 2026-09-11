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
            ("argsort", "cholesky", "convolve", "correlate", "cumsum", "diff", "eig", "fft",
             "gradient", "histogram", "interp", "inv", "lstsq", "matmul", "matrix_rank", "norm",
             "outer", "pack", "pairwise", "pinv", "qr", "select_k", "solve", "sort", "svd", "trace",
             "unpack"),
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
            for backend in case_module.engines_of_case(case, ops.engines_of(case["op"])):
                with self.subTest(op=case["op"], case=case["case"], backend=backend):
                    got = ops.call(case["op"], dict(case["args"], backend=backend))
                    passed, worst = harness.close(got, expected, case["tolerance"])
                    self.assertTrue(passed, f"{case['op']}/{backend} vs {case['reference']}: worst relative error {worst}")
                    json.dumps(harness.jsonable(got))
            checked.add(case["op"])
        self.assertEqual(checked, set(ops.ops()), "every op has at least one case")

    def test_the_engines_agree_with_each_other_and_not_only_with_numpy(self):
        for case in case_module.cases():
            engines = case_module.engines_of_case(case, ops.engines_of(case["op"]))
            answers = {backend: ops.call(case["op"], dict(case["args"], backend=backend)) for backend in engines}
            reference = "py" if "py" in answers else sorted(answers)[0]
            for backend, got in answers.items():
                passed, worst = harness.close(got, answers[reference], case["tolerance"])
                self.assertTrue(passed, f"{case['op']}/{case['case']}: {backend} and {reference} disagree by {worst}")


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


class TheBracketsWinnerAsAnOp(unittest.TestCase):
    """`pack`/`unpack` are what the array_store bracket decided, made usable.

    the round trip is exact - not close, exact - because nothing is turned into
    decimal text on the way: it is the float64 buffer, base64'd, and back.
    """

    def test_the_round_trip_is_exact_in_every_engine(self):
        matrix = [[float(row) * 0.1 + column / 3.0 for column in range(7)] for row in range(5)]
        for backend in ("py", "np", "sp"):
            packed = ops.call("pack", {"a": matrix, "backend": backend})
            self.assertEqual(packed["shape"], [5, 7])
            self.assertEqual(packed["dtype"], "float64")
            for other in ("py", "np", "sp"):
                back = ops.call("unpack", {"packed": packed, "backend": other})
                self.assertEqual(back["values"], matrix, f"{backend} packed, {other} unpacked")

    def test_the_engines_pack_the_same_bytes(self):
        matrix = [[1.5, -2.25], [3.125, 4.0]]
        packed = {backend: ops.call("pack", {"a": matrix, "backend": backend})["b64"] for backend in ("py", "np", "sp")}
        self.assertEqual(len(set(packed.values())), 1, packed)

    def test_packing_wins_on_real_float64_and_loses_on_short_decimals(self):
        """the honest boundary, not the slogan.

        base64 of float64 is a flat 11 bytes per number whatever the number is.
        json is as long as the decimal text: about 20 bytes for a drawn float64
        and 6 for a small round one. So packing wins by roughly 1.8x on measured
        data - which is what the array_store bracket measured - and loses on a
        table of small integers. The op is the right default for the ml vertical's
        matrices and the wrong one for a column of counts.
        """
        drawn = case_module.draw((48, 48)).tolist()
        packed = len(json.dumps(ops.call("pack", {"a": drawn, "backend": "np"})))
        nested = len(json.dumps({"shape": [48, 48], "values": drawn}))
        self.assertLess(packed, nested)
        self.assertGreater(nested / packed, 1.5)

        rounded = [[float(row * 48 + column) for column in range(48)] for row in range(48)]
        self.assertGreater(len(json.dumps(ops.call("pack", {"a": rounded, "backend": "np"}))),
                           len(json.dumps({"shape": [48, 48], "values": rounded})))

    def test_unpack_refuses_a_dtype_it_does_not_know(self):
        with self.assertRaises(ValueError) as refused:
            ops.call("unpack", {"packed": {"dtype": "float32", "shape": [1, 1], "b64": ""}, "backend": "py"})
        self.assertIn("float64 only", str(refused.exception))


class TheNewerOps(unittest.TestCase):
    def test_qr_reconstructs_a_and_its_q_is_orthonormal(self):
        for backend in ("py", "np", "sp"):
            got = ops.call("qr", {"a": case_module.B64, "backend": backend})
            q, r = got["q"]["values"], got["r"]["values"]
            for i in range(len(r)):
                self.assertGreaterEqual(r[i][i], 0.0, f"{backend}: r's diagonal is the sign convention")
            for i in range(len(q[0])):
                for j in range(len(q[0])):
                    dot = sum(q[k][i] * q[k][j] for k in range(len(q)))
                    self.assertAlmostEqual(dot, 1.0 if i == j else 0.0, places=9, msg=backend)
            for i, row in enumerate(case_module.B64):
                for j, cell in enumerate(row):
                    self.assertAlmostEqual(sum(q[i][k] * r[k][j] for k in range(len(r))), cell, places=9, msg=backend)

    def test_qr_refuses_a_matrix_wider_than_it_is_tall(self):
        with self.assertRaises(ValueError):
            ops.call("qr", {"a": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], "backend": "py"})

    def test_convolve_modes_agree_across_engines(self):
        a, v = [1.0, 2.0, 3.0, 4.0, 5.0], [0.25, 0.5, 0.25]
        for mode in ("full", "same", "valid"):
            answers = {backend: ops.call("convolve", {"a": a, "v": v, "mode": mode, "backend": backend})
                       for backend in ("py", "np", "sp")}
            for backend, got in answers.items():
                passed, worst = harness.close(got, answers["np"], 1e-9)
                self.assertTrue(passed, f"{mode}/{backend}: {worst}")
        with self.assertRaises(ValueError):
            ops.call("convolve", {"a": a, "v": v, "mode": "sideways", "backend": "py"})

    def test_interp_clamps_outside_the_samples_in_every_engine(self):
        args = {"x": [-5.0, 0.0, 0.5, 2.0, 7.0], "xp": [0.0, 1.0, 2.0], "fp": [3.0, 5.0, 9.0]}
        for backend in ("py", "np", "sp"):
            self.assertEqual(ops.call("interp", dict(args, backend=backend)), [3.0, 3.0, 4.0, 9.0, 9.0], backend)

    def test_interp_refuses_samples_that_do_not_increase(self):
        with self.assertRaises(ValueError):
            ops.call("interp", {"x": [0.5], "xp": [1.0, 1.0], "fp": [1.0, 2.0], "backend": "py"})


class TheLastOps(unittest.TestCase):
    def test_matrix_rank_sees_the_column_that_is_a_sum_of_two_others(self):
        for backend in ("py", "np", "sp"):
            self.assertEqual(ops.call("matrix_rank", {"a": case_module.B64, "backend": backend}), 4, backend)
        for backend in ("np", "sp"):
            self.assertEqual(ops.call("matrix_rank", {"a": case_module.DEFICIENT, "backend": backend}), 3, backend)

    def test_the_py_engine_of_matrix_rank_refuses_what_its_svd_cannot_resolve(self):
        """squaring the condition number is the cost of an svd through a^T a, and it
        is paid exactly here: the py engine says so instead of guessing."""
        with self.assertRaises(ValueError) as refused:
            ops.call("matrix_rank", {"a": case_module.DEFICIENT, "backend": "py"})
        self.assertIn("cannot resolve a singular value", str(refused.exception))

    def test_pinv_is_a_left_inverse_and_py_refuses_where_it_cannot_be_one(self):
        for backend in ("py", "np", "sp"):
            got = ops.call("pinv", {"a": case_module.B64, "backend": backend})["values"]
            product = [[sum(got[i][k] * case_module.B64[k][j] for k in range(6)) for j in range(4)] for i in range(4)]
            for i in range(4):
                for j in range(4):
                    self.assertAlmostEqual(product[i][j], 1.0 if i == j else 0.0, places=8, msg=backend)
        with self.assertRaises(ValueError) as refused:
            ops.call("pinv", {"a": case_module.DEFICIENT, "backend": "py"})
        self.assertIn("full column rank", str(refused.exception))
        self.assertEqual(len(ops.call("pinv", {"a": case_module.DEFICIENT, "backend": "np"})["values"]), 4)

    def test_gradient_keeps_the_length_and_diff_does_not(self):
        values = [1.0, 4.0, 9.0, 16.0]
        for backend in ("py", "np", "sp"):
            self.assertEqual(len(ops.call("gradient", {"values": values, "backend": backend})), 4, backend)
            self.assertEqual(ops.call("diff", {"values": values, "backend": backend}), [3.0, 5.0, 7.0], backend)
            self.assertEqual(ops.call("diff", {"values": values, "order": 2, "backend": backend}), [2.0, 2.0], backend)
        with self.assertRaises(ValueError):
            ops.call("gradient", {"values": [1.0], "backend": "py"})

    def test_correlate_is_not_convolve(self):
        a, v = [1.0, 2.0, 3.0, 4.0], [0.0, 1.0, 0.5]
        for backend in ("py", "np", "sp"):
            correlated = ops.call("correlate", {"a": a, "v": v, "mode": "full", "backend": backend})
            convolved = ops.call("convolve", {"a": a, "v": v, "mode": "full", "backend": backend})
            self.assertNotEqual(correlated, convolved, backend)
            self.assertEqual(correlated, ops.call("convolve", {"a": a, "v": list(reversed(v)), "mode": "full", "backend": backend}), backend)

    def test_outer_is_a_matrix_of_the_two_lengths(self):
        for backend in ("py", "np", "sp"):
            got = ops.call("outer", {"a": [1.0, 2.0], "b": [3.0, 4.0, 5.0], "backend": backend})
            self.assertEqual(got, {"shape": [2, 3], "values": [[3.0, 4.0, 5.0], [6.0, 8.0, 10.0]]}, backend)


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
