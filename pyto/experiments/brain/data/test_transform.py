import json
import unittest

from harness import close

import data.transform as transform
from data.datasets import CUSTOMERS, GAPPY, ORDERS
from data.table import check, column
from data.transform_cases import DRAWS, ORACLE_CASES, BENCH_CASES, Ledger, shape_only


def agrees(got, expected, tolerance=1e-9):
    return close(got, expected, tolerance)[0]


class TestOracles(unittest.TestCase):
    def test_every_oracle_case_matches_its_reference(self):
        self.assertGreaterEqual(len(ORACLE_CASES), 15)
        for case in ORACLE_CASES:
            with self.subTest(case=case["case"], calc=case["calc"]):
                args = dict(case["args"])
                if case["calc"].startswith("oc."):
                    args["effects"] = Ledger(DRAWS)
                got = transform.CALCS[case["calc"]](args)
                project = case.get("project")
                expected = case["expected"]()
                if project:
                    got = project(got)
                    if isinstance(expected, dict) and "columns" in expected:
                        expected = project(expected)
                self.assertTrue(agrees(got, expected, case["tolerance"]),
                                "%s disagrees with %s" % (case["case"], case["reference"]))

    def test_every_calculation_has_a_case(self):
        covered = {case["calc"] for case in ORACLE_CASES}
        self.assertEqual(set(transform.CALCS) - covered, set())


class TestPartsInPartsOut(unittest.TestCase):
    def test_every_result_is_a_dataset_part_that_survives_json(self):
        for case in ORACLE_CASES:
            args = dict(case["args"])
            if case["calc"].startswith("oc."):
                args["effects"] = Ledger(DRAWS)
            got = transform.CALCS[case["calc"]](args)
            check(got, case["case"])
            self.assertTrue(got["for"])
            self.assertEqual(json.loads(json.dumps(got)), got)

    def test_the_input_part_is_never_bent(self):
        before = json.dumps(ORDERS)
        transform.standardize({"table": ORDERS, "column": "items"})
        transform.dedupe({"table": ORDERS})
        transform.sample({"table": ORDERS, "n": 3, "effects": Ledger(DRAWS)})
        self.assertEqual(before, json.dumps(ORDERS))

    def test_a_holes_column_keeps_its_holes(self):
        got = transform.standardize({"table": ORDERS, "column": "price"})
        self.assertEqual([cell is None for cell in column(got, "price_z")],
                         [cell is None for cell in column(ORDERS, "price")])


class TestTheNumericTransforms(unittest.TestCase):
    def test_a_standardised_column_has_mean_zero_and_sd_one(self):
        import stats.descriptive as descriptive

        got = column(transform.standardize({"table": ORDERS, "column": "items"}), "items_z")
        self.assertAlmostEqual(descriptive.mean({"values": got}), 0.0, delta=1e-12)
        self.assertAlmostEqual(descriptive.stdev({"values": got}), 1.0, delta=1e-12)

    def test_a_normalised_column_runs_from_zero_to_one(self):
        got = [v for v in column(transform.normalize({"table": ORDERS, "column": "price"}),
                                 "price_unit") if v is not None]
        self.assertAlmostEqual(min(got), 0.0, delta=1e-15)
        self.assertAlmostEqual(max(got), 1.0, delta=1e-15)

    def test_descending_ranks_are_the_ascending_ones_turned_round(self):
        up = column(transform.rank_column({"table": ORDERS, "column": "items"}), "items_rank")
        down = column(transform.rank_column({"table": ORDERS, "column": "items",
                                             "descending": True}), "items_rank")
        for a, b in zip(up, down):
            self.assertAlmostEqual(a + b, len(up) + 1.0, delta=1e-12)

    def test_equal_width_bins_have_equal_width(self):
        got = transform.bin_column({"table": ORDERS, "column": "items", "bins": 4})
        widths = [got["edges"][i + 1] - got["edges"][i] for i in range(4)]
        for width in widths[1:]:
            self.assertAlmostEqual(width, widths[0], delta=1e-12)

    def test_quantile_bins_share_the_rows_out(self):
        got = transform.bin_column({"table": ORDERS, "column": "items", "bins": 2,
                                    "rule": "quantile", "labels": ["low", "high"]})
        counts = {}
        for label in column(got, "items_bin"):
            counts[label] = counts.get(label, 0) + 1
        self.assertEqual(set(counts), {"low", "high"})
        self.assertLessEqual(abs(counts["low"] - counts["high"]), 4)

    def test_the_two_outlier_rules_agree_on_an_obvious_one(self):
        table = {"for": "one obvious outlier", "columns": ["v"],
                 "rows": [[1.0], [1.1], [0.9], [1.05], [0.95], [1.02], [40.0]]}
        for rule, extra in (("iqr", {}), ("zscore", {"threshold": 2.0})):
            got = transform.outliers(dict(extra, table=table, column="v", rule=rule))
            self.assertEqual(got["outliers"], 1, rule)
            self.assertTrue(column(got, "v_outlier")[-1], rule)

    def test_py_and_np_agree(self):
        for address, args in (
            ("fn.brain.data.standardize", {"table": ORDERS, "column": "items"}),
            ("fn.brain.data.normalize", {"table": ORDERS, "column": "price"}),
            ("fn.brain.data.rank_column", {"table": ORDERS, "column": "items"}),
            ("fn.brain.data.outliers", {"table": ORDERS, "column": "price"}),
            ("fn.brain.data.bin_column", {"table": ORDERS, "column": "items",
                                          "rule": "quantile"}),
        ):
            with self.subTest(calc=address):
                fn = transform.CALCS[address]
                self.assertTrue(agrees(shape_only(fn(dict(args, backend="np"))),
                                       shape_only(fn(dict(args, backend="py")))))

    def test_a_constant_column_cannot_be_rescaled_or_binned(self):
        table = {"for": "flat", "columns": ["v"], "rows": [[3.0], [3.0], [3.0]]}
        for fn in (transform.standardize, transform.normalize, transform.bin_column):
            with self.assertRaises(ValueError):
                fn({"table": table, "column": "v"})

    def test_a_column_with_no_numbers_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            transform.standardize({"table": ORDERS, "column": "region"})
        self.assertIn("region", str(caught.exception))

    def test_a_name_that_is_taken_is_refused(self):
        with self.assertRaises(ValueError):
            transform.standardize({"table": ORDERS, "column": "items", "as": "price"})


