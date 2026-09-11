import math
import unittest

from scipy import special

from stats.special import betainc, bisect, gammainc, gammaincc, ndtr, ndtri


class TestAgainstScipySpecial(unittest.TestCase):
    def test_gammainc(self):
        for a in (0.5, 1.0, 3.5, 20.0, 200.0):
            for x in (0.01, 0.5, 2.2, 10.0, 50.0, 300.0):
                with self.subTest(a=a, x=x):
                    self.assertAlmostEqual(gammainc(a, x), float(special.gammainc(a, x)),
                                           delta=1e-12)

    def test_gammaincc_is_the_upper_tail(self):
        self.assertAlmostEqual(gammaincc(3.0, 2.0), float(special.gammaincc(3.0, 2.0)),
                               delta=1e-12)

    def test_betainc(self):
        for a, b in ((0.5, 0.5), (2.5, 3.5), (10.0, 1.0), (30.0, 40.0)):
            for x in (0.001, 0.1, 0.4, 0.75, 0.999):
                with self.subTest(a=a, b=b, x=x):
                    self.assertAlmostEqual(betainc(a, b, x), float(special.betainc(a, b, x)),
                                           delta=1e-12)

    def test_ndtr_and_ndtri_are_inverses_of_each_other(self):
        for p in (1e-10, 1e-3, 0.02, 0.5, 0.9, 1 - 1e-9):
            with self.subTest(p=p):
                x = ndtri(p)
                self.assertAlmostEqual(x, float(special.ndtri(p)),
                                       delta=1e-11 * max(1.0, abs(x)))
                self.assertAlmostEqual(ndtr(x), p, delta=1e-14 * max(1.0, p))

    def test_ndtri_at_the_ends(self):
        self.assertEqual(ndtri(0.0), float("-inf"))
        self.assertEqual(ndtri(1.0), float("inf"))

    def test_arguments_out_of_range_are_refused(self):
        for call in (lambda: gammainc(0.0, 1.0), lambda: gammainc(1.0, -1.0),
                     lambda: betainc(0.0, 1.0, 0.5), lambda: betainc(1.0, 1.0, 2.0),
                     lambda: ndtri(1.5)):
            with self.assertRaises(ValueError):
                call()

    def test_bisect_finds_the_crossing(self):
        self.assertAlmostEqual(bisect(lambda v: v * v, 2.0, 0.0, 4.0), math.sqrt(2.0),
                               delta=1e-12)


if __name__ == "__main__":
    unittest.main()
