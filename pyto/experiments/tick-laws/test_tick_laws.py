"""Tests for the exp/26 tick-law checker.

The tests intentionally use ordinary dictionaries so they exercise the record
contract at the same boundary as the CLI.  They are kept here, beside the
checker, because a record is the public input to this experiment.
"""

from __future__ import annotations

import copy
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from tick_laws import _tick_name, analyze_record, main  # noqa: E402


GROUPED_RECORD_PATH = HERE.parent / "grouped-ablation" / "evidence" / "run-1" / "record.json"
STUDENTS_RECORD_PATH = HERE.parent / "students" / "evidence" / "run-1" / "record.json"


def _invocation(identifier, *, consumes=(), produces=(), duration=0.1, declared=(), inputs=None):
    produces = list(produces)
    consumes = list(consumes)
    return {
        "id": identifier,
        "calculation": {
            "address": f"fn.test.{identifier}",
            "identity_scope": "runtime-function-body",
            "implementation_sha256": "0" * 64,
        },
        "actual_consumes": consumes,
        "actual_produces": produces,
        "declared_consumes": list(declared),
        "args": {},
        "inputs": dict(inputs) if inputs is not None else ({"part": declared[0]} if declared else {}),
        "duration_ms": duration,
        "hit": False,
        "into": produces[0] if produces else None,
        "result_sha256": "1" * 64,
        "value": {"kind": "json", "data": None, "note": None},
        "writes": [{"address": address, "kind": "new-address"} for address in produces],
    }


def _record(*ticks):
    invocations = [invocation for tick in ticks for invocation in tick]
    parts = {}
    for invocation in invocations:
        for address in invocation.get("actual_produces", []):
            parts[address] = {"preexisting": False, "read_by": [], "written_by": invocation["id"]}
        for address in invocation.get("actual_consumes", []) + invocation.get("declared_consumes", []):
            parts.setdefault(address, {"preexisting": True, "read_by": [], "written_by": None})
            if invocation.get("actual_consumes") and address in invocation["actual_consumes"]:
                parts[address]["read_by"].append(invocation["id"])
    work_ms = sum(
        duration for invocation in invocations
        if isinstance((duration := invocation.get("duration_ms")), (int, float))
    )
    return {
        "schema": "pyto-run-record@1",
        "source": {"runtime": "pyto", "version": "0.1.0", "commit": "test"},
        "pcr": "test",
        "counters": {"computed": len(invocations), "hits": 0, "invocations": len(invocations), "wall_ms": work_ms},
        "parts": parts,
        "ticks": [
            {"index": index, "name": f"Tick {index}", "invocations": list(invocations)}
            for index, invocations in enumerate(ticks)
        ],
    }


def _violations(report):
    """Return structured law findings from the checker report."""
    if isinstance(report, dict):
        findings = report.get("violations", report.get("findings", []))
        if isinstance(findings, list):
            return findings
    return []


def _violation_text(report):
    findings = _violations(report)
    return json.dumps(findings if findings else report, sort_keys=True)


def _finding_text(report):
    return json.dumps(_violations(report), sort_keys=True).lower()


def _has_violation(report):
    return bool(_violations(report))


def _metric(report, *names):
    """Find a named numeric metric without prescribing report presentation."""
    if isinstance(report, dict):
        for name in names:
            if name in report and isinstance(report[name], (int, float)):
                return report[name]
        for value in report.values():
            found = _metric(value, *names)
            if found is not None:
                return found
    elif isinstance(report, list):
        for value in report:
            found = _metric(value, *names)
            if found is not None:
                return found
    return None



