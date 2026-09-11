import json
import unittest

import stats.distributions as distributions
from stats.distributions_cases import BENCH_CASES, FROZEN, ORACLE_CASES, POINTS
from stats.tolerance import close


class Ledger:
    """a stand-in for the run's effects handle: the uniforms a replay would play back."""

    def __init__(self, draws):
        self.draws = list(draws)
        self.asked = []

    def random(self, n):
        self.asked.append(n)
        if n > len(self.draws):
            raise AssertionError("asked for more draws than the ledger holds")
        out, self.draws = self.draws[:n], self.draws[n:]
        return out


class TestOracles(unittest.TestCase):
    def test_every_oracle_case_matches_its_reference(self):
        self.assertGreaterEqual(len(ORACLE_CASES), 40)
        for case in ORACLE_CASES:
            with self.subTest(case=case["case"], calc=case["calc"]):
                got = distributions.CALCS[case["calc"]](case["args"])
                self.assertTrue(
                    close(got, case["expected"](), case["tolerance"]),
                    "%s: got %r, %s says %r" % (case["case"], got, case["reference"],
                                                case["expected"]()))

    def test_every_family_is_covered_on_both_backends(self):
        seen = {(case["calc"], case["backend"]) for case in ORACLE_CASES}
        for calc in ("fn.brain.stats.pdf", "fn.brain.stats.cdf", "fn.brain.stats.ppf"):
            self.assertIn((calc, "py"), seen)
            self.assertIn((calc, "sp"), seen)


class TestBackendsAgree(unittest.TestCase):
    def test_py_and_sp_agree_everywhere(self):
        for dist, (_, params) in FROZEN.items():
            with self.subTest(dist=dist):
                for calc in ("fn.brain.stats.pdf", "fn.brain.stats.cdf", "fn.brain.stats.sf"):
                    fn = distributions.CALCS[calc]
                    py = fn({"dist": dist, "params": params, "x": POINTS[dist], "backend": "py"})
                    sp = fn({"dist": dist, "params": params, "x": POINTS[dist], "backend": "sp"})
                    self.assertTrue(close(sp, py, 1e-7), "%s %s: %r vs %r" % (dist, calc, py, sp))
                qs = [0.01, 0.3, 0.66, 0.99]
                py = distributions.ppf({"dist": dist, "params": params, "q": qs, "backend": "py"})
                sp = distributions.ppf({"dist": dist, "params": params, "q": qs, "backend": "sp"})
                self.assertTrue(close(sp, py, 1e-9), "%s ppf: %r vs %r" % (dist, py, sp))


class TestRoundTrip(unittest.TestCase):
    def test_cdf_of_ppf_is_the_quantile(self):
        for dist, (_, params) in FROZEN.items():
            if dist in distributions.DISCRETE:
                continue
            for q in (0.005, 0.2, 0.5, 0.8, 0.995):
                with self.subTest(dist=dist, q=q):
                    x = distributions.ppf({"dist": dist, "params": params, "q": q})
                    self.assertAlmostEqual(
                        distributions.cdf({"dist": dist, "params": params, "x": x}), q,
                        delta=1e-10)

    def test_a_discrete_ppf_is_the_smallest_k_that_reaches_q(self):
        params = {"n": 20, "p": 0.35}
        for q in (0.05, 0.5, 0.9):
            k = distributions.ppf({"dist": "binomial", "params": params, "q": q})
            self.assertIsInstance(k, int)
            self.assertGreaterEqual(
                distributions.cdf({"dist": "binomial", "params": params, "x": k}), q - 1e-12)
            self.assertLess(
                distributions.cdf({"dist": "binomial", "params": params, "x": k - 1}), q)


class TestSampleIsAnEffect(unittest.TestCase):
    def test_sample_is_an_oc_address(self):
        self.assertTrue(distributions.SAMPLE.address.startswith("oc."))

    def test_sample_pushes_the_ledger_through_the_ppf(self):
        draws = [0.01, 0.25, 0.5, 0.75, 0.99]
        effects = Ledger(draws)
        out = distributions.sample({"dist": "normal", "params": {"mu": 2.0, "sigma": 3.0},
                                    "n": 5, "effects": effects})
        self.assertEqual(effects.asked, [5])
        self.assertEqual(out["n"], 5)
        expected = distributions.ppf({"dist": "normal", "params": {"mu": 2.0, "sigma": 3.0},
                                      "q": draws})
        self.assertTrue(close(out["values"], expected, 1e-12))
        self.assertEqual(json.loads(json.dumps(out)), out)

    def test_the_same_ledger_gives_the_same_sample(self):
        draws = [0.11, 0.42, 0.83]
        first = distributions.sample({"dist": "poisson", "params": {"mu": 4.5}, "n": 3,
                                      "effects": Ledger(draws)})
        second = distributions.sample({"dist": "poisson", "params": {"mu": 4.5}, "n": 3,
                                       "effects": Ledger(draws)})
        self.assertEqual(first, second)

    def test_sample_without_the_handle_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            distributions.sample({"dist": "normal", "n": 3})
        self.assertIn("effects", str(caught.exception))


class TestEdges(unittest.TestCase):
    def test_unknown_family_names_the_families(self):
        with self.assertRaises(ValueError) as caught:
            distributions.cdf({"dist": "cauchy", "x": 0.0})
        self.assertIn("poisson", str(caught.exception))

    def test_unknown_backend_is_refused(self):
        with self.assertRaises(ValueError):
            distributions.cdf({"dist": "normal", "x": 0.0, "backend": "np"})

    def test_impossible_parameters_are_refused(self):
        for args in ({"dist": "normal", "params": {"sigma": 0.0}, "x": 1.0},
                     {"dist": "t", "params": {"df": 0.0}, "x": 1.0},
                     {"dist": "binomial", "params": {"n": 5, "p": 1.5}, "x": 1},
                     {"dist": "poisson", "params": {"mu": -1.0}, "x": 1}):
            with self.assertRaises(ValueError):
                distributions.cdf(args)

    def test_a_quantile_outside_the_unit_interval_is_refused(self):
        with self.assertRaises(ValueError):
            distributions.ppf({"dist": "normal", "q": 1.2})

    def test_the_tails_of_a_ppf(self):
        self.assertEqual(distributions.ppf({"dist": "normal", "q": 0.0}), float("-inf"))
        self.assertEqual(distributions.ppf({"dist": "chi2", "params": {"df": 3.0}, "q": 0.0}), 0.0)

    def test_support_describes_the_family(self):
        self.assertEqual(distributions.support({"dist": "binomial", "params": {"n": 4, "p": 0.5}}),
                         {"dist": "binomial", "kind": "discrete",
                          "reference": "scipy.stats.binom", "params": ["n", "p"]})


class TestJsonAble(unittest.TestCase):
    def test_every_result_survives_json(self):
        for case in ORACLE_CASES:
            got = distributions.CALCS[case["calc"]](case["args"])
            self.assertEqual(json.loads(json.dumps(got)), got)


class TestBenchCases(unittest.TestCase):
    def test_bench_cases_are_paired_and_runnable(self):
        pairs = {}
        for case in BENCH_CASES:
            pairs.setdefault((case["calc"], case["size"]), set()).add(case["backend"])
        for key, backends in pairs.items():
            self.assertEqual(backends, {"py", "sp"}, "%r is not a comparable pair" % (key,))
        sample = BENCH_CASES[0]
        distributions.CALCS[sample["calc"]](sample["make_args"]())


if __name__ == "__main__":
    unittest.main()
