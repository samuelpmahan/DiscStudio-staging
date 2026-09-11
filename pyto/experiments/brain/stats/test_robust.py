import json
import unittest

import stats.robust as robust
from stats.robust_cases import (BENCH_CASES, CLEAN_X, CLEAN_Y, ORACLE_CASES, SPIKED_Y,
                                TIED_X, TIED_Y)
from stats.tolerance import close


class TestOracles(unittest.TestCase):
    def test_every_oracle_case_matches_its_reference(self):
        self.assertGreaterEqual(len(ORACLE_CASES), 20)
        for case in ORACLE_CASES:
            with self.subTest(case=case["case"], calc=case["calc"]):
                got = robust.CALCS[case["calc"]](case["args"])
                project = case.get("project")
                shaped = project(got) if project else got
                self.assertTrue(
                    close(shaped, case["expected"](), case["tolerance"]),
                    "%s: got %r, %s says %r" % (case["case"], shaped, case["reference"],
                                                case["expected"]()))

    def test_every_calculation_has_a_case_on_both_backends(self):
        seen = {(case["calc"], case["backend"]) for case in ORACLE_CASES}
        for address in robust.CALCS:
            self.assertIn((address, "py"), seen, address)
            self.assertIn((address, "sp"), seen, address)


class TestBackendsAgree(unittest.TestCase):
    def test_py_and_sp_agree(self):
        for address, args in (
            ("fn.brain.stats.linregress", {"x": CLEAN_X, "y": SPIKED_Y}),
            ("fn.brain.stats.theil_sen", {"x": CLEAN_X, "y": SPIKED_Y}),
            ("fn.brain.stats.siegel_slopes", {"x": CLEAN_X, "y": SPIKED_Y}),
        ):
            with self.subTest(calc=address):
                fn = robust.CALCS[address]
                self.assertTrue(close(fn(dict(args, backend="sp")),
                                      fn(dict(args, backend="py")), 1e-9))


class TestWhatRobustMeans(unittest.TestCase):
    def test_the_two_robust_slopes_survive_what_least_squares_does_not(self):
        """the whole reason these exist: two spikes in sixty points."""
        truth = 2.5
        least_squares = robust.linregress({"x": CLEAN_X, "y": SPIKED_Y})["slope"]
        for address in ("fn.brain.stats.theil_sen", "fn.brain.stats.siegel_slopes"):
            slope = robust.CALCS[address]({"x": CLEAN_X, "y": SPIKED_Y})["slope"]
            self.assertLess(abs(slope - truth), abs(least_squares - truth), address)
            self.assertAlmostEqual(slope, truth, delta=0.05, msg=address)

    def test_on_clean_data_all_three_agree(self):
        answers = [robust.linregress({"x": CLEAN_X, "y": CLEAN_Y})["slope"],
                   robust.theil_sen({"x": CLEAN_X, "y": CLEAN_Y})["slope"],
                   robust.siegel_slopes({"x": CLEAN_X, "y": CLEAN_Y})["slope"]]
        for slope in answers[1:]:
            self.assertAlmostEqual(slope, answers[0], delta=0.05)

    def test_the_interval_brackets_the_slope_and_widens_with_the_level(self):
        narrow = robust.theil_sen({"x": CLEAN_X, "y": SPIKED_Y, "level": 0.80})
        wide = robust.theil_sen({"x": CLEAN_X, "y": SPIKED_Y, "level": 0.99})
        for one in (narrow, wide):
            self.assertLessEqual(one["low"], one["slope"])
            self.assertLessEqual(one["slope"], one["high"])
        self.assertLessEqual(wide["low"], narrow["low"])
        self.assertGreaterEqual(wide["high"], narrow["high"])

    def test_a_perfect_line_is_recovered_exactly(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [3.0 * v - 1.0 for v in x]
        for address in ("fn.brain.stats.linregress", "fn.brain.stats.theil_sen",
                        "fn.brain.stats.siegel_slopes"):
            got = robust.CALCS[address]({"x": x, "y": y})
            self.assertAlmostEqual(got["slope"], 3.0, delta=1e-12, msg=address)
            self.assertAlmostEqual(got["intercept"], -1.0, delta=1e-12, msg=address)

    def test_ties_do_not_stop_a_median_of_slopes(self):
        for address in ("fn.brain.stats.theil_sen", "fn.brain.stats.siegel_slopes"):
            got = robust.CALCS[address]({"x": TIED_X, "y": TIED_Y})
            self.assertGreater(got["slope"], 0.0, address)

    def test_x_defaults_to_the_position(self):
        y = [5.0, 7.0, 9.0, 11.0]
        self.assertAlmostEqual(robust.linregress({"y": y})["slope"], 2.0, delta=1e-12)
        self.assertAlmostEqual(robust.theil_sen({"y": y})["slope"], 2.0, delta=1e-12)


class TestEdges(unittest.TestCase):
    def test_a_constant_x_has_no_slope(self):
        with self.assertRaises(ValueError):
            robust.linregress({"x": [2.0] * 6, "y": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]})
        with self.assertRaises(ValueError):
            robust.theil_sen({"x": [2.0] * 6, "y": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]})

    def test_mismatched_lengths_are_refused(self):
        with self.assertRaises(ValueError):
            robust.linregress({"x": CLEAN_X, "y": CLEAN_Y[:-1]})

    def test_too_few_points_are_refused(self):
        with self.assertRaises(ValueError):
            robust.linregress({"x": [1.0, 2.0], "y": [1.0, 2.0]})

    def test_an_unknown_alternative_is_refused(self):
        with self.assertRaises(ValueError):
            robust.linregress({"x": CLEAN_X, "y": CLEAN_Y, "alternative": "bigger"})

    def test_a_level_outside_the_unit_interval_is_refused(self):
        with self.assertRaises(ValueError):
            robust.theil_sen({"x": CLEAN_X, "y": CLEAN_Y, "level": 1.5})

    def test_an_unknown_backend_is_refused(self):
        with self.assertRaises(ValueError):
            robust.siegel_slopes({"x": CLEAN_X, "y": CLEAN_Y, "backend": "np"})


class TestJsonAble(unittest.TestCase):
    def test_every_result_survives_json(self):
        for case in ORACLE_CASES:
            got = robust.CALCS[case["calc"]](case["args"])
            self.assertEqual(json.loads(json.dumps(got)), got)


class TestBenchCases(unittest.TestCase):
    def test_bench_cases_are_paired_and_runnable(self):
        pairs = {}
        for case in BENCH_CASES:
            pairs.setdefault((case["calc"], case["size"]), set()).add(case["backend"])
        for key, backends in pairs.items():
            self.assertEqual(backends, {"py", "sp"}, "%r is not a comparable pair" % (key,))
        for case in BENCH_CASES[:3]:
            robust.CALCS[case["calc"]](case["make_args"]())


if __name__ == "__main__":
    unittest.main()
