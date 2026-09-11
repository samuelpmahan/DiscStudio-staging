import json
import math
import unittest

import stats.intervals as intervals
from stats.intervals_cases import (BENCH_CASES, GROUPS, LEDGER, ORACLE_CASES, OTHER, SAMPLE,
                                   TABLE, Ledger, brute_bootstrap)
from stats.tolerance import close


class TestOracles(unittest.TestCase):
    def test_every_oracle_case_matches_its_reference(self):
        self.assertGreaterEqual(len(ORACLE_CASES), 18)
        for case in ORACLE_CASES:
            with self.subTest(case=case["case"], calc=case["calc"]):
                args = dict(case["args"])
                if case["calc"].startswith("oc."):
                    args["effects"] = Ledger(LEDGER)
                got = intervals.CALCS[case["calc"]](args)
                project = case.get("project")
                shaped = project(got) if project else got
                self.assertTrue(
                    close(shaped, case["expected"](), case["tolerance"]),
                    "%s: got %r, %s says %r"
                    % (case["case"], shaped, case["reference"], case["expected"]()))

    def test_every_calculation_has_a_case(self):
        covered = {case["calc"] for case in ORACLE_CASES}
        self.assertEqual(set(intervals.CALCS) - covered, set())


class TestIntervals(unittest.TestCase):
    def test_the_interval_brackets_the_estimate(self):
        for args, address in (({"values": SAMPLE}, "fn.brain.stats.ci_mean"),
                              ({"x": SAMPLE, "y": OTHER}, "fn.brain.stats.ci_diff_means"),
                              ({"successes": 30, "n": 100}, "fn.brain.stats.ci_proportion"),
                              ({"values": SAMPLE}, "fn.brain.stats.ci_variance")):
            with self.subTest(calc=address):
                got = intervals.CALCS[address](args)
                self.assertLessEqual(got["low"], got["estimate"])
                self.assertLessEqual(got["estimate"], got["high"])

    def test_a_higher_level_is_a_wider_interval(self):
        narrow = intervals.ci_mean({"values": SAMPLE, "level": 0.80})
        wide = intervals.ci_mean({"values": SAMPLE, "level": 0.99})
        self.assertLess(wide["low"], narrow["low"])
        self.assertGreater(wide["high"], narrow["high"])

    def test_wilson_stays_inside_zero_and_one_where_wald_would_not(self):
        wilson = intervals.ci_proportion({"successes": 0, "n": 20, "method": "wilson"})
        self.assertGreaterEqual(wilson["low"], 0.0)
        self.assertGreater(wilson["high"], 0.0)
        wald = intervals.ci_proportion({"successes": 0, "n": 20, "method": "wald"})
        self.assertEqual(wald["low"], 0.0)
        self.assertEqual(wald["high"], 0.0)

    def test_a_level_outside_the_unit_interval_is_refused(self):
        for level in (0.0, 1.0, 1.5):
            with self.assertRaises(ValueError):
                intervals.ci_mean({"values": SAMPLE, "level": level})

    def test_impossible_counts_are_refused(self):
        for args in ({"successes": -1, "n": 10}, {"successes": 11, "n": 10},
                     {"successes": 1, "n": 0}):
            with self.assertRaises(ValueError):
                intervals.ci_proportion(args)


