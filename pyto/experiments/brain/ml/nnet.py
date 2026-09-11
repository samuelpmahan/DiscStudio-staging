"""the sparse linear model and the small networks: lasso, a perceptron, a one-hidden-layer mlp.

every weight that starts at random starts from args["seed"] through the one Stream,
so a network is a pure function of its arguments and its record replays exactly.
"""

from __future__ import annotations

import math

from . import core


# --- lasso, by coordinate descent --------------------------------------------


def _soft_threshold(value, amount):
    """the proximal step of the l1 penalty: shrink toward zero, and stop at zero."""
    if value > amount:
        return value - amount
    if value < -amount:
        return value + amount
    return 0.0


def lasso_fit(args):
    """fn.brain.ml.lasso_fit -- l1-penalised least squares, one coordinate at a time.

    the features are standardised inside the fit and the coefficients are handed back
    on the original scale, because an l1 penalty is not scale-free and a lasso fitted
    on raw columns penalises whichever column happens to be measured in small units.
    """
    data, target = args["data"], args["target"]
    backend = core.backend_of(args)
    alpha = float(args.get("alpha", 0.1))
    max_iter = int(args.get("max_iter", 1000))
    tol = float(args.get("tol", 1e-10))
    matrix, targets, features = core.xy(data, target)
    scaled, means, sds = core.standardize(matrix)
    centre = core.mean(targets)
    centred = [y - centre for y in targets]
    n, d = len(scaled), len(features)
    weights = [0.0] * d
    columns = core.transpose(scaled)
    norms = [math.fsum(v * v for v in column) for column in columns]
    if backend == "np" and core.numpy() is not None:
        np = core.numpy()
        x = np.asarray(scaled, dtype=float)
        y = np.asarray(centred, dtype=float)
        w = np.zeros(d)
        column_norms = np.asarray(norms)
        residual = y - x @ w
        taken = 0
        for step in range(max_iter):
            taken = step + 1
            biggest = 0.0
            for j in range(d):
                if column_norms[j] == 0.0:
                    continue
                rho = float(x[:, j] @ (residual + x[:, j] * w[j]))
                updated = _soft_threshold(rho, alpha * n) / column_norms[j]
                change = updated - w[j]
                if change:
                    residual = residual - x[:, j] * change
                    w[j] = updated
                biggest = max(biggest, abs(change))
            if biggest < tol:
                break
        weights = [float(v) for v in w]
    else:
        residual = list(centred)
        taken = 0
        for step in range(max_iter):
            taken = step + 1
            biggest = 0.0
            for j in range(d):
                if norms[j] == 0.0:
                    continue
                rho = math.fsum(columns[j][i] * (residual[i] + columns[j][i] * weights[j]) for i in range(n))
                updated = _soft_threshold(rho, alpha * n) / norms[j]
                change = updated - weights[j]
                if change:
                    for i in range(n):
                        residual[i] -= columns[j][i] * change
                    weights[j] = updated
                biggest = max(biggest, abs(change))
            if biggest < tol:
                break
    raw = [w / sd for w, sd in zip(weights, sds)]
    intercept = centre - math.fsum(w * m for w, m in zip(raw, means))
    return {
        "for": args.get("for", "a linear model with most of its coefficients at exactly zero"),
        "model": "lasso",
        "backend": backend,
        "target": target,
        "columns": features,
        "alpha": alpha,
        "intercept": intercept,
        "coef": raw,
        "scaled_coef": weights,
        "nonzero": [features[j] for j in range(d) if weights[j] != 0.0],
        "iters": taken,
        "n": n,
    }


# --- the perceptron ----------------------------------------------------------


def perceptron_fit(args):
    """fn.brain.ml.perceptron_fit -- rosenblatt's rule: only a mistake moves the boundary.

    the update is the whole algorithm, so the part records how many mistakes each
    pass cost: a pass with none is the convergence proof for a separable problem.
    """
    data, target = args["data"], args["target"]
    matrix, targets, features = core.xy(data, target)
    classes = sorted(set(targets))
    if len(classes) != 2:
        raise ValueError("the perceptron is a two-class rule; use one-vs-rest for more")
    signs = [1.0 if t == classes[1] else -1.0 for t in targets]
    rate = float(args.get("lr", 1.0))
    epochs = int(args.get("epochs", 30))
    rng = core.stream(args["seed"])
    weights = [rng.normal(0.0, 0.01) for _ in features]
    bias = 0.0
    mistakes = []
    for _ in range(epochs):
        wrong = 0
        for i in rng.permutation(len(matrix)):
            row, sign = matrix[i], signs[i]
            if sign * (bias + math.fsum(w * v for w, v in zip(weights, row))) <= 0.0:
                wrong += 1
                bias += rate * sign
                weights = [w + rate * sign * v for w, v in zip(weights, row)]
        mistakes.append(wrong)
        if wrong == 0:
            break
    return {
        "for": args.get("for", "the first boundary that gets every row right, if there is one"),
        "model": "perceptron",
        "target": target,
        "columns": features,
        "classes": classes,
        "seed": int(args["seed"]),
        "intercept": bias,
        "coef": weights,
        "mistakes": mistakes,
        "converged": mistakes[-1] == 0,
        "epochs": len(mistakes),
        "n": len(matrix),
    }


