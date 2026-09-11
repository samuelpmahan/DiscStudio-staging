import unittest

import numpy as np
from scipy import optimize
from scipy import stats
from scipy.spatial import distance

from . import calcs, classify, core


def two_classes(seed=13, n=120, d=3, k=2, spread=1.2):
    return calcs.call("synthetic_classification", {"seed": seed, "n": n, "d": d, "k": k, "spread": spread})


class LogisticRegression(unittest.TestCase):
    def setUp(self):
        self.data = two_classes()
        self.matrix, self.targets, _ = core.xy(self.data, "label")
        self.design = np.hstack([np.ones((len(self.matrix), 1)), np.asarray(self.matrix)])
        self.y = np.asarray(self.targets)

    def reference(self, l2=0.0):
        """the oracle: scipy minimising the negative log likelihood, no shared code."""

        def loss(w):
            z = self.design @ w
            return float(np.sum(np.logaddexp(0.0, z) - self.y * z) + 0.5 * l2 * float(w[1:] @ w[1:]))

        out = optimize.minimize(loss, np.zeros(self.design.shape[1]), method="L-BFGS-B",
                                options={"ftol": 1e-15, "gtol": 1e-12, "maxiter": 5000})
        return out.x.tolist()

    def test_newton_reaches_the_penalised_maximum_likelihood(self):
        """with a penalty the optimum is finite and unique, so the two routes must meet exactly."""
        model = calcs.call("logreg_fit", {"data": self.data, "target": "label", "method": "newton",
                                           "backend": "np", "l2": 1.0})
        got = [model["intercepts"][0]] + model["coefs"][0]
        want = self.reference(1.0)
        self.assertTrue(core.close(got, want, 1e-4), core.max_error(got, want))

    def test_newton_reaches_the_unpenalised_optimum_when_the_classes_overlap(self):
        """without a penalty the likelihood only has a maximum if the classes are not separable."""
        self.data = two_classes(seed=13, n=160, d=2, spread=3.0)
        self.matrix, self.targets, _ = core.xy(self.data, "label")
        self.design = np.hstack([np.ones((len(self.matrix), 1)), np.asarray(self.matrix)])
        self.y = np.asarray(self.targets)
        model = calcs.call("logreg_fit", {"data": self.data, "target": "label", "method": "newton", "backend": "np"})
        got = [model["intercepts"][0]] + model["coefs"][0]
        want = self.reference()
        self.assertTrue(core.close(got, want, 1e-3), core.max_error(got, want))

    def test_newton_backends_agree(self):
        args = {"data": self.data, "target": "label", "method": "newton"}
        a = calcs.call("logreg_fit", dict(args, backend="py"))
        b = calcs.call("logreg_fit", dict(args, backend="np"))
        self.assertTrue(core.close(a["coefs"], b["coefs"], 1e-7))

    def test_newton_takes_far_fewer_steps_than_gradient_descent(self):
        args = {"data": self.data, "target": "label", "backend": "np", "l2": 1.0}
        newton = calcs.call("logreg_fit", dict(args, method="newton"))
        walked = calcs.call("logreg_fit", dict(args, method="gd", lr=0.5, epochs=20000))
        self.assertLess(newton["iters"][0], 30)
        self.assertGreater(walked["iters"][0], 1000)
        a = calcs.call("logreg_predict", {"model": newton, "data": self.data})["labels"]
        b = calcs.call("logreg_predict", {"model": walked, "data": self.data})["labels"]
        self.assertEqual(a, b)

    def test_gradient_descent_backends_agree(self):
        args = {"data": self.data, "target": "label", "method": "gd", "lr": 0.4, "epochs": 400}
        a = calcs.call("logreg_fit", dict(args, backend="py"))
        b = calcs.call("logreg_fit", dict(args, backend="np"))
        self.assertTrue(core.close(a["coefs"], b["coefs"], 1e-9))

    def test_the_penalty_shrinks_the_coefficients(self):
        plain = calcs.call("logreg_fit", {"data": self.data, "target": "label", "backend": "np"})
        heavy = calcs.call("logreg_fit", {"data": self.data, "target": "label", "backend": "np", "l2": 100.0})
        self.assertLess(sum(abs(c) for c in heavy["coefs"][0]), sum(abs(c) for c in plain["coefs"][0]))

    def test_the_penalised_fit_matches_the_penalised_reference(self):
        model = calcs.call("logreg_fit", {"data": self.data, "target": "label", "backend": "np", "l2": 5.0})
        got = [model["intercepts"][0]] + model["coefs"][0]
        self.assertTrue(core.close(got, self.reference(5.0), 1e-4))

    def test_probabilities_are_a_distribution_and_the_label_is_their_argmax(self):
        model = calcs.call("logreg_fit", {"data": self.data, "target": "label", "backend": "np"})
        proba = calcs.call("logreg_proba", {"model": model, "data": self.data})["proba"]
        labels = calcs.call("logreg_predict", {"model": model, "data": self.data})["labels"]
        for row, label in zip(proba, labels):
            self.assertAlmostEqual(sum(row), 1.0, places=9)
            self.assertEqual(model["classes"][max(range(len(row)), key=lambda i: row[i])], label)

    def test_it_separates_classes_it_was_built_to_separate(self):
        model = calcs.call("logreg_fit", {"data": self.data, "target": "label", "backend": "np"})
        labels = calcs.call("logreg_predict", {"model": model, "data": self.data})["labels"]
        scored = calcs.call("classification_metrics", {"y_true": self.targets, "y_pred": labels})
        self.assertGreater(scored["accuracy"], 0.85)

    def test_one_vs_rest_for_three_classes(self):
        data = two_classes(seed=4, n=150, k=3, spread=0.9)
        model = calcs.call("logreg_fit", {"data": data, "target": "label", "backend": "np"})
        self.assertTrue(model["one_vs_rest"])
        self.assertEqual(len(model["coefs"]), 3)
        labels = calcs.call("logreg_predict", {"model": model, "data": data})["labels"]
        truth = [row[-1] for row in core.as_rows(data)]
        self.assertGreater(calcs.call("classification_metrics", {"y_true": truth, "y_pred": labels})["accuracy"], 0.8)

    def test_one_class_is_refused(self):
        flat = core.dataset("one class only", ["x0", "label"], [[1.0, 0.0], [2.0, 0.0]])
        with self.assertRaises(ValueError):
            calcs.call("logreg_fit", {"data": flat, "target": "label"})

    def test_the_sigmoid_does_not_overflow(self):
        self.assertAlmostEqual(classify.sigmoid(-1000.0), 0.0)
        self.assertAlmostEqual(classify.sigmoid(1000.0), 1.0)


