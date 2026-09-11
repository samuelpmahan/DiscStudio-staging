import unittest

import numpy as np
from scipy import optimize

from . import calcs, core, multiclass


def three_classes(seed=201, n=180, d=3, k=3, spread=1.5):
    return calcs.call("synthetic_classification",
                      {"seed": seed, "n": n, "d": d, "k": k, "spread": spread})


class TheSoftmaxItself(unittest.TestCase):
    def test_it_is_a_distribution(self):
        got = multiclass.softmax([1.0, 2.0, 3.0])
        self.assertAlmostEqual(sum(got), 1.0, places=12)
        self.assertEqual(got, sorted(got))

    def test_it_does_not_overflow(self):
        got = multiclass.softmax([1000.0, 0.0, -1000.0])
        self.assertAlmostEqual(got[0], 1.0)
        self.assertAlmostEqual(sum(got), 1.0, places=12)

    def test_adding_a_constant_to_every_score_changes_nothing(self):
        a = multiclass.softmax([0.4, -1.2, 2.0])
        b = multiclass.softmax([10.4, 8.8, 12.0])
        self.assertTrue(core.close(a, b, 1e-12))


class SoftmaxRegression(unittest.TestCase):
    def setUp(self):
        self.data = three_classes()
        self.matrix, self.targets, _ = core.xy(self.data, "label")
        self.design = np.hstack([np.ones((len(self.matrix), 1)), np.asarray(self.matrix)])
        self.classes = sorted(set(self.targets))

    def reference(self, l2=1.0):
        """the oracle: scipy minimising the same penalised cross-entropy, last class pinned."""
        n, width = self.design.shape
        free = len(self.classes) - 1
        y = np.zeros((n, len(self.classes)))
        for i, t in enumerate(self.targets):
            y[i, self.classes.index(t)] = 1.0

        def loss(flat):
            w = flat.reshape(free, width)
            scores = np.hstack([self.design @ w.T, np.zeros((n, 1))])
            scores = scores - scores.max(1, keepdims=True)
            e = np.exp(scores)
            p = e / e.sum(1, keepdims=True)
            return float(-np.log(np.maximum((p * y).sum(1), 1e-300)).mean()
                         + 0.5 * l2 * float((w[:, 1:] ** 2).sum()) / n)

        out = optimize.minimize(loss, np.zeros(free * width), method="L-BFGS-B",
                                options={"ftol": 1e-15, "gtol": 1e-12, "maxiter": 20000})
        return out.x.reshape(free, width).tolist(), float(out.fun)

    def test_it_reaches_the_optimum_scipy_finds(self):
        model = calcs.call("softmax_fit", {"data": self.data, "target": "label",
                                            "backend": "np", "lr": 1.0, "epochs": 6000, "l2": 1.0})
        want, want_loss = self.reference()
        got = [[b] + coef for b, coef in zip(model["intercepts"][:-1], model["coefs"][:-1])]
        self.assertAlmostEqual(model["loss"][-1], want_loss, places=4)
        self.assertTrue(core.close(got, want, 5e-2), core.max_error(got, want))

    def test_the_two_backends_agree(self):
        args = {"data": self.data, "target": "label", "epochs": 200, "lr": 0.5}
        a = calcs.call("softmax_fit", dict(args, backend="py"))
        b = calcs.call("softmax_fit", dict(args, backend="np"))
        self.assertTrue(core.close(a["coefs"], b["coefs"], 1e-9))
        self.assertTrue(core.close(a["loss"], b["loss"], 1e-9))

    def test_the_recorded_loss_is_the_loss_of_the_weights_it_returns(self):
        """a loss recorded before the step it is about describes weights nobody kept."""
        data = three_classes(seed=209, n=100)
        truth = [row[-1] for row in core.as_rows(data)]
        model = calcs.call("softmax_fit", {"data": data, "target": "label", "backend": "np",
                                            "l2": 0.0, "epochs": 120})
        proba = calcs.call("softmax_proba", {"model": model, "data": data})
        got = calcs.call("cross_entropy", {"y_true": truth, "y_pred": proba})
        self.assertAlmostEqual(got["mean"], model["loss"][-1], places=9)

    def test_the_loss_falls(self):
        model = calcs.call("softmax_fit", {"data": self.data, "target": "label", "backend": "np"})
        self.assertLess(model["loss"][-1], model["loss"][0])

    def test_probabilities_are_a_distribution_without_renormalising(self):
        model = calcs.call("softmax_fit", {"data": self.data, "target": "label", "backend": "np"})
        proba = calcs.call("softmax_proba", {"model": model, "data": self.data})["proba"]
        for row in proba:
            self.assertAlmostEqual(sum(row), 1.0, places=12)

    def test_the_pinned_class_has_no_weights_of_its_own(self):
        model = calcs.call("softmax_fit", {"data": self.data, "target": "label", "backend": "np"})
        self.assertEqual(model["pinned_class"], self.classes[-1])
        self.assertEqual(model["intercepts"][-1], 0.0)
        self.assertEqual(set(model["coefs"][-1]), {0.0})

    def test_it_classifies_at_least_as_well_as_one_vs_rest(self):
        truth = [row[-1] for row in core.as_rows(self.data)]
        soft = calcs.call("softmax_fit", {"data": self.data, "target": "label",
                                           "backend": "np", "lr": 1.0, "epochs": 2000})
        rest = calcs.call("logreg_fit", {"data": self.data, "target": "label",
                                          "backend": "np", "method": "newton", "l2": 1.0})
        a = calcs.call("classification_metrics",
                       {"y_true": truth, "y_pred": calcs.call("softmax_predict", {"model": soft, "data": self.data})["labels"]})
        b = calcs.call("classification_metrics",
                       {"y_true": truth, "y_pred": calcs.call("logreg_predict", {"model": rest, "data": self.data})["labels"]})
        self.assertGreaterEqual(a["accuracy"], b["accuracy"] - 0.02)
        self.assertGreater(a["accuracy"], 0.9)

    def test_one_class_is_refused(self):
        flat = core.dataset("one class only", ["x0", "label"], [[1.0, 0.0], [2.0, 0.0]])
        with self.assertRaises(ValueError):
            calcs.call("softmax_fit", {"data": flat, "target": "label"})


