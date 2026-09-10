"""``px``: a small shell over run records.

Seven commands -- ``ps``, ``ls``, ``cat``, ``diff``, ``laws``, ``receipts``,
``effects`` -- over a
``pyto-run-record@1`` document (``pyto/viewer/RECORD.md``).  The record is the one
interface, exactly as a path is in the shell this borrows its verbs from
(``pyto/questions.md`` ``{?} EverythingIsAPart``): every runtime that writes the
format gets these tools for nothing, and no command imports the kernel's runtime.
The only kernel-adjacent imports are the shared record validator
(``pyto/viewer/test/record_schema.py``) and the law checker
(``pyto/experiments/tick-laws/tick_laws.py``), both loaded by path the way
``experiments/students/grade.py`` loads the validator, so ``px`` reads JSON and
nothing else.

Every command's output is a pure function of its inputs.  Nothing is printed that
the record does not carry: no timestamps, no absolute paths (``px laws`` names the
record's ``pcr`` where ``tick_laws`` echoes the path it was given), stable
ordering everywhere, and durations only when ``--times`` asks for them.  Two runs
over the same file are byte for byte the same, which is what
``pyto/tests/test_px.py`` asserts against committed expected output.

Exit codes: ``0`` success, ``1`` a difference (``px diff``) or a law violation
(``px laws``), ``2`` bad usage or a record the validator rejects.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

__all__ = ["main"]

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = REPO_ROOT / "viewer" / "test" / "record_schema.py"
TICK_LAWS_PATH = REPO_ROOT / "experiments" / "tick-laws" / "tick_laws.py"

EXIT_OK = 0
EXIT_DIFFERENCE = 1
EXIT_USAGE = 2

MISSING_VALUE = "not carried"
NOTHING = "-"


class PxError(Exception):
    """Anything the user should see on stderr with exit code 2."""


# --- loading the two shared readers by path -----------------------------------


def _load_module(name: str, path: Path):
    """Import ``path`` under ``name`` without touching ``sys.path``.

    ``experiments/students/grade.py`` inserts the directory instead; a spec keeps
    ``px`` from changing global import state, which matters because ``px`` is a
    console script that may run inside anything.
    """
    if not path.exists():
        raise PxError(f"px: cannot find {name} at {path.name}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - importlib contract
        raise PxError(f"px: cannot load {name} from {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, module)
    spec.loader.exec_module(module)
    return module


def _schema():
    return _load_module("px_record_schema", VALIDATOR_PATH)


def _tick_laws():
    return _load_module("px_tick_laws", TICK_LAWS_PATH)


# --- the record ---------------------------------------------------------------


def load_record(path: str) -> dict[str, Any]:
    """Read, parse and validate one run record.  Every command starts here."""
    try:
        with open(path, encoding="utf-8") as handle:
            record = json.load(handle)
    except OSError as exc:
        raise PxError(f"px: cannot read {Path(path).name}: {exc.strerror}") from exc
    except json.JSONDecodeError as exc:
        raise PxError(f"px: {Path(path).name} is not JSON: {exc.msg} (line {exc.lineno})") from exc
    if not isinstance(record, dict):
        raise PxError(f"px: {Path(path).name} is not a record object")
    schema = _schema()
    try:
        schema.validate(record)
    except Exception as exc:
        raise PxError(f"px: {Path(path).name} is not a pyto-run-record@1: {exc}") from exc
    return record


def invocations(record: dict[str, Any]) -> list[tuple[int, str, dict[str, Any]]]:
    """Every invocation in run order as ``(tick index, tick name, invocation)``."""
    rows = []
    for tick in record["ticks"]:
        for inv in tick["invocations"]:
            rows.append((tick["index"], tick["name"], inv))
    return rows


def into_addresses(inv: dict[str, Any]) -> list[str]:
    """The addresses an invocation declared: ``into`` is one, several, or none."""
    return list(_schema().produce_addresses(inv["into"]))


def reads_of(record: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    """Every read per invocation id, resolved and sorted.

    ``inputs`` is the only field that carries every read: a ``px:`` binding is a
    store read, an ``fn:`` binding is a result read resolved through the
    producer's ``into`` (``pyto/questions.md`` ``{?} ResultReadsAreReads``).
    ``declared_consumes`` and ``actual_consumes`` are unioned in defensively, as
    both reference readers do (``viewer/adapters.js``,
    ``viewer/test/record_schema.py``).
    """
    schema = _schema()
    produced_by: dict[str, list[str]] = {}
    out: dict[str, tuple[str, ...]] = {}
    for _, _, inv in invocations(record):
        reads: set[str] = set(inv["actual_consumes"])
        for binding in list(inv["inputs"].values()) + list(inv["declared_consumes"]):
            reads.update(schema.resolve_binding(binding, produced_by))
        out[inv["id"]] = tuple(sorted(reads))
        produces = into_addresses(inv)
        if produces:
            produced_by[inv["id"]] = produces
    return out


# --- rendering ----------------------------------------------------------------


def table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    """Left-aligned columns, two spaces between, no trailing whitespace.

    Widths come from the data, so the output is a pure function of the record and
    a row never wraps because of a row in some other file.
    """
    widths = [len(head) for head in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    lines = []
    for row in [list(headers)] + [list(row) for row in rows]:
        cells = [
            cell.ljust(widths[index]) if index < len(row) - 1 else cell
            for index, cell in enumerate(row)
        ]
        lines.append("  ".join(cells).rstrip())
    return lines


def joined(values: Iterable[str]) -> str:
    values = list(values)
    return ",".join(values) if values else NOTHING


def milliseconds(value: Any) -> str:
    """A duration from the record, fixed to three places, or ``-`` when null.

    The number is the record's, never the clock's: ``px`` prints it only under
    ``--times`` and computes none of its own.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return NOTHING
    return f"{value:.3f}"


