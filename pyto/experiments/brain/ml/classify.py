"""classifiers: logistic regression (gradient descent and newton/irls), k nearest
neighbours, and naive bayes (gaussian and multinomial).

each is two calculations -- a fit that returns a json-able model part and a predict
that reads one -- so a model outlives the process that fitted it.
"""

from __future__ import annotations

import math

from . import core

# --- logistic regression -----------------------------------------------------


def sigmoid(z):
    """stable on both tails: never exp() a large positive number."""
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def _classes_of(targets):
    return sorted(set(targets))


def _binary_gd(design, labels, l2, lr, epochs):
    n = len(design)
    width = len(design[0])
    weights = [0.0] * width
    for _ in range(epochs):
        gradient = [0.0] * width
        for row, y in zip(design, labels):
            error = sigmoid(sum(w * v for w, v in zip(weights, row))) - y
            for j in range(width):
                gradient[j] += error * row[j] / n
        for j in range(width):
            if l2 and j > 0:
                gradient[j] += l2 * weights[j] / n
            weights[j] -= lr * gradient[j]
    return weights, epochs


def _binary_gd_np(design, labels, l2, lr, epochs):
    """the same full-batch descent, one matmul per pass instead of a python loop per row."""
    np = core.numpy()
    if np is None:
        return _binary_gd(design, labels, l2, lr, epochs)
    x = np.asarray(design, dtype=float)
    y = np.asarray(labels, dtype=float)
    n, width = x.shape
    weights = np.zeros(width)
    mask = np.ones(width)
    mask[0] = 0.0
    for _ in range(epochs):
        z = x @ weights
        p = np.where(z >= 0, 1.0 / (1.0 + np.exp(-np.abs(z))), np.exp(-np.abs(z)) / (1.0 + np.exp(-np.abs(z))))
        gradient = x.T @ (p - y) / n
        if l2:
            gradient = gradient + l2 * weights * mask / n
        weights = weights - lr * gradient
    return [float(w) for w in weights], epochs


def _binary_newton(design, labels, l2, epochs, tol):
    """iteratively reweighted least squares: the hessian is X' W X, W = p(1-p)."""
    width = len(design[0])
    weights = [0.0] * width
    taken = 0
    for step in range(epochs):
        taken = step + 1
        p = [sigmoid(sum(w * v for w, v in zip(weights, row))) for row in design]
        gradient = [0.0] * width
        for row, pi, y in zip(design, p, labels):
            for j in range(width):
                gradient[j] += (pi - y) * row[j]
        hessian = [[0.0] * width for _ in range(width)]
        for row, pi in zip(design, p):
            w = max(pi * (1.0 - pi), 1e-10)
            for j in range(width):
                if row[j] == 0.0:
                    continue
                for k in range(width):
                    hessian[j][k] += w * row[j] * row[k]
        for j in range(width):
            if j > 0:
                gradient[j] += l2 * weights[j]
                hessian[j][j] += l2
            hessian[j][j] += 1e-10
        step_vector = core.solve(hessian, gradient)
        weights = [w - s for w, s in zip(weights, step_vector)]
        if max(abs(s) for s in step_vector) < tol:
            break
    return weights, taken


def _binary_newton_np(design, labels, l2, epochs, tol):
    """irls again, with the hessian built as one weighted matmul: (X' * w) @ X."""
    np = core.numpy()
    if np is None:
        return _binary_newton(design, labels, l2, epochs, tol)
    x = np.asarray(design, dtype=float)
    y = np.asarray(labels, dtype=float)
    width = x.shape[1]
    weights = np.zeros(width)
    penalty = np.eye(width) * l2
    penalty[0, 0] = 0.0
    taken = 0
    for step in range(epochs):
        taken = step + 1
        z = x @ weights
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))
        w = np.maximum(p * (1.0 - p), 1e-10)
        gradient = x.T @ (p - y) + penalty @ weights
        hessian = (x.T * w) @ x + penalty + np.eye(width) * 1e-10
        step_vector = np.linalg.solve(hessian, gradient)
        weights = weights - step_vector
        if float(np.max(np.abs(step_vector))) < tol:
            break
    return [float(v) for v in weights], taken


LOGREG_METHODS = ("gd", "newton")