class CrossEntropy(unittest.TestCase):
    def test_a_confident_right_answer_costs_almost_nothing(self):
        got = calcs.call("cross_entropy", {"y_true": [0, 1], "y_pred": {"classes": [0, 1],
                                                                        "proba": [[0.999, 0.001], [0.001, 0.999]]}})
        self.assertLess(got["mean"], 0.002)

    def test_a_confident_wrong_answer_costs_a_lot(self):
        got = calcs.call("cross_entropy", {"y_true": [0, 1], "y_pred": {"classes": [0, 1],
                                                                        "proba": [[0.001, 0.999], [0.999, 0.001]]}})
        self.assertGreater(got["mean"], 6.0)

    def test_it_matches_the_loss_the_softmax_recorded(self):
        data = three_classes(seed=203, n=120)
        truth = [row[-1] for row in core.as_rows(data)]
        model = calcs.call("softmax_fit", {"data": data, "target": "label", "backend": "np",
                                            "l2": 0.0, "epochs": 300})
        proba = calcs.call("softmax_proba", {"model": model, "data": data})
        got = calcs.call("cross_entropy", {"y_true": truth, "y_pred": proba})
        self.assertAlmostEqual(got["mean"], model["loss"][-1], places=9)


class LogisticBoosting(unittest.TestCase):
    def setUp(self):
        self.data = three_classes(seed=205, n=200, k=2, spread=2.2)
        self.truth = [row[-1] for row in core.as_rows(self.data)]

    def test_the_loss_never_goes_up(self):
        model = calcs.call("logistic_gbm_fit", {"data": self.data, "target": "label",
                                                 "n_trees": 25, "learning_rate": 0.2})
        for before, after in zip(model["train_loss"], model["train_loss"][1:]):
            self.assertLessEqual(after, before + 1e-9)

    def test_it_starts_at_the_base_rate(self):
        model = calcs.call("logistic_gbm_fit", {"data": self.data, "target": "label", "n_trees": 1})
        rate = sum(1 for t in self.truth if t == model["classes"][1]) / len(self.truth)
        self.assertAlmostEqual(1.0 / (1.0 + pow(2.718281828459045, -model["init"])), rate, places=6)

    def test_the_newton_step_beats_fitting_the_residual_alone(self):
        """the squared-loss booster on the same data, given the same trees, is worse."""
        boosted = calcs.call("logistic_gbm_fit", {"data": self.data, "target": "label",
                                                   "n_trees": 25, "learning_rate": 0.2})
        plain = calcs.call("gbm_fit", {"data": self.data, "target": "label", "n_trees": 25,
                                        "learning_rate": 0.2, "max_depth": 2})
        a = calcs.call("logistic_gbm_predict", {"model": boosted, "data": self.data})["labels"]
        b = [boosted["classes"][1] if v >= 0.5 else boosted["classes"][0]
             for v in calcs.call("gbm_predict", {"model": plain, "data": self.data})["predictions"]]
        first = calcs.call("classification_metrics", {"y_true": self.truth, "y_pred": a})["accuracy"]
        second = calcs.call("classification_metrics", {"y_true": self.truth, "y_pred": b})["accuracy"]
        self.assertGreaterEqual(first, second)

    def test_it_separates_the_two_classes(self):
        model = calcs.call("logistic_gbm_fit", {"data": self.data, "target": "label",
                                                 "n_trees": 30, "learning_rate": 0.3})
        got = calcs.call("logistic_gbm_predict", {"model": model, "data": self.data})
        scored = calcs.call("classification_metrics", {"y_true": self.truth, "y_pred": got["labels"]})
        self.assertGreater(scored["accuracy"], 0.9)
        for row in got["proba"]:
            self.assertAlmostEqual(sum(row), 1.0, places=12)

    def test_the_area_under_the_curve_is_high(self):
        model = calcs.call("logistic_gbm_fit", {"data": self.data, "target": "label", "n_trees": 30})
        got = calcs.call("logistic_gbm_predict", {"model": model, "data": self.data})
        auc = calcs.call("roc_auc", {"y_true": self.truth, "y_pred": [p[1] for p in got["proba"]],
                                      "positive": model["classes"][1]})
        self.assertGreater(auc["auc"], 0.95)

    def test_three_classes_are_refused_rather_than_guessed(self):
        with self.assertRaises(ValueError):
            calcs.call("logistic_gbm_fit", {"data": three_classes(seed=207, k=3), "target": "label"})

    def test_the_model_is_json_able(self):
        import json

        model = calcs.call("logistic_gbm_fit", {"data": self.data, "target": "label", "n_trees": 4})
        self.assertEqual(json.loads(json.dumps(model)), model)
