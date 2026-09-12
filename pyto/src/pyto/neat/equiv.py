"""neat equiv <record.json> --calc <fn.address> --candidate <module:function>: the trust path.

The owner, 2026-09-12, on the rewrite that made his generation thirty times
faster: "Encode a path to trusting the sparsification of things."

What made him trust it was not the tests. It was that the fast renderer
reproduced all thirty-two result hashes of the recorded run. So that is the
verb: for every receipt of one Calculation in a record, rebuild the inputs that
receipt was given, run the candidate on them, and compare what comes back with
what the record kept. The answer is a witness Part,
``px.exp.neat.equiv.<calc>.<candidate-sha-prefix>``, and it says ``trusted:
true`` only when every receipt matched and none was left unrebuilt.

Inputs are rebuilt from the record first -- an input bound to an earlier
invocation is that invocation's recorded value -- then from ``--store`` (a
``{address: value}`` document, as ``px cat`` and the evo run's ``parts.json``
write one) for an input bound to a Part the record does not carry. An input that
is neither is a refusal naming the receipt, the input, what was needed and what
was had: a claim is never made over a receipt that could not be rebuilt.

**The canonical rule** (``canonical``) is where the whole trust rests, so it is
one function with its own tests. Two results are the same when they are the same
*values*, not the same Python object:

- an ndarray of single-byte integers (duck-typed on ``tobytes``/``dtype``/
  ``shape`` -- this kernel imports no numpy), and
- a flat or rectangular nested list of ints in 0..255

both canonicalize to the raw bytes in C order, so ``(256, 256, 3)`` uint8 and
the 196,608-int list the same render wrote are one value. Everything else --
an ndarray of any other dtype (through ``tolist``), a dict, a string, a float --
canonicalizes to canonical JSON, the same bytes ``pcr`` digests a result with.
The shape is deliberately *not* in the bytes: the owner's trust was thirty-two
pixel hashes, and a list of pixels and an array of pixels are the same pixels.

When the record omitted a result because it was over the value cap, its note
carries the sha256 of the JSON payload; the comparison then runs on the JSON
path against that sha, and the row says so. A note that also says the arrays
were truncated first is refused rather than believed.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import os
import re
import sys
from typing import Any, Callable, Mapping

from pyto import Calculation, PCR, Part, PxC
from pyto.materialize import run_record, write_record
from pyto.pcr import _implementation_sha256

ADDRESS_TEMPLATE = "px.exp.neat.equiv.{calc}.{sha}"
EQUIV_DIR = os.path.join("pyto", "experiments", "review", "equiv")

CAP_NOTE_SHA = re.compile(r"over the \d+ byte cap; sha256 = ([0-9a-f]{64})")
TRUNCATED = "truncated"
VALUE_KINDS = ("json", "text", "svg", "png-data-url")


# --- the canonical rule ------------------------------------------------------------

def _is_ndarray(value: Any) -> bool:
    """Duck-typed: an array is anything that can hand over its bytes, dtype and shape."""
    return all(hasattr(value, name) for name in ("tobytes", "dtype", "shape", "tolist"))


def _byte_leaves(value: Any) -> list[int] | None:
    """The leaves of a flat or rectangular nested list of ints in 0..255, or None.

    Rectangular is required: a ragged list is not an array, and flattening one
    would make two different values look the same.
    """
    if not isinstance(value, list) or not value:
        return None
    if all(isinstance(item, int) and not isinstance(item, bool) and 0 <= item <= 255 for item in value):
        return list(value)
    if not all(isinstance(item, list) for item in value):
        return None
    width = len(value[0])
    leaves: list[int] = []
    for item in value:
        if len(item) != width:
            return None
        inner = _byte_leaves(item)
        if inner is None:
            return None
        leaves.extend(inner)
    return leaves


def canonical(value: Any) -> tuple[bytes, str]:
    """``(payload, how)``: the bytes two equal *values* share, and which path they took.

    The payload carries its path as a tag, so a byte-path value and a JSON-path
    value can never collide even when their bodies happen to agree.
    """
    if isinstance(value, (bytes, bytearray, memoryview)):
        return b"bytes\x00" + bytes(value), "bytes"
    if _is_ndarray(value):
        dtype = value.dtype
        if getattr(dtype, "itemsize", 0) == 1 and getattr(dtype, "kind", "") in ("u", "i", "b"):
            return b"bytes\x00" + bytes(value.tobytes()), "bytes"
        return canonical_json(value.tolist())
    leaves = _byte_leaves(value)
    if leaves is not None:
        return b"bytes\x00" + bytes(leaves), "bytes"
    return canonical_json(value)


def canonical_json(value: Any) -> tuple[bytes, str]:
    """The JSON path on its own: the bytes ``pcr`` and ``materialize`` digest a value with."""
    if _is_ndarray(value):
        value = value.tolist()
    return b"json\x00" + json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"), "json"


def digest(value: Any) -> tuple[str, str]:
    payload, how = canonical(value)
    return hashlib.sha256(payload).hexdigest(), how


def json_payload_sha(value: Any) -> str:
    """The sha256 ``materialize`` puts in an over-cap note: canonical JSON, untagged."""
    if _is_ndarray(value):
        value = value.tolist()
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# --- the host: the record, the store, the candidate ---------------------------------

def load_json(path: str) -> Any:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_candidate(spec: str) -> tuple[Callable[..., Any], str, str]:
    """``module:function`` or ``path/to/file.py:function``."""
    if ":" not in spec:
        raise SystemExit(f"equiv: --candidate wants module:function, got {spec!r}")
    where, name = spec.rsplit(":", 1)
    if where.endswith(".py") or os.sep in where or "/" in where:
        module_name = os.path.splitext(os.path.basename(where))[0]
        loader = importlib.util.spec_from_file_location(module_name, where)
        if loader is None or loader.loader is None:
            raise SystemExit(f"equiv: no module at {where!r}")
        module = importlib.util.module_from_spec(loader)
        sys.modules.setdefault(module_name, module)
        loader.loader.exec_module(module)
    else:
        module = importlib.import_module(where)
    if not hasattr(module, name):
        raise SystemExit(f"equiv: {where!r} has no {name!r}")
    function = getattr(module, name)
    return function, where, name


def describe(function: Callable[..., Any], module: str | None = None, name: str | None = None) -> dict[str, Any]:
    """The candidate as the witness names it: where it came from and the sha256 of its source."""
    return {
        "module": module or getattr(function, "__module__", "?"),
        "function": name or getattr(function, "__qualname__", "?"),
        "implementation_sha256": _implementation_sha256(function) or "0" * 64,
    }


def index(record: Mapping[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    """Every invocation by id, and which invocation wrote each address."""
    by_id: dict[str, dict[str, Any]] = {}
    writer: dict[str, str] = {}
    for tick in record.get("ticks", ()):
        for invocation in tick.get("invocations", ()):
            by_id[str(invocation.get("id"))] = dict(invocation, tick=tick.get("name"))
            for write in invocation.get("writes", ()):
                writer.setdefault(str(write.get("address")), str(invocation.get("id")))
            into = invocation.get("into")
            for address in ([into] if isinstance(into, str) else list(into or ())):
                writer.setdefault(str(address), str(invocation.get("id")))
    return by_id, writer


def recorded_value(invocation: Mapping[str, Any], address: str | None = None) -> tuple[Any, str | None]:
    """``(value, refusal)``: what the record kept for an invocation, or why it kept nothing."""
    value = invocation.get("value") or {}
    kind, data, note = value.get("kind"), value.get("data"), value.get("note")
    if kind not in VALUE_KINDS or data is None:
        return None, f"the record holds {kind} for {invocation.get('id')} ({note or 'no value'})"
    if note and TRUNCATED in note:
        return None, f"the record truncated {invocation.get('id')}'s value ({note})"
    if address and isinstance(data, dict) and address in data:
        return data[address], None
    return data, None


def rebuild(invocation: Mapping[str, Any], by_id: Mapping[str, Mapping[str, Any]],
            writer: Mapping[str, str], store: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]], bool]:
    """The inputs this receipt was given as values, every one that could not be rebuilt,
    and whether ``--store`` had to supply any of them."""
    call: dict[str, Any] = {}
    refusals: list[dict[str, str]] = []
    from_store = False
    for name, reference in (invocation.get("inputs") or {}).items():
        needed, had = str(reference), ""
        if isinstance(reference, str) and reference.startswith("fn:"):
            body = reference[3:]
            source_id, _, address = body.partition("#")
            source = by_id.get(source_id)
            if source is None:
                had = f"no invocation {source_id} in the record"
            else:
                value, refusal = recorded_value(source, address or None)
                if refusal:
                    had = refusal
                else:
                    call[name] = value
                    continue
        elif isinstance(reference, str) and reference.startswith("px:"):
            address = reference[3:]
            source = by_id.get(writer.get(address, ""))
            value, refusal = (None, "not written in this run")
            if source is not None:
                value, refusal = recorded_value(source, address)
            if refusal is None:
                call[name] = value
                continue
            if address in store:
                call[name] = store[address]
                from_store = True
                continue
            had = f"{refusal}; and --store does not hold {address}"
            needed = address
        else:
            had = f"an input reference this verb does not read: {reference!r}"
        refusals.append({"input": name, "needed": needed, "had": had})
    for name, value in (invocation.get("args") or {}).items():
        call[name] = value
    return call, refusals, from_store


# --- the comparison ----------------------------------------------------------------

def compare(invocation: Mapping[str, Any], produced: Any) -> dict[str, Any]:
    """One receipt's recorded result against one candidate result."""
    value = invocation.get("value") or {}
    kind, data, note = value.get("kind"), value.get("data"), value.get("note")
    if kind in VALUE_KINDS and data is not None and not (note and TRUNCATED in note):
        expected, how = digest(data)
        actual, actual_how = digest(produced)
        return {
            "state": "match" if expected == actual and how == actual_how else "mismatch",
            "via": f"canonical {how}", "expected": expected, "actual": actual,
        }
    match = CAP_NOTE_SHA.search(note or "") if kind == "omitted" else None
    if match and TRUNCATED not in (note or ""):
        expected = match.group(1)
        actual = json_payload_sha(produced)
        return {
            "state": "match" if expected == actual else "mismatch",
            "via": "the record's over-cap note: sha256 of the json payload",
            "expected": expected, "actual": actual,
        }
    return {
        "state": "not-comparable", "via": "none",
        "expected": None, "actual": None,
        "reason": f"the record kept {kind} for this receipt ({note or 'no value'})",
    }


