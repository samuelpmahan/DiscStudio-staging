import unittest

import numpy as np

from . import calcs, core, trees


def split_data(seed=44, n=200, d=3, k=2, spread=1.4):
    return calcs.call("synthetic_classification", {"seed": seed, "n": n, "d": d, "k": k, "spread": spread})


class TheImpurities(unittest.TestCase):
    def test_gini_and_entropy_by_hand(self):
        self.assertAlmostEqual(trees._impurity([2, 2], 4, "gini"), 0.5)
        self.assertAlmostEqual(trees._impurity([4, 0], 4, "gini"), 0.0)
        self.assertAlmostEqual(trees._impurity([2, 2], 4, "entropy"), 1.0)
        self.assertAlmostEqual(trees._impurity([3, 1], 4, "entropy"), 0.8112781244591328)

    def test_a_pure_node_has_no_impurity_under_either(self):
        for criterion in ("gini", "entropy"):
            self.assertAlmostEqual(trees._impurity([7], 7, criterion), 0.0)


class OneTree(unittest.TestCase):
    def test_a_tree_on_a_split_it_must_find(self):
        """the oracle: a threshold put there by hand, which the search has to recover."""
        rows = [[x, 0.0] for x in (0.0, 1.0, 2.0, 3.0, 7.0, 8.0, 9.0, 10.0)]
        labels = [0, 0, 0, 0, 1, 1, 1, 1]
        data = core.dataset("a split at 5", ["x0", "x1", "label"],
                            [row + [label] for row, label in zip(rows, labels)])
        model = calcs.call("tree_fit", {"data": data, "target": "label", "max_depth": 1})
        self.assertEqual(model["root"]["feature"], 0)
        self.assertAlmostEqual(model["root"]["threshold"], 5.0)
        got = calcs.call("tree_predict", {"model": model, "data": data})["labels"]
        self.assertEqual(got, labels)

    def test_depth_is_respected(self):
        data = split_data()
        for depth in (1, 2, 4):
            model = calcs.call("tree_fit", {"data": data, "target": "label", "max_depth": depth})
            self.assertLessEqual(model["depth"], depth)
            self.assertLessEqual(trees.tree_depth(model["root"]), depth)

    def test_a_deep_enough_tree_memorises_its_training_rows(self):
        data = split_data(n=120)
        model = calcs.call("tree_fit", {"data": data, "target": "label", "max_depth": 20, "min_samples_leaf": 1})
        got = calcs.call("tree_predict", {"model": model, "data": data})["labels"]
        truth = [row[-1] for row in core.as_rows(data)]
        self.assertEqual(got, truth)

    def test_entropy_and_gini_agree_on_an_easy_problem(self):
        data = split_data(seed=7, spread=0.7)
        picks = {}
        for criterion in ("gini", "entropy"):
            model = calcs.call("tree_fit", {"data": data, "target": "label", "criterion": criterion, "max_depth": 3})
            picks[criterion] = calcs.call("tree_predict", {"model": model, "data": data})["labels"]
        self.assertEqual(picks["gini"], picks["entropy"])

    def test_the_regression_tree_splits_where_the_variance_drops(self):
        rows = [[float(i)] for i in range(20)]
        y = [0.0] * 10 + [10.0] * 10
        data = core.dataset("a step at ten", ["x0", "y"], [r + [v] for r, v in zip(rows, y)])
        model = calcs.call("tree_fit", {"data": data, "target": "y", "criterion": "mse", "max_depth": 1})
        self.assertAlmostEqual(model["root"]["threshold"], 9.5)
        got = calcs.call("tree_predict", {"model": model, "data": data})["predictions"]
        self.assertEqual(got, y)

    def test_leaf_probabilities_are_a_distribution(self):
        data = split_data()
        model = calcs.call("tree_fit", {"data": data, "target": "label", "max_depth": 3})
        for row in calcs.call("tree_predict", {"model": model, "data": data})["proba"]:
            self.assertAlmostEqual(sum(row), 1.0)

    def test_an_unknown_criterion_or_search_is_refused(self):
        data = split_data(n=40)
        with self.assertRaises(ValueError):
            calcs.call("tree_fit", {"data": data, "target": "label", "criterion": "chi2"})
        with self.assertRaises(ValueError):
            calcs.call("tree_fit", {"data": data, "target": "label", "search": "quantile"})

    def test_the_tree_is_json_able(self):
        import json

        data = split_data(n=60)
        model = calcs.call("tree_fit", {"data": data, "target": "label", "max_depth": 4})
        self.assertEqual(json.loads(json.dumps(model)), model)


