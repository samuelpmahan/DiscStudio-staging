"""Executable spec of parallel Ticks and the node law (task 39).

A Tick is the parallel element of the circuit ({?} TicksAsCircuits, owner
2026-09-10: "In electric circuits connections connect in serial or parallel"):
the Calculations inside one Tick are independent branches, so they may run at
the same time, and the two laws that make the drawing honest are checked at
bind time -- no invocation consumes a sibling's produce, no two siblings
produce the same Part.

The oracle every test here turns on: **scheduling is not the program**. The
testimony (`PcrRun.ticks`, `json.dumps([asdict(t) for t in run.ticks])`, the
bytes consumers embed) is byte-identical serial versus parallel, because
placement and durations were never in it and are not added to it now. What a
parallel run adds lives where durations already live: `Receipt.placement` and,
in the record, `placement`, `latency_ms`, `parallel` and `budget`.

Mutation-checked claims (one-line edits applied to a scratch copy of the tree,
never to the repository; see pyto/experiments/tasks/39/packet.md):

    pcr.py:_publish is called in declared order after the      -> publish from the
        whole Tick, so the store never holds half a Tick          worker instead (call
        `self._publish(...)` at the end of `_prepare_parallel.prepare_one`) and
        Placement.test_a_parallel_tick_publishes_in_declared_order fails: the
        writes land in completion order, so the last-declared branch is not the
        last write: killed.
    pcr.py:_refuse_sibling_bindings raises for a ResultRef     -> `continue` instead of
        naming a sibling in the same Tick                         raising and
        NodeLaw.test_a_sibling_result_ref_is_refused_at_bind_time fails (the bind
        is accepted): killed.
    materialize.py:run_record writes `placement` only when     -> write it
        the run reports a schedule                                unconditionally and
        SerialRecordUnchanged.test_a_serial_record_carries_none_of_the_four_new_keys
        fails, and so does experiments/students' grade check 2 (a fresh record no
        longer reproduces the committed one): killed.

Every Calculation body is a named module-level function; no lambdas
(experiments/CAPTURE.md, rule 2).
"""

from __future__ import annotations

import json
import os
import sys
import time
import unittest
from dataclasses import asdict

from pyto import Calculation, Part, PCR, PxC
from pyto.materialize import run_record

PYTO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWER_TEST_DIR = os.path.join(PYTO_ROOT, "viewer", "test")
if VIEWER_TEST_DIR not in sys.path:
    print(f"[tests/test_parallel] sys.path.insert(0, {VIEWER_TEST_DIR!r})", file=sys.stderr)
    sys.path.insert(0, VIEWER_TEST_DIR)

from record_schema import invocation_placement  # noqa: E402
from record_schema import run_schedule, tick_latency_ms  # noqa: E402
from record_schema import validate as validate_record  # noqa: E402

FIXTURE = os.path.join(PYTO_ROOT, "viewer", "fixtures", "pyto-grouped-ablation.json")

#: Each branch of the fanned-out Tick sleeps this long. Real sleep, on purpose:
#: latency is the one claim here that a fake clock cannot make.
BRANCH_SLEEP_MS = 50.0
BRANCHES = 4


def make_seed(args):
    return {"base": args["base"]}


def slow_branch(args):
    """One independent branch: real work, measured in wall time."""
    time.sleep(BRANCH_SLEEP_MS / 1000.0)
    return {"index": args["index"], "value": args["seed"]["base"] + args["index"]}


def gather(args):
    branches = [args[f"branch{index}"] for index in range(BRANCHES)]
    return {"total": sum(branch["value"] for branch in branches), "count": len(branches)}


def echo(args):
    return args["value"]


SEED = Calculation("fn.parallel.seed", make_seed)
BRANCH = Calculation("fn.parallel.branch", slow_branch)
GATHER = Calculation("fn.parallel.gather", gather)
ECHO = Calculation("fn.parallel.echo", echo)


