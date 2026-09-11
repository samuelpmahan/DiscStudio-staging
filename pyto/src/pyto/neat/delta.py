"""neat delta <a> <b>: the capability delta against cost of two landings, computed.

The owner, 2026-09-11, on task 78 (a second page built beside the PxC composer
that already existed) against task 79 (the composer refined): "Obviously the
capability delta vs cost calculation ridiculously favors my way. Derive and
record THAT then make it a reusable thing through neat. Notes are useless. Code
that works once works again."

So this module is the calculation, not a note about it. Two landings in, one
Part out, ``px.exp.neat.delta.<a>.<b>``, and it runs the same way on any two
landings this repository (or any neat repository) has made.

What is measured, per landing, from its receipt and its git diff (the host,
``measure``; reading git is an effect, so it stays out of the Calculation):

- ``verified``: what works at the landing's result -- the verifier's own pass
  count (``# pass N`` in the landing's ``verifier.txt``) plus the sum of the
  receipt's ``check_all.counts``. This is capability in the only unit the
  owner accepts: code that runs green.
- ``patterns``: added and removed lines matching each named regex in the
  repository's manifest (``pyto/experiments/delta/patterns.json``):
  capability patterns (Calculations registered, user actions, prefix queries)
  and cost patterns (pages, moved assertions).
- ``files``, ``added``, ``removed``: the diff's size, excluding the evidence
  the landing itself writes (tasks, landings, the board).
- ``address_roots``: ``px.<a>.<b>`` roots that appear in added lines and
  nowhere in the base tree -- new address space.
- ``fixtures``: fixture files the landing regenerated.

And for the pair, ``measure_pair``:

- ``end_states``: the composite diff from the FIRST landing's base to the
  SECOND landing's result, measured like a landing, against the first
  landing alone. Two candidates for one capability are compared as end
  states: what the tree can do afterwards, and what it cost to get there.
- ``rework``: lines the second landing removed that the first landing added.
  The price of having built the other way first; zero when the second way
  was taken first.

``fn.neat.delta.evaluate`` (pure) turns the two measurements into the Part:
capability per end state (``verified`` first, then the capability patterns),
cost per end state (lines changed, files, pages, new address roots, moved
assertions, regenerated fixtures), the rework, and a verdict: the end state
with more verified behaviour wins, then more capability points (the capability
patterns summed), then the cheaper one; the ratio ``capability / cost`` is printed for both.

Same inputs, same bytes: the measurement is deterministic over the git
history, and the Calculation reads no clock and no environment.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Any, Mapping

from pyto import Calculation, PCR, Part, PxC
from pyto.materialize import run_record, write_record

ADDRESS_TEMPLATE = "px.exp.neat.delta.{a}.{b}"
DELTAS_DIR = os.path.join("pyto", "experiments", "review", "deltas")
PATTERNS_PATH = os.path.join("pyto", "experiments", "delta", "patterns.json")
LANDINGS_DIR = os.path.join("pyto", "experiments", "landings")

DEFAULT_PATTERNS: dict[str, Any] = {
    "exclude": ["pyto/experiments/tasks/", "pyto/experiments/landings/", "pyto/BOARD.md"],
    "capability": [
        {"name": "calculations", "regex": r"register\('(fn|oc)\.|Calculation\(\"(fn|oc)\."},
        {"name": "actions", "regex": r"data-action=\"|data-control=\""},
        {"name": "queries", "regex": r"\.\*['\"]"},
    ],
    "cost": [
        {"name": "pages", "regex": r"route === '|ui\.route = \["},
        {"name": "moved_assertions", "regex": r"\bassert", "files": r"(^|/)tests?/", "existing_only": True},
    ],
    "fixtures": r"(^|/)fixtures/",
    "lines_exclude": [r"(^|/)fixtures/", r"\.md$"],
}

ADDRESS_ROOT = re.compile(r"\bpx\.([a-z][a-zA-Z0-9]*)\.([a-z][a-zA-Z0-9]*)")


# --- the host: git and the landing directory ---------------------------------------

def _git(root: str, *args: str) -> str:
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, check=True).stdout


def load_patterns(root: str) -> dict[str, Any]:
    path = os.path.join(root, PATTERNS_PATH)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    return DEFAULT_PATTERNS


def find_landing(root: str, key: str) -> str:
    """The landing directory for a task id (``78``), a package (``task-78``) or a landing id."""
    landings = os.path.join(root, LANDINGS_DIR)
    if os.path.isdir(os.path.join(landings, key)):
        return os.path.join(landings, key)
    package = key if key.startswith("task-") else f"task-{key}"
    matches = sorted(d for d in os.listdir(landings) if d.endswith(f"-{package}") and os.path.isdir(os.path.join(landings, d)))
    if not matches:
        raise SystemExit(f"delta: no landing for {key!r} under {LANDINGS_DIR}")
    return os.path.join(landings, matches[-1])


def read_receipt(landing_dir: str) -> dict[str, Any]:
    with open(os.path.join(landing_dir, "receipt.json"), encoding="utf-8") as handle:
        return json.load(handle)


def result_sha(root: str, landing_dir: str, receipt: Mapping[str, Any]) -> str:
    """The landing's commit: the receipt's ``result_sha`` when the next landing filled it,
    else the commit whose message names this receipt (land.sh writes the receipt path in it)."""
    if receipt.get("result_sha"):
        return receipt["result_sha"]
    landing_id = os.path.basename(landing_dir)
    found = _git(root, "log", "--all", "--format=%H", f"--grep={landing_id}").split()
    if not found:
        raise SystemExit(f"delta: no commit names landing {landing_id}")
    return found[-1]


def verifier_pass(landing_dir: str) -> int:
    """``# pass N`` from node:test, or ``Ran N tests`` from unittest; 0 when neither is found."""
    path = os.path.join(landing_dir, "verifier.txt")
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    total = 0
    for match in re.finditer(r"^# pass (\d+)", text, re.M):
        total += int(match.group(1))
    for match in re.finditer(r"^Ran (\d+) tests?", text, re.M):
        total += int(match.group(1))
    return total