def canonical_json(value: Any) -> str:
    """The record's own spelling: sorted keys, two-space indent (RECORD.md)."""
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)


# --- px ps --------------------------------------------------------------------


def cmd_ps(args: argparse.Namespace) -> int:
    """One line per invocation, in run order: the record's process table."""
    record = load_record(args.record)
    headers = ["TICK", "TICK-NAME", "ID", "CALCULATION", "INTO", "STATE"]
    if args.times:
        headers.append("MS")
    rows = []
    for index, name, inv in invocations(record):
        row = [
            str(index),
            name,
            inv["id"],
            inv["calculation"]["address"],
            joined(into_addresses(inv)),
            "hit" if inv["hit"] else "computed",
        ]
        if args.times:
            row.append(milliseconds(inv["duration_ms"]))
        rows.append(row)
    for line in table(headers, rows):
        print(line)
    return EXIT_OK


# --- px ls --------------------------------------------------------------------


def cmd_ls(args: argparse.Namespace) -> int:
    """Every address the record knows, sorted, with who produced each.

    The index is derived from the invocations by the shared validator's own
    reading of RECORD.md (``derive_part_index``) and then unioned with the
    record's ``parts`` block, which is where a receipt address appears when a
    record lists one -- ``parts`` is derived and for convenience, so it is a
    second source and not the only one.
    """
    record = load_record(args.record)
    derived = _schema().derive_part_index(record["ticks"])
    rows_by_address: dict[str, dict[str, Any]] = {}
    for address, row in derived.items():
        rows_by_address[address] = dict(row)
    for address, row in record["parts"].items():
        rows_by_address.setdefault(address, dict(row))
    lines = []
    for address in sorted(rows_by_address):
        if args.prefix and not address.startswith(args.prefix):
            continue
        row = rows_by_address[address]
        written_by = row.get("written_by")
        if written_by:
            origin = written_by
        elif row.get("preexisting"):
            origin = "preexisting"
        else:
            origin = "unknown"
        kind = "receipt" if address.startswith("px.receipt.") else "part"
        lines.append([address, kind, origin])
    for line in table(["ADDRESS", "KIND", "PRODUCED-BY"], lines):
        print(line)
    return EXIT_OK


# --- px cat -------------------------------------------------------------------


def cmd_cat(args: argparse.Namespace) -> int:
    """The value of a produced Part, as canonical JSON.

    The last invocation to publish the address wins, which is the value the store
    was left holding.  A record may carry no value at all (``kind: omitted``, or
    a runtime that retains none), and then this says so rather than inventing
    one.
    """
    record = load_record(args.record)
    producer = None
    for _, _, inv in invocations(record):
        if args.address in into_addresses(inv):
            producer = inv
    if producer is None:
        raise PxError(
            f"px: no invocation in this record produced {args.address!r} "
            f"(px ls {Path(args.record).name} lists what it knows)"
        )
    block = producer.get("value")
    if not isinstance(block, dict) or block.get("kind") == "omitted" or block.get("data") is None:
        note = (block or {}).get("note") if isinstance(block, dict) else None
        print(f"{MISSING_VALUE}: {note}" if note else MISSING_VALUE)
        return EXIT_OK
    data = block["data"]
    declared = into_addresses(producer)
    if len(declared) > 1:
        if isinstance(data, dict) and args.address in data:
            data = data[args.address]
        else:
            print(f"{MISSING_VALUE}: {producer['id']} published several Parts and the "
                  f"record's value does not name {args.address}")
            return EXIT_OK
    print(canonical_json(data))
    return EXIT_OK