def build_program(name: str = "parallel-fanout") -> PCR:
    """Three Ticks in series; the middle one is four branches in parallel.

    Series and parallel exactly as the circuit reading has them: Prepare and
    Gather are single elements in the wire, Fan is the parallel element. No
    branch of Fan reads another (the node law), and each reads what Prepare
    produced -- the fan-out on the consuming side ({?} TicksAsCircuits, the
    Badge Basket Tee example).
    """
    pcr = PCR(name)
    seed = pcr.calc("Prepare", SEED, id="seed", into=Part("px.parallel.seed"), args={"base": 10})
    branches = [
        pcr.calc(
            "Fan",
            BRANCH,
            id=f"branch{index}",
            into=Part(f"px.parallel.branch.{index}"),
            seed=seed,
            args={"index": index},
        )
        for index in range(BRANCHES)
    ]
    pcr.calc(
        "Gather",
        GATHER,
        id="gather",
        into=Part("px.parallel.total"),
        **{f"branch{index}": ref for index, ref in enumerate(branches)},
    )
    return pcr


def testimony_bytes(run) -> str:
    """The bytes consumers embed: json.dumps([asdict(t) for t in run.ticks])."""
    return json.dumps([asdict(tick) for tick in run.ticks], sort_keys=True)


class Testimony(unittest.TestCase):
    """Scheduling is not the program."""

    def test_the_testimony_bytes_are_identical_serial_and_parallel(self):
        serial = build_program().run(PxC(), observe=True)
        parallel = build_program().run(PxC(), observe=True, parallel=True)
        self.assertEqual(testimony_bytes(serial), testimony_bytes(parallel))

    def test_the_results_are_identical_serial_and_parallel(self):
        serial = build_program().run(PxC(), observe=True)
        parallel = build_program().run(PxC(), observe=True, parallel=True)
        self.assertEqual(serial.results, parallel.results)
        self.assertEqual(serial.results["gather"], {"total": 46, "count": 4})

    def test_the_store_holds_the_same_parts_with_the_same_values(self):
        serial_store, parallel_store = PxC(), PxC()
        build_program().run(serial_store, observe=False)
        build_program().run(parallel_store, observe=False, parallel=True)
        self.assertEqual(serial_store.items(), parallel_store.items())


class Placement(unittest.TestCase):
    def setUp(self):
        self.pxc = PxC()
        self.run = build_program().run(self.pxc, observe=True, parallel=True)
        self.record = run_record(self.run, self.pxc)
        validate_record(self.record)

    def test_every_invocation_of_a_parallel_run_carries_a_placement(self):
        workers = os.cpu_count() or 1
        for tick in self.record["ticks"]:
            for invocation in tick["invocations"]:
                placement = invocation_placement(invocation)
                self.assertIsNotNone(placement, f"{invocation['id']} has no placement")
                self.assertGreaterEqual(placement["worker"], 0)
                self.assertLess(placement["worker"], workers)
                self.assertGreaterEqual(placement["started_ms"], 0.0)

    def test_the_four_branches_really_overlapped(self):
        """Every branch starts before the first one could have finished."""
        fan = next(tick for tick in self.record["ticks"] if tick["name"] == "Fan")
        starts = [invocation_placement(inv)["started_ms"] for inv in fan["invocations"]]
        self.assertEqual(len(starts), BRANCHES)
        for started_ms in starts:
            self.assertLess(started_ms, BRANCH_SLEEP_MS)

    def test_a_parallel_tick_publishes_in_declared_order(self):
        """The store never holds half a Tick, and the order is the program's."""
        fan = next(tick for tick in self.run.ticks if tick.name == "Fan")
        declared = [testimony.id for testimony in fan.calculations]
        self.assertEqual(declared, [f"branch{index}" for index in range(BRANCHES)])
        # Each receipt's `writes` is the invocation's own; the Tick's writes in
        # publication order are the concatenation, and they must be declared order.
        published = [
            write.address
            for testimony in fan.calculations
            for write in self.run.receipts[testimony.id].writes
        ]
        self.assertEqual(
            published, [f"px.parallel.branch.{index}" for index in range(BRANCHES)]
        )
        # Not one branch saw another's Part: a half-Tick would show as a read.
        for testimony in fan.calculations:
            receipt = self.run.receipts[testimony.id]
            self.assertEqual(receipt.actual_consumes, ())

    def test_the_fanned_tick_takes_less_time_than_it_does_work(self):
        """Work adds; time is the longest branch ({?} TicksAsCircuits)."""
        fan = next(tick for tick in self.record["ticks"] if tick["name"] == "Fan")
        work = sum(invocation["duration_ms"] for invocation in fan["invocations"])
        latency = tick_latency_ms(fan)
        self.assertEqual(latency, fan["latency_ms"])
        self.assertGreater(work, BRANCHES * BRANCH_SLEEP_MS * 0.8)
        self.assertLess(
            latency,
            work,
            f"the Fan Tick took {latency:.1f} ms of wall time for {work:.1f} ms of work",
        )
        # Four 50 ms sleeps on at least two workers cannot take four sleeps' time.
        if (os.cpu_count() or 1) >= BRANCHES:
            self.assertLess(latency, BRANCHES * BRANCH_SLEEP_MS * 0.75)

    def test_the_record_says_the_run_was_parallel(self):
        self.assertIs(self.record["parallel"], True)
        schedule = run_schedule(self.record)
        self.assertEqual(
            schedule,
            {
                "parallel": True,
                "budget": {"limit_ms": None, "stopped_after_tick": None, "completed": True},
            },
        )

    def test_a_serial_run_places_nothing(self):
        pxc = PxC()
        run = build_program().run(pxc, observe=True)
        for receipt in run.receipts.values():
            self.assertIsNone(receipt.placement)


