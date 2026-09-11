"""three tournaments, decided by the evidence Parts and not by anyone's taste.

each one: two or three branches that answer the same question, criteria written
into the bracket Part BEFORE anything is judged, a judge that did not build any
branch, a winner decided from the recorded scores by the recorded criteria, and
the winner refined. losers stay in the store as candidates; nothing is deleted.

the judge here is `evidence`: it reads the oracle Part (correctness), the
benchmark Part at the largest size (speed) and the branch's own source (clarity:
lines, and whether it says what it does). a mechanical judge cannot be talked
into anything, and every score it gives points at the Part it came from. that is
the strongest judge available in this session - there was no model worker to
spawn - and the bracket records which judge scored it either way.

`python -m experiments.brain.backend.tournament` (from pyto/) rebuilds all three;
`test_tournament.py` rebuilds them into a temporary store and checks that each
one still decides.
"""

from __future__ import annotations

import base64
import heapq
import inspect
import json
import math
import time
from typing import Any, Callable

from experiments.brain import harness
from experiments.brain.backend import cases as case_module
from experiments.brain.backend import ops

VERTICAL = "backend"
JUDGE = "evidence"

# three points a million from the origin and a millionth of a unit apart: the input on which
# |a|^2 + |b|^2 - 2 a.b has no significant digits left, by construction and not by luck.
CANCELLING = [
    [1_000_000.0, 1_000_000.0, 1_000_000.0],
    [1_000_000.000001, 1_000_000.0, 1_000_000.0],
    [1_000_000.0, 1_000_000.000002, 1_000_000.0],
]

CRITERIA = [
    {"name": "correctness", "how": "the branch's oracle Part passes against the reference", "direction": "higher", "weight": 3.0},
    {"name": "speed", "how": "wall_ms_median of the branch's benchmark Part at the largest size", "direction": "lower", "weight": 2.0},
    {"name": "clarity", "how": "1 for a docstring that says what it does, plus 1 minus lines/40", "direction": "higher", "weight": 1.0},
]


def clarity(fn: Callable) -> float:
    """a branch is read more often than it is run; this is that, as a number."""
    source = inspect.getsource(fn).splitlines()
    lines = len([one for one in source if one.strip() and not one.strip().startswith("#")])
    return (1.0 if (fn.__doc__ or "").strip() else 0.0) + max(0.0, 1.0 - lines / 40.0)


# --- (a) pairwise euclidean distance -------------------------------------------


def pairwise_py_gram_unguarded(args):
    """the gram expansion, straight: |a|^2 + |b|^2 - 2 a.b, norms precomputed once.

    it is the obvious pure-python speedup - one dot product per pair instead of a
    python loop over the coordinates - and it is a failed backend. Where two
    points are close the subtraction cancels, and the square root turns what is
    left of the mantissa into a number that is wrong in its eighth digit. Its
    oracle Part records exactly that; the candidate in the bracket is the guarded
    one below.
    """
    a = ops.matrix(args["a"])
    b = ops.matrix(args["b"]) if args.get("b") is not None else a
    na = [math.fsum(x * x for x in row) for row in a]
    nb = [math.fsum(y * y for y in row) for row in b]
    out = []
    for row, norm in zip(a, na):
        line = []
        for other, other_norm in zip(b, nb):
            gap = norm + other_norm - 2.0 * sum(map(float.__mul__, row, other))
            line.append(math.sqrt(gap) if gap > 0.0 else 0.0)
        out.append(line)
    return ops.shaped(out)


def pairwise_py_gram(args):
    """the gram expansion, guarded: the cheap formula, except where it cancels.

    the guard is one comparison per pair: when what is left after the
    subtraction is small next to the norms that produced it, the digits that
    survived are noise, so that pair is recomputed from the coordinates. Well
    separated points - almost all of them - never take the slow path.
    """
    a = ops.matrix(args["a"])
    b = ops.matrix(args["b"]) if args.get("b") is not None else a
    na = [math.fsum(x * x for x in row) for row in a]
    nb = [math.fsum(y * y for y in row) for row in b]
    out = []
    for row, norm in zip(a, na):
        line = []
        for other, other_norm in zip(b, nb):
            scale = norm + other_norm
            gap = scale - 2.0 * sum(map(float.__mul__, row, other))
            if gap <= 1e-8 * scale:
                gap = math.fsum((x - y) ** 2 for x, y in zip(row, other))
            line.append(math.sqrt(gap) if gap > 0.0 else 0.0)
        out.append(line)
    return ops.shaped(out)


