import json
import math
import unittest

from harness import close

import data.timeseries as timeseries
from data.timeseries_cases import (BENCH_CASES, BIG, FLATISH, ORACLE_CASES, SERIES, SHORT,
                                   brute_ar)


def agrees(got, expected, tolerance=1e-9):
    return close(got, expected, tolerance)[0]


class TestOracles(unittest.TestCase):
    def test_every_oracle_case_matches_its_reference(self):
        self.assertGreaterEqual(len(ORACLE_CASES), 40)
        for case in ORACLE_CASES:
            with self.subTest(case=case["case"], calc=case["calc"]):
                got = timeseries.CALCS[case["calc"]](case["args"])
                project = case.get("project")
                shaped = project(got) if project else got
                self.assertTrue(
                    agrees(shaped, case["expected"](), case["tolerance"]),
                    "%s: got %r, %s says %r"
                    % (case["case"], shaped, case["reference"], case["expected"]()))

    def test_every_calculation_has_a_case(self):
        covered = {case["calc"] for case in ORACLE_CASES}
        self.assertEqual(set(timeseries.CALCS) - covered,
                         {"fn.brain.data.holt", "fn.brain.data.ar_forecast"})

    def test_the_three_rolling_engines_all_have_cases(self):
        seen = {case["backend"] for case in ORACLE_CASES
                if case["calc"] == "fn.brain.data.rolling"}
        self.assertEqual(seen, {"py", "np", "cumsum"})

    def test_every_case_names_a_reference_and_a_backend(self):
        for case in ORACLE_CASES:
            self.assertTrue(case["reference"])
            self.assertIn(case["backend"], ("py", "np", "cumsum"))


class TestBackendsAgree(unittest.TestCase):
    def test_py_and_np_agree(self):
        for address, args in (
            ("fn.brain.data.rolling", {"values": SERIES, "window": 9, "fn": "std"}),
            ("fn.brain.data.acf", {"values": SERIES, "nlags": 15}),
            ("fn.brain.data.pacf", {"values": SERIES, "nlags": 6}),
            ("fn.brain.data.ar_fit", {"values": SERIES, "order": 3}),
            ("fn.brain.data.seasonal_decompose", {"values": SERIES, "period": 5}),
        ):
            with self.subTest(calc=address):
                fn = timeseries.CALCS[address]
                py = fn(dict(args, backend="py"))
                np_ = fn(dict(args, backend="np"))
                self.assertTrue(agrees(np_, py, 1e-8), "%s: %r vs %r" % (address, py, np_))


class TestRolling(unittest.TestCase):
    def test_the_window_is_none_until_it_fills(self):
        got = timeseries.rolling({"values": SHORT, "window": 4})
        self.assertEqual(got[:3], [None, None, None])
        self.assertIsNotNone(got[3])

    def test_min_periods_lets_it_start_early(self):
        got = timeseries.rolling({"values": SHORT, "window": 4, "min_periods": 1})
        self.assertEqual(got[0], SHORT[0])

    def test_a_window_of_one_is_the_series_itself(self):
        self.assertEqual(timeseries.rolling({"values": SHORT, "window": 1}), SHORT)

    def test_holes_are_skipped_not_counted(self):
        got = timeseries.rolling({"values": [1.0, None, 3.0, 5.0], "window": 3,
                                  "min_periods": 2, "fn": "mean"})
        self.assertIsNone(got[0])
        self.assertAlmostEqual(got[2], 2.0)

    def test_the_cumsum_engine_agrees_with_the_slice_engines_everywhere(self):
        holes = [v if i % 5 else None for i, v in enumerate(SERIES)]
        for values in (SERIES, holes):
            for kind in ("count", "sum", "mean", "var", "std"):
                for width, least, centred in ((7, 7, False), (30, 1, False), (5, 3, True)):
                    with self.subTest(kind=kind, window=width, center=centred,
                                      holes=values is holes):
                        args = {"values": values, "window": width, "fn": kind,
                                "min_periods": least, "center": centred}
                        self.assertTrue(agrees(
                            timeseries.rolling(dict(args, backend="cumsum")),
                            timeseries.rolling(dict(args, backend="py")), 1e-9))

    def test_the_cumsum_engine_refuses_what_it_cannot_do_in_one_pass(self):
        for kind in ("min", "max", "median"):
            with self.subTest(fn=kind):
                with self.assertRaises(ValueError) as caught:
                    timeseries.rolling({"values": SERIES, "fn": kind, "backend": "cumsum"})
                self.assertIn("whole-window form", str(caught.exception))

    def test_the_cumsum_variance_holds_up_on_a_series_with_a_big_offset(self):
        """the shift-by-the-mean trick is what this is measuring."""
        offset = [v + 1e7 for v in SERIES]
        self.assertTrue(agrees(
            timeseries.rolling({"values": offset, "window": 12, "fn": "var",
                                "backend": "cumsum"}),
            timeseries.rolling({"values": offset, "window": 12, "fn": "var"}), 1e-9))

    def test_an_unknown_fn_names_the_ones_there_are(self):
        with self.assertRaises(ValueError) as caught:
            timeseries.rolling({"values": SHORT, "fn": "skew"})
        self.assertIn("median", str(caught.exception))

    def test_bad_widths_are_refused(self):
        for args in ({"values": SHORT, "window": 0},
                     {"values": SHORT, "window": 3, "min_periods": 0},
                     {"values": SHORT, "window": 3, "min_periods": 9}):
            with self.assertRaises(ValueError):
                timeseries.rolling(args)


