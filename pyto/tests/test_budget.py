"""Executable spec of the run budget (task 39).

A budget is spent in series, so it is checked where a series has seams: at the
Tick boundary and nowhere else ({?} TicksAsCircuits -- a sequence of Ticks is
the wire, and a Tick is the element you can stop between). When the budget is
gone the run stops **before** the next Tick: everything up to the seam is
published in full, `PcrRun.stopped_after_tick` names the last Tick that
completed, `PcrRun.completed` is False, and the testimony is the byte-for-byte
prefix of the unbudgeted run's.

The clock is injected, so this is a determinism test and not a race: a
`StepClock` advances a fixed number of milliseconds per reading and the run
reads it once per Tick boundary, which is what makes "stops after Tick 2 with a
250 ms budget" an arithmetic fact rather than a timing one.

Mutation-checked claim (a one-line edit applied to a scratch copy of the tree,
never to the repository; see pyto/experiments/tasks/39/packet.md):

    pcr.py:run breaks out of the Tick loop when the budget is  -> `continue` instead of
        spent, so no later Tick runs                              `break` and
        Budget.test_the_published_parts_are_exactly_the_first_two_ticks fails: Tick
        Three runs on the next reading and publishes px.budget.three: killed.

Every Calculation body is a named module-level function; no lambdas
(experiments/CAPTURE.md, rule 2).
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from dataclasses import asdict

from pyto import Calculation, Part, PCR, PxC
from pyto.core import RECEIPT_PREFIX
from pyto.materialize import run_record

PYTO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWER_TEST_DIR = os.path.join(PYTO_ROOT, "viewer", "test")
if VIEWER_TEST_DIR not in sys.path:
    print(f"[tests/test_budget] sys.path.insert(0, {VIEWER_TEST_DIR!r})", file=sys.stderr)
    sys.path.insert(0, VIEWER_TEST_DIR)

from record_schema import RecordSchemaError  # noqa: E402
from record_schema import run_schedule  # noqa: E402
from record_schema import validate as validate_record  # noqa: E402


def constant(args):
    return args["value"]


def double(args):
    return args["value"] * 2


def total(args):
    return args["left"] + args["right"]


CONSTANT = Calculation("fn.budget.constant", constant)
DOUBLE = Calculation("fn.budget.double", double)
TOTAL = Calculation("fn.budget.total", total)


class StepClock:
    """A clock that advances a fixed step per reading, and counts its readings.

    Deterministic on purpose: the budget's answer must be arithmetic. Reading N
    (0-based) is `N * step_ms`, so with a 100 ms step the run reads 0 before the
    first Tick and 100, 200, 300 at the three boundaries that follow.
    """

    def __init__(self, step_ms: float) -> None:
        self.step_ms = step_ms
        self.readings: list[float] = []

    def __call__(self) -> float:
        value = self.step_ms * len(self.readings)
        self.readings.append(value)
        return value


def build_program(name: str = "budget-series") -> PCR:
    """Three Ticks in series, each publishing one or two Parts."""
    pcr = PCR(name)
    one = pcr.calc("One", CONSTANT, id="one", into=Part("px.budget.one"), args={"value": 3})
    left = pcr.calc("Two", DOUBLE, id="two.left", into=Part("px.budget.two.left"), value=one)
    right = pcr.calc("Two", DOUBLE, id="two.right", into=Part("px.budget.two.right"), value=one)
    pcr.calc("Three", TOTAL, id="three", into=Part("px.budget.three"), left=left, right=right)
    return pcr


def testimony_bytes(ticks) -> str:
    return json.dumps([asdict(tick) for tick in ticks], sort_keys=True)


class Budget(unittest.TestCase):
    def setUp(self):
        self.clock = StepClock(100.0)
        self.pxc = PxC()
        self.run = build_program().run(
            self.pxc, observe=True, budget_ms=250.0, clock=self.clock
        )
        self.record = run_record(self.run, self.pxc)

    def test_the_run_stops_after_the_second_tick(self):
        self.assertEqual([tick.name for tick in self.run.ticks], ["One", "Two"])
        self.assertEqual(self.run.stopped_after_tick, "Two")
        self.assertIs(self.run.completed, False)
        self.assertEqual(self.run.budget_ms, 250.0)

    def test_the_clock_is_read_once_at_each_tick_boundary(self):
        # One reading to start, then one before each of the three Ticks: the third
        # reads 300 ms against a 250 ms budget and the run stops there.
        self.assertEqual(self.clock.readings, [0.0, 100.0, 200.0, 300.0])

    def test_the_published_parts_are_exactly_the_first_two_ticks(self):
        published = tuple(
            address
            for address in self.pxc.addresses()
            if not address.startswith(RECEIPT_PREFIX)
        )
        self.assertEqual(
            published,
            ("px.budget.one", "px.budget.two.left", "px.budget.two.right"),
        )
        self.assertNotIn("px.budget.three", self.pxc.addresses())
        self.assertEqual(sorted(self.run.results), ["one", "two.left", "two.right"])
        self.assertEqual(sorted(self.run.receipts), ["one", "two.left", "two.right"])

    def test_the_testimony_is_the_unbudgeted_runs_prefix_byte_for_byte(self):
        full = build_program().run(PxC(), observe=True)
        self.assertEqual([tick.name for tick in full.ticks], ["One", "Two", "Three"])
        self.assertEqual(
            testimony_bytes(self.run.ticks), testimony_bytes(full.ticks[:2])
        )

    def test_the_record_validates_and_says_where_the_run_stopped(self):
        validate_record(self.record)
        self.assertEqual(
            self.record["budget"],
            {"limit_ms": 250.0, "stopped_after_tick": "Two", "completed": False},
        )
        self.assertIs(self.record["parallel"], False)
        self.assertEqual(len(self.record["ticks"]), 2)
        self.assertEqual(self.record["counters"]["invocations"], 3)
        self.assertEqual(
            run_schedule(self.record)["budget"],
            {"limit_ms": 250.0, "stopped_after_tick": "Two", "completed": False},
        )

    def test_every_completed_tick_carries_its_latency(self):
        for tick in self.record["ticks"]:
            self.assertIsNotNone(tick["latency_ms"])
            self.assertAlmostEqual(
                tick["latency_ms"],
                sum(invocation["duration_ms"] for invocation in tick["invocations"]),
                places=9,
            )


class BudgetEdges(unittest.TestCase):
    def test_a_budget_that_is_never_spent_completes(self):
        clock = StepClock(100.0)
        pxc = PxC()
        run = build_program().run(pxc, observe=True, budget_ms=10_000.0, clock=clock)
        self.assertIs(run.completed, True)
        self.assertIsNone(run.stopped_after_tick)
        self.assertEqual([tick.name for tick in run.ticks], ["One", "Two", "Three"])
        record = run_record(run, pxc)
        validate_record(record)
        self.assertEqual(
            record["budget"],
            {"limit_ms": 10_000.0, "stopped_after_tick": None, "completed": True},
        )

    def test_a_budget_already_spent_publishes_nothing_and_names_no_tick(self):
        clock = StepClock(1000.0)
        pxc = PxC()
        run = build_program().run(pxc, observe=True, budget_ms=100.0, clock=clock)
        self.assertIs(run.completed, False)
        self.assertIsNone(run.stopped_after_tick)
        self.assertEqual(run.ticks, ())
        self.assertEqual(pxc.addresses(), ())

    def test_an_unbudgeted_run_never_reads_the_clock(self):
        clock = StepClock(100.0)
        build_program().run(PxC(), observe=True, clock=clock)
        self.assertEqual(clock.readings, [])

    def test_a_budget_stops_a_parallel_run_at_the_same_seam(self):
        clock = StepClock(100.0)
        pxc = PxC()
        run = build_program().run(
            pxc, observe=True, parallel=True, budget_ms=250.0, clock=clock
        )
        self.assertEqual(run.stopped_after_tick, "Two")
        self.assertIs(run.completed, False)
        serial = build_program().run(PxC(), observe=True, budget_ms=250.0, clock=StepClock(100.0))
        self.assertEqual(testimony_bytes(run.ticks), testimony_bytes(serial.ticks))
        record = run_record(run, pxc)
        validate_record(record)
        self.assertIs(record["parallel"], True)

    def test_the_default_clock_is_monotonic_milliseconds(self):
        """No injected clock: a generous budget completes, a zero budget does not."""
        run = build_program().run(PxC(), observe=True, budget_ms=60_000.0)
        self.assertIs(run.completed, True)
        stopped = build_program().run(PxC(), observe=True, budget_ms=-1.0)
        self.assertIs(stopped.completed, False)
        self.assertEqual(stopped.ticks, ())


class BudgetRecordRules(unittest.TestCase):
    """What both validators refuse, at the same path."""

    def setUp(self):
        clock = StepClock(100.0)
        pxc = PxC()
        run = build_program().run(pxc, observe=True, budget_ms=250.0, clock=clock)
        self.record = run_record(run, pxc)

    def test_a_completed_run_may_not_name_a_stopping_tick(self):
        record = json.loads(json.dumps(self.record))
        record["budget"]["completed"] = True
        with self.assertRaises(RecordSchemaError) as caught:
            validate_record(record)
        self.assertEqual(caught.exception.path, "budget.stopped_after_tick")

    def test_a_stopping_tick_must_name_a_tick_of_this_record(self):
        record = json.loads(json.dumps(self.record))
        record["budget"]["stopped_after_tick"] = "Three"
        with self.assertRaises(RecordSchemaError) as caught:
            validate_record(record)
        self.assertEqual(caught.exception.path, "budget.stopped_after_tick")

    def test_budget_carries_its_three_fields_and_no_others(self):
        record = json.loads(json.dumps(self.record))
        record["budget"]["spent_ms"] = 300.0
        with self.assertRaises(RecordSchemaError) as caught:
            validate_record(record)
        self.assertEqual(caught.exception.path, "budget")

    def test_latency_is_a_number_or_null(self):
        record = json.loads(json.dumps(self.record))
        record["ticks"][0]["latency_ms"] = "fast"
        with self.assertRaises(RecordSchemaError) as caught:
            validate_record(record)
        self.assertEqual(caught.exception.path, "ticks[0].latency_ms")

    def test_a_placement_worker_is_a_non_negative_integer(self):
        record = json.loads(json.dumps(self.record))
        record["ticks"][0]["invocations"][0]["placement"] = {
            "worker": -1,
            "started_ms": 0.0,
        }
        with self.assertRaises(RecordSchemaError) as caught:
            validate_record(record)
        self.assertEqual(caught.exception.path, "ticks[0].invocations[0].placement.worker")


if __name__ == "__main__":
    unittest.main()
