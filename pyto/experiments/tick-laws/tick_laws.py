"""Check observed dependency laws in pyto run records."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

LIMITATION = (
    "reads are every input binding: px: bindings are store reads, fn: bindings are result reads "
    "resolved through the producer's into (pyto/questions.md, ResultReadsAreReads); writes are "
    "actual_produces plus the declared into; no parallel execution exists yet, these numbers are "
    "what parallel would buy."
)


def _into_addresses(inv: dict[str, Any]) -> list[str]:
    """The addresses an invocation publishes: `into` is one string or, since a Calculation may
    produce several Parts, a list of them (pyto/questions.md, WhatIsATick)."""
    into = inv.get("into")
    if into is None:
        return []
    if isinstance(into, str):
        return [into]
    return [str(a) for a in into]


def _writes(inv: dict[str, Any]) -> set[str]:
    return set(inv.get("actual_produces") or []) | set(_into_addresses(inv))


def _reads(inv: dict[str, Any], into_by_id: dict[str, list[str]]) -> set[str]:
    """Every read: `px:<address>` is a store read; `fn:<id>` is a result read of everything that
    invocation published; `fn:<id>#<address>` names one produce of a multi-produce invocation.
    Unioned with actual_consumes, defensively, as the two reference readers do
    (viewer/adapters.js, viewer/test/record_schema.py)."""
    reads = set(inv.get("actual_consumes") or [])
    for binding in (inv.get("inputs") or {}).values():
        if not isinstance(binding, str):
            continue
        if binding.startswith("px:"):
            reads.add(binding[3:])
        elif binding.startswith("fn:"):
            ref = binding[3:]
            if ref in into_by_id:
                reads.update(into_by_id[ref])
            elif "#" in ref:
                head, _, addr = ref.rpartition("#")
                reads.add(addr if head in into_by_id else addr)
    return reads


def _validator():
    root = Path(__file__).resolve().parents[2]
    path = root / "viewer" / "test"
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
    try:
        from record_schema import validate  # type: ignore
    except ImportError:
        return None
    return validate


def validate_record(record: dict[str, Any]) -> list[str]:
    validator = _validator()
    if validator is None:
        return ["shared record validator could not be imported"]
    try:
        validator(record)
    except Exception as exc:
        return [str(exc)]
    return []


def _duration(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) and value >= 0 else None


def _id(inv: dict[str, Any]) -> str:
    return str(inv.get("id", "<unnamed>"))


def _empty_report(errors: list[str]) -> dict[str, Any]:
    violations = [{"law": "validation", "kind": "validation", "message": e} for e in errors]
    return {"ok": False, "valid": False, "limitation": LIMITATION, "violations": violations,
            "laws": {"node": {"ok": None, "violations": []}, "loop": {"ok": None, "violations": []}},
            "ticks": [], "summary": {"work_ms": None, "critical_path_ms": None}}


def analyze_record(record: dict[str, Any]) -> dict[str, Any]:
    """Validate and analyze a single complete run-record dictionary."""
    if not isinstance(record, dict):
        return _empty_report(["record must be an object"])
    errors = validate_record(record)
    if errors:
        return _empty_report(errors)
    ticks = list(record["ticks"])
    produced: dict[str, list[tuple[int, str]]] = {}
    into_by_id: dict[str, list[str]] = {}
    for ti, tick in enumerate(ticks):
        for inv in tick["invocations"]:
            into_by_id[_id(inv)] = _into_addresses(inv)
    for ti, tick in enumerate(ticks):
        for inv in tick["invocations"]:
            for part in sorted(_writes(inv)):
                produced.setdefault(part, []).append((ti, _id(inv)))

    violations: list[dict[str, Any]] = []
    node: list[dict[str, Any]] = []
    loop: list[dict[str, Any]] = []
    for ti, tick in enumerate(ticks):
        invocations = tick["invocations"]
        siblings: dict[str, list[str]] = {}
        for inv in invocations:
            for part in sorted(_writes(inv)):
                siblings.setdefault(part, []).append(_id(inv))
        for part in sorted(siblings):
            ids = siblings[part]
            if len(ids) > 1:
                finding = {"kind": "duplicate_produce", "tick": ti, "part": part,
                           "producer_ids": ids,
                           "message": f"node law violation: Tick {ti} has two producers for {part}: {', '.join(ids)}"}
                node.append(finding); violations.append({"law": "node", **finding})
        for inv in invocations:
            consumer = _id(inv)
            for part in sorted(_reads(inv, into_by_id)):
                producers_here = [p for p in siblings.get(part, []) if p != consumer]
                if producers_here:
                    finding = {"kind": "sibling_read", "tick": ti, "part": part,
                               "consumer_id": consumer, "producer_ids": producers_here,
                               "message": f"node law violation: {consumer} reads sibling-produced {part} in Tick {ti}"}
                    node.append(finding); violations.append({"law": "node", **finding})
                entries = produced.get(part, [])
                prior = [entry for entry in entries if entry[0] < ti]
                same_tick = [entry for entry in entries if entry[0] == ti]
                later = [entry for entry in entries if entry[0] > ti]
                if not prior and not same_tick and later:
                    finding = {"kind": "late_producer", "tick": ti, "part": part,
                               "consumer_id": consumer,
                               "producer_ids": [{"tick": p, "invocation": n} for p, n in later],
                               "message": f"loop law violation: {consumer} in Tick {ti} consumes {part} before its only producer(s), in later Tick(s)"}
                    loop.append(finding); violations.append({"law": "loop", **finding})

    tick_reports = []
    for ti, tick in enumerate(ticks):
        durations = [_duration(inv["duration_ms"]) for inv in tick["invocations"]]
        if not durations:
            work = latency = 0.0
        elif any(d is None for d in durations):
            work = latency = None
        else:
            work, latency = sum(durations), max(durations)
        tick_reports.append({"tick": ti, "work_ms": work, "latency_ms": latency})
    work = sum(t["work_ms"] for t in tick_reports) if all(t["work_ms"] is not None for t in tick_reports) else None
    critical = sum(t["latency_ms"] for t in tick_reports) if all(t["latency_ms"] is not None for t in tick_reports) else None
    return {"ok": not violations, "valid": True, "limitation": LIMITATION, "violations": violations,
            "laws": {"node": {"ok": not node, "violations": node}, "loop": {"ok": not loop, "violations": loop}},
            "ticks": tick_reports, "summary": {"work_ms": work, "critical_path_ms": critical}}


def load_record(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("record JSON must be an object")
    return value


def analyze_records(paths: Iterable[str | Path]) -> dict[str, Any]:
    records = []
    for path in paths:
        try:
            report = analyze_record(load_record(path))
        except Exception as exc:
            report = _empty_report([str(exc)])
        records.append({"path": str(path), "report": report})
    return {"ok": all(item["report"]["ok"] for item in records), "records": records, "limitation": LIMITATION}


def _print_text(result: dict[str, Any]) -> None:
    print(f"LIMITATION: {result['limitation']}")
    for item in result["records"]:
        report = item["report"]
        print(item["path"])
        for tick in report["ticks"]:
            print(f"Tick {tick['tick']}: work_ms={tick['work_ms']} latency_ms={tick['latency_ms']}")
        print(f"Summary: work_ms={report['summary']['work_ms']} critical_path_ms={report['summary']['critical_path_ms']}")
        print("no parallel execution exists yet")
        for violation in report["violations"]:
            producers = violation.get("producer_ids")
            suffix = f" producers={producers}" if producers else ""
            print(f"VIOLATION: {violation['message']}{suffix}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit nonzero on validation or law failure")
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    parser.add_argument("paths", nargs="+", help="run-record JSON paths")
    args = parser.parse_args(argv)
    result = analyze_records(args.paths)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_text(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
