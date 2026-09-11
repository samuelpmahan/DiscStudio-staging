import json
import math
import unittest

import numpy as np

import stats.regression as regression
from stats.regression_cases import (BENCH_CASES, CLASSES, DESIGN, ORACLE_CASES, SIMPLE,
                                    SIMPLE_Y, WEIGHTS, X1, X2, Y, brute_ols, brute_wls)
from stats.tolerance import close

TWO = [[a, b] for a, b in zip(X1, X2)]


class TestOracles(unittest.TestCase):
    def test_every_oracle_case_matches_its_reference(self):
        self.assertGreaterEqual(len(ORACLE_CASES), 18)
        for case in ORACLE_CASES:
            with self.subTest(case=case["case"], calc=case["calc"]):
                got = regression.CALCS[case["calc"]](case["args"])
                project = case.get("project")
                shaped = project(got) if project else got
                self.assertTrue(
                    close(shaped, case["expected"](), case["tolerance"]),
                    "%s: got %r, %s says %r"
                    % (case["case"], shaped, case["reference"], case["expected"]()))

    def test_all_three_solvers_have_a_case(self):
        covered = {case["calc"] for case in ORACLE_CASES}
        for address in ("fn.brain.stats.ols_normal", "fn.brain.stats.ols_qr",
                        "fn.brain.stats.ols_lstsq", "fn.brain.stats.ols",
                        "fn.brain.stats.ridge"):
            self.assertIn(address, covered)


class TestTheThreeSolversAgree(unittest.TestCase):
    """the tournament's correctness criterion: three routes, one answer."""

    def test_the_solvers_agree_on_the_coefficients(self):
        answers = [regression.ols({"x": DESIGN, "y": Y, "solver": solver})
                   for solver in ("normal", "qr", "lstsq")]
        for other in answers[1:]:
            self.assertTrue(close(other["coefficients"], answers[0]["coefficients"], 1e-8))
            self.assertTrue(close(other["stderr"], answers[0]["stderr"], 1e-8))
            self.assertTrue(close(other["pvalues"], answers[0]["pvalues"], 1e-8))

    def test_the_solvers_agree_on_an_ill_conditioned_design(self):
        """a nearly collinear design is where the normal equations are supposed to suffer."""
        base = [[v, v + 1e-5 * (i % 7)] for i, v in enumerate(X1)]
        target = [3.0 * row[0] - 1.0 * row[1] for row in base]
        answers = {}
        for solver in ("normal", "qr", "lstsq"):
            answers[solver] = regression.ols({"x": base, "y": target, "solver": solver})
        for solver in ("qr", "lstsq"):
            self.assertTrue(
                close(answers[solver]["fitted"], answers["normal"]["fitted"], 1e-6),
                "%s and normal disagree on the fitted values" % solver)

    def test_an_exactly_collinear_design_is_refused_by_all_three(self):
        base = [[v, 2.0 * v] for v in X1]
        target = list(SIMPLE_Y)
        for solver in ("normal", "qr", "lstsq"):
            with self.subTest(solver=solver):
                with self.assertRaises(ValueError):
                    regression.ols({"x": base, "y": target, "solver": solver})


class TestOlsShape(unittest.TestCase):
    def test_a_perfect_fit_has_r2_one(self):
        target = [2.0 + 3.0 * row[0] for row in SIMPLE]
        got = regression.ols({"x": SIMPLE, "y": target})
        self.assertAlmostEqual(got["r2"], 1.0, delta=1e-12)
        self.assertAlmostEqual(got["coefficients"][0], 2.0, delta=1e-9)
        self.assertAlmostEqual(got["coefficients"][1], 3.0, delta=1e-9)

    def test_the_residuals_are_orthogonal_to_the_design(self):
        got = regression.ols({"x": DESIGN, "y": Y})
        a = np.asarray([[1.0] + row for row in DESIGN], dtype=float)
        product = a.T @ np.asarray(got["residuals"], dtype=float)
        self.assertLess(float(np.abs(product).max()), 1e-9)

    def test_the_names_carry_the_intercept(self):
        got = regression.ols({"x": DESIGN, "y": Y, "columns": ["a", "b", "c"]})
        self.assertEqual(got["names"], ["intercept", "a", "b", "c"])
        without = regression.ols({"x": DESIGN, "y": Y, "columns": ["a", "b", "c"],
                                  "intercept": False})
        self.assertEqual(without["names"], ["a", "b", "c"])

    def test_a_dataset_part_is_a_design(self):
        table = {"for": "a design as a dataset Part", "columns": ["a", "b", "c"],
                 "rows": [list(row) for row in DESIGN]}
        got = regression.ols({"x": table, "y": Y})
        self.assertTrue(close(got["coefficients"],
                              regression.ols({"x": DESIGN, "y": Y})["coefficients"], 1e-12))

    def test_mismatched_lengths_are_refused(self):
        with self.assertRaises(ValueError) as caught:
            regression.ols({"x": DESIGN, "y": Y[:-1]})
        self.assertIn("has", str(caught.exception))

    def test_more_columns_than_rows_is_refused(self):
        with self.assertRaises(ValueError):
            regression.ols({"x": DESIGN[:3], "y": Y[:3]})

    def test_an_unknown_solver_names_the_ones_there_are(self):
        with self.assertRaises(ValueError) as caught:
            regression.ols({"x": DESIGN, "y": Y, "solver": "cholesky"})
        self.assertIn("qr", str(caught.exception))


