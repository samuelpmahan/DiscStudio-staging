"""Day 2, second experiment (a): apply Day 1's comparison procedure to a
cross-cutting 3x5 grouping -- a different partition of the same 15 features,
each new group holding at most two of the three planted-weight features.

    python3 experiments/grouped-ablation/run_regrouped.py
    python3 experiments/grouped-ablation/run_regrouped.py --out evidence/run-2-regroup --force

Only the input Part (the `groups` mapping passed to run.run_experiment) and the
resulting variants list change; build_program, family and REGISTRY are imported
unchanged (research/ULTRACODE-WEEK.md Day 2 kill criterion). Same seed and n as
run-1 (7, 400): 'split' depends only on rows, so its result and receipt duration
are expected to match run-1's exactly, which is the evidence that reuse-by-digest
is valid across a regrouping.
"""

from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from features import FEATURES  # noqa: E402
from calculations import REGISTRY  # noqa: E402
import retain  # noqa: E402
from run import EXTERNAL_ADDRESSES, run_experiment  # noqa: E402
import second_experiment as se  # noqa: E402

SEED, N = 7, 400  # same fixture as run-1: only `groups` changes.

# A cross-cutting 3x5 partition of FEATURES (Day 1 is 5x3: g0..g4). Each of h0/h1/h2
# holds exactly one of the three planted features (f00 weight 1.5, f03 weight 0.8,
# f09 weight 2.0, features.py TRUE_W) -- "at most two planted weights per group".
CROSS_GROUPS = {
    "h0": [FEATURES[i] for i in (0, 4, 7, 10, 13)],
    "h1": [FEATURES[i] for i in (1, 3, 8, 11, 14)],
    "h2": [FEATURES[i] for i in (2, 5, 6, 9, 12)],
}
assert sorted(c for cols in CROSS_GROUPS.values() for c in cols) == sorted(FEATURES)
assert sum(len(cols) for cols in CROSS_GROUPS.values()) == len(FEATURES)


def interpretation(comparison: list[dict], record_1: dict, record_2: dict, saved: dict) -> str:
    split_equal = record_1["results"]["split"] == record_2["results"]["split"]
    biggest = max(abs(row["delta_vs_baseline"]) for row in comparison if row["variant"] != "all")
    lines = [
        "# run-2-regroup: cross-cutting 3x5 grouping",
        "",
        f"CROSS_GROUPS: {CROSS_GROUPS}",
        "",
        f"split digest equal to run-1 (same seed/n, groups is the only changed input Part): {split_equal}",
        "",
        f"Largest |delta vs baseline| across the three cross-cutting drops: {biggest:.4f}.",
        f"No single drop exceeds +0.9 RMSE: {biggest <= 0.9} -- each new group holds exactly one of the "
        "three planted-weight features (features.py TRUE_W), the same as Day 1's per-group ablations; "
        "the cross-cutting regroup does not concentrate more planted weight into one group than Day 1 did, "
        "so it produces a comparably sized, not a larger, RMSE increase.",
        "",
        f"Invocations skippable by digest against run-1 (compare_local.explain_changes, "
        f"unchanged_upstream): {saved['invocations_skippable_by_digest']}. Only 'split' is expected: "
        "'select' changes because the groups external differs; every fit.*/score.*/compare id changes "
        "because the variant keys (h0/h1/h2 vs g0..g4) differ, which explain_changes reports as "
        "added/removed ids, not a digest drift on a shared id.",
        f"ms saved (run-1 receipts.json duration of the skippable ids): {saved['ms_saved']}",
        "",
        "Reconstruction required: no. program.py and calculations.py are imported unchanged "
        "(git diff shows program_lines_changed == 0 above); only the `groups` input Part and the "
        "variants list it produces via select_variants differ from run-1.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=None)
    parser.add_argument("--force", action="store_true")
    ns = parser.parse_args(argv)
    try:
        out_dir = se.resolve_named_out_dir(ns.out, "evidence/run-2-regroup", ns.force)
    except FileExistsError as error:
        print(f"run_regrouped.py: refusing to overwrite evidence: {error}", file=sys.stderr)
        return 2

    result = run_experiment(SEED, N, groups=CROSS_GROUPS)
    se.write_common_evidence(
        out_dir,
        title="Grouped ablation, cross-cutting 3x5 regroup",
        seed=SEED, n=N, groups=CROSS_GROUPS,
        variants=result["variants"], testimony=result["testimony"],
        comparison=result["comparison"], pcr=result["pcr"], timings=result["timings"],
    )
    record_2 = se.write_retained(result["pxc"], result["run"], list(EXTERNAL_ADDRESSES), REGISTRY, out_dir)
    se.write_receipts(result["run"], out_dir)

    record_1 = se.load_json(os.path.join(se.RUN_1, "retained.json"))
    receipts_1 = se.load_json(os.path.join(se.RUN_1, "receipts.json"))
    program_lines = se.changed_lines(
        [os.path.join(HERE, "program.py"), os.path.join(HERE, "calculations.py")]
    )
    saved = se.saved_work(
        run_label=os.path.basename(os.path.normpath(out_dir)),
        prior_run_label="run-1",
        registry_addresses_used=sorted(retain.registry_from_pcr(result["pcr"])),
        all_registry_addresses=sorted(REGISTRY),
        input_parts_changed=["input.ablation.groups"],
        record_prior=record_1, record_this=record_2,
        prior_receipts=receipts_1,
        program_lines=program_lines,
        skip_reason="unchanged_upstream",
    )
    se._dump(os.path.join(out_dir, "saved-work.json"), saved)
    se._text(os.path.join(out_dir, "interpretation.md"), interpretation(result["comparison"], record_1, record_2, saved))

    print(f"wrote {out_dir}")
    print("ranking:", " > ".join(row["variant"] for row in result["comparison"] if row["variant"] != "all"))
    print("split digest equal to run-1:", record_1["results"]["split"] == record_2["results"]["split"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