def _excluded(path: str, patterns: Mapping[str, Any]) -> bool:
    return any(path.startswith(prefix) or path == prefix.rstrip("/") for prefix in patterns.get("exclude", ()))


def diff_lines(root: str, base: str, result: str, patterns: Mapping[str, Any]) -> tuple[dict[str, tuple[int, int]], dict[str, list[str]], dict[str, list[str]]]:
    """Per file: (added, removed) counts, and the added / removed line texts."""
    numstat: dict[str, tuple[int, int]] = {}
    for line in _git(root, "diff", "--numstat", base, result).splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, removed, path = parts
        if _excluded(path, patterns):
            continue
        numstat[path] = (int(added) if added != "-" else 0, int(removed) if removed != "-" else 0)
    added_by: dict[str, list[str]] = {}
    removed_by: dict[str, list[str]] = {}
    current = None
    for line in _git(root, "diff", "-U0", "--no-color", base, result).splitlines():
        if line.startswith("+++ "):
            current = line[4:].removeprefix("b/") if line[4:] != "/dev/null" else current
            continue
        if line.startswith("--- "):
            if line[4:] != "/dev/null":
                current = line[4:].removeprefix("a/")
            continue
        if current is None or _excluded(current, patterns):
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added_by.setdefault(current, []).append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            removed_by.setdefault(current, []).append(line[1:])
    return numstat, added_by, removed_by


def _count(pattern: Mapping[str, Any], lines_by: Mapping[str, list[str]], new_files: set[str] = frozenset()) -> int:
    """Lines matching the pattern's regex; ``files`` narrows to paths matching it, and
    ``existing_only`` skips files the diff created (a new test file's asserts are
    verified behaviour, not assertions moved)."""
    regex = re.compile(pattern["regex"])
    files = re.compile(pattern["files"]) if pattern.get("files") else None
    total = 0
    for path, lines in lines_by.items():
        if files and not files.search(path):
            continue
        if pattern.get("existing_only") and path in new_files:
            continue
        total += sum(1 for line in lines if regex.search(line))
    return total


def new_address_roots(root: str, base: str, added_by: Mapping[str, list[str]]) -> list[str]:
    roots = {f"px.{m.group(1)}.{m.group(2)}" for lines in added_by.values() for line in lines for m in ADDRESS_ROOT.finditer(line)}
    if not roots:
        return []
    try:
        present = _git(root, "grep", "-ohE", r"px\.[a-z][a-zA-Z0-9]*\.[a-z][a-zA-Z0-9]*", base, "--", ".")
    except subprocess.CalledProcessError:
        present = ""
    seen = set(present.split())
    return sorted(r for r in roots if r not in seen)


