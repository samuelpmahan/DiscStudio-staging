import unittest

import numpy as np
from scipy import optimize

from . import calcs, core, nnet


class Lasso(unittest.TestCase):
    def setUp(self):
        self.data = calcs.call("synthetic_regression", {"seed": 91, "n": 150, "d": 6, "noise": 0.3})
        self.matrix, self.targets, self.features = core.xy(self.data, "y")

    def reference(self, alpha):
        """the oracle: scipy minimising the same objective, on the same standardised columns."""
        scaled, means, sds = core.standardize(self.matrix)
        x = np.asarray(scaled)
        centre = float(np.mean(self.targets))
        y = np.asarray(self.targets) - centre
        n = len(y)

        def loss(w):
            return float(((y - x @ w) ** 2).sum() / (2 * n) + alpha * np.abs(w).sum())

        out = optimize.minimize(loss, np.zeros(x.shape[1]), method="Powell",
                                options={"xtol": 1e-12, "ftol": 1e-14, "maxiter": 200000, "maxfev": 200000})
        return out.x.tolist()

    def test_coordinate_descent_matches_scipy_on_the_same_objective(self):
        for alpha in (0.05, 0.3):
            model = calcs.call("lasso_fit", {"data": self.data, "target": "y", "alpha": alpha, "backend": "np"})
            self.assertTrue(core.close(model["scaled_coef"], self.reference(alpha), 2e-3),
                            f"alpha={alpha}: {core.max_error(model['scaled_coef'], self.reference(alpha))}")

    def test_backends_agree(self):
        a = calcs.call("lasso_fit", {"data": self.data, "target": "y", "alpha": 0.2, "backend": "py"})
        b = calcs.call("lasso_fit", {"data": self.data, "target": "y", "alpha": 0.2, "backend": "np"})
        self.assertTrue(core.close(a["coef"], b["coef"], 1e-8))

    def test_a_bigger_penalty_zeroes_more_columns(self):
        light = calcs.call("lasso_fit", {"data": self.data, "target": "y", "alpha": 0.01, "backend": "np"})
        middling = calcs.call("lasso_fit", {"data": self.data, "target": "y", "alpha": 3.0, "backend": "np"})
        heavy = calcs.call("lasso_fit", {"data": self.data, "target": "y", "alpha": 50.0, "backend": "np"})
        self.assertGreater(len(light["nonzero"]), len(middling["nonzero"]))
        self.assertGreater(len(middling["nonzero"]), len(heavy["nonzero"]))
        self.assertEqual(heavy["nonzero"], [])

    def test_it_selects_rather_than_only_shrinking(self):
        model = calcs.call("lasso_fit", {"data": self.data, "target": "y", "alpha": 0.5, "backend": "np"})
        ridge = calcs.call("ridge_fit", {"data": self.data, "target": "y", "alpha": 0.5, "backend": "np"})
        self.assertTrue(any(c == 0.0 for c in model["coef"]))
        self.assertTrue(all(c != 0.0 for c in ridge["coef"]))

    def test_a_tiny_penalty_lands_near_least_squares(self):
        model = calcs.call("lasso_fit", {"data": self.data, "target": "y", "alpha": 1e-6, "backend": "np"})
        plain = calcs.call("linreg_fit", {"data": self.data, "target": "y", "backend": "np"})
        self.assertTrue(core.close(model["coef"], plain["coef"], 1e-2))

    def test_the_soft_threshold_is_the_shrinkage_it_claims(self):
        self.assertAlmostEqual(nnet._soft_threshold(3.0, 1.0), 2.0)
        self.assertAlmostEqual(nnet._soft_threshold(-3.0, 1.0), -2.0)
        self.assertAlmostEqual(nnet._soft_threshold(0.5, 1.0), 0.0)


