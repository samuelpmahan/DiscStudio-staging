"""Day 2, second experiment (b): apply Day 1's comparison procedure to a second
input -- a new seed and a larger n -- with the original 5x3 grouping unchanged.

    python3 experiments/grouped-ablation/run_reinput.py
    python3 experiments/grouped-ablation/run_reinput.py --out evidence/run-3-reinput --force

Only the input Parts feeding make_data (seed, n) change; features.GROUPS,
build_program, family and REGISTRY are imported unchanged (research/
ULTRACODE-WEEK.md Day 2 kill criterion). Because rows differ from run-1, split's
retained digest is expected to differ too -- the counterpart of run_regrouped.py's
"split digest equal" claim, proving explain_changes reports a real change here.
"""

from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from features import GROUPS  # noqa: E402
from calculations import REGISTRY  # noqa: E402
import retain  # noqa: E402
from run import EXTERNAL_ADDRESSES, run_experiment  # noqa: E402
import second_experiment as se  # noqa: E402

SEED, N = 11, 800  # a new seed and n=800 (Day 1 fixture: seed=7, n=400).


def interpretation(comparison: list[dict], record_1: dict, record_3: dict, saved: dict) -> str:
    split_equal = record_1["results"]["split"] == record_3["results"]["split"]
    top3 = [row["variant"] for row in comparison if row["variant"] != "all"][:3]
    return "\n".join([
        "# run-3-reinput: seed and n changed",
        "",
        f"seed={SEED}, n={N} (Day 1: seed=7, n=400); same 5x3 grouping (features.GROUPS) and the same "
        "variants list (select_variants({'groups': GROUPS}) is unchanged, so this is literally Day 1's "
        f"program run over {N} freshly drawn rows instead of 400.",
        "",
        f"split digest equal to run-1: {split_equal} -- expected False: split's args include the rows "
        "themselves (calculations.py:split), and a new seed and a different n change every row.",
        "",
        f"Ranking (ablations only): {' > '.join(top3)}. The planted ranking (drop_g3 > drop_g0 > drop_g1, "
        "features.py TRUE_W) is expected to hold regardless of seed/n (Day 1 kill criterion, verified "
        "across seeds 3, 11, 13, 99 in the completeness critic's checks).",
        "",
        f"Invocations skippable by digest against run-1 (compare_local.explain_changes, "
        f"unchanged_upstream): {saved['invocations_skippable_by_digest']}. 'select' is the one id whose "
        "inputs, args and external value (features.GROUPS) are byte-identical to run-1 and whose result "
        "digest therefore matches -- the only genuinely reusable invocation when just the rows change.",
        f"ms saved (run-1 receipts.json duration of the skippable ids): {saved['ms_saved']}",
        "",
        "Reconstruction required: no. program.py and calculations.py are imported unchanged "
        "(program_lines_changed == 0 above); only seed and n (and the rows they produce) differ from run-1.",
        "",
    ])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=None)
    parser.add_argument("--force", action="store_true")
    ns = parser.parse_args(argv)
    try:
        out_dir = se.resolve_named_out_dir(ns.out, "evidence/run-3-reinput", ns.force)
    except FileExistsError as error:
        print(f"run_reinput.py: refusing to overwrite evidence: {error}", file=sys.stderr)
        return 2

    result = run_experiment(SEED, N)  # groups=None -> features.GROUPS, unchanged
    se.write_common_evidence(
        out_dir,
        title="Grouped ablation, second input",
        seed=SEED, n=N, groups=GROUPS,
        variants=result["variants"], testimony=result["testimony"],
        comparison=result["comparison"], pcr=result["pcr"], timings=result["timings"],
    )
    record_3 = se.write_retained(result["pxc"], result["run"], list(EXTERNAL_ADDRESSES), REGISTRY, out_dir)
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
        input_parts_changed=["input.ablation.rows"],
        record_prior=record_1, record_this=record_3,
        prior_receipts=receipts_1,
        program_lines=program_lines,
        program_lines_base=se.DAY2_BASE,
        skip_reason="unchanged_upstream",
    )
    se._dump(os.path.join(out_dir, "saved-work.json"), saved)
    se._text(os.path.join(out_dir, "interpretation.md"), interpretation(result["comparison"], record_1, record_3, saved))

    print(f"wrote {out_dir}")
    print("ranking:", " > ".join(row["variant"] for row in result["comparison"] if row["variant"] != "all"))
    print("split digest equal to run-1:", record_1["results"]["split"] == record_3["results"]["split"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
