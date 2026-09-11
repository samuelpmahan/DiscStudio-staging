"""tournaments: brackets whose criteria are written before anyone scores.

`python -m experiments.brain.ml.tournament` (from pyto/) rebuilds every bracket
from its candidates, so the verdict is re-runnable rather than remembered. a
candidate is a named branch plus the calculation and the args that spell it; the
evidence a judge reads is the candidate's own oracle Part and benchmark Part, and
nothing else -- a candidate whose oracle failed cannot win on speed.
"""

from __future__ import annotations

import inspect
import math

from . import calcs, core, parts

VERTICAL = "ml"

#: the criteria, in the shape the harness records them. weight and direction are
#: part of the criterion, so `decide` needs nothing that is not in the bracket.
CRITERIA = [
    {"name": "correct", "weight": 3.0, "direction": "higher",
     "note": "1 when this candidate's oracle part passed against the reference, 0 otherwise"},
    {"name": "speed_band", "weight": 1.5, "direction": "lower",
     "note": "the candidate's band, from the fastest sample of every benchmark part in this bracket: sorted, then "
             "cut wherever the next is more than BAND times the fastest in the band, and numbered "
             "from the fastest. a band rather than a time because a linear score lets one slow branch "
             "compress the fast ones into nothing, and because two branches within 40% of each other are "
             "the same speed on this machine tonight -- letting that decide a winner makes the bracket "
             "un-re-runnable, which is the one thing a bracket has to be"},
    {"name": "source_lines", "weight": 0.5, "direction": "lower",
     "note": "lines of the function the candidate runs: the clarity the contract asks for"},
    {"name": "documented", "weight": 0.5, "direction": "higher",
     "note": "1 when that function carries a docstring"},
]

JUDGE = "recorded-criteria-scorer"

#: two medians within this factor of each other are the same speed, and share a band.
BAND = 1.4


def speed_bands(store, candidates):
    """every candidate's band index, from the benchmark parts this bracket recorded.

    the minimum of the samples, not the median: interference only ever makes a run
    slower, so the fastest sample is the least contaminated estimate of the branch,
    and the median moves under a machine that is also running someone else's suite.
    """
    medians = {c["branch"]: float(store.get(c["bench"])["wall_ms_min"]) for c in candidates}
    order = sorted(medians, key=lambda branch: (medians[branch], branch))
    bands, band, floor_ms = {}, 0, medians[order[0]]
    for branch in order:
        if medians[branch] > floor_ms * BAND:
            band += 1
            floor_ms = medians[branch]
        bands[branch] = band
    return bands


def source_size(fn):
    """(lines, has a docstring) of the function a candidate actually runs."""
    try:
        source = inspect.getsource(fn)
    except (OSError, TypeError):  # pragma: no cover - not reachable in the repository
        return 0, 0
    lines = [line for line in source.splitlines() if line.strip() and not line.strip().startswith("#")]
    return len(lines), 1 if (fn.__doc__ or "").strip() else 0


def score(store, candidate, bands):
    """every number a judge is allowed to use, read back out of the store."""
    oracle = store.get(candidate["oracle"]) if store.has(candidate["oracle"]) else {"pass": False}
    lines, documented = source_size(candidate["fn"])
    return {
        "correct": 1.0 if oracle.get("pass") else 0.0,
        "speed_band": float(bands[candidate["branch"]]),
        "source_lines": float(lines),
        "documented": float(documented),
    }


def hold(store, problem, for_, candidates, note_for):
    """open the bracket, score every candidate by the recorded criteria, decide, refine."""
    parts.bracket(
        store, VERTICAL, problem, CRITERIA,
        [{"branch": c["branch"], "calc": c["calc"], "address": c["bench"], "note": c["note"]} for c in candidates],
        for_,
    )
    bands = speed_bands(store, candidates)
    for candidate in candidates:
        parts.judge(store, VERTICAL, problem, JUDGE, candidate["branch"],
                    score(store, candidate, bands), candidate["note"])
    decided = parts.decide(store, VERTICAL, problem)
    parts.refine(store, VERTICAL, problem, note_for(decided["winner"]), decided["candidates"][0]["address"])
    return decided