class TestEwmaAndCrossCorrelation(unittest.TestCase):
    def test_alpha_one_is_the_series_itself(self):
        self.assertTrue(agrees(timeseries.ewma({"values": SHORT, "alpha": 1.0}), SHORT, 1e-12))

    def test_a_span_is_an_alpha(self):
        self.assertTrue(agrees(timeseries.ewma({"values": SHORT, "span": 9}),
                               timeseries.ewma({"values": SHORT, "alpha": 2.0 / 10.0}), 1e-12))

    def test_the_adjusted_and_unadjusted_forms_meet_in_the_end(self):
        adjusted = timeseries.ewma({"values": SERIES, "alpha": 0.5})
        plain = timeseries.ewma({"values": SERIES, "alpha": 0.5, "adjust": False})
        self.assertNotAlmostEqual(adjusted[1], plain[1], delta=1e-12)
        self.assertAlmostEqual(adjusted[-1], plain[-1], delta=1e-9)

    def test_an_ewma_of_a_constant_is_that_constant(self):
        self.assertTrue(agrees(timeseries.ewma({"values": [3.0] * 12}), [3.0] * 12, 1e-12))
        self.assertTrue(agrees(
            [v for v in timeseries.ewma({"values": [3.0] * 12, "fn": "var"}) if v is not None],
            [0.0] * len([v for v in timeseries.ewma({"values": [3.0] * 12, "fn": "var"})
                         if v is not None]), 1e-12))

    def test_the_ewma_parameters_are_checked(self):
        for args in ({"values": SHORT, "alpha": 0.0}, {"values": SHORT, "alpha": 1.5},
                     {"values": SHORT, "span": 0.5}, {"values": SHORT, "fn": "median"}):
            with self.assertRaises(ValueError):
                timeseries.ewma(args)

    def test_a_series_cross_correlated_with_itself_starts_at_one(self):
        got = timeseries.cross_correlation({"x": SERIES, "y": SERIES, "nlags": 4})
        self.assertAlmostEqual(got[0], 1.0, delta=1e-12)
        self.assertTrue(all(abs(v) <= 1.0 + 1e-12 for v in got))

    def test_it_is_the_acf_when_the_two_series_are_the_same(self):
        self.assertTrue(agrees(
            timeseries.cross_correlation({"x": SERIES, "y": SERIES, "nlags": 6}),
            timeseries.acf({"values": SERIES, "nlags": 6}), 1e-12))

    def test_a_flat_series_has_no_cross_correlation(self):
        with self.assertRaises(ValueError):
            timeseries.cross_correlation({"x": [2.0] * 8, "y": SERIES[:8]})

    def test_unequal_lengths_are_refused(self):
        with self.assertRaises(ValueError):
            timeseries.cross_correlation({"x": SERIES, "y": SERIES[:-1]})


