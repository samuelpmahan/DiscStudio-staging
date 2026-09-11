"""trees: cart (gini, entropy, squared error), a small random forest, small gradient boosting.

a fitted tree is a json-able nested dict, so a forest is a list of them and a
boosted model is a list plus a learning rate. nothing here holds a python object
that a record could not carry.

the split search is the whole cost of a tree, and it is written twice on purpose:
`sort` scans every midpoint between distinct values (exact), `hist` scans a fixed
number of equal-width bin edges (approximate, and cheaper as n grows). they are the
two branches of the split-search bracket.
"""

from __future__ import annotations

import math

from . import core

CRITERIA = ("gini", "entropy", "mse")


def _impurity(counts, total, criterion):
    if total <= 0:
        return 0.0
    if criterion == "gini":
        return 1.0 - math.fsum((c / total) ** 2 for c in counts)
    return -sum((c / total) * math.log2(c / total) for c in counts if c > 0)


def _leaf_classification(labels, classes):
    counts = [sum(1 for y in labels if y == c) for c in classes]
    total = len(labels) or 1
    best = max(range(len(classes)), key=lambda i: (counts[i], -i))
    return {
        "leaf": classes[best],
        "n": len(labels),
        "proba": [c / total for c in counts],
    }


def _leaf_regression(values):
    return {"leaf": core.mean(values), "n": len(values)}


# --- split search: the sorting branch ----------------------------------------


def _best_split_sort(rows, targets, feature_index, criterion, min_leaf, classes):
    """every midpoint between distinct values of every candidate feature, exactly.

    one sort per feature, then one pass with running counts, so the whole scan is
    O(n log n) per feature and never recomputes an impurity from scratch.
    """
    n = len(rows)
    best = None
    for feature in feature_index:
        order = sorted(range(n), key=lambda i: rows[i][feature])
        values = [rows[i][feature] for i in order]
        if criterion == "mse":
            left_sum = left_sq = 0.0
            total_sum = math.fsum(targets)
            total_sq = math.fsum(y * y for y in targets)
            for at in range(n - 1):
                y = targets[order[at]]
                left_sum += y
                left_sq += y * y
                left_n = at + 1
                right_n = n - left_n
                if left_n < min_leaf or right_n < min_leaf or values[at] == values[at + 1]:
                    continue
                left_error = left_sq - left_sum * left_sum / left_n
                right_error = (total_sq - left_sq) - (total_sum - left_sum) ** 2 / right_n
                score = (left_error + right_error) / n
                if best is None or score < best[0]:
                    best = (score, feature, (values[at] + values[at + 1]) / 2.0)
        else:
            index = {c: i for i, c in enumerate(classes)}
            left = [0] * len(classes)
            total = [0] * len(classes)
            for y in targets:
                total[index[y]] += 1
            for at in range(n - 1):
                left[index[targets[order[at]]]] += 1
                left_n = at + 1
                right_n = n - left_n
                if left_n < min_leaf or right_n < min_leaf or values[at] == values[at + 1]:
                    continue
                right = [t - l for t, l in zip(total, left)]
                score = (
                    left_n * _impurity(left, left_n, criterion)
                    + right_n * _impurity(right, right_n, criterion)
                ) / n
                if best is None or score < best[0]:
                    best = (score, feature, (values[at] + values[at + 1]) / 2.0)
    return best


# --- split search: the histogram branch --------------------------------------