def check(record: Mapping[str, Any], calc: str, candidate: Callable[..., Any],
          store: Mapping[str, Any] | None = None, record_path: str = "") -> dict[str, Any]:
    """Every receipt of one Calculation, rebuilt, run and compared. The host; it runs the candidate."""
    by_id, writer = index(record)
    store = store or {}
    rows: list[dict[str, Any]] = []
    store_used = False
    for invocation in by_id.values():
        if (invocation.get("calculation") or {}).get("address") != calc:
            continue
        row = {"id": invocation.get("id"), "tick": invocation.get("tick"), "into": invocation.get("into")}
        call, refusals, from_store = rebuild(invocation, by_id, writer, store)
        store_used = store_used or from_store
        if refusals:
            row.update({"state": "not-rebuildable", "refusals": refusals,
                        "reason": "; ".join(f"{r['input']}: needed {r['needed']}, had {r['had']}" for r in refusals)})
            rows.append(row)
            continue
        try:
            produced = candidate(call)
        except Exception as error:  # the candidate is someone else's code: its failure is a row
            row.update({"state": "mismatch", "via": "the candidate raised",
                        "reason": f"{type(error).__name__}: {error}"})
            rows.append(row)
            continue
        row.update(compare(invocation, produced))
        rows.append(row)
    rows.sort(key=lambda row: str(row["id"]))
    return {
        "record": {"path": record_path, "pcr": record.get("pcr")},
        "calculation": calc,
        "rows": rows,
        "store_used": store_used,
    }


