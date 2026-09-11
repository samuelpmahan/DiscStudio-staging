import unittest

import numpy as np

from . import calcs, core, linear, resample


def problem(seed=7, n=80, d=3, noise=0.05):
    return calcs.call("synthetic_regression", {"seed": seed, "n": n, "d": d, "noise": noise})


class ClosedFormAgainstNumpy(unittest.TestCase):
    """the oracle: numpy's least squares on the same design, which pyto never calls."""

    def setUp(self):
        self.data = problem()
        self.matrix, self.targets, _ = core.xy(self.data, "y")

    def reference(self, l2=0.0):
        x = np.hstack([np.ones((len(self.matrix), 1)), np.asarray(self.matrix)])
        y = np.asarray(self.targets)
        if l2:
            # the augmented-data spelling of ridge, an independent route to the same answer
            penalty = np.sqrt(l2) * np.eye(x.shape[1])
            penalty[0, 0] = 0.0
            x = np.vstack([x, penalty])
            y = np.concatenate([y, np.zeros(x.shape[1])])
        return np.linalg.lstsq(x, y, rcond=None)[0].tolist()

    def test_py_backend(self):
        model = calcs.call("linreg_fit", {"data": self.data, "target": "y", "backend": "py"})
        got = [model["intercept"]] + model["coef"]
        self.assertTrue(core.close(got, self.reference(), 1e-8), core.max_error(got, self.reference()))

    def test_np_backend_is_the_same_semantics(self):
        args = {"data": self.data, "target": "y"}
        a = calcs.call("linreg_fit", dict(args, backend="py"))
        b = calcs.call("linreg_fit", dict(args, backend="np"))
        self.assertTrue(core.close(a["coef"], b["coef"], 1e-8))
        self.assertAlmostEqual(a["intercept"], b["intercept"], places=8)

    def test_ridge_against_the_augmented_reference(self):
        for l2 in (0.5, 5.0):
            model = calcs.call("ridge_fit", {"data": self.data, "target": "y", "alpha": l2, "backend": "np"})
            got = [model["intercept"]] + model["coef"]
            self.assertTrue(core.close(got, self.reference(l2), 1e-7), f"l2={l2}")

    def test_ridge_shrinks_but_not_the_intercept(self):
        plain = calcs.call("linreg_fit", {"data": self.data, "target": "y"})
        heavy = calcs.call("ridge_fit", {"data": self.data, "target": "y", "alpha": 50.0})
        self.assertLess(sum(abs(c) for c in heavy["coef"]), sum(abs(c) for c in plain["coef"]))
        self.assertEqual(heavy["model"], "ridge")

    def test_it_recovers_the_weights_it_was_built_from(self):
        model = calcs.call("linreg_fit", {"data": self.data, "target": "y"})
        truth = self.data["truth"]
        self.assertTrue(core.close(model["coef"], truth["coef"], 5e-2))
        self.assertAlmostEqual(model["intercept"], truth["intercept"], places=1)

    def test_no_intercept(self):
        model = calcs.call("linreg_fit", {"data": self.data, "target": "y", "fit_intercept": False})
        self.assertEqual(model["intercept"], 0.0)
        self.assertEqual(len(model["coef"]), 3)


class GradientDescent(unittest.TestCase):
    def setUp(self):
        self.data = problem(seed=3, n=60, d=2)

    def test_gd_walks_to_the_closed_form(self):
        args = {"data": self.data, "target": "y"}
        closed = calcs.call("linreg_fit", args)
        walked = calcs.call("linreg_fit", dict(args, method="gd", lr=0.08, epochs=4000))
        self.assertTrue(core.close(walked["coef"], closed["coef"], 1e-3), core.max_error(walked["coef"], closed["coef"]))

    def test_gd_backends_agree(self):
        args = {"data": self.data, "target": "y", "method": "gd", "lr": 0.05, "epochs": 300}
        a = calcs.call("linreg_fit", dict(args, backend="py"))
        b = calcs.call("linreg_fit", dict(args, backend="np"))
        self.assertTrue(core.close(a["coef"], b["coef"], 1e-9))

    def test_sgd_is_a_pure_function_of_the_seed(self):
        args = {"data": self.data, "target": "y", "method": "sgd", "lr": 0.01, "epochs": 5, "seed": 4}
        self.assertEqual(calcs.call("linreg_fit", args), calcs.call("linreg_fit", args))
        other = calcs.call("linreg_fit", dict(args, seed=5))
        self.assertNotEqual(other["coef"], calcs.call("linreg_fit", args)["coef"])

    def test_sgd_without_a_seed_is_refused(self):
        with self.assertRaises(KeyError):
            calcs.call("linreg_fit", {"data": self.data, "target": "y", "method": "sgd"})

    def test_unknown_method_is_refused(self):
        with self.assertRaises(ValueError):
            calcs.call("linreg_fit", {"data": self.data, "target": "y", "method": "newton"})


class Predict(unittest.TestCase):
    def setUp(self):
        self.data = problem(seed=9, n=40, d=2)
        self.model = calcs.call("linreg_fit", {"data": self.data, "target": "y"})

    def test_predictions_match_numpy(self):
        got = calcs.call("linreg_predict", {"model": self.model, "data": self.data})["predictions"]
        matrix, _, _ = core.xy(self.data, "y")
        want = (np.asarray(matrix) @ np.asarray(self.model["coef"]) + self.model["intercept"]).tolist()
        self.assertTrue(core.close(got, want, 1e-9))

    def test_backends_agree(self):
        a = calcs.call("linreg_predict", {"model": self.model, "data": self.data, "backend": "py"})
        b = calcs.call("linreg_predict", {"model": self.model, "data": self.data, "backend": "np"})
        self.assertTrue(core.close(a["predictions"], b["predictions"], 1e-9))

    def test_a_missing_column_is_refused_not_guessed(self):
        thin = core.dataset("one column short", ["x0", "y"], [[1.0, 2.0]])
        with self.assertRaises(KeyError):
            calcs.call("linreg_predict", {"model": self.model, "data": thin})

    def test_the_model_is_json_able(self):
        import json

        self.assertEqual(json.loads(json.dumps(self.model)), self.model)
