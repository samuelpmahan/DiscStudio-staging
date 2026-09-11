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
from scipy.spatial import distance

from . import calcs, core, linear, metrics, parts, resample, tournament

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
    d = distance.cdist(np.asarray(rows), np.asarray(knn["rows"]), metric="euclidean")
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
    {"address": "fn.brain.ml.lasso_fit", "why": "coordinate descent is queued behind the classifiers; ridge covers the penalised case today"},
    {"address": "fn.brain.ml.dbscan", "why": "density clustering is behind k-means and the hierarchies in the queue"},
    {"address": "fn.brain.ml.logreg_fit multinomial", "why": "multiclass is one-vs-rest, not a softmax; the softmax needs its own oracle and is not worth a half-checked one"},
    {"address": "fn.brain.ml.knn_fit approximate", "why": "the exact vote is the reference; a kd-tree or ball-tree is a backend of it, and belongs after the shared pairwise-distance primitive"},
]

NEXT = [
    {"what": "cart, a small forest and small gradient boosting",
     "for": "the non-linear half; the split-search is the one place the py backend will really hurt"},
    {"what": "k-means with a seeded k-means++ init, and pca through svd",
     "for": "unsupervised needs the same parts discipline, and silhouette is already here to score it"},
    {"what": "a pairwise-distance calculation on the backend vertical, and knn/k-means/silhouette routed through it",
     "for": "three calculations recompute the same n-by-n matrix; one backend primitive would serve all three"},
]

FINDINGS = {
    "newton-beats-descent-once-the-hessian-is-one-matmul": {
        "kind": "strength",
        "text": "the logistic bracket says it plainly: on 400 rows and 6 columns, newton/irls through numpy is about 22 times faster than the same steps in python and about 200 times faster than full-batch gradient descent, and all three land on scipy's penalised optimum. the cost of newton is a solve per step, and one weighted matmul pays for it.",
        "for": "gradient descent is the default in most teaching code; on this shape it is the slowest correct answer, and the bracket is the evidence rather than the opinion",
    },
    "a-linear-speed-criterion-is-decided-by-its-slowest-branch": {
        "kind": "friction",
        "text": "scored on raw milliseconds, the bracket's winner flipped: min-max normalising wall time across candidates lets one slow branch compress the fast ones into a rounding difference, and a docstring then decided a 22x speed gap.",
        "for": "a tournament whose verdict is an artefact of its normalisation teaches the wrong lesson and is worse than no tournament",
        "workaround": "the criterion recorded in the bracket is log2 of the median, so a constant factor is a constant distance whatever the spread of the field",
        "proposal": "harness.decide should offer a log or a rank normalisation per criterion, declared in the criterion next to its direction and weight, so timing criteria are not silently linear",
    },
    "one-pairwise-distance-is-recomputed-by-three-calculations": {
        "kind": "friction",
        "text": "knn_predict, silhouette and (next) k-means each build the same n-by-n euclidean matrix, each with their own np spelling of it. the identity |a-b|^2 = |a|^2 - 2ab + |b|^2 is written twice already in this vertical.",
        "for": "it is the single hottest kernel in the unsupervised half, and three copies means three places for a backend to change semantics",
        "workaround": "knn_predict uses the matmul identity, silhouette uses the broadcast subtraction; both are oracled against scipy cdist so at least they agree",
        "proposal": "fn.brain.backend.pairwise(metric) as one calculation in the backend vertical, with knn, silhouette, k-means and dbscan routed through it and one oracle against scipy.spatial.distance.cdist covering all four",
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
    store = store or parts.Store(VERTICAL)
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
