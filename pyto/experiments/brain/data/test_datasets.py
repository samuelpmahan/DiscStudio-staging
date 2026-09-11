import json
import unittest

import data.datasets as datasets
from data.table import check, column


class Reader:
    """a stand-in for the run's effects handle: the file it read lands on a ledger."""

    def __init__(self, files):
        self.files = dict(files)
        self.read = []

    def read_text(self, path):
        self.read.append(path)
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]


CSV = "order,customer,price,expedited\n1,ada,42.50,true\n2,bo,,false\n3,\"cy, jr\",19.99,TRUE\n"
JSON_ROWS = json.dumps([{"a": 1, "b": "x"}, {"a": 2, "c": True}])
JSON_TABLE = json.dumps({"for": "a dataset stored as itself", "columns": ["a"], "rows": [[1], [2]]})


class TestBuiltInDatasets(unittest.TestCase):
    def test_every_built_in_is_a_dataset_part_with_a_for(self):
        for name, table in datasets.BUILT_IN.items():
            with self.subTest(name=name):
                check(table, name)
                self.assertTrue(table["for"])
                self.assertEqual(json.loads(json.dumps(table)), table)

    def test_builtin_hands_back_a_copy_nobody_can_bend(self):
        first = datasets.builtin({"name": "orders"})
        first["rows"][0][0] = 999
        self.assertEqual(datasets.builtin({"name": "orders"})["rows"][0][0], 1001)

    def test_an_unknown_name_lists_the_ones_there_are(self):
        with self.assertRaises(ValueError) as caught:
            datasets.builtin({"name": "titanic"})
        self.assertIn("orders", str(caught.exception))

    def test_missing_is_none_and_never_nan(self):
        for table in datasets.BUILT_IN.values():
            for row in table["rows"]:
                for cell in row:
                    self.assertFalse(isinstance(cell, float) and cell != cell)


class TestLoaderIsAnEffect(unittest.TestCase):
    def test_load_is_an_oc_address(self):
        self.assertTrue(datasets.LOAD.address.startswith("oc."))

    def test_load_reads_csv_through_the_handle(self):
        effects = Reader({"in/orders.csv": CSV})
        got = datasets.load({"path": "in/orders.csv", "effects": effects})
        self.assertEqual(effects.read, ["in/orders.csv"])
        check(got, "the loaded table")
        self.assertEqual(got["columns"], ["order", "customer", "price", "expedited"])
        self.assertEqual(column(got, "price"), [42.50, None, 19.99])
        self.assertEqual(column(got, "expedited"), [True, False, True])
        self.assertEqual(column(got, "customer")[2], "cy, jr")
        self.assertEqual(column(got, "order"), [1, 2, 3])

    def test_load_reads_a_list_of_mappings(self):
        got = datasets.load({"path": "in/rows.json", "format": "json",
                             "effects": Reader({"in/rows.json": JSON_ROWS})})
        self.assertEqual(got["columns"], ["a", "b", "c"])
        self.assertEqual(got["rows"], [[1, "x", None], [2, None, True]])

    def test_load_reads_the_dataset_shape_itself(self):
        got = datasets.load({"path": "in/table.json", "format": "json",
                             "effects": Reader({"in/table.json": JSON_TABLE})})
        self.assertEqual(got["for"], "a dataset stored as itself")
        self.assertEqual(got["rows"], [[1], [2]])

    def test_load_without_the_handle_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            datasets.load({"path": "in/orders.csv"})
        self.assertIn("effects", str(caught.exception))

    def test_load_without_a_path_is_refused(self):
        with self.assertRaises(ValueError):
            datasets.load({"effects": Reader({})})

    def test_an_unknown_format_is_refused(self):
        with self.assertRaises(ValueError):
            datasets.load({"path": "x", "format": "parquet", "effects": Reader({"x": ""})})

    def test_a_ragged_line_names_the_line(self):
        effects = Reader({"bad.csv": "a,b\n1,2\n3\n"})
        with self.assertRaises(ValueError) as caught:
            datasets.load({"path": "bad.csv", "effects": effects})
        self.assertIn("line 3", str(caught.exception))

    def test_the_spellings_of_missing_are_configurable(self):
        effects = Reader({"m.csv": "a,b\n1,-\n2,3\n"})
        got = datasets.load({"path": "m.csv", "missing": ["-"], "effects": effects})
        self.assertEqual(column(got, "b"), [None, 3])

    def test_the_same_text_gives_the_same_part(self):
        first = datasets.load({"path": "in/orders.csv", "effects": Reader({"in/orders.csv": CSV})})
        second = datasets.load({"path": "in/orders.csv", "effects": Reader({"in/orders.csv": CSV})})
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
