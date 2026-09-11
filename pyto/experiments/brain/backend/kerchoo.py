"""the owner's speed pass, measured: before, after, speedup, engine chosen.

nothing here changes an answer. it re-times the calculations this pass touched,
against the wall_ms_min the committed benchmark Parts already recorded, and
writes one Part - px.exp.brain.bench.kerchoo - so the claim "faster" is a
receipt rather than a sentence. The before numbers are read out of the store,
not retyped.

`BRAIN_RECORDS=commit python -m experiments.brain.backend.kerchoo` from pyto/.
"""

from __future__ import annotations

import statistics
import time

from experiments.brain import harness

VERTICAL = "backend"
ADDRESS = "px.exp.brain.bench.kerchoo"


def _time(fn, n=5) -> float:
    samples = []
    for _ in range(n):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000.0)
    return min(samples)


def targets():
    """(address of the committed benchmark Part, label, a thunk that redoes the work)."""
    import os
    import sys

    # the other verticals import each other as top-level packages (stats.x, data.y), the way
    # `unittest discover` puts experiments/brain on the path; do the same here.
    experiments = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if experiments not in sys.path:
        sys.path.insert(0, experiments)

    from experiments.brain.backend import cases as backend_cases
    from experiments.brain.backend import ops
    import data.timeseries_cases as timeseries_cases
    import stats.distributions_cases as distributions_cases

    out = []

    for case in distributions_cases.BENCH_CASES:
        if case["backend"] != "sp" or not case["size"].endswith("n=4000"):
            continue
        name = case["calc"].split(".")[-1]
        calc = distributions_cases.CALCS[case["calc"]]
        out.append((f"px.exp.brain.bench.stats.{name}.sp.{case['size'].replace('.', '_')}",
                    f"stats.{name} sp {case['size']}",
                    (lambda calc=calc, make=case["make_args"]: calc(make())), "sp"))

    for case in timeseries_cases.BENCH_CASES:
        if case["backend"] != "np" or case["size"] != "n=4000" or "expanding" not in case["calc"]:
            continue
        calc = timeseries_cases.CALCS[case["calc"]]
        out.append(("px.exp.brain.bench.data.expanding.np.n=4000", "data.expanding np n=4000",
                    (lambda calc=calc, make=case["make_args"]: calc(make())), "np"))

    for op, size in (("svd", 128), ("pinv", 96), ("matrix_rank", 96)):
        args = backend_cases.bench_inputs(op, size)
        plan = ops.default_plan()
        chosen = ops.choose_engine(plan, op, ops.elements(args)) if plan else "py"
        out.append((harness.bench_address(VERTICAL, op, "py", size), f"backend.{op} (was py) {size}",
                    (lambda op=op, args=args: ops.call(op, dict(args))), chosen))
    return out


def build(store) -> str:
    rows = []
    for address, label, work, engine in targets():
        before = store.get(address)["wall_ms_min"] if store.has(address) else None
        after = _time(work)
        rows.append({
            "calc": label,
            "before_wall_ms_min": before,
            "after_wall_ms_min": after,
            "speedup": round(before / after, 2) if before and after else None,
            "engine": engine,
            "before_from": address,
        })
    rows.sort(key=lambda row: -(row["speedup"] or 0))
    store.put(ADDRESS, {
        "for": "the owner's speed pass: what each calculation cost before, what it costs now, and which engine answers",
        "backend": "mixed",
        "size": "as the committed benchmark Part measured it",
        "n": 5,
        "rule": "before is wall_ms_min out of the committed benchmark Part; after is the minimum of five runs here",
        "rows": rows,
        "wall_ms_median": sum(row["after_wall_ms_min"] for row in rows) / max(1, len(rows)),
        "wall_ms_min": min((row["after_wall_ms_min"] for row in rows), default=0.0),
        "inputs_sha256": harness.digest([row["before_from"] for row in rows]),
    })
    return ADDRESS


def main() -> int:
    store = harness.Store(commit=True)
    store.load_store()
    build(store)
    part = store.get(ADDRESS)
    harness.finding(
        store, VERTICAL, "the_pass_reached_the_loops_not_the_facades", "friction",
        "the two kinds of slowness found here are not the same kind. A vectorised engine that called scipy or numpy "
        "once per element is a bug and was fixed at source (stats pdf/cdf/ppf, and data's rolling/expanding np engine, "
        "which was slower than its own pure-python engine). The rest - ml.knn_predict at 524 ms and ml.softmax_fit at "
        "467 ms - are pure-python calculations running on py because their facade has no plan to read: making them fast "
        "means giving the stats, data and ml facades the same default-to-the-plan dispatch the backend facade now has, "
        "and extending px.exp.brain.result.backend.plan to their bench Parts. That is a change to three verticals' "
        "dispatchers and it did not fit in the window.",
        for_="the next pass: the remaining time is in three facades that cannot yet read what the benchmark Parts know",
        workaround="the backend facade defaults to the plan now, so svd, pinv and matrix_rank stop running on py; the "
                   "other three verticals still need an engine named by hand",
        proposal="one shared dispatcher in harness.py - choose(op, args, plan) - that every vertical's facade calls, so "
                 "'which engine' is answered in one place from the benchmark Parts for all of them",
    )
    store.save(VERTICAL)
    print(f"{ADDRESS}: {len(part['rows'])} calcs")
    for row in part["rows"]:
        print("  %-34s %8s -> %7.3f ms  x%-6s %s" % (
            row["calc"], round(row["before_wall_ms_min"], 1) if row["before_wall_ms_min"] else "?",
            row["after_wall_ms_min"], row["speedup"], row["engine"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
