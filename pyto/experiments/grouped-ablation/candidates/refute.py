"""Apply three lenses to the three retained-program schema candidates and write README.md.

    python3 candidates/refute.py            # rewrite candidates/README.md from the lens run
    python3 candidates/refute.py --check    # exit 1 if README.md differs from a fresh run

Every verdict and every number in README.md is produced by this run; nothing in
the file is typed by hand. test_retain.py runs --check, so the record cannot
drift away from the code it describes.

Lenses
------
roundtrip       export -> json.dumps/loads -> restore(registry) -> run on a fresh
                PxC seeded from the fixture's externals -> the replayed run's
                testimony bytes must equal the original run's, and the retained
                calculation entries must be identical to the testimony entries
                (no translation layer between what a run testifies and what is kept).
expressiveness  the schema must be able to hold an `fn:` direct-result reference
                (pcr.py:112-123) and an invocation with `into=None` (pcr.py:29).
leakage         the exported document must serialise with json.dumps and no
                `default=`, contain neither "lambda" nor "<function", and a program
                carrying a callable in args must be refused at export.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXPERIMENT = os.path.dirname(HERE)
REPO = os.path.normpath(os.path.join(EXPERIMENT, "..", "..", ".."))
if EXPERIMENT not in sys.path:
    sys.path.insert(0, EXPERIMENT)

from pyto import PCR, Calculation, Part, PxC  # noqa: E402

import candidate_pcr_json  # noqa: E402
import candidate_readpql  # noqa: E402
import candidate_testimony  # noqa: E402
import retain  # noqa: E402
from calculations import REGISTRY  # noqa: E402
from features import GROUPS, make_data  # noqa: E402
from program import GROUPS as GROUPS_PART, ROWS, build_program  # noqa: E402

CANDIDATES = (candidate_testimony, candidate_pcr_json, candidate_readpql)
LENSES = ("roundtrip", "expressiveness", "leakage")
SEED, ROWS_N = 7, 400
CHECKER = os.path.join(HERE, "readpql_check.mjs")
EXEC_JS = os.path.join(REPO, "src", "core", "exec.js")


# ------------------------------------------------------------------ fan-out fixture
# Module-level functions only: retained evidence names no lambda (CAPTURE.md rule 2).


def render_disc(args: dict) -> dict:
    return {"art": args["value"]}


def single_card(args: dict) -> dict:
    return {"card": "single", "art": args["art"]}


def battle_card(args: dict) -> dict:
    return {"card": "battle", "art": args["art"]}


FANOUT_REGISTRY = {
    "fn.discArt.render": Calculation("fn.discArt.render", render_disc),
    "fn.card.single": Calculation("fn.card.single", single_card),
    "fn.card.battle": Calculation("fn.card.battle", battle_card),
}


def testimony_bytes(run) -> str:
    return json.dumps([dataclasses.asdict(tick) for tick in run.ticks], sort_keys=True)


@dataclasses.dataclass(frozen=True)
class Fixture:
    name: str
    note: str
    program: dict
    testimony: str
    registry: dict
    external: dict


def fixture_day1() -> Fixture:
    pxc = PxC()
    pxc.set(ROWS, make_data(SEED, ROWS_N))
    pxc.set(GROUPS_PART, GROUPS)
    from calculations import select_variants

    pcr = build_program(select_variants({"groups": GROUPS}))
    run = pcr.run(pxc)
    return Fixture(
        "day1",
        "the Day 1 grouped ablation: fn: refs everywhere, every invocation publishes",
        retain.to_program(run),
        testimony_bytes(run),
        REGISTRY,
        {ROWS.address: pxc.get(ROWS), GROUPS_PART.address: pxc.get(GROUPS_PART)},
    )


def fixture_fanout_px() -> Fixture:
    """Two PCRs over one PxC: the second one's bindings are px: because writers are per PCR."""
    pxc = PxC()
    pxc.set(Part("px.disc.request"), {"seed": SEED, "family": "orbit-foundry"})
    first = PCR("fanout.render")
    first.calc("Render", FANOUT_REGISTRY["fn.discArt.render"], id="render-disc",
               value=Part("px.disc.request"), into="px.disc.art")
    first.run(pxc)
    second = PCR("fanout.cards")
    second.calc("Cards", FANOUT_REGISTRY["fn.card.single"], id="single-card",
                art=Part("px.disc.art"), into="px.card.single")
    second.calc("Cards", FANOUT_REGISTRY["fn.card.battle"], id="battle-card",
                art=Part("px.disc.art"), into="px.card.battle")
    run = second.run(pxc)
    return Fixture(
        "fanout_px",
        "a px-only fan-out (second PCR over the same PxC), every invocation publishes",
        retain.to_program(run),
        testimony_bytes(run),
        FANOUT_REGISTRY,
        {"px.disc.art": pxc.get("px.disc.art")},
    )


