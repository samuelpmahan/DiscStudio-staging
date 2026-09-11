import json
import math
import unittest

import stats.summaries as summaries
from stats.summaries_cases import BENCH_CASES, COUNTS, ORACLE_CASES, OTHER, POSITIVE
from stats.hypothesis_cases import A, SKEWED
from stats.tolerance import close


class TestOracles(unittest.TestCase):
    def test_every_oracle_case_matches_its_reference(self):
        self.assertGreaterEqual(len(ORACLE_CASES), 25)
        for case in ORACLE_CASES:
            with self.subTest(case=case["case"], calc=case["calc"]):
                got = summaries.CALCS[case["calc"]](case["args"])
                project = case.get("project")
                shaped = project(got) if project else got
                self.assertTrue(
                    close(shaped, case["expected"](), case["tolerance"]),
                    "%s: got %r, %s says %r" % (case["case"], shaped, case["reference"],
                                                case["expected"]()))

    def test_every_calculation_has_a_case_on_both_of_its_backends(self):
        seen = {(case["calc"], case["backend"]) for case in ORACLE_CASES}
        for address in summaries.CALCS:
            other = "np" if address.endswith("histogram") else "sp"
            self.assertIn((address, "py"), seen, address)
            self.assertIn((address, other), seen, address)


class TestBackendsAgree(unittest.TestCase):
    def test_py_and_the_library_agree(self):
        for address, args, other in (
            ("fn.brain.stats.trimmed_mean", {"values": A, "proportiontocut": 0.15}, "sp"),
            ("fn.brain.stats.winsorize", {"values": A, "limits": 0.15}, "sp"),
            ("fn.brain.stats.median_abs_deviation", {"values": SKEWED}, "sp"),
            ("fn.brain.stats.gmean", {"values": POSITIVE}, "sp"),
            ("fn.brain.stats.hmean", {"values": POSITIVE}, "sp"),
            ("fn.brain.stats.entropy", {"values": COUNTS, "qk": OTHER}, "sp"),
            ("fn.brain.stats.histogram", {"values": A, "bins": 9}, "np"),
        ):
            with self.subTest(calc=address):
                fn = summaries.CALCS[address]
                self.assertTrue(close(fn(dict(args, backend=other)),
                                      fn(dict(args, backend="py")), 1e-9))


class TestWhatTheyMean(unittest.TestCase):
    def test_trimming_nothing_is_the_mean(self):
        import stats.descriptive as descriptive

        self.assertAlmostEqual(summaries.trimmed_mean({"values": A, "proportiontocut": 0.0}),
                               descriptive.mean({"values": A}), delta=1e-12)

    def test_trimming_moves_the_answer_away_from_an_outlier(self):
        spiked = list(A) + [10000.0]
        plain = math.fsum(spiked) / len(spiked)
        trimmed = summaries.trimmed_mean({"values": spiked, "proportiontocut": 0.1})
        self.assertLess(abs(trimmed - 10.0), abs(plain - 10.0))

    def test_winsorising_keeps_the_length_and_the_order(self):
        got = summaries.winsorize({"values": A, "limits": 0.1})
        self.assertEqual(len(got), len(A))
        self.assertLessEqual(max(got), max(A))
        self.assertGreaterEqual(min(got), min(A))

    def test_the_mad_of_a_normal_sample_is_about_its_sd(self):
        import stats.descriptive as descriptive

        scaled = summaries.median_abs_deviation({"values": A, "scale": "normal"})
        self.assertAlmostEqual(scaled, descriptive.stdev({"values": A, "ddof": 1}), delta=1.0)

    def test_the_three_means_are_ordered(self):
        """harmonic <= geometric <= arithmetic, always."""
        import stats.descriptive as descriptive

        harmonic = summaries.hmean({"values": POSITIVE})
        geometric = summaries.gmean({"values": POSITIVE})
        arithmetic = descriptive.mean({"values": POSITIVE})
        self.assertLessEqual(harmonic, geometric + 1e-12)
        self.assertLessEqual(geometric, arithmetic + 1e-12)

    def test_a_flat_distribution_has_the_most_entropy(self):
        flat = summaries.entropy({"values": [1.0] * 8})
        peaked = summaries.entropy({"values": [100.0] + [1.0] * 7})
        self.assertGreater(flat, peaked)
        self.assertAlmostEqual(flat, math.log(8), delta=1e-12)

    def test_a_divergence_from_itself_is_zero(self):
        self.assertAlmostEqual(summaries.entropy({"values": COUNTS, "qk": COUNTS}), 0.0,
                               delta=1e-12)

    def test_a_divergence_onto_an_impossible_outcome_is_infinite(self):
        self.assertEqual(summaries.entropy({"values": [1.0, 1.0], "qk": [1.0, 0.0]}),
                         float("inf"))

    def test_the_histogram_counts_everything_once(self):
        got = summaries.histogram({"values": A, "bins": 7})
        self.assertEqual(sum(got["counts"]), len(A))
        self.assertEqual(len(got["edges"]), 8)
        self.assertAlmostEqual(
            math.fsum(d * (got["edges"][i + 1] - got["edges"][i])
                      for i, d in enumerate(got["density"])), 1.0, delta=1e-12)

    def test_a_range_drops_what_is_outside_it(self):
        got = summaries.histogram({"values": A, "bins": 4, "range": [10.0, 11.0]})
        self.assertLess(sum(got["counts"]), len(A))


