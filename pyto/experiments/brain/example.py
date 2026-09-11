"""the harness end to end, in one small piece: the pattern every vertical copies.

one facade `Calculation` with two engines, run through a real `PCR`; an oracle
per engine against numpy; a benchmark per engine at three sizes; a bracket whose
criteria are written before anyone judges, judged by someone who did not build,
decided and refined; a finding and a map part. `build(store)` is re-runnable:
the same store comes out every time, which is what makes the test above it and
`python -m experiments.brain.map` mean the same thing.
"""

from __future__ import annotations

from pyto import Calculation

from experiments.brain import harness
from experiments.brain.harness import Store

VERTICAL = "backend"


def mean(args):
    """the mean of a dataset part, by the engine `args["backend"]` names."""
    rows = harness.values_of(args["data"])
    flat = [float(cell) for row in rows for cell in row]
    backend = args.get("backend", "py")
    if backend == "py":
        return sum(flat) / len(flat)
    if backend == "np":
        import numpy as np

        return float(np.mean(np.asarray(flat, dtype="float64")))
    if backend == "sp":
        from scipy import stats

        return float(stats.tmean(flat))
    raise ValueError(f"brain: unknown backend {backend!r}")


MEAN = Calculation("fn.brain.backend.mean", mean)


def build(store: Store) -> Store:
    small = harness.synthetic(store, "example_small", "the harness, proven on something real", seed=11, shape=(8, 4))
    run = store.run(
        "brain_example",
        [
            (
                "mean",
                [
                    {"id": "py", "calc": MEAN, "into": harness.result_address(VERTICAL, "mean", "example_py"), "args": {"backend": "py"}, "inputs": {"data": small}},
                    {"id": "np", "calc": MEAN, "into": harness.result_address(VERTICAL, "mean", "example_np"), "args": {"backend": "np"}, "inputs": {"data": small}},
                ],
            )
        ],
    )

    import numpy as np

    flat = np.asarray(harness.values_of(store.get(small)), dtype="float64").ravel()
    expected = float(flat.mean())
    for backend, step in (("py", "py"), ("np", "np")):
        harness.oracle(
            store,
            VERTICAL,
            "mean",
            f"example_{backend}",
            got=run.results[step],
            expected=expected,
            reference="numpy.ndarray.mean",
            for_="every engine answers the same question the same way, or it is a failed backend",
        )

    for size in (64, 4096, 65536):
        values = [[float(x)] for x in range(size)]
        part = {"for": "bench input", "shape": [size, 1], "values": values}
        for backend in ("py", "np"):
            harness.bench(
                store,
                VERTICAL,
                "mean",
                backend,
                size,
                lambda part=part, backend=backend: mean({"data": part, "backend": backend}),
                n=5,
                for_="where the engine boundary actually pays",
                inputs={"size": size},
            )

    harness.bracket(
        store,
        VERTICAL,
        "example_mean",
        criteria=[
            {"name": "correctness", "how": "the oracle part for this engine passes", "direction": "higher", "weight": 2.0},
            {"name": "speed", "how": "wall_ms_median of the largest benchmark", "direction": "lower"},
            {"name": "clarity", "how": "lines and docstring", "direction": "higher"},
        ],
        candidates=[
            {"branch": "engine_py", "calc": "fn.brain.backend.mean", "address": harness.result_address(VERTICAL, "mean", "example_py")},
            {"branch": "engine_np", "calc": "fn.brain.backend.mean", "address": harness.result_address(VERTICAL, "mean", "example_np")},
        ],
        for_="the shape of every tournament in this sprint, small enough to read",
    )
    harness.judge(store, VERTICAL, "example_mean", "reader", "engine_py", {"correctness": 1.0, "speed": 40.0, "clarity": 1.0}, "pure python, no import, slow past a few thousand")
    harness.judge(store, VERTICAL, "example_mean", "reader", "engine_np", {"correctness": 1.0, "speed": 1.0, "clarity": 1.0}, "one call, fast, needs the dependency")
    harness.decide(store, VERTICAL, "example_mean")
    harness.refine(store, VERTICAL, "example_mean", "the winner is the facade's default at size; the loser stays as the reference engine")

    harness.finding(
        store,
        VERTICAL,
        "harness_carries",
        "strength",
        "the facade shape (one Calculation, args['backend']) plus an oracle part per engine made 'a backend that changes semantics is a failed backend' a mechanical check rather than a habit",
        for_="every vertical adds an engine without re-arguing correctness",
    )
    harness.map_part(
        store,
        VERTICAL,
        built=[harness.bracket_address(VERTICAL, "example_mean")],
        stubbed=[{"address": "px.exp.brain.result.backend.*", "why": "the facade ops land as their own neat tasks after the harness"}],
        next_=[{"what": "fn.brain.backend.<op> for matmul, solve, lstsq, eig/svd, sort/select-k, distances, histogram, cumsum, fft", "for": "the stats and ml verticals, which cannot start without them"}],
        for_="what the backend vertical has, and what the other two are waiting on",
    )
    return store
