import json
import unittest

import stats.hypothesis as hypothesis
from stats.hypothesis_cases import (A, B, GROUPS, ORACLE_CASES, BENCH_CASES, SKEWED, TABLE,
                                    SHAPIRO_TOLERANCE)
from stats.tolerance import close


class TestOracles(unittest.TestCase):
    def test_every_oracle_case_matches_its_reference(self):
        self.assertGreaterEqual(len(ORACLE_CASES), 30)
        for case in ORACLE_CASES:
            with self.subTest(case=case["case"], calc=case["calc"]):
                got = hypothesis.CALCS[case["calc"]](case["args"])
                self.assertTrue(
                    close(got, case["expected"](), case["tolerance"]),
                    "%s: got %r, %s says %r" % (case["case"], got, case["reference"],
                                                case["expected"]()))

    def test_every_test_has_a_case_on_both_backends(self):
        seen = {(case["calc"], case["backend"]) for case in ORACLE_CASES}
        for address in hypothesis.CALCS:
            self.assertIn((address, "py"), seen, address)
            self.assertIn((address, "sp"), seen, address)

    def test_the_loose_tolerance_is_only_shapiro_and_is_recorded(self):
        for case in ORACLE_CASES:
            if case["tolerance"] > 1e-9:
                self.assertEqual(case["calc"], "fn.brain.stats.shapiro")
                self.assertEqual(case["tolerance"], SHAPIRO_TOLERANCE)


class TestBackendsAgree(unittest.TestCase):
    def test_py_and_sp_agree(self):
        for address, args, tolerance in (
            ("fn.brain.stats.ttest_1samp", {"values": A, "popmean": 9.5}, 1e-9),
            ("fn.brain.stats.ttest_ind", {"x": A, "y": B}, 1e-9),
            ("fn.brain.stats.ttest_ind", {"x": A, "y": B, "equal_var": False}, 1e-9),
            ("fn.brain.stats.ttest_rel", {"x": A[:34], "y": B}, 1e-9),
            ("fn.brain.stats.chisquare", {"observed": [9, 11, 14, 6]}, 1e-9),
            ("fn.brain.stats.chi2_contingency", {"table": TABLE}, 1e-9),
            ("fn.brain.stats.f_oneway", {"groups": GROUPS}, 1e-9),
            ("fn.brain.stats.mannwhitneyu", {"x": A, "y": B}, 1e-9),
            ("fn.brain.stats.shapiro", {"values": SKEWED}, SHAPIRO_TOLERANCE),
        ):
            with self.subTest(calc=address, args=sorted(args)):
                fn = hypothesis.CALCS[address]
                py = fn(dict(args, backend="py"))
                sp = fn(dict(args, backend="sp"))
                self.assertTrue(close(sp, py, tolerance), "%s: %r vs %r" % (address, py, sp))


class TestEdges(unittest.TestCase):
    def test_unknown_alternative_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            hypothesis.ttest_1samp({"values": A, "alternative": "bigger"})
        self.assertIn("two-sided", str(caught.exception))

    def test_unknown_backend_is_refused(self):
        with self.assertRaises(ValueError):
            hypothesis.ttest_ind({"x": A, "y": B, "backend": "np"})

    def test_a_flat_sample_has_no_t(self):
        with self.assertRaises(ValueError):
            hypothesis.ttest_1samp({"values": [3.0] * 8})

    def test_a_paired_test_needs_equal_lengths(self):
        with self.assertRaises(ValueError) as caught:
            hypothesis.ttest_rel({"x": A, "y": B})
        self.assertIn("equal lengths", str(caught.exception))

    def test_a_goodness_of_fit_needs_positive_expectations(self):
        with self.assertRaises(ValueError):
            hypothesis.chisquare({"observed": [4, 5], "expected": [0.0, 9.0]})

    def test_independence_needs_a_two_by_two_at_least(self):
        with self.assertRaises(ValueError):
            hypothesis.chi2_contingency({"table": [[3, 4, 5]]})

    def test_ragged_tables_are_refused(self):
        with self.assertRaises(ValueError):
            hypothesis.chi2_contingency({"table": [[1, 2], [3, 4, 5]]})

    def test_anova_needs_two_groups(self):
        with self.assertRaises(ValueError):
            hypothesis.f_oneway({"groups": [A]})

    def test_shapiro_needs_three_observations(self):
        with self.assertRaises(ValueError):
            hypothesis.shapiro({"values": [1.0, 2.0]})

    def test_yates_correction_can_be_turned_off(self):
        table = [[10, 20], [6, 9]]
        with_yates = hypothesis.chi2_contingency({"table": table})["statistic"]
        without = hypothesis.chi2_contingency({"table": table, "correction": False})["statistic"]
        self.assertLess(with_yates, without)

    def test_a_one_sided_pair_adds_to_one(self):
        less = hypothesis.ttest_ind({"x": A, "y": B, "alternative": "less"})["pvalue"]
        greater = hypothesis.ttest_ind({"x": A, "y": B, "alternative": "greater"})["pvalue"]
        self.assertAlmostEqual(less + greater, 1.0, delta=1e-12)


class TestJsonAble(unittest.TestCase):
    def test_every_verdict_survives_json(self):
        for case in ORACLE_CASES:
            got = hypothesis.CALCS[case["calc"]](case["args"])
            self.assertEqual(json.loads(json.dumps(got)), got)
            self.assertIn("statistic", got)
            self.assertIn("pvalue", got)
            self.assertTrue(0.0 <= got["pvalue"] <= 1.0)


class TestBenchCases(unittest.TestCase):
    def test_bench_cases_are_paired_and_runnable(self):
        pairs = {}
        for case in BENCH_CASES:
            pairs.setdefault((case["calc"], case["size"]), set()).add(case["backend"])
        for key, backends in pairs.items():
            self.assertEqual(backends, {"py", "sp"}, "%r is not a comparable pair" % (key,))
        sample = BENCH_CASES[0]
        hypothesis.CALCS[sample["calc"]](sample["make_args"]())


if __name__ == "__main__":
    unittest.main()
