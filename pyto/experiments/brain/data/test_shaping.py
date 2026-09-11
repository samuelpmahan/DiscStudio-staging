import json
import unittest

from harness import close

import data.frame as frame
import data.shaping as shaping
from data.datasets import GAPPY, ORDERS, READINGS
from data.shaping_cases import ORACLE_CASES, WIDE, shape_only
from data.table import check, column


def agrees(got, expected, tolerance=1e-9):
    return close(got, expected, tolerance)[0]


class TestOracles(unittest.TestCase):
    def test_every_oracle_case_matches_its_reference(self):
        for case in ORACLE_CASES:
            with self.subTest(case=case["case"], calc=case["calc"]):
                got = shaping.CALCS[case["calc"]](case["args"])
                project = case.get("project")
                expected = case["expected"]()
                self.assertTrue(
                    agrees(project(got) if project else got,
                           project(expected) if project else expected, case["tolerance"]),
                    "%s disagrees with %s" % (case["case"], case["reference"]))

    def test_every_calculation_has_a_case(self):
        covered = {case["calc"] for case in ORACLE_CASES}
        self.assertEqual(set(shaping.CALCS) - covered, set())


class TestMelt(unittest.TestCase):
    def test_melt_undoes_pivot(self):
        long = shaping.melt({"table": WIDE, "id_vars": ["station"], "var_name": "month",
                             "value_name": "celsius", "drop_missing": True})
        again = frame.pivot({"table": long, "index": "station", "columns": "month",
                             "values": "celsius", "agg": "mean"})
        self.assertEqual(again["columns"], WIDE["columns"])
        self.assertTrue(agrees(shape_only(again), shape_only(WIDE)))

    def test_every_cell_survives_the_fold(self):
        long = shaping.melt({"table": WIDE, "id_vars": ["station"]})
        self.assertEqual(len(long["rows"]),
                         len(WIDE["rows"]) * (len(WIDE["columns"]) - 1))

    def test_dropping_missing_leaves_the_holes_out(self):
        kept = shaping.melt({"table": WIDE, "id_vars": ["station"]})
        dropped = shaping.melt({"table": WIDE, "id_vars": ["station"], "drop_missing": True})
        self.assertGreater(len(kept["rows"]), len(dropped["rows"]))
        self.assertNotIn(None, column(dropped, "value"))

    def test_the_result_is_a_dataset_part(self):
        long = shaping.melt({"table": ORDERS, "id_vars": ["order"],
                             "value_vars": ["items", "price"]})
        check(long, "the melted table")
        self.assertTrue(long["for"])
        self.assertEqual(json.loads(json.dumps(long)), long)

    def test_a_column_cannot_be_both_an_id_and_a_value(self):
        with self.assertRaises(ValueError) as caught:
            shaping.melt({"table": ORDERS, "id_vars": ["order"], "value_vars": ["order"]})
        self.assertIn("both an id and a value", str(caught.exception))

    def test_a_name_collision_is_refused(self):
        with self.assertRaises(ValueError):
            shaping.melt({"table": ORDERS, "id_vars": ["order"], "value_vars": ["items"],
                          "var_name": "order"})

    def test_a_missing_column_names_itself(self):
        with self.assertRaises(ValueError) as caught:
            shaping.melt({"table": ORDERS, "id_vars": ["nope"]})
        self.assertIn("nope", str(caught.exception))

    def test_nothing_to_fold_is_refused(self):
        with self.assertRaises(ValueError):
            shaping.melt({"table": ORDERS, "id_vars": list(ORDERS["columns"])})


class TestDescribeTable(unittest.TestCase):
    def test_it_is_a_dataset_part_with_one_row_per_column(self):
        got = shaping.describe_table({"table": ORDERS})
        check(got, "the summary")
        self.assertEqual(len(got["rows"]), len(ORDERS["columns"]))
        self.assertEqual(column(got, "column"), list(ORDERS["columns"]))
        self.assertEqual(json.loads(json.dumps(got)), got)

    def test_it_counts_the_holes(self):
        got = shaping.describe_table({"table": GAPPY})
        by_column = {row[0]: row for row in got["rows"]}
        self.assertEqual(by_column["reading"][3], 4)
        self.assertEqual(by_column["step"][3], 0)

    def test_a_text_column_gets_no_numbers(self):
        got = shaping.describe_table({"table": ORDERS})
        by_column = {row[0]: row for row in got["rows"]}
        self.assertEqual(by_column["region"][1], "other")
        self.assertEqual(by_column["region"][5:], [None] * 7)

    def test_the_numbers_are_the_stats_vertical_s_own(self):
        import stats.descriptive as descriptive

        got = shaping.describe_table({"table": ORDERS})
        by_column = {row[0]: row for row in got["rows"]}
        prices = [c for c in column(ORDERS, "price") if c is not None]
        self.assertAlmostEqual(by_column["price"][5],
                               descriptive.mean({"values": prices}), delta=1e-12)
        self.assertAlmostEqual(by_column["price"][8],
                               descriptive.quantile({"values": prices, "q": 0.25}), delta=1e-12)

    def test_py_and_np_agree(self):
        for table in (ORDERS, GAPPY, READINGS):
            with self.subTest(table=table["for"][:20]):
                self.assertTrue(agrees(
                    shape_only(shaping.describe_table({"table": table, "backend": "np"})),
                    shape_only(shaping.describe_table({"table": table, "backend": "py"}))))

    def test_an_unknown_backend_is_refused(self):
        with self.assertRaises(ValueError):
            shaping.describe_table({"table": ORDERS, "backend": "sp"})

    def test_a_chosen_subset_of_columns(self):
        got = shaping.describe_table({"table": ORDERS, "columns": ["price"]})
        self.assertEqual(len(got["rows"]), 1)


if __name__ == "__main__":
    unittest.main()
