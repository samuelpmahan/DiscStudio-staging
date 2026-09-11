"""evaluation: what a prediction was worth, as a part.

every metric is a calculation over two lists (or a list of lists, for probabilities),
py and np, same numbers within tolerance.
"""

from __future__ import annotations

import math

from . import core, distance


#: the keys a part may carry its numbers under: a column, a regression, a classifier.
CARRIERS = ("values", "predictions", "labels", "proba")


def numbers_in(part):
    """the list of numbers inside a part, whichever of the carriers it used."""
    if not isinstance(part, dict):
        return list(part)
    for key in CARRIERS:
        if key in part:
            return list(part[key])
    raise KeyError(f"this part carries no numbers under any of {CARRIERS}: {sorted(part)}")


def _pair(args):
    truth = numbers_in(args["y_true"])
    guess = numbers_in(args["y_pred"])
    if len(truth) != len(guess):
        raise ValueError(f"y_true has {len(truth)} rows and y_pred has {len(guess)}")
    return truth, guess


def regression(args):
    """fn.brain.ml.regression_metrics -- mse, rmse, mae, r2."""
    truth, guess = _pair(args)
    backend = core.backend_of(args)
    n = len(truth)
    if backend == "np" and core.numpy() is not None:
        np = core.numpy()
        t, g = np.asarray(truth, dtype=float), np.asarray(guess, dtype=float)
        residual = t - g
        mse = float((residual**2).mean())
        mae = float(np.abs(residual).mean())
        total = float(((t - t.mean()) ** 2).sum())
        explained = float((residual**2).sum())
    else:
        residual = [a - b for a, b in zip(truth, guess)]
        mse = math.fsum(r * r for r in residual) / n
        mae = math.fsum(abs(r) for r in residual) / n
        mu = core.mean(truth)
        total = math.fsum((a - mu) ** 2 for a in truth)
        explained = math.fsum(r * r for r in residual)
    r2 = 1.0 - explained / total if total > 0 else 0.0
    return {
        "for": args.get("for", "how far the predictions were"),
        "backend": backend,
        "n": n,
        "mse": mse,
        "rmse": math.sqrt(mse),
        "mae": mae,
        "r2": r2,
    }


def _labels(truth, guess):
    return sorted(set(truth) | set(guess))


def confusion(args):
    """fn.brain.ml.confusion_matrix -- rows are truth, columns are prediction."""
    truth, guess = _pair(args)
    labels = args.get("labels") or _labels(truth, guess)
    index = {label: i for i, label in enumerate(labels)}
    matrix = [[0 for _ in labels] for _ in labels]
    for a, b in zip(truth, guess):
        matrix[index[a]][index[b]] += 1
    return {
        "for": args.get("for", "which classes were confused for which"),
        "labels": list(labels),
        "matrix": matrix,
    }


def classification(args):
    """fn.brain.ml.classification_metrics -- accuracy and per-class precision, recall, f1.

    `average` is "macro" (unweighted mean over classes), "micro" (global counts, which
    for single-label prediction equals accuracy) or "weighted" (by class support).
    """
    truth, guess = _pair(args)
    labels = args.get("labels") or _labels(truth, guess)
    n = len(truth)
    correct = sum(1 for a, b in zip(truth, guess) if a == b)
    per_class = {}
    for label in labels:
        tp = sum(1 for a, b in zip(truth, guess) if a == label and b == label)
        fp = sum(1 for a, b in zip(truth, guess) if a != label and b == label)
        fn = sum(1 for a, b in zip(truth, guess) if a == label and b != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[str(label)] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": tp + fn,
        }
    average = args.get("average", "macro")
    supports = [per_class[str(l)]["support"] for l in labels]
    total_support = sum(supports) or 1
    if average == "micro":
        macro = {"precision": correct / n, "recall": correct / n, "f1": correct / n}
    elif average == "weighted":
        macro = {
            k: math.fsum(per_class[str(l)][k] * s for l, s in zip(labels, supports)) / total_support
            for k in ("precision", "recall", "f1")
        }
    else:
        macro = {k: core.mean([per_class[str(l)][k] for l in labels]) for k in ("precision", "recall", "f1")}
    return {
        "for": args.get("for", "how well the classifier told the classes apart"),
        "labels": [str(l) for l in labels],
        "n": n,
        "accuracy": correct / n,
        "average": average,
        "per_class": per_class,
        "precision": macro["precision"],
        "recall": macro["recall"],
        "f1": macro["f1"],
    }


def roc_auc(args):
    """fn.brain.ml.roc_auc -- the area under the roc curve for a binary score.

    computed from the rank-sum identity (the mann-whitney u), with ties given
    their average rank, so it is exact and needs no curve to be traced.
    """
    truth, score = _pair(args)
    positive = args.get("positive", 1)
    pairs = sorted(zip(score, truth), key=lambda p: p[0])
    ranks = [0.0] * len(pairs)
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        average_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = average_rank
        i = j + 1
    positives = [r for r, (_, t) in zip(ranks, pairs) if t == positive]
    n_pos, n_neg = len(positives), len(pairs) - len(positives)
    if n_pos == 0 or n_neg == 0:
        auc = 0.5
    else:
        auc = (math.fsum(positives) - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return {
        "for": args.get("for", "how well the score separates the two classes"),
        "auc": auc,
        "n_pos": n_pos,
        "n_neg": n_neg,
    }


def roc_curve(args):
    """fn.brain.ml.roc_curve -- the (fpr, tpr) points, one per distinct threshold."""
    truth, score = _pair(args)
    positive = args.get("positive", 1)
    order = sorted(range(len(score)), key=lambda i: -score[i])
    n_pos = sum(1 for t in truth if t == positive)
    n_neg = len(truth) - n_pos
    tp = fp = 0
    points = [(0.0, 0.0)]
    previous = None
    for i in order:
        if previous is not None and score[i] != previous:
            points.append((fp / n_neg if n_neg else 0.0, tp / n_pos if n_pos else 0.0))
        if truth[i] == positive:
            tp += 1
        else:
            fp += 1
        previous = score[i]
    points.append((fp / n_neg if n_neg else 0.0, tp / n_pos if n_pos else 0.0))
    return {
        "for": args.get("for", "the trade-off curve between false and true positives"),
        "fpr": [p[0] for p in points],
        "tpr": [p[1] for p in points],
    }


def silhouette(args):
    """fn.brain.ml.silhouette -- how well each point sits in its cluster, and the mean."""
    data = args["data"]
    labels = args["labels"]
    labels = labels["labels"] if isinstance(labels, dict) else labels
    rows = core.as_rows(data)
    backend = distance.backend_of(args, calc="silhouette")
    n = len(rows)
    groups = {}
    for i, label in enumerate(labels):
        groups.setdefault(label, []).append(i)
    matrix = distance.pairwise(rows, backend=backend)
    scores = []
    for i in range(n):
        own = groups[labels[i]]
        if len(own) <= 1:
            scores.append(0.0)
            continue
        a = math.fsum(matrix[i][j] for j in own if j != i) / (len(own) - 1)
        b = min(
            math.fsum(matrix[i][j] for j in members) / len(members)
            for label, members in groups.items()
            if label != labels[i]
        )
        scores.append((b - a) / max(a, b) if max(a, b) > 0 else 0.0)
    return {
        "for": args.get("for", "whether the clusters are really apart"),
        "backend": backend,
        "scores": scores,
        "mean": core.mean(scores),
        "clusters": len(groups),
    }