def measure_range(root: str, base: str, result: str, patterns: Mapping[str, Any]) -> dict[str, Any]:
    numstat, added_by, removed_by = diff_lines(root, base, result, patterns)
    fixtures = re.compile(patterns.get("fixtures", r"(^|/)fixtures/"))
    new_files = set(_git(root, "diff", "--diff-filter=A", "--name-only", base, result).split())
    lines_exclude = [re.compile(x) for x in patterns.get("lines_exclude", [patterns.get("fixtures", r"(^|/)fixtures/"), r"\.md$"])]
    source = {path: counts for path, counts in numstat.items() if not any(x.search(path) for x in lines_exclude)}
    return {
        "base_sha": base,
        "result_sha": result,
        "files": len(numstat),
        "added": sum(a for a, _ in source.values()),
        "removed": sum(r for _, r in source.values()),
        "patterns": {
            p["name"]: {"added": _count(p, added_by, new_files), "removed": _count(p, removed_by, new_files)}
            for p in [*patterns.get("capability", ()), *patterns.get("cost", ())]
        },
        "address_roots": new_address_roots(root, base, added_by),
        "fixtures": sorted(path for path in numstat if fixtures.search(path)),
        "_added_lines": sorted({line for lines in added_by.values() for line in lines if line.strip()}),
        "_removed_lines": sorted({line for lines in removed_by.values() for line in lines if line.strip()}),
    }


