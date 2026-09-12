"""neat hot <record.json>: the efficiency pass over one run record, computed.

The owner, 2026-09-12, after an evolutionary art generation kept 32 renders as
Python lists of 196,608 ints and paid per pixel in every stage: "come up with
some compiler-ish efficiency pass to prevent things like this?"

So this module is the pass, not a note about it. One ``pyto-run-record@1`` in,
one Part out, ``px.exp.neat.hot.<record-stem>``, and it runs the same way on any
record this repository (or any pyto program) has left behind. It reads the
record and nothing else: no clock, no import of the program that made it.

What is measured, per invocation, from the receipts the record already carries:

- ``duration_ms``: what that invocation cost.
- ``kind`` and ``bytes``: the result's value object -- the size of its JSON data,
  or, for an ``omitted`` value, the byte count its note carries.
- ``elements``: how many entries the value holds when it is a list, flattened;
  a rectangular nested list also records its ``shape``, because a rectangular
  list of numbers is an array written the long way.
- ``ns_per_element``: duration over the elements this invocation moved -- its
  own, or, when its result is not a list, the largest list any of its recorded
  inputs handed it. A receipt that returns one dict still paid per element when
  it read 196,608 of them.

And the findings, each naming the Calculation, its numbers and its ``for``:

- ``dense-list``: a result that is a list of more than ``--dense`` numbers
  (4096 by default) and would be an array.
- ``per-element``: ``ns_per_element`` over ``--per-element`` (50 ns by default,
  calibrated below) on at least ``ELEMENT_FLOOR`` elements.
- ``over-cap``: a value over the record cap -- omitted with the cap's note, or
  kept only because the run raised the cap, with the bytes it costs the record.
- ``repeat-input``: two or more receipts of one Calculation with the same
  resolved input digests and the same args: a cache that isn't there.
- ``hot``: the top three Calculations by total duration, always, whether or not
  anything else fires.

The 50 ns threshold, calibrated on the evolution record this was written for:
in the dense run every stage trips it (render 894 ns per pixel, fitness 254,
encode 85) and in the array run nothing does, because 50 ns is about one Python
bytecode's worth of work per element -- above it the elements are being walked
in Python, below it they are being moved in one pass. ``ELEMENT_FLOOR`` (1024)
keeps a 16-entry list that took a tenth of a millisecond out of the findings:
cost per element only means something over many elements.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Mapping

from pyto import Calculation, PCR, Part, PxC
from pyto.materialize import run_record, write_record

ADDRESS_TEMPLATE = "px.exp.neat.hot.{stem}"
HOT_DIR = os.path.join("pyto", "experiments", "review", "hot")

DENSE_LIST = 4096  # a list of more than this many numbers is an array written the long way
PER_ELEMENT_NS = 50.0  # about one Python bytecode per element; see the module docstring
ELEMENT_FLOOR = 1024  # cost per element is only measured over many elements
CAP_BYTES = 262144  # RECORD.md:63, materialize.VALUE_CAP_BYTES: the default value cap
TOP = 3

CAP_NOTE = re.compile(r"value is (\d+) bytes, over the (\d+) byte cap")
TRUNCATED_NOTE = re.compile(r"array\(s\) truncated to the first \d+ entries; original lengths: \[([\d, ]*)\]")
NUMBER = (int, float)


# --- the shape of a value ----------------------------------------------------------

def flatten(value: Any) -> tuple[int, list[int] | None, bool]:
    """``(elements, shape, numeric)`` for a list: its leaves, flattened.

    ``shape`` is filled only when every level is rectangular -- the same length
    all the way down -- which is what makes a nested list an array. ``numeric``
    is true when every leaf is a number, and a bool is not a number here: a list
    of flags is not a dense array of pixels.
    """
    if not isinstance(value, list):
        return 0, None, False
    if not value:
        return 0, [0], True
    if all(isinstance(item, list) for item in value):
        inner = [flatten(item) for item in value]
        total = sum(count for count, _, _ in inner)
        numeric = all(is_numeric for _, _, is_numeric in inner)
        shapes = {tuple(shape) if shape is not None else None for _, shape, _ in inner}
        shape = None
        if len(shapes) == 1:
            only = shapes.pop()
            shape = [len(value), *only] if only is not None else None
        return total, shape, numeric
    numeric = all(isinstance(item, NUMBER) and not isinstance(item, bool) for item in value)
    return len(value), [len(value)], numeric


def value_shape(value: Mapping[str, Any] | None) -> dict[str, Any]:
    """The record's ``{kind, data, note}`` read as a shape: kind, bytes, elements, shape."""
    if not value:
        return {"kind": "missing", "bytes": 0, "elements": 0, "shape": None, "numeric": False,
                "over_cap": None, "truncated": False}
    kind, data, note = value.get("kind"), value.get("data"), value.get("note")
    over_cap: dict[str, Any] | None = None
    if kind == "omitted":
        match = CAP_NOTE.search(note or "")
        size = int(match.group(1)) if match else 0
        if match:
            over_cap = {"bytes": size, "cap": int(match.group(2)), "kept": False}
        return {"kind": kind, "bytes": size, "elements": 0, "shape": None, "numeric": False,
                "over_cap": over_cap, "truncated": False}
    if isinstance(data, str):
        size = len(data.encode("utf-8"))
    else:
        try:
            size = len(json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        except (TypeError, ValueError):  # pragma: no cover - the record is JSON
            size = 0
    elements, shape, numeric = flatten(data)
    # A record written with the default array cap holds the first 200 entries and a note
    # carrying the original lengths. The value was that long when it was computed, so that
    # is the length this pass measures: otherwise every default-cap record looks sparse.
    truncated = TRUNCATED_NOTE.search(note or "") if kind == "json" else None
    if truncated:
        lengths = [int(n) for n in truncated.group(1).replace(" ", "").split(",") if n]
        elements, shape = max(lengths or [elements]), None
    if size > CAP_BYTES:
        over_cap = {"bytes": size, "cap": CAP_BYTES, "kept": True}
    return {"kind": kind, "bytes": size, "elements": elements, "shape": shape, "numeric": numeric,
            "over_cap": over_cap, "truncated": bool(truncated)}


# --- the host: one record read -----------------------------------------------------

def load_record(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _ref_id(reference: Any) -> str | None:
    """The invocation id a ``fn:<id>`` (or ``fn:<id>#<address>``) input reference names."""
    if isinstance(reference, str) and reference.startswith("fn:"):
        return reference[3:].split("#", 1)[0]
    return None


def measure(record: Mapping[str, Any], path: str = "") -> dict[str, Any]:
    """Every invocation of the record, with the shape of its result and what it cost."""
    invocations: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for tick in record.get("ticks", ()):
        for invocation in tick.get("invocations", ()):
            shape = value_shape(invocation.get("value"))
            row = {
                "tick": tick.get("name"),
                "id": invocation.get("id"),
                "calculation": (invocation.get("calculation") or {}).get("address"),
                "duration_ms": float(invocation.get("duration_ms") or 0.0),
                "hit": bool(invocation.get("hit")),
                "into": invocation.get("into"),
                "inputs": dict(invocation.get("inputs") or {}),
                "args": invocation.get("args") or {},
                "result_sha256": invocation.get("result_sha256"),
                **shape,
            }
            invocations.append(row)
            by_id[str(row["id"])] = row
    for row in invocations:
        # What this invocation moved: its own elements, or the largest list it was handed.
        read = 0
        for reference in row["inputs"].values():
            source = by_id.get(_ref_id(reference) or "")
            if source:
                read = max(read, int(source["elements"]))
        row["input_elements"] = read
        moved = max(int(row["elements"]), read)
        row["moved"] = moved
        row["ns_per_element"] = round(row["duration_ms"] * 1e6 / moved, 2) if moved else None
        # The cache key a repeat would hit: what it read, and what it was told.
        digests = []
        known = True
        for name in sorted(row["inputs"]):
            reference = row["inputs"][name]
            source = by_id.get(_ref_id(reference) or "")
            if source is None:
                digests.append(f"{name}={reference}")
            elif source["result_sha256"]:
                digests.append(f"{name}={source['result_sha256']}")
            else:
                known = False
        row["input_key"] = (
            json.dumps([digests, row["args"]], sort_keys=True, separators=(",", ":")) if known else None
        )
    counters = dict(record.get("counters") or {})
    return {
        "path": path,
        "pcr": record.get("pcr"),
        "schema": record.get("schema"),
        "counters": counters,
        "invocations": invocations,
        "thresholds": {
            "dense_list": DENSE_LIST,
            "per_element_ns": PER_ELEMENT_NS,
            "element_floor": ELEMENT_FLOOR,
            "cap_bytes": CAP_BYTES,
            "top": TOP,
        },
    }


# --- fn.neat.hot.evaluate ----------------------------------------------------------

def _group(rows: list[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["calculation"]), []).append(row)
    return grouped


def evaluate(args: Mapping[str, Any]) -> dict[str, Any]:
    """The measurement read as findings: what is hot, and the shape that made it hot.

    Pure over the measurement, so the same record always answers the same way.
    Findings are per Calculation, not per invocation: thirty-two renders of one
    Calculation are one thing to fix, and the count is one of its numbers.
    """
    measured = args["measured"]
    thresholds = measured["thresholds"]
    dense_at = int(args.get("dense_list", thresholds["dense_list"]))
    per_element_at = float(args.get("per_element_ns", thresholds["per_element_ns"]))
    floor = int(args.get("element_floor", thresholds["element_floor"]))
    top = int(args.get("top", thresholds["top"]))
    rows = [row for row in measured["invocations"]]
    total_ms = sum(row["duration_ms"] for row in rows) or 1.0

    calculations = []
    for address, group in sorted(_group(rows).items()):
        worst = max(group, key=lambda row: row["duration_ms"])
        per = [row["ns_per_element"] for row in group if row["ns_per_element"] is not None]
        calculations.append({
            "calculation": address,
            "invocations": len(group),
            "total_ms": round(sum(row["duration_ms"] for row in group), 3),
            "max_ms": round(worst["duration_ms"], 3),
            "share": round(sum(row["duration_ms"] for row in group) / total_ms, 4),
            "kind": worst["kind"],
            "bytes": worst["bytes"],
            "elements": worst["elements"],
            "shape": worst["shape"],
            "moved": worst["moved"],
            "ns_per_element": max(per) if per else None,
        })
    by_total = sorted(calculations, key=lambda row: (-row["total_ms"], row["calculation"]))

    findings: list[dict[str, Any]] = []
    for row in by_total[:top]:
        findings.append({
            "finding": "hot",
            "calculation": row["calculation"],
            "invocations": row["invocations"],
            "total_ms": row["total_ms"],
            "share": row["share"],
            "for": (
                f"{row['calculation']} is {round(row['share'] * 100, 1)}% of this run "
                f"({row['total_ms']} ms over {row['invocations']} invocation(s)): fix here first"
            ),
        })

    for address, group in sorted(_group(rows).items()):
        dense = [row for row in group if row["numeric"] and row["elements"] > dense_at]
        if dense:
            worst = max(dense, key=lambda row: row["elements"])
            findings.append({
                "finding": "dense-list",
                "calculation": address,
                "invocations": len(dense),
                "elements": worst["elements"],
                "shape": worst["shape"],
                "bytes": worst["bytes"],
                "truncated": bool(worst["truncated"]),
                "for": (
                    f"{address} returns a list of {worst['elements']} numbers "
                    + (f"(the record kept its first entries and a note) " if worst["truncated"]
                       else f"({worst['bytes']} bytes in the record) ")
                    + "that would be an array"
                ),
            })
        costly = [
            row for row in group
            if row["ns_per_element"] is not None
            and row["ns_per_element"] > per_element_at
            and row["moved"] >= floor
        ]
        if costly:
            worst = max(costly, key=lambda row: row["ns_per_element"])
            findings.append({
                "finding": "per-element",
                "calculation": address,
                "invocations": len(costly),
                "ns_per_element": worst["ns_per_element"],
                "elements": worst["moved"],
                "total_ms": round(sum(row["duration_ms"] for row in costly), 3),
                "for": (
                    f"{address} spends {worst['ns_per_element']} ns on each of {worst['moved']} elements: "
                    f"it is walking them in Python, not moving them in one pass"
                ),
            })
        capped = [row for row in group if row["over_cap"]]
        if capped:
            worst = max(capped, key=lambda row: row["over_cap"]["bytes"])
            kept = sum(1 for row in capped if row["over_cap"]["kept"])
            total_bytes = sum(row["over_cap"]["bytes"] for row in capped)
            findings.append({
                "finding": "over-cap",
                "calculation": address,
                "invocations": len(capped),
                "bytes": worst["over_cap"]["bytes"],
                "total_bytes": total_bytes,
                "cap": worst["over_cap"]["cap"],
                "kept": bool(kept),
                "for": (
                    f"{address} puts {total_bytes} bytes into the record over {len(capped)} invocation(s), "
                    + (
                        f"each over the {worst['over_cap']['cap']} byte cap: the record carries them only "
                        "because the run raised the cap"
                        if kept else
                        f"omitted over the {worst['over_cap']['cap']} byte cap: the record kept a note, not the value"
                    )
                ),
            })
        seen: dict[str, int] = {}
        for row in group:
            if row["input_key"]:
                seen[row["input_key"]] = seen.get(row["input_key"], 0) + 1
        repeats = {key: count for key, count in seen.items() if count > 1}
        if repeats:
            findings.append({
                "finding": "repeat-input",
                "calculation": address,
                "invocations": sum(repeats.values()),
                "repeats": len(repeats),
                "most": max(repeats.values()),
                "for": (
                    f"{address} was computed {sum(repeats.values())} times on {len(repeats)} distinct input(s): "
                    "a cache that isn't there"
                ),
            })

    order = {"hot": 0, "dense-list": 1, "per-element": 2, "over-cap": 3, "repeat-input": 4}
    findings.sort(key=lambda f: (order[f["finding"]], -f.get("total_ms", 0.0), f["calculation"]))
    return {
        "address": ADDRESS_TEMPLATE.format(stem=args["stem"]),
        "for": "name the hot Calculations of one run and the shape of their values, so the next pass is chosen and not guessed",
        "record": {
            "path": measured["path"],
            "pcr": measured["pcr"],
            "invocations": len(rows),
            "wall_ms": measured["counters"].get("wall_ms"),
            "measured_ms": round(total_ms, 3),
        },
        "thresholds": {
            "dense_list": dense_at,
            "per_element_ns": per_element_at,
            "element_floor": floor,
            "cap_bytes": thresholds["cap_bytes"],
            "top": top,
        },
        "calculations": by_total,
        "findings": findings,
        "quiet": [f["finding"] for f in findings] == ["hot"] * min(top, len(by_total)),
    }


EVALUATE = Calculation("fn.neat.hot.evaluate", evaluate)


def run_hot(measured: Mapping[str, Any], stem: str, record_path: str | None = None, **knobs: Any) -> dict[str, Any]:
    """Evaluate through a PCR so the pass leaves a receipt and a run record (as delta does)."""
    pxc = PxC()
    pcr = PCR("neat-hot")
    address = ADDRESS_TEMPLATE.format(stem=stem)
    pcr.calc("Hot", EVALUATE, id="evaluate", into=Part(address),
             args={"measured": dict(measured), "stem": stem, **knobs})
    run = pcr.run(pxc, observe=True)
    if record_path:
        write_record(run_record(run, pxc), record_path)
    return run.results["evaluate"]


# --- the table ---------------------------------------------------------------------

def stem_of(path: str, name: str | None = None) -> str:
    raw = name or os.path.splitext(os.path.basename(path))[0]
    slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    return slug or "record"


def table(part: Mapping[str, Any]) -> str:
    record = part["record"]
    lines = [
        f"record: {record['path']}  pcr={record['pcr']}  invocations={record['invocations']}  "
        f"measured={record['measured_ms']} ms"
    ]
    rows = [("CALCULATION", "N", "TOTAL MS", "MAX MS", "KIND", "BYTES", "ELEMENTS", "NS/ELEMENT")]
    for row in part["calculations"]:
        rows.append((
            row["calculation"], str(row["invocations"]), f"{row['total_ms']:.1f}", f"{row['max_ms']:.1f}",
            str(row["kind"]), str(row["bytes"]), str(row["elements"] or row["moved"] or 0),
            "-" if row["ns_per_element"] is None else f"{row['ns_per_element']:.1f}",
        ))
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    lines.extend("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip() for row in rows)
    lines.append("")
    lines.append("findings")
    for finding in part["findings"]:
        lines.append(f"  {finding['finding']:<12} {finding['for']}")
    if part["quiet"]:
        lines.append("  (nothing but hot: no dense list, no per-element cost, no over-cap value, no repeat)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="neat hot")
    parser.add_argument("record", help="one pyto-run-record@1 document")
    parser.add_argument("--name", default=None, help="the address stem (default: the record's file name)")
    parser.add_argument("--out-dir", default=None, help=f"where the Part and its record go (default {HOT_DIR})")
    parser.add_argument("--dense", type=int, default=DENSE_LIST, help=f"dense-list threshold (default {DENSE_LIST})")
    parser.add_argument("--per-element", type=float, default=PER_ELEMENT_NS,
                        help=f"per-element threshold in ns (default {PER_ELEMENT_NS})")
    parser.add_argument("--top", type=int, default=TOP, help=f"how many hot Calculations (default {TOP})")
    parser.add_argument("--json", action="store_true", help="print the Part instead of the table")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    measured = measure(load_record(args.record), path=args.record)
    stem = stem_of(args.record, args.name)
    out_dir = args.out_dir or os.path.join(args.root, HOT_DIR)
    os.makedirs(out_dir, exist_ok=True)
    part = run_hot(measured, stem, os.path.join(out_dir, f"{stem}.record.json"),
                   dense_list=args.dense, per_element_ns=args.per_element, top=args.top)
    with open(os.path.join(out_dir, f"{stem}.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(part, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(part, indent=2, sort_keys=True) if args.json else table(part))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