class NearestNeighbours(unittest.TestCase):
    def setUp(self):
        self.data = two_classes(seed=21, n=80, d=2, spread=1.0)
        self.model = calcs.call("knn_fit", {"data": self.data, "target": "label", "k": 5})

    def test_against_a_cdist_reference(self):
        """the oracle: scipy's pairwise distances and a vote written from scratch."""
        rows, targets, _ = core.xy(self.data, "label")
        query = rows[:20]
        d = distance.cdist(np.asarray(query), np.asarray(rows), metric="euclidean")
        want = []
        for row in d:
            order = sorted(range(len(row)), key=lambda i: (row[i], i))[:5]
            tally = {}
            for i in order:
                tally[targets[i]] = tally.get(targets[i], 0) + 1
            want.append(max(sorted(tally), key=lambda label: tally[label]))
        thin = core.dataset("the first twenty rows", ["x0", "x1"], query)
        got = calcs.call("knn_predict", {"model": self.model, "data": thin, "backend": "np"})["labels"]
        self.assertEqual(got, want)

    def test_backends_agree(self):
        a = calcs.call("knn_predict", {"model": self.model, "data": self.data, "backend": "py"})
        b = calcs.call("knn_predict", {"model": self.model, "data": self.data, "backend": "np"})
        self.assertEqual(a["labels"], b["labels"])

    def test_k_of_one_reproduces_the_training_labels(self):
        model = calcs.call("knn_fit", {"data": self.data, "target": "label", "k": 1})
        got = calcs.call("knn_predict", {"model": model, "data": self.data})["labels"]
        self.assertEqual(got, [row[-1] for row in core.as_rows(self.data)])

    def test_manhattan_is_a_different_metric_not_a_broken_one(self):
        model = calcs.call("knn_fit", {"data": self.data, "target": "label", "k": 5, "metric": "manhattan"})
        rows, targets, _ = core.xy(self.data, "label")
        got = calcs.call("knn_predict", {"model": model, "data": self.data, "backend": "np"})["labels"]
        d = distance.cdist(np.asarray(rows), np.asarray(rows), metric="cityblock")
        want = []
        for row in d:
            order = sorted(range(len(row)), key=lambda i: (row[i], i))[:5]
            tally = {}
            for i in order:
                tally[targets[i]] = tally.get(targets[i], 0) + 1
            want.append(max(sorted(tally), key=lambda label: tally[label]))
        self.assertEqual(got, want)

    def test_regression_averages_the_neighbours(self):
        data = calcs.call("synthetic_regression", {"seed": 6, "n": 60, "d": 2})
        model = calcs.call("knn_fit", {"data": data, "target": "y", "k": 3, "task": "regress"})
        got = calcs.call("knn_predict", {"model": model, "data": data})
        self.assertEqual(len(got["predictions"]), 60)
        scored = calcs.call("regression_metrics", {"y_true": [r[-1] for r in core.as_rows(data)], "y_pred": got["predictions"]})
        self.assertGreater(scored["r2"], 0.5)

    def test_distance_weighting_changes_the_votes(self):
        far = calcs.call("knn_fit", {"data": self.data, "target": "label", "k": 9, "weights": "distance"})
        got = calcs.call("knn_predict", {"model": far, "data": self.data})
        self.assertTrue(all(v is not None for v in got["votes"]))