# --- fn.neat.equiv.judge -----------------------------------------------------------

def judge(args: Mapping[str, Any]) -> dict[str, Any]:
    """The rows counted, and the one sentence the witness is for: trusted, or why not.

    Pure over the comparison: the candidate ran in the host, and what reaches the
    Part is digests and states.
    """
    rows = list(args["rows"])
    counts = {
        "receipts": len(rows),
        "matched": sum(1 for row in rows if row["state"] == "match"),
        "mismatched": sum(1 for row in rows if row["state"] == "mismatch"),
        "not_rebuildable": sum(1 for row in rows if row["state"] in ("not-rebuildable", "not-comparable")),
    }
    calc, candidate = args["calculation"], args["candidate"]
    trusted = bool(rows) and counts["matched"] == counts["receipts"]
    if not rows:
        reason = f"no receipt of {calc} in this record: nothing was compared"
    elif trusted:
        reason = (
            f"{counts['matched']}/{counts['receipts']} receipts of {calc} reproduced by "
            f"{candidate['module']}:{candidate['function']}, value for value"
        )
    else:
        reason = (
            f"{counts['matched']}/{counts['receipts']} matched; {counts['mismatched']} mismatched, "
            f"{counts['not_rebuildable']} not rebuilt"
        )
    return {
        "address": ADDRESS_TEMPLATE.format(calc=calc, sha=candidate["implementation_sha256"][:8]),
        "for": "witness that a candidate reproduces every recorded result of one Calculation, so the faster one can be trusted",
        "record": args["record"],
        "calculation": calc,
        "candidate": candidate,
        "counts": counts,
        "trusted": trusted,
        "reason": reason,
        "rows": [row for row in rows if row["state"] != "match"],
        "store_used": bool(args.get("store_used")),
    }


