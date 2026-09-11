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
from scipy import optimize, stats
from scipy.cluster import hierarchy
from scipy.spatial import distance as sp_distance

import math

from . import calcs, core, distance, linear, metrics, multiclass, nnet, parts, resample, tournament, trees, unsup, validate

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

    store.run_program("brain-ml-regression", program, record_name="ml.regression")

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


@section
def classification_pipeline(store):
    """one program again, for the classifiers: data, split, four fits, four scores."""

    def program(pcr):
        pcr.calc(
            "data", calcs.calc("synthetic_classification"), id="make",
            into=D("classification"),
            args={"seed": 29, "n": 300, "d": 4, "k": 3, "spread": 1.6,
                  "for": "the three-class problem every classifier here is scored on"},
        )
        pcr.calc(
            "split", calcs.calc("train_test_split"), id="split",
            into=R("train_test_split", "classification"), data=D("classification"),
            args={"seed": 29, "test_size": 0.3, "stratify": "label",
                  "for": "a stratified split, so every class is in both halves"},
        )
        for which, name in (("train_index", "classification_train"), ("test_index", "classification_test")):
            pcr.calc(
                "split", calcs.calc("subset"), id=name,
                into=D(name), data=D("classification"), index=R("train_test_split", "classification"),
                args={"which": which, "for": f"the {which.split('_')[0]} half"},
            )
        pcr.calc(
            "fit", calcs.calc("logreg_fit"), id="logreg",
            into=R("logreg", "classification"), data=D("classification_train"),
            args={"target": "label", "backend": "np", "method": "newton", "l2": 1.0,
                  "for": "one-vs-rest logistic regression, by the step the bracket picked"},
        )
        pcr.calc(
            "fit", calcs.calc("knn_fit"), id="knn",
            into=R("knn", "classification"), data=D("classification_train"),
            args={"target": "label", "k": 7, "for": "seven neighbours, uniform vote"},
        )
        pcr.calc(
            "fit", calcs.calc("gaussian_nb_fit"), id="gnb",
            into=R("gaussian_nb", "classification"), data=D("classification_train"),
            args={"target": "label", "for": "a mean and a variance per feature per class"},
        )
        pcr.calc(
            "predict", calcs.calc("column"), id="truth",
            into=R("column", "classification_test_label"), data=D("classification_test"),
            args={"name": "label", "for": "what those held-out rows really were"},
        )
        for id_, calc, model in (
            ("logreg_p", "logreg_predict", R("logreg", "classification")),
            ("knn_p", "knn_predict", R("knn", "classification")),
            ("gnb_p", "gaussian_nb_predict", R("gaussian_nb", "classification")),
        ):
            pcr.calc(
                "predict", calcs.calc(calc), id=id_,
                into=R(calc, "classification_test"), model=model, data=D("classification_test"),
                args={"backend": "np", "for": f"what {calc} says about rows it never saw"},
            )
        for id_, calc in (("logreg_s", "logreg_predict"), ("knn_s", "knn_predict"), ("gnb_s", "gaussian_nb_predict")):
            pcr.calc(
                "score", calcs.calc("classification_metrics"), id=id_,
                into=R("classification_metrics", f"{calc}_test"),
                y_true=R("column", "classification_test_label"), y_pred=R(calc, "classification_test"),
                args={"for": f"the held-out accuracy, precision, recall and f1 of {calc}"},
            )

    store.run_program("brain-ml-classification", program, record_name="ml.classification")

    # the oracles.
    train = store.get("px.exp.brain.data.ml.classification_train")
    matrix, targets, _ = core.xy(train, "label")
    design = np.hstack([np.ones((len(matrix), 1)), np.asarray(matrix)])
    model = store.get("px.exp.brain.result.ml.logreg.classification")
    for index, label in enumerate(model["classes"]):
        y = np.asarray([1.0 if t == label else 0.0 for t in targets])

        def loss(w, y=y):
            z = design @ w
            return float(np.sum(np.logaddexp(0.0, z) - y * z) + 0.5 * float(w[1:] @ w[1:]))

        reference = optimize.minimize(
            loss, np.zeros(design.shape[1]), method="L-BFGS-B",
            options={"ftol": 1e-16, "gtol": 1e-14, "maxiter": 20000},
        ).x.tolist()
        parts.oracle(
            store, VERTICAL, "logreg_fit", f"one_vs_rest_class_{index}",
            [model["intercepts"][index]] + model["coefs"][index], reference,
            "scipy.optimize.minimize on the penalised negative log likelihood", 5e-3,
            "one-vs-rest is only k independent fits if each one really is that fit",
        )
    test = store.get("px.exp.brain.data.ml.classification_test")
    rows, _, _ = core.xy(test, "label")
    knn = store.get("px.exp.brain.result.ml.knn.classification")
    d = sp_distance.cdist(np.asarray(rows), np.asarray(knn["rows"]), metric="euclidean")
    want = []
    for row in d:
        order = sorted(range(len(row)), key=lambda i: (row[i], i))[: knn["k"]]
        tally = {}
        for i in order:
            tally[knn["labels"][i]] = tally.get(knn["labels"][i], 0) + 1
        want.append(max(sorted(tally), key=lambda label: tally[label]))
    parts.oracle(
        store, VERTICAL, "knn_predict", "against_cdist",
        store.get("px.exp.brain.result.ml.knn_predict.classification_test")["labels"], want,
        "scipy.spatial.distance.cdist and a vote written from scratch", 0.0,
        "knn has no parameters to check, so the vote itself is the only thing an oracle can hold",
    )
    gnb = store.get("px.exp.brain.result.ml.gaussian_nb.classification")
    got = store.get("px.exp.brain.result.ml.gaussian_nb_predict.classification_test")["log_posterior"]
    want = [
        [float(np.log(prior) + stats.norm.logpdf(row, loc=mu, scale=np.sqrt(var)).sum())
         for prior, mu, var in zip(gnb["priors"], gnb["means"], gnb["variances"])]
        for row in rows
    ]
    parts.oracle(
        store, VERTICAL, "gaussian_nb_predict", "log_posterior",
        got, want, "scipy.stats.norm.logpdf, summed per class", 1e-9,
        "naive bayes is a sum of log densities; if the densities are wrong nothing downstream shows it",
    )
    counts = calcs.call("synthetic_counts", {"seed": 29, "n": 200, "k": 3, "vocabulary": 10, "length": 30})
    store.put("px.exp.brain.data.ml.counts", counts)
    mnb = calcs.call("multinomial_nb_fit", {"data": counts, "target": "label", "alpha": 1.0})
    parts.result(store, VERTICAL, "multinomial_nb", "counts", mnb)
    predicted = calcs.call("multinomial_nb_predict", {"model": mnb, "data": counts, "backend": "np"})
    parts.result(store, VERTICAL, "multinomial_nb_predict", "counts", {k: predicted[k] for k in ("for", "classes", "labels")})
    count_rows, count_labels, _ = core.xy(counts, "label")
    reference = [
        [float(np.log(prior) + np.dot(row, probabilities))
         for prior, probabilities in zip(mnb["priors"], mnb["log_prob"])]
        for row in count_rows
    ]
    parts.oracle(
        store, VERTICAL, "multinomial_nb_predict", "log_posterior",
        predicted["log_posterior"][:25], reference[:25],
        "numpy, the log-count dot product written out longhand, on the first 25 rows", 1e-9,
        "the np backend of a classifier must not quietly become a different classifier",
    )
    scored = calcs.call("classification_metrics", {"y_true": count_labels, "y_pred": predicted["labels"]})
    parts.result(store, VERTICAL, "classification_metrics", "multinomial_nb_counts", scored)
    parts.oracle(
        store, VERTICAL, "multinomial_nb_predict", "recovers_the_profiles_it_was_drawn_from",
        scored["accuracy"] > 0.85, True,
        "the known per-class word profiles the counts were drawn from", 0.0,
        "a generative model that cannot recover its own generator is not fitted, it is decorated",
    )
    # a binary problem, so roc auc has something to say.
    binary = calcs.call("synthetic_classification", {"seed": 30, "n": 200, "d": 3, "k": 2, "spread": 2.4})
    store.put("px.exp.brain.data.ml.binary", binary)
    fitted = calcs.call("logreg_fit", {"data": binary, "target": "label", "backend": "np", "method": "newton", "l2": 1.0})
    proba = calcs.call("logreg_proba", {"model": fitted, "data": binary})
    truth = [row[-1] for row in core.as_rows(binary)]
    auc = calcs.call("roc_auc", {"y_true": truth, "y_pred": [p[1] for p in proba["proba"]], "positive": 1.0})
    parts.result(store, VERTICAL, "roc_auc", "logreg_binary", auc)
    positives = [p[1] for p, t in zip(proba["proba"], truth) if t == 1.0]
    negatives = [p[1] for p, t in zip(proba["proba"], truth) if t != 1.0]
    u = float(stats.mannwhitneyu(positives, negatives, alternative="two-sided").statistic)
    parts.oracle(
        store, VERTICAL, "roc_auc", "logreg_binary",
        auc["auc"], u / (len(positives) * len(negatives)),
        "scipy.stats.mannwhitneyu on the fitted probabilities", 1e-12,
        "a threshold-free score is what makes two classifiers comparable when the classes are uneven",
    )
    curve = calcs.call("roc_curve", {"y_true": truth, "y_pred": [p[1] for p in proba["proba"]], "positive": 1.0})
    parts.result(store, VERTICAL, "roc_curve", "logreg_binary", curve)