# --- the brackets ------------------------------------------------------------

BRACKETS = []


def bracket_builder(fn):
    BRACKETS.append(fn)
    return fn


@bracket_builder
def logistic_ascent(store):
    """how a logistic regression should climb: a step it can afford, or a step that curves.

    the three branches solve the same problem on the same data: full-batch gradient
    descent, newton/irls in pure python, and newton/irls through numpy. the oracle
    for all three is scipy minimising the same penalised negative log likelihood.
    """
    from scipy import optimize

    import numpy as np

    from . import classify

    data = calcs.call("synthetic_classification", {"seed": 61, "n": 400, "d": 6, "k": 2, "spread": 2.2})
    # the recipe, not the rows: a seeded dataset is fully described by its calculation and
    # its args, and 400x7 floats in the store would be 50kb of something regenerable exactly.
    store.put("px.exp.brain.data.ml.logistic_bracket", {
        "for": "the one problem every branch of the logistic bracket solves",
        "recipe": {"calc": "fn.brain.ml.synthetic_classification",
                   "args": {"seed": 61, "n": 400, "d": 6, "k": 2, "spread": 2.2}},
        "columns": core.columns_of(data),
        "shape": [len(core.as_rows(data)), len(core.columns_of(data))],
    })
    matrix, targets, _ = core.xy(data, "label")
    design = np.hstack([np.ones((len(matrix), 1)), np.asarray(matrix)])
    y = np.asarray(targets)
    l2 = 1.0

    def loss(w):
        z = design @ w
        return float(np.sum(np.logaddexp(0.0, z) - y * z) + 0.5 * l2 * float(w[1:] @ w[1:]))

    reference = optimize.minimize(
        loss, np.zeros(design.shape[1]), method="L-BFGS-B",
        options={"ftol": 1e-16, "gtol": 1e-14, "maxiter": 20000},
    ).x.tolist()

    branches = [
        {"branch": "gd-np", "fn": classify._binary_gd_np, "method": "gd", "backend": "np",
         "args": {"lr": 0.5, "epochs": 8000},
         "note": "one cheap step per pass, many passes; no matrix to solve"},
        {"branch": "newton-py", "fn": classify._binary_newton, "method": "newton", "backend": "py",
         "args": {"epochs": 30},
         "note": "the curvature is paid for in full: an n-by-d-by-d build and a solve per step"},
        {"branch": "newton-np", "fn": classify._binary_newton_np, "method": "newton", "backend": "np",
         "args": {"epochs": 30},
         "note": "the same steps, with the hessian built by one weighted matmul"},
    ]
    candidates = []
    for branch in branches:
        args = dict(branch["args"], data=data, target="label", backend=branch["backend"],
                    method=branch["method"], l2=l2)
        model = calcs.call("logreg_fit", args)
        case = f"bracket_{branch['branch'].replace('-', '_')}"
        parts.result(store, VERTICAL, "logreg", case, model)
        parts.oracle(
            store, VERTICAL, "logreg_fit", case,
            [model["intercepts"][0]] + model["coefs"][0], reference,
            "scipy.optimize.minimize on the penalised negative log likelihood", 5e-3,
            "a faster climb that stops somewhere else has not solved the same problem",
        )
        parts.bench(
            store, VERTICAL, "logreg_fit", branch["branch"], "bracket_n400_d6",
            lambda args=args: calcs.call("logreg_fit", args), 3,
            "the same 400 rows and the same penalty for every branch",
        )
        candidates.append({
            "branch": branch["branch"],
            "calc": "fn.brain.ml.logreg_fit",
            "fn": branch["fn"],
            "oracle": parts.H.oracle_address(VERTICAL, "logreg_fit", case),
            "bench": parts.H.bench_address(VERTICAL, "logreg_fit", branch["branch"], "bracket_n400_d6"),
            "note": branch["note"],
        })
    return hold(
        store, "logistic_ascent",
        "gradient descent needs no linear algebra; newton needs a solve per step. which is worth it, on the evidence",
        candidates,
        lambda winner: (
            f"{winner} wins on the recorded criteria and is what fn.brain.ml.logreg_fit defaults to "
            "(method='newton', backend chosen by args); the losing branches stay reachable through the "
            "same calculation's args, and their oracles and benchmarks stay in the store as the evidence"
        ),
    )


