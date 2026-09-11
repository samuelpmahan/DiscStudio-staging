import json
import os
import shutil
import tempfile
import unittest

import harness

import stats.build as build
import stats.referee as referee

HERE = os.path.dirname(os.path.abspath(__file__))
TRACKED_STORE = os.path.join(os.path.dirname(HERE), "store")
TRACKED_RECORDS = os.path.join(os.path.dirname(HERE), "records")


class BuildOnce(unittest.TestCase):
    """one --quick build into a temp directory, shared by every assertion below.

    a test never writes into a tracked path: the store and the records of this
    run land in a tempdir that is removed again, and the committed
    store/stats.json is produced by running the module by hand.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="brain-stats-build-")
        cls.store_dir = os.path.join(cls.tmp, "store")
        cls.records_dir = os.path.join(cls.tmp, "records")
        cls.store, cls.summary = build.build(cls.store_dir, cls.records_dir, quick=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)


class TestTheBuildWritesNothingTracked(BuildOnce):
    def test_the_store_and_records_are_the_temp_dirs(self):
        self.assertEqual(self.store.store_dir, self.store_dir)
        self.assertEqual(self.store.records_dir, self.records_dir)
        for path in self.store.records:
            self.assertTrue(path.startswith(self.tmp), path)

    def test_saving_lands_in_the_temp_dir_and_reads_back(self):
        path = self.store.save("stats", os.path.join(self.store_dir, "stats.json"))
        self.assertTrue(path.startswith(self.tmp))
        with open(path, encoding="utf-8") as handle:
            held = json.load(handle)
        self.assertEqual(set(held), set(self.store.written))
        fresh = harness.Store(store_dir=self.store_dir, records_dir=self.records_dir)
        loaded = fresh.load_store()
        self.assertEqual(sum(loaded.values()), len(held))


class TestOracles(BuildOnce):
    def test_every_oracle_part_passes(self):
        failures = [a for a in self.store.brain_addresses()
                    if a.startswith("px.exp.brain.oracle.stats.")
                    and not self.store.get(a)["pass"]]
        self.assertEqual(failures, [])
        self.assertEqual(self.summary["oracles_failed"], 0)
        self.assertGreater(self.summary["oracles_passed"], 120)

    def test_every_oracle_part_names_a_reference_and_a_tolerance(self):
        for address in self.store.brain_addresses():
            if not address.startswith("px.exp.brain.oracle.stats."):
                continue
            part = self.store.get(address)
            self.assertTrue(part["reference"])
            self.assertGreater(part["tolerance"], 0.0)
            self.assertTrue(part["for"])
            self.assertEqual(address, address.lower())

    def test_both_backends_of_a_calculation_answer_to_the_same_reference(self):
        by_calc = {}
        for address in self.store.brain_addresses():
            if not address.startswith("px.exp.brain.oracle.stats."):
                continue
            part = self.store.get(address)
            by_calc.setdefault(part["calc"], set()).add(part["reference"])
        self.assertIn("mean", by_calc)
        self.assertEqual(by_calc["mean"], {"numpy.mean"})
        self.assertEqual(by_calc["ttest_ind"], {"scipy.stats.ttest_ind"})


class TestBenchmarksAndResults(BuildOnce):
    def test_the_benchmarks_are_parts_with_a_median_and_a_digest(self):
        benches = [self.store.get(a) for a in self.store.brain_addresses()
                   if a.startswith("px.exp.brain.bench.stats.")]
        self.assertTrue(benches)
        for part in benches:
            self.assertGreaterEqual(part["wall_ms_median"], 0.0)
            self.assertLessEqual(part["wall_ms_min"], part["wall_ms_median"])
            self.assertEqual(len(part["inputs_sha256"]), 64)

    def test_the_run_left_result_parts_and_a_record(self):
        results = [a for a in self.store.brain_addresses()
                   if a.startswith("px.exp.brain.result.stats.")]
        self.assertGreaterEqual(len(results), 5)
        for address in results:
            json.dumps(self.store.get(address))
        self.assertEqual(len(self.store.records), 1)
        with open(self.store.records[0], encoding="utf-8") as handle:
            record = json.load(handle)
        self.assertEqual(record["schema"], "pyto-run-record@1")
        self.assertEqual(record["pcr"], "brain_stats")
        self.assertEqual(len(record["ticks"]), 3)

    def test_the_datasets_are_parts(self):
        for name in ("stats_sample57", "stats_pair63", "stats_groups", "stats_design80"):
            part = self.store.get(harness.data_address(name))
            self.assertTrue(part["for"])
            self.assertEqual(len(part["rows"][0]), len(part["columns"]))


class TestTheOlsTournament(BuildOnce):
    @property
    def bracket(self):
        return self.store.get(harness.bracket_address("stats", "ols_solver"))

    def test_the_criteria_were_written_down_before_the_judging(self):
        criteria = self.bracket["criteria"]
        self.assertEqual([one["name"] for one in criteria],
                         ["correctness", "conditioning", "speed", "clarity"])
        for one in criteria:
            self.assertTrue(one["how"])
            self.assertIn(one["direction"], ("higher", "lower"))

    def test_three_candidates_and_every_one_judged(self):
        branches = [one["branch"] for one in self.bracket["candidates"]]
        self.assertEqual(sorted(branches), ["lstsq", "normal", "qr"])
        judged = {one["candidate"] for one in self.bracket["judged"]}
        self.assertEqual(judged, set(branches))

    def test_the_judge_did_not_build(self):
        branches = {one["branch"] for one in self.bracket["candidates"]}
        for one in self.bracket["judged"]:
            self.assertNotIn(one["judge"], branches)
            self.assertEqual(one["judge"], referee.NAME)
            self.assertTrue(one["note"])

    def test_a_judge_that_built_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            self.store.judge("stats", "ols_solver", "qr", "normal", {"speed": 1.0})
        self.assertIn("did not build", str(caught.exception))

    def test_a_criterion_nobody_recorded_is_refused(self):
        with self.assertRaises(ValueError):
            self.store.judge("stats", "ols_solver", "someone_else", "qr", {"elegance": 1.0})

    def test_the_normal_equations_really_are_the_worst_conditioned(self):
        """the conditioning criterion has to separate the candidates, or it is decoration."""
        scores = {one["candidate"]: one["scores"] for one in self.bracket["judged"]}
        self.assertGreater(scores["normal"]["conditioning"], scores["qr"]["conditioning"] * 100)
        self.assertGreater(scores["normal"]["conditioning"], scores["lstsq"]["conditioning"] * 100)
        for branch in ("normal", "qr", "lstsq"):
            self.assertEqual(scores[branch]["correctness"], 1.0)

    def test_there_is_a_winner_and_it_was_refined(self):
        self.assertIn(self.bracket["winner"], ("normal", "qr", "lstsq"))
        self.assertTrue(self.bracket["refined"])
        self.assertIn(self.bracket["winner"], self.bracket["refinement"]["note"])
        self.assertEqual(self.bracket["refinement"]["address"], "fn.brain.stats.ols")

    def test_the_losers_are_still_in_the_store(self):
        for branch in ("normal", "qr", "lstsq"):
            found = [a for a in self.store.brain_addresses()
                     if a.startswith("px.exp.brain.oracle.stats.")
                     and self.store.get(a)["calc"] == "ols_%s" % branch]
            self.assertTrue(found, branch)

    def test_the_bracket_is_re_runnable_and_decides_the_same_way(self):
        again = harness.Store(store_dir=self.store_dir, records_dir=self.records_dir)
        again.pxc = self.store.pxc
        decided = again.decide("stats", "ols_solver")
        self.assertEqual(decided["winner"], self.bracket["winner"])

    def test_the_facade_default_is_a_candidate_and_the_refinement_says_so(self):
        """the bracket's output is a line of source; the refinement records whether it agrees."""
        import stats.regression as regression

        branches = [one["branch"] for one in self.bracket["candidates"]]
        self.assertIn(regression.DEFAULT_SOLVER, branches)
        note = self.bracket["refinement"]["note"]
        self.assertIn(repr(regression.DEFAULT_SOLVER), note)
        self.assertIn(repr(self.bracket["winner"]), note)
        design = [[1.0], [2.0], [3.0], [5.0]]
        target = [2.0, 4.1, 5.9, 10.2]
        default = regression.ols({"x": design, "y": target})
        named = regression.ols({"x": design, "y": target,
                                "solver": regression.DEFAULT_SOLVER})
        self.assertEqual(default["coefficients"], named["coefficients"])


