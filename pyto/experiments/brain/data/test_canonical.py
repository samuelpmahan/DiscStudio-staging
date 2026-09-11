import unittest

from data.table import canonical


class TestCanonical(unittest.TestCase):
    """a committed store document has to be reproducible on another BLAS."""

    def test_it_rounds_to_twelve_significant_digits(self):
        self.assertEqual(canonical(0.1234567890123456789), 0.123456789012)
        self.assertEqual(canonical(123456789012345.6), 123456789012346.0)

    def test_it_is_idempotent_and_walks_the_whole_shape(self):
        value = {"for": "a table", "columns": ["a"], "rows": [[1.0 / 3.0], [None], ["x"]]}
        self.assertEqual(canonical(value), canonical(canonical(value)))
        self.assertEqual(canonical(value)["rows"][1], [None])
        self.assertEqual(canonical(value)["rows"][2], ["x"])

    def test_the_two_verticals_round_the_same_way(self):
        from stats.tolerance import canonical as stats_canonical

        value = [1.0 / 7.0, 1e-30, 6.02214076e23, 0.0]
        self.assertEqual(canonical(value), stats_canonical(value))


if __name__ == "__main__":
    unittest.main()
