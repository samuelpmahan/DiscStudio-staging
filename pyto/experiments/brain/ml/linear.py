"""linear models: least squares (closed form, gradient descent, seeded sgd) and ridge.

a fitted model is a part: json-able, address px.exp.brain.result.ml.<model>.<case>.
fit and predict are separate calculations, so a model can be stored, read back and
predicted from without ever refitting.
"""

from __future__ import annotations

from . import core


def _design(matrix, fit_intercept):
    return core.add_bias(matrix) if fit_intercept else [list(row) for row in matrix]


def _normal_equations(design, targets, l2, fit_intercept):
    """(X'X + l2 * P) w = X'y, with P zero on the intercept: ridge never shrinks the intercept."""
    xt = core.transpose(design)
    gram = core.matmul(xt, design)
    if l2:
        for i in range(len(gram)):
            if fit_intercept and i == 0:
                continue
            gram[i][i] += l2
    rhs = core.matvec(xt, targets)
    return gram, rhs


def fit_closed_py(matrix, targets, fit_intercept=True, l2=0.0):
    design = _design(matrix, fit_intercept)
    gram, rhs = _normal_equations(design, targets, l2, fit_intercept)
    weights = core.solve(gram, rhs)
    return weights


def fit_closed_np(matrix, targets, fit_intercept=True, l2=0.0):
    np = core.numpy()
    if np is None:
        return fit_closed_py(matrix, targets, fit_intercept, l2)
    x = np.asarray(matrix, dtype=float)
    if fit_intercept:
        x = np.hstack([np.ones((x.shape[0], 1)), x])
    y = np.asarray(targets, dtype=float)
    gram = x.T @ x
    if l2:
        penalty = np.eye(x.shape[1]) * l2
        if fit_intercept:
            penalty[0, 0] = 0.0
        gram = gram + penalty
    weights = np.linalg.solve(gram, x.T @ y)
    return [float(w) for w in weights]


def fit_gd_py(matrix, targets, fit_intercept=True, l2=0.0, lr=0.01, epochs=200):
    design = _design(matrix, fit_intercept)
    n = len(design)
    width = len(design[0]) if design else 0
    weights = [0.0] * width
    for _ in range(epochs):
        residual = [sum(w * v for w, v in zip(weights, row)) - y for row, y in zip(design, targets)]
        gradient = [0.0] * width
        for row, r in zip(design, residual):
            for j in range(width):
                gradient[j] += 2.0 * r * row[j] / n
        for j in range(width):
            if l2 and not (fit_intercept and j == 0):
                gradient[j] += 2.0 * l2 * weights[j] / n
            weights[j] -= lr * gradient[j]
    return weights


def fit_gd_np(matrix, targets, fit_intercept=True, l2=0.0, lr=0.01, epochs=200):
    np = core.numpy()
    if np is None:
        return fit_gd_py(matrix, targets, fit_intercept, l2, lr, epochs)
    x = np.asarray(matrix, dtype=float)
    if fit_intercept:
        x = np.hstack([np.ones((x.shape[0], 1)), x])
    y = np.asarray(targets, dtype=float)
    n, width = x.shape
    weights = np.zeros(width)
    mask = np.ones(width)
    if fit_intercept:
        mask[0] = 0.0
    for _ in range(epochs):
        gradient = 2.0 * x.T @ (x @ weights - y) / n
        if l2:
            gradient = gradient + 2.0 * l2 * weights * mask / n
        weights = weights - lr * gradient
    return [float(w) for w in weights]


def fit_sgd(matrix, targets, seed, fit_intercept=True, l2=0.0, lr=0.01, epochs=20):
    """one pass per epoch over a seeded shuffle. the seed is the whole of the randomness."""
    design = _design(matrix, fit_intercept)
    n = len(design)
    width = len(design[0]) if design else 0
    weights = [0.0] * width
    rng = core.stream(seed)
    for _ in range(epochs):
        for i in rng.permutation(n):
            row = design[i]
            residual = sum(w * v for w, v in zip(weights, row)) - targets[i]
            for j in range(width):
                grad = 2.0 * residual * row[j]
                if l2 and not (fit_intercept and j == 0):
                    grad += 2.0 * l2 * weights[j]
                weights[j] -= lr * grad
    return weights


METHODS = ("closed", "gd", "sgd")


def fit(args):
    """fn.brain.ml.linreg_fit / fn.brain.ml.ridge_fit -- a fitted model, as a part."""
    data = args["data"]
    target = args["target"]
    backend = core.backend_of(args)
    method = args.get("method", "closed")
    if method not in METHODS:
        raise ValueError(f"unknown method {method!r}: {METHODS}")
    fit_intercept = bool(args.get("fit_intercept", True))
    l2 = float(args.get("l2", args.get("alpha", 0.0)))
    matrix, targets, features = core.xy(data, target)
    if method == "closed":
        weights = (fit_closed_np if backend == "np" else fit_closed_py)(matrix, targets, fit_intercept, l2)
        iters = 0
    elif method == "gd":
        lr, epochs = float(args.get("lr", 0.01)), int(args.get("epochs", 200))
        weights = (fit_gd_np if backend == "np" else fit_gd_py)(matrix, targets, fit_intercept, l2, lr, epochs)
        iters = epochs
    else:
        lr, epochs = float(args.get("lr", 0.01)), int(args.get("epochs", 20))
        weights = fit_sgd(matrix, targets, args["seed"], fit_intercept, l2, lr, epochs)
        iters = epochs
    intercept = weights[0] if fit_intercept else 0.0
    coef = weights[1:] if fit_intercept else weights
    return {
        "for": args.get("for", "a linear model of " + target),
        "model": "ridge" if l2 else "linreg",
        "backend": backend,
        "method": method,
        "target": target,
        "columns": features,
        "fit_intercept": fit_intercept,
        "l2": l2,
        "intercept": float(intercept),
        "coef": [float(c) for c in coef],
        "iters": iters,
        "n": len(matrix),
    }


def predict(args):
    """fn.brain.ml.linreg_predict -- predictions for every row of a dataset part."""
    model = args["model"]
    data = args["data"]
    backend = core.backend_of(args)
    columns = core.columns_of(data)
    wanted = model["columns"]
    missing = [c for c in wanted if c not in columns]
    if missing:
        raise KeyError(f"the model needs columns this dataset does not have: {missing}")
    at = [columns.index(c) for c in wanted]
    rows = [[float(row[i]) for i in at] for row in core.as_rows(data)]
    coef, intercept = model["coef"], model["intercept"]
    if backend == "np" and core.numpy() is not None:
        np = core.numpy()
        values = np.asarray(rows, dtype=float) @ np.asarray(coef, dtype=float) + intercept
        predictions = [float(v) for v in values]
    else:
        predictions = [intercept + sum(c * v for c, v in zip(coef, row)) for row in rows]
    return {"for": args.get("for", "predictions from " + model["model"]), "predictions": predictions}
