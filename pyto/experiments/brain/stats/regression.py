"""regression: ordinary least squares (three solvers), ridge, and logistic.

the three OLS solvers are separate Calculations on purpose -- they are the
candidates of a tournament, and the facade ``fn.brain.stats.ols`` dispatches to
one of them by ``args["solver"]``. all three answer to the same oracle: numpy's
``lstsq`` coefficients and the textbook standard errors.

the design is ``args["x"]``: a list of rows (each a list of numbers), or a
dataset Part plus ``args["columns"]``. ``args["intercept"]`` (default true) adds
the column of ones; it is never penalised by ridge.
"""

import math

from pyto import Calculation

from stats.distributions import cdf as distribution_cdf


def _weights(args, rows):
    """the observation weights, checked. no weights is the same as all-ones."""
    weights = args.get("weights")
    if weights is None:
        return None
    weights = [float(v) for v in weights]
    if len(weights) != rows:
        raise ValueError("there are %d rows and %d weights" % (rows, len(weights)))
    if any(v < 0.0 for v in weights):
        raise ValueError("a weight cannot be negative")
    if not any(v > 0.0 for v in weights):
        raise ValueError("at least one weight has to be positive")
    return weights


def _design(args):
    x = args["x"]
    if isinstance(x, dict):
        names = args.get("columns") or [c for c in x["columns"]]
        at = []
        for name in names:
            if name not in x["columns"]:
                raise ValueError("no column %r in this dataset: %r" % (name, list(x["columns"])))
            at.append(list(x["columns"]).index(name))
        rows = [[float(row[i]) for i in at] for row in x["rows"]]
    else:
        rows = []
        for row in x:
            if not isinstance(row, (list, tuple)):
                rows.append([float(row)])
            else:
                rows.append([float(v) for v in row])
        names = args.get("columns") or ["x%d" % i for i in range(len(rows[0]) if rows else 0)]
    if not rows:
        raise ValueError("a regression needs at least one row of design")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("every row of the design must be the same width")
    y = [float(v) for v in args["y"]]
    if len(y) != len(rows):
        raise ValueError("the design has %d rows and y has %d values" % (len(rows), len(y)))
    if args.get("intercept", True):
        rows = [[1.0] + row for row in rows]
        names = ["intercept"] + list(names)
    if len(rows) <= len(rows[0]):
        raise ValueError(
            "a regression needs more rows (%d) than columns (%d)" % (len(rows), len(rows[0])))
    return rows, y, list(names)


def _backend(args, allowed=("py", "np")):
    backend = args.get("backend", "py")
    if backend not in allowed:
        raise ValueError("unknown backend %r for a regression: %s"
                         % (backend, " or ".join(allowed)))
    return backend


def _gram(design):
    width = len(design[0])
    return [[math.fsum(row[i] * row[j] for row in design) for j in range(width)]
            for i in range(width)]


def _solve(matrix, right):
    """gauss-jordan with partial pivoting; returns the solution and the inverse."""
    width = len(matrix)
    work = [list(matrix[i]) + [0.0] * width + [right[i]] for i in range(width)]
    for i in range(width):
        work[i][width + i] = 1.0
    for column in range(width):
        pivot = max(range(column, width), key=lambda r: abs(work[r][column]))
        if abs(work[pivot][column]) < 1e-12:
            raise ValueError("this design is singular: two columns say the same thing")
        work[column], work[pivot] = work[pivot], work[column]
        scale = work[column][column]
        work[column] = [v / scale for v in work[column]]
        for row in range(width):
            if row == column:
                continue
            factor = work[row][column]
            if factor:
                work[row] = [v - factor * w for v, w in zip(work[row], work[column])]
    solution = [work[i][2 * width] for i in range(width)]
    inverse = [[work[i][width + j] for j in range(width)] for i in range(width)]
    return solution, inverse


def _householder_qr(design):
    """the thin QR of the design by householder reflections, in pure python.

    returns ``(r, qty)`` where ``r`` is upper triangular and the caller has
    already had Q' applied to y -- the reflections are applied to the augmented
    matrix, so Q is never formed.
    """
    rows = [list(row) for row in design]
    n, width = len(rows), len(rows[0]) - 1
    for column in range(width):
        norm = math.sqrt(math.fsum(rows[i][column] ** 2 for i in range(column, n)))
        if norm == 0.0:
            raise ValueError("this design is singular: a column is all zeros")
        alpha = -norm if rows[column][column] >= 0 else norm
        v = [0.0] * n
        v[column] = rows[column][column] - alpha
        for i in range(column + 1, n):
            v[i] = rows[i][column]
        vv = math.fsum(value * value for value in v[column:])
        if vv == 0.0:
            continue
        for j in range(column, width + 1):
            dot = math.fsum(v[i] * rows[i][j] for i in range(column, n))
            factor = 2.0 * dot / vv
            for i in range(column, n):
                rows[i][j] -= factor * v[i]
    r = [[rows[i][j] for j in range(width)] for i in range(width)]
    qty = [rows[i][width] for i in range(width)]
    return r, qty