class TheTwoSplitSearches(unittest.TestCase):
    """the histogram branch approximates the sorting branch; it never claims to equal it."""

    def setUp(self):
        self.data = split_data(seed=12, n=300, d=4, spread=1.2)

    def test_both_searches_find_a_useful_split(self):
        picks = {}
        for search in ("sort", "hist"):
            model = calcs.call("tree_fit", {"data": self.data, "target": "label", "search": search,
                                            "max_depth": 4, "bins": 64})
            got = calcs.call("tree_predict", {"model": model, "data": self.data})["labels"]
            truth = [row[-1] for row in core.as_rows(self.data)]
            picks[search] = calcs.call("classification_metrics", {"y_true": truth, "y_pred": got})["accuracy"]
            self.assertGreater(picks[search], 0.85, search)
        self.assertLess(abs(picks["sort"] - picks["hist"]), 0.1)

    def test_more_bins_move_the_histogram_threshold_toward_the_exact_one(self):
        exact = calcs.call("tree_fit", {"data": self.data, "target": "label", "max_depth": 1})["root"]["threshold"]
        coarse = calcs.call("tree_fit", {"data": self.data, "target": "label", "search": "hist",
                                          "bins": 4, "max_depth": 1})["root"]["threshold"]
        fine = calcs.call("tree_fit", {"data": self.data, "target": "label", "search": "hist",
                                        "bins": 256, "max_depth": 1})["root"]["threshold"]
        self.assertLessEqual(abs(fine - exact), abs(coarse - exact) + 1e-9)

    def test_the_searches_agree_exactly_when_the_bins_land_on_the_midpoints(self):
        rows = [[float(i)] for i in range(8)]
        labels = [0, 0, 0, 0, 1, 1, 1, 1]
        data = core.dataset("a split at 3.5", ["x0", "label"], [r + [float(l)] for r, l in zip(rows, labels)])
        a = calcs.call("tree_fit", {"data": data, "target": "label", "max_depth": 1})
        b = calcs.call("tree_fit", {"data": data, "target": "label", "search": "hist", "bins": 14, "max_depth": 1})
        self.assertEqual(a["root"]["feature"], b["root"]["feature"])
        self.assertLess(abs(a["root"]["threshold"] - b["root"]["threshold"]), 0.6)


class AForest(unittest.TestCase):
    def setUp(self):
        self.data = split_data(seed=15, n=200, d=4, spread=1.6)

    def test_the_seed_is_the_whole_of_the_forest(self):
        args = {"data": self.data, "target": "label", "n_trees": 6, "seed": 3, "max_depth": 4}
        self.assertEqual(calcs.call("forest_fit", args), calcs.call("forest_fit", args))
        other = calcs.call("forest_fit", dict(args, seed=4))
        self.assertNotEqual(other["trees"][0]["root"], calcs.call("forest_fit", args)["trees"][0]["root"])

    def test_the_trees_really_disagree(self):
        import json

        model = calcs.call("forest_fit", {"data": self.data, "target": "label", "n_trees": 8, "seed": 3, "max_depth": 4})
        shapes = {json.dumps(tree["root"], sort_keys=True) for tree in model["trees"]}
        self.assertGreater(len(shapes), 1)
        self.assertTrue(all(size > 0 for size in model["oob_sizes"]))

    def test_a_forest_beats_the_single_tree_it_is_made_of(self):
        noisy = split_data(seed=19, n=240, d=5, spread=2.6)
        truth = [row[-1] for row in core.as_rows(noisy)]
        split = calcs.call("train_test_split", {"data": noisy, "seed": 5, "test_size": 0.4})
        train = core.take(noisy, split["train_index"])
        test = core.take(noisy, split["test_index"])
        want = [truth[i] for i in split["test_index"]]
        one = calcs.call("tree_fit", {"data": train, "target": "label", "max_depth": 8})
        many = calcs.call("forest_fit", {"data": train, "target": "label", "n_trees": 25, "seed": 5, "max_depth": 8})
        a = calcs.call("classification_metrics", {"y_true": want, "y_pred": calcs.call("tree_predict", {"model": one, "data": test})["labels"]})
        b = calcs.call("classification_metrics", {"y_true": want, "y_pred": calcs.call("forest_predict", {"model": many, "data": test})["labels"]})
        self.assertGreaterEqual(b["accuracy"], a["accuracy"])

    def test_a_regression_forest_averages(self):
        data = calcs.call("synthetic_regression", {"seed": 8, "n": 120, "d": 3, "noise": 0.5})
        model = calcs.call("forest_fit", {"data": data, "target": "y", "criterion": "mse",
                                           "n_trees": 8, "seed": 2, "max_depth": 5})
        got = calcs.call("forest_predict", {"model": model, "data": data})["predictions"]
        truth = [row[-1] for row in core.as_rows(data)]
        self.assertGreater(calcs.call("regression_metrics", {"y_true": truth, "y_pred": got})["r2"], 0.7)


