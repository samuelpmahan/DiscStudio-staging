import json
import unittest

from harness import close

import data.frame as frame
from data.datasets import CUSTOMERS, GAPPY, ORDERS, READINGS
from data.frame_cases import BENCH_CASES, ORACLE_CASES, shape_only, sorted_shape
from data.table import check, column


def agrees(got, expected, tolerance=1e-9):
    return close(got, expected, tolerance)[0]


class TestOracles(unittest.TestCase):
    def test_every_oracle_case_matches_its_reference(self):
        self.assertGreaterEqual(len(ORACLE_CASES), 20)
        for case in ORACLE_CASES:
            with self.subTest(case=case["case"], calc=case["calc"]):
                got = frame.CALCS[case["calc"]](case["args"])
                project = case.get("project")
                expected = case["expected"]()
                shaped = project(got) if project else got
                wanted = project(expected) if project else expected
                self.assertTrue(
                    agrees(shaped, wanted, case["tolerance"]),
                    "%s: got %r, %s says %r"
                    % (case["case"], shaped, case["reference"], wanted))

    def test_every_case_names_its_authority(self):
        for case in ORACLE_CASES:
            self.assertTrue(case["reference"])
            self.assertIn(case["backend"], ("py", "np"))

    def test_every_calculation_has_a_case(self):
        covered = {case["calc"] for case in ORACLE_CASES}
        self.assertEqual(set(frame.CALCS) - covered, set())


class TestBackendsAgree(unittest.TestCase):
    def test_group_by_py_and_np_agree_cell_for_cell(self):
        args = {"table": ORDERS, "by": ["region"],
                "aggregates": [{"column": "price", "fn": kind} for kind in
                               ("mean", "sum", "median", "min", "max", "std", "var",
                                "count", "count_missing")]}
        py = frame.group_by(dict(args, backend="py"))
        np_ = frame.group_by(dict(args, backend="np"))
        self.assertEqual(py["columns"], np_["columns"])
        self.assertTrue(agrees(np_["rows"], py["rows"]))

    def test_pivot_and_missing_py_and_np_agree(self):
        for args in ({"table": READINGS, "index": "station", "columns": "month",
                      "values": "celsius", "agg": "mean"},):
            py = frame.pivot(dict(args, backend="py"))
            np_ = frame.pivot(dict(args, backend="np"))
            self.assertTrue(agrees(shape_only(np_), shape_only(py)))
        args = {"table": GAPPY, "strategy": "median", "columns": ["reading"]}
        self.assertTrue(agrees(shape_only(frame.missing(dict(args, backend="np"))),
                               shape_only(frame.missing(dict(args, backend="py")))))


class TestPartsInPartsOut(unittest.TestCase):
    def test_every_table_result_is_a_dataset_part(self):
        for case in ORACLE_CASES:
            got = frame.CALCS[case["calc"]](case["args"])
            if isinstance(got, dict) and isinstance(got.get("columns"), list) \
                    and isinstance(got.get("rows"), list):
                check(got, case["case"])
                self.assertIn("for", got)
                self.assertTrue(got["for"])

    def test_results_survive_json(self):
        for case in ORACLE_CASES:
            got = frame.CALCS[case["calc"]](case["args"])
            self.assertEqual(json.loads(json.dumps(got)), got)

    def test_the_input_part_is_never_mutated(self):
        before = json.dumps(ORDERS)
        frame.sort({"table": ORDERS, "by": ["price"]})
        frame.missing({"table": ORDERS, "strategy": "constant", "value": 0.0})
        frame.window({"table": ORDERS, "fn": "row_number", "as": "n"})
        self.assertEqual(before, json.dumps(ORDERS))


class TestJoin(unittest.TestCase):
    def test_inner_drops_the_unmatched_on_both_sides(self):
        got = frame.join({"table": ORDERS, "other": CUSTOMERS, "on": "customer", "how": "inner"})
        self.assertNotIn("eli", column(got, "customer"))
        self.assertNotIn("fay", column(got, "customer"))

    def test_left_keeps_every_left_row(self):
        got = frame.join({"table": ORDERS, "other": CUSTOMERS, "on": "customer", "how": "left"})
        self.assertEqual(len(got["rows"]), len(ORDERS["rows"]))
        self.assertIn("eli", column(got, "customer"))

    def test_outer_keeps_both_orphans(self):
        got = frame.join({"table": ORDERS, "other": CUSTOMERS, "on": "customer", "how": "outer"})
        self.assertIn("eli", column(got, "customer"))
        self.assertIn("fay", column(got, "customer"))

    def test_a_clashing_column_takes_the_suffix(self):
        other = {"for": "a table that clashes", "columns": ["customer", "region"],
                 "rows": [["ada", "north"]]}
        got = frame.join({"table": ORDERS, "other": other, "on": "customer"})
        self.assertIn("region_left", got["columns"])
        self.assertIn("region_right", got["columns"])

    def test_a_missing_key_names_the_columns(self):
        with self.assertRaises(ValueError) as caught:
            frame.join({"table": ORDERS, "other": CUSTOMERS, "on": "nope"})
        self.assertIn("nope", str(caught.exception))

    def test_an_unknown_how_is_refused(self):
        with self.assertRaises(ValueError):
            frame.join({"table": ORDERS, "other": CUSTOMERS, "on": "customer", "how": "cross"})


