"""a bracket that cannot be re-run is a memory, not a record."""

import shutil
import tempfile
import unittest

from . import parts, tournament


def scratch_store(cases):
    """a store whose records go to a temp directory: a test never writes a tracked path."""
    directory = tempfile.mkdtemp(prefix="brain-ml-")
    cases.addClassCleanup(shutil.rmtree, directory, True)
    return parts.Store("ml", records_dir=directory)


class EveryBracketRebuilds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decided, cls.store = tournament.run(scratch_store(cls))

    def test_a_bracket_was_decided_for_every_problem(self):
        self.assertTrue(self.decided)
        for part in self.decided.values():
            self.assertIn(part["winner"], [c["branch"] for c in part["candidates"]])

    def test_the_verdict_is_the_same_on_a_second_run(self):
        again, _ = tournament.run(parts.Store("ml", records_dir=self.store.records_dir))
        for name, part in self.decided.items():
            self.assertEqual(again[name]["winner"], part["winner"], name)

    def test_the_criteria_were_recorded_before_any_score(self):
        for part in self.decided.values():
            names = {one["name"] for one in part["criteria"]}
            self.assertEqual(names, {c["name"] for c in tournament.CRITERIA})
            for row in part["judged"]:
                self.assertEqual(set(row["scores"]), names)

    def test_the_judge_did_not_build_a_candidate(self):
        for part in self.decided.values():
            branches = {c["branch"] for c in part["candidates"]}
            for row in part["judged"]:
                self.assertNotIn(row["judge"], branches)

    def test_every_candidate_was_judged_and_none_deleted(self):
        for part in self.decided.values():
            judged = {row["candidate"] for row in part["judged"]}
            self.assertEqual(judged, {c["branch"] for c in part["candidates"]})
            self.assertGreaterEqual(len(part["candidates"]), 2)

    def test_the_winner_is_refined_and_says_so(self):
        for part in self.decided.values():
            refreshed = self.store.get(f"px.exp.brain.bracket.ml.{part['problem']}")
            self.assertTrue(refreshed["refined"])
            self.assertIn(refreshed["winner"], refreshed["refinement"]["note"])

    def test_a_candidate_whose_oracle_failed_cannot_win_on_speed(self):
        """correctness outweighs every other criterion put together."""
        weights = {one["name"]: one["weight"] for one in tournament.CRITERIA}
        self.assertGreater(weights["correct"], sum(v for k, v in weights.items() if k != "correct") - weights["correct"])
        for part in self.decided.values():
            winner = [row for row in part["judged"] if row["candidate"] == part["winner"]][0]
            self.assertEqual(winner["scores"]["correct"], 1.0)

    def test_a_bracket_with_no_criteria_refuses_to_be_judged(self):
        store = parts.Store("ml")
        with self.assertRaises(ValueError):
            parts.bracket(store, "ml", "empty", [], [{"branch": "a"}, {"branch": "b"}], "no criteria")

    def test_the_judge_may_not_be_a_candidate(self):
        store = parts.Store("ml")
        parts.bracket(store, "ml", "small", tournament.CRITERIA,
                      [{"branch": "a"}, {"branch": "b"}], "two branches")
        with self.assertRaises(ValueError):
            parts.judge(store, "ml", "small", "a", "b", {"correct": 1.0})