def logreg_fit(args):
    """fn.brain.ml.logreg_fit -- one-vs-rest logistic regression, gd or newton/irls."""
    data, target = args["data"], args["target"]
    backend = core.backend_of(args)
    method = args.get("method", "newton")
    if method not in LOGREG_METHODS:
        raise ValueError(f"unknown method {method!r}: {LOGREG_METHODS}")
    l2 = float(args.get("l2", 0.0))
    lr, epochs = float(args.get("lr", 0.5)), int(args.get("epochs", 200 if method == "gd" else 25))
    tol = float(args.get("tol", 1e-10))
    matrix, targets, features = core.xy(data, target)
    design = core.add_bias(matrix)
    classes = _classes_of(targets)
    if len(classes) < 2:
        raise ValueError("a classifier needs at least two classes in the target column")
    rounds = classes if len(classes) > 2 else classes[1:]
    weights, iterations = [], []
    for label in rounds:
        one = [1.0 if t == label else 0.0 for t in targets]
        if method == "gd":
            w, taken = (_binary_gd_np if backend == "np" else _binary_gd)(design, one, l2, lr, epochs)
        else:
            w, taken = (_binary_newton_np if backend == "np" else _binary_newton)(design, one, l2, epochs, tol)
        weights.append([float(v) for v in w])
        iterations.append(taken)
    return {
        "for": args.get("for", "a logistic model of " + target),
        "model": "logreg",
        "backend": backend,
        "method": method,
        "target": target,
        "columns": features,
        "classes": classes,
        "one_vs_rest": len(classes) > 2,
        "l2": l2,
        "intercepts": [w[0] for w in weights],
        "coefs": [w[1:] for w in weights],
        "iters": iterations,
        "n": len(matrix),
    }


def _rows_for(model, data):
    columns = core.columns_of(data)
    missing = [c for c in model["columns"] if c not in columns]
    if missing:
        raise KeyError(f"the model needs columns this dataset does not have: {missing}")
    at = [columns.index(c) for c in model["columns"]]
    return [[float(row[i]) for i in at] for row in core.as_rows(data)]


def logreg_proba(args):
    """fn.brain.ml.logreg_proba -- one probability per class, per row."""
    model, data = args["model"], args["data"]
    rows = _rows_for(model, data)
    classes = model["classes"]
    scores = []
    for row in rows:
        raw = [
            sigmoid(b + sum(c * v for c, v in zip(coef, row)))
            for b, coef in zip(model["intercepts"], model["coefs"])
        ]
        if model["one_vs_rest"]:
            total = sum(raw) or 1.0
            scores.append([p / total for p in raw])
        else:
            scores.append([1.0 - raw[0], raw[0]])
    return {
        "for": args.get("for", "how sure the logistic model is, per class"),
        "classes": classes,
        "proba": scores,
    }


def logreg_predict(args):
    """fn.brain.ml.logreg_predict -- the most likely class per row."""
    out = logreg_proba(args)
    classes = out["classes"]
    return {
        "for": args.get("for", "the class the logistic model picks"),
        "classes": classes,
        "labels": [classes[max(range(len(p)), key=lambda i: p[i])] for p in out["proba"]],
    }


# --- k nearest neighbours ----------------------------------------------------


def knn_fit(args):
    """fn.brain.ml.knn_fit -- the model is the training set; there is nothing to solve."""
    data, target = args["data"], args["target"]
    matrix, targets, features = core.xy(data, target)
    task = args.get("task", "classify")
    return {
        "for": args.get("for", f"{args.get('k', 5)} nearest neighbours of {target}"),
        "model": "knn",
        "task": task,
        "target": target,
        "columns": features,
        "k": int(args.get("k", 5)),
        "metric": args.get("metric", "euclidean"),
        "weights": args.get("weights", "uniform"),
        "rows": matrix,
        "labels": targets,
        "classes": _classes_of(targets) if task == "classify" else None,
        "n": len(matrix),
    }


def _distances(model, rows, backend):
    train = model["rows"]
    metric = model["metric"]
    if backend == "np" and core.numpy() is not None:
        np = core.numpy()
        a, b = np.asarray(rows, dtype=float), np.asarray(train, dtype=float)
        if metric == "manhattan":
            return np.abs(a[:, None, :] - b[None, :, :]).sum(-1).tolist()
        # the identity |a-b|^2 = |a|^2 - 2ab + |b|^2: one matmul instead of a cube of subtractions
        squared = (a * a).sum(1)[:, None] - 2.0 * (a @ b.T) + (b * b).sum(1)[None, :]
        return np.sqrt(np.maximum(squared, 0.0)).tolist()
    if metric == "manhattan":
        return [[sum(abs(x - y) for x, y in zip(r, t)) for t in train] for r in rows]
    return [[core.euclidean(r, t) for t in train] for r in rows]