class TestWeightedLeastSquares(unittest.TestCase):
    """the weights go into the design, so the tournament's three solvers still apply."""

    def test_all_three_solvers_give_the_weighted_answer(self):
        reference = brute_wls(DESIGN, Y, WEIGHTS)
        for solver in ("normal", "qr", "lstsq"):
            with self.subTest(solver=solver):
                got = regression.wls({"x": DESIGN, "y": Y, "weights": WEIGHTS,
                                      "solver": solver})
                self.assertTrue(close(got["coefficients"], reference["coefficients"], 1e-8))
                self.assertEqual(got["solver"], solver)

    def test_equal_weights_are_ordinary_least_squares(self):
        plain = regression.ols({"x": DESIGN, "y": Y})
        for weights in (None, [1.0] * len(Y), [3.5] * len(Y)):
            with self.subTest(weights="none" if weights is None else weights[0]):
                got = regression.wls({"x": DESIGN, "y": Y, "weights": weights})
                self.assertTrue(close(got["coefficients"], plain["coefficients"], 1e-8))

    def test_a_zero_weight_drops_a_row(self):
        weights = [1.0] * len(Y)
        weights[0] = 0.0
        got = regression.wls({"x": DESIGN, "y": Y, "weights": weights})
        without = regression.ols({"x": DESIGN[1:], "y": Y[1:]})
        self.assertTrue(close(got["coefficients"], without["coefficients"], 1e-7))

    def test_the_residuals_come_back_on_the_original_scale(self):
        got = regression.wls({"x": DESIGN, "y": Y, "weights": WEIGHTS})
        for row, fitted, residual, actual in zip(DESIGN, got["fitted"], got["residuals"], Y):
            self.assertAlmostEqual(fitted + residual, actual, delta=1e-9)

    def test_a_bad_weight_is_refused(self):
        for weights in ([1.0] * (len(Y) - 1), [-1.0] + [1.0] * (len(Y) - 1), [0.0] * len(Y)):
            with self.assertRaises(ValueError):
                regression.wls({"x": DESIGN, "y": Y, "weights": weights})

    def test_an_unknown_solver_is_refused(self):
        with self.assertRaises(ValueError):
            regression.wls({"x": DESIGN, "y": Y, "weights": WEIGHTS, "solver": "cholesky"})


class TestRidge(unittest.TestCase):
    def test_zero_lambda_is_ols(self):
        self.assertTrue(close(regression.ridge({"x": DESIGN, "y": Y, "lam": 0.0})["coefficients"],
                              regression.ols({"x": DESIGN, "y": Y})["coefficients"], 1e-7))

    def test_more_penalty_shrinks_the_slopes(self):
        small = regression.ridge({"x": DESIGN, "y": Y, "lam": 1.0})["coefficients"][1:]
        large = regression.ridge({"x": DESIGN, "y": Y, "lam": 500.0})["coefficients"][1:]
        self.assertLess(math.fsum(v * v for v in large), math.fsum(v * v for v in small))

    def test_the_intercept_is_not_penalised(self):
        got = regression.ridge({"x": DESIGN, "y": Y, "lam": 1e6})
        self.assertAlmostEqual(got["coefficients"][0], math.fsum(Y) / len(Y), delta=1e-2)

    def test_a_negative_lambda_is_refused(self):
        with self.assertRaises(ValueError):
            regression.ridge({"x": DESIGN, "y": Y, "lam": -1.0})

    def test_py_and_np_agree(self):
        for penalty in (0.0, 2.5, 100.0):
            with self.subTest(lam=penalty):
                self.assertTrue(close(
                    regression.ridge({"x": DESIGN, "y": Y, "lam": penalty, "backend": "np"}),
                    regression.ridge({"x": DESIGN, "y": Y, "lam": penalty, "backend": "py"}),
                    1e-8))