class NodeLaw(unittest.TestCase):
    """Both laws, refused at bind time, naming both ids."""

    def test_a_sibling_result_ref_is_refused_at_bind_time(self):
        pcr = PCR("short")
        first = pcr.calc("t", SEED, id="first", into=Part("px.short.a"), args={"base": 1})
        with self.assertRaises(ValueError) as caught:
            pcr.calc("t", ECHO, id="second", into=Part("px.short.b"), value=first)
        message = str(caught.exception)
        self.assertIn("'first'", message)
        self.assertIn("'second'", message)
        self.assertIn("node law", message)

    def test_a_part_binding_on_a_siblings_produce_is_the_same_refusal(self):
        """`Part('px.short.a')` is a read of the sibling's result (ResultReadsAreReads)."""
        pcr = PCR("short-by-address")
        pcr.calc("t", SEED, id="first", into=Part("px.short.a"), args={"base": 1})
        with self.assertRaises(ValueError) as caught:
            pcr.calc("t", ECHO, id="second", into=Part("px.short.b"), value=Part("px.short.a"))
        message = str(caught.exception)
        self.assertIn("'first'", message)
        self.assertIn("'second'", message)

    def test_the_same_binding_in_a_later_tick_is_fine(self):
        pcr = PCR("series")
        first = pcr.calc("t1", SEED, id="first", into=Part("px.series.a"), args={"base": 1})
        pcr.calc("t2", ECHO, id="second", into=Part("px.series.b"), value=first)
        run = pcr.run(PxC(), observe=True)
        self.assertEqual(run.results["second"], {"base": 1})

    def test_two_siblings_producing_one_address_are_refused(self):
        pcr = PCR("two-writers")
        pcr.calc("t", SEED, id="left", into=Part("px.both"), args={"base": 1})
        with self.assertRaises(ValueError) as caught:
            pcr.calc("t", SEED, id="right", into=Part("px.both"), args={"base": 2})
        message = str(caught.exception)
        self.assertIn("'left'", message)
        self.assertIn("'right'", message)
        self.assertIn("px.both", message)
        self.assertIn("node law", message)

    def test_two_siblings_sharing_one_address_of_a_multi_produce_are_refused(self):
        pcr = PCR("two-writers-multi")
        pcr.calc("t", SEED, id="left", into=[Part("px.x"), Part("px.y")], args={"base": 1})
        with self.assertRaises(ValueError) as caught:
            pcr.calc("t", SEED, id="right", into=Part("px.y"), args={"base": 2})
        self.assertIn("'left'", str(caught.exception))
        self.assertIn("px.y", str(caught.exception))

    def test_a_tick_built_without_a_pcr_is_held_to_the_law_too(self):
        from pyto.pcr import Tick

        tick = Tick("standalone")
        first = tick.calc(SEED, id="first", into=Part("px.t.a"), args={"base": 1})
        with self.assertRaises(ValueError) as caught:
            tick.calc(ECHO, id="second", into=Part("px.t.b"), value=first)
        self.assertIn("'first'", str(caught.exception))
        self.assertIn("'second'", str(caught.exception))