class TestGroupBy(unittest.TestCase):
    def test_groups_come_out_in_first_seen_order_by_default(self):
        got = frame.group_by({"table": ORDERS, "by": ["region"],
                              "aggregates": [{"fn": "count", "as": "n"}]})
        self.assertEqual(column(got, "region"), ["north", "south", "east", "west"])

    def test_sorted_puts_them_in_order(self):
        got = frame.group_by({"table": ORDERS, "by": ["region"], "sorted": True,
                              "aggregates": [{"fn": "count", "as": "n"}]})
        self.assertEqual(column(got, "region"), ["east", "north", "south", "west"])

    def test_an_all_missing_group_aggregates_to_none(self):
        table = {"for": "one group with nothing in it", "columns": ["k", "v"],
                 "rows": [["a", None], ["a", None], ["b", 2.0]]}
        got = frame.group_by({"table": table, "by": ["k"],
                              "aggregates": [{"column": "v", "fn": "mean"}]})
        self.assertEqual(got["rows"][0][1], None)
        self.assertEqual(got["rows"][1][1], 2.0)

    def test_a_group_of_one_has_no_variance(self):
        table = {"for": "a group of one", "columns": ["k", "v"], "rows": [["a", 3.0]]}
        got = frame.group_by({"table": table, "by": ["k"],
                              "aggregates": [{"column": "v", "fn": "std"}]})
        self.assertIsNone(got["rows"][0][1])

    def test_grouping_by_nothing_is_the_whole_table(self):
        got = frame.group_by({"table": ORDERS, "by": [],
                              "aggregates": [{"column": "price", "fn": "mean"}]})
        self.assertEqual(len(got["rows"]), 1)

    def test_an_unknown_aggregate_names_the_ones_there_are(self):
        with self.assertRaises(ValueError) as caught:
            frame.group_by({"table": ORDERS, "by": ["region"],
                            "aggregates": [{"column": "price", "fn": "mode"}]})
        self.assertIn("nunique", str(caught.exception))

    def test_group_by_needs_an_aggregate(self):
        with self.assertRaises(ValueError):
            frame.group_by({"table": ORDERS, "by": ["region"]})

    def test_a_repeated_output_name_is_refused(self):
        with self.assertRaises(ValueError):
            frame.group_by({"table": ORDERS, "by": ["region"],
                            "aggregates": [{"column": "price", "fn": "mean", "as": "region"}]})


class TestFilterAndSelect(unittest.TestCase):
    def test_or_combines(self):
        got = frame.filter_({"table": ORDERS, "combine": "or",
                             "where": [["region", "eq", "west"], ["items", "gt", 6]]})
        self.assertEqual(sorted(column(got, "order")), [1003, 1006, 1007, 1010])

    def test_no_clauses_keeps_everything(self):
        self.assertEqual(len(frame.filter_({"table": ORDERS})["rows"]), len(ORDERS["rows"]))

    def test_negate_is_the_complement(self):
        kept = frame.filter_({"table": ORDERS, "where": [["region", "eq", "east"]]})
        dropped = frame.filter_({"table": ORDERS, "where": [["region", "eq", "east"]],
                                 "negate": True})
        self.assertEqual(len(kept["rows"]) + len(dropped["rows"]), len(ORDERS["rows"]))

    def test_a_comparison_against_missing_is_false_not_an_error(self):
        got = frame.filter_({"table": ORDERS, "where": [["price", "gt", 0.0]]})
        self.assertEqual(len(got["rows"]), 10)

    def test_in_and_contains(self):
        got = frame.filter_({"table": ORDERS, "where": [["region", "in", ["north", "west"]]]})
        self.assertEqual(len(got["rows"]), 6)
        got = frame.filter_({"table": ORDERS, "where": [["customer", "contains", "d"]]})
        self.assertEqual(set(column(got, "customer")), {"ada", "dee"})

    def test_an_unknown_comparison_names_the_ones_there_are(self):
        with self.assertRaises(ValueError) as caught:
            frame.filter_({"table": ORDERS, "where": [["region", "like", "e%"]]})
        self.assertIn("contains", str(caught.exception))

    def test_a_malformed_clause_is_refused(self):
        with self.assertRaises(ValueError):
            frame.filter_({"table": ORDERS, "where": [["region"]]})

    def test_select_refuses_a_rename_that_collides(self):
        with self.assertRaises(ValueError):
            frame.select({"table": ORDERS, "columns": ["order", "items"],
                          "rename": {"order": "items"}})


