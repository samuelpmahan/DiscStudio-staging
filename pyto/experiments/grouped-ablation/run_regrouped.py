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

from features import FEATURES, GROUPS as DAY1_GROUPS, TRUE_W  # noqa: E402
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


def planted_weight_per_group(groups: dict[str, list[str]]) -> dict[str, float]:
    """Sum of |TRUE_W| over each group's columns (features.py TRUE_W), computed here."""
    return {
        name: sum(abs(TRUE_W[FEATURES.index(column)]) for column in columns)
        for name, columns in groups.items()
    }


def planted_features_per_group(groups: dict[str, list[str]]) -> dict[str, int]:
    """How many nonzero-weight features each group holds."""
    return {
        name: sum(1 for column in columns if TRUE_W[FEATURES.index(column)] != 0)
        for name, columns in groups.items()
    }


def _entry(record: dict, invocation_id: str) -> dict | None:
    for tick in record["program"]["ticks"]:
        for entry in tick["calculations"]:
            if entry["id"] == invocation_id:
                return entry
    return None


def interpretation(comparison: list[dict], record_1: dict, record_2: dict, saved: dict) -> str:
    """Every number below is computed here from the two retained records, this run's
    comparison and run-1's committed comparison.json -- none is a literal in the text
    (fixer round 1, findings 9 and 10)."""
    split_equal = record_1["results"]["split"] == record_2["results"]["split"]
    biggest = max(abs(row["delta_vs_baseline"]) for row in comparison if row["variant"] != "all")
    run_1_rows = se.load_json(os.path.join(se.RUN_1, "comparison.json"))["rows"]
    run_1_biggest = max(abs(row["delta_vs_baseline"]) for row in run_1_rows if row["variant"] != "all")

    cross_weight = planted_weight_per_group(CROSS_GROUPS)
    day1_weight = planted_weight_per_group(DAY1_GROUPS)
    cross_max, day1_max = max(cross_weight.values()), max(day1_weight.values())
    cross_planted = planted_features_per_group(CROSS_GROUPS)
    day1_planted = planted_features_per_group(DAY1_GROUPS)

    explanation = saved["explain_changes"]
    shared_changed = {i: explanation["reason"][i] for i in explanation["changed"]}
    args_detail = []
    for invocation_id, why in shared_changed.items():
        if why != "args":
            continue
        old_entry, new_entry = _entry(record_1, invocation_id), _entry(record_2, invocation_id)
        args_detail.append(
            f"  {invocation_id}: run-1 args={(old_entry or {}).get('args')} "
            f"-> run-2 args={(new_entry or {}).get('args')}"
        )

    lines = [
        "# run-2-regroup: cross-cutting 3x5 grouping",
        "",
        f"CROSS_GROUPS: {CROSS_GROUPS}",
        "",
        f"split digest equal to run-1 (same seed/n, groups is the only changed input Part): {split_equal}",
        "",
        "## The plan's predicted bound, measured",
        "",
        "research/ULTRACODE-WEEK.md Day 2 predicts: \"no single drop exceeds +0.9 RMSE because "
        "each group holds at most two planted weights\".",
        f"Largest |delta vs baseline| across the three cross-cutting drops: {biggest:.4f}.",
        f"No single drop exceeds +0.9 RMSE: {biggest <= 0.9}.",
        f"The predicted bound is {'held' if biggest <= 0.9 else 'REFUTED by measurement'}: "
        f"{biggest:.4f} against the predicted <= 0.9.",
        f"Run-1's largest |delta vs baseline| (evidence/run-1/comparison.json): {run_1_biggest:.4f}. "
        f"This regroup is larger than run-1: {biggest > run_1_biggest}.",
        f"Planted |w| per group -- Day 1 (features.GROUPS): {day1_weight}; this run (CROSS_GROUPS): "
        f"{cross_weight}.",
        f"Largest planted |w| in any one group: Day 1 {day1_max}, cross-cutting {cross_max}; the "
        f"regroup concentrates more planted weight into one group than Day 1 did: {cross_max > day1_max}.",
        f"Nonzero-weight features per group -- Day 1: {day1_planted}; this run: {cross_planted}.",
        "",
        "## What changed against run-1, as compare_local.explain_changes reports it",
        "",
        f"Invocations skippable by digest (unchanged_upstream): {saved['invocations_skippable_by_digest']}. "
        f"ms saved (run-1 receipts.json duration of those ids): {saved['ms_saved']}",
        f"Ids only in this run (added): {explanation['added']}",
        f"Ids only in run-1 (removed): {explanation['removed']}",
        f"Ids present in BOTH programs whose retained state changed, with the reason explain_changes "
        f"computed: {shared_changed}",
    ]
    lines.extend(args_detail)
    lines += [
        "",
        "Reconstruction required: no. program.py and calculations.py are imported unchanged "
        f"(git diff against {saved['program_lines_changed_base']} shows program_lines_changed "
        f"{saved['program_lines_changed']}); only the `groups` input Part and the variants list it "
        "produces via select_variants differ from run-1.",
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
        record_prior=record_1, record_this=record_2,
        prior_receipts=receipts_1,
        program_lines=program_lines,
        program_lines_base=se.DAY2_BASE,
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