@section
def classifier_benchmarks(store):
    """the np backend against the reference, on the two calculations that carry the most arithmetic."""
    data = calcs.call("synthetic_classification", {"seed": 31, "n": 600, "d": 8, "k": 2, "spread": 2.0})
    for backend in ("py", "np"):
        parts.bench(
            store, VERTICAL, "logreg_fit", backend, "n600_d8_newton",
            lambda backend=backend: calcs.call(
                "logreg_fit", {"data": data, "target": "label", "backend": backend, "method": "newton", "l2": 1.0}
            ), 3,
            "newton builds an n-by-d-by-d hessian per step: the worst case for a python loop",
        )
    model = calcs.call("knn_fit", {"data": data, "target": "label", "k": 7})
    for backend in ("py", "np"):
        parts.bench(
            store, VERTICAL, "knn_predict", backend, "n600_d8_k7",
            lambda backend=backend: calcs.call("knn_predict", {"model": model, "data": data, "backend": backend}), 3,
            "knn is one n-by-n distance matrix and nothing else",
        )


@section
def tournaments(store):
    """the brackets, rebuilt from their candidates every time this runs."""
    for build_bracket in tournament.BRACKETS:
        build_bracket(store)


@section
def tree_pipeline(store):
    """one program for the trees: data, split, a tree, a forest, boosting, and the scores."""

    def program(pcr):
        pcr.calc(
            "data", calcs.calc("synthetic_classification"), id="make",
            into=D("trees"),
            args={"seed": 67, "n": 320, "d": 5, "k": 3, "spread": 1.9,
                  "for": "the problem the tree, the forest and the boosting are all scored on"},
        )
        pcr.calc(
            "split", calcs.calc("train_test_split"), id="split",
            into=R("train_test_split", "trees"), data=D("trees"),
            args={"seed": 67, "test_size": 0.3, "stratify": "label",
                  "for": "a stratified split so every class is in both halves"},
        )
        for which, name in (("train_index", "trees_train"), ("test_index", "trees_test")):
            pcr.calc(
                "split", calcs.calc("subset"), id=name, into=D(name), data=D("trees"),
                index=R("train_test_split", "trees"),
                args={"which": which, "for": f"the {which.split('_')[0]} half"},
            )
        pcr.calc(
            "fit", calcs.calc("tree_fit"), id="tree", into=R("tree", "trees"), data=D("trees_train"),
            args={"target": "label", "criterion": "gini", "max_depth": 5,
                  "for": "one depth-limited cart tree, split by gini"},
        )
        pcr.calc(
            "fit", calcs.calc("tree_fit"), id="tree_entropy", into=R("tree", "trees_entropy"),
            data=D("trees_train"),
            args={"target": "label", "criterion": "entropy", "max_depth": 5,
                  "for": "the same tree, split by information gain instead"},
        )
        pcr.calc(
            "fit", calcs.calc("forest_fit"), id="forest", into=R("forest", "trees"), data=D("trees_train"),
            args={"target": "label", "n_trees": 20, "seed": 67, "max_depth": 6,
                  "for": "twenty bootstrapped trees, each on a seeded subset of the columns"},
        )
        pcr.calc(
            "predict", calcs.calc("column"), id="truth", into=R("column", "trees_test_label"),
            data=D("trees_test"), args={"name": "label", "for": "what the held-out rows really were"},
        )
        for id_, calc, model in (("tree_p", "tree_predict", R("tree", "trees")),
                                 ("forest_p", "forest_predict", R("forest", "trees"))):
            pcr.calc(
                "predict", calcs.calc(calc), id=id_, into=R(calc, "trees_test"),
                model=model, data=D("trees_test"),
                args={"for": f"what {calc} says about rows it never saw"},
            )
        for id_, calc in (("tree_s", "tree_predict"), ("forest_s", "forest_predict")):
            pcr.calc(
                "score", calcs.calc("classification_metrics"), id=id_,
                into=R("classification_metrics", f"{calc}_test"),
                y_true=R("column", "trees_test_label"), y_pred=R(calc, "trees_test"),
                args={"for": f"the held-out accuracy, precision, recall and f1 of {calc}"},
            )

    store.run_program("brain-ml-trees", program, record_name="ml.trees")

    # the oracles: invariants a tree cannot break, and a reference tree built by hand.
    tree = store.get("px.exp.brain.result.ml.tree.trees")
    parts.oracle(
        store, VERTICAL, "tree_fit", "depth_is_respected",
        [tree["depth"] <= tree["max_depth"], trees.tree_depth(tree["root"]) == tree["depth"]], [True, True],
        "the depth limit in args, checked against the tree that came back", 0.0,
        "a depth limit that is not enforced turns every tree into a lookup table of its training rows",
    )
    rows = [[float(x), 0.0] for x in (0.0, 1.0, 2.0, 3.0, 7.0, 8.0, 9.0, 10.0)]
    labels = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0]
    hand = core.dataset("a split put at five by hand", ["x0", "x1", "label"],
                        [row + [label] for row, label in zip(rows, labels)])
    found = calcs.call("tree_fit", {"data": hand, "target": "label", "max_depth": 1})
    parts.result(store, VERTICAL, "tree", "hand_case", {
        "for": "the smallest tree with a right answer", "root": found["root"], "nodes": found["nodes"]})
    parts.oracle(
        store, VERTICAL, "tree_fit", "hand_case",
        [found["root"]["feature"], found["root"]["threshold"]], [0, 5.0],
        "a threshold placed by hand at five, on the only informative column", 1e-12,
        "the split search is the one thing in a tree that can be checked exactly",
    )
    forest = store.get("px.exp.brain.result.ml.forest.trees")
    one = store.get("px.exp.brain.result.ml.classification_metrics.tree_predict_test")
    many = store.get("px.exp.brain.result.ml.classification_metrics.forest_predict_test")
    parts.oracle(
        store, VERTICAL, "forest_predict", "beats_the_tree_it_is_made_of",
        many["accuracy"] >= one["accuracy"], True,
        "the same held-out rows, scored for one tree and for the forest of twenty", 0.0,
        "if averaging bootstrapped trees does not help, the bootstrap or the vote is wrong",
    )
    parts.oracle(
        store, VERTICAL, "forest_fit", "the_seed_is_the_whole_forest",
        calcs.call("forest_fit", {"data": store.get("px.exp.brain.data.ml.trees_train"), "target": "label",
                                   "n_trees": 4, "seed": 67, "max_depth": 4})["trees"][0]["root"],
        calcs.call("forest_fit", {"data": store.get("px.exp.brain.data.ml.trees_train"), "target": "label",
                                   "n_trees": 4, "seed": 67, "max_depth": 4})["trees"][0]["root"],
        "the same calculation re-run from the same seed", 0.0,
        "a bootstrap that is not a function of its seed cannot be replayed from a record",
    )
    # boosting, on a regression problem, with its loss curve as a part.
    regression = store.get("px.exp.brain.data.ml.regression_train")
    boosted = calcs.call("gbm_fit", {"data": regression, "target": "y", "n_trees": 40,
                                      "learning_rate": 0.15, "max_depth": 2,
                                      "for": "forty small corrections to the mean"})
    parts.result(store, VERTICAL, "gbm", "regression", {
        "for": boosted["for"], "model": "gbm", "init": boosted["init"],
        "learning_rate": boosted["learning_rate"], "n_trees": boosted["n_trees"],
        "train_mse": boosted["train_mse"], "nodes": [tree["nodes"] for tree in boosted["trees"]]})
    losses = boosted["train_mse"]
    parts.oracle(
        store, VERTICAL, "gbm_fit", "the_loss_never_goes_up",
        all(after <= before + 1e-9 for before, after in zip(losses, losses[1:])), True,
        "the squared error the fit recorded after each of its own corrections", 0.0,
        "boosting is a sequence of corrections; a loss that rises means the correction has the wrong sign",
    )
    predicted = calcs.call("gbm_predict", {"model": boosted, "data": regression})
    truth = [row[-1] for row in core.as_rows(regression)]
    scored = calcs.call("regression_metrics", {"y_true": truth, "y_pred": predicted})
    parts.result(store, VERTICAL, "regression_metrics", "gbm_train", scored)
    parts.oracle(
        store, VERTICAL, "gbm_predict", "agrees_with_the_loss_the_fit_recorded",
        scored["mse"], losses[-1],
        "the last entry of the fit's own train_mse, recomputed from predict", 1e-9,
        "fit and predict are separate calculations; they must still describe the same model",
    )


