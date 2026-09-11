import unittest

from . import calcs, core


class CrossValidate(unittest.TestCase):
    def setUp(self):
        self.data = calcs.call("synthetic_regression", {"seed": 101, "n": 150, "d": 3, "noise": 0.4})

    def test_every_row_is_scored_exactly_once(self):
        got = calcs.call("cross_validate", {"data": self.data, "target": "y", "seed": 3, "k": 5,
                                             "fit": "linreg_fit", "predict": "linreg_predict"})
        self.assertEqual(sum(got["sizes"]), 150)
        self.assertEqual(len(got["test"]), 5)

    def test_it_is_a_pure_function_of_its_seed(self):
        args = {"data": self.data, "target": "y", "seed": 3, "k": 4,
                "fit": "linreg_fit", "predict": "linreg_predict"}
        self.assertEqual(calcs.call("cross_validate", args), calcs.call("cross_validate", args))
        self.assertNotEqual(calcs.call("cross_validate", dict(args, seed=4))["test"],
                            calcs.call("cross_validate", args)["test"])

    def test_the_held_out_error_is_at_least_the_training_error(self):
        got = calcs.call("cross_validate", {"data": self.data, "target": "y", "seed": 3, "k": 5,
                                             "fit": "linreg_fit", "predict": "linreg_predict"})
        self.assertGreaterEqual(got["mean"], core.mean(got["train"]) - 1e-9)

    def test_it_compares_two_models_on_the_same_folds(self):
        args = {"data": self.data, "target": "y", "seed": 3, "k": 5}
        linear = calcs.call("cross_validate", dict(args, fit="linreg_fit", predict="linreg_predict"))
        forest = calcs.call("cross_validate", dict(args, fit="forest_fit", predict="forest_predict",
                                                   fit_args={"criterion": "mse", "n_trees": 6,
                                                             "seed": 3, "max_depth": 5}))
        self.assertEqual(linear["sizes"], forest["sizes"])
        self.assertLess(linear["mean"], forest["mean"])

    def test_a_classifier_is_cross_validated_on_accuracy(self):
        data = calcs.call("synthetic_classification", {"seed": 102, "n": 150, "d": 3, "k": 2, "spread": 1.5})
        got = calcs.call("cross_validate", {"data": data, "target": "label", "seed": 3, "k": 5,
                                             "fit": "tree_fit", "predict": "tree_predict",
                                             "fit_args": {"max_depth": 4}, "metric": "accuracy"})
        self.assertTrue(all(0.0 <= v <= 1.0 for v in got["test"]))
        self.assertGreater(got["mean"], 0.7)


class LassoPath(unittest.TestCase):
    def setUp(self):
        self.data = calcs.call("synthetic_regression", {"seed": 103, "n": 120, "d": 5, "noise": 0.3})

    def test_the_surviving_columns_only_ever_shrink(self):
        got = calcs.call("lasso_path", {"data": self.data, "target": "y",
                                         "alphas": [0.001, 0.01, 0.1, 1.0, 10.0]})
        self.assertTrue(got["monotone"], [row["count"] for row in got["path"]])
        self.assertEqual(got["path"][-1]["count"], 0)

    def test_the_path_records_a_coefficient_per_column_per_penalty(self):
        got = calcs.call("lasso_path", {"data": self.data, "target": "y", "alphas": [0.01, 0.5]})
        for row in got["path"]:
            self.assertEqual(len(row["coef"]), 5)

    def test_cross_validation_picks_a_penalty_from_the_path(self):
        got = calcs.call("lasso_path", {"data": self.data, "target": "y", "seed": 5, "k": 4,
                                         "alphas": [0.001, 0.01, 0.1, 1.0]})
        self.assertIn(got["chosen"], [0.001, 0.01, 0.1, 1.0])
        best = min(got["path"], key=lambda row: row["cv_mse"])
        self.assertEqual(got["chosen"], best["alpha"])

    def test_without_a_seed_there_is_no_choice_only_a_path(self):
        got = calcs.call("lasso_path", {"data": self.data, "target": "y", "alphas": [0.01, 0.1]})
        self.assertIsNone(got["chosen"])
        self.assertNotIn("cv_mse", got["path"][0])