class TickLawTests(unittest.TestCase):
    def test_committed_students_records_are_clean(self):
        """Brief: both committed student records are valid reference witnesses."""
        paths = [GROUPED_RECORD_PATH, STUDENTS_RECORD_PATH]
        for path in paths:
            self.assertTrue(path.exists() and path.stat().st_size, f"missing committed witness: {path}")
        for path in paths:
            with self.subTest(record=path.parent.name):
                report = analyze_record(json.loads(path.read_text()))
                self.assertFalse(_has_violation(report), _violation_text(report))

    def test_ticks_are_reported_by_name_in_json_and_in_text(self):
        """Brief: a Tick is a step the program named, so the report says the name.

        The students record's four Ticks are Parse, Stats, Letters and Histogram;
        every tick report carries that name beside its index, and text mode prints
        it, so `Tick 1 Stats: work_ms=...` is what a reader sees instead of a bare
        position (`{?} TickReportsHaveNoNames`).
        """
        record = json.loads(STUDENTS_RECORD_PATH.read_text())
        names = [tick["name"] for tick in record["ticks"]]
        self.assertEqual(names, ["Parse", "Stats", "Letters", "Histogram"])

        report = analyze_record(record)
        self.assertEqual([tick["name"] for tick in report["ticks"]], names)
        self.assertEqual([tick["tick"] for tick in report["ticks"]], list(range(len(names))))

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main([str(STUDENTS_RECORD_PATH)]), 0)
        text = output.getvalue()
        for index, name in enumerate(names):
            self.assertIn(f"Tick {index} {name}: work_ms=", text)
        # The Stats line is the worked example the READMEs name: work above latency.
        stats = report["ticks"][names.index("Stats")]
        self.assertGreater(stats["work_ms"], stats["latency_ms"])

    def test_a_tick_with_no_name_reads_as_unnamed_not_as_a_crash(self):
        """Brief: the record contract requires a Tick name, so the reporter never
        invents one -- a record that reached the reporter without one (a producer
        the validator never saw) reads as `<unnamed>` rather than raising."""
        self.assertEqual(_tick_name({"index": 0, "invocations": []}), "<unnamed>")
        self.assertEqual(_tick_name({"name": ""}), "<unnamed>")
        self.assertEqual(_tick_name({"name": "Stats"}), "Stats")

    def test_a_consume_of_an_earlier_sibling_is_a_chain_not_a_violation(self):
        """Inside a Tick the Calculations are a sequence in declared order: a Calculation
        that consumes a Part an earlier sibling produced makes the Tick a chain, which runs
        in order, and the node law holds. The owner, 2026-09-10: "'Calculations inside a
        Tick must be independent' was added as a rule, while your existing ChainSpot program
        deliberately chains dependent Calculations inside a Tick. Your definition was the
        moment that sequence becomes inspectable." The link names producer, consumer and Part."""
        record = _record(
            [
                _invocation("producer", produces=("px.shared",)),
                _invocation("consumer", consumes=("px.shared",)),
            ]
        )
        report = analyze_record(record)
        self.assertTrue(report["valid"], _violation_text(report))
        self.assertFalse(_has_violation(report), _violation_text(report))
        self.assertTrue(report["ok"])
        self.assertTrue(report["laws"]["node"]["ok"])
        self.assertEqual(report["laws"]["node"]["modes"], {"parallel": 0, "chain": 1})
        tick = report["ticks"][0]
        self.assertEqual(tick["mode"], "chain")
        self.assertEqual(
            tick["chain"], [{"consumer_id": "consumer", "producer_ids": ["producer"], "part": "px.shared"}]
        )

    def test_a_backwards_read_is_a_node_law_violation(self):
        """A Calculation that reads a Part a sibling declared *after* it produces reads
        something the sequence has not produced yet: still a violation, named as such."""
        record = _record(
            [
                _invocation("consumer", consumes=("px.shared",)),
                _invocation("producer", produces=("px.shared",)),
            ]
        )
        report = analyze_record(record)
        self.assertTrue(report["valid"], _violation_text(report))
        self.assertTrue(_has_violation(report), _finding_text(report))
        self.assertFalse(report["ok"])
        finding = report["laws"]["node"]["violations"][0]
        self.assertEqual(finding["kind"], "backwards_read")
        self.assertEqual(finding["consumer_id"], "consumer")
        self.assertEqual(finding["producer_ids"], ["producer"])
        self.assertEqual(finding["part"], "px.shared")
        self.assertIn("reads a sibling declared after it", finding["message"])
        # A Tick with sibling reads is a chain even when one of them is backwards.
        self.assertEqual(report["ticks"][0]["mode"], "chain")

    def test_a_chain_takes_the_sum_and_a_parallel_tick_the_longest_branch(self):
        """A chain runs in order, so its latency is the sum through the chain; a Tick with
        no sibling reads runs at once, so its latency is its longest branch."""
        record = _record(
            [
                _invocation("first", produces=("px.a",), duration=2.0),
                _invocation("second", consumes=("px.a",), produces=("px.b",), duration=5.0),
            ],
            [
                _invocation("left", produces=("px.l",), duration=2.0),
                _invocation("right", produces=("px.r",), duration=5.0),
            ],
        )
        report = analyze_record(record)
        self.assertFalse(_has_violation(report), _violation_text(report))
        self.assertEqual([t["mode"] for t in report["ticks"]], ["chain", "parallel"])
        self.assertEqual(report["ticks"][0]["work_ms"], 7.0)
        self.assertEqual(report["ticks"][0]["latency_ms"], 7.0)
        self.assertEqual(report["ticks"][1]["work_ms"], 7.0)
        self.assertEqual(report["ticks"][1]["latency_ms"], 5.0)
        self.assertEqual(report["summary"]["critical_path_ms"], 12.0)
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "chain.json"
            path.write_text(json.dumps(record))
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["--check", str(path)]), 0)
        text = output.getvalue()
        self.assertIn("Tick 0 Tick 0: work_ms=7.0 latency_ms=7.0 mode=chain", text)
        self.assertIn("Tick 1 Tick 1: work_ms=7.0 latency_ms=5.0 mode=parallel", text)

    def test_duplicate_actual_produces_names_calculation_and_part(self):
        """Brief: one Tick cannot have two actual producers for the same Part."""
        record = _record(
            [
                _invocation("first", produces=("px.duplicate",)),
                _invocation("second", produces=("px.duplicate",)),
            ]
        )
        report = analyze_record(record)
        self.assertTrue(report["valid"], _violation_text(report))
        text = _finding_text(report)
        self.assertTrue(_has_violation(report), text)
        self.assertIn("duplicate", text)
        self.assertIn("px.duplicate", text)
        self.assertIn("first", text)
        self.assertIn("second", text)

    def test_late_actual_producer_loop_is_reported(self):
        """Brief: an actual consumer cannot precede the producer across Ticks."""
        record = _record(
            [_invocation("consumer", consumes=("px.late",))],
            [_invocation("producer", produces=("px.late",))],
        )
        report = analyze_record(record)
        self.assertTrue(report["valid"], _violation_text(report))
        text = _finding_text(report)
        self.assertTrue(_has_violation(report), text)
        self.assertIn("late", text)
        self.assertIn("px.late", text)

    def test_tiny_durations_are_valid(self):
        """Brief: duration checks must work for very small positive runtimes."""
        record = _record(
            [
                _invocation("fast-a", produces=("px.fast-a",), duration=2.0),
                _invocation("fast-b", produces=("px.fast-b",), duration=5.0),
            ],
            [_invocation("fast-c", produces=("px.fast-c",), duration=3.0)],
        )
        report = analyze_record(record)
        self.assertTrue(report["valid"], _violation_text(report))
        self.assertFalse(_has_violation(report), _violation_text(report))
        self.assertEqual(report["ticks"][0]["work_ms"], 7.0)
        self.assertEqual(report["ticks"][1]["work_ms"], 3.0)
        self.assertEqual(report["ticks"][0]["latency_ms"], 5.0)
        self.assertEqual(report["ticks"][1]["latency_ms"], 3.0)
        self.assertEqual(report["summary"]["work_ms"], 10.0)
        self.assertEqual(report["summary"]["critical_path_ms"], 8.0)

    def test_a_result_read_of_an_earlier_sibling_is_a_chain(self):
        """A result read is a read (pyto/questions.md, ResultReadsAreReads): binding an earlier
        sibling's result with `fn:<id>` inside one Tick makes the Tick a chain even though
        actual_consumes is empty. Guards tick_laws._reads: the fn: branch that resolves through
        into_by_id -- drop it and the Tick reads as parallel."""
        record = _record(
            [
                _invocation("producer", produces=("px.input",)),
                _invocation("by-result", produces=("px.out",), inputs={"roster": "fn:producer"}),
            ]
        )
        report = analyze_record(record)
        self.assertTrue(report["valid"], _violation_text(report))
        self.assertFalse(_has_violation(report), _finding_text(report))
        tick = report["ticks"][0]
        self.assertEqual(tick["mode"], "chain")
        link = tick["chain"][0]
        self.assertEqual(link["consumer_id"], "by-result")
        self.assertEqual(link["producer_ids"], ["producer"])
        self.assertEqual(link["part"], "px.input")
        self.assertIn("result read", report["limitation"])
        # Bound the other way round, the same result read is a backwards read.
        backwards = _record(
            [
                _invocation("by-result", produces=("px.out",), inputs={"roster": "fn:producer"}),
                _invocation("producer", produces=("px.input",)),
            ]
        )
        self.assertEqual(analyze_record(backwards)["laws"]["node"]["violations"][0]["kind"], "backwards_read")

    def test_check_cli_exit_matrix_and_text_receipt(self):
        """Brief: --check reports clean, law, schema, and mixed outcomes exactly."""
        clean = _record([_invocation("clean", produces=("px.clean",))])
        # A chain (consumer after producer) is clean; a backwards read (consumer before
        # producer) breaks the node law.
        chain = _record(
            [_invocation("producer", produces=("px.bad",)), _invocation("consumer", consumes=("px.bad",))]
        )
        law = _record(
            [_invocation("consumer", consumes=("px.bad",)), _invocation("producer", produces=("px.bad",))]
        )
        cases = [("clean", clean, 0), ("chain", chain, 0), ("law", law, 1)]
        with tempfile.TemporaryDirectory() as directory:
            paths = {}
            for name, record, _expected in cases:
                path = Path(directory) / f"{name}.json"
                path.write_text(json.dumps(record))
                paths[name] = path
            invalid = Path(directory) / "invalid.json"
            invalid.write_text(json.dumps({"schema": "pyto-run-record@1"}))
            paths["invalid"] = invalid
            for name, _record_value, expected in cases:
                with self.subTest(case=name):
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        exit_code = main(["--check", str(paths[name])])
                    self.assertEqual(exit_code, expected)
                    if name == "clean":
                        receipt_output = io.StringIO()
                        with contextlib.redirect_stdout(receipt_output):
                            self.assertEqual(main([str(paths[name])]), 0)
                        receipt = receipt_output.getvalue().lower()
                        self.assertIn("tick", receipt)
                        self.assertIn("summary", receipt)
                        self.assertIn("no parallel execution exists yet", receipt)
            self.assertEqual(main(["--check", str(paths["invalid"])]), 1)
            self.assertEqual(main(["--check", str(paths["clean"]), str(paths["law"])]), 1)

    def test_empty_and_invalid_durations_have_explicit_metrics(self):
        """Brief: empty Ticks cost zero; missing durations produce null metrics."""
        record = _record([], [_invocation("unknown-duration", produces=("px.unknown",))])
        record["ticks"][1]["invocations"][0]["duration_ms"] = None
        report = analyze_record(record)
        self.assertEqual(report["ticks"][0]["work_ms"], 0)
        self.assertEqual(report["ticks"][0]["latency_ms"], 0)
        self.assertIsNone(report["ticks"][1]["work_ms"])
        self.assertIsNone(report["ticks"][1]["latency_ms"])

    def test_mutation_actual_consume_turns_parallel_into_chain(self):
        """Mutation: adding actual_consumes of an earlier sibling's Part turns the parallel
        Tick into a chain and nothing more; the same consume on the earlier sibling, of the
        later one's Part, is a backwards read and kills the clean result."""
        record = _record(
            [_invocation("producer", produces=("px.m",)), _invocation("sibling")]
        )
        self.assertEqual(analyze_record(record)["ticks"][0]["mode"], "parallel")
        mutated = copy.deepcopy(record)
        mutated["ticks"][0]["invocations"][1]["actual_consumes"] = ["px.m"]
        mutated["parts"]["px.m"]["read_by"] = ["sibling"]
        report = analyze_record(mutated)
        self.assertFalse(_has_violation(report), _violation_text(report))
        self.assertEqual(report["ticks"][0]["mode"], "chain")
        backwards = _record(
            [_invocation("sibling"), _invocation("producer", produces=("px.m",))]
        )
        backwards["ticks"][0]["invocations"][0]["actual_consumes"] = ["px.m"]
        backwards["parts"]["px.m"]["read_by"] = ["sibling"]
        self.assertTrue(_has_violation(analyze_record(backwards)))

    def test_mutation_duplicate_producer_is_killed(self):
        """Mutation: adding a second actual producer kills the clean result."""
        record = _record([_invocation("first", produces=("px.m",))])
        mutated = copy.deepcopy(record)
        mutated["ticks"][0]["invocations"].append(
            _invocation("second", produces=("px.m",))
        )
        mutated["counters"]["invocations"] = 2
        mutated["counters"]["computed"] = 2
        self.assertTrue(_has_violation(analyze_record(mutated)))


if __name__ == "__main__":
    unittest.main()