def measure(root: str, key: str, patterns: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One landing: its receipt's verified counts and its diff, measured."""
    patterns = patterns or load_patterns(root)
    landing_dir = find_landing(root, key)
    receipt = read_receipt(landing_dir)
    base, result = receipt["base_sha"], result_sha(root, landing_dir, receipt)
    measured = measure_range(root, base, result, patterns)
    counts = (receipt.get("check_all") or {}).get("counts") or {}
    measured.update({
        "package": receipt.get("package"),
        "landing": os.path.basename(landing_dir),
        "verified": {"verifier": verifier_pass(landing_dir), "check_all": sum(int(v) for v in counts.values())},
    })
    return measured


def measure_pair(root: str, a: str, b: str) -> dict[str, Any]:
    patterns = load_patterns(root)
    ma, mb = measure(root, a, patterns), measure(root, b, patterns)
    composite = measure_range(root, ma["base_sha"], mb["result_sha"], patterns)
    composite["verified"] = mb["verified"]
    rework = sorted(set(mb["_removed_lines"]) & set(ma["_added_lines"]))
    strip = lambda m: {k: v for k, v in m.items() if not k.startswith("_")}  # noqa: E731
    return {"a": strip(ma), "b": strip(mb), "composite": strip(composite), "rework": len(rework), "patterns": patterns}


# --- fn.neat.delta.evaluate --------------------------------------------------------

def _capability(m: Mapping[str, Any], patterns: Mapping[str, Any]) -> dict[str, Any]:
    verified = m["verified"]["verifier"] + m["verified"]["check_all"]
    gained = {p["name"]: m["patterns"][p["name"]]["added"] - m["patterns"][p["name"]]["removed"] for p in patterns.get("capability", ())}
    return {"verified": verified, **gained}


def _cost(m: Mapping[str, Any], patterns: Mapping[str, Any]) -> dict[str, Any]:
    out = {"lines": m["added"] + m["removed"], "files": m["files"], "address_roots": len(m["address_roots"]), "fixtures": len(m["fixtures"])}
    for p in patterns.get("cost", ()):
        out[p["name"]] = m["patterns"][p["name"]]["added"] + m["patterns"][p["name"]]["removed"]
    return out


def _total_cost(cost: Mapping[str, Any]) -> int:
    return sum(int(v) for v in cost.values())


def evaluate(args: Mapping[str, Any]) -> dict[str, Any]:
    """Two end states compared: more verified behaviour wins; at a tie, the cheaper one.

    ``after_a`` is the first landing alone; ``after_b`` is the composite from the first
    landing's base to the second landing's result (the tree after both), so the two
    candidates are what the tree can do afterwards and what it cost to get there.
    ``rework`` is what the second landing tore out of the first: zero had the second
    way been taken first.
    """
    patterns = args["patterns"]
    a, b, composite = args["a"], args["b"], args["composite"]
    after_a = {"capability": _capability(a, patterns), "cost": _cost(a, patterns)}
    after_b = {"capability": _capability(composite, patterns), "cost": _cost(composite, patterns)}
    for state in (after_a, after_b):
        total = _total_cost(state["cost"])
        state["cost"]["total"] = total
        state["ratio"] = round(state["capability"]["verified"] / total, 4) if total else None
    points = lambda state: sum(v for k, v in state["capability"].items() if k != "verified")  # noqa: E731
    for state in (after_a, after_b):
        state["capability"]["points"] = points(state)
    ka, kb = (after_a["capability"]["verified"], after_a["capability"]["points"]), (after_b["capability"]["verified"], after_b["capability"]["points"])
    ca, cb = after_a["cost"]["total"], after_b["cost"]["total"]
    say = lambda k, c: f"{k[0]} verified, {k[1]} capability points, cost {c}"  # noqa: E731
    if kb > ka or (kb == ka and cb < ca):
        verdict, reason = "b", f"after b: {say(kb, cb)}; after a alone: {say(ka, ca)}"
    elif ka > kb or (ka == kb and ca < cb):
        verdict, reason = "a", f"after a alone: {say(ka, ca)}; after b: {say(kb, cb)}"
    else:
        verdict, reason = "tie", f"both {say(ka, ca)}"
    if args.get("rework"):
        reason += f"; b removed {args['rework']} lines a had added (the price of building a first)"
    return {
        "address": ADDRESS_TEMPLATE.format(a=a["package"], b=b["package"]),
        "a": {"package": a["package"], "landing": a["landing"], "capability": _capability(a, patterns), "cost": _cost(a, patterns)},
        "b": {"package": b["package"], "landing": b["landing"], "capability": _capability(b, patterns), "cost": _cost(b, patterns)},
        "end_states": {"after_a": after_a, "after_b": after_b},
        "rework": int(args.get("rework", 0)),
        "verdict": verdict,
        "reason": reason,
    }


EVALUATE = Calculation("fn.neat.delta.evaluate", evaluate)


def run_delta(pair: Mapping[str, Any], record_path: str | None = None) -> dict[str, Any]:
    """Evaluate through a PCR so the comparison leaves a receipt and a run record (as gate does)."""
    pxc = PxC()
    pcr = PCR("neat-delta")
    address = ADDRESS_TEMPLATE.format(a=pair["a"]["package"], b=pair["b"]["package"])
    pcr.calc("Delta", EVALUATE, id="evaluate", into=Part(address),
             args={k: (dict(v) if isinstance(v, Mapping) else v) for k, v in pair.items()})
    run = pcr.run(pxc, observe=True)
    if record_path:
        write_record(run_record(run, pxc), record_path)
    return run.results["evaluate"]


# --- the table -----------------------------------------------------------------------

def table(part: Mapping[str, Any]) -> str:
    a, b = part["end_states"]["after_a"], part["end_states"]["after_b"]
    rows = [("", f"after {part['a']['package']}", f"after {part['b']['package']}")]
    for key in a["capability"]:
        rows.append((f"capability.{key}", str(a["capability"][key]), str(b["capability"][key])))
    for key in a["cost"]:
        rows.append((f"cost.{key}", str(a["cost"][key]), str(b["cost"][key])))
    rows.append(("verified / cost", str(a["ratio"]), str(b["ratio"])))
    widths = [max(len(r[i]) for r in rows) for i in range(3)]
    lines = ["  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip() for row in rows]
    lines.append(f"rework: {part['rework']} lines")
    lines.append(f"verdict: {part['verdict']} ({part['reason']})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="neat delta")
    parser.add_argument("a", help="a task id, package or landing id")
    parser.add_argument("b")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out-dir", default=None, help=f"where the Part and its record go (default {DELTAS_DIR})")
    parser.add_argument("--json", action="store_true", help="print the Part instead of the table")
    args = parser.parse_args(argv)
    pair = measure_pair(args.root, args.a, args.b)
    out_dir = args.out_dir or os.path.join(args.root, DELTAS_DIR)
    os.makedirs(out_dir, exist_ok=True)
    stem = f"{pair['a']['package']}-{pair['b']['package']}"
    part = run_delta(pair, os.path.join(out_dir, f"{stem}.record.json"))
    with open(os.path.join(out_dir, f"{stem}.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(part, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(part, indent=2, sort_keys=True) if args.json else table(part))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