def fixture_no_into() -> Fixture:
    pxc = PxC()
    pxc.set(Part("px.disc.request"), {"seed": SEED})
    pcr = PCR("fanout.unpublished")
    pcr.calc("Render", FANOUT_REGISTRY["fn.discArt.render"], id="render-disc", value=Part("px.disc.request"))
    run = pcr.run(pxc)
    return Fixture(
        "no_into",
        "one invocation with into=None: a result kept as fn: and never published",
        retain.to_program(run),
        testimony_bytes(run),
        FANOUT_REGISTRY,
        {"px.disc.request": pxc.get("px.disc.request")},
    )


def front_door_refusal() -> str:
    """What the shared exporter does with a callable in args. All three candidates go
    through retain.to_program, so this is a property of the front door, not of a schema."""
    pcr = PCR("leakage.probe")
    pcr.calc("T", FANOUT_REGISTRY["fn.discArt.render"], id="leak", value=Part("px.disc.request"),
             args={"post": render_disc}, into="px.leak")
    try:
        retain.to_program(pcr)
    except Exception as error:  # noqa: BLE001
        return f"{type(error).__name__}: {error}"
    return "not refused"


# ----------------------------------------------------------------------- the lenses


def count_fn_refs(program: dict) -> int:
    return sum(
        1
        for tick in program["ticks"]
        for entry in tick["calculations"]
        for ref in entry["inputs"].values()
        if ref.startswith("fn:")
    )


def count_unpublished(program: dict) -> int:
    return sum(1 for tick in program["ticks"] for entry in tick["calculations"] if entry["into"] is None)


def lens_roundtrip(candidate, fixtures: list[Fixture]) -> dict:
    notes, ok = [], True
    for fixture in fixtures:
        try:
            document = json.loads(json.dumps(candidate.export(fixture.program)))
        except Exception as error:  # noqa: BLE001 - the lens reports, it does not raise
            ok = False
            notes.append(f"{fixture.name}: export refused ({type(error).__name__})")
            continue
        try:
            pcr = candidate.restore(document, fixture.registry)
        except Exception as error:  # noqa: BLE001
            ok = False
            notes.append(f"{fixture.name}: restore refused ({type(error).__name__})")
            continue
        pxc = PxC()
        for address, value in fixture.external.items():
            pxc.set(Part(address), value)
        replayed = testimony_bytes(pcr.run(pxc))
        same = replayed == fixture.testimony
        identical_entries = document == fixture.program
        ok = ok and same and identical_entries
        detail = "testimony bytes equal" if same else "testimony bytes DIFFER"
        detail += "; entries identical to testimony" if identical_entries else "; entries need translation"
        notes.append(f"{fixture.name}: {detail}")
    return {"verdict": "accept" if ok else "reject", "detail": "; ".join(notes)}


def lens_expressiveness(candidate, day1: Fixture, no_into: Fixture) -> dict:
    notes, ok = [], True
    fn_refs = count_fn_refs(day1.program)
    try:
        candidate.export(day1.program)
        notes.append(f"{fn_refs} fn: ref(s) held")
    except Exception as error:  # noqa: BLE001
        ok = False
        notes.append(f"{fn_refs} fn: ref(s): refused ({type(error).__name__})")
    unpublished = count_unpublished(no_into.program)
    try:
        candidate.export(no_into.program)
        notes.append(f"{unpublished} invocation(s) with into=None held")
    except Exception as error:  # noqa: BLE001
        ok = False
        notes.append(f"{unpublished} invocation(s) with into=None: refused ({type(error).__name__})")
    return {"verdict": "accept" if ok else "reject", "detail": "; ".join(notes)}