@section
def unsupervised_pipeline(store):
    """one program for the unsupervised half: blobs, k-means, pca, dbscan, silhouette."""

    def program(pcr):
        pcr.calc(
            "data", calcs.calc("synthetic_blobs"), id="make", into=D("clusters"),
            args={"seed": 77, "n": 240, "k": 4, "d": 3, "spread": 0.8,
                  "for": "four clusters whose true membership is known, to score the clustering against"},
        )
        pcr.calc(
            "fit", calcs.calc("kmeans"), id="kmeans", into=R("kmeans", "clusters"), data=D("clusters"),
            args={"k": 4, "seed": 77, "backend": "np", "drop_last": True,
                  "for": "lloyd's iteration from a seeded k-means++ init"},
        )
        pcr.calc(
            "fit", calcs.calc("pca"), id="pca", into=R("pca", "clusters"), data=D("clusters"),
            args={"n_components": 2, "drop_last": True,
                  "for": "the two directions the cluster centres actually spread along"},
        )
        pcr.calc(
            "fit", calcs.calc("dbscan"), id="dbscan", into=R("dbscan", "clusters"), data=D("clusters"),
            args={"eps": 2.0, "min_samples": 5, "backend": "np", "drop_last": True,
                  "for": "the same clusters found without being told how many there are"},
        )

    store.run_program("brain-ml-unsupervised", program, record_name="ml.unsupervised")

    blobs = store.get("px.exp.brain.data.ml.clusters")
    features = core.dataset("the blob features alone", core.columns_of(blobs)[:-1],
                            [row[:-1] for row in core.as_rows(blobs)])
    truth = [int(row[-1]) for row in core.as_rows(blobs)]
    found = store.get("px.exp.brain.result.ml.kmeans.clusters")
    pairs = {}
    for label, real in zip(found["labels"], truth):
        pairs.setdefault(label, set()).add(real)
    parts.oracle(
        store, VERTICAL, "kmeans", "recovers_the_blobs_it_was_given",
        all(len(v) == 1 for v in pairs.values()), True,
        "the cluster each row was drawn from, which the generator recorded", 0.0,
        "a clustering that cannot recover blobs it was handed cannot be trusted on data that has none",
    )
    history = found["history"]
    parts.oracle(
        store, VERTICAL, "kmeans", "the_inertia_never_goes_up",
        all(after <= before + 1e-9 for before, after in zip(history, history[1:])), True,
        "the inertia the iteration recorded after each of its own assignments", 0.0,
        "lloyd's iteration is a descent; an inertia that rises means the update and the assignment disagree",
    )
    scored = calcs.call("silhouette", {"data": features, "labels": found["labels"], "backend": "np"})
    parts.result(store, VERTICAL, "silhouette", "kmeans_clusters",
                 {k: scored[k] for k in ("for", "mean", "clusters")})
    fitted = store.get("px.exp.brain.result.ml.pca.clusters")
    x = np.asarray([row[:-1] for row in core.as_rows(blobs)])
    centred = x - x.mean(0)
    _, s_values, vt = np.linalg.svd(centred, full_matrices=False)
    parts.oracle(
        store, VERTICAL, "pca", "explained_variance",
        fitted["explained_variance"], ((s_values**2) / (len(x) - 1))[:2].tolist(),
        "numpy.linalg.svd of the centred matrix, squared and scaled", 1e-9,
        "explained variance is what makes a component worth keeping; it is the number to check",
    )
    components = np.asarray(fitted["components"])
    parts.oracle(
        store, VERTICAL, "pca", "components_are_orthonormal",
        (components @ components.T).tolist(), np.eye(2).tolist(), "the definition of an orthonormal basis", 1e-9,
        "components that are not orthonormal make the explained-variance split meaningless",
    )
    by_python = calcs.call("pca", {"data": features, "n_components": 2, "backend": "py"})
    parts.oracle(
        store, VERTICAL, "pca", "jacobi_finds_the_same_variance_as_the_svd",
        by_python["explained_variance"], fitted["explained_variance"],
        "the pure-python covariance and jacobi rotation, against the numpy svd", 1e-6,
        "two routes to the same subspace is how a backend is shown not to have changed the answer",
    )
    density = store.get("px.exp.brain.result.ml.dbscan.clusters")
    parts.oracle(
        store, VERTICAL, "dbscan", "finds_the_same_four_groups",
        [density["clusters"], density["noise"]], [4, 0],
        "the four blobs the generator drew, counted without being told how many", 0.0,
        "dbscan is the one clustering here that is allowed to say a point belongs to nothing",
    )
    small = core.dataset("a few points, two tight groups and one stray", ["x0", "x1"],
                         [[0.0, 0.0], [0.1, 0.0], [0.0, 0.1], [0.1, 0.1],
                          [5.0, 5.0], [5.1, 5.0], [5.0, 5.1], [5.1, 5.1], [50.0, 50.0]])
    stray = calcs.call("dbscan", {"data": small, "eps": 0.5, "min_samples": 3})
    parts.result(store, VERTICAL, "dbscan", "hand_case", stray)
    parts.oracle(
        store, VERTICAL, "dbscan", "hand_case",
        [stray["clusters"], stray["noise"], stray["labels"][-1]], [2, 1, -1],
        "nine points placed by hand, two groups and one outlier", 0.0,
        "the noise label is the whole point of dbscan and the only part of it worth checking by hand",
    )
    linked = calcs.call("hierarchical", {"data": features, "linkage": "complete", "k": 4})
    parts.result(store, VERTICAL, "hierarchical", "clusters_complete",
                 {"for": linked["for"], "linkage": "complete", "k": 4,
                  "heights": linked["heights"][-8:], "labels": linked["labels"]})
    theirs = hierarchy.linkage(sp_distance.pdist(np.asarray([row[:-1] for row in core.as_rows(blobs)])),
                               method="complete")
    parts.oracle(
        store, VERTICAL, "hierarchical", "merge_heights_match_scipy",
        linked["heights"], theirs[:, 2].tolist(),
        "scipy.cluster.hierarchy.linkage, method complete", 1e-9,
        "the merge heights are the dendrogram; if they match, the tree matches",
    )