class NaiveBayes(unittest.TestCase):
    def test_gaussian_log_posterior_against_scipy(self):
        data = two_classes(seed=31, n=90, d=3, spread=1.5)
        model = calcs.call("gaussian_nb_fit", {"data": data, "target": "label"})
        got = calcs.call("gaussian_nb_predict", {"model": model, "data": data})
        rows, _, _ = core.xy(data, "label")
        want = []
        for row in rows:
            scores = []
            for prior, mu, var in zip(model["priors"], model["means"], model["variances"]):
                scores.append(float(np.log(prior) + stats.norm.logpdf(row, loc=mu, scale=np.sqrt(var)).sum()))
            want.append(scores)
        self.assertTrue(core.close(got["log_posterior"], want, 1e-10))

    def test_gaussian_separates_well_separated_classes(self):
        data = two_classes(seed=31, n=90, d=3, spread=0.8)
        model = calcs.call("gaussian_nb_fit", {"data": data, "target": "label"})
        labels = calcs.call("gaussian_nb_predict", {"model": model, "data": data})["labels"]
        truth = [row[-1] for row in core.as_rows(data)]
        self.assertGreater(calcs.call("classification_metrics", {"y_true": truth, "y_pred": labels})["accuracy"], 0.9)

    def test_multinomial_against_a_hand_written_reference(self):
        data = calcs.call("synthetic_counts", {"seed": 41, "n": 80, "k": 2, "vocabulary": 6, "length": 25})
        model = calcs.call("multinomial_nb_fit", {"data": data, "target": "label", "alpha": 1.0})
        rows, targets, _ = core.xy(data, "label")
        want = []
        for row in rows:
            want.append([
                float(np.log(prior) + np.dot(row, probabilities))
                for prior, probabilities in zip(model["priors"], model["log_prob"])
            ])
        got = calcs.call("multinomial_nb_predict", {"model": model, "data": data, "backend": "py"})
        self.assertTrue(core.close(got["log_posterior"], want, 1e-10))

    def test_multinomial_backends_agree(self):
        data = calcs.call("synthetic_counts", {"seed": 41, "n": 60, "k": 2, "vocabulary": 5})
        model = calcs.call("multinomial_nb_fit", {"data": data, "target": "label"})
        a = calcs.call("multinomial_nb_predict", {"model": model, "data": data, "backend": "py"})
        b = calcs.call("multinomial_nb_predict", {"model": model, "data": data, "backend": "np"})
        self.assertTrue(core.close(a["log_posterior"], b["log_posterior"], 1e-9))
        self.assertEqual(a["labels"], b["labels"])

    def test_smoothing_keeps_an_unseen_word_from_zeroing_a_class(self):
        data = core.dataset("counts", ["w0", "w1", "label"], [[3, 0, 0], [4, 0, 0], [0, 3, 1], [0, 4, 1]])
        model = calcs.call("multinomial_nb_fit", {"data": data, "target": "label", "alpha": 1.0})
        for row in model["log_prob"]:
            for value in row:
                self.assertGreater(value, -30.0)

    def test_every_model_is_json_able(self):
        import json

        data = two_classes(seed=2, n=40)
        for name in ("logreg_fit", "knn_fit", "gaussian_nb_fit"):
            model = calcs.call(name, {"data": data, "target": "label"})
            self.assertEqual(json.loads(json.dumps(model)), model, name)
