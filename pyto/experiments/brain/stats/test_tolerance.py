import unittest

from stats.tolerance import close


class TestTolerance(unittest.TestCase):
    def test_relative_near_a_big_number(self):
        self.assertTrue(close(1e9, 1e9 + 0.5, 1e-9))
        self.assertFalse(close(1e9, 1e9 + 5.0, 1e-9))

    def test_absolute_near_zero(self):
        self.assertTrue(close(0.0, 1e-12, 1e-9))
        self.assertFalse(close(0.0, 1e-6, 1e-9))

    def test_walks_lists_and_dicts(self):
        self.assertTrue(close({"a": [1.0, 2.0]}, {"a": [1.0, 2.0 + 1e-12]}, 1e-9))
        self.assertFalse(close({"a": [1.0]}, {"a": [1.0], "b": [1.0]}, 1e-9))
        self.assertFalse(close([1.0, 2.0], [1.0], 1e-9))

    def test_strings_bools_and_none_are_exact(self):
        self.assertTrue(close("x", "x"))
        self.assertFalse(close("x", "y"))
        self.assertTrue(close(None, None))
        self.assertFalse(close(1.0, True))
        self.assertFalse(close(None, 0.0))


if __name__ == "__main__":
    unittest.main()