def pairwise_py_naive(args):
    """the coordinate loop, straight off the definition. the readable reference."""
    return ops.call("pairwise", dict(args, backend="py"))


def pairwise_np(args):
    """numpy broadcasting: one (n, m, d) difference array, squared and summed."""
    return ops.call("pairwise", dict(args, backend="np"))


def pairwise_sp(args):
    """scipy.spatial.distance.cdist, which is the compiled loop written once."""
    return ops.call("pairwise", dict(args, backend="sp"))


# --- (b) top-k selection --------------------------------------------------------


def top_k_py_sorted(args):
    """sort all n, keep k. the obvious thing, and O(n log n) whatever k is."""
    return ops.call("select_k", dict(args, backend="py"))


def top_k_py_heap(args):
    """heapq.nlargest over (value, -index), which is O(n log k) and keeps the tie rule."""
    values = ops.vector(args["values"])
    k = int(args["k"])
    largest = bool(args.get("largest", True))
    keyed = [(value, -index) for index, value in enumerate(values)]
    picked = heapq.nlargest(k, keyed) if largest else heapq.nsmallest(k, [(value, index) for index, value in enumerate(values)])
    order = [(-one[1] if largest else one[1]) for one in picked]
    return {"values": [values[i] for i in order], "indices": order}


def top_k_np_argpartition(args):
    """np.argpartition to k, then order only those k. O(n) plus k log k."""
    return ops.call("select_k", dict(args, backend="np"))


# --- (c) how a large array sits in the store -----------------------------------


def store_nested(matrix: list[list[float]]) -> dict:
    """rows as nested json lists: what the contract's dataset Part already says."""
    return {"shape": [len(matrix), len(matrix[0])], "values": [list(row) for row in matrix]}


def store_nested_back(part: dict) -> list[list[float]]:
    return [list(row) for row in part["values"]]


def store_flat(matrix: list[list[float]]) -> dict:
    """one flat list plus the shape: the same numbers with n-1 fewer json arrays."""
    return {"shape": [len(matrix), len(matrix[0])], "flat": [cell for row in matrix for cell in row]}


def store_flat_back(part: dict) -> list[list[float]]:
    width = part["shape"][1]
    flat = part["flat"]
    return [flat[i * width:(i + 1) * width] for i in range(part["shape"][0])]


def store_b64(matrix: list[list[float]]) -> dict:
    """the float64 bytes, base64'd: exact, compact, and unreadable to a human.

    it is also the only one of the three that survives a value json cannot hold
    (a nan, an inf) without changing it.
    """
    import numpy as np

    array = np.asarray(matrix, dtype="float64")
    return {"shape": list(array.shape), "b64": base64.b64encode(array.tobytes()).decode("ascii")}


def store_b64_back(part: dict) -> list[list[float]]:
    import numpy as np

    return np.frombuffer(base64.b64decode(part["b64"]), dtype="float64").reshape(part["shape"]).tolist()


REPRESENTATIONS = {
    "nested_lists": (store_nested, store_nested_back),
    "flat_and_shape": (store_flat, store_flat_back),
    "base64_float64": (store_b64, store_b64_back),
}


# --- running the three ----------------------------------------------------------