def _back_substitute(r, qty):
    width = len(r)
    out = [0.0] * width
    for i in range(width - 1, -1, -1):
        if abs(r[i][i]) < 1e-12:
            raise ValueError("this design is rank deficient: the QR has a zero on the diagonal")
        total = qty[i] - math.fsum(r[i][j] * out[j] for j in range(i + 1, width))
        out[i] = total / r[i][i]
    return out


def _report(design, y, beta, names, inverse=None):
    n, width = len(design), len(design[0])
    fitted = [math.fsum(b * v for b, v in zip(beta, row)) for row in design]
    residuals = [actual - guess for actual, guess in zip(y, fitted)]
    rss = math.fsum(r * r for r in residuals)
    centre = math.fsum(y) / n
    tss = math.fsum((v - centre) ** 2 for v in y)
    free = n - width
    sigma2 = rss / free if free > 0 else None
    if inverse is None:
        _, inverse = _solve(_gram(design), [0.0] * width)
    stderr = [math.sqrt(sigma2 * inverse[i][i]) if sigma2 is not None and inverse[i][i] > 0
              else None for i in range(width)]
    t_values = [(b / s) if s else None for b, s in zip(beta, stderr)]
    pvalues = []
    for t in t_values:
        if t is None or free <= 0:
            pvalues.append(None)
        else:
            tail = distribution_cdf({"dist": "t", "params": {"df": float(free)}, "x": -abs(t)})
            pvalues.append(2.0 * tail)
    r2 = 1.0 - rss / tss if tss > 0 else None
    has_intercept = names and names[0] == "intercept"
    k = width - (1 if has_intercept else 0)
    adj = (1.0 - (1.0 - r2) * (n - 1) / free) if (r2 is not None and free > 0) else None
    fstat = f_pvalue = None
    if r2 is not None and k > 0 and free > 0 and r2 < 1.0:
        fstat = (r2 / k) / ((1.0 - r2) / free)
        from stats.hypothesis import _f_sf

        f_pvalue = _f_sf(fstat, float(k), float(free))
    return {"names": names, "coefficients": list(beta), "stderr": stderr,
            "t": t_values, "pvalues": pvalues, "residuals": residuals, "fitted": fitted,
            "n": n, "k": width, "df_residual": free, "sigma2": sigma2,
            "rss": rss, "tss": tss, "r2": r2, "adj_r2": adj,
            "fstat": fstat, "f_pvalue": f_pvalue}


def ols_normal(args):
    """OLS by the normal equations X'X b = X'y, solved with gauss-jordan. candidate one."""
    design, y, names = _design(args)
    _backend(args, ("py",))
    moment = [math.fsum(row[i] * value for row, value in zip(design, y))
              for i in range(len(design[0]))]
    beta, inverse = _solve(_gram(design), moment)
    return _report(design, y, beta, names, inverse)


def ols_qr(args):
    """OLS by a householder QR of the design, never forming X'X. candidate two."""
    design, y, names = _design(args)
    _backend(args, ("py",))
    r, qty = _householder_qr([list(row) + [value] for row, value in zip(design, y)])
    beta = _back_substitute(r, qty)
    width = len(r)
    inverse = []
    for column in range(width):
        unit = [1.0 if i == column else 0.0 for i in range(width)]
        # (X'X)^-1 = R^-1 R^-T, so solve R' z = e then R c = z.
        z = [0.0] * width
        for i in range(width):
            z[i] = (unit[i] - math.fsum(r[j][i] * z[j] for j in range(i))) / r[i][i]
        inverse.append(_back_substitute(r, z))
    inverse = [[inverse[j][i] for j in range(width)] for i in range(width)]
    return _report(design, y, beta, names, inverse)


def ols_lstsq(args):
    """OLS by numpy.linalg.lstsq (an SVD under the hood). candidate three."""
    design, y, names = _design(args)
    _backend(args, ("np",))
    import numpy as np

    a = np.asarray(design, dtype=float)
    b = np.asarray(y, dtype=float)
    solution, _, rank, _ = np.linalg.lstsq(a, b, rcond=None)
    if rank < a.shape[1]:
        raise ValueError("this design is rank deficient: two columns say the same thing")
    inverse = np.linalg.inv(a.T @ a)
    return _report(design, y, [float(v) for v in solution], names,
                   [[float(v) for v in row] for row in inverse])


