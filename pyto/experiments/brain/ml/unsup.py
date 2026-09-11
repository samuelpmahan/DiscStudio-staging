"""unsupervised: k-means (seeded k-means++), pca through svd, hierarchical linkage, dbscan.

k-means is where the seed matters most: the init is drawn from args["seed"] through
the same Stream every backend reads, so a py run and an np run of the same seed pick
the same starting centres and can be compared as algorithms rather than as dice.
"""

from __future__ import annotations

import math

from . import core

# --- k-means -----------------------------------------------------------------


def kmeans_plus_plus(rows, k, rng):
    """the seeded init: the first centre uniformly, each next one favouring far points."""
    n = len(rows)
    first = rng.randint(n)
    centres = [list(rows[first])]
    chosen = [first]
    for _ in range(k - 1):
        weights = [min(core.sq_euclidean(row, centre) for centre in centres) for row in rows]
        pick = rng.choice(weights)
        chosen.append(pick)
        centres.append(list(rows[pick]))
    return centres, chosen


def _assign_py(rows, centres):
    labels, inertia = [], 0.0
    for row in rows:
        best, at = None, 0
        for index, centre in enumerate(centres):
            d = core.sq_euclidean(row, centre)
            if best is None or d < best:
                best, at = d, index
        labels.append(at)
        inertia += best
    return labels, inertia


def _assign_np(rows, centres):
    """the same assignment through one broadcast subtraction."""
    np = core.numpy()
    if np is None:
        return _assign_py(rows, centres)
    x = np.asarray(rows, dtype=float)
    c = np.asarray(centres, dtype=float)
    squared = ((x[:, None, :] - c[None, :, :]) ** 2).sum(-1)
    labels = squared.argmin(1)
    return [int(v) for v in labels], float(squared[np.arange(len(x)), labels].sum())


def _assign_gram(rows, centres):
    """the same assignment through the identity |a-b|^2 = |a|^2 - 2ab + |b|^2: one matmul."""
    np = core.numpy()
    if np is None:
        return _assign_py(rows, centres)
    x = np.asarray(rows, dtype=float)
    c = np.asarray(centres, dtype=float)
    squared = (x * x).sum(1)[:, None] - 2.0 * (x @ c.T) + (c * c).sum(1)[None, :]
    labels = squared.argmin(1)
    inertia = float(np.maximum(squared[np.arange(len(x)), labels], 0.0).sum())
    return [int(v) for v in labels], inertia


ASSIGNMENTS = {"py": _assign_py, "np": _assign_np, "gram": _assign_gram}


def kmeans(args):
    """fn.brain.ml.kmeans -- lloyd's iteration from a seeded k-means++ init.

    `backend` picks how the assignment step is computed and nothing else: py loops,
    np broadcasts, gram uses the squared-distance identity. same seed, same answer.
    """
    data = args["data"]
    rows = [[float(v) for v in row] for row in core.as_rows(data)]
    if args.get("drop_last"):
        rows = [row[:-1] for row in rows]
    k = int(args["k"])
    if k < 1 or k > len(rows):
        raise ValueError(f"k must be between 1 and {len(rows)}; got {k}")
    backend = args.get("backend", "py")
    if backend not in ASSIGNMENTS:
        raise ValueError(f"unknown backend {backend!r}: {tuple(ASSIGNMENTS)}")
    assign = ASSIGNMENTS[backend]
    rng = core.stream(args["seed"])
    centres, seeded_from = kmeans_plus_plus(rows, k, rng)
    max_iter = int(args.get("max_iter", 100))
    tol = float(args.get("tol", 1e-10))
    labels, inertia = assign(rows, centres)
    history = [inertia]
    taken = 0
    for step in range(max_iter):
        taken = step + 1
        moved = []
        for index in range(k):
            members = [row for row, label in zip(rows, labels) if label == index]
            if not members:
                moved.append(list(centres[index]))
                continue
            moved.append([core.mean(column) for column in core.transpose(members)])
        shift = max(core.sq_euclidean(a, b) for a, b in zip(centres, moved))
        centres = moved
        labels, inertia = assign(rows, centres)
        history.append(inertia)
        if shift <= tol:
            break
    return {
        "for": args.get("for", f"{k} clusters found from seed {args['seed']}"),
        "model": "kmeans",
        "backend": backend,
        "k": k,
        "seed": int(args["seed"]),
        "init": "kmeans++",
        "seeded_from": seeded_from,
        "centres": centres,
        "labels": labels,
        "inertia": inertia,
        "history": history,
        "iters": taken,
        "n": len(rows),
    }


