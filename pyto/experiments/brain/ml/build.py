"""build the ml vertical's store: datasets, results, oracles, benchmarks, findings, map.

`python -m experiments.brain.ml.build` (from pyto/) writes
  experiments/brain/store/ml.json     every part this vertical produced
  experiments/brain/records/ml.*.json the run record of every PCR it ran
and the suite runs the same code, so the store in the landing is the store the
tests verified. later slices append to SECTIONS; nothing here is ever deleted.
"""

from __future__ import annotations

import numpy as np
from pyto import Part

from . import calcs, core, linear, metrics, parts, resample

VERTICAL = "ml"
SECTIONS = []


def section(fn):
    SECTIONS.append(fn)
    return fn


def D(name):
    return Part(f"px.exp.brain.data.ml.{name}")


def R(calc, case):
    return Part(f"px.exp.brain.result.ml.{calc}.{case}")


# --- the supervised regression pipeline, as one observed PCR ------------------


@section
def regression_pipeline(store):
    """one program: make data, split it, fit three ways, predict, score. receipts included."""

    def program(pcr):
        pcr.calc(
            "data", calcs.calc("synthetic_regression"), id="make",
            into=D("regression"),
            args={"seed": 17, "n": 240, "d": 4, "noise": 0.25,
                  "for": "the regression problem every linear oracle is checked on"},
        )
        pcr.calc(
            "split", calcs.calc("train_test_split"), id="split",
            into=R("train_test_split", "regression"),
            data=D("regression"),
            args={"seed": 17, "test_size": 0.25, "for": "a test set the fit never saw"},
        )
        pcr.calc(
            "split", calcs.calc("subset"), id="train",
            into=D("regression_train"), data=D("regression"),
            index=R("train_test_split", "regression"),
            args={"which": "train_index", "for": "the rows the fit may see"},
        )
        pcr.calc(
            "split", calcs.calc("subset"), id="test",
            into=D("regression_test"), data=D("regression"),
            index=R("train_test_split", "regression"),
            args={"which": "test_index", "for": "the rows the score is read off"},
        )
        for backend in ("py", "np"):
            pcr.calc(
                "fit", calcs.calc("linreg_fit"), id=f"closed_{backend}",
                into=R("linreg", f"regression_closed_{backend}"), data=D("regression_train"),
                args={"target": "y", "backend": backend, "method": "closed",
                      "for": f"least squares in closed form on the {backend} backend"},
            )
        pcr.calc(
            "fit", calcs.calc("linreg_fit"), id="gd",
            into=R("linreg", "regression_gd"), data=D("regression_train"),
            args={"target": "y", "backend": "np", "method": "gd", "lr": 0.05, "epochs": 3000,
                  "for": "the same fit walked to instead of solved for"},
        )
        pcr.calc(
            "fit", calcs.calc("ridge_fit"), id="ridge",
            into=R("ridge", "regression_a1"), data=D("regression_train"),
            args={"target": "y", "backend": "np", "alpha": 1.0,
                  "for": "least squares with the coefficients pulled toward zero"},
        )
        pcr.calc(
            "predict", calcs.calc("linreg_predict"), id="predict",
            into=R("linreg_predict", "regression_test"),
            model=R("linreg", "regression_closed_np"), data=D("regression_test"),
            args={"backend": "np", "for": "what the model says about rows it never saw"},
        )
        pcr.calc(
            "predict", calcs.calc("column"), id="truth",
            into=R("column", "regression_test_y"), data=D("regression_test"),
            args={"name": "y", "for": "what those rows really were"},
        )
        pcr.calc(
            "score", calcs.calc("regression_metrics"), id="score",
            into=R("regression_metrics", "regression_test"),
            y_true=R("column", "regression_test_y"), y_pred=R("linreg_predict", "regression_test"),
            args={"backend": "np", "for": "the held-out error of the closed-form fit"},
        )

    store.run("brain-ml-regression", program, record_name="ml.regression")

    # the oracles: an independent route to the same numbers, never the same code.
    train = store.get("px.exp.brain.data.ml.regression_train")
    matrix, targets, _ = core.xy(train, "y")
    design = np.hstack([np.ones((len(matrix), 1)), np.asarray(matrix)])
    reference = np.linalg.lstsq(design, np.asarray(targets), rcond=None)[0].tolist()
    for backend in ("py", "np"):
        model = store.get(f"px.exp.brain.result.ml.linreg.regression_closed_{backend}")
        parts.oracle(
            store, VERTICAL, "linreg_fit", f"closed_{backend}",
            [model["intercept"]] + model["coef"], reference,
            "numpy.linalg.lstsq on the same design matrix", 1e-8,
            "a backend that changes the answer is a failed backend, not a faster one",
        )
    walked = store.get("px.exp.brain.result.ml.linreg.regression_gd")
    parts.oracle(
        store, VERTICAL, "linreg_fit", "gd_reaches_closed_form",
        [walked["intercept"]] + walked["coef"], reference,
        "numpy.linalg.lstsq on the same design matrix", 5e-3,
        "gradient descent is only worth having if it arrives where the solve does",
    )
    ridge = store.get("px.exp.brain.result.ml.ridge.regression_a1")
    penalty = np.eye(design.shape[1])
    penalty[0, 0] = 0.0
    augmented = np.vstack([design, np.sqrt(1.0) * penalty])
    padded = np.concatenate([np.asarray(targets), np.zeros(design.shape[1])])
    ridge_reference = np.linalg.lstsq(augmented, padded, rcond=None)[0].tolist()
    parts.oracle(
        store, VERTICAL, "ridge_fit", "alpha_1",
        [ridge["intercept"]] + ridge["coef"], ridge_reference,
        "numpy.linalg.lstsq on the augmented-data spelling of ridge", 1e-7,
        "two spellings of ridge must agree or one of them is not ridge",
    )
    truth = store.get("px.exp.brain.result.ml.column.regression_test_y")["values"]
    guess = store.get("px.exp.brain.result.ml.linreg_predict.regression_test")["predictions"]
    scored = store.get("px.exp.brain.result.ml.regression_metrics.regression_test")
    t, g = np.asarray(truth), np.asarray(guess)
    parts.oracle(
        store, VERTICAL, "regression_metrics", "held_out",
        {"mse": scored["mse"], "mae": scored["mae"], "r2": scored["r2"]},
        {
            "mse": float(((t - g) ** 2).mean()),
            "mae": float(np.abs(t - g).mean()),
            "r2": float(1 - ((t - g) ** 2).sum() / ((t - t.mean()) ** 2).sum()),
        },
        "numpy, elementwise", 1e-12,
        "a metric that is wrong makes every model above it unreadable",
    )


