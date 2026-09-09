"""Day 5: the cross-project hit. Runs the shelf domain (program.py) and, in the
same process, resolves the ablation domain's seed-7, n=400 split through the SAME
content-addressed materials store (pyto/experiments/grouped-ablation/materials.py)
the ablation domain (pyto/experiments/grouped-ablation) already wrote to -- the
Day 5 answer to `{?} CrossProjectReuse` (pyto/questions.md): "Can a second domain
get a verified hit on material the first produced?"

    python3 experiments/cross-project/run.py
    python3 experiments/cross-project/run.py --out evidence/run-1 --force

Step A -- ensure the ablation material exists. `program.SHARED_REVISION` and
`program.shared_split_args()` are computed the SAME way the ablation domain's own
receipts recorded them (program.py imports `pyto.pcr`'s own digest function and
grouped-ablation's `features.make_data`, so there is no independent recomputation
to drift). The shared store is checked for that key first; only if it is not
already present is the ablation domain's OWN `fn.ablation.split` Calculation
(imported from grouped-ablation/calculations.py, never reimplemented) called
through `materials.material()` to produce and write it -- recorded in the ledger
as "seeded by domain A".

Step B -- run the shelf program (program.build_program) for its own testimony,
then resolve three materials through ONE shared MaterialsStore, in this order:
the ablation split first (must be a hit, zero writes), then the shelf's own
histogram and pick-to-carry (each a miss + write the first time anything under
`fn.shelf.*` is stored). Counters after the split resolution alone already show
hits >= 1, before either shelf write -- asserted here, not only reported.

Step C -- verify the hit's digest against the ablation experiment's own committed
evidence: pyto/experiments/grouped-ablation/evidence/run-6-cached/reuse-ledger.json
("split_receipts"."program_run_1"."result_sha256"), the same figure
pyto/experiments/grouped-ablation/evidence/run-1/receipts.json records for the
"split" invocation's `result_sha256`.

Files written to --out (mirrors run_cached.py: no --out is a fresh temp dir, never
the tracked evidence/run-1; an existing non-empty --out is refused unless --force):
counters.json, cross-project-ledger.json, interpretation.md.

Without an explicit --store-root, the shared store lives in a fresh temporary
directory for the lifetime of one `run_cross_project()` call (own_temp_root=True
in the ledger) -- never the real per-user `~/.pyto/materials` -- so a bare
verification run, and the committed evidence/run-1 itself, is reproducible and
self-contained rather than depending on whatever a prior run happened to leave on
this machine.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

GROUPED_ABLATION = os.path.normpath(os.path.join(HERE, "..", "grouped-ablation"))
if GROUPED_ABLATION not in sys.path:
    # Appended, never inserted at 0: HERE must stay ahead of GROUPED_ABLATION so this
    # module's own `import program` resolves to cross-project's own program.py, not
    # grouped-ablation's file of the same name. See program.py's matching comment.
    sys.path.append(GROUPED_ABLATION)

from pyto import PxC  # noqa: E402
from pyto.pcr import _result_sha256  # noqa: E402  -- the exact digest formula the ablation domain's own
# receipts used (pcr.py:362); imported, not reimplemented, so Step C's comparison is apples to apples.

import materials  # noqa: E402  -- grouped-ablation/materials.py: the ONE shared store implementation
import program  # noqa: E402  -- this domain's own (cross-project/program.py)

ABLATION_EVIDENCE_CITATIONS = (
    "pyto/experiments/grouped-ablation/evidence/run-6-cached/reuse-ledger.json",
    "pyto/experiments/grouped-ablation/evidence/run-1/receipts.json",
)


def _committed_split_digest() -> str:
    """The digest fn.ablation.split committed for seed=7, n=400 -- read straight off
    grouped-ablation's own committed evidence, never recomputed independently here.
    Cross-checked against evidence/run-1/receipts.json's "split" entry (the second
    citation) by test_cross_project.py::DigestVerification."""
    path = os.path.join(GROUPED_ABLATION, "evidence", "run-6-cached", "reuse-ledger.json")
    with open(path, "r", encoding="utf-8") as fh:
        ledger = json.load(fh)
    return ledger["split_receipts"]["program_run_1"]["result_sha256"]


def counters_delta(before: dict, after: dict) -> dict:
    """``after - before`` field by field: what ONE resolution moved in the shared
    counters (materials.MaterialsStore.counters is mutated in place)."""
    return {name: int(after.get(name, 0)) - int(before.get(name, 0)) for name in sorted(set(before) | set(after))}


def run_cross_project(store_root: str | None = None, bag_seed: int = 1, bag_n: int = 12) -> dict:
    """Steps A, B and C from the module docstring; returns everything the evidence
    writer needs. Raises AssertionError if the shared resolution is not a hit, if
    it wrote to the store, or if its digest disagrees with the ablation domain's
    committed evidence -- a cross-project hit that fails silently is not a hit."""
    own_temp_root = store_root is None
    root = Path(store_root) if store_root is not None else Path(tempfile.mkdtemp(prefix="cross-project-materials-"))
    store = materials.MaterialsStore(root=root)

    # -------------------------------------------------------------- Step A
    split_args = program.shared_split_args()
    shared_key = materials.material_key(revision=program.SHARED_REVISION, source=program.SHARED_SOURCE, args=split_args)
    already_present = store.has_value(shared_key)
    seeded_by_domain_a = False
    if not already_present:
        materials.material(
            PxC(), revision=program.SHARED_REVISION, source=program.SHARED_SOURCE,
            calculation=program.SHARED_CALCULATION, args=split_args, store=store,
        )
        seeded_by_domain_a = True

    # -------------------------------------------------------------- Step B
    bag = program.make_bag(bag_seed, bag_n)
    pcr = program.build_program(bag)
    pxc = PxC()
    pxc.set(program.BAG, bag)
    run = pcr.run(pxc, observe=True)

    resolutions = []

    # step_b_start is the baseline for "before any shelf write": Step A may itself have
    # written once already (seeding the ablation material on a fresh store), and that
    # write is domain A's, not the shelf's -- so "before any shelf write" is measured
    # from here, not from the store's lifetime start.
    step_b_start = dict(store.counters)
    shared_value = materials.material(
        PxC(), revision=program.SHARED_REVISION, source=program.SHARED_SOURCE,
        calculation=program.SHARED_CALCULATION, args=split_args, store=store,
    )
    delta = counters_delta(step_b_start, store.counters)
    resolutions.append({"material": "fn.ablation.split (shared)", "counters_delta": delta})
    if delta.get("hits", 0) < 1:
        raise AssertionError(
            f"cross-project run: the shared split was not a hit (delta={delta}); "
            "the store did not already hold the ablation material after Step A"
        )
    if delta.get("writes", 0) != 0:
        raise AssertionError(f"cross-project run: the shared split's resolution wrote to the store (delta={delta})")
    hits_before_any_shelf_write = counters_delta(step_b_start, store.counters)["hits"]
    writes_before_any_shelf_write = counters_delta(step_b_start, store.counters)["writes"]

    before = dict(store.counters)
    histogram_value = materials.material(
        PxC(), revision=program.HISTOGRAM_REVISION, source={"domain": "shelf", "bag_seed": bag_seed, "bag_n": bag_n},
        calculation=program.REGISTRY["fn.shelf.stabilityHistogram"], args={"bag": bag}, store=store,
    )
    resolutions.append(
        {"material": "fn.shelf.stabilityHistogram (own)", "counters_delta": counters_delta(before, store.counters)}
    )

    before = dict(store.counters)
    carry_value = materials.material(
        PxC(), revision=program.CARRY_REVISION, source={"domain": "shelf", "bag_seed": bag_seed, "bag_n": bag_n},
        calculation=program.REGISTRY["fn.shelf.pickToCarry"], args={"bag": bag}, store=store,
    )
    resolutions.append({"material": "fn.shelf.pickToCarry (own)", "counters_delta": counters_delta(before, store.counters)})

    # -------------------------------------------------------------- Step C
    committed_digest = _committed_split_digest()
    actual_digest = _result_sha256(shared_value)
    digest_equal = actual_digest == committed_digest
    if not digest_equal:
        raise AssertionError(
            f"cross-project run: the shared split's digest ({actual_digest}) does not match "
            f"the ablation experiment's committed digest ({committed_digest}); see "
            f"{ABLATION_EVIDENCE_CITATIONS[0]}"
        )

    ledger = {
        "shared_material": {
            "calculation": program.SHARED_CALCULATION.address,
            "key": shared_key,
            "revision": program.SHARED_REVISION,
            "source": program.SHARED_SOURCE,
            "producer": "grouped-ablation (domain A)",
            "consumer": "cross-project/shelf (domain B)",
            "seeded_by_domain_a": seeded_by_domain_a,
            "digest_this_run": actual_digest,
            "digest_committed_by_domain_a": committed_digest,
            "digest_equal": digest_equal,
            "digest_committed_citation": ABLATION_EVIDENCE_CITATIONS[0],
            "digest_committed_cross_check_citation": ABLATION_EVIDENCE_CITATIONS[1],
        },
        "resolutions": resolutions,
        "hits_before_any_shelf_write": hits_before_any_shelf_write,
        "writes_before_any_shelf_write": writes_before_any_shelf_write,
        "final_counters": dict(store.counters),
        "shelf_testimony_ticks": [tick.name for tick in run.ticks],
        "bag_seed": bag_seed,
        "bag_n": bag_n,
    }
    if own_temp_root:
        ledger["materials_root_process_is_temp"] = True

    return {
        "counters": dict(store.counters),
        "ledger": ledger,
        "store_root": str(store.root),
        "run": run,
        "pxc": pxc,
        "values": {"split": shared_value, "histogram": histogram_value, "carry": carry_value},
    }


def interpretation_markdown(report: dict) -> str:
    ledger = report["ledger"]
    shared = ledger["shared_material"]
    lines = [
        "# Cross-project hit: the shelf domain reuses the ablation domain's split",
        "",
        "The shelf domain (`px.shelf.*` / `fn.shelf.*`, this experiment) shared exactly one "
        "material with the ablation domain (`pyto/experiments/grouped-ablation`): the seed-7, "
        "n=400 split of `features.make_data`'s synthetic rows, resolved through the same "
        "content-addressed materials store both domains read "
        f"(`materials.material_key(revision, source, args)`, key `{shared['key']}`).",
        "",
        "Everything else -- the disc bag fixture, the stability histogram, and which discs to "
        "carry -- is the shelf domain's own: neither `px.shelf.*` nor `fn.shelf.*` exists anywhere "
        "in the ablation domain, and the shelf's own materials-store resolutions were misses (the "
        "first time anything under `fn.shelf.*` was ever stored) that then wrote this run's own "
        "new material.",
        "",
        "A hit here means the shelf domain asked the shared store for "
        "`sha(canonical({revision, source, args}))` of the ablation split and the store answered "
        "without calling `fn.ablation.split` again; the returned value's own sha256 digest "
        f"(`{shared['digest_this_run']}`) is checked byte for byte against the digest the ablation "
        f"experiment already committed ({shared['digest_committed_citation']}), not merely asserted "
        "equal by construction.",
        "",
        "The hit is not evidence that the two domains agree on what a disc or a feature row means "
        "-- it is evidence only that the same (revision, source, args) triple, computed the same "
        "way by two different programs, addresses the same stored bytes; the shelf domain never "
        "calls into the ablation domain's Calculations for anything except this one imported "
        "Calculation object, and never runs the ablation domain's own program.",
        "",
        "What would break it: a change to `fn.ablation.split`'s source (a different "
        "`implementation_sha256` revision), a change to `make_data`'s output for seed 7 / n 400 "
        "(a different args digest), or pointing `PYTO_MATERIALS_DIR` somewhere the shelf run "
        "cannot see -- each turns the resolution from a hit into a fresh miss, which is exactly "
        "what `test_cross_project.py`'s negative test demonstrates by mutating one of the shelf "
        "domain's OWN revision strings instead (the shared revision is the ablation domain's to "
        "change, not this experiment's).",
        "",
        "## Counters",
        "",
        f"final: {report['counters']}",
        f"hits before any shelf write: {ledger['hits_before_any_shelf_write']}; "
        f"writes before any shelf write: {ledger['writes_before_any_shelf_write']}",
        "",
        "| material | counters delta |",
        "|---|---|",
    ]
    for row in ledger["resolutions"]:
        delta = row["counters_delta"]
        rendered = " ".join(f"{name}={delta[name]:+d}" for name in ("requests", "hits", "misses", "writes") if name in delta)
        lines.append(f"| {row['material']} | {rendered} |")
    lines += [
        "",
        f"seeded by domain A this run: {shared['seeded_by_domain_a']}",
        f"digest equal to the ablation experiment's committed evidence: {shared['digest_equal']}",
        "",
    ]
    return "\n".join(lines)


def resolve_out_dir(out: str | None, force: bool) -> str:
    """Mirrors run_cached.py: no --out is a fresh temp dir; an existing non-empty
    --out is refused unless --force."""
    if out is None:
        return tempfile.mkdtemp(prefix="cross-project-run-")
    out_dir = out if os.path.isabs(out) else os.path.join(HERE, out)
    if os.path.isdir(out_dir) and os.listdir(out_dir) and not force:
        raise FileExistsError(f"{out_dir} already holds evidence; pass --force to overwrite it")
    return out_dir


def _dump(path: str, payload) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=None)
    parser.add_argument("--force", action="store_true")
    ns = parser.parse_args(argv)
    try:
        out_dir = resolve_out_dir(ns.out, ns.force)
    except FileExistsError as error:
        print(f"run.py: refusing to overwrite evidence: {error}", file=sys.stderr)
        return 2

    report = run_cross_project()
    os.makedirs(out_dir, exist_ok=True)
    _dump(os.path.join(out_dir, "counters.json"), report["counters"])
    _dump(os.path.join(out_dir, "cross-project-ledger.json"), report["ledger"])
    _text(os.path.join(out_dir, "interpretation.md"), interpretation_markdown(report))

    print("counters:", report["counters"])
    print("digest equal to committed ablation evidence:", report["ledger"]["shared_material"]["digest_equal"])
    print("seeded by domain A:", report["ledger"]["shared_material"]["seeded_by_domain_a"])
    print("wrote", out_dir, sorted(os.listdir(out_dir)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
