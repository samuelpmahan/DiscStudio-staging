import json
import unittest

import stats.comparisons as comparisons
from stats.comparisons_cases import (BENCH_CASES, ORACLE_CASES, PVALUES, SPREADS, TABLE22,
                                     brute_bonferroni, brute_holm)
from stats.hypothesis_cases import GROUPS
from stats.tolerance import close


class TestOracles(unittest.TestCase):
    def test_every_oracle_case_matches_its_reference(self):
        self.assertGreaterEqual(len(ORACLE_CASES), 30)
        for case in ORACLE_CASES:
            with self.subTest(case=case["case"], calc=case["calc"]):
                got = comparisons.CALCS[case["calc"]](case["args"])
                project = case.get("project")
                shaped = project(got) if project else got
                self.assertTrue(
                    close(shaped, case["expected"](), case["tolerance"]),
                    "%s: got %r, %s says %r" % (case["case"], shaped, case["reference"],
                                                case["expected"]()))

    def test_every_calculation_has_a_case_on_both_backends(self):
        seen = {(case["calc"], case["backend"]) for case in ORACLE_CASES}
        for address in comparisons.CALCS:
            self.assertIn((address, "py"), seen, address)
            self.assertIn((address, "sp"), seen, address)


class TestBackendsAgree(unittest.TestCase):
    def test_py_and_sp_agree(self):
        for address, args in (
            ("fn.brain.stats.kruskal", {"groups": GROUPS}),
            ("fn.brain.stats.levene", {"groups": SPREADS}),
            ("fn.brain.stats.bartlett", {"groups": SPREADS}),
            ("fn.brain.stats.binom_test", {"successes": 9, "n": 25, "p": 0.4}),
            ("fn.brain.stats.fisher_exact", {"table": TABLE22}),
            ("fn.brain.stats.multipletests", {"pvalues": PVALUES}),
        ):
            with self.subTest(calc=address):
                fn = comparisons.CALCS[address]
                self.assertTrue(close(fn(dict(args, backend="sp")),
                                      fn(dict(args, backend="py")), 1e-9))


class TestTheShapeOfTheAnswers(unittest.TestCase):
    def test_kruskal_finds_a_difference_that_is_there(self):
        apart = [[1.0, 2.0, 3.0, 4.0, 5.0], [21.0, 22.0, 23.0, 24.0, 25.0]]
        self.assertLess(comparisons.kruskal({"groups": apart})["pvalue"], 0.05)

    def test_levene_and_bartlett_see_unequal_spread(self):
        for address in ("fn.brain.stats.levene", "fn.brain.stats.bartlett"):
            got = comparisons.CALCS[address]({"groups": SPREADS})
            self.assertLess(got["pvalue"], 0.05, address)

    def test_bartlett_is_the_more_confident_of_the_two(self):
        self.assertLess(comparisons.bartlett({"groups": SPREADS})["pvalue"],
                        comparisons.levene({"groups": SPREADS})["pvalue"])

    def test_a_fair_coin_is_not_rejected(self):
        self.assertGreater(comparisons.binom_test({"successes": 20, "n": 40})["pvalue"], 0.5)

    def test_a_one_sided_pair_covers_the_whole_line(self):
        less = comparisons.binom_test({"successes": 13, "n": 40, "alternative": "less"})["pvalue"]
        greater = comparisons.binom_test({"successes": 13, "n": 40,
                                          "alternative": "greater"})["pvalue"]
        self.assertGreater(less + greater, 1.0)

    def test_fisher_on_a_table_with_no_association(self):
        got = comparisons.fisher_exact({"table": [[10, 10], [10, 10]]})
        self.assertEqual(got["pvalue"], 1.0)
        self.assertAlmostEqual(got["odds_ratio"], 1.0, delta=1e-12)


