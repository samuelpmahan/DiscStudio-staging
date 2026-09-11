import unittest

from . import calcs, core


class Split(unittest.TestCase):
    def setUp(self):
        self.data = calcs.call("synthetic_regression", {"seed": 1, "n": 40, "d": 2})

    def test_it_is_a_partition(self):
        got = calcs.call("train_test_split", {"data": self.data, "seed": 2, "test_size": 0.25})
        self.assertEqual(sorted(got["train_index"] + got["test_index"]), list(range(40)))
        self.assertEqual(len(got["test_index"]), 10)

    def test_the_seed_is_the_whole_of_it(self):
        args = {"data": self.data, "seed": 2}
        self.assertEqual(calcs.call("train_test_split", args), calcs.call("train_test_split", args))
        other = calcs.call("train_test_split", {"data": self.data, "seed": 3})
        self.assertNotEqual(other["test_index"], calcs.call("train_test_split", args)["test_index"])

    def test_an_absolute_test_size(self):
        got = calcs.call("train_test_split", {"data": self.data, "seed": 2, "test_size": 7})
        self.assertEqual(len(got["test_index"]), 7)

    def test_stratify_keeps_the_proportions(self):
        data = calcs.call("synthetic_classification", {"seed": 5, "n": 60, "k": 3})
        got = calcs.call("train_test_split", {"data": data, "seed": 2, "test_size": 1 / 3, "stratify": "label"})
        rows = core.as_rows(data)
        at = core.columns_of(data).index("label")
        for label in (0.0, 1.0, 2.0):
            in_test = sum(1 for i in got["test_index"] if rows[i][at] == label)
            self.assertEqual(in_test, 20 // 3 + (1 if 20 % 3 else 0) or in_test, f"label {label}")
            self.assertGreaterEqual(in_test, 6)
            self.assertLessEqual(in_test, 7)

    def test_subset_materialises_the_rows(self):
        got = calcs.call("train_test_split", {"data": self.data, "seed": 2})
        train = calcs.call("subset", {"data": self.data, "index": got, "which": "train_index"})
        self.assertEqual(len(core.as_rows(train)), len(got["train_index"]))
        self.assertEqual(core.columns_of(train), core.columns_of(self.data))


class KFold(unittest.TestCase):
    def setUp(self):
        self.data = calcs.call("synthetic_regression", {"seed": 1, "n": 23, "d": 2})

    def test_every_row_is_held_out_exactly_once(self):
        got = calcs.call("kfold", {"data": self.data, "seed": 4, "k": 5})
        held = sorted(i for fold in got["folds"] for i in fold["test_index"])
        self.assertEqual(held, list(range(23)))

    def test_folds_are_as_even_as_they_can_be(self):
        got = calcs.call("kfold", {"data": self.data, "seed": 4, "k": 5})
        sizes = sorted(len(f["test_index"]) for f in got["folds"])
        self.assertEqual(sizes, [4, 4, 5, 5, 5])

    def test_train_and_test_never_overlap(self):
        got = calcs.call("kfold", {"data": self.data, "seed": 4, "k": 4})
        for fold in got["folds"]:
            self.assertEqual(set(fold["train_index"]) & set(fold["test_index"]), set())
            self.assertEqual(len(fold["train_index"]) + len(fold["test_index"]), 23)

    def test_k_out_of_range_is_refused(self):
        with self.assertRaises(ValueError):
            calcs.call("kfold", {"data": self.data, "seed": 4, "k": 1})
        with self.assertRaises(ValueError):
            calcs.call("kfold", {"data": self.data, "seed": 4, "k": 99})


class Synthetic(unittest.TestCase):
    def test_regression_carries_the_truth_it_was_built_from(self):
        data = calcs.call("synthetic_regression", {"seed": 8, "n": 10, "d": 4})
        self.assertEqual(len(data["truth"]["coef"]), 4)
        self.assertEqual(core.columns_of(data), ["x0", "x1", "x2", "x3", "y"])
        self.assertEqual(len(core.as_rows(data)), 10)

    def test_blobs_and_counts_are_pure_functions_of_the_seed(self):
        for name, args in (
            ("synthetic_blobs", {"seed": 3, "n": 12, "k": 3}),
            ("synthetic_counts", {"seed": 3, "n": 12, "k": 2, "vocabulary": 5}),
            ("synthetic_classification", {"seed": 3, "n": 12, "k": 2}),
        ):
            self.assertEqual(calcs.call(name, args), calcs.call(name, args), name)

    def test_counts_sum_to_the_document_length(self):
        data = calcs.call("synthetic_counts", {"seed": 3, "n": 10, "k": 2, "vocabulary": 6, "length": 15})
        for row in core.as_rows(data):
            self.assertEqual(sum(row[:-1]), 15)

    def test_column_pulls_one_out(self):
        data = calcs.call("synthetic_blobs", {"seed": 3, "n": 9, "k": 3})
        got = calcs.call("column", {"data": data, "name": "cluster"})
        self.assertEqual(sorted(set(got["values"])), [0.0, 1.0, 2.0])


class TheRegistry(unittest.TestCase):
    def test_every_calculation_is_addressed_under_the_vertical(self):
        for address in calcs.addresses():
            self.assertTrue(address.startswith("fn.brain.ml."), address)

    def test_a_calculation_is_callable_through_the_store(self):
        from pyto import PxC

        pxc = PxC()
        pxc.register(calcs.calc("regression_metrics"))
        got = pxc.call("fn.brain.ml.regression_metrics", {"y_true": [1.0, 2.0], "y_pred": [1.0, 2.0]})
        self.assertAlmostEqual(got["mse"], 0.0)