@bracket_builder
def split_search(store):
    """how a tree should look for a split: every midpoint, or a fixed number of bins.

    the sorting branch is exact and pays O(n log n) per feature per node. the
    histogram branches bin first and scan at most bins-1 thresholds, which is
    cheaper and approximate. the oracle for every branch is the held-out accuracy
    of the exact tree: a branch that is faster and materially worse is not a backend.
    """
    from . import trees

    data = calcs.call("synthetic_classification", {"seed": 71, "n": 1200, "d": 6, "k": 3, "spread": 1.5})
    store.put("px.exp.brain.data.ml.split_search_bracket", {
        "for": "the one problem every branch of the split-search bracket grows a tree on",
        "recipe": {"calc": "fn.brain.ml.synthetic_classification",
                   "args": {"seed": 71, "n": 1200, "d": 6, "k": 3, "spread": 1.5}},
        "columns": core.columns_of(data),
        "shape": [len(core.as_rows(data)), len(core.columns_of(data))],
    })
    split = calcs.call("train_test_split", {"data": data, "seed": 71, "test_size": 0.3, "stratify": "label"})
    train, test = core.take(data, split["train_index"]), core.take(data, split["test_index"])
    truth = [row[-1] for row in core.as_rows(test)]

    def accuracy(model):
        got = calcs.call("tree_predict", {"model": model, "data": test})["labels"]
        return calcs.call("classification_metrics", {"y_true": truth, "y_pred": got})["accuracy"]

    exact = calcs.call("tree_fit", {"data": train, "target": "label", "max_depth": 6, "search": "sort"})
    reference = accuracy(exact)

    branches = [
        {"branch": "sort", "fn": trees._best_split_sort, "args": {"search": "sort"},
         "note": "one sort per feature per node, then every midpoint between distinct values"},
        {"branch": "hist-32", "fn": trees._best_split_hist, "args": {"search": "hist", "bins": 32},
         "note": "32 equal-width bins per feature: no sort, at most 31 thresholds"},
        {"branch": "hist-256", "fn": trees._best_split_hist, "args": {"search": "hist", "bins": 256},
         "note": "the same bin scan, eight times finer: nearer the exact threshold, still no sort"},
    ]
    candidates = []
    for branch in branches:
        args = dict(branch["args"], data=train, target="label", max_depth=6)
        model = calcs.call("tree_fit", args)
        case = f"bracket_{branch['branch'].replace('-', '_')}"
        parts.result(store, VERTICAL, "tree", case, {
            "for": f"the tree the {branch['branch']} search grew",
            "model": "tree", "search": model["search"], "nodes": model["nodes"],
            "depth": model["depth"], "root_feature": model["root"].get("feature"),
            "root_threshold": model["root"].get("threshold"), "accuracy": accuracy(model),
        })
        parts.oracle(
            store, VERTICAL, "tree_fit", case,
            accuracy(model) >= reference - 0.03, True,
            "the held-out accuracy of the exact (sorting) search on the same split", 0.0,
            "an approximate split search earns its speed only if the tree it grows is as good",
        )
        parts.bench(
            store, VERTICAL, "tree_fit", branch["branch"], "bracket_n840_d6_depth6",
            lambda args=args: calcs.call("tree_fit", args), 3,
            "the same training rows and the same depth for every branch",
        )
        candidates.append({
            "branch": branch["branch"], "calc": "fn.brain.ml.tree_fit", "fn": branch["fn"],
            "oracle": parts.H.oracle_address(VERTICAL, "tree_fit", case),
            "bench": parts.H.bench_address(VERTICAL, "tree_fit", branch["branch"], "bracket_n840_d6_depth6"),
            "note": branch["note"],
        })
    return hold(
        store, "split_search",
        "the split search is the whole cost of a tree; exact or binned is the one decision that changes it",
        candidates,
        lambda winner: (
            f"{winner} wins on the recorded criteria; fn.brain.ml.tree_fit keeps search='sort' as its "
            "default because it is the reference every other branch is oracled against, and reaches the "
            "winner through args (search, bins) so the forest and the boosting can take it by name"
        ),
    )