class TestEmpiricalCdf(unittest.TestCase):
    def test_it_ends_at_one_and_rises(self):
        got = summaries.ecdf({"values": A})
        self.assertAlmostEqual(got["cdf"][-1], 1.0, delta=1e-12)
        self.assertEqual(got["n"], len(A))
        for earlier, later in zip(got["cdf"], got["cdf"][1:]):
            self.assertLess(earlier, later)
        for value, tail in zip(got["cdf"], got["sf"]):
            self.assertAlmostEqual(value + tail, 1.0, delta=1e-15)

    def test_ties_share_one_step(self):
        got = summaries.ecdf({"values": [1.0, 2.0, 2.0, 3.0, 3.0, 3.0, 5.0, 8.0]})
        self.assertEqual(got["x"], [1.0, 2.0, 3.0, 5.0, 8.0])
        self.assertAlmostEqual(got["cdf"][2], 6.0 / 8.0, delta=1e-15)

    def test_the_inverse_is_the_smallest_value_that_reaches_the_quantile(self):
        got = summaries.ecdf({"values": [1.0, 2.0, 2.0, 3.0, 3.0, 3.0, 5.0, 8.0],
                              "q": [0.125, 0.5, 0.75, 1.0]})
        self.assertEqual(got["quantiles"], [1.0, 3.0, 3.0, 8.0])

    def test_one_quantile_comes_back_alone(self):
        self.assertEqual(summaries.ecdf({"values": [1.0, 2.0, 3.0], "q": 0.5})["quantiles"],
                         2.0)

    def test_a_quantile_outside_the_range_is_refused(self):
        for q in (0.0, 1.5):
            with self.assertRaises(ValueError):
                summaries.ecdf({"values": A, "q": q})


class TestEdges(unittest.TestCase):
    def test_a_cut_of_a_half_or_more_is_refused(self):
        for cut in (0.5, 0.9):
            with self.assertRaises(ValueError):
                summaries.trimmed_mean({"values": A, "proportiontocut": cut})

    def test_a_non_positive_value_has_no_geometric_or_harmonic_mean(self):
        for fn in (summaries.gmean, summaries.hmean):
            with self.assertRaises(ValueError):
                fn({"values": [1.0, 0.0, 2.0]})

    def test_a_negative_weight_is_refused_by_entropy(self):
        with self.assertRaises(ValueError):
            summaries.entropy({"values": [1.0, -1.0]})

    def test_two_distributions_of_different_length_are_refused(self):
        with self.assertRaises(ValueError):
            summaries.entropy({"values": COUNTS, "qk": OTHER[:3]})

    def test_no_bins_is_refused(self):
        with self.assertRaises(ValueError):
            summaries.histogram({"values": A, "bins": 0})

    def test_an_unknown_backend_is_refused(self):
        with self.assertRaises(ValueError):
            summaries.gmean({"values": POSITIVE, "backend": "np"})
        with self.assertRaises(ValueError):
            summaries.histogram({"values": A, "backend": "sp"})

    def test_a_flat_sample_still_has_a_histogram(self):
        got = summaries.histogram({"values": [4.0] * 5, "bins": 3})
        self.assertEqual(sum(got["counts"]), 5)


class TestJsonAble(unittest.TestCase):
    def test_every_result_survives_json(self):
        for case in ORACLE_CASES:
            got = summaries.CALCS[case["calc"]](case["args"])
            self.assertEqual(json.loads(json.dumps(got)), got)


class TestBenchCases(unittest.TestCase):
    def test_bench_cases_are_paired_and_runnable(self):
        pairs = {}
        for case in BENCH_CASES:
            pairs.setdefault((case["calc"], case["size"]), set()).add(case["backend"])
        for key, backends in pairs.items():
            self.assertEqual(len(backends), 2, "%r is not a comparable pair" % (key,))
        for case in BENCH_CASES[:3]:
            summaries.CALCS[case["calc"]](case["make_args"]())


if __name__ == "__main__":
    unittest.main()
