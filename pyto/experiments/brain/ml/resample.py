"""splits, folds and the synthetic datasets the oracles are built on.

every draw here is a pure function of args["seed"]: same seed, same rows, on any
backend and any machine. a split is returned as indices, not as copied rows, so a
split part stays small enough to sit in a record.
"""

from __future__ import annotations

from . import core


def train_test_split(args):
    """fn.brain.ml.train_test_split -- a seeded partition of the row positions.

    `stratify` names a column whose value classes keep their proportions in both
    halves; without it the shuffle is plain.
    """
    data = args["data"]
    rows = core.as_rows(data)
    n = len(rows)
    test_size = float(args.get("test_size", 0.25))
    k = int(round(n * test_size)) if test_size < 1 else int(test_size)
    k = max(0, min(n, k))
    rng = core.stream(args["seed"])
    stratify = args.get("stratify")
    if stratify:
        columns = core.columns_of(data)
        at = columns.index(stratify)
        buckets = {}
        for i, row in enumerate(rows):
            buckets.setdefault(row[at], []).append(i)
        test = []
        for label in sorted(buckets):
            members = buckets[label]
            order = rng.permutation(len(members))
            want = int(round(len(members) * (k / n))) if n else 0
            test.extend(members[j] for j in order[:want])
        test = sorted(test)
        chosen = set(test)
        train = [i for i in range(n) if i not in chosen]
    else:
        order = rng.permutation(n)
        test = sorted(order[:k])
        train = sorted(order[k:])
    return {
        "for": args.get("for", "a held-out test set that the fit never saw"),
        "seed": int(args["seed"]),
        "test_size": test_size,
        "stratify": stratify,
        "train_index": train,
        "test_index": test,
    }


