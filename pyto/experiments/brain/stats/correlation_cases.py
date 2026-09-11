"""oracle and benchmark cases for the correlation calculations."""

import numpy as np
from scipy import stats as sp_stats

import stats.correlation as correlation
from stats.descriptive_cases import draw

X = draw(63, seed=21)
Y = [0.7 * v + 11.0 + w for v, w in zip(X, draw(63, seed=22, low=-25.0, high=25.0))]
MONOTONE = sorted(draw(30, seed=31))
CURVED = [v ** 3 for v in MONOTONE]
TIES_X = [1.0, 1.0, 2.0, 3.0, 3.0, 3.0, 4.0, 5.0, 5.0, 6.0]
TIES_Y = [2.0, 1.0, 2.0, 2.0, 5.0, 4.0, 4.0, 6.0, 5.0, 5.0]
TABLE = {
    "for": "a small numeric table the correlation matrix is read from",
    "columns": ["x", "y", "z"],
    "rows": [[X[i], Y[i], X[i] * X[i]] for i in range(20)],
}


def _case(calc, case, backend, args, reference, expected, tolerance=1e-9):
    return {"calc": calc, "case": case, "backend": backend,
            "args": dict(args, backend=backend), "reference": reference,
            "expected": expected, "tolerance": tolerance}


def _both(calc, case, args, reference, expected, tolerance=1e-9):
    return [_case(calc, "%s.py" % case, "py", args, reference, expected, tolerance),
            _case(calc, "%s.np" % case, "np", args, reference, expected, tolerance)]


ORACLE_CASES = []
ORACLE_CASES += _both(
    "fn.brain.stats.covariance", "linear", {"x": X, "y": Y, "ddof": 1},
    "numpy.cov", lambda: float(np.cov(X, Y, ddof=1)[0, 1]))
ORACLE_CASES += _both(
    "fn.brain.stats.pearson", "linear", {"x": X, "y": Y},
    "scipy.stats.pearsonr", lambda: float(sp_stats.pearsonr(X, Y).statistic))
ORACLE_CASES += _both(
    "fn.brain.stats.pearson", "curved", {"x": MONOTONE, "y": CURVED},
    "scipy.stats.pearsonr", lambda: float(sp_stats.pearsonr(MONOTONE, CURVED).statistic))
ORACLE_CASES += [
    _case("fn.brain.stats.rank", "ties.py", "py", {"values": TIES_X},
          "scipy.stats.rankdata", lambda: [float(v) for v in sp_stats.rankdata(TIES_X)]),
]
ORACLE_CASES += _both(
    "fn.brain.stats.spearman", "curved", {"x": MONOTONE, "y": CURVED},
    "scipy.stats.spearmanr", lambda: float(sp_stats.spearmanr(MONOTONE, CURVED).statistic))
ORACLE_CASES += _both(
    "fn.brain.stats.spearman", "ties", {"x": TIES_X, "y": TIES_Y},
    "scipy.stats.spearmanr", lambda: float(sp_stats.spearmanr(TIES_X, TIES_Y).statistic))
ORACLE_CASES += _both(
    "fn.brain.stats.kendall", "linear", {"x": X[:30], "y": Y[:30]},
    "scipy.stats.kendalltau",
    lambda: float(sp_stats.kendalltau(X[:30], Y[:30]).statistic))
ORACLE_CASES += _both(
    "fn.brain.stats.kendall", "ties", {"x": TIES_X, "y": TIES_Y},
    "scipy.stats.kendalltau", lambda: float(sp_stats.kendalltau(TIES_X, TIES_Y).statistic))
ORACLE_CASES += _both(
    "fn.brain.stats.correlation_matrix", "three", {"table": TABLE},
    "numpy.corrcoef",
    lambda: {"columns": ["x", "y", "z"],
             "matrix": [[float(v) for v in row]
                        for row in np.corrcoef(np.asarray(TABLE["rows"], dtype=float).T)]})

_SMALL_X = draw(1000, seed=301)
_SMALL_Y = draw(1000, seed=302)
_LARGE_X = draw(50000, seed=401)
_LARGE_Y = draw(50000, seed=402)
_KENDALL_SMALL = (draw(200, seed=501), draw(200, seed=502))
_KENDALL_BIG = (draw(800, seed=503), draw(800, seed=504))

BENCH_CASES = []
for _calc in ("fn.brain.stats.covariance", "fn.brain.stats.pearson", "fn.brain.stats.spearman"):
    for _backend in ("py", "np"):
        for _size, _pair in (("n=1000", (_SMALL_X, _SMALL_Y)), ("n=50000", (_LARGE_X, _LARGE_Y))):
            BENCH_CASES.append({
                "calc": _calc, "backend": _backend, "size": _size,
                "make_args": (lambda pair=_pair, backend=_backend:
                              {"x": pair[0], "y": pair[1], "backend": backend})})
for _backend in ("py", "np"):
    for _size, _pair in (("n=200", _KENDALL_SMALL), ("n=800", _KENDALL_BIG)):
        BENCH_CASES.append({
            "calc": "fn.brain.stats.kendall", "backend": _backend, "size": _size,
            "make_args": (lambda pair=_pair, backend=_backend:
                          {"x": pair[0], "y": pair[1], "backend": backend})})

CALCS = correlation.CALCS
