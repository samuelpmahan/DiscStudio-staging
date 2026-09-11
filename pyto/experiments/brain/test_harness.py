"""every harness helper, through a real PCR run, read back through PQL.

these tests are the harness's contract with the other verticals: if one of them
goes red, someone's Calculations stopped being able to record what they did.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from pyto import Calculation, PQL, Part, PxC

from experiments.brain import example, harness
from experiments.brain.harness import Store


def add_up(args):
    return sum(float(one) for one in args["numbers"])


def halve(args):
    return args["total"] / 2.0


def two_ways(args):
    total = sum(float(one) for one in args["numbers"])
    return {
        "px.exp.brain.result.backend.demo.total": total,
        "px.exp.brain.result.backend.demo.count": len(args["numbers"]),
    }


def add_rows(args):
    return sum(float(row[0]) for row in args["data"]["rows"])


ADD_UP = Calculation("fn.brain.backend.add_up", add_up)
ADD_ROWS = Calculation("fn.brain.backend.add_rows", add_rows)
HALVE = Calculation("fn.brain.backend.halve", halve)
TWO_WAYS = Calculation("fn.brain.backend.two_ways", two_ways)


def fresh(kind="harness") -> tuple[Store, tempfile.TemporaryDirectory]:
    tmp = tempfile.TemporaryDirectory(prefix=f"brain-{kind}-")
    store = Store(store_dir=os.path.join(tmp.name, "store"), records_dir=os.path.join(tmp.name, "records"))
    return store, tmp


class TheStore(unittest.TestCase):
    def setUp(self):
        self.store, self.tmp = fresh()
        self.addCleanup(self.tmp.cleanup)

    def test_a_part_is_json_lowercase_and_inside_the_brain(self):
        self.store.put("px.exp.brain.data.ok", {"for": "a test", "columns": ["a"], "rows": [[1]]})
        self.assertEqual(self.store.get("px.exp.brain.data.ok")["rows"], [[1]])
        with self.assertRaises(ValueError):
            self.store.put("px.exp.brain.data.NotLower", {})
        with self.assertRaises(ValueError):
            self.store.put("px.order.total", 1)
        with self.assertRaises(TypeError):
            self.store.put("px.exp.brain.data.bad", {"for": "x", "rows": object()})

    def test_numpy_comes_back_as_json(self):
        import numpy as np

        self.store.put("px.exp.brain.data.np", {"for": "x", "shape": [2, 2], "values": np.eye(2)})
        value = self.store.get("px.exp.brain.data.np")["values"]
        self.assertEqual(value, [[1.0, 0.0], [0.0, 1.0]])
        json.dumps(value)

    def test_run_publishes_parts_writes_a_record_and_leaves_receipts(self):
        numbers = harness.dataset(self.store, "numbers", "a run with something in it", ["n"], [[1], [2], [3]])
        total = harness.result_address("backend", "add_up", "small")
        half = harness.result_address("backend", "halve", "small")
        run = self.store.run(
            "brain_demo",
            [
                ("sum", [{"id": "total", "calc": ADD_ROWS, "into": total, "inputs": {"data": numbers}}]),
                ("half", [{"id": "half", "calc": HALVE, "into": half, "inputs": {"total": total}}]),
            ],
        )
        self.assertEqual(run.results["total"], 6.0)
        self.assertEqual(self.store.get(half), 3.0)
        self.assertEqual([tick.name for tick in run.ticks], ["sum", "half"])
        self.assertIn("half", run.receipts)
        self.assertEqual(run.receipts["half"].declared_produces, (half,))
        self.assertEqual(
            run.ticks[1].calculations[0].inputs["total"],
            "fn:total",
            "the second tick read the first tick's result, not the store",
        )
        path = os.path.join(self.store.records_dir, "brain_demo.json")
        self.assertTrue(os.path.exists(path))
        with open(path, encoding="utf-8") as handle:
            record = json.load(handle)
        self.assertEqual(record["schema"], "pyto-run-record@1")
        self.assertIn(total, record["parts"])
        self.assertTrue(record["parts"][numbers]["preexisting"])

    def test_a_step_may_publish_several_parts(self):
        run = self.store.run(
            "brain_two_ways",
            [
                (
                    "both",
                    [
                        {
                            "id": "both",
                            "calc": TWO_WAYS,
                            "into": ["px.exp.brain.result.backend.demo.total", "px.exp.brain.result.backend.demo.count"],
                            "args": {"numbers": [1, 2, 3, 4]},
                            "inputs": {},
                        }
                    ],
                )
            ],
        )
        self.assertEqual(run.results["both"]["px.exp.brain.result.backend.demo.count"], 4)
        self.assertEqual(self.store.get("px.exp.brain.result.backend.demo.total"), 10.0)

    def test_save_and_load_store_round_trip_and_merge(self):
        harness.dataset(self.store, "kept", "persistence", ["a"], [[1]])
        path = self.store.save("backend")
        self.assertTrue(path.endswith("backend.json"))
        other = Store(store_dir=self.store.store_dir, records_dir=self.store.records_dir)
        harness.finding(other, "stats", "later", "friction", "written by another vertical", for_="the map must see both")
        other.save("stats")
        merged = Store(store_dir=self.store.store_dir, records_dir=self.store.records_dir)
        loaded = merged.load_store()
        self.assertEqual(sorted(loaded), ["backend.json", "stats.json"])
        self.assertEqual(merged.get("px.exp.brain.data.kept")["rows"], [[1]])
        self.assertEqual(merged.get("proposal.brain.stats.later")["kind"], "friction")
        # saving again merges rather than truncating
        harness.dataset(self.store, "kept2", "persistence", ["a"], [[2]])
        self.store.save("backend")
        with open(path, encoding="utf-8") as handle:
            held = json.load(handle)
        self.assertEqual(sorted(held), ["px.exp.brain.data.kept", "px.exp.brain.data.kept2"])



class WhereAStoreWrites(unittest.TestCase):
    """a test must not dirty the repository.

    a run record holds wall-clock durations, so a suite that rewrites a tracked
    record leaves MAIN dirty and `land.sh` refuses the next landing - for every
    vertical, not only the one whose test wrote it. so the default `Store` reads
    the committed store and writes into a temporary directory, and only an
    explicit record run writes what git tracks.
    """

    def test_the_default_store_writes_nowhere_the_repository_tracks(self):
        store = harness.Store()
        self.assertFalse(store.commit)
        self.assertFalse(store.writes_into_the_repository)
        for directory in (store.store_dir, store.records_dir):
            self.assertFalse(
                os.path.abspath(directory).startswith(os.path.abspath(harness.BRAIN_DIR)),
                directory,
            )

    def test_the_default_store_still_reads_the_committed_store(self):
        self.assertEqual(harness.Store().read_store_dir, harness.STORE_DIR)

    def test_an_explicit_record_run_writes_the_committed_paths(self):
        store = harness.Store(commit=True)
        self.assertEqual(store.store_dir, harness.STORE_DIR)
        self.assertEqual(store.records_dir, harness.RECORDS_DIR)
        self.assertTrue(store.writes_into_the_repository)

    def test_the_environment_says_it_too(self):
        self.assertFalse(harness.committing())
        os.environ["BRAIN_RECORDS"] = "commit"
        self.addCleanup(os.environ.pop, "BRAIN_RECORDS", None)
        self.assertTrue(harness.committing())
        self.assertTrue(harness.Store().writes_into_the_repository)
        self.assertFalse(harness.committing(False), "an explicit flag beats the environment")

    def test_a_default_store_running_a_program_leaves_the_repository_alone(self):
        before = sorted(os.listdir(harness.RECORDS_DIR)) if os.path.isdir(harness.RECORDS_DIR) else []
        store = harness.Store()
        store.run(
            "brain_untracked",
            [("one", [{"id": "one", "calc": ADD_ROWS, "into": "px.exp.brain.result.backend.demo.total",
                       "args": {"data": {"rows": [[1.0], [2.0]]}}}])],
        )
        self.assertTrue(os.path.exists(os.path.join(store.records_dir, "brain_untracked.json")))
        after = sorted(os.listdir(harness.RECORDS_DIR)) if os.path.isdir(harness.RECORDS_DIR) else []
        self.assertEqual(before, after)
        self.assertNotIn("brain_untracked.json", after)


class TheEvidenceParts(unittest.TestCase):
    def setUp(self):
        self.store, self.tmp = fresh("evidence")
        self.addCleanup(self.tmp.cleanup)

    def test_dataset_and_synthetic(self):
        table = harness.dataset(self.store, "table", "a table", ["a", "b"], [[1, 2], [3, 4]])
        self.assertEqual(table, "px.exp.brain.data.table")
        self.assertEqual(harness.values_of(self.store.get(table)), [[1, 2], [3, 4]])
        with self.assertRaises(ValueError):
            harness.dataset(self.store, "ragged", "x", ["a", "b"], [[1]])
        drawn = harness.synthetic(self.store, "drawn", "a draw", seed=7, shape=(3, 2))
        value = self.store.get(drawn)
        self.assertEqual(value["shape"], [3, 2])
        self.assertEqual(len(value["values"]), 3)
        again = Store(store_dir=self.store.store_dir, records_dir=self.store.records_dir)
        harness.synthetic(again, "drawn", "a draw", seed=7, shape=(3, 2))
        self.assertEqual(again.get(drawn)["values"], value["values"], "the seed is the part")
        spd = self.store.get(harness.synthetic(self.store, "spd", "square", seed=3, shape=(4, 4), kind="spd"))
        self.assertEqual(spd["shape"], [4, 4])
        with self.assertRaises(ValueError):
            harness.synthetic(self.store, "nope", "x", seed=1, shape=(2, 2), kind="unheard_of")

    def test_oracle_passes_and_fails_and_keeps_the_evidence(self):
        ok = harness.oracle(self.store, "backend", "solve", "small", got=[1.0, 2.0], expected=[1.0, 2.0 + 1e-12], reference="numpy.linalg.solve", for_="x")
        self.assertTrue(ok)
        bad = harness.oracle(self.store, "backend", "solve", "wrong", got=[1.0, 2.5], expected=[1.0, 2.0], reference="numpy.linalg.solve", for_="x")
        self.assertFalse(bad)
        part = self.store.get(harness.oracle_address("backend", "solve", "wrong"))
        self.assertEqual(part["got"], [1.0, 2.5])
        self.assertGreater(part["worst_relative_error"], 0.2)
        self.assertFalse(harness.close([1.0], [1.0, 2.0])[0], "a different shape is not close")
        self.assertTrue(harness.close({"a": float("nan")}, {"a": float("nan")})[0], "nan matches nan")


    def test_a_big_value_is_outlined_rather_than_copied_into_the_oracle_part(self):
        """an oracle Part is evidence; it is not a second copy of every matrix.

        the verdict is still decided on the full values - that is the whole point -
        but what the Part keeps of a 192x192 matrix is its size, its digest, its
        shape and its first numbers. Before this cap the three pairwise tournaments
        put 6.5 MB of decimal text into store/backend.json.
        """
        wide = {"shape": [120, 120], "values": [[float(row * 120 + column) for column in range(120)] for row in range(120)]}
        kept = harness.outline(wide)
        self.assertEqual(kept["shape"], [120, 120], "the readable parts of a mapping stay readable")
        self.assertTrue(kept["values"]["outline"])
        self.assertEqual(kept["values"]["shape"], [120, 120])
        self.assertEqual(kept["values"]["head"], [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
        self.assertEqual(kept["values"]["sha256"], harness.digest(wide["values"]))
        self.assertLess(len(json.dumps(kept)), 1000)

        self.assertTrue(harness.oracle(self.store, "backend", "wide", "same", got=wide, expected=wide,
                                       reference="itself", for_="the comparison is on the full value"))
        wrong = json.loads(json.dumps(wide))
        wrong["values"][0][0] = 99.0
        self.assertFalse(harness.oracle(self.store, "backend", "wide", "different", got=wrong, expected=wide,
                                        reference="itself", for_="an outlined Part still knows it failed"))
        part = self.store.get(harness.oracle_address("backend", "wide", "different"))
        self.assertNotEqual(part["got"]["values"]["sha256"], part["expected"]["values"]["sha256"])
        self.assertLess(len(json.dumps(part)), 2000)

    def test_a_small_value_is_kept_whole(self):
        self.assertEqual(harness.outline([1.0, 2.0]), [1.0, 2.0])
        self.assertEqual(harness.shape_of([[1.0, 2.0], [3.0, 4.0]]), [2, 2])

    def test_bench_records_median_min_and_a_digest(self):
        value = harness.bench(self.store, "backend", "mean", "py", 128, lambda: sum(range(1000)), n=3, for_="x", inputs={"size": 128})
        self.assertEqual(value["n"], 3)
        self.assertGreaterEqual(value["wall_ms_median"], value["wall_ms_min"])
        self.assertEqual(len(value["inputs_sha256"]), 64)
        self.assertEqual(
            value["inputs_sha256"],
            harness.digest({"size": 128}),
            "the same inputs digest the same way, so two benchmarks are comparable",
        )
        self.assertTrue(self.store.has("px.exp.brain.bench.backend.mean.py.128"))


class TheTournament(unittest.TestCase):
    def setUp(self):
        self.store, self.tmp = fresh("bracket")
        self.addCleanup(self.tmp.cleanup)
        self.criteria = [
            {"name": "correctness", "how": "oracle parts pass", "direction": "higher", "weight": 2.0},
            {"name": "speed", "how": "wall_ms_median", "direction": "lower"},
        ]
        self.candidates = [
            {"branch": "branch_a", "calc": "fn.brain.backend.pairwise", "address": "px.exp.brain.result.backend.pairwise.a"},
            {"branch": "branch_b", "calc": "fn.brain.backend.pairwise", "address": "px.exp.brain.result.backend.pairwise.b"},
        ]

    def open_one(self):
        return harness.bracket(self.store, "backend", "pairwise", self.criteria, self.candidates, for_="x")

    def test_criteria_are_written_before_any_judging(self):
        with self.assertRaises(ValueError):
            harness.bracket(self.store, "backend", "pairwise", [], self.candidates, for_="x")
        with self.assertRaises(ValueError):
            harness.bracket(self.store, "backend", "pairwise", self.criteria, self.candidates[:1], for_="x")
        address = self.open_one()
        part = self.store.get(address)
        self.assertEqual([one["name"] for one in part["criteria"]], ["correctness", "speed"])
        self.assertEqual(part["judged"], [])
        self.assertIsNone(part["winner"])

    def test_a_judge_did_not_build_and_scores_only_the_recorded_criteria(self):
        self.open_one()
        with self.assertRaises(ValueError):
            harness.judge(self.store, "backend", "pairwise", "branch_a", "branch_b", {"correctness": 1.0})
        with self.assertRaises(ValueError):
            harness.judge(self.store, "backend", "pairwise", "reader", "branch_c", {"correctness": 1.0})
        with self.assertRaises(ValueError):
            harness.judge(self.store, "backend", "pairwise", "reader", "branch_a", {"vibes": 1.0})

    def test_decide_needs_every_candidate_judged_then_names_the_winner(self):
        address = self.open_one()
        harness.judge(self.store, "backend", "pairwise", "reader", "branch_a", {"correctness": 1.0, "speed": 90.0}, "correct, slow")
        with self.assertRaises(ValueError):
            harness.decide(self.store, "backend", "pairwise")
        harness.judge(self.store, "backend", "pairwise", "reader", "branch_b", {"correctness": 1.0, "speed": 3.0}, "correct, fast")
        part = harness.decide(self.store, "backend", "pairwise")
        self.assertEqual(part["winner"], "branch_b", "same correctness, lower is better on speed")
        self.assertEqual(len(part["judged"]), 2, "losers stay in the bracket; nothing is deleted")
        harness.refine(self.store, "backend", "pairwise", "the winner became the default")
        self.assertTrue(self.store.get(address)["refined"])

    def test_a_judgment_is_replaced_not_doubled(self):
        self.open_one()
        harness.judge(self.store, "backend", "pairwise", "reader", "branch_a", {"correctness": 0.0})
        harness.judge(self.store, "backend", "pairwise", "reader", "branch_a", {"correctness": 1.0})
        judged = self.store.get(harness.bracket_address("backend", "pairwise"))["judged"]
        self.assertEqual(len(judged), 1)
        self.assertEqual(judged[0]["scores"]["correctness"], 1.0)


class FindingsAndTheMap(unittest.TestCase):
    def setUp(self):
        self.store, self.tmp = fresh("map")
        self.addCleanup(self.tmp.cleanup)

    def test_a_finding_is_a_part_with_its_for(self):
        address = harness.finding(self.store, "backend", "store_fights_arrays", "friction", "a 65536-element array is a json list in the record", for_="records get large fast", workaround="digest the array, store the shape", proposal="a part value that is bytes")
        self.assertEqual(address, "proposal.brain.backend.store_fights_arrays")
        value = self.store.get(address)
        self.assertEqual(value["kind"], "friction")
        self.assertIn("workaround", value)
        with self.assertRaises(ValueError):
            harness.finding(self.store, "backend", "x", "opinion", "no", for_="no")

    def test_the_map_part_says_built_stubbed_and_next(self):
        address = harness.map_part(
            self.store,
            "backend",
            built=["px.exp.brain.result.backend.matmul.small"],
            stubbed=[{"address": "px.exp.brain.result.backend.fft.large", "why": "no py engine worth the lines"}],
            next_=[{"what": "sparse", "for": "the ml vertical"}],
            for_="what the backend has",
        )
        self.assertEqual(address, "px.exp.brain.map.backend")
        self.assertEqual(self.store.get(address)["stubbed"][0]["why"], "no py engine worth the lines")


class Navigating(unittest.TestCase):
    def test_the_example_builds_and_navigate_reads_it_all_back_through_pql(self):
        store, tmp = fresh("navigate")
        self.addCleanup(tmp.cleanup)
        example.build(store)

        # everything the example wrote is readable as parts, through PQL, not through python state
        pxc = store.pxc
        self.assertEqual(
            PQL.part("px.exp.brain.map.backend").one(pxc)["next"][0]["for"],
            "the stats and ml verticals, which cannot start without them",
        )
        oracles = PQL.prefix("px.exp.brain.oracle.").matches(pxc)
        self.assertEqual(len(oracles), 2)
        self.assertTrue(all(match.value["pass"] for match in oracles), "py and np must agree with numpy")
        self.assertEqual(len(PQL.prefix("px.exp.brain.bench.backend.mean.").addresses(pxc)), 6)
        failing = PQL.prefix("px.exp.brain.oracle.").where(lambda match: not match.value["pass"]).addresses(pxc)
        self.assertEqual(failing, ())
        self.assertTrue(PQL.prefix("px.receipt.brain_example.").addresses(pxc), "the run was observed")

        seen = harness.navigate(store)
        self.assertEqual(seen["counts"]["oracle"]["backend"], 2)
        self.assertEqual(seen["counts"]["bench"]["backend"], 6)
        self.assertEqual(seen["counts"]["data"]["data"], 1)
        self.assertEqual(seen["oracles"]["failed"], [])
        self.assertEqual([one["winner"] for one in seen["won"]], ["engine_np"])
        self.assertTrue(seen["won"][0]["refined"])
        self.assertEqual(seen["unjudged"], [])
        self.assertEqual(seen["stubbed"][0]["vertical"], "backend")
        self.assertEqual([one["kind"] for one in seen["findings"]], ["strength"])

        page = harness.territory(store)
        for expected in ("the pxc brain, read back through pql", "oracles: 2 (0 failed)", "won      example_mean: engine_np", "findings"):
            self.assertIn(expected, page)

        # and the whole territory survives a save/load into a fresh process's store
        store.save("backend")
        again = Store(store_dir=store.store_dir, records_dir=store.records_dir)
        again.load_store()
        self.assertEqual(harness.navigate(again)["won"], seen["won"])
        self.assertTrue(os.path.exists(os.path.join(store.records_dir, "brain_example.json")))

    def test_navigate_on_an_empty_store_says_nothing_rather_than_raising(self):
        store, tmp = fresh("empty")
        self.addCleanup(tmp.cleanup)
        store.load_store()
        seen = harness.navigate(store)
        self.assertEqual(seen["addresses"], 0)
        self.assertEqual(seen["counts"], {})
        self.assertIn("parts: 0", harness.territory(store))


class TheMapModule(unittest.TestCase):
    def test_python_m_experiments_brain_map_prints_the_territory(self):
        import subprocess
        import sys

        pyto = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        done = subprocess.run([sys.executable, "-m", "experiments.brain.map"], cwd=pyto, capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("the pxc brain, read back through pql", done.stdout)


if __name__ == "__main__":
    unittest.main()
