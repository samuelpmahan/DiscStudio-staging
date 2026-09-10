"""The mechanical half of the grade.

    python grade.py --run evidence/run-1 --handoff HANDOFF.md

Four checks, each of which a machine can settle on its own, and nothing else:

  1. Contract.   The run record validates against `pyto/viewer/RECORD.md`, read
                 through `viewer/test/record_schema.py` -- a validator written
                 from that document independently of the materializer that wrote
                 the record, so this is a second reader and not the producer
                 marking its own work.
  2. Replay.     A fresh process, started with a stripped environment from a
                 working directory outside the repository, runs the homework
                 again and produces a record that is byte-identical to the
                 committed one on the compared fields (COMPARED_OUT below says
                 what is left out and why).
  3. Receipts.   Every Tick in the record has a receipt for every invocation in
                 it, and each receipt's `implementation_sha256` is the digest of
                 that Calculation's source *as it is on disk right now*. Editing
                 homework.py without re-running it fails here.
  4. Hand-off.   HANDOFF.md gives every Tick in the record a list line of its own
                 under its "One line per Tick" heading, and names every file this
                 homework is made of. A Tick name that only turns up in prose does
                 not count: the step has to have its own line.

What is NOT checked here, and is the actual point of the assignment: whether the
hand-off explains the program in plain words well enough that a cold reader --
a person or an agent who has seen only the hand-off and never the code -- can
say what the program does. `grade.py` prints that reader's brief and stops. The
comparison between what the cold reader writes and what the program does is the
grade, and no exit code stands for it.

The caveat this whole experiment is built around: identical digests prove the
same computation, not the right answer. Checks 1-4 passing means the student's
record is honest about the program they wrote. Whether that program computes the
right thing needs a reference -- a worked answer, a second implementation, a
teacher -- which this file does not have and does not pretend to have.

Exit 0 when checks 1-4 all pass, 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PYTO_ROOT = os.path.dirname(os.path.dirname(HERE))
REPO_ROOT = os.path.dirname(PYTO_ROOT)
VIEWER_TEST_DIR = os.path.join(PYTO_ROOT, "viewer", "test")

# Two intra-repo sys.path inserts, both stated and printed
# (pyto/experiments/CAPTURE.md, "sys.path: what is logged and what is forbidden"):
# this experiment's own homework.py, and the viewer's independent validator.
for _directory, _why in (
    (HERE, "this experiment's own homework.py"),
    (VIEWER_TEST_DIR, "the independent record validator (record_schema.py)"),
):
    if _directory not in sys.path:
        print(f"[students/grade] sys.path.insert(0, {_directory!r})  # intra-repo: {_why}", file=sys.stderr)
        sys.path.insert(0, _directory)

import homework  # noqa: E402
from record_schema import RecordSchemaError  # noqa: E402
from record_schema import validate as validate_record  # noqa: E402

DEFAULT_RUN = os.path.join(HERE, "evidence", "run-1")
DEFAULT_HANDOFF = os.path.join(HERE, "HANDOFF.md")

# What check 2 leaves out of the comparison, and why. Everything else -- every
# Tick name, every invocation id, every binding, every argument, every address,
# every write, every result digest, every value, the part index and the invocation
# and hit counts -- is compared byte for byte.
COMPARED_OUT = (
    ("source", "names the runtime version and the commit, which move without the program moving"),
    ("counters.wall_ms", "a wall clock"),
    ("ticks[].invocations[].duration_ms", "a wall clock"),
)

COLD_READER_QUESTION = (
    "You have read the hand-off above and nothing else -- not the code, not the record.\n"
    "In plain words, and in no more than a paragraph: what does this program do?\n"
    "Name what goes in, what comes out, and what each step contributes. Then say\n"
    "which one sentence of the hand-off you were least sure of."
)

# `python -I -B -c <snippet> <experiment dir>`: no site packages beyond the
# interpreter's own, no bytecode read or written, no environment but PATH, and a
# working directory outside this repository. The child imports `pyto` and this
# experiment's `homework` and nothing else, runs the four Ticks, and writes the
# record it produced to stdout as canonical JSON. It does not know what it is
# being compared against; the parent does the comparing.
CHILD_SNIPPET = """\
import json, sys
experiment_dir = sys.argv[1]
sys.path.insert(0, experiment_dir)
sys.stderr.write(
    "[grade-child] sys.path.insert(0, %r)  # intra-repo: this experiment's own homework.py;"
    " see pyto/experiments/CAPTURE.md\\n" % experiment_dir
)
sys.stderr.write("[grade-child] dont_write_bytecode=%r\\n" % sys.dont_write_bytecode)
import homework
sys.stdout.write(json.dumps(homework.run()["record"], sort_keys=True))
"""

STRIPPED_ENV = {"PATH": os.environ.get("PATH", "")}
if os.name == "nt":  # python.exe will not start without these two on Windows
    for _name, _default in (("SystemRoot", None), ("SystemDrive", "C:")):
        _value = os.environ.get(_name, _default)
        if _value:
            STRIPPED_ENV[_name] = _value


def source_digest(function) -> str | None:
    """sha256 of a function's source with line endings normalized to LF.

    The same rule `pyto/src/pyto/pcr.py:_implementation_sha256` applies when it
    fills a receipt, restated here rather than imported: check 3 is worth nothing
    if the digest and the thing it is checked against come from the same code.
    """
    try:
        source = inspect.getsource(function)
    except (OSError, TypeError):
        return None
    return hashlib.sha256(source.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def compared(record: dict) -> str:
    """The record as canonical JSON, with the fields in COMPARED_OUT removed."""
    trimmed = {key: value for key, value in record.items() if key != "source"}
    trimmed["counters"] = {
        key: value for key, value in record["counters"].items() if key != "wall_ms"
    }
    trimmed["ticks"] = [
        {
            **tick,
            "invocations": [
                {key: value for key, value in invocation.items() if key != "duration_ms"}
                for invocation in tick["invocations"]
            ],
        }
        for tick in record["ticks"]
    ]
    return json.dumps(trimmed, sort_keys=True, indent=2)


def homework_files() -> list[str]:
    """Every file this homework is made of, as paths relative to this directory.

    Mechanical on purpose: whatever is in the experiment directory is what the
    hand-off has to account for. Bytecode is not a file anyone wrote, so
    `__pycache__` and `.pyc` are skipped and nothing else is.
    """
    found = []
    for root, directories, names in os.walk(HERE):
        directories[:] = sorted(name for name in directories if name != "__pycache__")
        for name in sorted(names):
            if name.endswith(".pyc"):
                continue
            found.append(os.path.relpath(os.path.join(root, name), HERE).replace(os.sep, "/"))
    return sorted(found)


# --- the four checks -----------------------------------------------------------


def check_contract(record: dict) -> tuple[bool, list[str]]:
    """1. The record is a `pyto-run-record@1` document, per an independent reader."""
    try:
        validate_record(record)
    except RecordSchemaError as error:
        return False, [f"the record does not validate: {error}"]
    return True, [f"validates as {record['schema']} ({record['counters']['invocations']} invocations)"]


def check_replay(record: dict, python: str | None = None) -> tuple[bool, list[str]]:
    """2. A fresh process reproduces the record byte-identically on the compared fields."""
    python = python or sys.executable
    workdir = tempfile.mkdtemp(prefix="students-grade-cwd-")
    if os.path.abspath(workdir).startswith(os.path.abspath(REPO_ROOT) + os.sep):
        return False, [f"the replay working directory {workdir} is inside the repository"]
    completed = subprocess.run(
        [python, "-I", "-B", "-c", CHILD_SNIPPET, HERE],
        cwd=workdir, env=dict(STRIPPED_ENV), capture_output=True, text=True, timeout=180,
    )
    if completed.returncode != 0:
        return False, [
            f"the fresh process exited {completed.returncode}",
            *completed.stderr.strip().splitlines()[-5:],
        ]
    try:
        replayed = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        return False, [f"the fresh process did not print a record: {error}"]
    mine, theirs = compared(record), compared(replayed)
    if mine != theirs:
        return False, ["the fresh process produced a different record", *_first_difference(mine, theirs)]
    lines = [
        f"a fresh process ({os.path.basename(python)} -I -B, env={sorted(STRIPPED_ENV)}, cwd outside the repository)",
        f"reproduced {len(mine)} bytes of compared record, byte for byte",
    ]
    lines += [f"not compared: {name} -- {why}" for name, why in COMPARED_OUT]
    return True, lines


def _first_difference(mine: str, theirs: str) -> list[str]:
    """The first line the two canonical renderings disagree on, with its neighbours."""
    left, right = mine.splitlines(), theirs.splitlines()
    for index in range(max(len(left), len(right))):
        a = left[index] if index < len(left) else "<end of committed record>"
        b = right[index] if index < len(right) else "<end of replayed record>"
        if a != b:
            return [f"line {index + 1}: committed {a.strip()!r}", f"line {index + 1}: replayed {b.strip()!r}"]
    return ["(the two renderings differ only in length)"]


def check_receipts(record: dict, receipts: dict) -> tuple[bool, list[str]]:
    """3. Every invocation has a receipt whose source digest is today's source."""
    problems, checked = [], 0
    for tick in record["ticks"]:
        if not tick["invocations"]:
            problems.append(f"Tick {tick['name']!r} has no invocation and so no receipt")
        for invocation in tick["invocations"]:
            identifier = invocation["id"]
            receipt = receipts.get(identifier)
            if receipt is None:
                problems.append(f"{identifier}: no receipt in receipts.json")
                continue
            function = homework.SOURCE_OF.get(identifier)
            if function is None:
                problems.append(f"{identifier}: homework.SOURCE_OF names no function for this invocation")
                continue
            today = source_digest(function)
            claimed = receipt["calculation"]["implementation_sha256"]
            in_record = invocation["calculation"]["implementation_sha256"]
            if claimed != today:
                problems.append(
                    f"{identifier}: the receipt's source digest {claimed} is not the digest of "
                    f"{function.__name__} as it is on disk ({today}) -- the source changed since the run"
                )
            elif in_record != today:
                problems.append(
                    f"{identifier}: the record's source digest {in_record} disagrees with the receipt's {claimed}"
                )
            else:
                checked += 1
    if problems:
        return False, problems
    return True, [f"{checked} invocation(s) across {len(record['ticks'])} Tick(s): receipt present, source digest is today's source"]


