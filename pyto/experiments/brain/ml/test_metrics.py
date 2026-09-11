import unittest

import numpy as np
from scipy import stats

from . import calcs, core


class RegressionMetrics(unittest.TestCase):
    def setUp(self):
        self.truth = [3.0, -0.5, 2.0, 7.0, 4.2]
        self.guess = [2.5, 0.0, 2.0, 8.0, 4.0]

    def reference(self):
        t, g = np.asarray(self.truth), np.asarray(self.guess)
        mse = float(((t - g) ** 2).mean())
        mae = float(np.abs(t - g).mean())
        r2 = float(1 - ((t - g) ** 2).sum() / ((t - t.mean()) ** 2).sum())
        return {"mse": mse, "mae": mae, "r2": r2}

    def test_py_backend_against_numpy(self):
        got = calcs.call("regression_metrics", {"y_true": self.truth, "y_pred": self.guess})
        want = self.reference()
        self.assertTrue(core.close({k: got[k] for k in want}, want, 1e-12))

    def test_np_backend_is_the_same(self):
        a = calcs.call("regression_metrics", {"y_true": self.truth, "y_pred": self.guess, "backend": "py"})
        b = calcs.call("regression_metrics", {"y_true": self.truth, "y_pred": self.guess, "backend": "np"})
        self.assertTrue(core.close({k: a[k] for k in ("mse", "mae", "r2")}, {k: b[k] for k in ("mse", "mae", "r2")}, 1e-12))

    def test_r2_of_a_perfect_fit_is_one(self):
        got = calcs.call("regression_metrics", {"y_true": self.truth, "y_pred": self.truth})
        self.assertAlmostEqual(got["r2"], 1.0)
        self.assertAlmostEqual(got["mse"], 0.0)

    def test_r2_against_scipy_linregress(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.1, 3.9, 6.2, 7.8, 10.1]
        fit = stats.linregress(x, y)
        guess = [fit.intercept + fit.slope * v for v in x]
        got = calcs.call("regression_metrics", {"y_true": y, "y_pred": guess})
        self.assertAlmostEqual(got["r2"], fit.rvalue**2, places=12)

    def test_mismatched_lengths_are_refused(self):
        with self.assertRaises(ValueError):
            calcs.call("regression_metrics", {"y_true": [1.0], "y_pred": [1.0, 2.0]})


class ClassificationMetrics(unittest.TestCase):
    def setUp(self):
        self.truth = [0, 0, 0, 1, 1, 1, 1, 2, 2, 2]
        self.guess = [0, 0, 1, 1, 1, 1, 2, 2, 2, 0]

    def test_confusion_matrix_by_hand(self):
        got = calcs.call("confusion_matrix", {"y_true": self.truth, "y_pred": self.guess})
        self.assertEqual(got["labels"], [0, 1, 2])
        self.assertEqual(got["matrix"], [[2, 1, 0], [0, 3, 1], [1, 0, 2]])
        self.assertEqual(sum(sum(r) for r in got["matrix"]), len(self.truth))

    def test_accuracy_and_per_class_by_hand(self):
        got = calcs.call("classification_metrics", {"y_true": self.truth, "y_pred": self.guess})
        self.assertAlmostEqual(got["accuracy"], 7 / 10)
        self.assertAlmostEqual(got["per_class"]["1"]["precision"], 3 / 4)
        self.assertAlmostEqual(got["per_class"]["1"]["recall"], 3 / 4)
        self.assertAlmostEqual(got["per_class"]["1"]["f1"], 3 / 4)
        self.assertEqual(got["per_class"]["2"]["support"], 3)

    def test_micro_average_equals_accuracy(self):
        got = calcs.call("classification_metrics", {"y_true": self.truth, "y_pred": self.guess, "average": "micro"})
        self.assertAlmostEqual(got["f1"], got["accuracy"])

    def test_macro_is_the_unweighted_mean(self):
        got = calcs.call("classification_metrics", {"y_true": self.truth, "y_pred": self.guess})
        by_hand = core.mean([got["per_class"][k]["f1"] for k in ("0", "1", "2")])
        self.assertAlmostEqual(got["f1"], by_hand)


class RocAuc(unittest.TestCase):
    def setUp(self):
        self.truth = [0, 0, 1, 1, 0, 1, 1, 0, 1, 0]
        self.score = [0.1, 0.4, 0.35, 0.8, 0.2, 0.9, 0.55, 0.3, 0.7, 0.6]

    def test_against_the_mann_whitney_u(self):
        """the oracle: scipy's u statistic, the identity auc = u / (n_pos * n_neg)."""
        positives = [s for s, t in zip(self.score, self.truth) if t == 1]
        negatives = [s for s, t in zip(self.score, self.truth) if t == 0]
        u = stats.mannwhitneyu(positives, negatives, alternative="two-sided").statistic
        got = calcs.call("roc_auc", {"y_true": self.truth, "y_pred": self.score})
        self.assertAlmostEqual(got["auc"], u / (len(positives) * len(negatives)), places=12)

    def test_a_perfect_score_is_one_and_a_reversed_one_is_zero(self):
        truth = [0, 0, 1, 1]
        self.assertAlmostEqual(calcs.call("roc_auc", {"y_true": truth, "y_pred": [0.0, 0.1, 0.9, 1.0]})["auc"], 1.0)
        self.assertAlmostEqual(calcs.call("roc_auc", {"y_true": truth, "y_pred": [1.0, 0.9, 0.1, 0.0]})["auc"], 0.0)

    def test_ties_take_the_average_rank(self):
        got = calcs.call("roc_auc", {"y_true": [0, 1], "y_pred": [0.5, 0.5]})
        self.assertAlmostEqual(got["auc"], 0.5)

    def test_the_curve_starts_at_the_origin_and_ends_at_one(self):
        curve = calcs.call("roc_curve", {"y_true": self.truth, "y_pred": self.score})
        self.assertEqual((curve["fpr"][0], curve["tpr"][0]), (0.0, 0.0))
        self.assertEqual((curve["fpr"][-1], curve["tpr"][-1]), (1.0, 1.0))
        self.assertEqual(curve["fpr"], sorted(curve["fpr"]))


class Silhouette(unittest.TestCase):
    def test_two_tight_far_apart_clusters_score_near_one(self):
        data = core.dataset("two clusters", ["x", "y"], [[0, 0], [0, 0.1], [10, 10], [10, 10.1]])
        got = calcs.call("silhouette", {"data": data, "labels": [0, 0, 1, 1]})
        self.assertGreater(got["mean"], 0.98)

    def test_a_scrambled_labelling_scores_worse(self):
        data = core.dataset("two clusters", ["x", "y"], [[0, 0], [0, 0.1], [10, 10], [10, 10.1]])
        good = calcs.call("silhouette", {"data": data, "labels": [0, 0, 1, 1]})["mean"]
        bad = calcs.call("silhouette", {"data": data, "labels": [0, 1, 0, 1]})["mean"]
        self.assertLess(bad, good)
        self.assertLess(bad, 0.0)

    def test_backends_agree(self):
        data = calcs.call("synthetic_blobs", {"seed": 2, "n": 30, "k": 3})
        labels = [int(row[-1]) for row in core.as_rows(data)]
        rows = core.dataset("features", ["x0", "x1"], [row[:-1] for row in core.as_rows(data)])
        a = calcs.call("silhouette", {"data": rows, "labels": labels, "backend": "py"})
        b = calcs.call("silhouette", {"data": rows, "labels": labels, "backend": "np"})
        self.assertTrue(core.close(a["scores"], b["scores"], 1e-9))
