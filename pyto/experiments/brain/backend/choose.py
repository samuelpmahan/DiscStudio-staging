"""`backend="auto"`: the engine chosen from the benchmark Parts, not from reflex.

"use numpy" is a claim about size. At 64 elements the numpy call's own overhead is
most of the measurement and the pure-python engine wins; at 131072 it is not close.
This module turns the benchmark Parts the vertical already wrote into one Part - the
plan - and the facade reads the plan like any other input:

    plan = store.get(choose.PLAN)            # or choose.build(store) to make it
    ops.call("pairwise", {"a": rows, "backend": "auto", "plan": plan})

The plan is a Part, so a Calculation that uses it stays pure over its inputs: no
file is read and no clock is consulted inside the calculation. A caller that asks
for "auto" without one is refused by name rather than quietly given numpy.
"""

from __future__ import annotations

from pyto import PQL

from experiments.brain import harness
from experiments.brain.backend import cases as case_module
from experiments.brain.backend import ops

VERTICAL = "backend"
PLAN = "px.exp.brain.result.backend.plan"
RULE = ("the engine measured fastest at the largest recorded input not larger than this one; "
        "below the smallest recorded input, the engine measured fastest there")


def build(store, vertical: str = VERTICAL) -> str:
    """read every benchmark Part through PQL and write the plan Part. returns its address.

    only the sizes at which every engine of an op was measured can decide anything,
    so a partially measured size is skipped rather than guessed at.
    """
    measured: dict[str, dict[int, dict[str, float]]] = {}
    for match in PQL.prefix(f"{harness.BENCH}{vertical}.").matches(store.pxc):
        segments = match.address.split(".")
        if len(segments) != 8 or segments[6] not in ops.ENGINES or not segments[7].isdigit():
            continue
        op, engine, size = segments[5], segments[6], int(segments[7])
        if op not in ops.ops():
            continue
        measured.setdefault(op, {}).setdefault(size, {})[engine] = float(match.value["wall_ms_median"])

    by_op: dict[str, list] = {}
    for op, sizes in sorted(measured.items()):
        steps = []
        for size in sorted(sizes):
            row = sizes[size]
            if set(row) != set(ops.engines_of(op)):
                continue
            fastest = min(sorted(row), key=lambda engine: row[engine])
            steps.append([ops.elements(case_module.bench_inputs(op, size)), fastest, round(row[fastest], 6),
                          round(max(row.values()) / row[fastest], 3)])
        if steps:
            by_op[op] = steps
    # Every other vertical's benchmark Parts, keyed "<vertical>.<calc>". Their size tokens
    # are each vertical's own words (n600_d8_k7, t.n=4000) and cannot be turned into an
    # element count the way the backend's can, so what is recorded per calc is the engine
    # that was fastest at the LARGEST recorded case, and the spread it won by. A facade
    # with no size to reason about still gets the right default.
    by_calc: dict[str, dict] = {}
    for match in PQL.prefix(harness.BENCH).matches(store.pxc):
        segments = match.address.split(".")
        if len(segments) != 8 or segments[4] == vertical:
            continue
        key = f"{segments[4]}.{segments[5]}"
        by_calc.setdefault(key, {}).setdefault(segments[7], {})[segments[6]] = float(match.value["wall_ms_min"])
    decided = {}
    for key, sizes in sorted(by_calc.items()):
        best_case, best_engine, spread = None, None, 1.0
        for case, row in sorted(sizes.items()):
            if len(row) < 2:
                continue
            fastest = min(sorted(row), key=lambda engine: row[engine])
            slowest = max(row.values())
            if row[fastest] > 0 and slowest / row[fastest] >= spread:
                best_case, best_engine, spread = case, fastest, slowest / row[fastest]
        if best_engine:
            decided[key] = {"engine": best_engine, "at": best_case, "spread": round(spread, 2),
                            "engines": sorted(sizes[best_case])}

    address = store.put(
        PLAN,
        {
            "for": "the facade choosing an engine from what was measured, at the size the caller actually has",
            "rule": RULE,
            "by_op": by_op,
            "ops": sorted(by_op),
            "by_calc": decided,
            "calcs": sorted(decided),
        },
    )
    return address


def engine_for_calc(plan, vertical: str, calc: str, engines):
    """the engine the plan names for `<vertical>.<calc>`, or None if it says nothing.

    `engines` is what the caller's facade can actually run; a plan that names an
    engine the facade does not have (a tournament branch, say) is ignored rather
    than obeyed, so a stale plan can never make a facade refuse.
    """
    row = (plan or {}).get("by_calc", {}).get(f"{vertical}.{calc}")
    if not row or row["engine"] not in tuple(engines):
        return None
    return row["engine"]


def engine_for(plan, op: str, elements: int) -> str:
    """the engine the plan names for this op at this many elements."""
    steps = (plan or {}).get("by_op", {}).get(op)
    if not steps:
        raise ValueError(
            f"brain: the plan says nothing about {op!r}; build it with "
            "experiments.brain.backend.choose.build(store) after the benchmarks, or name an engine"
        )
    chosen = steps[0][1]
    for size, engine, _median, _spread in steps:
        if elements >= size:
            chosen = engine
    return chosen


def explain(plan, op: str) -> str:
    """one line a reader can check against the benchmark Parts."""
    steps = plan["by_op"][op]
    return f"{op}: " + ", ".join(f"<={size} {engine} ({median} ms, {spread}x)" for size, engine, median, spread in steps)
