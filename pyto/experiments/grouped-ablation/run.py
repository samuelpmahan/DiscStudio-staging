"""Run the grouped ablation and retain evidence under evidence/run-<k>/.

    python3 experiments/grouped-ablation/run.py --seed 7 --n 400 --out evidence/run-1

Files written (gap 18d: testimony.json is {pcr, ticks} only; observations are a
later seam): testimony.json, comparison.json, comparison.md, timings.json,
variants.json, failed-variants.md, mermaid.mmd, saved-work.json, commit.txt.
Every count in saved-work.json is computed at run time (gap 18b).
"""

from __future__ import annotations

import argparse
import dataclasses
import functools
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from pyto import PQL, PxC  # noqa: E402

from calculations import REGISTRY, select_variants  # noqa: E402
from features import FIXTURE_LABEL, GROUPS, TRUE_W, make_data, planted_weight_by_group  # noqa: E402
from program import BASELINE_KEY, COMPARISON, GROUPS as GROUPS_PART, ROWS, VARIANTS, build_program  # noqa: E402
from timing import timed  # noqa: E402

AUTHORING_FILES = ("features.py", "calculations.py", "program.py")
UNINFORMATIVE_DELTA = 0.05


def jsonable(value):
    """asdict() keeps TickTestimony.calculations as a tuple (pcr.py:73); JSON has only lists."""
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    return value


def testimony_of(run) -> dict:
    """Gap 18d: testimony.json is {pcr, ticks} only; results and later observations live elsewhere."""
    return {"pcr": run.pcr, "ticks": jsonable([dataclasses.asdict(tick) for tick in run.ticks])}


def run_experiment(seed: int, n: int) -> dict:
    """Execute the program once; return everything the evidence writer needs."""
    rows, t_data = timed("make_data", functools.partial(make_data, seed, n))
    pxc = PxC()
    pxc.set(ROWS, rows)
    pxc.set(GROUPS_PART, GROUPS)

    variants = select_variants({"groups": GROUPS})  # authoring-time copy of the selector's result
    pcr, t_build = timed("build_program", functools.partial(build_program, variants))
    run, t_run = timed("pcr.run", functools.partial(pcr.run, pxc))

    selected_inside = PQL.part(VARIANTS).one(pxc)
    if selected_inside != variants:
        raise RuntimeError("selector result inside the PCR differs from the authoring-time variant list")

    comparison = PQL.part(COMPARISON).one(pxc)
    testimony = testimony_of(run)
    return {
        "seed": seed,
        "n": n,
        "fixture": FIXTURE_LABEL,
        "variants": variants,
        "pcr": pcr,
        "run": run,
        "testimony": testimony,
        "comparison": comparison,
        "timings": [t_data, t_build, t_run],
        "pxc": pxc,
    }


def ranking(comparison: list[dict]) -> list[str]:
    return [row["variant"] for row in comparison if row["variant"] != BASELINE_KEY]


def failed_variants(comparison: list[dict]) -> list[dict]:
    """Ablations whose |delta| is below UNINFORMATIVE_DELTA: retained, not hidden."""
    planted = planted_weight_by_group()
    out = []
    for row in comparison:
        if row["variant"] == BASELINE_KEY:
            continue
        group = row["variant"].removeprefix("drop_")
        if abs(row["delta_vs_baseline"]) < UNINFORMATIVE_DELTA:
            out.append({"variant": row["variant"], "group": group, "delta_vs_baseline": row["delta_vs_baseline"], "planted_weight": planted.get(group, 0.0)})
    return out


def comparison_markdown(result: dict) -> str:
    planted = planted_weight_by_group()
    lines = [
        f"# Grouped ablation, seed={result['seed']} n={result['n']} ({result['fixture']})",
        "",
        "Leave-one-group-out over 5 groups x 3 features; baseline `all` keeps every column.",
        "Rank 1 is the largest RMSE increase when the group is dropped.",
        "",
        "| rank | variant | rmse | delta vs all | planted |w| in group |",
        "|---:|---|---:|---:|---:|",
    ]
    for row in result["comparison"]:
        group = row["variant"].removeprefix("drop_")
        weight = planted.get(group, 0.0) if row["variant"] != BASELINE_KEY else sum(abs(w) for w in TRUE_W)
        lines.append(f"| {row['rank']} | {row['variant']} | {row['rmse']:.4f} | {row['delta_vs_baseline']:+.4f} | {weight:.1f} |")
    lines.append("")
    lines.append(f"Ranking (ablations only): {' > '.join(ranking(result['comparison']))}")
    lines.append("")
    return "\n".join(lines)


