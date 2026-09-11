import json
import unittest

import stats.correlation as correlation
from stats.correlation_cases import BENCH_CASES, ORACLE_CASES, TABLE, TIES_X, TIES_Y, X, Y
from stats.tolerance import close


class TestOracles(unittest.TestCase):
    def test_every_oracle_case_matches_its_reference(self):
        self.assertGreaterEqual(len(ORACLE_CASES), 15)
        for case in ORACLE_CASES:
            with self.subTest(case=case["case"], calc=case["calc"]):
                got = correlation.CALCS[case["calc"]](case["args"])
                self.assertTrue(
                    close(got, case["expected"](), case["tolerance"]),
                    "%s: got %r, %s says %r" % (case["case"], got, case["reference"], case["expected"]()))

    def test_every_calculation_has_a_case(self):
        covered = {case["calc"] for case in ORACLE_CASES}
        self.assertEqual(set(correlation.CALCS) - covered, set())


class TestBackendsAgree(unittest.TestCase):
    def test_py_and_np_agree(self):
        for address in ("fn.brain.stats.covariance", "fn.brain.stats.pearson",
                        "fn.brain.stats.spearman", "fn.brain.stats.kendall"):
            with self.subTest(calc=address):
                calc = correlation.CALCS[address]
                py = calc({"x": X[:40], "y": Y[:40], "backend": "py"})
                np_ = calc({"x": X[:40], "y": Y[:40], "backend": "np"})
                self.assertTrue(close(np_, py, 1e-9))

    def test_the_matrix_backends_agree(self):
        py = correlation.correlation_matrix({"table": TABLE, "backend": "py"})
        np_ = correlation.correlation_matrix({"table": TABLE, "backend": "np"})
        self.assertTrue(close(np_["matrix"], py["matrix"], 1e-9))


class TestEdges(unittest.TestCase):
    def test_length_mismatch_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            correlation.pearson({"x": [1.0, 2.0], "y": [1.0]})
        self.assertIn("same length", str(caught.exception))

    def test_one_observation_is_refused(self):
        with self.assertRaises(ValueError):
            correlation.pearson({"x": [1.0], "y": [2.0]})

    def test_a_constant_sample_has_no_pearson(self):
        for backend in ("py", "np"):
            with self.assertRaises(ValueError):
                correlation.pearson({"x": [1.0, 1.0, 1.0], "y": [1.0, 2.0, 3.0],
                                     "backend": backend})

    def test_a_fully_tied_sample_has_no_tau_b(self):
        with self.assertRaises(ValueError):
            correlation.kendall({"x": [2.0] * 6, "y": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]})

    def test_perfect_agreement(self):
        straight = [1.0, 2.0, 3.0, 4.0, 5.0]
        self.assertAlmostEqual(correlation.pearson({"x": straight, "y": straight}), 1.0)
        self.assertAlmostEqual(correlation.kendall({"x": straight, "y": straight}), 1.0)
        self.assertAlmostEqual(
            correlation.spearman({"x": straight, "y": list(reversed(straight))}), -1.0)

    def test_a_missing_column_names_what_is_there(self):
        with self.assertRaises(ValueError) as caught:
            correlation.correlation_matrix({"table": TABLE, "columns": ["x", "nope"]})
        self.assertIn("nope", str(caught.exception))

    def test_rank_averages_ties(self):
        self.assertEqual(correlation.rank({"values": [5.0, 1.0, 5.0, 3.0]}),
                         [3.5, 1.0, 3.5, 2.0])
        self.assertEqual(correlation.rank({"values": TIES_Y})[:3], [3.0, 1.0, 3.0])


class TestJsonAble(unittest.TestCase):
    def test_every_result_survives_json(self):
        for case in ORACLE_CASES:
            got = correlation.CALCS[case["calc"]](case["args"])
            self.assertEqual(json.loads(json.dumps(got)), got)


class TestBenchCases(unittest.TestCase):
    def test_bench_cases_are_paired_and_runnable(self):
        pairs = {}
        for case in BENCH_CASES:
            pairs.setdefault((case["calc"], case["size"]), set()).add(case["backend"])
        for key, backends in pairs.items():
            self.assertEqual(backends, {"py", "np"}, "%r is not a comparable pair" % (key,))
        sample = BENCH_CASES[0]
        correlation.CALCS[sample["calc"]](sample["make_args"]())


if __name__ == "__main__":
    unittest.main()
