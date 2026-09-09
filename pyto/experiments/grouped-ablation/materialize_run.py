"""Materialize the grouped ablation into the shared run record and per-Tick sheets.

    python3 experiments/grouped-ablation/materialize_run.py                    # evidence/run-1/record.json + ticks/
    python3 experiments/grouped-ablation/materialize_run.py --out /tmp/look    # anywhere else
    python3 experiments/grouped-ablation/materialize_run.py --no-sheets        # record only (no Pillow needed)

Runs the Day 1 program (seed 7, n 400) with `observe=True` through run.run_experiment
-- the same function that produced the committed evidence -- and writes exactly two
new things beside the existing evidence:

    evidence/run-1/record.json      the `pyto-run-record@1` document (pyto/viewer/RECORD.md)
    evidence/run-1/ticks/*.png      one neon sheet per Tick, plus a .svg beside the sheet
                                    for any SVG value (the library does not rasterize SVG)

It never writes any other file, so the nine Day 1 evidence files (testimony.json,
comparison.json, comparison.md, timings.json, variants.json, failed-variants.md,
mermaid.mmd, saved-work.json, commit.txt) and Day 2's retained.json/receipts.json are
left byte-identical: the record is derived from a fresh execution of the same program
and is checked against the committed comparison.json before anything is written
(`--allow-drift` downgrades that check to a warning).

`preexisting` is `run.EXTERNAL_ADDRESSES` -- the two Parts run_experiment seeds before
executing -- which is the accurate pre-run store RECORD.md:122 asks the pyto adapter
for, so `select` and `split` are the run's two hits and the other thirteen invocations
are computed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from pyto.materialize import run_record, tick_sheets, write_record  # noqa: E402

from run import (  # noqa: E402
    EXTERNAL_ADDRESSES,
    commit_sha,
    evidence_excludes,
    run_experiment,
)

DEFAULT_OUT = os.path.join(HERE, "evidence", "run-1")
SEED, N = 7, 400


def source_of(out_dir: str) -> dict:
    """The record's `source`: this runtime and the commit that produced it.

    `commit_sha` appends `-dirty` when this experiment or pyto/src differs from HEAD,
    with the evidence tree excluded (run.py:evidence_excludes) -- outputs are not the
    code that produced them.
    """
    return {"runtime": "pyto", "commit": commit_sha(HERE, exclude=evidence_excludes(out_dir))}


def check_against_committed(comparison: list[dict], out_dir: str) -> str | None:
    """None when the fresh run agrees with the committed comparison.json, else why not."""
    path = os.path.join(out_dir, "comparison.json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as handle:
        committed = json.load(handle)
    if committed.get("seed") != SEED or committed.get("n") != N:
        return f"{path} was generated with seed={committed.get('seed')} n={committed.get('n')}, not {SEED}/{N}"
    if committed.get("rows") != comparison:
        return f"the fresh run's comparison differs from {path}"
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--n", type=int, default=N)
    parser.add_argument(
        "--out",
        default=DEFAULT_OUT,
        help="evidence directory; relative paths resolve against the experiment directory "
        "(default: evidence/run-1, where only record.json and ticks/ are written)",
    )
    parser.add_argument("--no-sheets", action="store_true", help="write record.json only (no Pillow needed)")
    parser.add_argument(
        "--allow-drift",
        action="store_true",
        help="warn instead of failing when the fresh run disagrees with the committed comparison.json",
    )
    ns = parser.parse_args(argv)

    out_dir = ns.out if os.path.isabs(ns.out) else os.path.join(HERE, ns.out)
    result = run_experiment(ns.seed, ns.n)

    drift = check_against_committed(result["comparison"], out_dir) if (ns.seed, ns.n) == (SEED, N) else None
    if drift is not None:
        message = f"materialize_run.py: {drift}"
        if not ns.allow_drift:
            print(message + " -- refusing to write a record that describes a different run", file=sys.stderr)
            return 2
        print("warning: " + message, file=sys.stderr)

    record = run_record(
        result["run"],
        result["pxc"],
        preexisting=set(EXTERNAL_ADDRESSES),
        source=source_of(out_dir),
    )
    written = [write_record(record, os.path.join(out_dir, "record.json"))]
    if not ns.no_sheets:
        written.extend(tick_sheets(record, os.path.join(out_dir, "ticks")))

    counters = record["counters"]
    print(f"pcr:        {record['pcr']}  ({record['schema']})")
    print(f"source:     {json.dumps(record['source'], sort_keys=True)}")
    print(f"ticks:      {[(tick['name'], len(tick['invocations'])) for tick in record['ticks']]}")
    print(
        "counters:   "
        f"invocations={counters['invocations']} hits={counters['hits']} "
        f"computed={counters['computed']} wall_ms={counters['wall_ms']:.3f}"
    )
    hits = [inv["id"] for tick in record["ticks"] for inv in tick["invocations"] if inv["hit"]]
    print(f"hits:       {hits}")
    kinds: dict[str, int] = {}
    for tick in record["ticks"]:
        for invocation in tick["invocations"]:
            kinds[invocation["value"]["kind"]] = kinds.get(invocation["value"]["kind"], 0) + 1
    print(f"value kinds:{json.dumps(kinds, sort_keys=True)}")
    print(f"parts:      {len(record['parts'])}")
    for path in written:
        relative = os.path.relpath(path, HERE)
        print("wrote", path if relative.startswith("..") else relative)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