# --- px diff ------------------------------------------------------------------


def cmd_diff(args: argparse.Namespace) -> int:
    """The two records' differences by invocation; exit 1 when there are any.

    Four kinds, in this order: an invocation added, one removed, a result digest
    changed, a read set changed.  Anything else two records may disagree about --
    durations above all -- is not a difference in what was computed and is not
    reported.
    """
    left = load_record(args.a)
    right = load_record(args.b)
    left_by_id = {inv["id"]: (index, name, inv) for index, name, inv in invocations(left)}
    right_by_id = {inv["id"]: (index, name, inv) for index, name, inv in invocations(right)}
    left_reads, right_reads = reads_of(left), reads_of(right)

    lines: list[str] = []
    for id_ in sorted(set(right_by_id) - set(left_by_id)):
        index, name, _ = right_by_id[id_]
        lines.append(f"added    {id_}  tick {index} {name}")
    for id_ in sorted(set(left_by_id) - set(right_by_id)):
        index, name, _ = left_by_id[id_]
        lines.append(f"removed  {id_}  tick {index} {name}")
    for id_ in sorted(set(left_by_id) & set(right_by_id)):
        before, after = left_by_id[id_][2], right_by_id[id_][2]
        if before["result_sha256"] != after["result_sha256"]:
            lines.append(
                f"digest   {id_}  {before['result_sha256']} -> {after['result_sha256']}"
            )
        if left_reads[id_] != right_reads[id_]:
            gone = [f"-{address}" for address in left_reads[id_] if address not in right_reads[id_]]
            new = [f"+{address}" for address in right_reads[id_] if address not in left_reads[id_]]
            lines.append(f"reads    {id_}  {' '.join(gone + new)}")

    if not lines:
        print("no differences")
        return EXIT_OK
    for line in lines:
        print(line)
    return EXIT_DIFFERENCE


# --- px laws ------------------------------------------------------------------


def cmd_laws(args: argparse.Namespace) -> int:
    """The node law and the loop law, delegated to ``tick_laws``.

    ``tick_laws.analyze_record`` is the checker; ``px`` only renders it, because
    ``tick_laws``' own text output echoes the path it was handed and ``px``
    prints no paths.  The record's ``pcr`` name stands in its place, and the exit
    code is ``tick_laws``': ``0`` when both laws hold, ``1`` otherwise.

    Work and critical path come from the record's durations, so they appear only
    under ``--times``, like every other duration ``px`` prints.

    Inside a Tick the Calculations are a sequence in declared order; ``tick_laws``
    classifies each Tick ``parallel`` (no sibling reads) or ``chain`` (reads earlier
    siblings, runs in order, latency is the sum). A chain is not a violation. When a
    record has one, the node-law line counts the modes (``node law: ok (2 parallel,
    1 chain)``) and under ``--times`` the chain Tick's line says ``chain``; a record
    with no chain prints exactly as before. Only a backwards read (a sibling declared
    after the reader) and two siblings producing one Part break the node law.
    """
    record = load_record(args.record)
    report = _tick_laws().analyze_record(record)
    print(f"LIMITATION: {report['limitation']}")
    print(f"pcr: {record['pcr']}")
    modes = report["laws"]["node"]["modes"]
    for law in ("node", "loop"):
        found = report["laws"][law]["violations"]
        line = f"{law} law: ok" if not found else f"{law} law: {len(found)} violation(s)"
        if law == "node" and modes["chain"]:
            line += f" ({modes['parallel']} parallel, {modes['chain']} chain)"
        print(line)
    if args.times:
        for tick in report["ticks"]:
            print(
                f"Tick {tick['tick']}: work_ms={milliseconds(tick['work_ms'])} "
                f"latency_ms={milliseconds(tick['latency_ms'])}"
                + (" chain" if tick["mode"] == "chain" else "")
            )
        summary = report["summary"]
        print(
            f"Summary: work_ms={milliseconds(summary['work_ms'])} "
            f"critical_path_ms={milliseconds(summary['critical_path_ms'])}"
        )
    for violation in report["violations"]:
        print(f"VIOLATION {violation['law']}: {violation['message']}")
    return EXIT_OK if report["ok"] else EXIT_DIFFERENCE


# --- px receipts --------------------------------------------------------------


