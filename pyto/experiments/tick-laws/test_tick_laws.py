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

from tick_laws import analyze_record, main  # noqa: E402


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

    def test_sibling_actual_consume_names_calculation_and_part(self):
        """Brief: a calculation may not consume a Part produced by a sibling in its Tick."""
        record = _record(
            [
                _invocation("producer", produces=("px.shared",)),
                _invocation("consumer", consumes=("px.shared",)),
            ]
        )
        report = analyze_record(record)
        self.assertTrue(report["valid"], _violation_text(report))
        text = _finding_text(report)
        self.assertTrue(_has_violation(report), text)
        self.assertIn("producer", text)
        self.assertIn("consumer", text)
        self.assertIn("px.shared", text)

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

    def test_a_result_read_of_a_sibling_is_a_node_law_violation(self):
        """A result read is a read (pyto/questions.md, ResultReadsAreReads): binding a sibling's
        result with `fn:<id>` inside one Tick breaks the node law even though actual_consumes is
        empty. Guards tick_laws._reads: the fn: branch that resolves through into_by_id."""
        record = _record(
            [
                _invocation("producer", produces=("px.input",)),
                _invocation("by-result", produces=("px.out",), inputs={"roster": "fn:producer"}),
            ]
        )
        report = analyze_record(record)
        self.assertTrue(report["valid"], _violation_text(report))
        self.assertTrue(_has_violation(report), _finding_text(report))
        finding = report["laws"]["node"]["violations"][0]
        self.assertEqual(finding["consumer_id"], "by-result")
        self.assertEqual(finding["producer_ids"], ["producer"])
        self.assertEqual(finding["part"], "px.input")
        self.assertIn("result read", report["limitation"])

    def test_check_cli_exit_matrix_and_text_receipt(self):
        """Brief: --check reports clean, law, schema, and mixed outcomes exactly."""
        clean = _record([_invocation("clean", produces=("px.clean",))])
        law = _record(
            [_invocation("producer", produces=("px.bad",)), _invocation("consumer", consumes=("px.bad",))]
        )
        cases = [("clean", clean, 0), ("law", law, 1)]
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

    def test_mutation_actual_consume_is_killed(self):
        """Mutation: adding actual_consumes to a sibling kills the clean result."""
        record = _record(
            [_invocation("producer", produces=("px.m",)), _invocation("sibling")]
        )
        mutated = copy.deepcopy(record)
        mutated["ticks"][0]["invocations"][1]["actual_consumes"] = ["px.m"]
        mutated["parts"]["px.m"]["read_by"] = ["sibling"]
        self.assertTrue(_has_violation(analyze_record(mutated)))

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