def kfold(args):
    """fn.brain.ml.kfold -- k seeded folds; every row is in exactly one test fold."""
    data = args["data"]
    n = len(core.as_rows(data))
    k = int(args.get("k", 5))
    if k < 2 or k > n:
        raise ValueError(f"k must be between 2 and {n}; got {k}")
    order = core.stream(args["seed"]).permutation(n) if args.get("shuffle", True) else list(range(n))
    sizes = [n // k + (1 if i < n % k else 0) for i in range(k)]
    folds = []
    at = 0
    for size in sizes:
        test = sorted(order[at : at + size])
        chosen = set(test)
        folds.append({"train_index": [i for i in range(n) if i not in chosen], "test_index": test})
        at += size
    return {
        "for": args.get("for", "every row held out exactly once"),
        "seed": int(args["seed"]),
        "k": k,
        "folds": folds,
    }


def subset(args):
    """fn.brain.ml.subset -- the rows at those positions, as a dataset part."""
    data = args["data"]
    index = args["index"]
    if isinstance(index, dict):
        index = index[args.get("which", "train_index")]
    out = core.take(data, index)
    out["for"] = args.get("for", data.get("for", "a subset"))
    return out


def column(args):
    """fn.brain.ml.column -- one column of a dataset, as a list part."""
    data = args["data"]
    name = args["name"]
    columns = core.columns_of(data)
    at = columns.index(name)
    return {
        "for": args.get("for", f"the {name} column"),
        "name": name,
        "values": [row[at] for row in core.as_rows(data)],
    }


# --- synthetic data ----------------------------------------------------------


def synthetic_regression(args):
    """fn.brain.ml.synthetic_regression -- y = b + w.x + noise, a pure function of the seed."""
    seed = args["seed"]
    n = int(args.get("n", 100))
    d = int(args.get("d", 3))
    noise = float(args.get("noise", 0.1))
    rng = core.stream(seed)
    weights = [round(rng.normal(0.0, 2.0), 6) for _ in range(d)]
    intercept = round(rng.normal(0.0, 1.0), 6)
    rows = []
    for _ in range(n):
        x = [rng.normal(0.0, 1.0) for _ in range(d)]
        y = intercept + sum(w * v for w, v in zip(weights, x)) + rng.normal(0.0, noise)
        rows.append(x + [y])
    out = core.dataset(
        args.get("for", "a regression problem whose true weights are known"),
        [f"x{i}" for i in range(d)] + ["y"],
        rows,
    )
    out["truth"] = {"intercept": intercept, "coef": weights, "noise": noise}
    out["seed"] = int(seed)
    return out


def synthetic_blobs(args):
    """fn.brain.ml.synthetic_blobs -- k gaussian blobs and the cluster each row came from."""
    seed = args["seed"]
    n = int(args.get("n", 120))
    d = int(args.get("d", 2))
    k = int(args.get("k", 3))
    spread = float(args.get("spread", 0.6))
    separation = float(args.get("separation", 6.0))
    rng = core.stream(seed)
    centres = _separated_centres(rng, k, d, separation, float(args.get("min_gap", 6.0)) * spread)
    rows = []
    for i in range(n):
        which = i % k
        rows.append([centres[which][j] + rng.normal(0.0, spread) for j in range(d)] + [float(which)])
    out = core.dataset(
        args.get("for", "clusters whose true membership is known"),
        [f"x{i}" for i in range(d)] + ["cluster"],
        rows,
    )
    out["truth"] = {"centres": centres, "k": k, "spread": spread}
    out["seed"] = int(seed)
    return out


def _separated_centres(rng, k, d, separation, min_gap, tries=200):
    """centres no closer than min_gap, drawn from the same seeded stream.

    drawing k centres from one normal and hoping is how a clustering fixture ends up
    testing the fixture: two centres land half a standard deviation apart and the
    clustering is blamed. this redraws until they are apart, and says so if it cannot.
    """
    best, best_gap = None, -1.0
    for _ in range(tries):
        centres = [[rng.normal(0.0, separation) for _ in range(d)] for _ in range(k)]
        gap = min(
            (core.euclidean(centres[i], centres[j]) for i in range(k) for j in range(i + 1, k)),
            default=float("inf"),
        )
        if gap > best_gap:
            best, best_gap = centres, gap
        if gap >= min_gap:
            return centres
    scale = (min_gap / best_gap) if best_gap > 0 else 1.0
    return [[v * scale for v in centre] for centre in best]


def synthetic_classification(args):
    """fn.brain.ml.synthetic_classification -- two (or k) linearly separable-ish classes."""
    seed = args["seed"]
    n = int(args.get("n", 120))
    d = int(args.get("d", 2))
    k = int(args.get("k", 2))
    spread = float(args.get("spread", 1.0))
    separation = float(args.get("separation", 2.5))
    rng = core.stream(seed)
    centres = [[rng.normal(0.0, separation) for _ in range(d)] for _ in range(k)]
    rows = []
    for i in range(n):
        label = i % k
        rows.append([centres[label][j] + rng.normal(0.0, spread) for j in range(d)] + [float(label)])
    order = rng.permutation(n)
    rows = [rows[i] for i in order]
    out = core.dataset(
        args.get("for", "a classification problem with known class centres"),
        [f"x{i}" for i in range(d)] + ["label"],
        rows,
    )
    out["truth"] = {"centres": centres, "k": k}
    out["seed"] = int(seed)
    return out


def synthetic_counts(args):
    """fn.brain.ml.synthetic_counts -- multinomial word counts per class, for naive bayes."""
    seed = args["seed"]
    n = int(args.get("n", 120))
    vocabulary = int(args.get("vocabulary", 8))
    k = int(args.get("k", 2))
    length = int(args.get("length", 20))
    rng = core.stream(seed)
    profiles = []
    for c in range(k):
        weights = [rng.uniform() + (2.0 if (i % k) == c else 0.0) for i in range(vocabulary)]
        total = sum(weights)
        profiles.append([w / total for w in weights])
    rows = []
    for i in range(n):
        label = i % k
        counts = [0] * vocabulary
        for _ in range(length):
            counts[rng.choice(profiles[label])] += 1
        rows.append([float(c) for c in counts] + [float(label)])
    order = rng.permutation(n)
    rows = [rows[i] for i in order]
    out = core.dataset(
        args.get("for", "word counts drawn from known per-class profiles"),
        [f"w{i}" for i in range(vocabulary)] + ["label"],
        rows,
    )
    out["truth"] = {"profiles": profiles, "k": k}
    out["seed"] = int(seed)
    return out