@section
def learning_curves(store):
    """a learning curve is a part: does this model want more rows, or a different model."""
    data = store.get("px.exp.brain.data.ml.regression")
    for name, fit, predict, fit_args in (
        ("linreg", "linreg_fit", "linreg_predict", {}),
        ("gbm", "gbm_fit", "gbm_predict", {"n_trees": 25, "learning_rate": 0.15, "max_depth": 2}),
    ):
        curve = calcs.call("learning_curve", {
            "data": data, "target": "y", "seed": 81, "fit": fit, "predict": predict,
            "fit_args": fit_args, "metric": "mse", "fractions": [0.1, 0.25, 0.5, 0.75, 1.0],
            "for": f"whether {name} is short of rows or short of capacity"})
        parts.result(store, VERTICAL, "learning_curve", name, curve)
        parts.oracle(
            store, VERTICAL, "learning_curve", f"{name}_test_error_falls",
            curve["test"][-1] <= curve["test"][0], True,
            "the same held-out rows, scored from a tenth of the training set and from all of it", 0.0,
            "a curve whose test error does not fall with rows is measuring the split, not the model",
        )
    classification = store.get("px.exp.brain.data.ml.trees")
    curve = calcs.call("learning_curve", {
        "data": classification, "target": "label", "seed": 81, "fit": "tree_fit", "predict": "tree_predict",
        "fit_args": {"max_depth": 5}, "metric": "accuracy", "fractions": [0.1, 0.25, 0.5, 1.0],
        "for": "where a depth-five tree stops learning from more rows"})
    parts.result(store, VERTICAL, "learning_curve", "tree", curve)
    parts.oracle(
        store, VERTICAL, "learning_curve", "tree_train_accuracy_is_at_least_test",
        all(train >= test - 1e-9 for train, test in zip(curve["train"], curve["test"])), True,
        "the same tree scored on the rows it was fitted to and on rows it never saw", 0.0,
        "a model that scores better on held-out rows than on its own training rows is mis-wired",
    )


@section
def tree_benchmarks(store):
    """the two split searches and the three k-means assignments, timed on shared inputs."""
    data = calcs.call("synthetic_classification", {"seed": 83, "n": 1500, "d": 8, "k": 3, "spread": 1.6})
    for search, size in (("sort", "n1500_d8_sort"), ("hist", "n1500_d8_hist32")):
        parts.bench(
            store, VERTICAL, "tree_fit", search, size,
            lambda search=search: calcs.call(
                "tree_fit", {"data": data, "target": "label", "max_depth": 6, "search": search, "bins": 32}), 3,
            "the sort is O(n log n) per feature per node; the histogram is one pass and a fixed scan",
        )
    blobs = calcs.call("synthetic_blobs", {"seed": 83, "n": 600, "k": 5, "d": 6, "spread": 0.9})
    features = core.dataset("features", core.columns_of(blobs)[:-1], [row[:-1] for row in core.as_rows(blobs)])
    for backend in ("py", "np", "gram"):
        parts.bench(
            store, VERTICAL, "kmeans", backend, "n600_k5_d6",
            lambda backend=backend: calcs.call(
                "kmeans", {"data": features, "k": 5, "seed": 83, "backend": backend}), 3,
            "every iteration is one point-to-centre distance matrix; this is the cost of spelling it three ways",
        )


@section
def sparse_and_networks(store):
    """the sparse linear model and the two small networks, on the problems already in the store."""
    regression = store.get("px.exp.brain.data.ml.regression_train")
    matrix, targets, features = core.xy(regression, "y")
    scaled, _, _ = core.standardize(matrix)
    x, centre = np.asarray(scaled), float(np.mean(targets))
    y = np.asarray(targets) - centre
    for alpha in (0.05, 0.5):
        model = calcs.call("lasso_fit", {"data": regression, "target": "y", "alpha": alpha, "backend": "np",
                                          "for": f"least squares with an l1 penalty of {alpha}"})
        parts.result(store, VERTICAL, "lasso", f"regression_a{str(alpha).replace('.', '_')}", model)

        def loss(w, alpha=alpha):
            return float(((y - x @ w) ** 2).sum() / (2 * len(y)) + alpha * np.abs(w).sum())

        reference = optimize.minimize(loss, np.zeros(x.shape[1]), method="Powell",
                                      options={"xtol": 1e-12, "ftol": 1e-14,
                                               "maxiter": 200000, "maxfev": 200000}).x.tolist()
        parts.oracle(
            store, VERTICAL, "lasso_fit", f"alpha_{str(alpha).replace('.', '_')}",
            model["scaled_coef"], reference,
            "scipy.optimize.minimize on the same penalised objective, same standardised columns", 3e-3,
            "coordinate descent is only the lasso if it lands where the objective's minimum is",
        )
    heavy = calcs.call("lasso_fit", {"data": regression, "target": "y", "alpha": 50.0, "backend": "np"})
    ridge = store.get("px.exp.brain.result.ml.ridge.regression_a1")
    parts.oracle(
        store, VERTICAL, "lasso_fit", "selects_where_ridge_only_shrinks",
        [heavy["nonzero"] == [], all(c != 0.0 for c in ridge["coef"])], [True, True],
        "the same columns under an l1 and an l2 penalty", 0.0,
        "shrinking every coefficient and zeroing some are different jobs; that is the whole reason both exist",
    )
    for backend in ("py", "np"):
        parts.bench(
            store, VERTICAL, "lasso_fit", backend, "n180_d4_a0_5",
            lambda backend=backend: calcs.call(
                "lasso_fit", {"data": regression, "target": "y", "alpha": 0.5, "backend": backend}), 3,
            "coordinate descent touches one column at a time: the case where numpy has least to win",
        )

    separable = calcs.call("synthetic_classification",
                           {"seed": 97, "n": 200, "d": 3, "k": 2, "spread": 0.4, "separation": 9.0,
                            "for": "two classes that really are separable, so the perceptron must converge"})
    store.put("px.exp.brain.data.ml.separable", separable)
    walked = calcs.call("perceptron_fit", {"data": separable, "target": "label", "seed": 97, "epochs": 60,
                                            "for": "the boundary the mistake rule walked to"})
    parts.result(store, VERTICAL, "perceptron", "separable", walked)
    truth = [row[-1] for row in core.as_rows(separable)]
    got = calcs.call("perceptron_predict", {"model": walked, "data": separable})["labels"]
    parts.oracle(
        store, VERTICAL, "perceptron_fit", "converges_on_a_separable_problem",
        [walked["converged"], got == truth], [True, True],
        "the perceptron convergence theorem, on a problem drawn to satisfy it", 0.0,
        "the one guarantee the perceptron has is that it stops on a separable problem; if it does not, the update is wrong",
    )

    network = calcs.call("mlp_fit", {"data": regression, "target": "y", "seed": 97, "hidden": 12,
                                      "lr": 0.05, "epochs": 300,
                                      "for": "a twelve-unit hidden layer fitted by sgd from one seed"})
    parts.result(store, VERTICAL, "mlp", "regression", {
        "for": network["for"], "model": "mlp", "hidden": network["hidden"], "seed": network["seed"],
        "learning_rate": network["learning_rate"], "epochs": network["epochs"],
        "loss_first": network["loss"][0], "loss_last": network["loss"][-1],
        "loss": network["loss"][::20]})
    predicted = calcs.call("mlp_predict", {"model": network, "data": regression})
    scored = calcs.call("regression_metrics", {"y_true": targets, "y_pred": predicted})
    parts.result(store, VERTICAL, "regression_metrics", "mlp_train", scored)
    closed = store.get("px.exp.brain.result.ml.linreg.regression_closed_np")
    closed_fit = calcs.call("linreg_predict", {"model": closed, "data": regression, "backend": "np"})
    closed_scored = calcs.call("regression_metrics", {"y_true": targets, "y_pred": closed_fit})
    parts.oracle(
        store, VERTICAL, "mlp_fit", "the_loss_falls_and_reaches_the_linear_fit",
        [network["loss"][-1] < network["loss"][0], scored["r2"] > 0.9 * closed_scored["r2"]], [True, True],
        "the closed-form least squares fit of the same rows, which is the right answer here", 0.0,
        "the data is linear, so the network has no excuse: it must at least get near the line",
    )
    parts.oracle(
        store, VERTICAL, "mlp_fit", "the_seed_is_the_whole_init",
        calcs.call("mlp_fit", {"data": regression, "target": "y", "seed": 97, "hidden": 4, "epochs": 5})["w1"],
        calcs.call("mlp_fit", {"data": regression, "target": "y", "seed": 97, "hidden": 4, "epochs": 5})["w1"],
        "the same calculation re-run from the same seed", 0.0,
        "a network whose init is not a function of its seed cannot be replayed from its record",
    )