def _best_split_hist(rows, targets, feature_index, criterion, min_leaf, classes, bins=32):
    """equal-width bin edges instead of every midpoint: one pass per feature, no sort.

    the answer is the best of at most `bins - 1` thresholds rather than of every
    midpoint, so it is an approximation of the sorting branch and says so.
    """
    n = len(rows)
    best = None
    index = {c: i for i, c in enumerate(classes)} if criterion != "mse" else {}
    for feature in feature_index:
        values = [row[feature] for row in rows]
        low, high = min(values), max(values)
        if high <= low:
            continue
        width = (high - low) / bins
        edges = [low + width * (b + 1) for b in range(bins - 1)]
        if criterion == "mse":
            bin_n = [0] * bins
            bin_sum = [0.0] * bins
            bin_sq = [0.0] * bins
            for value, y in zip(values, targets):
                b = min(int((value - low) / width), bins - 1)
                bin_n[b] += 1
                bin_sum[b] += y
                bin_sq[b] += y * y
            total_n, total_sum, total_sq = n, math.fsum(bin_sum), math.fsum(bin_sq)
            left_n = left_sum = left_sq = 0.0
            for b, edge in enumerate(edges):
                left_n += bin_n[b]
                left_sum += bin_sum[b]
                left_sq += bin_sq[b]
                right_n = total_n - left_n
                if left_n < min_leaf or right_n < min_leaf:
                    continue
                left_error = left_sq - left_sum * left_sum / left_n
                right_error = (total_sq - left_sq) - (total_sum - left_sum) ** 2 / right_n
                score = (left_error + right_error) / n
                if best is None or score < best[0]:
                    best = (score, feature, edge)
        else:
            table = [[0] * len(classes) for _ in range(bins)]
            for value, y in zip(values, targets):
                b = min(int((value - low) / width), bins - 1)
                table[b][index[y]] += 1
            total = [sum(row[c] for row in table) for c in range(len(classes))]
            left = [0] * len(classes)
            left_n = 0
            for b, edge in enumerate(edges):
                for c in range(len(classes)):
                    left[c] += table[b][c]
                left_n += sum(table[b])
                right_n = n - left_n
                if left_n < min_leaf or right_n < min_leaf:
                    continue
                right = [t - l for t, l in zip(total, left)]
                score = (
                    left_n * _impurity(left, left_n, criterion)
                    + right_n * _impurity(right, right_n, criterion)
                ) / n
                if best is None or score < best[0]:
                    best = (score, feature, edge)
    return best


SEARCHES = {"sort": _best_split_sort, "hist": _best_split_hist}


def _grow(rows, targets, classes, criterion, depth, max_depth, min_split, min_leaf, search, features, rng, max_features):
    task_is_regression = criterion == "mse"
    leaf = _leaf_regression(targets) if task_is_regression else _leaf_classification(targets, classes)
    if depth >= max_depth or len(rows) < min_split or len(set(targets)) == 1:
        return leaf
    candidates = list(range(features))
    if max_features and max_features < features:
        order = rng.permutation(features)
        candidates = sorted(order[:max_features])
    found = search(rows, targets, candidates, criterion, min_leaf, classes)
    if found is None:
        return leaf
    _, feature, threshold = found
    left_rows, left_y, right_rows, right_y = [], [], [], []
    for row, y in zip(rows, targets):
        if row[feature] <= threshold:
            left_rows.append(row)
            left_y.append(y)
        else:
            right_rows.append(row)
            right_y.append(y)
    if not left_rows or not right_rows:
        return leaf
    return {
        "feature": feature,
        "threshold": threshold,
        "n": len(rows),
        "left": _grow(left_rows, left_y, classes, criterion, depth + 1, max_depth, min_split, min_leaf, search, features, rng, max_features),
        "right": _grow(right_rows, right_y, classes, criterion, depth + 1, max_depth, min_split, min_leaf, search, features, rng, max_features),
    }


def tree_fit(args):
    """fn.brain.ml.tree_fit -- one cart tree, depth-limited, as a nested json dict."""
    data, target = args["data"], args["target"]
    criterion = args.get("criterion", "gini")
    if criterion not in CRITERIA:
        raise ValueError(f"unknown criterion {criterion!r}: {CRITERIA}")
    split_search = args.get("search", "sort")
    if split_search not in SEARCHES:
        raise ValueError(f"unknown split search {split_search!r}: {tuple(SEARCHES)}")
    rows, targets, features = core.xy(data, target)
    classes = sorted(set(targets)) if criterion != "mse" else []
    bins = int(args.get("bins", 32))
    search = SEARCHES[split_search]
    if split_search == "hist":
        search = lambda *a, bins=bins: _best_split_hist(*a, bins=bins)
    rng = core.stream(args.get("seed", 0))
    root = _grow(
        rows, targets, classes, criterion, 0,
        int(args.get("max_depth", 5)), int(args.get("min_samples_split", 2)),
        int(args.get("min_samples_leaf", 1)), search, len(features), rng,
        int(args.get("max_features", 0)),
    )
    return {
        "for": args.get("for", f"a depth-limited tree of {target}"),
        "model": "tree",
        "task": "regress" if criterion == "mse" else "classify",
        "criterion": criterion,
        "search": split_search,
        "target": target,
        "columns": features,
        "classes": classes,
        "max_depth": int(args.get("max_depth", 5)),
        "root": root,
        "nodes": count_nodes(root),
        "depth": tree_depth(root),
        "n": len(rows),
    }