class TestLogistic(unittest.TestCase):
    def test_irls_solves_the_score_equations(self):
        """the oracle for a logistic fit: X'(y - p) is zero at the answer."""
        got = regression.logistic({"x": TWO, "y": CLASSES})
        a = np.asarray([[1.0] + row for row in TWO], dtype=float)
        score = a.T @ (np.asarray(CLASSES) - np.asarray(got["probabilities"]))
        self.assertLess(float(np.abs(score).max()), 1e-7)
        self.assertTrue(got["converged"])

    def test_gradient_descent_reaches_the_same_place(self):
        irls = regression.logistic({"x": TWO, "y": CLASSES})
        gd = regression.logistic({"x": TWO, "y": CLASSES, "method": "gd",
                                  "max_iter": 60000, "learning_rate": 0.5})
        self.assertTrue(close(gd["coefficients"], irls["coefficients"], 1e-4))
        self.assertAlmostEqual(gd["log_likelihood"], irls["log_likelihood"], delta=1e-6)

    def test_py_and_np_irls_agree(self):
        py = regression.logistic({"x": TWO, "y": CLASSES, "backend": "py"})
        np_ = regression.logistic({"x": TWO, "y": CLASSES, "backend": "np"})
        self.assertTrue(close(np_["coefficients"], py["coefficients"], 1e-8))
        self.assertTrue(close(np_["stderr"], py["stderr"], 1e-8))

    def test_a_label_that_is_not_zero_or_one_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            regression.logistic({"x": TWO, "y": [2.0] * len(TWO)})
        self.assertIn("{0, 1}", str(caught.exception))

    def test_one_class_is_refused(self):
        with self.assertRaises(ValueError):
            regression.logistic({"x": TWO, "y": [1.0] * len(TWO)})

    def test_an_unknown_method_is_refused(self):
        with self.assertRaises(ValueError):
            regression.logistic({"x": TWO, "y": CLASSES, "method": "newton"})


class TestPredict(unittest.TestCase):
    def test_predicting_the_training_rows_gives_the_fitted_values(self):
        fit = regression.ols({"x": DESIGN, "y": Y})
        self.assertTrue(close(regression.predict({"fit": fit, "x": DESIGN}), fit["fitted"], 1e-9))

    def test_the_logit_link_gives_probabilities(self):
        fit = regression.logistic({"x": TWO, "y": CLASSES})
        got = regression.predict({"fit": fit, "x": TWO, "link": "logit"})
        self.assertTrue(close(got, fit["probabilities"], 1e-12))
        self.assertTrue(all(0.0 <= p <= 1.0 for p in got))

    def test_a_row_of_the_wrong_width_is_refused(self):
        fit = regression.ols({"x": DESIGN, "y": Y})
        with self.assertRaises(ValueError):
            regression.predict({"fit": fit, "x": [[1.0]]})


class TestJsonAble(unittest.TestCase):
    def test_every_fit_survives_json(self):
        for args in ({"x": DESIGN, "y": Y}, {"x": DESIGN, "y": Y, "lam": 1.0}):
            fit = regression.ols(args) if "lam" not in args else regression.ridge(args)
            self.assertEqual(json.loads(json.dumps(fit)), fit)
        fit = regression.logistic({"x": TWO, "y": CLASSES})
        self.assertEqual(json.loads(json.dumps(fit)), fit)


class TestBenchCases(unittest.TestCase):
    def test_bench_cases_are_runnable(self):
        seen = {}
        for case in BENCH_CASES:
            seen.setdefault(case["size"], set()).add(case["calc"])
        for size, calcs in seen.items():
            self.assertIn("fn.brain.stats.ols_qr", calcs, size)
            self.assertIn("fn.brain.stats.ols_normal", calcs, size)
            self.assertIn("fn.brain.stats.ols_lstsq", calcs, size)
        for case in BENCH_CASES[:3]:
            regression.CALCS[case["calc"]](case["make_args"]())


if __name__ == "__main__":
    unittest.main()
