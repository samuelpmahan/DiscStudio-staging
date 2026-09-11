"""the two multiclass models the one-vs-rest ones were standing in for.

softmax logistic regression fits every class at once against one shared denominator,
so its probabilities are a distribution by construction rather than by renormalising
k independent sigmoids afterwards. logistic-loss boosting is the same trade one level
up: the squared-loss booster fits the residual, and this one fits the gradient and
takes the newton step the second derivative asks for, per leaf.
"""

from __future__ import annotations

import math

from . import core, trees


def _rows_for(model, data):
    columns = core.columns_of(data)
    missing = [c for c in model["columns"] if c not in columns]
    if missing:
        raise KeyError(f"the model needs columns this dataset does not have: {missing}")
    at = [columns.index(c) for c in model["columns"]]
    return [[float(row[i]) for i in at] for row in core.as_rows(data)]


def softmax(scores):
    """exp over a shared denominator, shifted by the largest score so nothing overflows."""
    top = max(scores)
    exponentials = [math.exp(s - top) for s in scores]
    total = math.fsum(exponentials)
    return [e / total for e in exponentials]


# --- softmax logistic regression ---------------------------------------------


def softmax_fit(args):
    """fn.brain.ml.softmax_fit -- multinomial logistic regression by gradient descent.

    the last class is pinned to zero weights, which is what makes the optimum unique:
    a softmax is invariant to adding the same vector to every class, so without the
    pin there is a flat direction and two runs land in different places.
    """
    data, target = args["data"], args["target"]
    backend = core.backend_of(args)
    l2 = float(args.get("l2", 1.0))
    lr, epochs = float(args.get("lr", 0.5)), int(args.get("epochs", 400))
    matrix, targets, features = core.xy(data, target)
    design = core.add_bias(matrix)
    classes = sorted(set(targets))
    if len(classes) < 2:
        raise ValueError("a classifier needs at least two classes in the target column")
    free = len(classes) - 1
    n, width = len(design), len(design[0])
    index = {label: i for i, label in enumerate(classes)}
    losses = []
    if backend == "np" and core.numpy() is not None:
        np = core.numpy()
        x = np.asarray(design, dtype=float)
        y = np.zeros((n, len(classes)))
        for i, t in enumerate(targets):
            y[i, index[t]] = 1.0
        w = np.zeros((free, width))
        for _ in range(epochs):
            scores = np.hstack([x @ w.T, np.zeros((n, 1))])
            scores = scores - scores.max(1, keepdims=True)
            exponentials = np.exp(scores)
            p = exponentials / exponentials.sum(1, keepdims=True)
            losses.append(float(-np.log(np.maximum((p * y).sum(1), 1e-300)).mean()
                                + 0.5 * l2 * float((w[:, 1:] ** 2).sum()) / n))
            gradient = (p[:, :free] - y[:, :free]).T @ x / n
            gradient[:, 1:] += l2 * w[:, 1:] / n
            w = w - lr * gradient
        # the loss recorded inside the loop is the loss *before* that step; one more,
        # after the last step, is the loss of the weights this part actually returns.
        scores = np.hstack([x @ w.T, np.zeros((n, 1))])
        scores = scores - scores.max(1, keepdims=True)
        exponentials = np.exp(scores)
        p = exponentials / exponentials.sum(1, keepdims=True)
        losses.append(float(-np.log(np.maximum((p * y).sum(1), 1e-300)).mean()
                            + 0.5 * l2 * float((w[:, 1:] ** 2).sum()) / n))
        weights = w.tolist()
    else:
        weights = [[0.0] * width for _ in range(free)]
        for _ in range(epochs):
            gradient = [[0.0] * width for _ in range(free)]
            loss = 0.0
            for row, t in zip(design, targets):
                scores = [math.fsum(wk[j] * row[j] for j in range(width)) for wk in weights] + [0.0]
                p = softmax(scores)
                loss -= math.log(max(p[index[t]], 1e-300))
                for k in range(free):
                    error = p[k] - (1.0 if index[t] == k else 0.0)
                    for j in range(width):
                        gradient[k][j] += error * row[j] / n
            penalty = 0.5 * l2 * math.fsum(wk[j] ** 2 for wk in weights for j in range(1, width)) / n
            losses.append(loss / n + penalty)
            for k in range(free):
                for j in range(width):
                    if j:
                        gradient[k][j] += l2 * weights[k][j] / n
                    weights[k][j] -= lr * gradient[k][j]
        losses.append(_softmax_loss(design, targets, weights, index, l2))
    return {
        "for": args.get("for", "one fit of every class against one shared denominator"),
        "model": "softmax",
        "backend": backend,
        "target": target,
        "columns": features,
        "classes": classes,
        "l2": l2,
        "pinned_class": classes[-1],
        "intercepts": [w[0] for w in weights] + [0.0],
        "coefs": [w[1:] for w in weights] + [[0.0] * (width - 1)],
        "epochs": epochs,
        "loss": losses[:: max(1, len(losses) // 20)] + [losses[-1]],
        "n": n,
    }


def _softmax_loss(design, targets, weights, index, l2):
    """the penalised cross-entropy of exactly these weights, for the pure-python backend."""
    n, width = len(design), len(design[0])
    total = 0.0
    for row, t in zip(design, targets):
        scores = [math.fsum(wk[j] * row[j] for j in range(width)) for wk in weights] + [0.0]
        total -= math.log(max(softmax(scores)[index[t]], 1e-300))
    penalty = 0.5 * l2 * math.fsum(wk[j] ** 2 for wk in weights for j in range(1, width)) / n
    return total / n + penalty


def softmax_proba(args):
    """fn.brain.ml.softmax_proba -- one distribution per row, summing to one by construction."""
    model, data = args["model"], args["data"]
    rows = _rows_for(model, data)
    out = []
    for row in rows:
        scores = [b + math.fsum(c * v for c, v in zip(coef, row))
                  for b, coef in zip(model["intercepts"], model["coefs"])]
        out.append(softmax(scores))
    return {"for": args.get("for", "how the softmax splits its one unit of belief"),
            "classes": model["classes"], "proba": out}


def softmax_predict(args):
    """fn.brain.ml.softmax_predict -- the class with the largest share."""
    out = softmax_proba(args)
    classes = out["classes"]
    return {"for": args.get("for", "the class the softmax picks"),
            "classes": classes,
            "labels": [classes[max(range(len(p)), key=lambda i: p[i])] for p in out["proba"]]}


def cross_entropy(args):
    """fn.brain.ml.cross_entropy -- the loss a probabilistic classifier is actually judged on."""
    truth = args["y_true"]
    truth = truth["values"] if isinstance(truth, dict) else truth
    predicted = args["y_pred"]
    classes = predicted["classes"] if isinstance(predicted, dict) else args["classes"]
    proba = predicted["proba"] if isinstance(predicted, dict) else predicted
    index = {label: i for i, label in enumerate(classes)}
    total = 0.0
    for t, row in zip(truth, proba):
        total -= math.log(max(row[index[t]], 1e-300))
    return {"for": args.get("for", "how surprised the model was by the truth"),
            "classes": list(classes), "n": len(truth), "mean": total / len(truth), "total": total}


# --- gradient boosting on the logistic loss ----------------------------------


def logistic_gbm_fit(args):
    """fn.brain.ml.logistic_gbm_fit -- boosting where the leaf value is a newton step.

    squared loss lets a tree fit the residual and stop. the logistic loss does not: the
    tree is fitted to the negative gradient (y - p), and then every leaf's value is
    replaced by sum(gradient) / sum(p(1-p)) over the rows in it -- the one-dimensional
    newton step for that leaf. without that replacement the model underfits and says so.
    """
    data, target = args["data"], args["target"]
    matrix, targets, features = core.xy(data, target)
    classes = sorted(set(targets))
    if len(classes) != 2:
        raise ValueError("this booster is two-class; use one-vs-rest or the softmax for more")
    y = [1.0 if t == classes[1] else 0.0 for t in targets]
    n_trees = int(args.get("n_trees", 30))
    rate = float(args.get("learning_rate", 0.2))
    depth = int(args.get("max_depth", 2))
    columns = core.columns_of(data)
    positive = math.fsum(y) / len(y)
    positive = min(max(positive, 1e-6), 1 - 1e-6)
    init = math.log(positive / (1.0 - positive))
    scores = [init] * len(matrix)
    built, losses = [], []
    for t in range(n_trees):
        p = [1.0 / (1.0 + math.exp(-max(min(s, 500.0), -500.0))) for s in scores]
        gradient = [yi - pi for yi, pi in zip(y, p)]
        shaped = core.dataset("the negative gradient so far", columns,
                              [list(row) + [g] for row, g in zip(matrix, gradient)])
        tree = trees.tree_fit({"data": shaped, "target": target, "criterion": "mse",
                               "max_depth": depth, "min_samples_leaf": 1,
                               "for": f"the {t}th correction, fitted to the gradient"})
        _newton_leaves(tree["root"], matrix, gradient, p)
        step = [trees._walk(tree["root"], row)["leaf"] for row in matrix]
        scores = [s + rate * v for s, v in zip(scores, step)]
        built.append(tree)
        losses.append(_logistic_loss(y, scores))
    return {
        "for": args.get("for", "a sum of newton corrections on the logistic loss"),
        "model": "logistic_gbm",
        "task": "classify",
        "target": target,
        "columns": features,
        "classes": classes,
        "init": init,
        "learning_rate": rate,
        "n_trees": n_trees,
        "max_depth": depth,
        "trees": built,
        "train_loss": losses,
        "n": len(matrix),
    }


def _newton_leaves(node, rows, gradient, probabilities, at=None):
    """replace every leaf's mean gradient with the newton step for the rows that reach it."""
    at = list(range(len(rows))) if at is None else at
    if "leaf" in node:
        # the gradient is y - p, so |y - p| is p when y is 0 and 1 - p when y is 1:
        # either way |g| * (1 - |g|) is p * (1 - p), the second derivative this step needs,
        # and the probabilities never have to be carried down the tree to get it.
        numerator = math.fsum(gradient[i] for i in at)
        denominator = math.fsum(abs(gradient[i]) * (1.0 - abs(gradient[i])) for i in at)
        node["leaf"] = numerator / denominator if denominator > 1e-12 else 0.0
        node["rows"] = len(at)
        return
    left = [i for i in at if rows[i][node["feature"]] <= node["threshold"]]
    right = [i for i in at if rows[i][node["feature"]] > node["threshold"]]
    _newton_leaves(node["left"], rows, gradient, probabilities, left)
    _newton_leaves(node["right"], rows, gradient, probabilities, right)


def _logistic_loss(y, scores):
    """mean log(1 + exp(-margin)), computed on whichever side does not overflow."""
    total = 0.0
    for yi, s in zip(y, scores):
        margin = max(min((2.0 * yi - 1.0) * s, 500.0), -500.0)
        total += math.log1p(math.exp(-margin)) if margin >= 0 else -margin + math.log1p(math.exp(margin))
    return total / len(y)


def logistic_gbm_predict(args):
    """fn.brain.ml.logistic_gbm_predict -- the summed score, through the logistic."""
    model, data = args["model"], args["data"]
    rows = _rows_for(model, data)
    scores = [model["init"]] * len(rows)
    for tree in model["trees"]:
        step = [trees._walk(tree["root"], row)["leaf"] for row in rows]
        scores = [s + model["learning_rate"] * v for s, v in zip(scores, step)]
    classes = model["classes"]
    proba = [1.0 / (1.0 + math.exp(-max(min(s, 500.0), -500.0))) for s in scores]
    return {
        "for": args.get("for", "what the boosted classifier believes"),
        "classes": classes,
        "scores": scores,
        "proba": [[1.0 - p, p] for p in proba],
        "labels": [classes[1] if p >= 0.5 else classes[0] for p in proba],
    }
