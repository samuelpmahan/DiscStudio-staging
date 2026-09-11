import unittest

from . import calcs, core


def problem(seed=311, n=240, d=4, k=3, spread=1.9):
    return calcs.call("synthetic_classification",
                      {"seed": seed, "n": n, "d": d, "k": k, "spread": spread})


class OutOfBag(unittest.TestCase):
    def setUp(self):
        self.data = problem()
        self.truth = [row[-1] for row in core.as_rows(self.data)]
        self.model = calcs.call("forest_fit", {"data": self.data, "target": "label",
                                                "n_trees": 25, "seed": 311, "max_depth": 6})

    def test_a_tree_never_votes_on_a_row_it_was_fitted_to(self):
        for tree_index, missed in enumerate(self.model["oob_index"]):
            self.assertEqual(len(missed), self.model["oob_sizes"][tree_index])
            self.assertEqual(len(set(missed)), len(missed))

    def test_about_a_third_of_the_rows_are_out_of_bag_for_each_tree(self):
        share = core.mean([float(size) / self.model["n"] for size in self.model["oob_sizes"]])
        self.assertGreater(share, 0.30)
        self.assertLess(share, 0.42)

    def test_every_row_is_covered_by_enough_trees_to_vote(self):
        got = calcs.call("forest_oob", {"model": self.model})
        self.assertEqual(got["uncovered"], [])
        self.assertEqual(got["scored"], self.model["n"])
        self.assertGreater(got["mean_voters"], 5.0)

    def test_the_out_of_bag_score_is_below_the_training_score(self):
        """the whole point: the training score of a deep forest is a lie, and this is not."""
        oob = calcs.call("forest_oob", {"model": self.model})["score"]
        fitted = calcs.call("classification_metrics", {
            "y_true": self.truth,
            "y_pred": calcs.call("forest_predict", {"model": self.model, "data": self.data})["labels"]})
        self.assertLess(oob, fitted["accuracy"])

    def test_it_agrees_with_a_real_held_out_split(self):
        """the oracle for a free held-out number is a held-out number someone paid for."""
        split = calcs.call("train_test_split", {"data": self.data, "seed": 311, "test_size": 0.3,
                                                 "stratify": "label"})
        train = core.take(self.data, split["train_index"])
        test = core.take(self.data, split["test_index"])
        honest = calcs.call("forest_fit", {"data": train, "target": "label", "n_trees": 25,
                                            "seed": 311, "max_depth": 6})
        want = calcs.call("classification_metrics", {
            "y_true": [row[-1] for row in core.as_rows(test)],
            "y_pred": calcs.call("forest_predict", {"model": honest, "data": test})["labels"]})["accuracy"]
        oob = calcs.call("forest_oob", {"model": self.model})["score"]
        self.assertLess(abs(oob - want), 0.08, f"oob {oob} against held out {want}")

    def test_a_regression_forest_scores_itself_too(self):
        data = calcs.call("synthetic_regression", {"seed": 312, "n": 200, "d": 3, "noise": 0.6})
        model = calcs.call("forest_fit", {"data": data, "target": "y", "criterion": "mse",
                                           "n_trees": 20, "seed": 312, "max_depth": 6})
        got = calcs.call("forest_oob", {"model": model, "metric": "mse"})
        truth = [row[-1] for row in core.as_rows(data)]
        fitted = calcs.call("regression_metrics", {
            "y_true": truth,
            "y_pred": calcs.call("forest_predict", {"model": model, "data": data})["predictions"]})
        self.assertGreater(got["score"], fitted["mse"])

    def test_it_is_a_pure_function_of_the_model(self):
        a = calcs.call("forest_oob", {"model": self.model})
        b = calcs.call("forest_oob", {"model": self.model})
        self.assertEqual(a, b)

    def test_more_trees_cover_every_row_more_often(self):
        small = calcs.call("forest_fit", {"data": self.data, "target": "label", "n_trees": 6,
                                           "seed": 311, "max_depth": 6})
        few = calcs.call("forest_oob", {"model": small})["mean_voters"]
        many = calcs.call("forest_oob", {"model": self.model})["mean_voters"]
        self.assertLess(few, many)

    def test_the_model_with_its_bags_is_still_json_able(self):
        import json

        self.assertEqual(json.loads(json.dumps(self.model)), self.model)