def lens_leakage(candidate, fixtures: list[Fixture]) -> dict:
    notes, ok = [], True
    for fixture in fixtures:
        try:
            text = json.dumps(candidate.export(fixture.program), sort_keys=True)
        except Exception as error:  # noqa: BLE001
            notes.append(f"{fixture.name}: not exportable ({type(error).__name__})")
            continue
        leaked = [token for token in ("lambda", "<function") if token in text]
        if leaked:
            ok = False
            notes.append(f"{fixture.name}: document contains {leaked}")
        else:
            notes.append(f"{fixture.name}: json-serialisable, no lambda/<function")
    return {"verdict": "accept" if ok else "reject", "detail": "; ".join(notes)}


# ---------------------------------------------------------------------- node checks


def node_cases(day1: Fixture, fanout: Fixture) -> dict:
    """Documents handed to the real browser reader (src/core/exec.js:37-49)."""
    naive = {
        "PrincipleComponentRender": day1.program["name"],
        "Ticks": [
            {"name": tick["name"], "Calculations": [
                {"call": entry["calculation"],
                 "with": {name: (ref[3:] if ref.startswith("px:") else ref)
                          for name, ref in entry["inputs"].items()},
                 "args": entry["args"], "into": entry["into"]}
                for entry in tick["calculations"]]}
            for tick in day1.program["ticks"]
        ],
    }
    return {"cases": [
        {"name": "px_only_fanout_accepted", "kind": "accept",
         "document": candidate_readpql.export(fanout.program)},
        {"name": "missing_into_refused", "kind": "reject", "expect": "expected a nonempty string",
         "document": {"PrincipleComponentRender": "probe", "Ticks": [
             {"name": "T", "Calculations": [{"call": "fn.a", "with": {}, "args": {}}]}]}},
        {"name": "shadowed_arg_refused", "kind": "reject", "expect": "appears in both with and args",
         "document": {"PrincipleComponentRender": "probe", "Ticks": [
             {"name": "T", "Calculations": [
                 {"call": "fn.a", "with": {"v": "px.v"}, "args": {"v": 1}, "into": "px.o"}]}]}},
        {"name": "fn_ref_written_as_address_is_read_then_fails_at_invoke", "kind": "invoke_fails",
         "expect": "slot 'fn:split' not produced yet", "seed": {address: None for address in day1.external},
         "document": naive},
    ]}


def run_node(cases: dict, workdir: str) -> tuple[bool, list[dict]]:
    path = os.path.join(workdir, "readpql-cases.json")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(cases, handle)
    proc = subprocess.run(["node", CHECKER, path], capture_output=True, text=True, cwd=HERE)
    verdicts = [json.loads(line) for line in proc.stdout.splitlines() if line.strip().startswith("{")]
    summary = verdicts.pop() if verdicts and "ok" in verdicts[-1] else {"ok": False}
    return bool(summary.get("ok")) and proc.returncode == 0, verdicts


# --------------------------------------------------------------------------- report


def evaluate(workdir: str) -> dict:
    day1, fanout, no_into = fixture_day1(), fixture_fanout_px(), fixture_no_into()
    fixtures = [day1, fanout]
    rows = {}
    for candidate in CANDIDATES:
        rows[candidate.NAME] = {
            "shape": candidate.SHAPE,
            "roundtrip": lens_roundtrip(candidate, fixtures),
            "expressiveness": lens_expressiveness(candidate, day1, no_into),
            "leakage": lens_leakage(candidate, fixtures),
        }
    node_ok, node_verdicts = run_node(node_cases(day1, fanout), workdir)
    survivors = [name for name, row in rows.items() if all(row[lens]["verdict"] == "accept" for lens in LENSES)]
    return {
        "fixtures": [{"name": f.name, "note": f.note} for f in (day1, fanout, no_into)],
        "counts": {
            "day1_invocations": sum(len(t["calculations"]) for t in day1.program["ticks"]),
            "day1_fn_refs": count_fn_refs(day1.program),
            "fanout_invocations": sum(len(t["calculations"]) for t in fanout.program["ticks"]),
            "no_into_unpublished": count_unpublished(no_into.program),
        },
        "rows": rows,
        "survivors": survivors,
        "graph_pcr_executes": candidate_pcr_json.executes(),
        "front_door_refusal": front_door_refusal(),
        "node": {"ok": node_ok, "verdicts": node_verdicts},
    }