def wls(args):
    """weighted least squares, through whichever of the three solvers is named.

    the weights go into the DESIGN, not into a fourth solver: each row of X and
    each y is multiplied by sqrt(w), which makes the weighted normal equations
    the ordinary ones of the scaled problem. so the tournament's answer still
    holds -- `solver` picks the same three routes -- and the reported residuals
    and fitted values are put back on the original scale before they are handed
    out. reference: numpy.linalg.lstsq on the scaled design.
    """
    rows = args["x"]
    length = len(rows["rows"]) if isinstance(rows, dict) else len(rows)
    weights = _weights(args, length)
    if weights is None:
        return ols(args)
    solver = args.get("solver", DEFAULT_SOLVER)
    if solver not in SOLVERS:
        raise ValueError("unknown solver %r: one of %s" % (solver, ", ".join(sorted(SOLVERS))))
    design, y, names = _design(args)
    roots = [math.sqrt(w) for w in weights]
    scaled_rows = [[value * root for value in row] for row, root in zip(design, roots)]
    scaled_y = [value * root for value, root in zip(y, roots)]
    backend = "np" if solver == "lstsq" else "py"
    fit = SOLVERS[solver]({"x": scaled_rows, "y": scaled_y, "intercept": False,
                           "columns": names, "backend": backend})
    beta = fit["coefficients"]
    fitted = [math.fsum(b * v for b, v in zip(beta, row)) for row in design]
    residuals = [actual - guess for actual, guess in zip(y, fitted)]
    weighted_rss = math.fsum(w * r * r for w, r in zip(weights, residuals))
    total_weight = math.fsum(weights)
    centre = math.fsum(w * value for w, value in zip(weights, y)) / total_weight
    weighted_tss = math.fsum(w * (value - centre) ** 2 for w, value in zip(weights, y))
    out = dict(fit)
    out.update({"names": names, "weights": weights, "fitted": fitted,
                "residuals": residuals, "rss": weighted_rss, "tss": weighted_tss,
                "r2": (1.0 - weighted_rss / weighted_tss) if weighted_tss > 0 else None,
                "solver": solver})
    free = out["df_residual"]
    out["adj_r2"] = ((1.0 - (1.0 - out["r2"]) * (len(y) - 1) / free)
                     if (out["r2"] is not None and free > 0) else None)
    return out


SOLVERS = {"normal": ols_normal, "qr": ols_qr, "lstsq": ols_lstsq}

DEFAULT_SOLVER = "lstsq"
"""which route the facade takes when nobody names one.

this constant is the tournament's output, not an opinion: the bracket
`px.exp.brain.bracket.stats.ols_solver` scores the three solvers on correctness,
conditioning, speed and clarity, and `stats.build` re-runs it and records whether
this line still agrees with the winner. change the line, not the bracket.
"""


def ols(args):
    """the OLS facade: ``solver`` picks normal, qr or lstsq. reference: numpy.linalg.lstsq."""
    solver = args.get("solver", DEFAULT_SOLVER)
    if solver not in SOLVERS:
        raise ValueError("unknown solver %r: one of %s" % (solver, ", ".join(sorted(SOLVERS))))
    backend = args.get("backend", "np" if solver == "lstsq" else "py")
    return SOLVERS[solver](dict(args, backend=backend))


def ridge(args):
    """ridge regression: (X'X + lambda I) b = X'y, with the intercept left unpenalised."""
    design, y, names = _design(args)
    penalty = float(args.get("lam", 1.0))
    if penalty < 0.0:
        raise ValueError("ridge needs a non-negative lambda, got %r" % (penalty,))
    backend = _backend(args)
    width = len(design[0])
    has_intercept = names and names[0] == "intercept"
    if backend == "np":
        import numpy as np

        a = np.asarray(design, dtype=float)
        b = np.asarray(y, dtype=float)
        eye = np.eye(width)
        if has_intercept:
            eye[0, 0] = 0.0
        beta = np.linalg.solve(a.T @ a + penalty * eye, a.T @ b)
        beta = [float(v) for v in beta]
    else:
        gram = _gram(design)
        for i in range(width):
            if not (has_intercept and i == 0):
                gram[i][i] += penalty
        moment = [math.fsum(row[i] * value for row, value in zip(design, y))
                  for i in range(width)]
        beta, _ = _solve(gram, moment)
    fitted = [math.fsum(b * v for b, v in zip(beta, row)) for row in design]
    residuals = [actual - guess for actual, guess in zip(y, fitted)]
    rss = math.fsum(r * r for r in residuals)
    centre = math.fsum(y) / len(y)
    tss = math.fsum((v - centre) ** 2 for v in y)
    return {"names": names, "coefficients": list(beta), "lam": penalty,
            "residuals": residuals, "fitted": fitted, "rss": rss,
            "r2": (1.0 - rss / tss) if tss > 0 else None, "n": len(y), "k": width}


def _sigmoid(z):
    if z >= 0.0:
        return 1.0 / (1.0 + math.exp(-z))
    exponent = math.exp(z)
    return exponent / (1.0 + exponent)