class SerialRecordUnchanged(unittest.TestCase):
    """The four new keys are the only difference, and a serial run has none of them."""

    NEW_KEYS = ("parallel", "budget", "latency_ms", "placement")

    def setUp(self):
        self.serial_pxc = PxC()
        self.serial = run_record(
            build_program().run(self.serial_pxc, observe=True), self.serial_pxc
        )
        self.parallel_pxc = PxC()
        self.parallel = run_record(
            build_program().run(self.parallel_pxc, observe=True, parallel=True),
            self.parallel_pxc,
        )

    def test_a_serial_record_carries_none_of_the_four_new_keys(self):
        self.assertNotIn("parallel", self.serial)
        self.assertNotIn("budget", self.serial)
        for tick in self.serial["ticks"]:
            self.assertNotIn("latency_ms", tick)
            for invocation in tick["invocations"]:
                self.assertNotIn("placement", invocation)

    def test_a_serial_records_key_sets_are_the_committed_fixtures(self):
        """Byte level, not shape level: the pre-change record's own key sets."""
        with open(FIXTURE, encoding="utf-8") as handle:
            fixture = json.load(handle)
        self.assertEqual(set(self.serial), set(fixture))
        self.assertEqual(set(self.serial["ticks"][0]), set(fixture["ticks"][0]))
        self.assertEqual(
            set(self.serial["ticks"][0]["invocations"][0]),
            set(fixture["ticks"][0]["invocations"][0]),
        )

    def test_the_committed_fixture_still_validates_and_reads_as_serial(self):
        with open(FIXTURE, encoding="utf-8") as handle:
            fixture = json.load(handle)
        validate_record(fixture)
        self.assertEqual(
            run_schedule(fixture),
            {
                "parallel": False,
                "budget": {"limit_ms": None, "stopped_after_tick": None, "completed": True},
            },
        )
        # Absent latency_ms falls back to the sum of the Tick's durations.
        tick = fixture["ticks"][0]
        self.assertAlmostEqual(
            tick_latency_ms(tick),
            sum(invocation["duration_ms"] for invocation in tick["invocations"]),
            places=6,
        )
        for tick in fixture["ticks"]:
            for invocation in tick["invocations"]:
                self.assertIsNone(invocation_placement(invocation))

    def test_deleting_the_four_new_keys_makes_the_parallel_record_the_serial_one(self):
        self.assertEqual(
            _without_schedule_and_clocks(self.parallel),
            _without_schedule_and_clocks(self.serial),
        )

    def test_a_serial_ticks_latency_is_the_sum_of_its_durations(self):
        """Which is what a series of Calculations means: durations add."""
        pxc = PxC()
        run = build_program().run(pxc, observe=True, budget_ms=10_000.0)
        record = run_record(run, pxc)
        validate_record(record)
        self.assertIs(record["parallel"], False)
        for tick in record["ticks"]:
            self.assertAlmostEqual(
                tick["latency_ms"],
                sum(invocation["duration_ms"] for invocation in tick["invocations"]),
                places=9,
            )


def _without_schedule_and_clocks(record):
    """The record without the four new keys and without any wall clock.

    The wall clocks go for the same reason experiments/students/grade.py drops
    them: `duration_ms` and `wall_ms` move without the program moving. What is
    left is the whole record -- every id, binding, write, digest, value, the
    part index and the counters -- and it must not know how the run was
    scheduled.
    """
    trimmed = {key: value for key, value in record.items() if key not in ("parallel", "budget")}
    trimmed["counters"] = {
        key: value for key, value in record["counters"].items() if key != "wall_ms"
    }
    trimmed["ticks"] = [
        {
            key: value
            for key, value in tick.items()
            if key not in ("latency_ms", "invocations")
        }
        | {
            "invocations": [
                {
                    key: value
                    for key, value in invocation.items()
                    if key not in ("duration_ms", "placement")
                }
                for invocation in tick["invocations"]
            ]
        }
        for tick in record["ticks"]
    ]
    return json.dumps(trimmed, sort_keys=True, indent=2)


if __name__ == "__main__":
    unittest.main()