class TestTheSeriesTransforms(unittest.TestCase):
    def test_pct_change_and_difference_are_the_same_shape(self):
        changed = timeseries.pct_change({"values": SHORT})
        differenced = timeseries.difference({"values": SHORT})
        self.assertEqual(len(changed), len(differenced))
        self.assertIsNone(changed[0])
        for value, delta, base in zip(changed[1:], differenced[1:], SHORT[:-1]):
            self.assertAlmostEqual(value, delta / base, delta=1e-12)

    def test_a_zero_base_has_no_proportional_change(self):
        self.assertEqual(timeseries.pct_change({"values": [0.0, 5.0, 10.0]}),
                         [None, None, 1.0])

    def test_pct_change_needs_a_positive_period(self):
        with self.assertRaises(ValueError):
            timeseries.pct_change({"values": SHORT, "periods": 0})

    def test_an_expanding_window_is_a_rolling_window_as_wide_as_the_series(self):
        for kind in ("count", "sum", "mean", "var", "std"):
            with self.subTest(fn=kind):
                self.assertTrue(agrees(
                    timeseries.expanding({"values": SHORT, "fn": kind}),
                    timeseries.rolling({"values": SHORT, "window": len(SHORT), "fn": kind,
                                        "min_periods": 1}), 1e-12))

    def test_every_engine_expands_the_same_way(self):
        for kind in ("count", "sum", "mean", "var", "std"):
            base = timeseries.expanding({"values": SERIES, "fn": kind})
            for backend in ("np", "cumsum"):
                with self.subTest(fn=kind, backend=backend):
                    self.assertTrue(agrees(
                        timeseries.expanding({"values": SERIES, "fn": kind,
                                              "backend": backend}), base, 1e-9))

    def test_the_last_expanding_value_is_the_whole_series(self):
        import math

        self.assertAlmostEqual(timeseries.expanding({"values": SHORT, "fn": "mean"})[-1],
                               math.fsum(SHORT) / len(SHORT), delta=1e-12)

    def test_interpolation_fills_the_inside_and_leaves_the_ends(self):
        holes = [1.0, None, None, 4.0, None, 6.0, None]
        self.assertEqual(timeseries.interpolate({"values": holes}),
                         [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, None])

    def test_the_ends_can_be_carried_out(self):
        holes = [None, 2.0, None, 4.0, None]
        self.assertEqual(timeseries.interpolate({"values": holes, "limit_direction": "both"}),
                         [2.0, 2.0, 3.0, 4.0, 4.0])
        self.assertIsNone(timeseries.interpolate({"values": holes,
                                                  "limit_direction": "forward"})[0])

    def test_it_interpolates_along_the_positions_it_is_given(self):
        self.assertEqual(timeseries.interpolate({"values": [0.0, None, 10.0],
                                                 "x": [0.0, 9.0, 10.0]}),
                         [0.0, 9.0, 10.0])

    def test_a_series_of_nothing_but_holes_is_refused(self):
        with self.assertRaises(ValueError):
            timeseries.interpolate({"values": [None, None]})

    def test_an_unknown_limit_direction_is_refused(self):
        with self.assertRaises(ValueError):
            timeseries.interpolate({"values": [1.0, None, 3.0], "limit_direction": "outward"})


class TestDifferencing(unittest.TestCase):
    def test_difference_and_integrate_are_inverses(self):
        differenced = timeseries.difference({"values": SHORT})
        back = timeseries.integrate({"values": differenced[1:], "start": SHORT[0]})
        self.assertTrue(agrees(back, SHORT[1:], 1e-12))

    def test_order_zero_is_refused(self):
        with self.assertRaises(ValueError):
            timeseries.difference({"values": SHORT, "order": 0})

    def test_a_hole_is_refused_by_a_difference(self):
        with self.assertRaises(ValueError):
            timeseries.difference({"values": [1.0, None, 3.0]})


