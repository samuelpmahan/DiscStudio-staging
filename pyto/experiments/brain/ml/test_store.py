"""the store in the landing is the store the suite verified."""

import json
import os
import unittest

from . import build, parts


def scratch_store(cases):
    """a store that may not commit: it reads the committed store and writes only a scratch one."""
    store = parts.Store("ml")
    assert not store.commit, "a test store must not be able to write what the repository tracks"
    return store


class TheStoreBuilds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = build.build(scratch_store(cls), save=False)
        cls.view = parts.navigate(cls.store)

    def test_every_oracle_passes(self):
        failed = [one["address"] for one in self.view["oracles"]["failed"]]
        self.assertEqual(failed, [], f"oracles that did not pass: {failed}")
        self.assertGreater(self.view["oracles"]["total"], 0)

    def test_every_part_is_lowercase_and_addressed_under_the_contract(self):
        for address in self.store.document():
            self.assertEqual(address, address.lower(), address)
            self.assertTrue(
                address.startswith("px.exp.brain.") or address.startswith("proposal.brain."),
                address,
            )

    def test_every_part_carries_its_for(self):
        for address, value in self.store.document().items():
            if isinstance(value, dict) and not address.startswith("px.exp.brain.result."):
                self.assertIn("for", value, address)
                self.assertTrue(value["for"], address)

    def test_every_part_is_json_able(self):
        document = self.store.document()
        self.assertEqual(json.loads(json.dumps(document)), document)

    def test_the_committed_bracket_still_names_the_same_winner(self):
        import json as _json

        path = os.path.join(parts.STORE_DIR, "ml.json")
        if not os.path.exists(path):
            self.skipTest("store/ml.json is written by python -m experiments.brain.ml.build")
        with open(path, encoding="utf-8") as handle:
            saved = _json.load(handle)
        for address, value in saved.items():
            if address.startswith("px.exp.brain.bracket."):
                self.assertEqual(self.store.get(address)["winner"], value["winner"], address)

    def test_the_map_names_what_was_built(self):
        the_map = self.store.get("px.exp.brain.map.ml")
        self.assertIn("px.exp.brain.result.ml.linreg.regression_closed_np", the_map["built"])
        self.assertTrue(the_map["next"])
        for row in the_map["next"]:
            self.assertTrue(row["for"])

    def test_every_finding_has_its_for_and_its_kind(self):
        findings = [one["address"] for one in self.view["findings"]]
        self.assertTrue(findings)
        for address in findings:
            value = self.store.get(address)
            self.assertIn(value["kind"], ("strength", "friction"))
            self.assertTrue(value["for"])
            if value["kind"] == "friction":
                self.assertIn("proposal", value, address)

    def test_a_benchmark_exists_for_both_backends(self):
        benches = {one["backend"] for one in self.view["benches"]}
        self.assertTrue({"py", "np"} <= benches, benches)

    def test_the_vertical_goes_through_the_shared_harness(self):
        self.assertIs(parts.Store.__bases__[0], parts.harness().Store)
        self.assertIs(parts.oracle, parts.harness().oracle)


class TheCommittedStore(unittest.TestCase):
    """the file on disk says what the run said, benchmarks aside (wall time is not a claim)."""

    @classmethod
    def setUpClass(cls):
        cls.fresh = build.build(scratch_store(cls), save=False).document()

    def test_the_saved_document_matches_a_fresh_build(self):
        path = os.path.join(parts.STORE_DIR, "ml.json")
        if not os.path.exists(path):
            self.skipTest("store/ml.json is written by python -m experiments.brain.ml.build")
        with open(path, encoding="utf-8") as handle:
            saved = json.load(handle)
        fresh = self.fresh
        # a wall time is not a claim, and a bracket's totals are read off wall times.
        moving = ("px.exp.brain.bench.", "px.exp.brain.bracket.")
        stable = lambda d: {k: v for k, v in d.items() if not k.startswith(moving)}
        self.assertEqual(sorted(stable(saved)), sorted(stable(fresh)))
        for address, value in stable(fresh).items():
            self.assertEqual(saved[address], value, address)

    def test_the_committed_record_is_the_one_the_program_leaves(self):
        path = os.path.join(parts.RECORDS_DIR, "ml.regression.json")
        if not os.path.exists(path):
            self.skipTest("records are written by python -m experiments.brain.ml.build")
        with open(path, encoding="utf-8") as handle:
            record = json.load(handle)
        self.assertEqual(record["pcr"], "brain-ml-regression")
        self.assertTrue(record["ticks"])
