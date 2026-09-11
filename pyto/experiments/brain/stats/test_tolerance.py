import unittest

from stats.tolerance import canonical, close


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


class TestCanonical(unittest.TestCase):
    """the rule that makes a committed document a fact about the calculation."""

    def test_it_rounds_to_twelve_significant_digits(self):
        self.assertEqual(canonical(0.1234567890123456789), 0.123456789012)
        self.assertEqual(canonical(123456789012345.6), 123456789012346.0)
        self.assertEqual(canonical(1.5e-17), 1.5e-17)

    def test_it_is_idempotent(self):
        value = {"a": [0.1 / 3.0, 1e300, -2.718281828459045], "b": {"c": 1.0 / 7.0}}
        self.assertEqual(canonical(value), canonical(canonical(value)))

    def test_it_leaves_everything_that_is_not_a_float_alone(self):
        value = {"n": None, "b": True, "s": "x", "i": 7, "l": [1, "two", None]}
        self.assertEqual(canonical(value), value)

    def test_it_survives_the_ends_of_the_line(self):
        for value in (0.0, float("inf"), float("-inf")):
            self.assertEqual(canonical(value), value)
        self.assertNotEqual(canonical(float("nan")), canonical(float("nan")))

    def test_rounding_stays_far_inside_the_tolerance_it_is_measured_against(self):
        for value in (1.0 / 3.0, 1e-8, 1e8, -2.5e-3):
            self.assertTrue(close(canonical(value), value, 1e-9), value)


if __name__ == "__main__":
    unittest.main()
