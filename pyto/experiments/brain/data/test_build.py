import json
import os
import shutil
import tempfile
import unittest

import harness

import data.build as build
import data.referee as referee


class BuildOnce(unittest.TestCase):
    """one --quick build into a temp directory. a test never writes a tracked path."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="brain-data-build-")
        cls.store_dir = os.path.join(cls.tmp, "store")
        cls.records_dir = os.path.join(cls.tmp, "records")
        cls.store, cls.summary = build.build(cls.store_dir, cls.records_dir, quick=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)


class TestTheBuildWritesNothingTracked(BuildOnce):
    def test_the_store_and_records_are_the_temp_dirs(self):
        self.assertEqual(self.store.store_dir, self.store_dir)
        for path in self.store.records:
            self.assertTrue(path.startswith(self.tmp), path)

    def test_saving_lands_in_the_temp_dir_and_reads_back(self):
        path = self.store.save("data", os.path.join(self.store_dir, "data.json"))
        self.assertTrue(path.startswith(self.tmp))
        with open(path, encoding="utf-8") as handle:
            held = json.load(handle)
        self.assertEqual(set(held), set(self.store.written))


class TestOracles(BuildOnce):
    def test_every_oracle_part_passes(self):
        failures = [a for a in self.store.brain_addresses()
                    if a.startswith("px.exp.brain.oracle.data.")
                    and not self.store.get(a)["pass"]]
        self.assertEqual(failures, [])
        self.assertEqual(self.summary["oracles_failed"], 0)
        self.assertGreater(self.summary["oracles_passed"], 50)

    def test_every_oracle_part_names_its_authority(self):
        for address in self.store.brain_addresses():
            if not address.startswith("px.exp.brain.oracle.data."):
                continue
            part = self.store.get(address)
            self.assertTrue(part["reference"])
            self.assertTrue(part["for"])
            self.assertEqual(address, address.lower())

    def test_the_relational_cases_say_their_authority_is_a_second_implementation(self):
        relational = [self.store.get(a) for a in self.store.brain_addresses()
                      if a.startswith("px.exp.brain.oracle.data.join.")]
        self.assertTrue(relational)
        for part in relational:
            self.assertIn("independent", part["reference"])


class TestTheRunAndTheDatasets(BuildOnce):
    def test_the_pipeline_run_left_results_and_a_record(self):
        results = [a for a in self.store.brain_addresses()
                   if a.startswith("px.exp.brain.result.data.")]
        self.assertGreaterEqual(len(results), 4)
        self.assertEqual(len(self.store.records), 1)
        with open(self.store.records[0], encoding="utf-8") as handle:
            record = json.load(handle)
        self.assertEqual(record["pcr"], "brain_data")
        self.assertEqual([tick["name"] for tick in record["ticks"]], ["Shape", "Widen", "Smooth"])

    def test_a_step_that_binds_a_sibling_reads_the_result_not_the_store(self):
        with open(self.store.records[0], encoding="utf-8") as handle:
            record = json.load(handle)
        steps = {inv["id"]: inv for tick in record["ticks"] for inv in tick["invocations"]}
        self.assertIn("grouped", steps)
        self.assertIn("fn:kept", json.dumps(steps["grouped"]["inputs"]))

    def test_the_grouped_result_is_a_dataset_part(self):
        part = self.store.get(harness.result_address("data", "group_by", "orders_by_region"))
        self.assertEqual(part["columns"][0], "region")
        self.assertIn("orders", part["columns"])
        self.assertTrue(part["for"])

    def test_every_built_in_table_is_a_dataset_part(self):
        for name in ("orders", "customers", "readings", "gappy", "wide400", "series64"):
            part = self.store.get(harness.data_address(name))
            self.assertTrue(part["for"])
            self.assertTrue(part["rows"])


class TestTheGroupByTournament(BuildOnce):
    @property
    def bracket(self):
        return self.store.get(harness.bracket_address("data", "group_by_aggregation"))

    def test_the_criteria_were_written_down_before_the_judging(self):
        self.assertEqual([one["name"] for one in self.bracket["criteria"]],
                         ["correctness", "speed", "clarity"])
        for one in self.bracket["criteria"]:
            self.assertTrue(one["how"])

    def test_both_backends_are_candidates_and_both_were_judged(self):
        branches = sorted(one["branch"] for one in self.bracket["candidates"])
        self.assertEqual(branches, ["np", "py"])
        self.assertEqual({one["candidate"] for one in self.bracket["judged"]}, set(branches))

    def test_the_judge_did_not_build(self):
        for one in self.bracket["judged"]:
            self.assertEqual(one["judge"], referee.NAME)
            self.assertNotIn(one["judge"], [c["branch"] for c in self.bracket["candidates"]])
            self.assertTrue(one["note"])

    def test_both_candidates_are_correct_so_the_bracket_turns_on_speed(self):
        for one in self.bracket["judged"]:
            self.assertEqual(one["scores"]["correctness"], 1.0)

    def test_there_is_a_winner_and_it_was_refined(self):
        self.assertIn(self.bracket["winner"], ("py", "np"))
        self.assertTrue(self.bracket["refined"])
        self.assertEqual(self.bracket["refinement"]["address"], "fn.brain.data.group_by")

    def test_the_bracket_re_runs_to_the_same_winner(self):
        again = harness.Store(store_dir=self.store_dir, records_dir=self.records_dir)
        again.pxc = self.store.pxc
        self.assertEqual(again.decide("data", "group_by_aggregation")["winner"],
                         self.bracket["winner"])

    def test_the_losing_backend_is_still_reachable(self):
        import data.frame as frame
        from data.datasets import ORDERS

        loser = "np" if self.bracket["winner"] == "py" else "py"
        got = frame.group_by({"table": ORDERS, "by": ["region"], "backend": loser,
                              "aggregates": [{"column": "price", "fn": "mean"}]})
        self.assertTrue(got["rows"])


class TestFindingsAndTheMap(BuildOnce):
    def test_the_findings_are_parts_with_a_kind_and_a_for(self):
        found = [self.store.get(a) for a in self.store.brain_addresses()
                 if a.startswith("proposal.brain.data.")]
        self.assertGreaterEqual(len(found), 4)
        for part in found:
            self.assertIn(part["kind"], ("strength", "friction"))
            self.assertTrue(part["for"])
            if part["kind"] == "friction":
                self.assertTrue(part.get("proposal"))
                self.assertTrue(part.get("workaround"))

    def test_the_map_lists_what_exists_and_what_does_not(self):
        part = self.store.get(harness.map_address("data"))
        self.assertTrue(part["for"])
        self.assertGreater(len(part["built"]), 50)
        for address in part["built"]:
            self.assertTrue(self.store.has(address), address)
        self.assertGreaterEqual(len(part["stubbed"]), 3)
        for one in part["stubbed"]:
            self.assertTrue(one["why"])
        for one in part["next"]:
            self.assertTrue(one["what"])
            self.assertTrue(one["for"])


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