def failed_variants_markdown(result: dict) -> str:
    rows = failed_variants(result["comparison"])
    lines = [
        "# Failed / uninformative variants",
        "",
        f"A variant is uninformative when |delta vs all| < {UNINFORMATIVE_DELTA}. These are retained,",
        "not dropped: an ablation that changes nothing is evidence about the fixture, not noise to hide.",
        "",
    ]
    if not rows:
        lines.append("None for this seed (unexpected: g2 and g4 carry no planted weight, see features.py TRUE_W).")
    for row in rows:
        lines.append(
            f"- `{row['variant']}`: delta {row['delta_vs_baseline']:+.4f}; planted |w| in {row['group']} = {row['planted_weight']:.1f}. "
            "Interpretation: the group carries no planted weight (features.py TRUE_W), so removing its three columns "
            "cannot raise test RMSE; any nonzero delta is ridge/OLS fit noise on 100 test rows, and a small negative "
            "delta means the dropped columns were only fitting noise. The variant is a control, not a failure of the method."
        )
    lines.append("")
    return "\n".join(lines)


def _wc_lines(paths: list[str]) -> dict[str, int]:
    out = subprocess.run(["wc", "-l", *paths], capture_output=True, text=True, check=True).stdout
    counts = {}
    for line in out.strip().splitlines():
        count, name = line.split(None, 1)
        if name != "total":
            counts[os.path.basename(name)] = int(count)
    return counts


def saved_work(result: dict) -> dict:
    invocations = sum(len(tick["calculations"]) for tick in result["testimony"]["ticks"])
    authoring = _wc_lines([os.path.join(HERE, f) for f in AUTHORING_FILES])
    wall = {t["label"]: t["wall_ms"] for t in result["timings"]}
    return {
        "run": "run-1 baseline (nothing reused yet; later runs report work saved against this)",
        "fixture": result["fixture"],
        "calculations_authored": len(REGISTRY),
        "calculation_addresses": sorted(REGISTRY),
        "authoring_lines": authoring,
        "authoring_lines_total": sum(authoring.values()),
        "variants": len(result["variants"]),
        "ablation_variants": sum(1 for v in result["variants"] if v["kind"] == "ablation"),
        "invocations_executed": invocations,
        "ticks": [tick["name"] for tick in result["testimony"]["ticks"]],
        "wall_ms": wall,
        "wall_ms_total": round(sum(wall.values()), 3),
        "inherited_calculations": 0,
        "invocations_skipped": 0,
        "ms_saved": 0.0,
    }


def commit_sha() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=HERE)
    return proc.stdout.strip() if proc.returncode == 0 else f"unavailable: {proc.stderr.strip()}"


def _dump(path: str, payload) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def write_evidence(result: dict, out_dir: str) -> list[str]:
    os.makedirs(out_dir, exist_ok=True)
    _dump(os.path.join(out_dir, "testimony.json"), result["testimony"])
    _dump(os.path.join(out_dir, "comparison.json"), {"seed": result["seed"], "n": result["n"], "baseline": BASELINE_KEY, "ranking": ranking(result["comparison"]), "rows": result["comparison"]})
    _text(os.path.join(out_dir, "comparison.md"), comparison_markdown(result))
    _dump(os.path.join(out_dir, "timings.json"), {"seed": result["seed"], "n": result["n"], "fixture": result["fixture"], "timings": result["timings"]})
    _dump(os.path.join(out_dir, "variants.json"), {"seed": result["seed"], "groups": GROUPS, "variants": result["variants"], "failed_or_uninformative": failed_variants(result["comparison"])})
    _text(os.path.join(out_dir, "failed-variants.md"), failed_variants_markdown(result))
    _text(os.path.join(out_dir, "mermaid.mmd"), result["pcr"].mermaid())
    _dump(os.path.join(out_dir, "saved-work.json"), saved_work(result))
    _text(os.path.join(out_dir, "commit.txt"), commit_sha() + "\n")
    return sorted(os.listdir(out_dir))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--n", type=int, default=400)
    parser.add_argument("--out", default="evidence/run-1", help="relative paths resolve against the experiment directory")
    ns = parser.parse_args(argv)
    out_dir = ns.out if os.path.isabs(ns.out) else os.path.join(HERE, ns.out)
    result = run_experiment(ns.seed, ns.n)
    files = write_evidence(result, out_dir)
    print(comparison_markdown(result))
    failed = failed_variants(result["comparison"])
    print("uninformative variants flagged:", [row["variant"] for row in failed])
    print("wall ms:", {t["label"]: t["wall_ms"] for t in result["timings"]})
    print("wrote", out_dir, files)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