def kmeans_predict(args):
    """fn.brain.ml.kmeans_predict -- the nearest centre of a fitted model, for new rows."""
    model, data = args["model"], args["data"]
    rows = [[float(v) for v in row] for row in core.as_rows(data)]
    if args.get("drop_last"):
        rows = [row[:-1] for row in rows]
    backend = args.get("backend", model.get("backend", "py"))
    labels, inertia = ASSIGNMENTS[backend](rows, model["centres"])
    return {"for": args.get("for", "which cluster each row falls in"), "labels": labels, "inertia": inertia}


# --- pca ---------------------------------------------------------------------


def pca(args):
    """fn.brain.ml.pca -- principal components through the svd, with explained variance.

    the svd of the centred matrix, not the eigendecomposition of the covariance:
    same answer, and it does not square the condition number to get there.
    """
    np = core.numpy()
    data = args["data"]
    rows = [[float(v) for v in row] for row in core.as_rows(data)]
    if args.get("drop_last"):
        rows = [row[:-1] for row in rows]
    n_components = int(args.get("n_components", min(len(rows), len(rows[0]))))
    whiten = bool(args.get("whiten", False))
    if np is None or args.get("backend") == "py":
        return _pca_py(rows, n_components, args)
    x = np.asarray(rows, dtype=float)
    mean = x.mean(0)
    centred = x - mean
    u, s, vt = np.linalg.svd(centred, full_matrices=False)
    variance = (s**2) / (len(rows) - 1)
    total = float(variance.sum())
    components = vt[:n_components]
    # the sign of a component is arbitrary; pin it so the part is the same every run.
    for i in range(components.shape[0]):
        at = int(np.argmax(np.abs(components[i])))
        if components[i][at] < 0:
            components[i] = -components[i]
    scores = centred @ components.T
    if whiten:
        scores = scores / np.sqrt(variance[:n_components])
    return {
        "for": args.get("for", "the directions the data actually varies in"),
        "model": "pca",
        "backend": "np",
        "n_components": n_components,
        "mean": [float(v) for v in mean],
        "components": components.tolist(),
        "explained_variance": [float(v) for v in variance[:n_components]],
        "explained_variance_ratio": [float(v) / total for v in variance[:n_components]],
        "singular_values": [float(v) for v in s[:n_components]],
        "scores": scores.tolist(),
        "total_variance": total,
        "n": len(rows),
    }


def _pca_py(rows, n_components, args):
    """the reference: the covariance matrix and the jacobi eigenvalue rotation, no numpy."""
    columns = core.transpose(rows)
    mean = [core.mean(column) for column in columns]
    centred = [[v - m for v, m in zip(row, mean)] for row in rows]
    n, d = len(rows), len(mean)
    covariance = [
        [sum(centred[r][i] * centred[r][j] for r in range(n)) / (n - 1) for j in range(d)]
        for i in range(d)
    ]
    values, vectors = _jacobi(covariance)
    order = sorted(range(d), key=lambda i: -values[i])
    components = []
    for i in order[:n_components]:
        vector = [vectors[r][i] for r in range(d)]
        at = max(range(d), key=lambda j: abs(vector[j]))
        if vector[at] < 0:
            vector = [-v for v in vector]
        components.append(vector)
    total = sum(values)
    return {
        "for": args.get("for", "the directions the data actually varies in"),
        "model": "pca",
        "backend": "py",
        "n_components": n_components,
        "mean": mean,
        "components": components,
        "explained_variance": [values[i] for i in order[:n_components]],
        "explained_variance_ratio": [values[i] / total for i in order[:n_components]],
        "singular_values": [math.sqrt(max(values[i], 0.0) * (n - 1)) for i in order[:n_components]],
        "scores": [[sum(row[j] * component[j] for j in range(d)) for component in components] for row in centred],
        "total_variance": total,
        "n": n,
    }


def _jacobi(matrix, sweeps=100, tol=1e-12):
    """the cyclic jacobi rotation: a symmetric matrix's eigenvalues, in pure python."""
    n = len(matrix)
    a = [list(row) for row in matrix]
    v = core.eye(n)
    for _ in range(sweeps):
        off = math.sqrt(sum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j))
        if off < tol:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(a[p][q]) < tol:
                    continue
                theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
                t = (1.0 if theta >= 0 else -1.0) / (abs(theta) + math.sqrt(theta * theta + 1.0))
                c = 1.0 / math.sqrt(t * t + 1.0)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p] = c * akp - s * akq
                    a[k][q] = s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k] = c * apk - s * aqk
                    a[q][k] = s * apk + c * aqk
                for k in range(n):
                    vkp, vkq = v[k][p], v[k][q]
                    v[k][p] = c * vkp - s * vkq
                    v[k][q] = s * vkp + c * vkq
    return [a[i][i] for i in range(n)], v