TICK_SECTION = "One line per Tick"


def tick_list_lines(handoff_text: str) -> list[str]:
    """The bullets under the hand-off's "One line per Tick" heading, text only.

    A bullet is a line that starts at column zero with `- ` or `* `; the indented
    lines a bullet wraps onto belong to the bullet above them and are not lines of
    their own. The section runs from its heading to the next heading of any level.
    """
    bullets: list[str] = []
    inside = False
    for line in handoff_text.splitlines():
        if line.startswith("#"):
            inside = TICK_SECTION.lower() in line.lower()
            continue
        if inside and line.startswith(("- ", "* ")):
            bullets.append(line[2:].strip())
    return bullets


def names_tick(bullet: str, name: str) -> bool:
    """Does this bullet's text start by naming `name`?

    Three forms, and only these three: `**Name**` (any punctuation after it),
    `Name:` and `Name ` -- plus a bullet that is the bare name and nothing else.
    The name has to open the line: a bullet that merely mentions the Tick
    somewhere in its prose is a mention, not that Tick's own line.
    """
    return bullet == name or bullet.startswith((f"**{name}**", f"{name}:", f"{name} "))


def check_handoff(record: dict, handoff_text: str) -> tuple[bool, list[str]]:
    """4. The hand-off gives every Tick a list line of its own, and names every file.

    The Tick half is deliberately not a substring search of the page. A step's name
    turns up in prose all over a good hand-off, so "the name appears somewhere"
    passes even when the student deleted that step's entry from the list -- which is
    exactly the omission this check exists to catch. What is required is a bullet
    under the "One line per Tick" heading whose text *starts* with the Tick's name.

    The file half stays a substring search: a file name is written in backticks and
    a hand-off may mention it anywhere it likes, so there is no line to look for.
    """
    ticks = [tick["name"] for tick in record["ticks"]]
    files = homework_files()
    bullets = tick_list_lines(handoff_text)
    missing_ticks = [name for name in ticks if not any(names_tick(b, name) for b in bullets)]
    missing_files = [name for name in files if name not in handoff_text]
    if missing_ticks or missing_files:
        problems = [
            f"the hand-off's {TICK_SECTION!r} list has no line of its own for Tick {name!r}"
            for name in missing_ticks
        ]
        if missing_ticks and not bullets:
            problems.append(f"(the hand-off has no {TICK_SECTION!r} section, or it holds no list lines)")
        problems += [f"the hand-off never names the file {name!r}" for name in missing_files]
        return False, problems
    return True, [
        f"one list line each for all {len(ticks)} Tick(s): {', '.join(ticks)}",
        f"names all {len(files)} file(s)",
    ]