def count_nodes(node):
    return 1 if "leaf" in node else 1 + count_nodes(node["left"]) + count_nodes(node["right"])


def tree_depth(node):
    return 0 if "leaf" in node else 1 + max(tree_depth(node["left"]), tree_depth(node["right"]))


def _walk(node, row):
    while "leaf" not in node:
        node = node["left"] if row[node["feature"]] <= node["threshold"] else node["right"]
    return node


def _rows_for(model, data):
    columns = core.columns_of(data)
    missing = [c for c in model["columns"] if c not in columns]
    if missing:
        raise KeyError(f"the model needs columns this dataset does not have: {missing}")
    at = [columns.index(c) for c in model["columns"]]
    return [[float(row[i]) for i in at] for row in core.as_rows(data)]


def tree_predict(args):
    """fn.brain.ml.tree_predict -- walk each row to its leaf."""
    model, data = args["model"], args["data"]
    rows = _rows_for(model, data)
    leaves = [_walk(model["root"], row) for row in rows]
    out = {
        "for": args.get("for", "where each row lands in the tree"),
        "labels": [leaf["leaf"] for leaf in leaves],
    }
    if model["task"] == "classify":
        out["classes"] = model["classes"]
        out["proba"] = [leaf["proba"] for leaf in leaves]
    else:
        out["predictions"] = out["labels"]
    return out


# --- a small forest ----------------------------------------------------------


def forest_fit(args):
    """fn.brain.ml.forest_fit -- n_trees bootstrapped trees, each on a seeded subset of features."""
    data, target = args["data"], args["target"]
    rows, targets, features = core.xy(data, target)
    n_trees = int(args.get("n_trees", 10))
    seed = args["seed"]
    rng = core.stream(seed)
    criterion = args.get("criterion", "gini")
    max_features = int(args.get("max_features", 0)) or max(1, int(math.sqrt(len(features))))
    trees = []
    bags = []
    for t in range(n_trees):
        picks = rng.sample_indices(len(rows), len(rows))
        bags.append(sorted(set(picks)))
        bag = core.dataset("a bootstrap of the training rows", core.columns_of(data),
                           [list(rows[i]) + [targets[i]] for i in picks])
        tree = tree_fit({
            "data": bag, "target": target, "criterion": criterion,
            "max_depth": int(args.get("max_depth", 6)),
            "min_samples_leaf": int(args.get("min_samples_leaf", 1)),
            "max_features": max_features,
            "search": args.get("search", "sort"),
            "seed": rng.randint(1_000_000),
            "for": f"tree {t} of the forest",
        })
        trees.append(tree)
    return {
        "for": args.get("for", f"{n_trees} trees that disagree on purpose"),
        "model": "forest",
        "task": trees[0]["task"],
        "target": target,
        "columns": features,
        "classes": trees[0]["classes"],
        "seed": int(seed),
        "n_trees": n_trees,
        "max_features": max_features,
        "trees": trees,
        "oob_sizes": [len(rows) - len(bag) for bag in bags],
        "n": len(rows),
    }


def forest_predict(args):
    """fn.brain.ml.forest_predict -- the trees vote (classify) or average (regress)."""
    model, data = args["model"], args["data"]
    per_tree = [tree_predict({"model": tree, "data": data})["labels"] for tree in model["trees"]]
    rows = list(zip(*per_tree))
    if model["task"] == "regress":
        labels = [core.mean(list(row)) for row in rows]
        return {"for": args.get("for", "the forest average"), "labels": labels, "predictions": labels}
    labels = []
    for row in rows:
        tally = {}
        for vote in row:
            tally[vote] = tally.get(vote, 0) + 1
        labels.append(max(sorted(tally), key=lambda label: tally[label]))
    return {
        "for": args.get("for", "the forest vote"),
        "classes": model["classes"],
        "labels": labels,
        "votes": [{str(v): list(row).count(v) for v in sorted(set(row))} for row in rows],
    }


# --- small gradient boosting, squared loss -----------------------------------


