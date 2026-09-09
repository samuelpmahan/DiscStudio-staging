"""Day 2, second experiment (c): consume run-1's retained split as an external
Part instead of recomputing it -- the "skipped Prepare invocation" case.

    python3 experiments/grouped-ablation/run_from_retained.py
    python3 experiments/grouped-ablation/run_from_retained.py --out evidence/run-4-from-retained --force

This is not a fourth build_program() call: it edits the *retained program dict*
(data, loaded from evidence/run-1/retained.json), not program.py or
calculations.py. The `split` entry is dropped from the Prepare tick and every
`fn:split` reference is rewritten to `px:scratch.ablation.split`
(program.SPLIT.address) -- an fn: edge whose producer left the selected set
becomes an external input bound to that producer's `into` address (the same
boundary rule Day 3's promote.py uses, ULTRACODE-WEEK.md critic gap 5).
retain.from_program then rebuilds the rest through PCR.calc exactly as usual, so
writer/id rules re-apply; REGISTRY is imported unchanged and never invoked for
'fn.ablation.split' in this run.

The value seeded at scratch.ablation.split is computed by calling
calculations.split() directly (the same function REGISTRY invokes, called here
the way any consumer of a retained record would call it) on run-1's retained rows
-- not by re-running the Prepare tick's `split` invocation through a PCR. Its
digest is asserted equal to run-1's retained result digest for 'split' before the
rest of the program runs: that equality *is* "joins provenance to run-1's fn:split
by digest". The Prepare tick's `split` invocation is then genuinely absent from
this run's testimony and receipts, and run-1's receipts.json names how many ms it
cost -- the number this script reports as saved.
"""

from __future__ import annotations

import argparse
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from pyto import PxC  # noqa: E402

import retain  # noqa: E402
from calculations import REGISTRY, select_variants  # noqa: E402
from calculations import split as split_fn  # noqa: E402
from program import GROUPS as GROUPS_PART, ROWS, SPLIT  # noqa: E402
from run import testimony_of, timed  # noqa: E402
import second_experiment as se  # noqa: E402


class ProvenanceMismatch(retain.RetainError):
    """Recomputing split() from run-1's retained rows did not match run-1's retained digest."""


def _without_split(program: dict) -> dict:
    """Drop the `split` invocation and rebind every `fn:split` consumer to `px:<SPLIT address>`."""
    out = copy.deepcopy(program)
    found = False
    for tick in out["ticks"]:
        kept = []
        for entry in tick["calculations"]:
            if entry["id"] == "split":
                found = True
                continue
            kept.append(entry)
        tick["calculations"] = kept
    if not found:
        raise ValueError("run_from_retained: no 'split' invocation in the retained program")
    fn_split = "fn:split"
    px_split = f"px:{SPLIT.address}"
    for tick in out["ticks"]:
        for entry in tick["calculations"]:
            entry["inputs"] = {
                name: (px_split if ref == fn_split else ref) for name, ref in entry["inputs"].items()
            }
    return out


def interpretation(record_1: dict, record_4: dict, split_value_digest: str, saved: dict) -> str:
    joined = split_value_digest == record_1["results"]["split"]
    return "\n".join([
        "# run-4-from-retained: split consumed as an external Part",
        "",
        f"digest(calculations.split(rows=run-1's retained rows)) == run-1 retained result digest for "
        f"'split': {joined} -- this is the provenance join to run-1's fn:split by digest.",
        "",
        f"'split' present in this run's program: "
        f"{'split' in [e['id'] for tick in record_4['program']['ticks'] for e in tick['calculations']]}"
        " (expected False: it is now an external Part, not a declared invocation).",
        "",
        f"Skipped Prepare invocations (compare_local.explain_changes(record_1, record_4)['removed']): "
        f"{saved['invocations_skippable_by_digest']}.",
        f"ms saved (run-1 receipts.json duration of the skipped invocation(s)): {saved['ms_saved']}",
        "",
        "Reconstruction required: no. program.py and calculations.py are imported unchanged and never "
        "edited; only the retained *program dict* (data loaded from evidence/run-1/retained.json) is "
        "edited before retain.from_program rebuilds the rest through PCR.calc, which re-applies the "
        "writer/id rules exactly as it does for any other retained program (tests/test_retain.py::"
        "FromProgram::test_writer_and_id_rules_re_apply_on_import).",
        "",
    ])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=None)
    parser.add_argument("--force", action="store_true")
    ns = parser.parse_args(argv)
    try:
        out_dir = se.resolve_named_out_dir(ns.out, "evidence/run-4-from-retained", ns.force)
    except FileExistsError as error:
        print(f"run_from_retained.py: refusing to overwrite evidence: {error}", file=sys.stderr)
        return 2

    record_1 = se.load_json(os.path.join(se.RUN_1, "retained.json"))
    receipts_1 = se.load_json(os.path.join(se.RUN_1, "receipts.json"))

    rows = record_1["external"][ROWS.address]
    groups = record_1["external"][GROUPS_PART.address]
    split_value = split_fn({"rows": rows})
    split_digest = retain.digest_of(split_value)
    if split_digest != record_1["results"]["split"]:
        raise ProvenanceMismatch(
            f"run_from_retained: digest({split_digest}) of calculations.split(rows=run-1's rows) does "
            f"not match run-1's retained result digest for 'split' ({record_1['results']['split']})"
        )

    modified_program = _without_split(record_1["program"])
    pcr = retain.from_program(modified_program, REGISTRY)

    pxc = PxC()
    pxc.set(GROUPS_PART, groups)
    pxc.set(SPLIT, split_value)
    run, t_run = timed("pcr.run", lambda: pcr.run(pxc, observe=True))
    testimony = testimony_of(run)
    comparison = run.results["compare"]

    # Informational only (variants.json / comparison.md): the same selector call
    # run.py makes for its authoring-time copy, over run-1's retained groups.
    variants = select_variants({"groups": groups})

    se.write_common_evidence(
        out_dir,
        title="Grouped ablation, split reused from run-1's retained record",
        seed=7, n=400, groups=groups,
        variants=variants, testimony=testimony,
        comparison=comparison, pcr=pcr, timings=[t_run],
    )
    record_4 = se.write_retained(pxc, run, [GROUPS_PART.address, SPLIT.address], REGISTRY, out_dir)
    se.write_receipts(run, out_dir)

    program_lines = se.changed_lines(
        [os.path.join(HERE, "program.py"), os.path.join(HERE, "calculations.py")]
    )
    saved = se.saved_work(
        run_label=os.path.basename(os.path.normpath(out_dir)),
        prior_run_label="run-1",
        registry_addresses_used=sorted(retain.registry_from_pcr(pcr)),
        all_registry_addresses=sorted(REGISTRY),
        record_prior=record_1, record_this=record_4,
        prior_receipts=receipts_1,
        program_lines=program_lines,
        program_lines_base=se.DAY2_BASE,
        skip_reason="removed",
    )
    se._dump(os.path.join(out_dir, "saved-work.json"), saved)
    se._text(
        os.path.join(out_dir, "interpretation.md"),
        interpretation(record_1, record_4, split_digest, saved),
    )

    print(f"wrote {out_dir}")
    print("ranking:", " > ".join(row["variant"] for row in comparison if row["variant"] != "all"))
    print("split provenance joined by digest:", split_digest == record_1["results"]["split"])
    print("skipped Prepare invocation(s):", saved["invocations_skippable_by_digest"], "ms saved:", saved["ms_saved"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