class TestWindow(unittest.TestCase):
    def test_lag_and_lead_are_each_other_shifted(self):
        lagged = frame.window({"table": ORDERS, "fn": "lag", "column": "items", "as": "back"})
        led = frame.window({"table": ORDERS, "fn": "lead", "column": "items", "as": "ahead"})
        self.assertIsNone(column(lagged, "back")[0])
        self.assertIsNone(column(led, "ahead")[-1])
        self.assertEqual(column(lagged, "back")[1:], column(ORDERS, "items")[:-1])

    def test_rank_and_dense_rank_differ_on_ties(self):
        table = {"for": "ties", "columns": ["v"], "rows": [[1.0], [1.0], [2.0]]}
        ranked = frame.window({"table": table, "fn": "rank", "column": "v", "as": "r"})
        dense = frame.window({"table": table, "fn": "dense_rank", "column": "v", "as": "r"})
        self.assertEqual(column(ranked, "r"), [1, 1, 3])
        self.assertEqual(column(dense, "r"), [1, 1, 2])

    def test_share_sums_to_one_inside_a_partition(self):
        got = frame.window({"table": ORDERS, "fn": "share", "column": "items",
                            "partition_by": ["region"], "as": "s"})
        totals = {}
        for region, share in zip(column(got, "region"), column(got, "s")):
            totals[region] = totals.get(region, 0.0) + share
        for region, total in totals.items():
            self.assertAlmostEqual(total, 1.0, delta=1e-12, msg=region)

    def test_order_by_orders_inside_the_partition(self):
        got = frame.window({"table": ORDERS, "fn": "cumsum", "column": "items",
                            "partition_by": ["region"], "order_by": "items", "as": "run"})
        by_region = {}
        for region, items, run in zip(column(got, "region"), column(got, "items"),
                                      column(got, "run")):
            by_region.setdefault(region, []).append((items, run))
        for region, pairs in by_region.items():
            pairs.sort()
            self.assertEqual(pairs[0][1], float(pairs[0][0]), region)

    def test_a_numeric_window_over_a_hole_is_refused(self):
        with self.assertRaises(ValueError):
            frame.window({"table": ORDERS, "fn": "cumsum", "column": "price", "as": "run"})

    def test_a_window_name_that_is_taken_is_refused(self):
        with self.assertRaises(ValueError):
            frame.window({"table": ORDERS, "fn": "row_number", "as": "region"})


class TestMissing(unittest.TestCase):
    def test_drop_any_and_drop_all(self):
        self.assertEqual(len(frame.missing({"table": GAPPY})["rows"]), 3)
        self.assertEqual(
            len(frame.missing({"table": GAPPY, "how": "all",
                               "columns": ["reading", "label"]})["rows"]), 5)

    def test_forward_and_backward_leave_the_far_end_alone(self):
        forward = frame.missing({"table": GAPPY, "strategy": "forward", "columns": ["reading"]})
        self.assertIsNone(column(forward, "reading")[0])
        self.assertEqual(column(forward, "reading")[2], 12.0)
        backward = frame.missing({"table": GAPPY, "strategy": "backward", "columns": ["reading"]})
        self.assertEqual(column(backward, "reading")[0], 12.0)
        self.assertIsNone(column(backward, "reading")[-1])

    def test_constant_needs_a_value(self):
        with self.assertRaises(ValueError):
            frame.missing({"table": GAPPY, "strategy": "constant"})

    def test_an_unknown_strategy_names_the_ones_there_are(self):
        with self.assertRaises(ValueError) as caught:
            frame.missing({"table": GAPPY, "strategy": "interpolate"})
        self.assertIn("forward", str(caught.exception))


class TestSortAndShape(unittest.TestCase):
    def test_sort_is_stable_across_keys(self):
        got = frame.sort({"table": ORDERS,
                          "by": ["region", {"column": "items", "descending": True}]})
        self.assertEqual(column(got, "region")[:3], ["east", "east", "east"])
        self.assertEqual(column(got, "items")[:3], [9, 3, 2])

    def test_missing_sorts_first(self):
        got = frame.sort({"table": ORDERS, "by": ["price"]})
        self.assertIsNone(column(got, "price")[0])

    def test_shape_reads_the_kinds(self):
        got = frame.shape({"table": ORDERS})
        self.assertEqual(got["rows"], 12)
        self.assertEqual(got["kinds"]["region"], "text")
        self.assertEqual(got["kinds"]["price"], "number")
        self.assertEqual(got["kinds"]["expedited"], "boolean")

    def test_a_ragged_table_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            frame.shape({"table": {"columns": ["a", "b"], "rows": [[1]]}})
        self.assertIn("header has 2", str(caught.exception))

    def test_an_unknown_backend_is_refused(self):
        with self.assertRaises(ValueError):
            frame.group_by({"table": ORDERS, "by": ["region"], "backend": "sp",
                            "aggregates": [{"fn": "count"}]})


class TestBenchCases(unittest.TestCase):
    def test_bench_cases_are_paired_and_runnable(self):
        pairs = {}
        for case in BENCH_CASES:
            pairs.setdefault((case["calc"], case["size"]), set()).add(case["backend"])
        for key, backends in pairs.items():
            self.assertEqual(backends, {"py", "np"}, "%r is not a comparable pair" % (key,))
        for case in BENCH_CASES[:2]:
            frame.CALCS[case["calc"]](case["make_args"]())


if __name__ == "__main__":
    unittest.main()