class TestFindingsAndTheMap(BuildOnce):
    def test_the_findings_are_parts_with_a_kind_and_a_for(self):
        found = [self.store.get(a) for a in self.store.brain_addresses()
                 if a.startswith("proposal.brain.stats.")]
        self.assertGreaterEqual(len(found), 5)
        for part in found:
            self.assertIn(part["kind"], ("strength", "friction"))
            self.assertTrue(part["for"])
            self.assertTrue(part["text"])
            if part["kind"] == "friction":
                self.assertTrue(part.get("proposal"))

    def test_both_kinds_of_finding_are_there(self):
        kinds = {self.store.get(a)["kind"] for a in self.store.brain_addresses()
                 if a.startswith("proposal.brain.stats.")}
        self.assertEqual(kinds, {"strength", "friction"})

    def test_the_map_lists_what_exists_and_what_does_not(self):
        part = self.store.get(harness.map_address("stats"))
        self.assertTrue(part["for"])
        self.assertGreater(len(part["built"]), 100)
        for address in part["built"]:
            self.assertTrue(self.store.has(address), address)
        self.assertGreaterEqual(len(part["stubbed"]), 3)
        for one in part["stubbed"]:
            self.assertFalse(self.store.has(one["address"]))
            self.assertTrue(one["why"])
        self.assertGreaterEqual(len(part["next"]), 3)
        for one in part["next"]:
            self.assertTrue(one["what"])
            self.assertTrue(one["for"])

    def test_navigate_can_see_the_vertical(self):
        seen = self.store.navigate()
        self.assertIn("stats", json.dumps(seen))


class TestEverythingIsLowercaseAndJsonable(BuildOnce):
    def test_every_address_is_lowercase_and_in_the_brain(self):
        for address in self.store.brain_addresses():
            self.assertEqual(address, address.lower())
            self.assertTrue(address.startswith(("px.exp.brain.", "proposal.brain.")), address)

    def test_every_value_survives_json(self):
        for address in self.store.brain_addresses():
            value = self.store.get(address)
            self.assertEqual(json.loads(json.dumps(value)), value, address)


if __name__ == "__main__":
    unittest.main()
