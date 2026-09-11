import json
import math
import unittest

from scipy import stats as sp_stats

import stats.nonparametric as nonparametric
from stats.nonparametric_cases import BENCH_CASES, CHI2_LIKE, ORACLE_CASES, ZEROS
from stats.hypothesis_cases import A, B
from stats.tolerance import close


class TestOracles(unittest.TestCase):
    def test_every_oracle_case_matches_its_reference(self):
        self.assertGreaterEqual(len(ORACLE_CASES), 30)
        for case in ORACLE_CASES:
            with self.subTest(case=case["case"], calc=case["calc"]):
                got = nonparametric.CALCS[case["calc"]](case["args"])
                project = case.get("project")
                shaped = project(got) if project else got
                self.assertTrue(
                    close(shaped, case["expected"](), case["tolerance"]),
                    "%s: got %r, %s says %r" % (case["case"], shaped, case["reference"],
                                                case["expected"]()))

    def test_every_calculation_has_a_case_on_both_backends(self):
        seen = {(case["calc"], case["backend"]) for case in ORACLE_CASES}
        for address in nonparametric.CALCS:
            self.assertIn((address, "py"), seen, address)
            self.assertIn((address, "sp"), seen, address)


class TestBackendsAgree(unittest.TestCase):
    def test_py_and_sp_agree(self):
        for address, args in (
            ("fn.brain.stats.ks_1samp", {"values": [v - 10.0 for v in A]}),
            ("fn.brain.stats.ks_2samp", {"x": A, "y": B}),
            ("fn.brain.stats.wilcoxon", {"values": ZEROS}),
            ("fn.brain.stats.pearson_p", {"x": A[:34], "y": B}),
        ):
            for alternative in ("two-sided", "less", "greater"):
                with self.subTest(calc=address, alternative=alternative):
                    fn = nonparametric.CALCS[address]
                    py = fn(dict(args, alternative=alternative, backend="py"))
                    sp = fn(dict(args, alternative=alternative, backend="sp"))
                    self.assertTrue(close(sp, py, 1e-9), "%s: %r vs %r" % (address, py, sp))


class TestTheTailsThemselves(unittest.TestCase):
    def test_the_limiting_kolmogorov_tail(self):
        for x in (0.2, 0.5, 1.0, 1.36, 2.0, 3.5):
            with self.subTest(x=x):
                self.assertAlmostEqual(nonparametric.kolmogorov_sf(x),
                                       float(sp_stats.kstwobign.sf(x)), delta=1e-12)

    def test_the_exact_one_sided_tail(self):
        for n in (5, 12, 40, 200):
            for d in (0.05, 0.15, 0.4):
                with self.subTest(n=n, d=d):
                    self.assertAlmostEqual(nonparametric.ksone_sf(d, n),
                                           float(sp_stats.ksone.sf(d, n)), delta=1e-12)

    def test_the_tails_are_bounded_and_monotone(self):
        self.assertEqual(nonparametric.kolmogorov_sf(0.0), 1.0)
        self.assertEqual(nonparametric.ksone_sf(1.0, 10), 0.0)
        self.assertGreater(nonparametric.kolmogorov_sf(0.5), nonparametric.kolmogorov_sf(1.5))


class TestEdges(unittest.TestCase):
    def test_a_sample_that_is_its_own_null_is_not_rejected(self):
        """A is drawn N(10, 3), so standardised it IS the null the test is given."""
        standard = [(v - 10.0) / 3.0 for v in A]
        got = nonparametric.ks_1samp({"values": standard, "dist": "normal"})
        self.assertLess(got["statistic"], 0.25)
        self.assertGreater(got["pvalue"], 0.05)
        shifted = nonparametric.ks_1samp(
            {"values": standard, "dist": "normal", "params": {"mu": 2.0, "sigma": 1.0}})
        self.assertLess(shifted["pvalue"], got["pvalue"])

    def test_a_sample_that_is_not_its_null_is_rejected(self):
        got = nonparametric.ks_1samp({"values": CHI2_LIKE, "dist": "normal"})
        self.assertLess(got["pvalue"], 0.01)

    def test_two_copies_of_one_sample_are_indistinguishable(self):
        got = nonparametric.ks_2samp({"x": A, "y": list(A)})
        self.assertEqual(got["statistic"], 0.0)
        self.assertEqual(got["pvalue"], 1.0)

    def test_an_unknown_alternative_is_refused(self):
        for fn in (nonparametric.ks_1samp, nonparametric.wilcoxon):
            with self.assertRaises(ValueError):
                fn({"values": A, "alternative": "different"})

    def test_an_unknown_backend_is_refused(self):
        with self.assertRaises(ValueError):
            nonparametric.ks_2samp({"x": A, "y": B, "backend": "np"})

    def test_all_zero_differences_are_refused(self):
        with self.assertRaises(ValueError):
            nonparametric.wilcoxon({"values": [0.0] * 8})

    def test_a_paired_signed_rank_needs_equal_lengths(self):
        with self.assertRaises(ValueError):
            nonparametric.wilcoxon({"x": A, "y": B})

    def test_pearson_p_agrees_with_the_coefficient_alone(self):
        import stats.correlation as correlation

        got = nonparametric.pearson_p({"x": A[:34], "y": B})
        self.assertAlmostEqual(got["r"], correlation.pearson({"x": A[:34], "y": B}), delta=1e-12)

    def test_a_perfect_correlation_has_no_room_for_doubt(self):
        straight = [1.0, 2.0, 3.0, 4.0, 5.0]
        got = nonparametric.pearson_p({"x": straight, "y": straight})
        self.assertAlmostEqual(got["r"], 1.0, delta=1e-12)
        self.assertEqual(got["pvalue"], 0.0)

    def test_a_one_sided_pair_adds_to_one(self):
        less = nonparametric.pearson_p({"x": A[:34], "y": B, "alternative": "less"})["pvalue"]
        greater = nonparametric.pearson_p({"x": A[:34], "y": B,
                                           "alternative": "greater"})["pvalue"]
        self.assertAlmostEqual(less + greater, 1.0, delta=1e-12)


class TestJsonAble(unittest.TestCase):
    def test_every_verdict_survives_json(self):
        for case in ORACLE_CASES:
            got = nonparametric.CALCS[case["calc"]](case["args"])
            self.assertEqual(json.loads(json.dumps(got)), got)
            self.assertTrue(0.0 <= got["pvalue"] <= 1.0)
            self.assertTrue(math.isfinite(got["pvalue"]))


class TestBenchCases(unittest.TestCase):
    def test_bench_cases_are_paired_and_runnable(self):
        pairs = {}
        for case in BENCH_CASES:
            pairs.setdefault((case["calc"], case["size"]), set()).add(case["backend"])
        for key, backends in pairs.items():
            self.assertEqual(backends, {"py", "sp"}, "%r is not a comparable pair" % (key,))
        for case in BENCH_CASES[:2]:
            nonparametric.CALCS[case["calc"]](case["make_args"]())


if __name__ == "__main__":
    unittest.main()
