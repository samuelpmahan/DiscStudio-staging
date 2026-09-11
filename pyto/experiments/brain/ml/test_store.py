"""the store in the landing is the store the suite verified."""

import json
import os
import unittest

from . import build, parts


class TheStoreBuilds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = build.build(save=False)
        cls.view = parts.navigate(cls.store)

    def test_every_oracle_passes(self):
        failed = [a for a in self.view["oracle"] if not self.store.get(a)["pass"]]
        self.assertEqual(failed, [], f"oracles that did not pass: {failed}")
        self.assertGreater(self.view["oracles_total"], 0)

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

    def test_the_map_names_what_was_built(self):
        the_map = self.store.get("px.exp.brain.map.ml")
        self.assertIn("px.exp.brain.result.ml.linreg.regression_closed_np", the_map["built"])
        self.assertTrue(the_map["next"])
        for row in the_map["next"]:
            self.assertTrue(row["for"])

    def test_every_finding_has_its_for_and_its_kind(self):
        findings = self.view["findings"]
        self.assertTrue(findings)
        for address in findings:
            value = self.store.get(address)
            self.assertIn(value["kind"], ("strength", "friction"))
            self.assertTrue(value["for"])
            if value["kind"] == "friction":
                self.assertIn("proposal", value, address)

    def test_a_benchmark_exists_for_both_backends(self):
        benches = {self.store.get(a)["backend"] for a in self.view["bench"]}
        self.assertEqual(benches, {"py", "np"})


class TheCommittedStore(unittest.TestCase):
    """the file on disk says what the run said, benchmarks aside (wall time is not a claim)."""

    def test_the_saved_document_matches_a_fresh_build(self):
        path = os.path.join(parts.STORE_DIR, "ml.json")
        if not os.path.exists(path):
            self.skipTest("store/ml.json is written by python -m experiments.brain.ml.build")
        with open(path, encoding="utf-8") as handle:
            saved = json.load(handle)
        fresh = build.build(save=False).document()
        stable = lambda d: {k: v for k, v in d.items() if not k.startswith("px.exp.brain.bench.")}
        self.assertEqual(sorted(stable(saved)), sorted(stable(fresh)))
        for address, value in stable(fresh).items():
            self.assertEqual(saved[address], value, address)

    def test_a_record_was_written_for_the_run(self):
        path = os.path.join(parts.RECORDS_DIR, "ml.regression.json")
        if not os.path.exists(path):
            self.skipTest("records are written by python -m experiments.brain.ml.build")
        with open(path, encoding="utf-8") as handle:
            record = json.load(handle)
        self.assertEqual(record["pcr"], "brain-ml-regression")
        self.assertTrue(record["ticks"])