@section
def resampling_oracles(store):
    """a split has no closed form; its oracle is the invariant it must not break."""
    data = store.get("px.exp.brain.data.ml.regression")
    split = store.get("px.exp.brain.result.ml.train_test_split.regression")
    n = len(core.as_rows(data))
    parts.oracle(
        store, VERTICAL, "train_test_split", "is_a_partition",
        sorted(split["train_index"] + split["test_index"]), list(range(n)),
        "the partition invariant, checked by hand", 0.0,
        "a split that loses or duplicates a row silently inflates every score above it",
    )
    again = calcs.call("train_test_split", {"data": data, "seed": 17, "test_size": 0.25})
    parts.oracle(
        store, VERTICAL, "train_test_split", "seed_is_the_whole_randomness",
        again["test_index"], split["test_index"],
        "the same calculation re-run from the same seed", 0.0,
        "a seed in args is what makes a random calculation replayable from its record",
    )
    folds = calcs.call("kfold", {"data": data, "seed": 17, "k": 5})
    parts.result(store, VERTICAL, "kfold", "regression_k5", folds)
    parts.oracle(
        store, VERTICAL, "kfold", "every_row_held_out_once",
        sorted(i for f in folds["folds"] for i in f["test_index"]), list(range(n)),
        "the k-fold invariant, checked by hand", 0.0,
        "cross-validation means every row is a test row exactly once; anything else is a lie",
    )


