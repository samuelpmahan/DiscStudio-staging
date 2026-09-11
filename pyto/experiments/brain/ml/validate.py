"""the loops that were still written at every call site: cross-validation and a lasso path.

both are Parts: one row per fold, one row per penalty, so a choice made from them is
a choice someone else can read back out of the store without re-running anything.
"""

from __future__ import annotations

from . import core


def cross_validate(args):
    """fn.brain.ml.cross_validate -- fit, predict and score once per fold, as one part.

    the fold assignment is the seeded kfold calculation, so the same seed is the same
    folds for every model and two models can be compared on the rows, not on the luck.
    """
    from . import calcs

    data, target = args["data"], args["target"]
    fit_name, predict_name = args["fit"], args["predict"]
    fit_args = dict(args.get("fit_args", {}))
    metric = args.get("metric", "mse")
    folds = calcs.call("kfold", {"data": data, "seed": args["seed"], "k": int(args.get("k", 5))})
    at = core.columns_of(data).index(target)
    rows = core.as_rows(data)
    scores, train_scores, sizes = [], [], []
    for fold in folds["folds"]:
        train = core.take(data, fold["train_index"])
        test = core.take(data, fold["test_index"])
        model = calcs.call(fit_name, dict(fit_args, data=train, target=target))
        scores.append(_score(calcs, [rows[i][at] for i in fold["test_index"]],
                             calcs.call(predict_name, {"model": model, "data": test}), metric))
        train_scores.append(_score(calcs, [rows[i][at] for i in fold["train_index"]],
                                   calcs.call(predict_name, {"model": model, "data": train}), metric))
        sizes.append(len(fold["test_index"]))
    return {
        "for": args.get("for", f"{fit_name} scored on every row exactly once"),
        "fit": fit_name,
        "metric": metric,
        "seed": int(args["seed"]),
        "k": folds["k"],
        "sizes": sizes,
        "test": scores,
        "train": train_scores,
        "mean": core.mean(scores),
        "spread": max(scores) - min(scores),
        "worst": max(scores) if metric in ("mse", "mae") else min(scores),
    }


def _score(calcs, truth, prediction, metric):
    from . import metrics

    guess = metrics.numbers_in(prediction)
    if metric == "accuracy":
        return calcs.call("classification_metrics", {"y_true": truth, "y_pred": guess})["accuracy"]
    return calcs.call("regression_metrics", {"y_true": truth, "y_pred": guess})[metric]


def lasso_path(args):
    """fn.brain.ml.lasso_path -- the coefficients and the surviving columns at every penalty.

    one alpha is a guess. the path is the thing worth reading: where each column drops
    out, and which penalty the cross-validated error actually prefers.
    """
    from . import calcs

    data, target = args["data"], args["target"]
    alphas = list(args.get("alphas", [0.001, 0.01, 0.05, 0.1, 0.3, 1.0, 3.0, 10.0]))
    backend = args.get("backend", "np")
    rows = []
    for alpha in alphas:
        model = calcs.call("lasso_fit", {"data": data, "target": target, "alpha": alpha, "backend": backend})
        row = {"alpha": alpha, "coef": model["coef"], "nonzero": model["nonzero"],
               "count": len(model["nonzero"]), "intercept": model["intercept"]}
        if args.get("seed") is not None:
            scored = cross_validate({
                "data": data, "target": target, "seed": args["seed"], "k": int(args.get("k", 5)),
                "fit": "lasso_fit", "predict": "linreg_predict",
                "fit_args": {"alpha": alpha, "backend": backend}, "metric": "mse"})
            row["cv_mse"] = scored["mean"]
        rows.append(row)
    best = None
    if args.get("seed") is not None:
        best = min(rows, key=lambda r: r["cv_mse"])["alpha"]
    return {
        "for": args.get("for", "where each column drops out as the penalty rises"),
        "columns": core.columns_of(data),
        "target": target,
        "alphas": alphas,
        "path": rows,
        "chosen": best,
        "monotone": all(a["count"] >= b["count"] for a, b in zip(rows, rows[1:])),
    }