class TestCorrections(unittest.TestCase):
    def test_the_three_corrections_are_ordered(self):
        """bonferroni is never smaller than holm, and holm never smaller than BH."""
        by_method = {method: comparisons.multipletests(
            {"pvalues": PVALUES, "method": method})["adjusted"] for method in comparisons.METHODS}
        for bonf, holm, bh in zip(by_method["bonferroni"], by_method["holm"],
                                  by_method["benjamini-hochberg"]):
            self.assertGreaterEqual(bonf + 1e-12, holm)
            self.assertGreaterEqual(holm + 1e-12, bh)

    def test_bonferroni_and_holm_match_the_published_definitions(self):
        self.assertTrue(close(comparisons.multipletests(
            {"pvalues": PVALUES, "method": "bonferroni"})["adjusted"],
            brute_bonferroni(PVALUES)))
        self.assertTrue(close(comparisons.multipletests(
            {"pvalues": PVALUES, "method": "holm"})["adjusted"], brute_holm(PVALUES)))

    def test_an_adjusted_p_value_is_never_smaller_than_the_raw_one(self):
        for method in comparisons.METHODS:
            adjusted = comparisons.multipletests({"pvalues": PVALUES, "method": method})
            for raw, fixed in zip(PVALUES, adjusted["adjusted"]):
                self.assertGreaterEqual(fixed + 1e-12, raw, method)

    def test_one_p_value_is_left_alone(self):
        for method in comparisons.METHODS:
            got = comparisons.multipletests({"pvalues": [0.03], "method": method})
            self.assertAlmostEqual(got["adjusted"][0], 0.03, delta=1e-12)

    def test_the_rejections_are_counted(self):
        got = comparisons.multipletests({"pvalues": PVALUES, "alpha": 0.05})
        self.assertEqual(got["rejections"], sum(1 for one in got["rejected"] if one))
        self.assertGreater(got["rejections"], 0)

    def test_an_unknown_method_names_the_ones_there_are(self):
        with self.assertRaises(ValueError) as caught:
            comparisons.multipletests({"pvalues": PVALUES, "method": "sidak"})
        self.assertIn("benjamini-hochberg", str(caught.exception))


class TestEdges(unittest.TestCase):
    def test_one_group_is_refused(self):
        for address in ("fn.brain.stats.kruskal", "fn.brain.stats.levene",
                        "fn.brain.stats.bartlett"):
            with self.assertRaises(ValueError):
                comparisons.CALCS[address]({"groups": [GROUPS[0]]})

    def test_a_flat_group_has_no_bartlett(self):
        with self.assertRaises(ValueError):
            comparisons.bartlett({"groups": [[2.0] * 5, [1.0, 2.0, 3.0, 4.0, 5.0]]})

    def test_a_table_that_is_not_two_by_two_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            comparisons.fisher_exact({"table": [[1, 2, 3], [4, 5, 6]]})
        self.assertIn("2x2", str(caught.exception))

    def test_impossible_counts_are_refused(self):
        for args in ({"successes": -1, "n": 10}, {"successes": 11, "n": 10},
                     {"successes": 1, "n": 0}, {"successes": 1, "n": 10, "p": 1.5}):
            with self.assertRaises(ValueError):
                comparisons.binom_test(args)

    def test_an_empty_family_is_refused(self):
        with self.assertRaises(ValueError):
            comparisons.multipletests({"pvalues": []})

    def test_a_p_value_outside_the_unit_interval_is_refused(self):
        with self.assertRaises(ValueError):
            comparisons.multipletests({"pvalues": [0.5, 1.2]})

    def test_an_unknown_backend_is_refused(self):
        with self.assertRaises(ValueError):
            comparisons.kruskal({"groups": GROUPS, "backend": "np"})


class TestJsonAble(unittest.TestCase):
    def test_every_result_survives_json(self):
        for case in ORACLE_CASES:
            got = comparisons.CALCS[case["calc"]](case["args"])
            self.assertEqual(json.loads(json.dumps(got)), got)


class TestBenchCases(unittest.TestCase):
    def test_bench_cases_are_paired_and_runnable(self):
        pairs = {}
        for case in BENCH_CASES:
            pairs.setdefault((case["calc"], case["size"]), set()).add(case["backend"])
        for key, backends in pairs.items():
            self.assertEqual(backends, {"py", "sp"}, "%r is not a comparable pair" % (key,))
        for case in BENCH_CASES[:3]:
            comparisons.CALCS[case["calc"]](case["make_args"]())


if __name__ == "__main__":
    unittest.main()