def gbm_fit(args):
    """fn.brain.ml.gbm_fit -- stumps (or small trees) fitted to the residual, one after another.

    squared loss only, so the residual is the negative gradient and there is no
    line search to get wrong: the model is the mean plus a shrunken sum of trees.
    """
    data, target = args["data"], args["target"]
    rows, targets, features = core.xy(data, target)
    n_trees = int(args.get("n_trees", 25))
    rate = float(args.get("learning_rate", 0.1))
    columns = core.columns_of(data)
    init = core.mean(targets)
    working = [init] * len(rows)
    trees, losses = [], []
    for t in range(n_trees):
        residual = [y - f for y, f in zip(targets, working)]
        stump_data = core.dataset("the residual so far", columns, [list(r) + [g] for r, g in zip(rows, residual)])
        tree = tree_fit({
            "data": stump_data, "target": target, "criterion": "mse",
            "max_depth": int(args.get("max_depth", 2)),
            "min_samples_leaf": int(args.get("min_samples_leaf", 1)),
            "search": args.get("search", "sort"),
            "for": f"the {t}th correction",
        })
        step = tree_predict({"model": tree, "data": stump_data})["labels"]
        working = [f + rate * s for f, s in zip(working, step)]
        trees.append(tree)
        losses.append(math.fsum((y - f) ** 2 for y, f in zip(targets, working)) / len(rows))
    return {
        "for": args.get("for", "a sum of small corrections"),
        "model": "gbm",
        "task": "regress",
        "target": target,
        "columns": features,
        "init": init,
        "learning_rate": rate,
        "n_trees": n_trees,
        "trees": trees,
        "train_mse": losses,
        "n": len(rows),
    }


def gbm_predict(args):
    """fn.brain.ml.gbm_predict -- the mean plus every shrunken correction."""
    model, data = args["model"], args["data"]
    rows = _rows_for(model, data)
    out = [model["init"]] * len(rows)
    for tree in model["trees"]:
        step = [_walk(tree["root"], row)["leaf"] for row in rows]
        out = [f + model["learning_rate"] * s for f, s in zip(out, step)]
    return {"for": args.get("for", "the boosted prediction"), "predictions": out, "labels": out}


# --- learning curves ---------------------------------------------------------


def learning_curve(args):
    """fn.brain.ml.learning_curve -- train and test error against the number of training rows.

    a curve is a part: the fractions, the sizes, and the two errors at each size,
    every fit re-done from the same seed so the curve is a function of its args.
    """
    from . import calcs

    data, target = args["data"], args["target"]
    fit_name, predict_name = args["fit"], args["predict"]
    fit_args = dict(args.get("fit_args", {}))
    metric = args.get("metric", "mse")
    fractions = list(args.get("fractions", [0.1, 0.25, 0.5, 0.75, 1.0]))
    split = calcs.call("train_test_split", {"data": data, "seed": args["seed"], "test_size": args.get("test_size", 0.25)})
    train = core.take(data, split["train_index"])
    test = core.take(data, split["test_index"])
    truth_train = [row[core.columns_of(data).index(target)] for row in core.as_rows(train)]
    truth_test = [row[core.columns_of(data).index(target)] for row in core.as_rows(test)]
    rng = core.stream(args["seed"])
    order = rng.permutation(len(core.as_rows(train)))
    sizes, train_error, test_error = [], [], []
    for fraction in fractions:
        k = max(2, int(round(len(order) * fraction)))
        part = core.take(train, sorted(order[:k]))
        model = calcs.call(fit_name, dict(fit_args, data=part, target=target))
        on_train = calcs.call(predict_name, {"model": model, "data": part})
        on_test = calcs.call(predict_name, {"model": model, "data": test})
        want_train = [truth_train[i] for i in sorted(order[:k])]
        sizes.append(k)
        train_error.append(_error(want_train, on_train, metric))
        test_error.append(_error(truth_test, on_test, metric))
    return {
        "for": args.get("for", "whether more rows would still help"),
        "fit": fit_name,
        "metric": metric,
        "seed": int(args["seed"]),
        "fractions": fractions,
        "sizes": sizes,
        "train": train_error,
        "test": test_error,
    }


#: the keys a prediction part may carry its numbers under.
CARRIERS = ("predictions", "labels", "values")


def _numbers_in(part):
    if not isinstance(part, dict):
        return list(part)
    for key in CARRIERS:
        if key in part:
            return list(part[key])
    raise KeyError(f"this part carries no numbers under any of {CARRIERS}: {sorted(part)}")


def _error(truth, prediction, metric):
    from . import calcs

    guess = _numbers_in(prediction)
    if metric == "accuracy":
        return calcs.call("classification_metrics", {"y_true": truth, "y_pred": guess})["accuracy"]
    return calcs.call("regression_metrics", {"y_true": truth, "y_pred": guess})[metric]