def perceptron_predict(args):
    """fn.brain.ml.perceptron_predict -- which side of the boundary each row is on."""
    model, data = args["model"], args["data"]
    rows = _rows_for(model, data)
    classes = model["classes"]
    scores = [model["intercept"] + math.fsum(w * v for w, v in zip(model["coef"], row)) for row in rows]
    return {
        "for": args.get("for", "the side of the boundary"),
        "classes": classes,
        "scores": scores,
        "labels": [classes[1] if s > 0 else classes[0] for s in scores],
    }


def _rows_for(model, data):
    columns = core.columns_of(data)
    missing = [c for c in model["columns"] if c not in columns]
    if missing:
        raise KeyError(f"the model needs columns this dataset does not have: {missing}")
    at = [columns.index(c) for c in model["columns"]]
    return [[float(row[i]) for i in at] for row in core.as_rows(data)]


# --- one hidden layer --------------------------------------------------------


def _tanh(z):
    return math.tanh(z)


def mlp_fit(args):
    """fn.brain.ml.mlp_fit -- one hidden tanh layer, sgd, seeded init, numpy inside.

    the smallest network worth the name: input -> tanh -> linear (regression) or
    sigmoid (two-class). the init, the shuffles and nothing else come from the seed.
    """
    np = core.numpy()
    data, target = args["data"], args["target"]
    matrix, targets, features = core.xy(data, target)
    hidden = int(args.get("hidden", 8))
    rate = float(args.get("lr", 0.05))
    epochs = int(args.get("epochs", 200))
    batch = int(args.get("batch", 16))
    task = args.get("task", "regress")
    rng = core.stream(args["seed"])
    d = len(features)
    limit = math.sqrt(6.0 / (d + hidden))
    w1 = [[(rng.uniform() * 2 - 1) * limit for _ in range(hidden)] for _ in range(d)]
    b1 = [0.0] * hidden
    limit2 = math.sqrt(6.0 / (hidden + 1))
    w2 = [(rng.uniform() * 2 - 1) * limit2 for _ in range(hidden)]
    b2 = 0.0
    classes = sorted(set(targets)) if task == "classify" else []
    if task == "classify" and len(classes) != 2:
        raise ValueError("this mlp has one output; use one-vs-rest for more than two classes")
    y = [1.0 if t == classes[1] else 0.0 for t in targets] if task == "classify" else list(targets)
    if np is None:  # pragma: no cover - the brain extra installs numpy
        raise RuntimeError("the mlp needs numpy; the reference here is the closed-form linear model")
    x = np.asarray(matrix, dtype=float)
    yv = np.asarray(y, dtype=float)
    W1, B1 = np.asarray(w1), np.asarray(b1)
    W2, B2 = np.asarray(w2), b2
    n = len(matrix)
    losses = []
    for _ in range(epochs):
        order = rng.permutation(n)
        for start in range(0, n, batch):
            index = order[start : start + batch]
            xb, yb = x[index], yv[index]
            hidden_in = xb @ W1 + B1
            hidden_out = np.tanh(hidden_in)
            out = hidden_out @ W2 + B2
            if task == "classify":
                out = 1.0 / (1.0 + np.exp(-np.clip(out, -500, 500)))
            error = (out - yb) / len(index)
            gW2 = hidden_out.T @ error
            gB2 = float(error.sum())
            back = np.outer(error, W2) * (1.0 - hidden_out**2)
            gW1 = xb.T @ back
            gB1 = back.sum(0)
            W1 = W1 - rate * gW1
            B1 = B1 - rate * gB1
            W2 = W2 - rate * gW2
            B2 = B2 - rate * gB2
        full = np.tanh(x @ W1 + B1) @ W2 + B2
        if task == "classify":
            p = 1.0 / (1.0 + np.exp(-np.clip(full, -500, 500)))
            losses.append(float(-np.mean(yv * np.log(p + 1e-12) + (1 - yv) * np.log(1 - p + 1e-12))))
        else:
            losses.append(float(((full - yv) ** 2).mean()))
    return {
        "for": args.get("for", f"a {hidden}-unit hidden layer fitted by sgd from seed {args['seed']}"),
        "model": "mlp",
        "task": task,
        "target": target,
        "columns": features,
        "classes": classes,
        "hidden": hidden,
        "seed": int(args["seed"]),
        "learning_rate": rate,
        "epochs": epochs,
        "w1": W1.tolist(),
        "b1": B1.tolist(),
        "w2": [float(v) for v in W2],
        "b2": float(B2),
        "loss": losses,
        "n": n,
    }


def mlp_predict(args):
    """fn.brain.ml.mlp_predict -- one forward pass."""
    np = core.numpy()
    model, data = args["model"], args["data"]
    rows = _rows_for(model, data)
    x = np.asarray(rows, dtype=float)
    out = np.tanh(x @ np.asarray(model["w1"]) + np.asarray(model["b1"])) @ np.asarray(model["w2"]) + model["b2"]
    if model["task"] == "classify":
        p = 1.0 / (1.0 + np.exp(-np.clip(out, -500, 500)))
        classes = model["classes"]
        return {
            "for": args.get("for", "what the network says"),
            "classes": classes,
            "proba": [[float(1 - v), float(v)] for v in p],
            "labels": [classes[1] if v >= 0.5 else classes[0] for v in p],
        }
    values = [float(v) for v in out]
    return {"for": args.get("for", "what the network says"), "predictions": values, "labels": values}
