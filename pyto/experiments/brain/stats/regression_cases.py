"""oracle and benchmark cases for the regression calculations.

the authority is numpy and scipy together: ``numpy.linalg.lstsq`` for the
coefficients, and the textbook standard errors, t statistics, F and their tails
from ``scipy.stats.t`` and ``scipy.stats.f`` -- all of it computed below in
``brute_ols``, which is the reference every one of the three solvers answers to.
``scipy.stats.linregress`` checks the simple-regression corner independently.
"""

import numpy as np
from scipy import stats as sp_stats

import stats.regression as regression


def draw(n, seed, low=-3.0, high=3.0):
    state = (seed * 6364136223846793005 + 1442695040888963407) % (2 ** 64)
    out = []
    for _ in range(n):
        state = (state * 6364136223846793005 + 1442695040888963407) % (2 ** 64)
        out.append(low + (high - low) * ((state >> 11) / float(2 ** 53)))
    return out


N = 80
X1 = draw(N, 201)
X2 = draw(N, 202, low=0.0, high=10.0)
X3 = [a * 0.5 + b * 0.1 for a, b in zip(draw(N, 203), X2)]
NOISE = draw(N, 204, low=-1.2, high=1.2)
Y = [4.5 + 2.0 * a - 0.75 * b + 1.25 * c + e for a, b, c, e in zip(X1, X2, X3, NOISE)]
DESIGN = [[a, b, c] for a, b, c in zip(X1, X2, X3)]
SIMPLE = [[a] for a in X1]
SIMPLE_Y = [3.0 + 1.5 * a + e for a, e in zip(X1, NOISE)]
CLASSES = [1.0 if (2.0 * a - 0.4 * b + e) > 0.0 else 0.0
           for a, b, e in zip(X1, X2, NOISE)]
BIG_DESIGN = [[a, b, c] for a, b, c in zip(draw(2000, 301), draw(2000, 302),
                                           draw(2000, 303))]
BIG_Y = [1.0 + 2.0 * r[0] - 0.5 * r[1] + 0.25 * r[2] for r in BIG_DESIGN]
MID_DESIGN, MID_Y = BIG_DESIGN[:300], BIG_Y[:300]


def brute_ols(design, y, intercept=True):
    """numpy for the fit, scipy for the tails: the reference the solvers answer to."""
    a = np.asarray([([1.0] + list(row)) if intercept else list(row) for row in design],
                   dtype=float)
    b = np.asarray(y, dtype=float)
    beta = np.linalg.lstsq(a, b, rcond=None)[0]
    fitted = a @ beta
    residuals = b - fitted
    n, width = a.shape
    free = n - width
    rss = float(residuals @ residuals)
    tss = float(((b - b.mean()) ** 2).sum())
    sigma2 = rss / free
    inverse = np.linalg.inv(a.T @ a)
    stderr = np.sqrt(sigma2 * np.diag(inverse))
    t_values = beta / stderr
    pvalues = 2.0 * sp_stats.t.sf(np.abs(t_values), free)
    r2 = 1.0 - rss / tss
    k = width - (1 if intercept else 0)
    fstat = (r2 / k) / ((1.0 - r2) / free)
    return {
        "coefficients": [float(v) for v in beta],
        "stderr": [float(v) for v in stderr],
        "t": [float(v) for v in t_values],
        "pvalues": [float(v) for v in pvalues],
        "n": n, "k": width, "df_residual": free,
        "sigma2": sigma2, "rss": rss, "tss": tss, "r2": r2,
        "adj_r2": 1.0 - (1.0 - r2) * (n - 1) / free,
        "fstat": float(fstat), "f_pvalue": float(sp_stats.f.sf(fstat, k, free)),
    }


def brute_ridge(design, y, penalty, intercept=True):
    """numpy.linalg.solve on the penalised normal equations; the intercept is free."""
    a = np.asarray([([1.0] + list(row)) if intercept else list(row) for row in design],
                   dtype=float)
    b = np.asarray(y, dtype=float)
    eye = np.eye(a.shape[1])
    if intercept:
        eye[0, 0] = 0.0
    beta = np.linalg.solve(a.T @ a + penalty * eye, a.T @ b)
    return [float(v) for v in beta]