@section
def evaluation_oracles(store):
    """the metrics, against scipy and against hand-checked small cases."""
    from scipy import stats

    truth = [0, 0, 1, 1, 0, 1, 1, 0, 1, 0]
    score = [0.1, 0.4, 0.35, 0.8, 0.2, 0.9, 0.55, 0.3, 0.7, 0.6]
    auc = calcs.call("roc_auc", {"y_true": truth, "y_pred": score})
    parts.result(store, VERTICAL, "roc_auc", "ten_points", auc)
    positives = [s for s, t in zip(score, truth) if t == 1]
    negatives = [s for s, t in zip(score, truth) if t == 0]
    u = float(stats.mannwhitneyu(positives, negatives, alternative="two-sided").statistic)
    parts.oracle(
        store, VERTICAL, "roc_auc", "ten_points",
        auc["auc"], u / (len(positives) * len(negatives)),
        "scipy.stats.mannwhitneyu, through the identity auc = u / (n_pos * n_neg)", 1e-12,
        "the rank identity is exact, so auc needs no curve and no threshold sweep",
    )
    y_true = [0, 0, 0, 1, 1, 1, 1, 2, 2, 2]
    y_pred = [0, 0, 1, 1, 1, 1, 2, 2, 2, 0]
    table = calcs.call("confusion_matrix", {"y_true": y_true, "y_pred": y_pred})
    parts.result(store, VERTICAL, "confusion_matrix", "three_classes", table)
    parts.oracle(
        store, VERTICAL, "confusion_matrix", "three_classes",
        table["matrix"], [[2, 1, 0], [0, 3, 1], [1, 0, 2]],
        "counted by hand from the ten pairs", 0.0,
        "every classification metric is read off this table, so it is checked first",
    )
    scored = calcs.call("classification_metrics", {"y_true": y_true, "y_pred": y_pred})
    parts.result(store, VERTICAL, "classification_metrics", "three_classes", scored)
    parts.oracle(
        store, VERTICAL, "classification_metrics", "three_classes",
        {"accuracy": scored["accuracy"], "f1_of_class_1": scored["per_class"]["1"]["f1"]},
        {"accuracy": 0.7, "f1_of_class_1": 0.75},
        "read off the hand-counted confusion matrix", 1e-12,
        "precision and recall are the two halves nobody should have to recompute",
    )
    blobs = calcs.call("synthetic_blobs", {"seed": 21, "n": 90, "k": 3, "d": 2})
    store.put("px.exp.brain.data.ml.blobs", blobs)
    features = core.dataset("the blob features alone", ["x0", "x1"], [r[:-1] for r in core.as_rows(blobs)])
    labels = [int(r[-1]) for r in core.as_rows(blobs)]
    sil = calcs.call("silhouette", {"data": features, "labels": labels, "backend": "np"})
    parts.result(store, VERTICAL, "silhouette", "blobs_true_labels", {k: sil[k] for k in ("for", "mean", "clusters")})
    shuffled = core.stream(99).permutation(len(labels))
    scrambled = calcs.call("silhouette", {"data": features, "labels": [labels[i] for i in shuffled]})
    parts.oracle(
        store, VERTICAL, "silhouette", "true_beats_scrambled",
        sil["mean"] > scrambled["mean"], True,
        "the same measure on the true labelling and on a deliberately wrong one", 0.0,
        "a cluster score that cannot tell a true labelling from a shuffled one measures nothing",
    )


@section
def benchmarks(store):
    """py against np, on the same inputs, only where both oracles passed."""
    for size, n in (("small", 200), ("medium", 2000)):
        data = calcs.call("synthetic_regression", {"seed": 5, "n": n, "d": 12})
        for backend in ("py", "np"):
            parts.bench(
                store, VERTICAL, "linreg_fit", backend, f"{size}_n{n}_d12",
                lambda data=data, backend=backend: calcs.call(
                    "linreg_fit", {"data": data, "target": "y", "backend": backend}
                ),
                n=5,
                for_="what the np backend is worth on the one calculation everything else leans on",
            )
    big = calcs.call("synthetic_blobs", {"seed": 5, "n": 400, "k": 4, "d": 3})
    features = core.dataset("features", ["x0", "x1", "x2"], [r[:-1] for r in core.as_rows(big)])
    labels = [int(r[-1]) for r in core.as_rows(big)]
    for backend in ("py", "np"):
        parts.bench(
            store, VERTICAL, "silhouette", backend, "n400_k4",
            lambda backend=backend: calcs.call(
                "silhouette", {"data": features, "labels": labels, "backend": backend}
            ),
            n=3,
            for_="silhouette is all pairwise distance, so it is where vectorising should pay most",
        )


# --- the map and the findings ------------------------------------------------


def map_and_findings(store):
    built = [a for a in store.addresses("px.exp.brain.") if not a.startswith("px.receipt.")]
    stubbed = list(STUBBED)
    parts.map_part(
        store, VERTICAL, built, stubbed, NEXT,
        "the territory of the ml vertical, readable through PQL without opening a file",
    )
    for k, value in FINDINGS.items():
        payload = dict(value)
        parts.finding(store, VERTICAL, k, payload.pop("kind"), payload.pop("text"), payload.pop("for"), **payload)


STUBBED = [
    {"address": "fn.brain.ml.lasso_fit", "why": "coordinate descent is written for the next slice; ridge covers the penalised case today"},
    {"address": "fn.brain.ml.dbscan", "why": "density clustering is behind k-means and the hierarchies in the queue"},
]

NEXT = [
    {"what": "logistic regression, knn and naive bayes on this same split and these same metrics",
     "for": "classification is half the surface and every metric above is already oracled for it"},
    {"what": "cart, a small forest and small gradient boosting",
     "for": "the non-linear half; the split-search is the one place the py backend will really hurt"},
    {"what": "k-means with a seeded k-means++ init, and pca through svd",
     "for": "unsupervised needs the same parts discipline, and silhouette is already here to score it"},
    {"what": "a pairwise-distance calculation on the backend vertical, and knn/k-means/silhouette routed through it",
     "for": "three calculations recompute the same n-by-n matrix; one backend primitive would serve all three"},
]