JUDGE = Calculation("fn.neat.equiv.judge", judge)


def run_equiv(checked: Mapping[str, Any], candidate: Mapping[str, Any],
              record_path: str | None = None) -> dict[str, Any]:
    """Judge through a PCR so the witness has a receipt and a run record (as delta does)."""
    pxc = PxC()
    pcr = PCR("neat-equiv")
    address = ADDRESS_TEMPLATE.format(calc=checked["calculation"], sha=candidate["implementation_sha256"][:8])
    pcr.calc("Equiv", JUDGE, id="judge", into=Part(address),
             args={"rows": list(checked["rows"]), "calculation": checked["calculation"],
                   "record": dict(checked["record"]), "candidate": dict(candidate),
                   "store_used": checked["store_used"]})
    run = pcr.run(pxc, observe=True)
    if record_path:
        write_record(run_record(run, pxc), record_path)
    return run.results["judge"]


# --- the table ---------------------------------------------------------------------

def table(part: Mapping[str, Any]) -> str:
    counts = part["counts"]
    candidate = part["candidate"]
    lines = [
        f"record: {part['record']['path']}  pcr={part['record']['pcr']}",
        f"calculation: {part['calculation']}",
        f"candidate: {candidate['module']}:{candidate['function']}  sha256={candidate['implementation_sha256'][:12]}",
        "",
        f"matched {counts['matched']}/{counts['receipts']}  mismatched {counts['mismatched']}  "
        f"not rebuildable {counts['not_rebuildable']}",
    ]
    if part["rows"]:
        rows = [("ID", "STATE", "VIA", "EXPECTED", "ACTUAL", "WHY")]
        for row in part["rows"]:
            rows.append((
                str(row.get("id")), str(row.get("state")), str(row.get("via") or "-"),
                (row.get("expected") or "-")[:12], (row.get("actual") or "-")[:12],
                str(row.get("reason") or "")[:80],
            ))
        widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
        lines.append("")
        lines.extend("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip() for row in rows)
    lines.append("")
    lines.append(f"trusted: {str(part['trusted']).lower()} ({part['reason']})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="neat equiv")
    parser.add_argument("record", help="one pyto-run-record@1 document")
    parser.add_argument("--calc", required=True, help="the Calculation address whose receipts are the test")
    parser.add_argument("--candidate", required=True, help="module:function (or path/to/file.py:function)")
    parser.add_argument("--store", default=None, help="a {address: value} document for inputs the record does not carry")
    parser.add_argument("--out-dir", default=None, help=f"where the witness and its record go (default {EQUIV_DIR})")
    parser.add_argument("--json", action="store_true", help="print the witness Part instead of the table")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    record = load_json(args.record)
    store = load_json(args.store) if args.store else {}
    function, where, name = load_candidate(args.candidate)
    candidate = describe(function, module=where, name=name)
    checked = check(record, args.calc, function, store, record_path=args.record)
    out_dir = args.out_dir or os.path.join(args.root, EQUIV_DIR)
    os.makedirs(out_dir, exist_ok=True)
    stem = f"{args.calc}.{candidate['implementation_sha256'][:8]}"
    part = run_equiv(checked, candidate, os.path.join(out_dir, f"{stem}.record.json"))
    with open(os.path.join(out_dir, f"{stem}.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(part, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(part, indent=2, sort_keys=True) if args.json else table(part))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