def _report_fields(got):
    """the fields the reference has an opinion about, in the reference's own shape."""
    return {key: got[key] for key in
            ("coefficients", "stderr", "t", "pvalues", "n", "k", "df_residual",
             "sigma2", "rss", "tss", "r2", "adj_r2", "fstat", "f_pvalue")}


def _case(calc, case, backend, args, reference, expected, tolerance=1e-8, project=None):
    return {"calc": calc, "case": case, "backend": backend,
            "args": dict(args, backend=backend), "reference": reference,
            "expected": expected, "tolerance": tolerance, "project": project}


ORACLE_CASES = []
for _address, _backend in (("fn.brain.stats.ols_normal", "py"),
                           ("fn.brain.stats.ols_qr", "py"),
                           ("fn.brain.stats.ols_lstsq", "np")):
    _short = _address.rsplit("_", 1)[1]
    ORACLE_CASES.append(_case(
        _address, "three.predictors.%s" % _short, _backend, {"x": DESIGN, "y": Y},
        "numpy.linalg.lstsq with scipy.stats.t/f for the tails",
        lambda: brute_ols(DESIGN, Y), 1e-8, _report_fields))
    ORACLE_CASES.append(_case(
        _address, "simple.%s" % _short, _backend, {"x": SIMPLE, "y": SIMPLE_Y},
        "numpy.linalg.lstsq with scipy.stats.t/f for the tails",
        lambda: brute_ols(SIMPLE, SIMPLE_Y), 1e-8, _report_fields))
    ORACLE_CASES.append(_case(
        _address, "no.intercept.%s" % _short, _backend,
        {"x": DESIGN, "y": Y, "intercept": False},
        "numpy.linalg.lstsq with scipy.stats.t/f for the tails",
        lambda: brute_ols(DESIGN, Y, intercept=False), 1e-8, _report_fields))

for _solver, _backend in (("normal", "py"), ("qr", "py"), ("lstsq", "np")):
    ORACLE_CASES.append(_case(
        "fn.brain.stats.ols", "facade.%s" % _solver, _backend,
        {"x": DESIGN, "y": Y, "solver": _solver},
        "numpy.linalg.lstsq with scipy.stats.t/f for the tails",
        lambda: brute_ols(DESIGN, Y), 1e-8, _report_fields))

for _penalty in (0.0, 0.5, 25.0):
    for _backend in ("py", "np"):
        ORACLE_CASES.append(_case(
            "fn.brain.stats.ridge", "lambda%s.%s" % (str(_penalty).replace(".", "p"), _backend),
            _backend, {"x": DESIGN, "y": Y, "lam": _penalty},
            "numpy.linalg.solve on the penalised normal equations",
            (lambda penalty=_penalty: brute_ridge(DESIGN, Y, penalty)), 1e-8,
            lambda got: got["coefficients"]))

BENCH_CASES = []
for _calc, _backend in (("fn.brain.stats.ols_normal", "py"),
                        ("fn.brain.stats.ols_qr", "py"),
                        ("fn.brain.stats.ols_lstsq", "np")):
    for _size, _pair in (("n=300", (MID_DESIGN, MID_Y)), ("n=2000", (BIG_DESIGN, BIG_Y))):
        BENCH_CASES.append({
            "calc": _calc, "backend": _backend, "size": _size,
            "make_args": (lambda pair=_pair, backend=_backend:
                          {"x": pair[0], "y": pair[1], "backend": backend})})
for _backend in ("py", "np"):
    for _size, _pair in (("n=300", (MID_DESIGN, MID_Y)), ("n=2000", (BIG_DESIGN, BIG_Y))):
        BENCH_CASES.append({
            "calc": "fn.brain.stats.ridge", "backend": _backend, "size": _size,
            "make_args": (lambda pair=_pair, backend=_backend:
                          {"x": pair[0], "y": pair[1], "lam": 1.0, "backend": backend})})

CALCS = regression.CALCS