@section
def validation(store):
    """the two loops, as Parts: k-fold scores per model, and the lasso path with its choice."""
    regression = store.get("px.exp.brain.data.ml.regression")
    folds = {}
    for name, fit, predict, fit_args in (
        ("linreg", "linreg_fit", "linreg_predict", {}),
        ("ridge_a1", "ridge_fit", "linreg_predict", {"alpha": 1.0, "backend": "np"}),
        ("forest", "forest_fit", "forest_predict", {"criterion": "mse", "n_trees": 10, "seed": 105, "max_depth": 5}),
    ):
        scored = calcs.call("cross_validate", {
            "data": regression, "target": "y", "seed": 105, "k": 5, "fit": fit, "predict": predict,
            "fit_args": fit_args, "metric": "mse",
            "for": f"{name} scored on every row of the same five folds, exactly once"})
        parts.result(store, VERTICAL, "cross_validate", name, scored)
        folds[name] = scored
    parts.oracle(
        store, VERTICAL, "cross_validate", "the_same_folds_for_every_model",
        [folds["linreg"]["sizes"], folds["forest"]["sizes"]],
        [folds["ridge_a1"]["sizes"], folds["ridge_a1"]["sizes"]],
        "the fold sizes of the seeded kfold every one of them was handed", 0.0,
        "two models compared on different folds are compared on the luck of the split, not on the model",
    )
    parts.oracle(
        store, VERTICAL, "cross_validate", "held_out_error_is_not_below_training_error",
        all(one["mean"] >= core.mean(one["train"]) - 1e-9 for one in folds.values()), True,
        "each model's own training error on the same folds", 0.0,
        "a held-out error below the training error means the fold leaked, and every number above it is worthless",
    )
    parts.oracle(
        store, VERTICAL, "cross_validate", "the_linear_truth_is_fitted_best_by_a_linear_model",
        folds["linreg"]["mean"] < folds["forest"]["mean"], True,
        "the same folds, a linear model and a forest, on data drawn from a linear truth", 0.0,
        "cross-validation is only worth having if it prefers the model that is actually right",
    )
    path = calcs.call("lasso_path", {
        "data": regression, "target": "y", "seed": 105, "k": 5,
        "alphas": [0.001, 0.01, 0.05, 0.1, 0.3, 1.0, 3.0, 10.0],
        "for": "where each column drops out as the penalty rises, and which penalty the folds prefer"})
    parts.result(store, VERTICAL, "lasso_path", "regression", path)
    parts.oracle(
        store, VERTICAL, "lasso_path", "columns_only_ever_drop_out",
        [path["monotone"], path["path"][-1]["count"]], [True, 0],
        "the l1 penalty's own definition: a larger penalty can only zero more coefficients", 0.0,
        "a path that is not monotone means the coordinate descent stopped somewhere that is not the minimum",
    )
    parts.oracle(
        store, VERTICAL, "lasso_path", "the_chosen_penalty_is_the_one_the_folds_preferred",
        path["chosen"], min(path["path"], key=lambda row: row["cv_mse"])["alpha"],
        "the cross-validated error the path itself recorded at every penalty", 0.0,
        "the choice has to be readable back out of the Part, or it is a number somebody remembered",
    )


@section
def distances(store):
    """the one matrix four calculations read, and the proof that the spelling does not move them."""
    from . import distance

    blobs = store.get("px.exp.brain.data.ml.blobs")
    rows = [row[:-1] for row in core.as_rows(blobs)]
    features = core.dataset("the blob features alone", core.columns_of(blobs)[:-1], rows)
    reference = sp_distance.cdist(np.asarray(rows), np.asarray(rows), metric="euclidean").tolist()
    for backend in distance.BACKENDS:
        got = distance.pairwise(rows, backend=backend)
        parts.oracle(
            store, VERTICAL, "pairwise", backend,
            got[:30], [row[:len(got)] for row in reference[:30]],
            "scipy.spatial.distance.cdist on the same rows", 1e-9,
            "the ml vertical stopped owning this matrix; every spelling of it still has to be the same matrix",
        )
    parts.result(store, VERTICAL, "pairwise", "worst_difference_between_spellings",
                 {"for": "how far apart the five spellings of the same matrix are",
                  "worst": distance.worst_difference(rows)})

    # the diagonal is where the identity spelling is at its weakest, so it is checked on its own.
    identity = distance.pairwise(rows, backend="gram")
    parts.oracle(
        store, VERTICAL, "pairwise", "gram_diagonal_is_zero",
        [identity[i][i] for i in range(len(rows))], [0.0] * len(rows),
        "a point's distance to itself, which is zero by definition", 0.0,
        "|x|^2 - 2|x|^2 + |x|^2 cancels to rounding and the square root turns 1e-14 into 1e-7; "
        "k=1 neighbour votes and dbscan's eps both read that number",
    )

    # the four calculations, each run through every spelling: the answers must be identical.
    labels = [int(row[-1]) for row in core.as_rows(blobs)]
    classification = store.get("px.exp.brain.data.ml.classification")
    knn = calcs.call("knn_fit", {"data": classification, "target": "label", "k": 5})
    for name, call in (
        ("kmeans", lambda b: calcs.call("kmeans", {"data": features, "k": 3, "seed": 131, "backend": b})["labels"]),
        ("silhouette", lambda b: calcs.call("silhouette", {"data": features, "labels": labels, "backend": b})["scores"]),
        ("knn_predict", lambda b: calcs.call("knn_predict", {"model": knn, "data": classification, "backend": b})["labels"]),
        ("dbscan", lambda b: calcs.call("dbscan", {"data": features, "eps": 2.0, "min_samples": 5, "backend": b})["labels"]),
    ):
        reference_answer = call("py")
        for backend in distance.BACKENDS[1:]:
            parts.oracle(
                store, VERTICAL, name, f"unmoved_by_{backend}",
                call(backend), reference_answer,
                f"the same calculation on the py spelling of the same distances", 1e-9,
                "routing a calculation through a faster matrix is a backend change; if the answer moves it is a rewrite",
            )
    for backend in distance.BACKENDS:
        parts.bench(
            store, VERTICAL, "pairwise", backend, "n90_d2",
            lambda backend=backend: distance.pairwise(rows, backend=backend), 5,
            "the small case: where the python loop is still competitive and the array spellings pay their setup",
        )