FINDINGS = {
    "seed-in-args-makes-one-oracle-cover-two-backends": {
        "kind": "strength",
        "text": "every seeded calculation here reads one deterministic Stream built from args['seed'], never random or numpy's generator. the py and np backends then return the same bytes, so a seeded calculation needs one oracle instead of one per backend, and a record replays exactly.",
        "for": "the contract's rule that a backend which changes semantics is a failed backend is only checkable if the randomness is shared",
    },
    "a-fitted-model-is-a-part": {
        "kind": "strength",
        "text": "fit and predict are separate Calculations and the model between them is a json-able dict at px.exp.brain.result.ml.<model>.<case>. the receipt digests it, PQL finds it, and predicting from a model a different run fitted costs nothing.",
        "for": "an ml layer whose models only exist inside a process cannot be audited, compared or replayed",
    },
    "pxc-has-no-document": {
        "kind": "friction",
        "text": "PxC can be walked (addresses, PQL.prefix) but cannot hand back or take in a whole document, so every vertical writes its own save/load pair and its own receipt-exclusion rule.",
        "for": "the store is where the night's work lives; persisting it is not a per-vertical concern",
        "workaround": "Store.document()/save()/load_store() in experiments/brain/ml/parts.py, written to the shape the shared harness will expose",
        "proposal": "PxC.document(exclude_prefix='px.receipt.') and PxC.merge(document), so a store round-trips through json in the kernel and every vertical's persistence is the same code",
    },
    "a-calculation-cannot-declare-its-args": {
        "kind": "friction",
        "text": "a Calculation is a pure function of one mapping, and nothing at author time says which keys it needs. a missing args['seed'] or args['target'] surfaces as a KeyError deep inside a Tick, after the run has started and after earlier Ticks have already written their Parts.",
        "for": "the whole point of declaring produces and consumes is that a program is refused before it runs, not during it",
        "workaround": "each calculation reads its required keys first and raises a named error; the tests assert the refusal",
        "proposal": "an optional args schema on Calculation (names and whether required) checked by PCR.calc at author time, the way a read of a later sibling's Part already is",
    },
    "pql-cannot-select-on-a-field-inside-a-value": {
        "kind": "friction",
        "text": "navigating this store means questions like 'every oracle that failed' or 'every benchmark of the np backend'. PQL.prefix gets to the subtree, but the selection itself is a python closure over match.value written at each call site, so the query is not a value that can be stored, named or put in a record.",
        "for": "the brief says use PQL to navigate what you are building; a query you cannot store is not navigation, it is a script",
        "workaround": "parts.navigate() holds the handful of closures the vertical actually asks and returns their answers as plain data",
        "proposal": "PQL.field('pass', False) / PQL.field('backend', 'np') composing with prefix and where, so a query stays a value and can itself be a Part",
    },
    "worker-sessions-could-not-be-spawned": {
        "kind": "friction",
        "text": "the vertical was briefed to fan out to parallel worker sessions for each build and each tournament judge. every route to one was refused in this environment, so the whole vertical was built serially in one session and the tournament judges are deterministic scoring functions over the recorded criteria instead of separate readers.",
        "for": "a tournament judged by the same agent that built the candidates is weaker evidence, and the surface built in a night is bounded by how much one session can write",
        "workaround": "criteria are written into the bracket Part before any score exists, the judge is a pure function of the oracle and benchmark Parts, and a test re-runs the whole bracket from the candidates so the verdict is reproducible rather than trusted",
        "proposal": "the sprint harness should hand each vertical a way to run a scoped worker session, or the contract should say plainly that a recorded, re-runnable scoring function is the judge of record",
    },
}


def build(store=None, save=True):
    # save=True is the explicit record run (`python -m experiments.brain.ml.build`);
    # save=False is a test, and a test writes neither the store nor the records.
    store = store or parts.Store(VERTICAL, commit=save)
    for fn in SECTIONS:
        fn(store)
    map_and_findings(store)
    if save:
        store.save(VERTICAL)
    return store


def main():
    store = build()
    view = parts.navigate(store)
    print(f"ml vertical: {len(store.document())} parts")
    for kind in ("data", "result", "oracle", "bench", "bracket", "map"):
        print(f"  {kind:<8} {len(view[kind])}")
    print(f"  oracles  {view['oracles_passing']} of {view['oracles_total']} passing")
    print(f"  findings {len(view['findings'])}")
    return 0 if view["oracles_passing"] == view["oracles_total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