def logistic(args):
    """logistic regression by IRLS (default) or gradient descent.

    ``{"names", "coefficients", "iterations", "converged", "log_likelihood",
    "stderr", "z", "pvalues", "method"}``. y must be 0/1.
    """
    design, y, names = _design(args)
    for value in y:
        if value not in (0.0, 1.0):
            raise ValueError("logistic regression needs y in {0, 1}, got %r" % (value,))
    if len(set(y)) < 2:
        raise ValueError("logistic regression needs both classes in y")
    method = args.get("method", "irls")
    if method not in ("irls", "gd"):
        raise ValueError("logistic method must be irls or gd, got %r" % (method,))
    backend = _backend(args)
    steps = int(args.get("max_iter", 100 if method == "irls" else 20000))
    tolerance = float(args.get("tol", 1e-10))
    rate = float(args.get("learning_rate", 0.1))
    width = len(design[0])
    beta = [0.0] * width
    converged = False
    used = 0
    inverse = None
    for used in range(1, steps + 1):
        probabilities = [_sigmoid(math.fsum(b * v for b, v in zip(beta, row))) for row in design]
        gradient = [math.fsum((value - p) * row[i] for row, value, p in zip(design, y, probabilities))
                    for i in range(width)]
        if method == "gd":
            step = [rate * g / len(y) for g in gradient]
            beta = [b + s for b, s in zip(beta, step)]
            if max(abs(s) for s in step) < tolerance:
                converged = True
                break
        else:
            weights = [max(p * (1.0 - p), 1e-12) for p in probabilities]
            if backend == "np":
                import numpy as np

                a = np.asarray(design, dtype=float)
                w = np.asarray(weights, dtype=float)
                hessian = (a * w[:, None]).T @ a
                inverse = np.linalg.inv(hessian)
                step = inverse @ np.asarray(gradient, dtype=float)
                step = [float(v) for v in step]
                inverse = [[float(v) for v in row] for row in inverse]
            else:
                hessian = [[math.fsum(w * row[i] * row[j] for row, w in zip(design, weights))
                            for j in range(width)] for i in range(width)]
                step, inverse = _solve(hessian, gradient)
            beta = [b + s for b, s in zip(beta, step)]
            if max(abs(s) for s in step) < tolerance:
                converged = True
                break
    probabilities = [_sigmoid(math.fsum(b * v for b, v in zip(beta, row))) for row in design]
    log_likelihood = math.fsum(
        value * math.log(max(p, 1e-300)) + (1.0 - value) * math.log(max(1.0 - p, 1e-300))
        for value, p in zip(y, probabilities))
    stderr = z = pvalues = None
    if inverse is not None:
        stderr = [math.sqrt(inverse[i][i]) if inverse[i][i] > 0 else None for i in range(width)]
        z = [(b / s) if s else None for b, s in zip(beta, stderr)]
        pvalues = [None if value is None else
                   2.0 * distribution_cdf({"dist": "normal", "x": -abs(value)}) for value in z]
    return {"names": names, "coefficients": list(beta), "method": method,
            "iterations": used, "converged": converged, "log_likelihood": log_likelihood,
            "probabilities": probabilities, "stderr": stderr, "z": z, "pvalues": pvalues}


def predict(args):
    """the linear (or logistic) prediction of a fit over new rows."""
    fit = args["fit"]
    beta = [float(v) for v in fit["coefficients"]]
    rows = args["x"]
    if isinstance(rows, dict):
        rows = [list(row) for row in rows["rows"]]
    out = []
    for row in rows:
        values = [float(v) for v in (row if isinstance(row, (list, tuple)) else [row])]
        if fit.get("names") and fit["names"][0] == "intercept":
            values = [1.0] + values
        if len(values) != len(beta):
            raise ValueError("a row of %d values cannot meet %d coefficients"
                             % (len(values), len(beta)))
        total = math.fsum(b * v for b, v in zip(beta, values))
        out.append(_sigmoid(total) if args.get("link") == "logit" else total)
    return out


OLS = Calculation("fn.brain.stats.ols", ols)
WLS = Calculation("fn.brain.stats.ols_weighted", wls)
OLS_NORMAL = Calculation("fn.brain.stats.ols_normal", ols_normal)
OLS_QR = Calculation("fn.brain.stats.ols_qr", ols_qr)
OLS_LSTSQ = Calculation("fn.brain.stats.ols_lstsq", ols_lstsq)
RIDGE = Calculation("fn.brain.stats.ridge", ridge)
LOGISTIC = Calculation("fn.brain.stats.logistic", logistic)
PREDICT = Calculation("fn.brain.stats.predict", predict)

CALCS = {c.address: c
         for c in (OLS, WLS, OLS_NORMAL, OLS_QR, OLS_LSTSQ, RIDGE, LOGISTIC, PREDICT)}
