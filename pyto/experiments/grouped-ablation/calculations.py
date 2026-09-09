"""Module-level Calculations for the grouped ablation, in an explicit REGISTRY.

Every entry is a named module-level function (never an anonymous one), so the retained evidence
can name each Calculation by address and the registry can be imported by a
replay process. Args conventions:

  fn.ablation.selectVariants  {'groups': {g: [cols]}}          -> [variant dict]
  fn.ablation.split           {'rows': [[x, y], ...]}           -> {'train': [X, y], 'test': [X, y]}
  fn.ablation.fit             {'split': ..., 'columns': [...], 'variant': key} -> {'columns', 'w'}
  fn.ablation.score           {'split': ..., 'model': {...}}    -> {'rmse', 'n'}
  fn.ablation.compare         {'baseline': key, <key>: score, ...} -> ranked [row]
"""

from __future__ import annotations

from pyto import Calculation

from features import FEATURES

RIDGE_LAMBDA = 1e-3
TRAIN_FRACTION = 0.75


def select_variants(args: dict) -> list[dict]:
    """Baseline plus leave-one-group-out. Never enumerates feature subsets."""
    groups: dict[str, list[str]] = args["groups"]
    variants = [
        {"key": "all", "kind": "baseline", "drop": [], "columns": [f for g in groups.values() for f in g]}
    ]
    for dropped in groups:
        columns = [f for name, fs in groups.items() if name != dropped for f in fs]
        variants.append({"key": f"drop_{dropped}", "kind": "ablation", "drop": [dropped], "columns": columns})
    return variants


def split(args: dict) -> dict:
    rows = args["rows"]
    k = int(len(rows) * TRAIN_FRACTION)
    train, test = rows[:k], rows[k:]
    return {
        "train": [[r[0] for r in train], [r[1] for r in train]],
        "test": [[r[0] for r in test], [r[1] for r in test]],
    }


def _pivot_row(matrix: list[list[float]], column: int, start: int) -> int:
    best, best_abs = start, abs(matrix[start][column])
    for r in range(start + 1, len(matrix)):
        if abs(matrix[r][column]) > best_abs:
            best, best_abs = r, abs(matrix[r][column])
    return best


def solve(a: list[list[float]], b: list[float]) -> list[float]:
    """Gauss-Jordan elimination with partial pivoting on a small dense system."""
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = _pivot_row(m, c, c)
        m[c], m[p] = m[p], m[c]
        piv = m[c][c] or 1e-12
        m[c] = [v / piv for v in m[c]]
        for r in range(n):
            if r != c and m[r][c]:
                f = m[r][c]
                m[r] = [rv - f * cv for rv, cv in zip(m[r], m[c])]
    return [m[i][n] for i in range(n)]


def fit(args: dict) -> dict:
    """Ridge-regularised OLS restricted to args['columns'] on args['split']['train']."""
    columns: list[str] = args["columns"]
    x_rows, y = args["split"]["train"]
    idx = [FEATURES.index(c) for c in columns]
    xs = [[r[i] for i in idx] for r in x_rows]
    d = len(idx)
    gram = [
        [sum(xs[k][i] * xs[k][j] for k in range(len(xs))) + (RIDGE_LAMBDA if i == j else 0.0) for j in range(d)]
        for i in range(d)
    ]
    rhs = [sum(xs[k][i] * y[k] for k in range(len(xs))) for i in range(d)]
    return {"columns": list(columns), "w": solve(gram, rhs), "variant": args.get("variant")}


def score(args: dict) -> dict:
    """RMSE of args['model'] on args['split']['test']."""
    model = args["model"]
    columns, w = model["columns"], model["w"]
    x_rows, y = args["split"]["test"]
    idx = [FEATURES.index(c) for c in columns]
    err = [(sum(wi * r[i] for wi, i in zip(w, idx)) - yi) ** 2 for r, yi in zip(x_rows, y)]
    return {"rmse": (sum(err) / len(err)) ** 0.5, "n": len(err)}


def _delta_desc(row: dict) -> float:
    return -row["delta_vs_baseline"]


def compare(args: dict) -> list[dict]:
    """Rank every non-baseline input by RMSE increase over the baseline (largest first)."""
    baseline_key = args["baseline"]
    scores = {key: value for key, value in args.items() if key != "baseline"}
    base = scores[baseline_key]["rmse"]
    rows = []
    for key, value in scores.items():
        rows.append(
            {
                "variant": key,
                "rmse": round(value["rmse"], 4),
                "delta_vs_baseline": round(value["rmse"] - base, 4),
                "n": value["n"],
            }
        )
    rows.sort(key=_delta_desc)
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows


REGISTRY: dict[str, Calculation] = {
    "fn.ablation.selectVariants": Calculation("fn.ablation.selectVariants", select_variants),
    "fn.ablation.split": Calculation("fn.ablation.split", split),
    "fn.ablation.fit": Calculation("fn.ablation.fit", fit),
    "fn.ablation.score": Calculation("fn.ablation.score", score),
    "fn.ablation.compare": Calculation("fn.ablation.compare", compare),
}