@bracket_builder
def kmeans_assignment(store):
    """the assignment step of k-means, three ways, with the init held fixed by one seed.

    every branch runs lloyd's iteration from the same seeded k-means++ start, so the
    only difference is how the point-to-centre distances are computed: python loops,
    a broadcast subtraction, or the |a-b|^2 = |a|^2 - 2ab + |b|^2 identity as one matmul.
    the oracle is the py branch's labelling, which is the reference by definition.
    """
    from . import unsup

    blobs = calcs.call("synthetic_blobs", {"seed": 73, "n": 900, "k": 6, "d": 8, "spread": 0.9})
    features = core.dataset("the blob features alone", core.columns_of(blobs)[:-1],
                            [row[:-1] for row in core.as_rows(blobs)])
    store.put("px.exp.brain.data.ml.kmeans_bracket", {
        "for": "the one problem every branch of the k-means bracket clusters",
        "recipe": {"calc": "fn.brain.ml.synthetic_blobs",
                   "args": {"seed": 73, "n": 900, "k": 6, "d": 8, "spread": 0.9}},
        "columns": core.columns_of(features),
        "shape": [len(core.as_rows(features)), len(core.columns_of(features))],
    })
    reference = calcs.call("kmeans", {"data": features, "k": 6, "seed": 73, "backend": "py"})
    branches = [
        {"branch": "py", "fn": unsup._assign_py, "note": "the reference: one python loop per point per centre"},
        {"branch": "np", "fn": unsup._assign_np, "note": "one broadcast subtraction: an n by k by d array in memory"},
        {"branch": "gram", "fn": unsup._assign_gram, "note": "the squared-distance identity: one n by d by k matmul, no cube"},
    ]
    candidates = []
    for branch in branches:
        args = {"data": features, "k": 6, "seed": 73, "backend": branch["branch"]}
        got = calcs.call("kmeans", args)
        case = f"bracket_{branch['branch']}"
        parts.result(store, VERTICAL, "kmeans", case, {
            "for": f"what the {branch['branch']} assignment found",
            "backend": got["backend"], "k": got["k"], "seed": got["seed"],
            "seeded_from": got["seeded_from"], "inertia": got["inertia"], "iters": got["iters"],
        })
        parts.oracle(
            store, VERTICAL, "kmeans", case,
            {"labels": got["labels"], "inertia": got["inertia"]},
            {"labels": reference["labels"], "inertia": reference["inertia"]},
            "the py backend of the same calculation, from the same seed", 1e-9,
            "the seed fixes the init, so any difference between backends is a difference in semantics",
        )
        parts.bench(
            store, VERTICAL, "kmeans", branch["branch"], "bracket_n900_k6_d8",
            lambda args=args: calcs.call("kmeans", args), 3,
            "900 points, 6 centres, 8 columns: the assignment step is nearly all of the work",
        )
        candidates.append({
            "branch": branch["branch"], "calc": "fn.brain.ml.kmeans", "fn": branch["fn"],
            "oracle": parts.H.oracle_address(VERTICAL, "kmeans", case),
            "bench": parts.H.bench_address(VERTICAL, "kmeans", branch["branch"], "bracket_n900_k6_d8"),
            "note": branch["note"],
        })
    return hold(
        store, "kmeans_assignment",
        "every iteration of k-means is one distance matrix; which spelling of it deserves the default",
        candidates,
        lambda winner: (
            f"{winner} wins on the recorded criteria and is what fn.brain.ml.kmeans should default to; "
            "the py branch stays as the reference every oracle here is written against, and the same "
            "identity belongs in a shared pairwise-distance calculation rather than in three verticals"
        ),
    )