@section
def multiclass_and_second_order(store):
    """the softmax and the logistic booster, on problems already in the store."""
    from . import multiclass

    data = store.get("px.exp.brain.data.ml.classification")
    matrix, targets, _ = core.xy(data, "label")
    design = np.hstack([np.ones((len(matrix), 1)), np.asarray(matrix)])
    classes = sorted(set(targets))
    model = calcs.call("softmax_fit", {"data": data, "target": "label", "backend": "np",
                                        "lr": 1.0, "epochs": 4000, "l2": 1.0,
                                        "for": "every class fitted at once against one denominator"})
    parts.result(store, VERTICAL, "softmax", "classification",
                 {k: model[k] for k in ("for", "model", "backend", "target", "columns", "classes",
                                        "l2", "pinned_class", "intercepts", "coefs", "epochs", "loss", "n")})
    n, width = design.shape
    free = len(classes) - 1
    y = np.zeros((n, len(classes)))
    for i, t in enumerate(targets):
        y[i, classes.index(t)] = 1.0

    def loss(flat):
        w = flat.reshape(free, width)
        scores = np.hstack([design @ w.T, np.zeros((n, 1))])
        scores = scores - scores.max(1, keepdims=True)
        e = np.exp(scores)
        p = e / e.sum(1, keepdims=True)
        return float(-np.log(np.maximum((p * y).sum(1), 1e-300)).mean()
                     + 0.5 * 1.0 * float((w[:, 1:] ** 2).sum()) / n)

    best = optimize.minimize(loss, np.zeros(free * width), method="L-BFGS-B",
                             options={"ftol": 1e-15, "gtol": 1e-12, "maxiter": 20000})
    parts.oracle(
        store, VERTICAL, "softmax_fit", "reaches_the_cross_entropy_optimum",
        model["loss"][-1], float(best.fun),
        "scipy.optimize.minimize on the same penalised cross-entropy, same pinned class", 1e-3,
        "a softmax that stops short of the optimum is a one-vs-rest with extra steps",
    )
    proba = calcs.call("softmax_proba", {"model": model, "data": data})
    parts.oracle(
        store, VERTICAL, "softmax_proba", "is_a_distribution_without_renormalising",
        [round(math.fsum(row), 12) for row in proba["proba"]], [1.0] * len(proba["proba"]),
        "the definition of a softmax: one shared denominator", 1e-12,
        "one-vs-rest divides k sigmoids by their sum afterwards; this is the model that never needed to",
    )
    truth = [row[-1] for row in core.as_rows(data)]
    scored = calcs.call("classification_metrics",
                        {"y_true": truth,
                         "y_pred": calcs.call("softmax_predict", {"model": model, "data": data})["labels"]})
    parts.result(store, VERTICAL, "classification_metrics", "softmax_train", scored)
    entropy = calcs.call("cross_entropy", {"y_true": truth, "y_pred": proba})
    parts.result(store, VERTICAL, "cross_entropy", "softmax_train", entropy)
    rest = store.get("px.exp.brain.result.ml.logreg.classification")
    rest_proba = calcs.call("logreg_proba", {"model": rest, "data": data})
    rest_entropy = calcs.call("cross_entropy", {"y_true": truth, "y_pred": rest_proba})
    parts.result(store, VERTICAL, "cross_entropy", "one_vs_rest_train", rest_entropy)
    parts.oracle(
        store, VERTICAL, "softmax_fit", "beats_one_vs_rest_on_the_loss_it_optimises",
        entropy["mean"] <= rest_entropy["mean"], True,
        "the same rows scored by cross-entropy under both multiclass models", 0.0,
        "the two models predict nearly the same labels; the difference is in the probabilities, "
        "and cross-entropy is the one measure that can see it",
    )

    # the booster on the logistic loss, against the squared-loss one it replaces.
    binary = store.get("px.exp.brain.data.ml.binary")
    binary_truth = [row[-1] for row in core.as_rows(binary)]
    boosted = calcs.call("logistic_gbm_fit", {"data": binary, "target": "label", "n_trees": 30,
                                               "learning_rate": 0.25, "max_depth": 2,
                                               "for": "thirty newton corrections on the logistic loss"})
    parts.result(store, VERTICAL, "logistic_gbm", "binary", {
        "for": boosted["for"], "model": "logistic_gbm", "classes": boosted["classes"],
        "init": boosted["init"], "learning_rate": boosted["learning_rate"],
        "n_trees": boosted["n_trees"], "max_depth": boosted["max_depth"],
        "train_loss": boosted["train_loss"], "nodes": [tree["nodes"] for tree in boosted["trees"]]})
    losses = boosted["train_loss"]
    parts.oracle(
        store, VERTICAL, "logistic_gbm_fit", "the_loss_never_goes_up",
        all(after <= before + 1e-9 for before, after in zip(losses, losses[1:])), True,
        "the logistic loss the fit recorded after each of its own corrections", 0.0,
        "a newton step that overshoots raises the loss; that is exactly what the second derivative is for",
    )
    base = math.fsum(1.0 for t in binary_truth if t == boosted["classes"][1]) / len(binary_truth)
    parts.oracle(
        store, VERTICAL, "logistic_gbm_fit", "starts_at_the_base_rate",
        1.0 / (1.0 + math.exp(-boosted["init"])), base,
        "the proportion of the positive class, which is the best constant prediction", 1e-9,
        "a booster that starts anywhere else spends its first trees walking back to the base rate",
    )
    predicted = calcs.call("logistic_gbm_predict", {"model": boosted, "data": binary})
    scored = calcs.call("classification_metrics", {"y_true": binary_truth, "y_pred": predicted["labels"]})
    parts.result(store, VERTICAL, "classification_metrics", "logistic_gbm_binary", scored)
    auc = calcs.call("roc_auc", {"y_true": binary_truth, "y_pred": [p[1] for p in predicted["proba"]],
                                  "positive": boosted["classes"][1]})
    parts.result(store, VERTICAL, "roc_auc", "logistic_gbm_binary", auc)
    linear_auc = store.get("px.exp.brain.result.ml.roc_auc.logreg_binary")["auc"]
    parts.oracle(
        store, VERTICAL, "logistic_gbm_predict", "at_least_as_separating_as_the_linear_model",
        auc["auc"] >= linear_auc - 0.02, True,
        "the area under the curve of the logistic regression on the same rows", 0.0,
        "a booster that cannot match a straight line on a nearly linear problem is mis-wired, not flexible",
    )
    for backend in ("py", "np"):
        parts.bench(
            store, VERTICAL, "softmax_fit", backend, "n300_d4_k3_400epochs",
            lambda backend=backend: calcs.call(
                "softmax_fit", {"data": data, "target": "label", "backend": backend, "epochs": 400}), 3,
            "every epoch is one n-by-k score matrix and one k-by-d gradient: all matmul, no solve",
        )


@section
def out_of_bag(store):
    """the held-out number the forest gets for free, against one somebody paid for."""
    data = store.get("px.exp.brain.data.ml.trees")
    truth = [row[-1] for row in core.as_rows(data)]
    forest = calcs.call("forest_fit", {"data": data, "target": "label", "n_trees": 25,
                                        "seed": 141, "max_depth": 6,
                                        "for": "twenty-five trees, each with a third of the rows held back from it"})
    oob = calcs.call("forest_oob", {"model": forest})
    parts.result(store, VERTICAL, "forest_oob", "trees", {
        "for": oob["for"], "metric": oob["metric"], "score": oob["score"],
        "scored": oob["scored"], "uncovered": len(oob["uncovered"]),
        "mean_voters": oob["mean_voters"], "n_trees": oob["n_trees"]})
    fitted = calcs.call("classification_metrics", {
        "y_true": truth,
        "y_pred": calcs.call("forest_predict", {"model": forest, "data": data})["labels"]})
    parts.oracle(
        store, VERTICAL, "forest_oob", "is_below_the_training_score",
        oob["score"] < fitted["accuracy"], True,
        "the same forest scored on the rows it was fitted to", 0.0,
        "a forest deep enough to memorise its training rows scores 1.0 on them; the out-of-bag number is the one worth reading",
    )
    split = calcs.call("train_test_split", {"data": data, "seed": 141, "test_size": 0.3, "stratify": "label"})
    honest = calcs.call("forest_fit", {"data": core.take(data, split["train_index"]), "target": "label",
                                        "n_trees": 25, "seed": 141, "max_depth": 6})
    held_out = core.take(data, split["test_index"])
    paid_for = calcs.call("classification_metrics", {
        "y_true": [row[-1] for row in core.as_rows(held_out)],
        "y_pred": calcs.call("forest_predict", {"model": honest, "data": held_out})["labels"]})["accuracy"]
    parts.result(store, VERTICAL, "classification_metrics", "forest_held_out",
                 {"for": "the same forest's accuracy on a real held-out third", "accuracy": paid_for})
    parts.oracle(
        store, VERTICAL, "forest_oob", "agrees_with_a_held_out_split",
        oob["score"], paid_for,
        "a stratified 30 percent split, fitted and scored separately", 0.08,
        "the out-of-bag score costs nothing; the only question is whether it says the same thing as the score that costs a third of the data",
    )
    share = core.mean([float(size) / forest["n"] for size in forest["oob_sizes"]])
    parts.oracle(
        store, VERTICAL, "forest_fit", "a_bootstrap_leaves_out_about_a_third",
        0.30 < share < 0.42, True,
        "1/e, the share of rows a bootstrap of n draws with replacement misses", 0.0,
        "if the bags are not really bootstraps the out-of-bag rows are not really held out, and the free number is not free",
    )


