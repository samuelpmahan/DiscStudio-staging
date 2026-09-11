"""the three brackets, rebuilt from their candidates into a temporary store.

a tournament nobody can re-run is an anecdote. this rebuilds all three and
checks the things that must hold however the wall clock lands on the night: the
criteria were recorded before any judging, no branch judged itself, every
candidate was scored on every criterion, the bracket decides, and the losers are
still there.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from pyto import PQL

from experiments.brain import harness
from experiments.brain.backend import tournament


class TheBrackets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="brain-tournament-")
        cls.store = harness.Store(store_dir=os.path.join(cls.tmp.name, "store"), records_dir=os.path.join(cls.tmp.name, "records"))
        cls.built = tournament.build(cls.store)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def part(self, problem):
        return self.store.get(harness.bracket_address(tournament.VERTICAL, problem))

    def test_all_three_brackets_exist_and_decided(self):
        self.assertEqual(sorted(self.built), ["array_store", "pairwise", "top_k"])
        for problem in self.built:
            part = self.part(problem)
            branches = [one["branch"] for one in part["candidates"]]
            self.assertIn(part["winner"], branches, problem)
            self.assertTrue(part["refined"], problem)
            self.assertGreaterEqual(len(branches), 3, problem)

    def test_the_criteria_were_recorded_before_any_judging(self):
        for problem in self.built:
            part = self.part(problem)
            names = [one["name"] for one in part["criteria"]]
            self.assertIn("correctness", names)
            self.assertIn("speed", names)
            for one in part["criteria"]:
                self.assertTrue(one["how"], f"{problem}/{one['name']} has no how")
            for judged in part["judged"]:
                self.assertEqual(set(judged["scores"]), set(names), problem)

    def test_no_branch_judged_itself(self):
        for problem in self.built:
            part = self.part(problem)
            branches = {one["branch"] for one in part["candidates"]}
            for judged in part["judged"]:
                self.assertNotIn(judged["judge"], branches, problem)
                self.assertEqual(judged["judge"], tournament.JUDGE)

    def test_every_candidate_is_correct_so_speed_is_what_decides(self):
        for problem in self.built:
            for judged in self.part(problem)["judged"]:
                self.assertEqual(judged["scores"]["correctness"], 1.0, f"{problem}/{judged['candidate']}")

    def test_the_unguarded_gram_expansion_is_a_failed_backend(self):
        """the candidate that is not in the bracket, and the reason the guard exists."""
        for size in (16, 64, 192):
            part = self.store.get(harness.oracle_address("backend", "pairwise_tournament", f"py_gram_unguarded_{size}"))
            self.assertFalse(part["pass"], size)
            self.assertGreater(part["worst_relative_error"], part["tolerance"])
            guarded = self.store.get(harness.oracle_address("backend", "pairwise_tournament", f"py_gram_{size}"))
            self.assertTrue(guarded["pass"], size)

    def test_the_losers_are_still_in_the_store(self):
        for problem in self.built:
            part = self.part(problem)
            self.assertEqual(len(part["judged"]), len(part["candidates"]))
            for one in part["candidates"]:
                if one["branch"] == part["winner"]:
                    continue
                self.assertTrue(any(j["candidate"] == one["branch"] for j in part["judged"]))

    def test_the_pure_python_branch_does_not_win_on_speed_at_the_largest_size(self):
        """the point of the arithmetic tournaments: where the engine boundary pays."""
        for problem in ("pairwise", "top_k"):
            self.assertNotIn(self.part(problem)["winner"], ("py_gram", "py_sorted", "py_heap"), problem)

    def test_every_branch_left_its_oracle_and_benchmark_parts(self):
        for problem in self.built:
            oracles = PQL.prefix(f"px.exp.brain.oracle.backend.{problem}_tournament.").matches(self.store.pxc)
            benches = PQL.prefix(f"px.exp.brain.bench.backend.{problem}_tournament.").matches(self.store.pxc)
            self.assertTrue(oracles, problem)
            self.assertTrue(benches, problem)
            self.assertTrue(
                all(match.value["pass"] for match in oracles if "unguarded" not in match.address),
                problem,
            )

    def test_every_candidate_address_in_a_bracket_resolves_to_a_part(self):
        """a bracket that names a Part nobody wrote is a bracket nobody can re-read."""
        for problem in self.built:
            for one in self.part(problem)["candidates"]:
                self.assertTrue(self.store.has(one["address"]), f"{problem}: {one['address']}")

    def test_the_representations_hold_the_same_matrix(self):
        matrix = [[1.5, -2.25], [3.125, 4.0]]
        for name, (encode, decode) in tournament.REPRESENTATIONS.items():
            self.assertEqual(decode(encode(matrix)), matrix, name)

    def test_clarity_is_a_number_off_the_source_and_not_a_vote(self):
        self.assertGreater(tournament.clarity(tournament.pairwise_py_gram), 0.0)
        self.assertEqual(tournament.clarity(lambda args: args), 1.0 - 1 / 40.0)


if __name__ == "__main__":
    unittest.main()