@bracket_builder
def pairwise_spelling(store):
    """the one n-by-n matrix four calculations need, five ways.

    three of the branches are this vertical's own (a python loop, a broadcast
    subtraction, the squared-distance identity) and two are the backend vertical's
    facade, fn.brain.backend.pairwise, on its np and its scipy engines. the oracle
    for every branch is scipy's cdist, which only one of them calls.
    """
    from scipy.spatial import distance as sp_distance

    import numpy as np

    from . import distance

    blobs = calcs.call("synthetic_blobs", {"seed": 121, "n": 300, "k": 5, "d": 8, "spread": 0.9})
    rows = [row[:-1] for row in core.as_rows(blobs)]
    store.put("px.exp.brain.data.ml.pairwise_bracket", {
        "for": "the one matrix every branch of the pairwise bracket computes",
        "recipe": {"calc": "fn.brain.ml.synthetic_blobs",
                   "args": {"seed": 121, "n": 300, "k": 5, "d": 8, "spread": 0.9}},
        "columns": core.columns_of(blobs)[:-1],
        "shape": [len(rows), len(rows[0])],
    })
    reference = sp_distance.cdist(np.asarray(rows), np.asarray(rows), metric="euclidean").tolist()
    notes = {
        "py": "one python loop per pair, with fsum: the reference, and the only one with no array in it",
        "np": "one broadcast subtraction: an n by n by d array in memory, so 300 rows is 720 thousand floats",
        "gram": "the squared-distance identity: one matmul, no cube, and the diagonal pinned to the zero it is",
        "backend_np": "fn.brain.backend.pairwise on its np engine: the same shape, owned by the backend vertical",
        "backend_sp": "fn.brain.backend.pairwise on its scipy engine: cdist, which is the oracle's own routine",
    }
    candidates = []
    for branch in distance.BACKENDS:
        got = distance.pairwise(rows, metric="euclidean", backend=branch)
        case = f"bracket_{branch}"
        parts.result(store, VERTICAL, "pairwise", case, {
            "for": f"what the {branch} spelling computed",
            "backend": branch, "shape": [len(got), len(got[0])],
            "first_row": got[0][:8], "trace": math.fsum(got[i][i] for i in range(len(got))),
        })
        parts.oracle(
            store, VERTICAL, "pairwise", case,
            got[:40], [row[:len(got)] for row in reference[:40]],
            "scipy.spatial.distance.cdist on the same rows", 1e-9,
            "four calculations read this matrix; a spelling that is off by 1e-7 moves a k=1 vote",
        )
        parts.bench(
            store, VERTICAL, "pairwise", branch, "bracket_n300_d8",
            lambda branch=branch: distance.pairwise(rows, metric="euclidean", backend=branch), 5,
            "300 rows and 8 columns: the same ninety thousand pairs, five times, for every branch",
        )
        candidates.append({
            "branch": branch, "calc": "fn.brain.ml.pairwise", "fn": getattr(distance, "_" + branch, distance.pairwise),
            "oracle": parts.H.oracle_address(VERTICAL, "pairwise", case),
            "bench": parts.H.bench_address(VERTICAL, "pairwise", branch, "bracket_n300_d8"),
            "note": notes[branch],
        })
    return hold(
        store, "pairwise_spelling",
        "knn, silhouette, k-means and dbscan all read one n-by-n matrix; this decides which spelling computes it",
        candidates,
        lambda winner: (
            f"{winner} wins on the recorded criteria. the ml vertical keeps py as its default because it is "
            "the reference every oracle here is written against, and fn.brain.ml.pairwise reaches every other "
            "branch through args['backend'] -- including the backend vertical's own engines, which is the point: "
            "this vertical no longer owns the primitive, it calls it"
        ),
    )


def run(store=None):
    store = store or parts.Store(VERTICAL)
    return {fn.__name__: fn(store) for fn in BRACKETS}, store


def main():
    decided, store = run()
    for name, part in decided.items():
        print(f"{part['problem']}: winner {part['winner']}")
        for branch, total in sorted(part["totals"].items(), key=lambda kv: -kv[1]):
            print(f"  {branch:<12} {total:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
