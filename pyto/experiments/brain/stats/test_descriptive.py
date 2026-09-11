import json
import math
import unittest

import stats.descriptive as descriptive
from stats.tolerance import close
from stats.descriptive_cases import BENCH_CASES, ORACLE_CASES, SAMPLE, TIED, FLAT


class TestOracles(unittest.TestCase):
    def test_every_oracle_case_matches_its_reference(self):
        self.assertGreaterEqual(len(ORACLE_CASES), 30)
        for case in ORACLE_CASES:
            with self.subTest(case=case["case"], calc=case["calc"]):
                calc = descriptive.CALCS[case["calc"]]
                got = calc(case["args"])
                self.assertTrue(
                    close(got, case["expected"](), case["tolerance"]),
                    "%s: got %r, %s says %r" % (case["case"], got, case["reference"], case["expected"]()))

    def test_every_case_names_a_reference_and_a_backend(self):
        for case in ORACLE_CASES:
            self.assertIn(case["backend"], ("py", "np"))
            self.assertTrue(case["reference"].startswith(("numpy.", "scipy.")))
            self.assertEqual(case["args"].get("backend"), case["backend"])
            self.assertEqual(case["case"], case["case"].lower())

    def test_every_calculation_has_a_case(self):
        covered = {case["calc"] for case in ORACLE_CASES}
        missing = set(descriptive.CALCS) - covered - {"fn.brain.stats.describe"}
        self.assertEqual(missing, set())


class TestBackendsAgree(unittest.TestCase):
    def test_py_and_np_agree(self):
        for address, extra in (
            ("fn.brain.stats.mean", {}),
            ("fn.brain.stats.median", {}),
            ("fn.brain.stats.variance", {"ddof": 1}),
            ("fn.brain.stats.stdev", {"ddof": 1}),
            ("fn.brain.stats.quantile", {"q": [0.05, 0.5, 0.95]}),
            ("fn.brain.stats.iqr", {}),
            ("fn.brain.stats.skewness", {"bias": False}),
            ("fn.brain.stats.kurtosis", {"bias": False}),
            ("fn.brain.stats.sem", {}),
            ("fn.brain.stats.zscores", {}),
        ):
            with self.subTest(calc=address):
                calc = descriptive.CALCS[address]
                py = calc(dict(extra, values=SAMPLE, backend="py"))
                np_ = calc(dict(extra, values=SAMPLE, backend="np"))
                self.assertTrue(close(np_, py, 1e-9), "%s: %r vs %r" % (address, py, np_))


class TestEdges(unittest.TestCase):
    def test_unknown_backend_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            descriptive.mean({"values": [1.0], "backend": "cuda"})
        self.assertIn("unknown backend", str(caught.exception))

    def test_empty_sample_is_refused(self):
        for fn in (descriptive.mean, descriptive.median, descriptive.quantile):
            with self.assertRaises(ValueError):
                fn({"values": [], "q": 0.5})

    def test_variance_needs_more_than_its_degrees_of_freedom(self):
        with self.assertRaises(ValueError):
            descriptive.variance({"values": [3.0], "ddof": 1})

    def test_quantile_q_out_of_range(self):
        with self.assertRaises(ValueError):
            descriptive.quantile({"values": SAMPLE, "q": 1.5})

    def test_flat_sample_has_no_skew_and_no_zscores(self):
        self.assertEqual(descriptive.skewness({"values": FLAT}), 0.0)
        with self.assertRaises(ValueError):
            descriptive.zscores({"values": FLAT})

    def test_mode_breaks_a_tie_towards_the_smallest(self):
        self.assertEqual(descriptive.mode({"values": [5.0, 5.0, 1.0, 1.0, 2.0]}),
                         {"mode": 1.0, "count": 2})

    def test_single_value(self):
        self.assertEqual(descriptive.mean({"values": [7.5]}), 7.5)
        self.assertEqual(descriptive.median({"values": [7.5]}), 7.5)
        self.assertEqual(descriptive.variance({"values": [7.5]}), 0.0)


class TestJsonAble(unittest.TestCase):
    def test_every_result_survives_json(self):
        for case in ORACLE_CASES:
            calc = descriptive.CALCS[case["calc"]]
            got = calc(case["args"])
            self.assertEqual(json.loads(json.dumps(got)), got)

    def test_describe_is_one_json_able_bundle(self):
        bundle = descriptive.describe({"values": SAMPLE})
        self.assertEqual(json.loads(json.dumps(bundle)), bundle)
        self.assertEqual(bundle["n"], len(SAMPLE))
        self.assertTrue(math.isfinite(bundle["kurtosis"]))
        self.assertEqual(sorted(descriptive.describe({"values": TIED})),
                         sorted(["n", "mean", "median", "min", "max", "variance",
                                 "stdev", "q25", "q75", "iqr", "skewness", "kurtosis"]))


class TestBenchCases(unittest.TestCase):
    def test_bench_cases_are_runnable_and_paired(self):
        self.assertTrue(BENCH_CASES)
        pairs = {}
        for case in BENCH_CASES:
            self.assertIn(case["backend"], ("py", "np"))
            pairs.setdefault((case["calc"], case["size"]), set()).add(case["backend"])
        for key, backends in pairs.items():
            self.assertEqual(backends, {"py", "np"}, "%r is not a comparable pair" % (key,))
        sample = BENCH_CASES[0]
        args = sample["make_args"]()
        self.assertEqual(args, sample["make_args"]())
        descriptive.CALCS[sample["calc"]](args)


if __name__ == "__main__":
    unittest.main()