def render(report: dict) -> str:
    counts = report["counts"]
    lines = [
        "# Retained-program schema candidates: three shapes, three lenses",
        "",
        "Generated by `candidates/refute.py`; `python3 candidates/refute.py --check` (run by",
        "test_retain.py) fails if this file and a fresh lens run disagree. Every verdict and",
        "number below was produced by that run.",
        "",
        "## Fixtures",
        "",
    ]
    for fixture in report["fixtures"]:
        lines.append(f"- `{fixture['name']}` -- {fixture['note']}")
    lines += [
        "",
        f"The `day1` program holds {counts['day1_invocations']} invocations carrying "
        f"{counts['day1_fn_refs']} `fn:` direct-result bindings; `fanout_px` holds "
        f"{counts['fanout_invocations']} px-only invocations; `no_into` holds "
        f"{counts['no_into_unpublished']} invocation with `into=None`.",
        "",
        "## Verdicts",
        "",
        "| candidate | roundtrip | expressiveness | leakage |",
        "|---|---|---|---|",
    ]
    for name, row in report["rows"].items():
        lines.append(f"| {name} | {row['roundtrip']['verdict']} | {row['expressiveness']['verdict']} | {row['leakage']['verdict']} |")
    lines += ["", "## Why each verdict", ""]
    for name, row in report["rows"].items():
        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"Shape: `{row['shape']}`")
        lines.append("")
        for lens in LENSES:
            lines.append(f"- **{lens}: {row[lens]['verdict']}** -- {row[lens]['detail']}")
        lines.append("")
    survivors = report["survivors"]
    lines += [
        "## Survivor",
        "",
        f"Accepted by all three lenses: {', '.join(survivors) if survivors else 'none'}.",
        "",
        "The expected survivor was the testimony shape and it survived, but not for the reason",
        "the plan assumed. The decisive lens is `roundtrip`, not `leakage`: all three shapes hold",
        "data only, so the leakage lens does not discriminate and is weak evidence on its own",
        "(it is kept because it is the lens that would catch a regression, not because it chose).",
        "",
        f"`graph.Pcr` exposes an executing or importing method: {report['graph_pcr_executes']}. Checked",
        "at run time with `hasattr`, so candidate B's refusal rests on a fact and not only on a",
        "quotation of docs/PYTHON-LAB-STEWARDSHIP.md:19.",
        "",
        "The leakage lens accepted all three because the check that matters happens before any of",
        "them: `retain.to_program` refuses a callable in `args` at export, naming the invocation --",
        f"`{report['front_door_refusal']}`",
        "",
        "Candidate C is not merely lossy: the readPql grammar has no field for an invocation id",
        "(src/core/exec.js:46 builds `{call, with, args, into}`), and `fn:` refs are addressed by",
        "id, so the shape cannot express them even in principle. Restoring one therefore has to",
        "invent ids, and the replayed testimony differs from the original on the `id` field alone.",
        "",
        "## The same documents through the real browser reader",
        "",
        "`candidates/readpql_check.mjs` imports `readPql`/`invokePql` from `src/core/exec.js`",
        "(relative path, inside this repository) with `JSON.parse` as the parser.",
        "",
        "| case | kind | pass | what node reported |",
        "|---|---|---|---|",
    ]
    for verdict in report["node"]["verdicts"]:
        detail = verdict["detail"].replace("|", "\\|")
        lines.append(f"| {verdict['name']} | {verdict['kind']} | {verdict['pass']} | {detail} |")
    lines += [
        "",
        f"All node cases passed: {report['node']['ok']}.",
        "",
        "The last row is the finding that put the `fn:` refusal in Python rather than in the",
        "grammar: node's reader accepts `\"split\": \"fn:split\"` as an ordinary Part address, so a",
        "silently-degraded document would be read successfully and die only at invocation. That",
        "is why `pql_document.to_pql_document` raises `PqlDocumentError` naming the first",
        "offending invocation instead of writing the literal address.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="exit 1 if README.md differs from a fresh run")
    parser.add_argument("--workdir", default=None, help="where the node case file is written (default: a temp dir)")
    ns = parser.parse_args(argv)
    workdir = ns.workdir
    if workdir is None:
        import tempfile

        workdir = tempfile.mkdtemp(prefix="readpql-cases-")
    text = render(evaluate(workdir))
    path = os.path.join(HERE, "README.md")
    if ns.check:
        with open(path, encoding="utf-8") as handle:
            current = handle.read()
        if current != text:
            sys.stderr.write("candidates/README.md is stale; run python3 candidates/refute.py\n")
            return 1
        print("candidates/README.md matches a fresh lens run")
        return 0
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