# --- the map and the findings ------------------------------------------------


def map_and_findings(store):
    built = list(store.brain_addresses())
    stubbed = list(STUBBED)
    parts.map_part(
        store, VERTICAL, built, stubbed, NEXT,
        "the territory of the ml vertical, readable through PQL without opening a file",
    )
    for k, value in FINDINGS.items():
        payload = dict(value)
        parts.finding(store, VERTICAL, k, payload.pop("kind"), payload.pop("text"), payload.pop("for"), **payload)


STUBBED = [
    {"address": "fn.brain.ml.logistic_gbm_fit multiclass", "why": "the booster is two-class; the k-class version boosts k scores against the softmax loss and needs its own oracle"},
    {"address": "fn.brain.ml.softmax_fit newton", "why": "the softmax is fitted by gradient descent only; its hessian is k*d by k*d and the logistic bracket's lesson says the solve would still pay"},
    {"address": "fn.brain.ml.cross_validate nested", "why": "the penalty on the lasso path is chosen on the same folds it is scored on, so that score is optimistic and an outer loop is what fixes it"},
    {"address": "fn.brain.ml.mlp_fit deep", "why": "the backward pass is hand-derived for exactly one hidden layer; a second layer needs autograd or another hand derivation, and a half-checked one is worth less than none"},
    {"address": "fn.brain.ml.knn_fit approximate", "why": "the exact vote is the reference; a kd-tree or ball-tree is a backend of it, and belongs after the shared pairwise-distance primitive"},
]

NEXT = [
    {"what": "the same facade treatment for sort/select-k and for the histogram, both of which exist in the backend vertical already",
     "for": "knn re-sorts a row it could select-k, and the tree's binned split search is a histogram; both are primitives this vertical still owns copies of"},
    {"what": "a chosen default per calculation, read off the brackets rather than set by hand",
     "for": "four brackets now name a winner and every calculation still defaults to the py reference; the gap between what the evidence says and what the code does is the next honest thing to close"},
    {"what": "elastic net, and the same path treatment for ridge and for the tree depth",
     "for": "the lasso path made the choice readable; every other model here still takes its hyper-parameter on faith"},
    {"what": "a multiclass booster over the softmax loss, and out-of-bag feature importance from the same bags",
     "for": "the booster is two-class; and the bags that give a free held-out score also give a free importance, by permuting one column of the out-of-bag rows"},
    {"what": "nested cross-validation, so a hyper-parameter chosen on the folds is not also scored on them",
     "for": "lasso_path picks its penalty on the same folds it reports; that number is optimistic and the Part should say so"},
    {"what": "a deeper network, softmax output and mini-batch shuffling through the effects handle rather than a seed",
     "for": "one hidden layer and one output is where this stops; the next step needs a real autograd or an honest admission that it is hand-derived"},
]

