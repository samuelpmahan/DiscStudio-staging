"""The homework: a class's scores, four Ticks, one run record.

    python homework.py --out evidence/run-1     # rewrite the committed evidence
    python homework.py --out /tmp/look          # anywhere else

What it computes, from one small CSV of names and scores held in a Part:

    Tick 1  Parse       the CSV text becomes a roster: one row per student, sorted by name
    Tick 2  Stats       the class average to two decimals, and the middle score
                        (the mean of the two middle scores for an even class),
                        as two Calculations side by side
    Tick 3  Letters     a letter for every student, from fixed cutoffs given as args
    Tick 4  Histogram   a text bar chart, one line per letter, A first

Mean and median share the Stats Tick because neither needs the other: both bind
the roster Parse produced and nothing else, so they are one step of the program.
A receipt is per Calculation, not per Tick, so each of them still records its own
reads, writes, duration and result digest exactly as it did when they were two
Ticks -- what one Tick adds is the claim that they could run side by side, which
`pyto/experiments/tick-laws` reads straight off this record.

What it writes into `--out`:

    record.json       the `pyto-run-record@1` document (pyto/viewer/RECORD.md),
                      produced by `pyto.materialize.run_record` -- the same
                      materializer the grouped-ablation experiment uses; no
                      format is invented here
    receipts.json     one `pyto.pcr.Receipt` per invocation, from
                      `PCR.run(pxc, observe=True)`, keyed by invocation id
    tick-viewer.html  the standalone Tick page, built by
                      `node pyto/viewer/embed.mjs`; skipped with a printed note
                      when node is not on PATH

Determinism. Nothing here reads the clock, the environment, a random source or a
file outside this directory: the roster is a constant in this file, every number
is computed from integers, and the two float divisions (mean, even-length median)
are IEEE doubles that every CPython gives the same bits for. Durations *are*
recorded -- `duration_ms` per invocation and `counters.wall_ms` -- because a
student's Tick timings are worth seeing, but `grade.py` removes them (and the
`source` block, which names the commit) before it compares anything. Those three
fields are the only place a wall clock reaches the record.

No kernel change: this file imports `pyto` and touches nothing under `pyto/src`.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import shutil
import subprocess
import sys

from pyto import PCR, Calculation, Part, PxC
from pyto.materialize import run_record, write_record

HERE = os.path.dirname(os.path.abspath(__file__))
PYTO_ROOT = os.path.dirname(os.path.dirname(HERE))
EMBED = os.path.join(PYTO_ROOT, "viewer", "embed.mjs")
DEFAULT_OUT = os.path.join(HERE, "evidence", "run-1")

PCR_NAME = "students-homework"

# The one input. A Part is a named value in the store; this one is the raw file the
# student was handed, and it is the only Part that exists before the run -- which is
# why `parse` is the run's one hit and the other four invocations are computed.
SCORES_CSV = Part("px.students.scores_csv")
ROSTER = Part("px.students.roster")
MEAN = Part("px.students.mean")
MEDIAN = Part("px.students.median")
LETTERS = Part("px.students.letters")
HISTOGRAM = Part("px.students.histogram")

CLASS_CSV = """name,score
Ada,91
Bao,78
Cleo,84
Dev,66
Eli,95
Fen,73
Gus,88
Hana,59
Ines,84
Jae,70
Kit,97
Lior,81
"""

# The rubric, as data: (letter, lowest score that earns it), highest first.
CUTOFFS = (("A", 90), ("B", 80), ("C", 70), ("D", 60), ("F", 0))


def parse_scores(args):
    """CSV text -> [{"name": str, "score": int}], sorted by name.

    The header row is required and is checked, so a student who pastes the wrong
    file is told so rather than getting a silently empty class.
    """
    lines = [line for line in args["text"].splitlines() if line.strip()]
    if not lines or lines[0].strip() != "name,score":
        raise ValueError("the first line must be the header 'name,score'")
    roster = []
    for number, line in enumerate(lines[1:], start=2):
        fields = line.split(",")
        if len(fields) != 2:
            raise ValueError(f"line {number}: expected 'name,score', got {line!r}")
        roster.append({"name": fields[0].strip(), "score": int(fields[1].strip())})
    return sorted(roster, key=lambda row: row["name"])


def mean_score(args):
    """The class average, to two decimals, with the total and the count beside it.

    `total` and `n` are in the result on purpose: a reader can redo the division by
    hand, which a bare average does not let them do.
    """
    scores = [row["score"] for row in args["roster"]]
    if not scores:
        raise ValueError("an empty roster has no mean")
    total = sum(scores)
    return {"n": len(scores), "total": total, "mean": round(total / len(scores), 2)}


def median_score(args):
    """The middle score; for an even class, the mean of the two middle scores."""
    scores = sorted(row["score"] for row in args["roster"])
    if not scores:
        raise ValueError("an empty roster has no median")
    middle = len(scores) // 2
    if len(scores) % 2 == 1:
        median = float(scores[middle])
    else:
        median = (scores[middle - 1] + scores[middle]) / 2
    return {"n": len(scores), "median": median}


def letter_grades(args):
    """A letter per student, from the cutoffs in `args`, in roster order."""
    cutoffs = [(str(letter), int(lowest)) for letter, lowest in args["cutoffs"]]
    graded = []
    for row in args["roster"]:
        letter = None
        for candidate, lowest in cutoffs:
            if row["score"] >= lowest:
                letter = candidate
                break
        if letter is None:
            raise ValueError(f"no cutoff covers {row['name']}'s score {row['score']}")
        graded.append({"name": row["name"], "score": row["score"], "letter": letter})
    return graded


def histogram(args):
    """A text bar chart: one line per letter in cutoff order, `bar` per student."""
    order = [str(letter) for letter, _lowest in args["cutoffs"]]
    counts = {letter: 0 for letter in order}
    for row in args["letters"]:
        counts[row["letter"]] += 1
    width = max(len(letter) for letter in order)
    return "\n".join(
        f"{letter:<{width}} {args['bar'] * counts[letter]} {counts[letter]}"
        for letter in order
    )


PARSE = Calculation("fn.students.parse", parse_scores)
MEAN_OF = Calculation("fn.students.mean", mean_score)
MEDIAN_OF = Calculation("fn.students.median", median_score)
LETTERS_OF = Calculation("fn.students.letters", letter_grades)
HISTOGRAM_OF = Calculation("fn.students.histogram", histogram)

# The invocation id -> the function whose source digest the receipt must carry.
# grade.py's check 3 reads this to recompute the digests from the source on disk.
SOURCE_OF = {
    "parse": parse_scores,
    "mean": mean_score,
    "median": median_score,
    "letters": letter_grades,
    "histogram": histogram,
}


def build_program() -> PCR:
    """The four Ticks, in order. This is the whole program.

    `Stats` names one Tick twice, which is how `PCR.calc` puts two Calculations in
    one Tick: `mean` and `median` both bind ROSTER (Parse's result) and neither
    binds the other, so the node law holds and the two are parallel branches.
    """
    pcr = PCR(PCR_NAME)
    pcr.calc("Parse", PARSE, id="parse", into=ROSTER, text=SCORES_CSV)
    pcr.calc("Stats", MEAN_OF, id="mean", into=MEAN, roster=ROSTER)
    pcr.calc("Stats", MEDIAN_OF, id="median", into=MEDIAN, roster=ROSTER)
    pcr.calc(
        "Letters", LETTERS_OF, id="letters", into=LETTERS,
        roster=ROSTER, args={"cutoffs": [list(pair) for pair in CUTOFFS]},
    )
    pcr.calc(
        "Histogram", HISTOGRAM_OF, id="histogram", into=HISTOGRAM,
        letters=LETTERS, args={"cutoffs": [list(pair) for pair in CUTOFFS], "bar": "#"},
    )
    return pcr


def commit_sha() -> str | None:
    """`git rev-parse HEAD`, or None when git cannot answer.

    Telemetry only: `grade.py` drops the whole `source` block before comparing, so
    a record made at one commit and replayed at another still matches.
    """
    try:
        completed = subprocess.run(
            ["git", "-C", HERE, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.stdout.strip() or None if completed.returncode == 0 else None


def run() -> dict:
    """Seed the store, run the four Ticks with observation on, return the record.

    `observe=True` is what gives the run receipts, and `run_record` requires them:
    without receipts a document could not honestly carry the calculation identity,
    the actual reads and writes, or the digests (pyto/viewer/RECORD.md).
    """
    pxc = PxC()
    pxc.set(SCORES_CSV, CLASS_CSV)
    preexisting = set(pxc.addresses())
    pcr = build_program()
    pcr_run = pcr.run(pxc, observe=True)
    record = run_record(
        pcr_run, pxc, preexisting=preexisting,
        source={"runtime": "pyto", "commit": commit_sha()},
    )
    return {"pxc": pxc, "pcr": pcr, "run": pcr_run, "record": record}


def receipts_payload(pcr_run) -> dict:
    """{invocation id: the Receipt as JSON}. The same shape run.py writes."""
    return {
        invocation_id: dataclasses.asdict(receipt)
        for invocation_id, receipt in pcr_run.receipts.items()
    }


def _dump(path: str, payload) -> str:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path


def write_viewer(record_path: str, out_path: str) -> str | None:
    """`node pyto/viewer/embed.mjs <record> --out <html>`, or None when node is absent."""
    if shutil.which("node") is None:
        return None
    subprocess.run(
        ["node", EMBED, record_path, "--out", out_path],
        check=True, capture_output=True, text=True, timeout=120,
    )
    return out_path


def write_evidence(result: dict, out_dir: str) -> list[str]:
    """record.json, receipts.json and (when node is on PATH) tick-viewer.html."""
    os.makedirs(out_dir, exist_ok=True)
    written = [write_record(result["record"], os.path.join(out_dir, "record.json"))]
    written.append(_dump(os.path.join(out_dir, "receipts.json"), receipts_payload(result["run"])))
    viewer = write_viewer(written[0], os.path.join(out_dir, "tick-viewer.html"))
    if viewer is None:
        print("note: node is not on PATH, so no tick-viewer.html was written", file=sys.stderr)
    else:
        written.append(viewer)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--out", default=DEFAULT_OUT,
        help="where the record, the receipts and the Tick page go "
        "(relative paths resolve against this directory; default evidence/run-1)",
    )
    ns = parser.parse_args(argv)
    out_dir = ns.out if os.path.isabs(ns.out) else os.path.join(HERE, ns.out)

    result = run()
    record = result["record"]
    counters = record["counters"]
    print(f"pcr:       {record['pcr']}  ({record['schema']})")
    print(f"ticks:     {[(tick['name'], len(tick['invocations'])) for tick in record['ticks']]}")
    print(
        "counters:  "
        f"invocations={counters['invocations']} hits={counters['hits']} computed={counters['computed']}"
    )
    print(f"mean:      {result['run'].results['mean']}")
    print(f"median:    {result['run'].results['median']}")
    print("histogram:")
    for line in result["run"].results["histogram"].splitlines():
        print("  " + line)
    for path in write_evidence(result, out_dir):
        # `--out` may point anywhere, including another drive on Windows, where
        # os.path.relpath raises rather than answering. The name is a label.
        try:
            shown = os.path.relpath(path, HERE)
        except ValueError:
            shown = os.path.abspath(path)
        print("wrote", shown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