class TestBootstrapIsAnEffect(unittest.TestCase):
    def test_bootstrap_is_an_oc_address(self):
        self.assertTrue(intervals.BOOTSTRAP.address.startswith("oc."))

    def test_it_asks_the_handle_for_exactly_the_draws_it_needs(self):
        effects = Ledger(LEDGER)
        intervals.bootstrap({"values": SAMPLE, "resamples": 50, "effects": effects})
        self.assertEqual(effects.asked, [50 * len(SAMPLE)])

    def test_the_same_ledger_is_the_same_interval(self):
        first = intervals.bootstrap({"values": SAMPLE, "resamples": 60,
                                     "effects": Ledger(LEDGER)})
        second = intervals.bootstrap({"values": SAMPLE, "resamples": 60,
                                      "effects": Ledger(LEDGER)})
        self.assertEqual(first, second)

    def test_the_basic_interval_is_the_percentile_one_reflected(self):
        percentile = intervals.bootstrap({"values": SAMPLE, "resamples": 80,
                                          "effects": Ledger(LEDGER)})
        basic = intervals.bootstrap({"values": SAMPLE, "resamples": 80, "method": "basic",
                                     "effects": Ledger(LEDGER)})
        self.assertAlmostEqual(basic["low"], 2.0 * percentile["estimate"] - percentile["high"],
                               delta=1e-12)

    def test_it_brackets_the_sample_mean(self):
        got = intervals.bootstrap({"values": SAMPLE, "resamples": 200, "effects": Ledger(LEDGER)})
        self.assertLess(got["low"], got["estimate"])
        self.assertGreater(got["high"], got["estimate"])

    def test_a_second_opinion_on_the_same_ledger(self):
        got = intervals.bootstrap({"values": SAMPLE, "statistic": "median", "resamples": 120,
                                   "effects": Ledger(LEDGER)})
        reference = brute_bootstrap(SAMPLE, LEDGER, "median", 120, 0.95)
        self.assertTrue(close({"low": got["low"], "high": got["high"]}, reference, 1e-9))

    def test_without_the_handle_it_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            intervals.bootstrap({"values": SAMPLE})
        self.assertIn("effects", str(caught.exception))

    def test_an_unknown_statistic_names_the_ones_there_are(self):
        with self.assertRaises(ValueError) as caught:
            intervals.bootstrap({"values": SAMPLE, "statistic": "mode",
                                 "effects": Ledger(LEDGER)})
        self.assertIn("trimmed_mean", str(caught.exception))

    def test_too_few_resamples_are_refused(self):
        with self.assertRaises(ValueError):
            intervals.bootstrap({"values": SAMPLE, "resamples": 1, "effects": Ledger(LEDGER)})


class TestEffectSizes(unittest.TestCase):
    def test_identical_samples_have_no_effect(self):
        self.assertAlmostEqual(intervals.cohens_d({"x": SAMPLE, "y": list(SAMPLE)}), 0.0,
                               delta=1e-12)
        self.assertAlmostEqual(intervals.rank_biserial({"x": SAMPLE, "y": list(SAMPLE)}), 0.0,
                               delta=1e-12)

    def test_hedges_g_is_smaller_than_cohens_d(self):
        d = intervals.cohens_d({"x": SAMPLE, "y": OTHER})
        g = intervals.hedges_g({"x": SAMPLE, "y": OTHER})
        self.assertLess(abs(g), abs(d))

    def test_eta_and_omega_are_between_zero_and_one(self):
        for address in ("fn.brain.stats.eta_squared", "fn.brain.stats.omega_squared"):
            value = intervals.CALCS[address]({"groups": GROUPS})
            self.assertGreaterEqual(value, -1.0)
            self.assertLessEqual(value, 1.0)

    def test_omega_is_no_larger_than_eta(self):
        self.assertLessEqual(intervals.omega_squared({"groups": GROUPS}),
                             intervals.eta_squared({"groups": GROUPS}))

    def test_cramers_v_is_between_zero_and_one(self):
        value = intervals.cramers_v({"table": TABLE})
        self.assertGreaterEqual(value, 0.0)
        self.assertLessEqual(value, 1.0)

    def test_a_flat_sample_has_no_effect_size(self):
        with self.assertRaises(ValueError):
            intervals.cohens_d({"x": [3.0] * 6, "y": [3.0] * 6})
        with self.assertRaises(ValueError):
            intervals.glass_delta({"x": SAMPLE, "y": [3.0] * 6})

    def test_one_group_is_refused(self):
        with self.assertRaises(ValueError):
            intervals.eta_squared({"groups": [SAMPLE]})


class TestJsonAble(unittest.TestCase):
    def test_every_result_survives_json(self):
        for case in ORACLE_CASES:
            args = dict(case["args"])
            if case["calc"].startswith("oc."):
                args["effects"] = Ledger(LEDGER)
            got = intervals.CALCS[case["calc"]](args)
            self.assertEqual(json.loads(json.dumps(got)), got)


class TestBenchCases(unittest.TestCase):
    def test_bench_cases_are_runnable(self):
        for case in BENCH_CASES:
            intervals.CALCS[case["calc"]](case["make_args"]())


if __name__ == "__main__":
    unittest.main()