# --- the report ----------------------------------------------------------------


def grade(run_dir: str, handoff_path: str, python: str | None = None) -> tuple[int, list[str]]:
    """Run the four checks and build the report. Returns (exit code, lines)."""
    lines: list[str] = [f"grade.py: {os.path.relpath(run_dir, HERE)} against {os.path.relpath(handoff_path, HERE)}", ""]
    record_path = os.path.join(run_dir, "record.json")
    receipts_path = os.path.join(run_dir, "receipts.json")
    for path in (record_path, receipts_path, handoff_path):
        if not os.path.isfile(path):
            lines.append(f"FAIL  there is no {path}")
            return 1, lines
    with open(record_path, encoding="utf-8") as handle:
        record = json.load(handle)
    with open(receipts_path, encoding="utf-8") as handle:
        receipts = json.load(handle)
    with open(handoff_path, encoding="utf-8") as handle:
        handoff_text = handle.read()

    results = [
        ("1 contract", check_contract(record)),
        ("2 replay", check_replay(record, python=python)),
        ("3 receipts", check_receipts(record, receipts)),
        ("4 hand-off", check_handoff(record, handoff_text)),
    ]
    failed = 0
    for name, (passed, detail) in results:
        lines.append(f"{'PASS' if passed else 'FAIL'}  {name}")
        lines += [f"        {line}" for line in detail]
        failed += 0 if passed else 1
    lines.append("")
    lines.append(f"mechanical: {len(results) - failed} of {len(results)} checks passed")
    lines.append(
        "not mechanical, and the actual grade: whether a cold reader can say what this "
        "program does from the hand-off alone. That is not automated here."
    )
    lines.append(
        "caveat: identical digests prove the same computation, not the right answer. "
        "A verifier still needs a reference."
    )
    lines.append("")
    lines.append("--- for the cold reader ---")
    lines.append("")
    lines.append(handoff_text.rstrip("\n"))
    lines.append("")
    lines.append("--- the question ---")
    lines.append("")
    lines.append(COLD_READER_QUESTION)
    return (0 if failed == 0 else 1), lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--run", default=DEFAULT_RUN, help="the run directory (default evidence/run-1)")
    parser.add_argument("--handoff", default=DEFAULT_HANDOFF, help="the hand-off page (default HANDOFF.md)")
    ns = parser.parse_args(argv)
    run_dir = ns.run if os.path.isabs(ns.run) else os.path.join(HERE, ns.run)
    handoff = ns.handoff if os.path.isabs(ns.handoff) else os.path.join(HERE, ns.handoff)
    code, lines = grade(run_dir, handoff)
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