# --- hierarchical clustering -------------------------------------------------


LINKAGES = ("single", "complete", "average")


def hierarchical(args):
    """fn.brain.ml.hierarchical -- agglomerative clustering, single/complete/average linkage.

    the merge order is the part: (a, b, distance, size) per step, the way a
    dendrogram is read, plus the flat labelling at the requested number of clusters.
    """
    data = args["data"]
    rows = [[float(v) for v in row] for row in core.as_rows(data)]
    if args.get("drop_last"):
        rows = [row[:-1] for row in rows]
    linkage = args.get("linkage", "single")
    if linkage not in LINKAGES:
        raise ValueError(f"unknown linkage {linkage!r}: {LINKAGES}")
    n = len(rows)
    distance = [[core.euclidean(a, b) for b in rows] for a in rows]
    clusters = {i: [i] for i in range(n)}
    merges = []
    names = {i: i for i in range(n)}
    next_name = n
    while len(clusters) > 1:
        best = None
        keys = sorted(clusters)
        for i_at, i in enumerate(keys):
            for j in keys[i_at + 1:]:
                pairs = [distance[a][b] for a in clusters[i] for b in clusters[j]]
                if linkage == "single":
                    d = min(pairs)
                elif linkage == "complete":
                    d = max(pairs)
                else:
                    d = sum(pairs) / len(pairs)
                if best is None or d < best[0]:
                    best = (d, i, j)
        d, i, j = best
        merges.append([names[i], names[j], d, len(clusters[i]) + len(clusters[j])])
        clusters[i] = clusters[i] + clusters[j]
        names[i] = next_name
        next_name += 1
        del clusters[j]
    k = int(args.get("k", 2))
    labels = _cut(merges, n, k)
    return {
        "for": args.get("for", f"the merge order under {linkage} linkage"),
        "model": "hierarchical",
        "linkage": linkage,
        "k": k,
        "merges": merges,
        "labels": labels,
        "heights": [row[2] for row in merges],
        "n": n,
    }


def _cut(merges, n, k):
    """the flat labelling you get by stopping the merges k clusters short of one."""
    members = {i: [i] for i in range(n)}
    next_name = n
    for a, b, _, _ in merges[: max(0, n - k)]:
        members[next_name] = members.pop(a) + members.pop(b)
        next_name += 1
    labels = [0] * n
    for index, name in enumerate(sorted(members)):
        for row in members[name]:
            labels[row] = index
    return labels


# --- dbscan ------------------------------------------------------------------


def dbscan(args):
    """fn.brain.ml.dbscan -- density clustering: core points, their reach, and the noise.

    noise is labelled -1, which is the one label k-means cannot produce and the whole
    reason this calculation exists next to it.
    """
    data = args["data"]
    rows = [[float(v) for v in row] for row in core.as_rows(data)]
    if args.get("drop_last"):
        rows = [row[:-1] for row in rows]
    eps = float(args["eps"])
    min_samples = int(args.get("min_samples", 4))
    backend = args.get("backend", "py")
    n = len(rows)
    if backend == "np" and core.numpy() is not None:
        np = core.numpy()
        x = np.asarray(rows, dtype=float)
        squared = (x * x).sum(1)[:, None] - 2.0 * (x @ x.T) + (x * x).sum(1)[None, :]
        near = np.sqrt(np.maximum(squared, 0.0)) <= eps
        neighbours = [[int(j) for j in np.flatnonzero(row)] for row in near]
    else:
        neighbours = [[j for j in range(n) if core.euclidean(rows[i], rows[j]) <= eps] for i in range(n)]
    labels = [-1] * n
    core_points = [i for i in range(n) if len(neighbours[i]) >= min_samples]
    is_core = set(core_points)
    cluster = 0
    seen = set()
    for i in core_points:
        if i in seen:
            continue
        queue = [i]
        seen.add(i)
        labels[i] = cluster
        while queue:
            at = queue.pop()
            for j in neighbours[at]:
                if labels[j] == -1:
                    labels[j] = cluster
                if j in is_core and j not in seen:
                    seen.add(j)
                    queue.append(j)
        cluster += 1
    return {
        "for": args.get("for", f"clusters of density eps={eps}, and the points that are in none"),
        "model": "dbscan",
        "backend": backend,
        "eps": eps,
        "min_samples": min_samples,
        "labels": labels,
        "core_points": core_points,
        "clusters": cluster,
        "noise": sum(1 for label in labels if label == -1),
        "n": n,
    }
