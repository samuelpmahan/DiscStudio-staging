"""Day 3: apply the content-addressed materials mechanism (materials.py) to the
Day 1 ablation split, and report the reuse it buys against receipts (the Day 2
seam, PCR.run(pxc, observe=True)).

    python3 experiments/grouped-ablation/run_cached.py
    python3 experiments/grouped-ablation/run_cached.py --out evidence/run-6-cached --force

The Day 1 program itself is run twice, unmodified, exactly as run.py runs it
(build_program, REGISTRY, PCR.run(observe=True)) -- this is "the Day 1 program"
the deliverable names, and its own receipts are the ms-saved oracle below.
Beside those two ordinary runs, the split invocation's own result is separately
resolved three times through materials.material():

  1. a fresh PxC, a fresh MaterialsStore rooted in a fresh temp directory -- MISS
     (nothing on disk yet), so `fn.ablation.split` actually runs once and its
     result is written to the store;
  2. a second fresh PxC sharing the SAME MaterialsStore -- disk HIT: the PxC
     itself never saw the address before, but the store already holds the key,
     so `fn.ablation.split` is not called again;
  3. a genuinely fresh `python3 -I` process, sharing the store only through
     PYTO_MATERIALS_DIR pointed at the same directory -- disk HIT again, which
     is the cross-process half of Reframing 3's thesis ("a Part produced in one
     process ... can be verified and reused in another").

Resolutions 2 and 3 are described above as disk hits because that is what an
intact store does; the ledger never takes that on faith. Each resolution's
`outcome` is derived from what the store's own `{requests, hits, misses,
writes}` counters moved across that one call (`outcome_from_delta` below), and
resolution 3's from the child process's own reported counters -- so a run in
which a `<key>.json` fails to load records "miss+write" for the resolution that
failed and saves nothing, instead of asserting a hit beside a counter that says
otherwise (origin.md:14-17, "dumb receipts and self-verified").

Because seed and n (and therefore `rows`) are identical across all three
resolutions, `materials.material_key(revision=..., source=..., args={"rows":
rows})` is identical every time -- the disk hits above are not a coincidence of
timing, they are the same content-addressed key. `revision` is Day 2's
implementation_sha256 of `fn.ablation.split`, read off the FIRST full program
run's own receipt ({?} CacheInvalidation, research/ULTRACODE-WEEK.md Reframing
2: "the key's `revision` component is a calculation identity; Day 2's
implementation_sha256 is the candidate").

"Milliseconds saved" is never measured by re-running split to see how long the
skipped call would have taken (that would defeat the point of skipping it); it
is read off the sibling full-program run's own `receipts.json` entry for the
'split' invocation -- both program runs' `duration_ms` for 'split' are reported
in reuse-ledger.json, and the smaller of the two is used as a conservative
estimate of the recomputation each cache hit avoided (Reframing 2: "Timings are
synthetic and labelled so"). It is multiplied by `hits_observed` -- how many of
the three resolutions' counters actually recorded a hit -- never by a constant.

hits.py's `hit_ledger` is run over both full program runs too, so the ordinary
within-program reuse (fit/score invoked once per variant, six variants sharing
one Calculation address each) is reported beside the materials reuse -- the two
are different things: hit_ledger counts a Calculation address already
registered inside ONE run; materials.material() counts a Part's VALUE reused
ACROSS runs and processes.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from pyto import PxC  # noqa: E402

import materials  # noqa: E402
from calculations import REGISTRY  # noqa: E402
from features import make_data  # noqa: E402
from hits import hit_ledger  # noqa: E402
from run import _dump, _text  # noqa: E402
from run import run_experiment  # noqa: E402
from second_experiment import resolve_named_out_dir  # noqa: E402

SEED, N = 7, 400  # identical across every resolution on purpose: the point is reuse, not variation
PYTO_ROOT = Path(HERE).resolve().parents[1]  # .../pyto/experiments/grouped-ablation -> .../pyto
CHECKOUT_ROOT = PYTO_ROOT.parent  # the clone or worktree pyto sits in
SPLIT_ADDRESS = "fn.ablation.split"
PYTHON = sys.executable
STRIPPED_ENV_BASE = {"PATH": os.environ.get("PATH", "")}
if os.name == "nt" and os.environ.get("SystemRoot"):
    # Windows cannot start python.exe from an environment block without SystemRoot (see replay.py).
    STRIPPED_ENV_BASE["SystemRoot"] = os.environ["SystemRoot"]
    STRIPPED_ENV_BASE["SystemDrive"] = os.environ.get("SystemDrive", "C:")  # else a literal "%SystemDrive%" folder appears in cwd

CHILD_SNIPPET = textwrap.dedent(
    """\
    import json, sys
    experiment_dir, seed, n, revision = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    sys.path.insert(0, experiment_dir)
    sys.stderr.write(
        "[run_cached-child] sys.path.insert(0, %r)  # this experiment's own modules"
        " (materials, calculations, features); see experiments/CAPTURE.md\\n" % experiment_dir
    )
    import materials
    from calculations import REGISTRY
    from features import make_data
    from pyto import PxC

    rows = make_data(seed, n)
    store = materials.MaterialsStore()  # root from PYTO_MATERIALS_DIR, set by the parent
    pxc = PxC()
    value = materials.material(
        pxc, revision=revision, source={"seed": seed, "n": n},
        calculation=REGISTRY["fn.ablation.split"], args={"rows": rows}, store=store,
    )
    sys.stdout.write(json.dumps({
        "materials_root": str(store.root),
        "counters": store.counters,
        "value": value,
    }))
    sys.exit(0)
    """
)


def full_program_run(seed: int, n: int) -> dict:
    """Run the unmodified Day 1 program once (run.run_experiment) and return it."""
    return run_experiment(seed, n)


def split_args_and_revision(result: dict) -> tuple[dict, str]:
    """The split invocation's own args (the actual rows this run used) and Day 2's
    implementation_sha256 for fn.ablation.split, both read off `result`'s own receipt --
    never recomputed by this module, so the revision is exactly the identity PCR.run
    itself observed (pcr.py:90-93, FrozenCalculation.implementation_sha256)."""
    receipt = result["run"].receipts["split"]
    if receipt.calculation.address != SPLIT_ADDRESS:
        raise AssertionError(f"expected {SPLIT_ADDRESS}, got {receipt.calculation.address}")
    args = {"rows": result["pxc"].get("input.ablation.rows")}
    return args, receipt.calculation.implementation_sha256


def counters_delta(before: dict, after: dict) -> dict:
    """``after - before`` field by field: what ONE resolution moved in the shared
    counters. ``before`` is snapshotted with ``dict(store.counters)`` immediately
    before the call, because ``MaterialsStore.counters`` is mutated in place."""
    return {name: int(after.get(name, 0)) - int(before.get(name, 0)) for name in sorted(set(before) | set(after))}


def outcome_from_delta(delta: dict) -> str:
    """The ledger's ``outcome`` string, READ OFF the counters rather than asserted.

    ``material()`` increments ``hits`` only after ``load_value()`` has returned a
    value (materials.py:236-243), so a truncated or hand-edited ``<key>.json``
    arrives here as a miss and this returns "miss+write" -- the ledger says miss
    for a resolution that missed. Every resolution in this script uses a fresh
    PxC, so an in-PxC hit is impossible and a counted hit is always the disk one.
    """
    hits = delta.get("hits", 0)
    misses = delta.get("misses", 0)
    writes = delta.get("writes", 0)
    if hits > 0:
        return "hit (disk)"
    if misses > 0:
        return "miss+write" if writes > 0 else "miss (no write)"
    return "no counter movement"


def resolve_in_process(pxc: PxC, store: materials.MaterialsStore, args: dict, revision: str) -> object:
    return materials.material(
        pxc, revision=revision, source={"seed": SEED, "n": N},
        calculation=REGISTRY[SPLIT_ADDRESS], args=args, store=store,
    )


def portable(path: str) -> str:
    """An absolute path as a landed receipt can still read it.

    The ledger is committed evidence, so a path that names THIS checkout is a
    receipt pointing at a directory that will not exist after landing -- a
    worktree is thrown away, a fresh clone sits elsewhere, another machine has
    neither. Anything under `pyto/` is therefore recorded relative to the pyto
    root as `<pyto>/...`; anything else inside the checkout -- a sibling `.venv`,
    say -- is recorded relative to the checkout root as `<checkout>/...`, because
    a `<pyto>/../` path climbs back out of the root it is anchored to and names
    no directory a reader can resolve. Anything outside the checkout (a system
    interpreter) is left exactly as it ran: that path is not ours to rewrite.
    """
    if not os.path.isabs(path):
        return path
    # Both spellings, because `.venv/bin/python` is a symlink whose target is
    # the system interpreter: resolving first would hide the checkout path that
    # is the one actually written down.
    for candidate in (Path(os.path.normpath(path)), Path(os.path.realpath(path))):
        for name, root in (("<pyto>", PYTO_ROOT), ("<checkout>", CHECKOUT_ROOT)):
            if candidate == root:
                return name
            if root in candidate.parents:
                return name + "/" + Path(os.path.relpath(candidate, root)).as_posix()
    return path


def resolve_in_fresh_process(store_root: Path, revision: str) -> dict:
    """`python3 -I` from a cwd outside the repo, env stripped to PATH plus
    PYTO_MATERIALS_DIR pointed at `store_root` -- the only channel the child shares
    with the parent. Returns the parsed child report (materials_root, counters, value)."""
    workdir = tempfile.mkdtemp(prefix="run-cached-cwd-")  # outside the repository on purpose
    env = dict(STRIPPED_ENV_BASE)
    env["PYTO_MATERIALS_DIR"] = str(store_root)
    args = [PYTHON, "-I", "-B", "-c", CHILD_SNIPPET, HERE, str(SEED), str(N), revision]
    completed = subprocess.run(args, cwd=workdir, env=env, capture_output=True, text=True, timeout=60)
    if completed.returncode != 0:
        raise RuntimeError(
            f"run_cached.py: fresh-process resolution failed (exit {completed.returncode})\n"
            f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
        )
    report = json.loads(completed.stdout)
    # `args` as recorded, not as executed: see portable() above.
    report["command"] = [portable(arg) for arg in args]
    report["cwd"] = workdir
    report["env"] = env
    report["stderr"] = completed.stderr
    return report


def receipts_summary(result: dict, invocation_id: str) -> dict:
    receipt = result["run"].receipts[invocation_id]
    return {
        "invocation_id": receipt.invocation_id,
        "calculation": receipt.calculation.address,
        "implementation_sha256": receipt.calculation.implementation_sha256,
        "duration_ms": receipt.duration_ms,
        "result_sha256": receipt.result_sha256,
    }


def run_cached(store_root: str | None = None) -> dict:
    """Run everything described in the module docstring; return the full report
    (what evidence/run-6-cached/{counters.json,reuse-ledger.json} are built from)."""
    own_temp_root = store_root is None
    root = Path(store_root) if store_root is not None else Path(tempfile.mkdtemp(prefix="grouped-ablation-materials-"))
    store = materials.MaterialsStore(root=root)

    result_1 = full_program_run(SEED, N)
    args_1, revision = split_args_and_revision(result_1)

    before_a = dict(store.counters)
    pxc_a = PxC()
    value_a = resolve_in_process(pxc_a, store, args_1, revision)  # nothing on disk yet
    delta_a = counters_delta(before_a, store.counters)

    result_2 = full_program_run(SEED, N)
    args_2, revision_2 = split_args_and_revision(result_2)
    if revision_2 != revision:
        raise AssertionError("fn.ablation.split's implementation_sha256 differed between two runs of the same code")

    before_b = dict(store.counters)
    pxc_b = PxC()
    value_b = resolve_in_process(pxc_b, store, args_2, revision)  # fresh PxC, same store
    delta_b = counters_delta(before_b, store.counters)

    if value_a != value_b:
        raise AssertionError("materials.material() returned different values for identical (revision, source, args)")
    if value_a != result_1["run"].results["split"]:
        raise AssertionError("materials.material()'s value differs from the PCR's own computed split result")

    child_report = resolve_in_fresh_process(store.root, revision)
    if child_report["value"] != value_a:
        raise AssertionError("fresh-process materials.material() returned a different value than the in-process resolutions")

    receipt_1 = receipts_summary(result_1, "split")
    receipt_2 = receipts_summary(result_2, "split")
    baseline_ms = min(receipt_1["duration_ms"], receipt_2["duration_ms"])

    ledger_1 = hit_ledger(result_1["run"])
    ledger_2 = hit_ledger(result_2["run"])

    # The child builds its own MaterialsStore with fresh (all-zero) counters, so the
    # counters it reports back ARE its delta for its single resolution.
    child_counters = {name: int(count) for name, count in dict(child_report["counters"]).items()}

    counters = dict(store.counters)  # {requests, hits, misses, writes} after the two in-process resolutions
    resolutions = [
        {
            "resolution": 1, "where": "in-process, fresh PxC, empty store",
            "outcome": outcome_from_delta(delta_a), "counters_delta": delta_a,
        },
        {
            "resolution": 2, "where": "in-process, second fresh PxC, same store",
            "outcome": outcome_from_delta(delta_b), "counters_delta": delta_b,
        },
        {
            "resolution": 3, "where": "fresh python3 -I process, PYTO_MATERIALS_DIR shared",
            "outcome": outcome_from_delta(child_counters), "counters_delta": child_counters,
            "child_counters": child_counters,
            "child_materials_root": child_report["materials_root"],
            "command": child_report["command"], "cwd": child_report["cwd"],
        },
    ]
    hits_observed = sum(1 for row in resolutions if row["counters_delta"].get("hits", 0) > 0)

    reuse_ledger = {
        "revision": revision,
        "key": materials.material_key(revision=revision, source={"seed": SEED, "n": N}, args=args_1),
        "seed": SEED,
        "n": N,
        "materials_root_process": str(store.root),
        "resolutions": resolutions,
        "in_process_counters": counters,
        "split_receipts": {"program_run_1": receipt_1, "program_run_2": receipt_2},
        "ms_saved_per_hit": baseline_ms,
        "ms_saved_note": (
            "Read from the sibling full-program run's own receipts.json duration_ms for "
            "'split' (the smaller of the two), never by re-running split to time the skipped "
            "call -- that would defeat the point of the cache hit. Synthetic-fixture wall "
            "time, labelled so (research/ULTRACODE-WEEK.md Reframing 2). ms_saved_total is "
            "this figure times hits_observed -- the number of the three resolutions whose "
            "own counters recorded a hit -- never times a constant, so a run in which a disk "
            "load fails reports 0 saved rather than hits that did not happen."
        ),
        "hits_observed": hits_observed,
        "ms_saved_total": round(baseline_ms * hits_observed, 3),
        "hit_ledger_program_run_1": ledger_1,
        "hit_ledger_program_run_2": ledger_2,
    }
    if own_temp_root:
        reuse_ledger["materials_root_process_is_temp"] = True

    return {"counters": counters, "reuse_ledger": reuse_ledger}


def interpretation_markdown(report: dict) -> str:
    counters = report["counters"]
    ledger = report["reuse_ledger"]
    lines = [
        "# run-6-cached: content-addressed materials over the Day 1 ablation split",
        "",
        "Ported from ChainSpot's `createMatrixMaterials` "
        "(pyto/reference/lab/chainspot-matrix/matrix/materials.ts:263-317), experiment-local "
        "(`materials.py`), applied to `fn.ablation.split`.",
        "",
        f"revision (fn.ablation.split's implementation_sha256, Day 2's receipts seam): "
        f"`{ledger['revision']}`",
        f"content-addressed key: `{ledger['key']}`",
        "",
        "## In-process counters (two fresh PxCs sharing one MaterialsStore)",
        "",
        f"requests={counters['requests']} hits={counters['hits']} misses={counters['misses']} "
        f"writes={counters['writes']}",
        "",
        "| resolution | where | outcome | counters delta |",
        "|---|---|---|---|",
    ]
    for row in ledger["resolutions"]:
        delta = row["counters_delta"]
        rendered = " ".join(f"{name}={delta[name]:+d}" for name in ("requests", "hits", "misses", "writes") if name in delta)
        lines.append(f"| {row['resolution']} | {row['where']} | {row['outcome']} | {rendered} |")
    lines += [
        "",
        "## Milliseconds saved",
        "",
        f"{ledger['ms_saved_note']}",
        f"split duration_ms, program run 1: {ledger['split_receipts']['program_run_1']['duration_ms']}; "
        f"program run 2: {ledger['split_receipts']['program_run_2']['duration_ms']}.",
        f"ms saved per cache hit (conservative, the smaller of the two): {ledger['ms_saved_per_hit']}.",
        f"Resolutions whose own counters recorded a hit (derived, never asserted): "
        f"{ledger['hits_observed']} of {len(ledger['resolutions'])} -> ms saved this run: "
        f"{ledger['ms_saved_total']}.",
        "",
        "## Ordinary within-program reuse (hits.py, for comparison)",
        "",
        "This is a different thing from the materials cache above: hit_ledger counts a "
        "Calculation address already registered earlier in the SAME run (e.g. `fn.ablation.fit` "
        "invoked once per variant); the materials cache counts one Part's VALUE reused ACROSS "
        "runs and processes.",
        "",
        f"program run 1: {ledger['hit_ledger_program_run_1']['counters']}",
        f"program run 2: {ledger['hit_ledger_program_run_2']['counters']}",
        "",
        "## What each cannot express",
        "",
        "The materials cache is silent about *why* a value is reused (no perceptual matching, "
        "no course identity -- ULTRACODE-WEEK.md Reframing 4); it only knows that "
        "`sha(canonical({revision, source, args}))` repeats. hits.py's Calculation ledger is "
        "silent about VALUES entirely -- two invocations of the same address with different "
        "args are equally 'already registered' even though they compute different things; it is "
        "a registration ledger, not a content-addressed one.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=None)
    parser.add_argument("--force", action="store_true")
    ns = parser.parse_args(argv)
    try:
        out_dir = resolve_named_out_dir(ns.out, "evidence/run-6-cached", ns.force)
    except FileExistsError as error:
        print(f"run_cached.py: refusing to overwrite evidence: {error}", file=sys.stderr)
        return 2

    report = run_cached()
    os.makedirs(out_dir, exist_ok=True)
    _dump(os.path.join(out_dir, "counters.json"), report["counters"])
    _dump(os.path.join(out_dir, "reuse-ledger.json"), report["reuse_ledger"])
    _text(os.path.join(out_dir, "interpretation.md"), interpretation_markdown(report))

    print("counters:", report["counters"])
    print("ms saved this run:", report["reuse_ledger"]["ms_saved_total"], "over",
          report["reuse_ledger"]["hits_observed"], "observed hit(s)")
    print("wrote", out_dir, sorted(os.listdir(out_dir)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