class Perceptron(unittest.TestCase):
    def setUp(self):
        self.data = calcs.call("synthetic_classification",
                               {"seed": 93, "n": 120, "d": 2, "k": 2, "spread": 0.4, "separation": 8.0})
        self.truth = [row[-1] for row in core.as_rows(self.data)]

    def test_it_converges_on_a_separable_problem(self):
        model = calcs.call("perceptron_fit", {"data": self.data, "target": "label", "seed": 5, "epochs": 60})
        self.assertTrue(model["converged"])
        self.assertEqual(model["mistakes"][-1], 0)
        got = calcs.call("perceptron_predict", {"model": model, "data": self.data})["labels"]
        self.assertEqual(got, self.truth)

    def test_the_mistake_count_falls_when_there_are_mistakes_to_make(self):
        harder = calcs.call("synthetic_classification",
                            {"seed": 94, "n": 200, "d": 4, "k": 2, "spread": 1.4, "separation": 3.0})
        model = calcs.call("perceptron_fit", {"data": harder, "target": "label", "seed": 5, "epochs": 40})
        self.assertGreater(model["mistakes"][0], 0)
        self.assertLess(min(model["mistakes"]), model["mistakes"][0])

    def test_the_seed_is_the_whole_of_it(self):
        args = {"data": self.data, "target": "label", "seed": 5, "epochs": 10}
        self.assertEqual(calcs.call("perceptron_fit", args), calcs.call("perceptron_fit", args))

    def test_three_classes_are_refused_rather_than_guessed(self):
        data = calcs.call("synthetic_classification", {"seed": 93, "n": 60, "d": 2, "k": 3})
        with self.assertRaises(ValueError):
            calcs.call("perceptron_fit", {"data": data, "target": "label", "seed": 1})


class Mlp(unittest.TestCase):
    def test_a_regression_network_beats_predicting_the_mean(self):
        data = calcs.call("synthetic_regression", {"seed": 95, "n": 240, "d": 3, "noise": 0.2})
        truth = [row[-1] for row in core.as_rows(data)]
        model = calcs.call("mlp_fit", {"data": data, "target": "y", "seed": 7, "hidden": 12,
                                        "lr": 0.05, "epochs": 250})
        got = calcs.call("mlp_predict", {"model": model, "data": data})["predictions"]
        scored = calcs.call("regression_metrics", {"y_true": truth, "y_pred": got})
        self.assertGreater(scored["r2"], 0.9)

    def test_the_loss_falls(self):
        data = calcs.call("synthetic_regression", {"seed": 95, "n": 160, "d": 3, "noise": 0.2})
        model = calcs.call("mlp_fit", {"data": data, "target": "y", "seed": 7, "epochs": 120})
        self.assertLess(model["loss"][-1], model["loss"][0])

    def test_the_seed_is_the_whole_of_the_init(self):
        data = calcs.call("synthetic_regression", {"seed": 95, "n": 80, "d": 2})
        args = {"data": data, "target": "y", "seed": 7, "hidden": 5, "epochs": 20}
        self.assertEqual(calcs.call("mlp_fit", args), calcs.call("mlp_fit", args))
        other = calcs.call("mlp_fit", dict(args, seed=8))
        self.assertNotEqual(other["w1"], calcs.call("mlp_fit", args)["w1"])

    def test_a_two_class_network_separates_two_classes(self):
        data = calcs.call("synthetic_classification", {"seed": 96, "n": 200, "d": 3, "k": 2, "spread": 1.2})
        truth = [row[-1] for row in core.as_rows(data)]
        model = calcs.call("mlp_fit", {"data": data, "target": "label", "task": "classify",
                                        "seed": 7, "hidden": 10, "lr": 0.2, "epochs": 250})
        got = calcs.call("mlp_predict", {"model": model, "data": data})
        scored = calcs.call("classification_metrics", {"y_true": truth, "y_pred": got["labels"]})
        self.assertGreater(scored["accuracy"], 0.9)
        for row in got["proba"]:
            self.assertAlmostEqual(sum(row), 1.0, places=9)

    def test_more_than_two_classes_is_refused(self):
        data = calcs.call("synthetic_classification", {"seed": 96, "n": 60, "d": 2, "k": 3})
        with self.assertRaises(ValueError):
            calcs.call("mlp_fit", {"data": data, "target": "label", "task": "classify", "seed": 1})

    def test_the_network_is_json_able(self):
        import json

        data = calcs.call("synthetic_regression", {"seed": 95, "n": 60, "d": 2})
        model = calcs.call("mlp_fit", {"data": data, "target": "y", "seed": 7, "hidden": 4, "epochs": 10})
        self.assertEqual(json.loads(json.dumps(model)), model)
