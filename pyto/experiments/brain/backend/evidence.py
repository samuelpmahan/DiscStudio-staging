"""the receipts: an oracle Part per engine per case, a benchmark Part per engine
per size, and every result published by a real observed `PCR`.

nothing here decides anything. it runs the facade the way a vertical would, and
writes down what happened where `PQL` can find it again: this is what "Parts in,
Parts out" costs, and it is the only reason the tournaments later can be judged
on evidence rather than on opinion.

`python -m experiments.brain.backend.evidence` (from pyto/) rebuilds all of it
into `experiments/brain/store/backend.json` and `experiments/brain/records/`.
"""

from __future__ import annotations

from typing import Any, Mapping

from experiments.brain import harness
from experiments.brain.backend import cases as case_module
from experiments.brain.backend import ops

VERTICAL = "backend"


def _split(args: Mapping[str, Any]) -> tuple[dict, dict]:
    """a case's arguments, split the way the contract splits them.

    a matrix or a column is an input and becomes a dataset Part; a bin count, a
    k, a metric, a range is a constant of the invocation and stays in `args`.
    """
    parts, constants = {}, {}
    for key, value in args.items():
        if isinstance(value, list) and value and isinstance(value[0], (list, int, float)):
            parts[key] = value
        else:
            constants[key] = value
    return parts, constants


def _dataset_for(store, op: str, case: str, key: str, value: list) -> str:
    rows = value if value and isinstance(value[0], list) else [[one] for one in value]
    return harness.dataset(
        store,
        f"backend_{op}_{case}_{key}",
        f"the {key} of the {op}/{case} case, so the calculation reads a Part and not a literal",
        [f"c{i}" for i in range(len(rows[0]))],
        rows,
    )


def build_results(store) -> dict:
    """every case, every engine, through one observed `PCR` per op."""
    by_op: dict[str, list] = {}
    for case in case_module.cases():
        by_op.setdefault(case["op"], []).append(case)
    produced = {}
    for op, group in sorted(by_op.items()):
        calc = ops.calculation(op)
        steps = []
        for case in group:
            parts, constants = _split(case["args"])
            inputs = {key: _dataset_for(store, op, case["case"], key, value) for key, value in parts.items()}
            for engine in case_module.engines_of_case(case, ops.engines_of(op)):
                step_id = f"{case['case']}_{engine}"
                address = harness.result_address(VERTICAL, op, step_id)
                steps.append({"id": step_id, "calc": calc, "into": address, "args": dict(constants, backend=engine), "inputs": dict(inputs)})
                produced[(op, case["case"], engine)] = address
        run = store.run(f"brain_backend_{op}", [(op, steps)])
        for case in group:
            for engine in case_module.engines_of_case(case, ops.engines_of(op)):
                produced[(op, case["case"], engine)] = run.results[f"{case['case']}_{engine}"]
    return produced


def build_oracles(store, produced: dict) -> dict:
    """one oracle Part per engine per case, against the numpy or scipy reference."""
    verdicts = {}
    for case in case_module.cases():
        expected = case["expected"]()
        for engine in case_module.engines_of_case(case, ops.engines_of(case["op"])):
            got = produced[(case["op"], case["case"], engine)]
            verdicts[(case["op"], case["case"], engine)] = harness.oracle(
                store,
                VERTICAL,
                case["op"],
                f"{case['case']}_{engine}",
                got=got,
                expected=expected,
                reference=case["reference"],
                tolerance=case["tolerance"],
                for_=f"the {engine} engine of {case['op']} must be the same question answered, or it is a failed backend",
            )
    return verdicts


def build_benchmarks(store, ops_to_bench=None) -> list[dict]:
    """three sizes per op per engine, wall clock in the host, never in a Calculation."""
    out = []
    for op in ops_to_bench or ops.ops():
        for size in case_module.sizes_for(op):
            args = case_module.bench_inputs(op, size)
            for engine in ops.engines_of(op):
                out.append(
                    harness.bench(
                        store,
                        VERTICAL,
                        op,
                        engine,
                        size,
                        lambda op=op, args=args, engine=engine: ops.call(op, dict(args, backend=engine)),
                        n=int(case_module.repeats_for(size)),
                        for_="where the engine boundary pays, and where it does not",
                        inputs={"op": op, "size": size, "shape": case_module.shape_of(args)},
                    )
                )
    return out


def build(store, benchmarks: bool = True) -> dict:
    produced = build_results(store)
    verdicts = build_oracles(store, produced)
    benches = build_benchmarks(store) if benchmarks else []
    plan = None
    if benches:
        # the benchmark Parts are not decoration: folded into one Part, they are what
        # `backend="auto"` reads to pick an engine at the size the caller actually has.
        from experiments.brain.backend import choose

        plan = choose.build(store)
    return {"results": len(produced), "oracles": verdicts, "benches": len(benches), "plan": plan}


def main() -> int:
    store = harness.Store()
    store.load_store()
    built = build(store)
    failed = [key for key, ok in built["oracles"].items() if not ok]
    store.save(VERTICAL)
    print(f"results {built['results']}  oracles {len(built['oracles'])} ({len(failed)} failed)  benchmarks {built['benches']}")
    if built.get("plan"):
        from experiments.brain.backend import choose

        plan = store.get(built["plan"])
        print(f"plan at {built['plan']}: {len(plan['ops'])} ops")
        for op in plan["ops"]:
            print("  " + choose.explain(plan, op))
    for key in failed:
        print("  FAILED", key)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
