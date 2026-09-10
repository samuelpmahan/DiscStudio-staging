"""Executable spec of parallel Ticks and the node law (task 39).

Inside a Tick the Calculations are a sequence in declared order, and the Tick
boundary is where that sequence becomes inspectable ({?} ChainsInsideATick,
owner 2026-09-10: "your existing ChainSpot program deliberately chains
dependent Calculations inside a Tick. Your definition was the moment that
sequence becomes inspectable"). A Tick in which no Calculation reads a sibling
may run at once; a Tick with such a read is a chain and runs in order whatever
the run's `parallel` says. Two things are refused at bind time: a read of a
Part a *later* sibling produces, and two siblings producing one Part.

The oracle every test here turns on: **scheduling is not the program**. The
testimony (`PcrRun.ticks`, `json.dumps([asdict(t) for t in run.ticks])`, the
bytes consumers embed) is byte-identical serial versus parallel, because
placement and durations were never in it and are not added to it now. What a
parallel run adds lives where durations already live: `Receipt.placement` and,
in the record, `placement`, `latency_ms`, `parallel` and `budget`.

Mutation-checked claims (one-line edits applied to a scratch copy of the tree,
never to the repository; see pyto/experiments/tasks/39/packet.md):

    pcr.py:run publishes a parallel Tick in declared order,    -> publish
        after the whole Tick                                       `reversed(prepared)`
        and Placement.test_a_parallel_tick_publishes_in_declared_order_after_the_-
        whole_tick fails at the store's own write order (branch.3 is written
        first): killed.
    pcr.py:run runs a chained Tick in declared order under   -> send it to the
        parallel=True                                             pool and
        NodeLaw.test_a_sibling_result_ref_is_a_chain fails (the later link binds a
        result that is not there yet): killed.
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
import threading
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


#: What happened, in the order it happened: ("finished", <branch id>) from a
#: Calculation body, ("wrote", <address>) from the store. The only oracle that can
#: see "the store never held half a Tick", because nothing in the record does.
EVENTS: list[tuple[str, str]] = []
EVENTS_LOCK = threading.Lock()


def note(kind: str, name: str) -> None:
    with EVENTS_LOCK:
        EVENTS.append((kind, name))


class RecordingPxC(PxC):
    """A PxC that remembers the order its Parts were written in, and nothing else.

    It relays every keyword it is given rather than deciding anything: a view
    that swallowed `_from_run` would refuse the run's own receipts (core.py's
    receipt guard, task 41), and a view that invented it would forge them.
    """

    def set(self, part, value, **marker):
        note("wrote", part if isinstance(part, str) else part.address)
        return super().set(part, value, **marker)


def slow_branch(args):
    """One independent branch: real work, measured in wall time."""
    time.sleep(BRANCH_SLEEP_MS / 1000.0)
    note("finished", f"branch{args['index']}")
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
        """As many branches as there are workers start before the first one finishes.

        Measured against the branches themselves, not a wall-clock budget: a
        slow runner starts its threads late (a macOS runner took 114 ms to start
        four, against a 50 ms sleep), and a runner with fewer cores than branches
        cannot overlap all of them (the pool is `min(len(tick), cpu_count)`
        workers). What parallel means is that the pool was full while the first
        branch was still running, and that is what is asserted.
        """
        fan = next(tick for tick in self.record["ticks"] if tick["name"] == "Fan")
        spans = [
            (invocation_placement(inv)["started_ms"], inv["duration_ms"])
            for inv in fan["invocations"]
        ]
        self.assertEqual(len(spans), BRANCHES)
        first_finish = min(started + duration for started, duration in spans)
        overlapping = sum(1 for started, _ in spans if started < first_finish)
        workers = max(1, min(BRANCHES, os.cpu_count() or 1))
        self.assertGreaterEqual(
            overlapping,
            min(BRANCHES, workers),
            f"only {overlapping} of {BRANCHES} branches had started when the first "
            f"finished at {first_finish:.1f} ms, on a pool of {workers}: {spans}",
        )

    def test_a_parallel_tick_publishes_in_declared_order_after_the_whole_tick(self):
        """The store never holds half a Tick, and the order is the program's.

        Watched at the store, because that is the only place it shows: every
        branch finishes before the first branch Part is written, and the four
        writes are in declared order however the pool ordered the work.
        """
        del EVENTS[:]
        pxc = RecordingPxC()
        build_program().run(pxc, observe=True, parallel=True)
        fan = [
            (kind, name)
            for kind, name in EVENTS
            if name.startswith("branch") or name.startswith("px.parallel.branch.")
        ]
        writes = [name for kind, name in fan if kind == "wrote"]
        self.assertEqual(
            writes, [f"px.parallel.branch.{index}" for index in range(BRANCHES)]
        )
        first_write = next(index for index, (kind, _) in enumerate(fan) if kind == "wrote")
        finished_first = sorted(name for kind, name in fan[:first_write] if kind == "finished")
        self.assertEqual(finished_first, [f"branch{index}" for index in range(BRANCHES)])
        # Not one branch saw another's Part either: a half-Tick would show as a read.
        for index in range(BRANCHES):
            self.assertEqual(self.run.receipts[f"branch{index}"].actual_consumes, ())

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
    """A chain inside a Tick runs; the two refusals that remain name both ids."""

    def test_a_sibling_result_ref_is_a_chain(self):
        """The later link binds the earlier one's result and runs after it, serial or parallel."""
        for parallel in (False, True):
            with self.subTest(parallel=parallel):
                pcr = PCR("chain")
                first = pcr.calc("t", SEED, id="first", into=Part("px.chain.a"), args={"base": 1})
                pcr.calc("t", ECHO, id="second", into=Part("px.chain.b"), value=first)
                pxc = PxC()
                run = pcr.run(pxc, observe=True, parallel=parallel)
                self.assertEqual(run.results["second"], {"base": 1})
                self.assertEqual(pxc.get(Part("px.chain.b")), {"base": 1})

    def test_a_part_binding_on_a_siblings_produce_is_the_same_chain(self):
        """`Part('px.chain.a')` is a read of the sibling's result (ResultReadsAreReads)."""
        pcr = PCR("chain-by-address")
        pcr.calc("t", SEED, id="first", into=Part("px.chain.a"), args={"base": 1})
        pcr.calc("t", ECHO, id="second", into=Part("px.chain.b"), value=Part("px.chain.a"))
        self.assertTrue(pcr.tick("t").chained())
        run = pcr.run(PxC(), observe=True, parallel=True)
        self.assertEqual(run.results["second"], {"base": 1})

    def test_a_chain_runs_in_order_on_one_worker_and_testifies_the_same(self):
        """Under parallel=True a chained Tick is placed on worker 0, one after another,
        and its testimony is the serial run's bytes."""
        def program():
            pcr = PCR("chain-placed")
            a = pcr.calc("t", SEED, id="a", into=Part("px.cp.a"), args={"base": 2})
            b = pcr.calc("t", ECHO, id="b", into=Part("px.cp.b"), value=a)
            pcr.calc("t", ECHO, id="c", into=Part("px.cp.c"), value=b)
            return pcr
        serial_pxc, parallel_pxc = PxC(), PxC()
        serial = program().run(serial_pxc, observe=True)
        parallel = program().run(parallel_pxc, observe=True, parallel=True)
        self.assertEqual(testimony_bytes(serial), testimony_bytes(parallel))
        record = run_record(parallel, parallel_pxc)
        validate_record(record)
        tick = record["ticks"][0]
        placements = [invocation_placement(inv) for inv in tick["invocations"]]
        self.assertEqual([p["worker"] for p in placements], [0, 0, 0])
        starts = [p["started_ms"] for p in placements]
        self.assertEqual(starts, sorted(starts))

    def test_the_same_binding_in_a_later_tick_is_fine(self):
        pcr = PCR("series")
        first = pcr.calc("t1", SEED, id="first", into=Part("px.series.a"), args={"base": 1})
        pcr.calc("t2", ECHO, id="second", into=Part("px.series.b"), value=first)
        self.assertFalse(pcr.tick("t1").chained())
        run = pcr.run(PxC(), observe=True)
        self.assertEqual(run.results["second"], {"base": 1})

    def test_a_read_of_a_later_sibling_is_refused(self):
        """The sequence runs in declared order, so a Part a later sibling produces is not there yet."""
        pcr = PCR("backwards")
        pcr.calc("t", ECHO, id="reader", into=Part("px.back.b"), value=Part("px.back.a"))
        with self.assertRaises(ValueError) as caught:
            pcr.calc("t", SEED, id="writer", into=Part("px.back.a"), args={"base": 1})
        message = str(caught.exception)
        self.assertIn("'reader'", message)
        self.assertIn("'writer'", message)
        self.assertIn("later", message)

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

    def test_a_tick_built_without_a_pcr_chains_too(self):
        from pyto.pcr import Tick

        tick = Tick("standalone")
        first = tick.calc(SEED, id="first", into=Part("px.t.a"), args={"base": 1})
        tick.calc(ECHO, id="second", into=Part("px.t.b"), value=first)
        self.assertTrue(tick.chained())
        with self.assertRaises(ValueError) as caught:
            tick.calc(SEED, id="third", into=Part("px.t.a"), args={"base": 2})
        self.assertIn("'first'", str(caught.exception))


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