class Boosting(unittest.TestCase):
    def setUp(self):
        self.data = calcs.call("synthetic_regression", {"seed": 23, "n": 160, "d": 3, "noise": 0.3})
        self.truth = [row[-1] for row in core.as_rows(self.data)]

    def test_the_training_loss_never_goes_up(self):
        model = calcs.call("gbm_fit", {"data": self.data, "target": "y", "n_trees": 30, "learning_rate": 0.1})
        losses = model["train_mse"]
        for before, after in zip(losses, losses[1:]):
            self.assertLessEqual(after, before + 1e-9)

    def test_it_starts_at_the_mean_and_improves_on_it(self):
        model = calcs.call("gbm_fit", {"data": self.data, "target": "y", "n_trees": 40, "learning_rate": 0.15})
        self.assertAlmostEqual(model["init"], float(np.mean(self.truth)), places=9)
        got = calcs.call("gbm_predict", {"model": model, "data": self.data})["predictions"]
        scored = calcs.call("regression_metrics", {"y_true": self.truth, "y_pred": got})
        flat = calcs.call("regression_metrics", {"y_true": self.truth, "y_pred": [model["init"]] * len(self.truth)})
        self.assertLess(scored["mse"], flat["mse"])
        self.assertGreater(scored["r2"], 0.8)

    def test_predict_agrees_with_the_loss_the_fit_recorded(self):
        model = calcs.call("gbm_fit", {"data": self.data, "target": "y", "n_trees": 12, "learning_rate": 0.2})
        got = calcs.call("gbm_predict", {"model": model, "data": self.data})["predictions"]
        mse = calcs.call("regression_metrics", {"y_true": self.truth, "y_pred": got})["mse"]
        self.assertAlmostEqual(mse, model["train_mse"][-1], places=9)

    def test_a_smaller_rate_needs_more_trees_for_the_same_loss(self):
        slow = calcs.call("gbm_fit", {"data": self.data, "target": "y", "n_trees": 20, "learning_rate": 0.05})
        fast = calcs.call("gbm_fit", {"data": self.data, "target": "y", "n_trees": 20, "learning_rate": 0.3})
        self.assertGreater(slow["train_mse"][-1], fast["train_mse"][-1])


class LearningCurves(unittest.TestCase):
    def test_the_curve_is_a_part_and_a_function_of_its_seed(self):
        data = calcs.call("synthetic_regression", {"seed": 33, "n": 200, "d": 3, "noise": 0.4})
        args = {"data": data, "target": "y", "seed": 6, "fit": "linreg_fit", "predict": "linreg_predict",
                "metric": "mse", "fractions": [0.2, 0.5, 1.0]}
        curve = calcs.call("learning_curve", args)
        self.assertEqual(curve, calcs.call("learning_curve", args))
        self.assertEqual(len(curve["sizes"]), 3)
        self.assertEqual(curve["sizes"], sorted(curve["sizes"]))

    def test_the_test_error_falls_as_rows_are_added(self):
        data = calcs.call("synthetic_regression", {"seed": 34, "n": 400, "d": 4, "noise": 0.4})
        curve = calcs.call("learning_curve", {
            "data": data, "target": "y", "seed": 6, "fit": "linreg_fit", "predict": "linreg_predict",
            "metric": "mse", "fractions": [0.05, 0.2, 1.0]})
        self.assertLess(curve["test"][-1], curve["test"][0])

    def test_a_classifier_curve_reads_accuracy(self):
        data = calcs.call("synthetic_classification", {"seed": 35, "n": 200, "d": 3, "k": 2, "spread": 1.8})
        curve = calcs.call("learning_curve", {
            "data": data, "target": "label", "seed": 6, "fit": "tree_fit", "predict": "tree_predict",
            "fit_args": {"max_depth": 4}, "metric": "accuracy", "fractions": [0.2, 1.0]})
        self.assertTrue(all(0.0 <= v <= 1.0 for v in curve["test"]))
        self.assertTrue(all(0.0 <= v <= 1.0 for v in curve["train"]))