class TestSmoothers(unittest.TestCase):
    def test_alpha_one_follows_the_series_exactly(self):
        got = timeseries.ses({"values": SHORT, "alpha": 1.0})
        self.assertAlmostEqual(got["level"], SHORT[-1], delta=1e-12)

    def test_a_smaller_alpha_smooths_a_flat_noisy_series_better(self):
        slow = timeseries.ses({"values": FLATISH, "alpha": 0.05})["sse"]
        fast = timeseries.ses({"values": FLATISH, "alpha": 0.9})["sse"]
        self.assertLess(slow, fast)

    def test_a_bigger_alpha_follows_a_trend_better(self):
        trending = [3.0 * i for i in range(30)]
        slow = timeseries.ses({"values": trending, "alpha": 0.05})["sse"]
        fast = timeseries.ses({"values": trending, "alpha": 0.9})["sse"]
        self.assertGreater(slow, fast)

    def test_holt_carries_a_straight_line_forward(self):
        straight = [2.0 * i + 1.0 for i in range(20)]
        got = timeseries.holt({"values": straight, "alpha": 0.8, "beta": 0.8, "horizon": 3})
        self.assertAlmostEqual(got["trend"], 2.0, delta=1e-6)
        self.assertAlmostEqual(got["forecast"][0], straight[-1] + 2.0, delta=1e-5)
        self.assertAlmostEqual(got["sse"], 0.0, delta=1e-15)

    def test_damping_pulls_the_forecast_in(self):
        straight = [2.0 * i + 1.0 for i in range(20)]
        plain = timeseries.holt({"values": straight, "alpha": 0.8, "beta": 0.8, "horizon": 5})
        damped = timeseries.holt({"values": straight, "alpha": 0.8, "beta": 0.8, "phi": 0.7,
                                  "horizon": 5})
        self.assertLess(damped["forecast"][-1], plain["forecast"][-1])

    def test_the_smoothing_parameters_are_checked(self):
        for args in ({"values": SHORT, "alpha": 0.0}, {"values": SHORT, "alpha": 1.5}):
            with self.assertRaises(ValueError):
                timeseries.ses(args)
        for args in ({"values": SHORT, "beta": 0.0}, {"values": SHORT, "phi": 1.4}):
            with self.assertRaises(ValueError):
                timeseries.holt(args)


class TestDecomposition(unittest.TestCase):
    def test_the_additive_parts_add_back_up(self):
        got = timeseries.seasonal_decompose({"values": SERIES, "period": 4})
        for value, trend, season, rest in zip(SERIES, got["trend"], got["seasonal"],
                                              got["remainder"]):
            if trend is None:
                continue
            self.assertAlmostEqual(trend + season + rest, value, delta=1e-9)

    def test_the_additive_season_sums_to_zero(self):
        got = timeseries.seasonal_decompose({"values": SERIES, "period": 4})
        self.assertAlmostEqual(math.fsum(got["seasonal"][:4]), 0.0, delta=1e-12)

    def test_the_multiplicative_parts_multiply_back_up(self):
        got = timeseries.seasonal_decompose({"values": SERIES, "period": 4,
                                             "model": "multiplicative"})
        self.assertAlmostEqual(math.fsum(got["seasonal"][:4]) / 4.0, 1.0, delta=1e-12)
        for value, trend, season, rest in zip(SERIES, got["trend"], got["seasonal"],
                                              got["remainder"]):
            if trend is None:
                continue
            self.assertAlmostEqual(trend * season * rest, value, delta=1e-9)

    def test_an_odd_period_works_too(self):
        got = timeseries.seasonal_decompose({"values": SERIES, "period": 5})
        self.assertEqual(len(got["seasonal"]), len(SERIES))

    def test_two_periods_are_the_minimum(self):
        with self.assertRaises(ValueError):
            timeseries.seasonal_decompose({"values": SERIES[:6], "period": 4})

    def test_an_unknown_model_is_refused(self):
        with self.assertRaises(ValueError):
            timeseries.seasonal_decompose({"values": SERIES, "period": 4, "model": "stl"})