def knn_predict(args):
    """fn.brain.ml.knn_predict -- vote (or average) over the k closest training rows."""
    model, data = args["model"], args["data"]
    backend = core.backend_of(args)
    rows = _rows_for(model, data)
    distance = _distances(model, rows, backend)
    k = model["k"]
    labels, votes = [], []
    for d in distance:
        order = sorted(range(len(d)), key=lambda i: (d[i], i))[:k]
        if model["weights"] == "distance":
            weights = [1.0 / (d[i] + 1e-12) for i in order]
        else:
            weights = [1.0] * len(order)
        if model["task"] == "regress":
            total = sum(weights) or 1.0
            labels.append(sum(model["labels"][i] * w for i, w in zip(order, weights)) / total)
            votes.append(None)
        else:
            tally = {}
            for i, w in zip(order, weights):
                tally[model["labels"][i]] = tally.get(model["labels"][i], 0.0) + w
            best = max(sorted(tally), key=lambda label: tally[label])
            labels.append(best)
            votes.append({str(label): tally[label] for label in sorted(tally)})
    out = {
        "for": args.get("for", "the class of the nearest neighbours"),
        "backend": backend,
        "labels": labels,
    }
    if model["task"] == "classify":
        out["votes"] = votes
        out["classes"] = model["classes"]
    else:
        out["predictions"] = labels
    return out


# --- naive bayes -------------------------------------------------------------


def gaussian_nb_fit(args):
    """fn.brain.ml.gaussian_nb_fit -- a mean and a variance per feature per class."""
    data, target = args["data"], args["target"]
    matrix, targets, features = core.xy(data, target)
    classes = _classes_of(targets)
    smoothing = float(args.get("var_smoothing", 1e-9))
    spread = max(core.variance([row[j] for row in matrix]) for j in range(len(features))) if features else 1.0
    floor = smoothing * spread
    priors, means, variances = [], [], []
    for label in classes:
        members = [row for row, t in zip(matrix, targets) if t == label]
        priors.append(len(members) / len(matrix))
        columns = core.transpose(members)
        means.append([core.mean(c) for c in columns])
        variances.append([core.variance(c) + floor for c in columns])
    return {
        "for": args.get("for", "a gaussian naive bayes model of " + target),
        "model": "gaussian_nb",
        "target": target,
        "columns": features,
        "classes": classes,
        "priors": priors,
        "means": means,
        "variances": variances,
        "n": len(matrix),
    }


def gaussian_nb_predict(args):
    """fn.brain.ml.gaussian_nb_predict -- the class with the largest log posterior."""
    model, data = args["model"], args["data"]
    rows = _rows_for(model, data)
    classes = model["classes"]
    log_posteriors, labels = [], []
    for row in rows:
        scores = []
        for prior, mu, var in zip(model["priors"], model["means"], model["variances"]):
            total = math.log(prior)
            for v, m, s in zip(row, mu, var):
                total += -0.5 * (math.log(2.0 * math.pi * s) + (v - m) ** 2 / s)
            scores.append(total)
        log_posteriors.append(scores)
        labels.append(classes[max(range(len(scores)), key=lambda i: scores[i])])
    return {
        "for": args.get("for", "the class gaussian naive bayes finds most likely"),
        "classes": classes,
        "log_posterior": log_posteriors,
        "labels": labels,
    }


def multinomial_nb_fit(args):
    """fn.brain.ml.multinomial_nb_fit -- laplace-smoothed word probabilities per class."""
    data, target = args["data"], args["target"]
    matrix, targets, features = core.xy(data, target)
    classes = _classes_of(targets)
    alpha = float(args.get("alpha", 1.0))
    priors, log_prob = [], []
    for label in classes:
        members = [row for row, t in zip(matrix, targets) if t == label]
        priors.append(len(members) / len(matrix))
        counts = [sum(row[j] for row in members) + alpha for j in range(len(features))]
        total = sum(counts)
        log_prob.append([math.log(c / total) for c in counts])
    return {
        "for": args.get("for", "a multinomial naive bayes model of " + target),
        "model": "multinomial_nb",
        "target": target,
        "columns": features,
        "classes": classes,
        "alpha": alpha,
        "priors": priors,
        "log_prob": log_prob,
        "n": len(matrix),
    }


def multinomial_nb_predict(args):
    """fn.brain.ml.multinomial_nb_predict -- counts dotted with the log probabilities."""
    model, data = args["model"], args["data"]
    backend = core.backend_of(args)
    rows = _rows_for(model, data)
    classes = model["classes"]
    log_priors = [math.log(p) for p in model["priors"]]
    if backend == "np" and core.numpy() is not None:
        np = core.numpy()
        x = np.asarray(rows, dtype=float)
        w = np.asarray(model["log_prob"], dtype=float)
        scores = (x @ w.T + np.asarray(log_priors)).tolist()
    else:
        scores = [
            [lp + sum(v * p for v, p in zip(row, probabilities))
             for lp, probabilities in zip(log_priors, model["log_prob"])]
            for row in rows
        ]
    return {
        "for": args.get("for", "the class multinomial naive bayes finds most likely"),
        "backend": backend,
        "classes": classes,
        "log_posterior": scores,
        "labels": [classes[max(range(len(s)), key=lambda i: s[i])] for s in scores],
    }
