"""Explain what changed between two retained records, by traversal over the program.

Experiment-local (critic gap 4: `explain_changes` is used experiment-locally here
before any promotion of a compare.py into pyto/src is even discussed). It reads
only retained data: the program dicts, the external map and the result digests of
two `retain.retain_run` records. It never executes anything.

`explain_changes(a, b)` answers the question a cache cannot answer: not "is this
value stale" but "which invocations changed, why, and which invocations are only
affected because they consume a changed one". The `reason` is the *first* of
these that applies, in this order:

    calculation  the fn. address at that id differs
    input        the binding map differs (a px: became fn:, a ref moved, ...)
    args         the args dict differs
    external     bindings and args are identical, but a px: address it reads has
                 a different external entry in the two records
    digest       everything above is identical and the retained result digest differs

The order matters: `args` outranks `digest` so an args key that shadows a bound
input (pcr.py:159-160 lets args win silently) is reported as an authored change,
not as an unexplained digest drift; and `external` outranks `digest` so an
unchanged program over changed input data is explained rather than called
"unchanged program, mystery result".

`unchanged_upstream` is the reuse claim: ids that are neither changed nor
downstream of a changed id. Those are the invocations a later run may skip by
digest. Nothing here asserts they *were* skipped.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Mapping

PX = "px:"
FN = "fn:"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _program_of(record: Mapping[str, Any]) -> Mapping[str, Any]:
    if "program" in record:
        return record["program"]
    if "ticks" in record and "name" in record:
        return record  # a bare program dict is accepted too
    raise ValueError("compare_local: expected a retained record with a 'program', or a program dict")


def invocations(program: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """{id: entry} in program order; entries gain 'tick' so a reader can locate them."""
    out: dict[str, dict[str, Any]] = {}
    for tick in program.get("ticks", []):
        for entry in tick.get("calculations", []):
            item = dict(entry)
            item["tick"] = tick.get("name")
            out[entry["id"]] = item
    return out


def consumers_of(program: Mapping[str, Any], ref: str) -> list[str]:
    """Ids binding `ref` ('fn:<id>' or 'px:<address>'), in program order.

    A px: ref also lists the ids that read the Part *address* written by another
    invocation's `into`, which is how a cross-PCR program (writers are per PCR,
    pcr.py:118-123) still shows its edges.
    """
    program = _program_of(program)
    if not (ref.startswith(PX) or ref.startswith(FN)):
        raise ValueError(f"compare_local.consumers_of: ref '{ref}' must start with 'px:' or 'fn:'")
    return [
        entry["id"]
        for entry in invocations(program).values()
        if ref in (entry.get("inputs") or {}).values()
    ]


def _edges(program: Mapping[str, Any]) -> dict[str, list[str]]:
    """producer id -> consumer ids, over fn: refs and over px: addresses written in-program."""
    entries = invocations(program)
    writer_of = {entry["into"]: entry["id"] for entry in entries.values() if entry.get("into")}
    out: dict[str, list[str]] = {invocation_id: [] for invocation_id in entries}
    for entry in entries.values():
        for ref in (entry.get("inputs") or {}).values():
            producer = None
            if ref.startswith(FN):
                producer = ref[len(FN):]
            elif ref.startswith(PX) and ref[len(PX):] in writer_of:
                producer = writer_of[ref[len(PX):]]
            if producer is not None and producer in out and entry["id"] not in out[producer]:
                out[producer].append(entry["id"])
    return out


def _external_entry(record: Mapping[str, Any], address: str) -> Any:
    return (record.get("external") or {}).get(address)


def _external_changed(record_a: Mapping[str, Any], record_b: Mapping[str, Any], entry: Mapping[str, Any]) -> bool:
    for ref in (entry.get("inputs") or {}).values():
        if not ref.startswith(PX):
            continue
        address = ref[len(PX):]
        left, right = _external_entry(record_a, address), _external_entry(record_b, address)
        if left is None and right is None:
            continue
        if _canonical(left) != _canonical(right):
            return True
    return False


def _reason(record_a: Mapping[str, Any], record_b: Mapping[str, Any], old: Mapping[str, Any], new: Mapping[str, Any]) -> str | None:
    if old.get("calculation") != new.get("calculation"):
        return "calculation"
    if _canonical(old.get("inputs") or {}) != _canonical(new.get("inputs") or {}):
        return "input"
    if _canonical(old.get("args") or {}) != _canonical(new.get("args") or {}):
        return "args"
    if _external_changed(record_a, record_b, new):
        return "external"
    digests_a, digests_b = record_a.get("results") or {}, record_b.get("results") or {}
    if new["id"] in digests_a or new["id"] in digests_b:
        if digests_a.get(new["id"]) != digests_b.get(new["id"]):
            return "digest"
    return None


def explain_changes(record_a: Mapping[str, Any], record_b: Mapping[str, Any]) -> dict[str, Any]:
    """Traversal-only diff of two retained records. Lists are in record_b's program order."""
    program_a, program_b = _program_of(record_a), _program_of(record_b)
    entries_a, entries_b = invocations(program_a), invocations(program_b)

    changed: list[str] = []
    reason: dict[str, str] = {}
    for invocation_id, new in entries_b.items():
        old = entries_a.get(invocation_id)
        if old is None:
            continue
        why = _reason(record_a, record_b, old, new)
        if why is not None:
            changed.append(invocation_id)
            reason[invocation_id] = why

    edges = _edges(program_b)
    seen = set(changed)
    queue = list(changed)
    affected: list[str] = []
    while queue:
        for consumer in edges.get(queue.pop(0), []):
            if consumer not in seen:
                seen.add(consumer)
                affected.append(consumer)
                queue.append(consumer)

    common = [i for i in entries_b if i in entries_a]
    order = list(entries_b)
    return {
        "changed": [i for i in order if i in set(changed)],
        "reason": reason,
        "downstream_affected": [i for i in order if i in set(affected)],
        "unchanged_upstream": [i for i in order if i in common and i not in seen],
        "added": [i for i in order if i not in entries_a],
        "removed": [i for i in entries_a if i not in entries_b],
    }


def skippable_by_digest(record_a: Mapping[str, Any], record_b: Mapping[str, Any]) -> list[str]:
    """The ids a later run could reuse from the earlier record: unchanged and not downstream."""
    return explain_changes(record_a, record_b)["unchanged_upstream"]


def render(explanation: Mapping[str, Any]) -> str:
    """One line per changed id plus the two counts; every number comes from the dict."""
    lines = [
        f"changed {len(explanation['changed'])}, downstream {len(explanation['downstream_affected'])}, "
        f"unchanged upstream {len(explanation['unchanged_upstream'])}, "
        f"added {len(explanation['added'])}, removed {len(explanation['removed'])}"
    ]
    for invocation_id in explanation["changed"]:
        lines.append(f"  {invocation_id}: {explanation['reason'][invocation_id]}")
    return "\n".join(lines)