def _time(fn, n=5) -> float:
    samples = []
    for _ in range(n):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000.0)
    samples.sort()
    return samples[len(samples) // 2]


def run_pairwise(store) -> str:
    import numpy as np
    from scipy.spatial.distance import cdist

    branches = {"py_gram": pairwise_py_gram, "np_broadcast": pairwise_np, "sp_cdist": pairwise_sp}
    sizes = (16, 64, 192)
    inputs = {size: {"a": case_module.draw((size, 3), seed=case_module.SEED + size).tolist()} for size in sizes}
    # `cancelling` is not a draw: it is three points a million units from the origin and a
    # millionth of a unit apart, which makes |a|^2 + |b|^2 - 2 a.b a subtraction of two numbers
    # near 3e12 whose difference is near 1e-12. Float64 has no digits left there, whatever BLAS
    # or numpy is underneath, so the unguarded expansion is wrong on it by construction rather
    # than by luck - and the guard, which recomputes from the coordinates when what is left is
    # small next to the norms that produced it, is right on it for the same reason.
    inputs["cancelling"] = {"a": CANCELLING}
    cases = tuple(sizes) + ("cancelling",)
    expected = {case: {"shape": [len(args["a"]), len(args["a"])],
                       "values": cdist(np.asarray(args["a"]), np.asarray(args["a"])).tolist()}
                for case, args in inputs.items()}
    for case in cases:
        harness.oracle(
            store, VERTICAL, "pairwise_tournament", f"py_gram_unguarded_{case}",
            got=pairwise_py_gram_unguarded(dict(inputs[case])), expected=expected[case],
            reference="scipy.spatial.distance.cdist", tolerance=1e-8,
            for_="the record of why the guard is there: the unguarded gram expansion is a failed backend",
        )
    scores = {}
    for branch, fn in branches.items():
        passed = all(
            harness.oracle(
                store, VERTICAL, "pairwise_tournament", f"{branch}_{case}",
                got=fn(dict(inputs[case])), expected=expected[case], reference="scipy.spatial.distance.cdist",
                tolerance=1e-8, for_="a candidate that is not correct cannot win on speed",
            )
            for case in cases
        )
        for size in sizes:
            harness.bench(
                store, VERTICAL, "pairwise_tournament", branch, size,
                lambda fn=fn, size=size: fn(dict(inputs[size])), n=5,
                for_="the tournament's speed criterion", inputs={"branch_input": size},
            )
        store.put(
            f"px.exp.brain.result.backend.pairwise_tournament.{branch}",
            {"for": "the candidate's own answer, so the bracket's address resolves to a Part",
             "answer": harness.outline(fn(dict(inputs[sizes[0]]))), "size": sizes[0]},
        )
        scores[branch] = {
            "correctness": 1.0 if passed else 0.0,
            "speed": store.get(harness.bench_address(VERTICAL, "pairwise_tournament", branch, sizes[-1]))["wall_ms_median"],
            "clarity": clarity(fn),
        }
    return _bracket(store, "pairwise", branches, scores,
                    "192 points in 3 dimensions is small enough that the python-level loop still shows, and large enough that it loses")


def run_top_k(store) -> str:
    branches = {"py_sorted": top_k_py_sorted, "py_heap": top_k_py_heap, "np_argpartition": top_k_np_argpartition}
    sizes = (1024, 16384, 131072)
    inputs = {size: {"values": case_module.draw((size,), seed=case_module.SEED + size).tolist(), "k": 10} for size in sizes}
    expected = {
        size: (lambda values, k: {"values": [values[i] for i in sorted(range(len(values)), key=lambda i: (-values[i], i))[:k]],
                                  "indices": sorted(range(len(values)), key=lambda i: (-values[i], i))[:k]})(args["values"], args["k"])
        for size, args in inputs.items()
    }
    scores = {}
    for branch, fn in branches.items():
        passed = all(
            harness.oracle(
                store, VERTICAL, "top_k_tournament", f"{branch}_{size}",
                got=fn(dict(inputs[size])), expected=expected[size], reference="a full stable sort with ties broken by index",
                for_="k out of n is only faster if it is the same k",
            )
            for size in sizes
        )
        for size in sizes:
            harness.bench(
                store, VERTICAL, "top_k_tournament", branch, size,
                lambda fn=fn, size=size: fn(dict(inputs[size])), n=5,
                for_="the tournament's speed criterion", inputs={"branch_input": size},
            )
        store.put(
            f"px.exp.brain.result.backend.top_k_tournament.{branch}",
            {"for": "the candidate's own answer, so the bracket's address resolves to a Part",
             "answer": harness.outline(fn(dict(inputs[sizes[0]]))), "size": sizes[0]},
        )
        scores[branch] = {
            "correctness": 1.0 if passed else 0.0,
            "speed": store.get(harness.bench_address(VERTICAL, "top_k_tournament", branch, sizes[-1]))["wall_ms_median"],
            "clarity": clarity(fn),
        }
    return _bracket(store, "top_k", branches, scores,
                    "k=10 out of 131072: the case where an O(n log n) sort is doing almost all of its work for nothing")


def run_array_store(store) -> str:
    """the third tournament is about the store itself, not about arithmetic.

    same matrix in, same matrix out, exactly: the three candidates differ only in
    what the Part looks like, so the criteria are bytes on disk, the round trip,
    and what it costs to digest - which is what `run_record` does to every Part.
    """
    matrix = case_module.draw((256, 256), seed=case_module.SEED).tolist()
    scores = {}
    branches = {}
    for branch, (encode, decode) in REPRESENTATIONS.items():
        branches[branch] = encode
        part = encode(matrix)
        exact = decode(part) == matrix
        harness.oracle(
            store, VERTICAL, "array_store_tournament", branch,
            got={"exact_round_trip": exact, "shape": part["shape"]},
            expected={"exact_round_trip": True, "shape": [256, 256]},
            reference="the same matrix, cell for cell",
            for_="a representation that loses a digit is not a representation",
        )
        text = json.dumps(part, sort_keys=True, separators=(",", ":"))
        harness.bench(store, VERTICAL, "array_store_tournament", branch, "encode",
                      lambda encode=encode: encode(matrix), n=5, for_="what it costs to put a 256x256 matrix in the store",
                      inputs={"branch_input": "256x256"})
        harness.bench(store, VERTICAL, "array_store_tournament", branch, "decode",
                      lambda decode=decode, part=part: decode(part), n=5, for_="what it costs to read one back",
                      inputs={"branch_input": "256x256"})
        harness.bench(store, VERTICAL, "array_store_tournament", branch, "digest",
                      lambda part=part: harness.digest(part), n=5, for_="what every run record pays per Part",
                      inputs={"branch_input": "256x256"})
        store.put(
            f"px.exp.brain.result.backend.array_store_tournament.{branch}",
            {"for": "the shape of the candidate, measured", "bytes": len(text.encode("utf-8")), "shape": part["shape"], "exact_round_trip": exact},
        )
        scores[branch] = {
            "correctness": 1.0 if exact else 0.0,
            "bytes": float(len(text.encode("utf-8"))),
            "speed": sum(store.get(harness.bench_address(VERTICAL, "array_store_tournament", branch, which))["wall_ms_median"]
                         for which in ("encode", "decode", "digest")),
            "clarity": clarity(encode),
        }
    criteria = CRITERIA + [{"name": "bytes", "how": "the Part as canonical json, in bytes", "direction": "lower", "weight": 2.0}]
    return _bracket(store, "array_store", branches, scores,
                    "a 256x256 float64 matrix is 65536 numbers; the store holds it as json and the record digests it",
                    criteria=criteria)


def _bracket(store, problem: str, branches: dict, scores: dict, for_: str, criteria=None) -> str:
    address = harness.bracket(
        store, VERTICAL, problem, criteria or CRITERIA,
        [{"branch": branch, "calc": f"fn.brain.backend.{problem}", "address": f"px.exp.brain.result.backend.{problem}_tournament.{branch}",
          "note": (fn.__doc__ or "").strip().splitlines()[0] if fn.__doc__ else ""}
         for branch, fn in branches.items()],
        for_=for_,
    )
    for branch, row in scores.items():
        harness.judge(store, VERTICAL, problem, JUDGE, branch, row,
                      "scored from this branch's oracle and benchmark Parts and its own source; no branch judged itself")
    decided = harness.decide(store, VERTICAL, problem)
    harness.refine(
        store, VERTICAL, problem,
        f"the winner {decided['winner']} is what fn.brain.backend dispatches to at size; the losers stay as candidates "
        "and as the readable reference the oracle checks the winner against",
        address=address,
    )
    return address


def build(store) -> dict:
    return {"pairwise": run_pairwise(store), "top_k": run_top_k(store), "array_store": run_array_store(store)}


def main() -> int:
    store = harness.Store(commit=True)
    store.load_store()
    built = build(store)
    store.save(VERTICAL)
    for problem, address in built.items():
        part = store.get(address)
        print(f"{problem:12} winner {part['winner']:16} of {', '.join(one['branch'] for one in part['candidates'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