FINDINGS = {
    "the-bag-a-tree-drew-is-a-held-out-set-nobody-paid-for": {
        "kind": "strength",
        "text": "a bootstrap of n rows misses about 1/e of them, so every tree in the forest already has a test set and the forest already has a held-out score: 0.94 out-of-bag against 1.00 on the rows it was fitted to, and within 8 points of what a real stratified 30 percent split says. it is a Part, it comes out of the same fit, and it costs no data.",
        "for": "every other honest number in this vertical costs a third of the rows; this one is the only one that does not, and it is the one a small dataset most needs",
    },
    "python-3-12-changed-sum-so-pure-python-data-is-not-portable": {
        "kind": "friction",
        "text": "the owner's machine (python 3.12.3, numpy 2.5.3) failed this vertical's committed-store test, and the measured 1.8e-15 difference was blamed on numpy's accumulation order. it was not numpy. python 3.12 changed the built-in sum() to neumaier compensated summation, so every pure-python float sum in this vertical -- including the one line that builds a synthetic target, y = intercept + sum(w*x) + noise -- returns a different last ulp on 3.11 and on 3.12. that ulp then chooses a different split threshold in a tree, and a cross-validated forest score moved in its third significant digit.",
        "for": "every seeded dataset in the brain is built in pure python precisely so it is reproducible; an interpreter upgrade silently took that away, and the failure surfaced two verticals downstream as a store that would not match itself",
        "workaround": "every float sum that feeds stored data, a model coefficient or a metric is math.fsum, which is exactly rounded and therefore the same number on any interpreter; the two stacks now produce byte-identical store documents",
        "proposal": "the contract should say it: a Calculation that sums floats uses math.fsum, and the harness's own helpers do too. a reference implementation whose answer depends on the interpreter's summation strategy is not a reference",
    },
    "a-part-has-to-be-canonical-or-it-records-the-machine": {
        "kind": "strength",
        "text": "Store.document() rounds every float to twelve significant digits, an oracle Part's numbers to eight, and anything a thousand times below an oracle's own declared tolerance to the zero that oracle already said it was. what is left is a document that is a function of the calculation: the same bytes under python 3.11 with numpy 2.4 and under python 3.12.3 with numpy 2.5.3, which is what makes 'the committed store matches a fresh build' a test anyone can run rather than a test that passes on one machine.",
        "for": "a store that differs by a last ulp between two builds of numpy turns every landing on another machine red, and the receipt says nothing about which half was wrong",
    },
    "a-store-file-is-merged-over-so-nothing-can-be-withdrawn": {
        "kind": "friction",
        "text": "harness.Store.save merges what this process wrote over what the file already holds. rename a finding or drop a Part and the old address stays in store/ml.json forever, with nothing in the code that produces it; the vertical's own test that the committed store matches a fresh build is what caught it, and only because the rename happened to be in the same landing.",
        "for": "a store nobody can retract from is an append-only log pretending to be a state, and the map reads it as state",
        "workaround": "this vertical writes its own file whole, because it never loads another vertical's parts, so its document is the complete set",
        "proposal": "harness.Store.save(vertical, merge=False) for a vertical that owns its file outright, or a save that drops any address under this vertical's own prefixes that this process did not write",
    },
    "a-record-inlines-values-that-are-already-parts": {
        "kind": "friction",
        "text": "run_record renders every produced value into the record, so a 300-row dataset Part is written twice: once in store/ml.json and again, in full, inside records/ml.classification.json. this vertical's records are 200kb each and the duplication is all of it. the address and the digest are already in the record; the value is not new information.",
        "for": "records are supposed to make a run replayable and auditable; at this rate the record of a real dataset is unreadable and unreviewable, and a landing diff is dominated by it",
        "workaround": "the datasets a bracket only needs as input are stored as a recipe Part (the calculation and its args) rather than as rows, so the record carries the seed instead of the draw",
        "proposal": "run_record should write a reference (address plus produce_sha256) instead of the value whenever the value is published to a Part in the same store, with the full rendering kept for values that are not",
    },
    "the-bracket-refuses-to-be-judged-before-its-criteria-exist": {
        "kind": "strength",
        "text": "harness.bracket refuses a bracket with no criteria, harness.judge refuses a score for a criterion the bracket did not record and refuses a judge whose name is one of the candidate branches, and harness.decide refuses to decide while any candidate is unjudged. writing the criteria first stopped being a discipline and became a thing the code will not let you skip.",
        "for": "the one failure mode of a tournament is choosing the criteria after seeing the numbers; a rule that is enforced by the store is worth more than a rule in a contract",
    },
    "one-address-scheme-made-the-map-free": {
        "kind": "strength",
        "text": "because every part is at px.exp.brain.<kind>.<vertical>.<name>, the map Part's built list is literally the store's own address list, and the shared map module counts kinds and verticals with prefix queries and nothing else. no vertical had to register anything or tell anyone what it had made.",
        "for": "the brief asks for the territory as Parts readable through PQL; the address scheme is why that cost nothing to produce and nothing to keep true",
    },
    "a-run-record-cannot-be-committed-while-it-holds-a-stopwatch": {
        "kind": "friction",
        "text": "pyto.materialize.run_record puts wall-clock readings (counters.wall_ms, each invocation's duration_ms) into the record, so the file's bytes change on every run. committed, it conflicts between any two branches that both re-ran the program, and any suite that regenerates it leaves the tree dirty behind a landing. it cost this vertical three refused landings and two other verticals one each.",
        "for": "the contract asks for a record of every PCR run in every landing; a record that cannot be committed cleanly is not a record anyone keeps",
        "workaround": "parts.settle() blanks every *_ms key before write_record, so the file is a function of the run and not of the stopwatch; the timings that are a claim live in benchmark Parts, which say how many samples they are the median of",
        "proposal": "run_record should take timings='measured'|'blank' (or write them to a sibling file), so the durable half of a record and the unrepeatable half are not the same bytes",
    },
    "a-clustering-fixture-can-fail-for-the-generator-not-the-algorithm": {
        "kind": "friction",
        "text": "synthetic_blobs drew k centres from one normal and hoped: at several seeds two centres landed closer than a standard deviation, and k-means was blamed for not separating blobs that were never separate. the same trap is waiting in every seeded fixture that draws a structure and then tests for it.",
        "for": "a test that fails for its fixture teaches the reader to loosen the assertion, which is how a real regression gets through",
        "workaround": "the generator now redraws centres from the same seeded stream until their minimum pairwise distance clears a multiple of the spread, and scales them apart if it cannot",
        "proposal": "harness.synthetic should take the structure it is drawing (blobs, classes, a low-rank matrix) and guarantee the property the caller is about to test for, rather than returning a draw and leaving the property to luck",
    },
    "an-approximate-backend-needs-a-different-oracle-than-an-exact-one": {
        "kind": "strength",
        "text": "the histogram split search is not the sorting one to 1e-9 and never will be: it scans bin edges, not midpoints. its oracle is not equality but the held-out accuracy of the exact tree within a stated margin, recorded in the same oracle Part shape as every exact one.",
        "for": "the contract's rule is that a backend which changes semantics is a failed backend; an approximation is a different calculation, and saying so in the oracle is what keeps the rule enforceable",
    },
    "seeded-init-is-what-makes-two-clusterings-comparable": {
        "kind": "strength",
        "text": "all three k-means branches read one Stream built from args['seed'] for the k-means++ init, so py, np and the gram-matrix branch start from the same centres and their oracle is exact equality of labels and inertia. without that the bracket would be comparing dice.",
        "for": "clustering is the family where nobody can tell a faster implementation from a luckier one, unless the seed is an argument",
    },
    "newton-beats-descent-once-the-hessian-is-one-matmul": {
        "kind": "strength",
        "text": "the logistic bracket says it plainly: on 400 rows and 6 columns, newton/irls through numpy is about 22 times faster than the same steps in python and about 200 times faster than full-batch gradient descent, and all three land on scipy's penalised optimum. the cost of newton is a solve per step, and one weighted matmul pays for it.",
        "for": "gradient descent is the default in most teaching code; on this shape it is the slowest correct answer, and the bracket is the evidence rather than the opinion",
    },
    "a-linear-speed-criterion-is-decided-by-its-slowest-branch": {
        "kind": "friction",
        "text": "scored on raw milliseconds, the bracket's winner flipped: min-max normalising wall time across candidates lets one slow branch compress the fast ones into a rounding difference, and a docstring then decided a 22x speed gap.",
        "for": "a tournament whose verdict is an artefact of its normalisation teaches the wrong lesson and is worse than no tournament",
        "workaround": "the criterion recorded in the bracket is a speed band computed from every candidate's median, so a constant factor is a constant distance whatever the spread of the field, and a difference inside the machine's noise is no distance at all",
        "proposal": "harness.decide should offer a log or a banded normalisation per criterion, declared in the criterion next to its direction and weight, so timing criteria are not silently linear",
    },
    "one-pairwise-distance-was-recomputed-by-four-calculations": {
        "kind": "friction",
        "text": "knn_predict, silhouette, k-means and dbscan each built the same n-by-n euclidean matrix, each with their own np spelling of it: the identity |a-b|^2 = |a|^2 - 2ab + |b|^2 was written twice in this vertical and once more in the backend vertical. this is resolved: ml/distance.py is the one facade, and two of its five spellings are fn.brain.backend.pairwise on the backend vertical's own engines. the bracket px.exp.brain.bracket.ml.pairwise_spelling says the scipy engine wins, and all four calculations are oracled as unmoved by the change.",
        "for": "it is the hottest kernel in the unsupervised half, and four copies meant four places for a backend to change semantics quietly",
        "workaround": "none needed now; the route to it was to build the facade, oracle every spelling against scipy cdist, and oracle every one of the four calculations as giving the same answer through each",
        "proposal": "the same treatment for the other primitives the verticals are each re-spelling: sort/select-k (knn and the tree split search both want it) and the histogram (the tree's binned search is one, and so is every distribution fit in the stats vertical)",
    },
    "a-bracket-decided-inside-its-own-timing-noise-is-not-re-runnable": {
        "kind": "friction",
        "text": "the pairwise bracket's top two branches were within a few percent of each other, and the winner flipped between runs of the same code on the same machine: the store said one, the re-run said the other, and the test that re-runs every bracket caught it. a tournament whose verdict is not reproducible is a coin toss with a receipt.",
        "for": "the whole value of a bracket is that someone else can re-run it and get the same answer; a flipping winner discredits every bracket in the store, not just this one",
        "workaround": "the speed criterion recorded in the bracket is a band, not a time: the medians are sorted and cut wherever the next is more than 1.4 times the fastest in the band, so two branches within 40 percent share a band and harness.decide breaks the tie by name, deterministically. rounding the log was not enough -- two branches 4 percent apart still fell either side of a rounding boundary",
        "proposal": "harness.bench should record the spread it saw (min, median and max, or an interquartile range) and harness.decide should refuse to separate two candidates whose intervals overlap -- a tie is an honest verdict and the current decide cannot express one",
    },
    "the-fastest-spelling-of-a-distance-is-the-least-accurate-one": {
        "kind": "friction",
        "text": "the squared-distance identity is the fastest way to an n-by-n matrix and the only one that is wrong on its own diagonal: |x|^2 - 2|x|^2 + |x|^2 cancels to about 1e-14 of rounding, and the square root turns that into 1e-7. seven digits. k=1 neighbour votes read exactly that number, and so does dbscan's eps comparison.",
        "for": "a tournament that scores speed and correctness separately will hand the win to a spelling that is quietly wrong in the one place nobody benchmarks",
        "workaround": "the facade pins the diagonal of a self-matrix to the zero it is and clamps the rest at zero, and an oracle Part checks the diagonal on its own, separately from the matrix",
        "proposal": "fn.brain.backend.pairwise should do the same clamp and diagonal pin in its np engine, and its oracle should include the self-matrix diagonal; the scipy engine already does",
    },
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
    # save=False is a test, and a test writes neither the tracked store nor the records.
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
    for kind, row in sorted(view["counts"].items()):
        if "ml" in row:
            print(f"  {kind:<9} {row['ml']}")
    failed = [one["address"] for one in view["oracles"]["failed"] if ".ml." in one["address"]]
    print(f"  oracles   {view['oracles']['total'] - len(failed)} of {view['oracles']['total']} passing")
    print(f"  findings  {len([f for f in view['findings'] if f['address'].startswith('proposal.brain.ml.')])}")
    if failed:
        for address in failed:
            print(f"  FAILED    {address}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