def cmd_receipts(args: argparse.Namespace) -> int:
    """The receipts as rows: declared beside actual, reads beside writes.

    A record carries no receipt store rows (RECORD.md, "Receipts as Parts": its
    ``ticks`` come from the testimony *and* the receipts), so these rows are the
    record's witness of each ``Receipt``, one per invocation.  Declared reads keep
    their ``px:`` spelling and actual reads are bare addresses, which is the whole
    point of showing them side by side: a read served from the run's results
    never went through the store and so leaves the actual column empty.
    """
    record = load_record(args.record)
    headers = [
        "TICK", "ID", "DECLARED-READS", "ACTUAL-READS",
        "DECLARED-WRITES", "ACTUAL-WRITES", "RESULT-SHA256", "IMPLEMENTATION-SHA256",
    ]
    rows = []
    for index, name, inv in invocations(record):
        if args.tick is not None and name != args.tick:
            continue
        rows.append([
            str(index),
            inv["id"],
            joined(inv["declared_consumes"]),
            joined(inv["actual_consumes"]),
            joined(into_addresses(inv)),
            joined(f"{write['address']}:{write['kind']}" for write in inv["writes"]),
            inv["result_sha256"] or NOTHING,
            inv["calculation"]["implementation_sha256"] or NOTHING,
        ])
    for line in table(headers, rows):
        print(line)
    return EXIT_OK


# --- px effects ---------------------------------------------------------------


def effect_summary(entry: dict[str, Any]) -> str:
    """One effect's arguments in one column: the path, or ``key=value`` pairs.

    The path is what a reader looks for first, so ``write_text`` and ``read_text``
    print it bare; every other kind prints its arguments sorted by name, and a
    kind with no arguments (``now_ms``, ``random_seed``) prints ``-``.
    """
    args = entry.get("args") or {}
    if entry.get("kind") in ("write_text", "read_text") and "path" in args:
        return str(args["path"])
    if not args:
        return NOTHING
    return ",".join(f"{name}={json.dumps(args[name], sort_keys=True)}" for name in sorted(args))


def cmd_effects(args: argparse.Namespace) -> int:
    """Every effect the record carries, one line each, in the order they happened.

    The ledger is per invocation and ordered (RECORD.md, "Effects"), so the index
    column is the entry's position in *that* invocation's ledger -- which is
    exactly what a refusal from ``ReplayEffects`` names when a replay diverges.
    A record whose run performed no effects carries no ledgers and prints the
    header alone; nothing is invented for it.
    """
    record = load_record(args.record)
    schema = _schema()
    headers = ["TICK", "ID", "INDEX", "KIND", "ARGS", "DIGEST"]
    rows = []
    for index, name, inv in invocations(record):
        if args.tick is not None and name != args.tick:
            continue
        for position, entry in enumerate(schema.invocation_effects(inv)):
            rows.append([
                str(index),
                inv["id"],
                str(position),
                entry["kind"],
                effect_summary(entry),
                entry["result_sha256"] or NOTHING,
            ])
    for line in table(headers, rows):
        print(line)
    return EXIT_OK


# --- the shell ----------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="px",
        description="A shell over pyto run records: ps, ls, cat, diff, laws, receipts, effects.",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    ps = sub.add_parser("ps", help="one line per invocation: tick, id, calculation, into, state")
    ps.add_argument("record")
    ps.add_argument("--times", action="store_true", help="add the recorded duration in ms")
    ps.set_defaults(run=cmd_ps)

    ls = sub.add_parser("ls", help="every address the record knows, sorted, with its producer")
    ls.add_argument("record")
    ls.add_argument("prefix", nargs="?", default=None, help="only addresses starting with this")
    ls.set_defaults(run=cmd_ls)

    cat = sub.add_parser("cat", help="the value of a produced Part, as canonical JSON")
    cat.add_argument("record")
    cat.add_argument("address")
    cat.set_defaults(run=cmd_cat)

    diff = sub.add_parser("diff", help="two records' differences by invocation; exit 1 when any")
    diff.add_argument("a")
    diff.add_argument("b")
    diff.set_defaults(run=cmd_diff)

    laws = sub.add_parser("laws", help="the node and loop laws over the record; exit 1 when broken")
    laws.add_argument("record")
    laws.add_argument("--times", action="store_true", help="add work and critical path in ms")
    laws.set_defaults(run=cmd_laws)

    receipts = sub.add_parser("receipts", help="receipts as rows: declared vs actual, and digests")
    receipts.add_argument("record")
    receipts.add_argument("--tick", default=None, help="only receipts from the Tick of this name")
    receipts.set_defaults(run=cmd_receipts)

    effects = sub.add_parser("effects", help="one line per recorded effect: kind, args, digest")
    effects.add_argument("record")
    effects.add_argument("--tick", default=None, help="only effects from the Tick of this name")
    effects.set_defaults(run=cmd_effects)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "run", None) is None:
        parser.print_help()
        return EXIT_USAGE
    try:
        return args.run(args)
    except PxError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE
    except BrokenPipeError:  # pragma: no cover - `px ls record | head`
        return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
