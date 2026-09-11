import unittest

from . import core


class SeedIsTheWholeRandomness(unittest.TestCase):
    def test_same_seed_same_numbers(self):
        a = [core.stream(11).normal() for _ in range(5)]
        b = [core.stream(11).normal() for _ in range(5)]
        self.assertEqual(a, b)

    def test_different_seed_different_numbers(self):
        self.assertNotEqual(core.stream(11).normal(), core.stream(12).normal())

    def test_permutation_is_a_permutation(self):
        self.assertEqual(sorted(core.stream(3).permutation(50)), list(range(50)))

    def test_choice_respects_weights(self):
        rng = core.stream(5)
        draws = [rng.choice([0.0, 1.0, 0.0]) for _ in range(20)]
        self.assertEqual(set(draws), {1})


class LinearAlgebra(unittest.TestCase):
    def test_solve_against_a_hand_case(self):
        # 2x + y = 5, x + 3y = 10  ->  x = 1, y = 3
        self.assertTrue(core.close(core.solve([[2.0, 1.0], [1.0, 3.0]], [5.0, 10.0]), [1.0, 3.0]))

    def test_solve_refuses_a_singular_matrix(self):
        with self.assertRaises(ValueError):
            core.solve([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0])

    def test_matmul_against_numpy(self):
        np = core.numpy()
        a = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        b = [[7.0, 8.0, 9.0], [10.0, 11.0, 12.0]]
        self.assertTrue(core.close(core.matmul(a, b), (np.array(a) @ np.array(b)).tolist()))

    def test_standardize_leaves_zero_mean_unit_sd(self):
        scaled, _, _ = core.standardize([[1.0], [2.0], [3.0], [4.0]])
        column = [row[0] for row in scaled]
        self.assertAlmostEqual(core.mean(column), 0.0)
        self.assertAlmostEqual(core.variance(column), 1.0)


class Datasets(unittest.TestCase):
    def setUp(self):
        self.data = core.dataset("a tiny table", ["a", "b", "y"], [[1, 2, 3], [4, 5, 6]])

    def test_xy_pulls_the_target_out(self):
        matrix, targets, features = core.xy(self.data, "y")
        self.assertEqual(matrix, [[1.0, 2.0], [4.0, 5.0]])
        self.assertEqual(targets, [3.0, 6.0])
        self.assertEqual(features, ["a", "b"])

    def test_xy_refuses_an_absent_target(self):
        with self.assertRaises(KeyError):
            core.xy(self.data, "z")

    def test_values_spelling_is_read_too(self):
        self.assertEqual(core.as_rows({"for": "x", "shape": [1, 2], "values": [[1.0, 2.0]]}), [[1.0, 2.0]])

    def test_close_and_max_error(self):
        self.assertTrue(core.close({"a": [1.0, 2.0]}, {"a": [1.0, 2.0 + 1e-12]}))
        self.assertFalse(core.close([1.0], [1.5]))
        self.assertAlmostEqual(core.max_error([1.0, 2.0], [1.0, 2.5]), 0.5)


class Backends(unittest.TestCase):
    def test_unknown_backend_is_refused(self):
        with self.assertRaises(ValueError):
            core.backend_of({"backend": "cuda"})

    def test_default_is_the_reference(self):
        self.assertEqual(core.backend_of({}), "py")