class TestTheRelationalTransforms(unittest.TestCase):
    def test_a_crosstab_counts_every_row_once(self):
        got = transform.crosstab({"table": ORDERS, "index": "region", "columns": "customer"})
        total = sum(sum(row[1:]) for row in got["rows"])
        self.assertEqual(total, len(ORDERS["rows"]))

    def test_margins_add_the_totals(self):
        got = transform.crosstab({"table": ORDERS, "index": "region", "columns": "expedited",
                                  "margins": True})
        self.assertEqual(got["columns"][-1], "total")
        self.assertEqual(got["rows"][-1][0], "total")
        self.assertEqual(got["rows"][-1][-1], len(ORDERS["rows"]))

    def test_dedupe_keeps_the_first_or_the_last(self):
        first = transform.dedupe({"table": ORDERS, "subset": ["customer"]})
        last = transform.dedupe({"table": ORDERS, "subset": ["customer"], "keep": "last"})
        self.assertEqual(column(first, "customer"), column(last, "customer"))
        self.assertNotEqual(column(first, "order"), column(last, "order"))

    def test_dedupe_of_a_table_with_no_repeats_changes_nothing(self):
        got = transform.dedupe({"table": CUSTOMERS})
        self.assertEqual(got["rows"], [list(row) for row in CUSTOMERS["rows"]])

    def test_concat_fills_the_columns_one_side_is_missing(self):
        got = transform.concat({"tables": [ORDERS, CUSTOMERS]})
        self.assertEqual(len(got["rows"]), len(ORDERS["rows"]) + len(CUSTOMERS["rows"]))
        self.assertIn("tier", got["columns"])
        self.assertIsNone(got["rows"][0][got["columns"].index("tier")])

    def test_strict_concat_refuses_a_different_header(self):
        with self.assertRaises(ValueError) as caught:
            transform.concat({"tables": [ORDERS, CUSTOMERS], "strict": True})
        self.assertIn("different header", str(caught.exception))

    def test_concat_needs_two(self):
        with self.assertRaises(ValueError):
            transform.concat({"tables": [ORDERS]})


class TestSampleIsAnEffect(unittest.TestCase):
    def test_sample_is_an_oc_address(self):
        self.assertTrue(transform.SAMPLE.address.startswith("oc."))

    def test_it_asks_for_exactly_one_draw_per_row(self):
        effects = Ledger(DRAWS)
        transform.sample({"table": ORDERS, "n": 5, "effects": effects})
        self.assertEqual(effects.asked, [5])

    def test_without_replacement_no_row_comes_twice(self):
        got = transform.sample({"table": ORDERS, "n": 8, "effects": Ledger(DRAWS)})
        orders = column(got, "order")
        self.assertEqual(len(orders), len(set(orders)))

    def test_with_replacement_a_row_may_come_twice(self):
        got = transform.sample({"table": ORDERS, "n": 6, "replace": True,
                                "effects": Ledger([0.1] * 6)})
        self.assertEqual(len(set(column(got, "order"))), 1)

    def test_the_same_ledger_is_the_same_sample(self):
        first = transform.sample({"table": ORDERS, "n": 6, "effects": Ledger(DRAWS)})
        second = transform.sample({"table": ORDERS, "n": 6, "effects": Ledger(DRAWS)})
        self.assertEqual(first, second)

    def test_more_rows_than_there_are_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            transform.sample({"table": ORDERS, "n": 99, "effects": Ledger(DRAWS)})
        self.assertIn("without replacement", str(caught.exception))

    def test_without_the_handle_it_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            transform.sample({"table": ORDERS, "n": 3})
        self.assertIn("effects", str(caught.exception))

    def test_an_empty_table_has_nothing_to_draw(self):
        with self.assertRaises(ValueError):
            transform.sample({"table": {"for": "nothing", "columns": ["a"], "rows": []},
                              "n": 1, "effects": Ledger(DRAWS)})


class TestBenchCases(unittest.TestCase):
    def test_bench_cases_are_paired_and_runnable(self):
        pairs = {}
        for case in BENCH_CASES:
            pairs.setdefault((case["calc"], case["size"]), set()).add(case["backend"])
        for key, backends in pairs.items():
            self.assertEqual(backends, {"py", "np"}, "%r is not a comparable pair" % (key,))
        for case in BENCH_CASES[:3]:
            transform.CALCS[case["calc"]](case["make_args"]())


if __name__ == "__main__":
    unittest.main()