class TestAutocorrelation(unittest.TestCase):
    def test_lag_zero_is_one(self):
        self.assertAlmostEqual(timeseries.acf({"values": SERIES, "nlags": 3})[0], 1.0, delta=1e-14)
        self.assertEqual(timeseries.pacf({"values": SERIES, "nlags": 3})[0], 1.0)

    def test_the_first_pacf_is_the_first_acf(self):
        self.assertAlmostEqual(timeseries.pacf({"values": SERIES, "nlags": 5})[1],
                               timeseries.acf({"values": SERIES, "nlags": 5})[1], delta=1e-12)

    def test_a_flat_series_has_no_autocorrelation(self):
        with self.assertRaises(ValueError):
            timeseries.acf({"values": [4.0] * 10})

    def test_too_many_lags_are_refused(self):
        with self.assertRaises(ValueError):
            timeseries.acf({"values": FLATISH, "nlags": len(FLATISH)})


class TestAutoregression(unittest.TestCase):
    def test_an_ar1_series_is_recovered(self):
        values = [1.0]
        for _ in range(200):
            values.append(3.0 + 0.65 * values[-1])
        got = timeseries.ar_fit({"values": values, "order": 1})
        self.assertAlmostEqual(got["coefficients"][0], 0.65, delta=1e-6)
        self.assertAlmostEqual(got["intercept"], 3.0, delta=1e-4)
        self.assertAlmostEqual(got["r2"], 1.0, delta=1e-9)

    def test_the_forecast_feeds_itself(self):
        fit = timeseries.ar_fit({"values": SERIES, "order": 2})
        got = timeseries.ar_forecast({"values": SERIES, "fit": fit, "horizon": 4})
        first = fit["intercept"] + fit["coefficients"][0] * SERIES[-1] \
            + fit["coefficients"][1] * SERIES[-2]
        self.assertAlmostEqual(got["forecast"][0], first, delta=1e-12)
        self.assertEqual(len(got["forecast"]), 4)

    def test_a_forecast_without_a_fit_fits_first(self):
        got = timeseries.ar_forecast({"values": SERIES, "order": 2, "horizon": 2})
        self.assertEqual(got["order"], 2)
        self.assertEqual(len(got["forecast"]), 2)

    def test_a_degenerate_series_is_refused(self):
        with self.assertRaises(ValueError):
            timeseries.ar_fit({"values": [2.0] * 12, "order": 2})

    def test_too_few_points_are_refused(self):
        with self.assertRaises(ValueError):
            timeseries.ar_fit({"values": SHORT[:3], "order": 3})

    def test_the_py_solver_matches_lstsq(self):
        for order in (1, 2, 4, 6):
            with self.subTest(order=order):
                self.assertTrue(agrees(timeseries.ar_fit({"values": SERIES, "order": order}),
                                       brute_ar(SERIES, order), 1e-8))


class TestJsonAble(unittest.TestCase):
    def test_every_result_survives_json(self):
        for case in ORACLE_CASES:
            got = timeseries.CALCS[case["calc"]](case["args"])
            self.assertEqual(json.loads(json.dumps(got)), got)

    def test_no_nan_ever_leaves_a_calculation(self):
        for case in ORACLE_CASES:
            got = timeseries.CALCS[case["calc"]](case["args"])
            for value in json.dumps(got).split(","):
                self.assertNotIn("NaN", value)


class TestBenchCases(unittest.TestCase):
    def test_bench_cases_are_paired_and_runnable(self):
        pairs = {}
        for case in BENCH_CASES:
            pairs.setdefault((case["calc"], case["size"]), set()).add(case["backend"])
        for key, backends in pairs.items():
            self.assertTrue({"py", "np"} <= backends, "%r is not a comparable pair" % (key,))
        self.assertIn("cumsum", pairs[("fn.brain.data.rolling", "n=4000")])
        for case in BENCH_CASES[:3]:
            timeseries.CALCS[case["calc"]](case["make_args"]())


if __name__ == "__main__":
    unittest.main()
