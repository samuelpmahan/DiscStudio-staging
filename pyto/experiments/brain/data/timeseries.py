"""time-series Calculations over one ordered numeric series.

every one takes ``args["values"]`` (a plain list of numbers, missing as ``None``
where the calculation says it tolerates one) and ``args["backend"]``: "py"
(pure python, the reference statement of the definition) or "np" (numpy). every
output is json-able; a window that has not filled yet is ``None``, never nan.
"""

import math

from pyto import Calculation

ROLLING = ("mean", "sum", "min", "max", "median", "var", "std", "count")
DECOMPOSITIONS = ("additive", "multiplicative")


def _backend(args):
    backend = args.get("backend", "py")
    if backend not in ("py", "np"):
        raise ValueError("unknown backend %r for a time-series calculation: py or np" % (backend,))
    return backend


def _series(args, key="values", least=1, allow_missing=False):
    values = args.get(key)
    if not isinstance(values, (list, tuple)):
        raise ValueError("%s must be a list of numbers" % key)
    out = []
    for v in values:
        if v is None:
            if not allow_missing:
                raise ValueError("this calculation needs a series with no holes in it")
            out.append(None)
        elif isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError("the series holds %r, which is not a number" % (v,))
        else:
            out.append(float(v))
    if len(out) < least:
        raise ValueError("this calculation needs at least %d points, got %d" % (least, len(out)))
    return out


def _reduce(kind, window):
    if kind == "count":
        return float(len(window))
    if kind == "sum":
        return math.fsum(window)
    if kind == "mean":
        return math.fsum(window) / len(window)
    if kind == "min":
        return min(window)
    if kind == "max":
        return max(window)
    if kind == "median":
        ordered = sorted(window)
        half = len(ordered) // 2
        return ordered[half] if len(ordered) % 2 else (ordered[half - 1] + ordered[half]) / 2.0
    if len(window) < 2:
        return None
    centre = math.fsum(window) / len(window)
    variance = math.fsum((v - centre) ** 2 for v in window) / (len(window) - 1)
    return variance if kind == "var" else math.sqrt(variance)


def rolling(args):
    """a rolling window statistic, one value per point, ``None`` until the window fills.

    ``window`` is the width, ``fn`` one of mean/sum/min/max/median/var/std/count,
    ``min_periods`` how few points still count (default: the whole window),
    ``center`` puts the window around the point instead of behind it.
    reference: numpy over the same slices.
    """
    values = _series(args, allow_missing=True)
    width = int(args.get("window", 3))
    if width < 1:
        raise ValueError("a rolling window needs a width of at least 1, got %d" % width)
    kind = args.get("fn", "mean")
    if kind not in ROLLING:
        raise ValueError("unknown rolling fn %r: one of %s" % (kind, ", ".join(ROLLING)))
    least = int(args.get("min_periods", width))
    if least < 1 or least > width:
        raise ValueError("min_periods must be between 1 and the window width")
    centred = bool(args.get("center", False))
    backend = _backend(args)
    out = []
    for i in range(len(values)):
        if centred:
            start = i - (width - 1) // 2
            stop = start + width
        else:
            start, stop = i - width + 1, i + 1
        window = [v for v in values[max(0, start):max(0, stop)] if v is not None]
        if len(window) < least:
            out.append(None)
        elif backend == "np":
            import numpy as np

            block = np.asarray(window, dtype=float)
            if kind == "count":
                out.append(float(block.size))
            elif kind == "sum":
                out.append(float(block.sum()))
            elif kind == "mean":
                out.append(float(block.mean()))
            elif kind == "min":
                out.append(float(block.min()))
            elif kind == "max":
                out.append(float(block.max()))
            elif kind == "median":
                out.append(float(np.median(block)))
            elif block.size < 2:
                out.append(None)
            elif kind == "var":
                out.append(float(block.var(ddof=1)))
            else:
                out.append(float(block.std(ddof=1)))
        else:
            out.append(_reduce(kind, window))
    return out


def difference(args):
    """the ``order``-th difference at lag ``lag``; the first points come back as ``None``."""
    values = _series(args)
    order = int(args.get("order", 1))
    lag = int(args.get("lag", 1))
    if order < 1 or lag < 1:
        raise ValueError("difference needs order >= 1 and lag >= 1")
    out = list(values)
    for _ in range(order):
        out = [None if i < lag or out[i] is None or out[i - lag] is None
               else out[i] - out[i - lag] for i in range(len(out))]
    return out


def integrate(args):
    """the running total that undoes a first difference, from ``start`` (default 0)."""
    values = _series(args, allow_missing=True)
    total = float(args.get("start", 0.0))
    out = []
    for v in values:
        if v is None:
            out.append(None)
            continue
        total += v
        out.append(total)
    return out


def ses(args):
    """simple exponential smoothing with level ``alpha``: the level, and a flat forecast.

    ``{"alpha", "fitted", "level", "forecast", "sse"}``. reference: the recurrence
    l_t = alpha x_t + (1 - alpha) l_{t-1}, l_0 = x_0.
    """
    values = _series(args, least=2)
    alpha = float(args.get("alpha", 0.3))
    if not 0.0 < alpha <= 1.0:
        raise ValueError("ses needs alpha in (0, 1], got %r" % (alpha,))
    horizon = int(args.get("horizon", 1))
    if horizon < 0:
        raise ValueError("horizon must not be negative")
    level = values[0]
    fitted = [None]
    sse = 0.0
    for value in values[1:]:
        fitted.append(level)
        sse += (value - level) ** 2
        level = alpha * value + (1.0 - alpha) * level
    return {"alpha": alpha, "level": level, "fitted": fitted, "sse": sse,
            "forecast": [level] * horizon}


def holt(args):
    """holt's linear trend: level and trend, damped by ``phi`` when it is given.

    ``{"alpha", "beta", "phi", "level", "trend", "fitted", "sse", "forecast"}``.
    """
    values = _series(args, least=3)
    alpha = float(args.get("alpha", 0.3))
    beta = float(args.get("beta", 0.1))
    phi = float(args.get("phi", 1.0))
    if not 0.0 < alpha <= 1.0 or not 0.0 < beta <= 1.0:
        raise ValueError("holt needs alpha and beta in (0, 1]")
    if not 0.0 < phi <= 1.0:
        raise ValueError("holt needs phi in (0, 1]")
    horizon = int(args.get("horizon", 3))
    if horizon < 0:
        raise ValueError("horizon must not be negative")
    level = values[0]
    trend = values[1] - values[0]
    fitted = [None, None]
    sse = 0.0
    for value in values[2:]:
        prediction = level + phi * trend
        fitted.append(prediction)
        sse += (value - prediction) ** 2
        new_level = alpha * value + (1.0 - alpha) * prediction
        trend = beta * (new_level - level) + (1.0 - beta) * phi * trend
        level = new_level
    forecast = []
    damped = 0.0
    for step in range(1, horizon + 1):
        damped += phi ** step
        forecast.append(level + damped * trend)
    return {"alpha": alpha, "beta": beta, "phi": phi, "level": level, "trend": trend,
            "fitted": fitted, "sse": sse, "forecast": forecast}


def seasonal_decompose(args):
    """trend, seasonal and remainder at a known ``period``.

    the trend is a centred moving average, the seasonal component the average
    detrended value per phase (centred to sum to zero, or to average one when the
    model is multiplicative), and the remainder what is left.
    """
    values = _series(args, least=4)
    period = int(args.get("period", 4))
    model = args.get("model", "additive")
    if model not in DECOMPOSITIONS:
        raise ValueError("model must be additive or multiplicative, got %r" % (model,))
    if period < 2:
        raise ValueError("a seasonal decomposition needs a period of at least 2")
    if len(values) < 2 * period:
        raise ValueError("a seasonal decomposition needs at least two whole periods")
    if model == "multiplicative" and any(v == 0.0 for v in values):
        raise ValueError("a multiplicative decomposition needs a series with no zeros")
    backend = _backend(args)
    trend = _centred_average(values, period, backend)
    detrended = []
    for value, level in zip(values, trend):
        if level is None:
            detrended.append(None)
        elif model == "additive":
            detrended.append(value - level)
        else:
            detrended.append(value / level)
    phases = [[] for _ in range(period)]
    for index, value in enumerate(detrended):
        if value is not None:
            phases[index % period].append(value)
    averages = [math.fsum(phase) / len(phase) if phase else (0.0 if model == "additive" else 1.0)
                for phase in phases]
    if model == "additive":
        shift = math.fsum(averages) / period
        averages = [a - shift for a in averages]
    else:
        scale = math.fsum(averages) / period
        averages = [a / scale for a in averages]
    seasonal = [averages[i % period] for i in range(len(values))]
    remainder = []
    for value, level, season in zip(values, trend, seasonal):
        if level is None:
            remainder.append(None)
        elif model == "additive":
            remainder.append(value - level - season)
        else:
            remainder.append(value / (level * season))
    return {"model": model, "period": period, "trend": trend, "seasonal": seasonal,
            "remainder": remainder}


def _centred_average(values, period, backend):
    out = []
    half = period // 2
    for i in range(len(values)):
        if period % 2 == 0:
            start, stop = i - half, i + half + 1
            if start < 0 or stop > len(values):
                out.append(None)
                continue
            window = values[start:stop]
            weights = [0.5] + [1.0] * (period - 1) + [0.5]
            total = math.fsum(w * v for w, v in zip(weights, window))
            out.append(total / period)
        else:
            start, stop = i - half, i + half + 1
            if start < 0 or stop > len(values):
                out.append(None)
                continue
            window = values[start:stop]
            if backend == "np":
                import numpy as np

                out.append(float(np.mean(np.asarray(window, dtype=float))))
            else:
                out.append(math.fsum(window) / period)
    return out


def acf(args):
    """the autocorrelation at lags 0..``nlags``. reference: numpy.correlate over the centred series.

    ``adjusted`` divides each lag by n - k instead of n (the unbiased estimate).
    """
    values = _series(args, least=2)
    nlags = int(args.get("nlags", min(10, len(values) - 1)))
    if nlags < 0 or nlags >= len(values):
        raise ValueError("nlags must be between 0 and one less than the series length")
    adjusted = bool(args.get("adjusted", False))
    backend = _backend(args)
    n = len(values)
    centre = math.fsum(values) / n
    if backend == "np":
        import numpy as np

        centred = np.asarray(values, dtype=float) - centre
        denominator = float((centred * centred).sum())
        if denominator == 0.0:
            raise ValueError("an autocorrelation needs a series that varies")
        out = []
        for k in range(nlags + 1):
            numerator = float((centred[k:] * centred[:n - k]).sum())
            out.append(numerator / (denominator * ((n - k) / n if adjusted else 1.0)))
        return out
    centred = [v - centre for v in values]
    denominator = math.fsum(v * v for v in centred)
    if denominator == 0.0:
        raise ValueError("an autocorrelation needs a series that varies")
    out = []
    for k in range(nlags + 1):
        numerator = math.fsum(centred[i + k] * centred[i] for i in range(n - k))
        out.append(numerator / (denominator * ((n - k) / n if adjusted else 1.0)))
    return out


def pacf(args):
    """the partial autocorrelation at lags 0..``nlags``, by the levinson-durbin recursion."""
    nlags = int(args.get("nlags", min(10, len(args.get("values", [])) - 1)))
    correlations = acf(dict(args, nlags=nlags, adjusted=False))
    out = [1.0]
    phi = {}
    for k in range(1, nlags + 1):
        if k == 1:
            phi[(1, 1)] = correlations[1]
        else:
            numerator = correlations[k] - math.fsum(
                phi[(k - 1, j)] * correlations[k - j] for j in range(1, k))
            denominator = 1.0 - math.fsum(
                phi[(k - 1, j)] * correlations[j] for j in range(1, k))
            if denominator == 0.0:
                raise ValueError("the levinson-durbin recursion broke down at lag %d" % k)
            phi[(k, k)] = numerator / denominator
        for j in range(1, k):
            phi[(k, j)] = phi[(k - 1, j)] - phi[(k, k)] * phi[(k - 1, k - j)]
        out.append(phi[(k, k)])
    return out


def ar_fit(args):
    """an AR(p) fit by ordinary least squares on the lagged design matrix.

    ``{"order", "intercept", "coefficients", "residuals", "sigma2", "r2", "n"}``
    where ``coefficients[i]`` multiplies x_{t-1-i}. reference: numpy.linalg.lstsq
    over the same design.
    """
    values = _series(args, least=3)
    order = int(args.get("order", 1))
    if order < 1:
        raise ValueError("an AR fit needs an order of at least 1")
    if len(values) <= order + 1:
        raise ValueError("an AR(%d) fit needs more than %d points" % (order, order + 1))
    fit_intercept = bool(args.get("intercept", True))
    backend = _backend(args)
    design = []
    target = []
    for t in range(order, len(values)):
        row = [values[t - 1 - i] for i in range(order)]
        if fit_intercept:
            row = [1.0] + row
        design.append(row)
        target.append(values[t])
    if backend == "np":
        import numpy as np

        a = np.asarray(design, dtype=float)
        b = np.asarray(target, dtype=float)
        solution, _, rank, _ = np.linalg.lstsq(a, b, rcond=None)
        if rank < a.shape[1]:
            raise ValueError("this AR design is rank deficient: the series is degenerate")
        beta = [float(v) for v in solution]
    else:
        beta = _normal_equations(design, target)
    intercept = beta[0] if fit_intercept else 0.0
    coefficients = beta[1:] if fit_intercept else beta
    residuals = []
    for row, actual in zip(design, target):
        predicted = math.fsum(c * v for c, v in zip(beta, row))
        residuals.append(actual - predicted)
    rss = math.fsum(r * r for r in residuals)
    centre = math.fsum(target) / len(target)
    tss = math.fsum((v - centre) ** 2 for v in target)
    free = len(target) - len(beta)
    return {"order": order, "intercept": intercept, "coefficients": coefficients,
            "residuals": residuals, "n": len(target),
            "sigma2": (rss / free) if free > 0 else None,
            "r2": (1.0 - rss / tss) if tss > 0 else None}


def _normal_equations(design, target):
    """solve the least-squares normal equations by gaussian elimination with partial pivoting."""
    width = len(design[0])
    gram = [[math.fsum(row[i] * row[j] for row in design) for j in range(width)]
            for i in range(width)]
    moment = [math.fsum(row[i] * y for row, y in zip(design, target)) for i in range(width)]
    for i in range(width):
        gram[i].append(moment[i])
    for column in range(width):
        pivot = max(range(column, width), key=lambda r: abs(gram[r][column]))
        if abs(gram[pivot][column]) < 1e-14:
            raise ValueError("this design is singular: the series is degenerate")
        gram[column], gram[pivot] = gram[pivot], gram[column]
        scale = gram[column][column]
        gram[column] = [v / scale for v in gram[column]]
        for row in range(width):
            if row == column:
                continue
            factor = gram[row][column]
            if factor:
                gram[row] = [v - factor * w for v, w in zip(gram[row], gram[column])]
    return [gram[i][width] for i in range(width)]


def ar_forecast(args):
    """``horizon`` steps ahead from an AR fit, feeding each prediction back in."""
    values = _series(args, least=1)
    fit = args.get("fit")
    if fit is None:
        fit = ar_fit(args)
    horizon = int(args.get("horizon", 3))
    if horizon < 1:
        raise ValueError("a forecast needs a horizon of at least 1")
    order = int(fit["order"])
    if len(values) < order:
        raise ValueError("a forecast needs at least as many points as the order")
    history = list(values)
    out = []
    for _ in range(horizon):
        prediction = fit["intercept"] + math.fsum(
            c * history[-1 - i] for i, c in enumerate(fit["coefficients"]))
        out.append(prediction)
        history.append(prediction)
    return {"order": order, "horizon": horizon, "forecast": out}


ROLLING_CALC = Calculation("fn.brain.data.rolling", rolling)
DIFFERENCE = Calculation("fn.brain.data.difference", difference)
INTEGRATE = Calculation("fn.brain.data.integrate", integrate)
SES = Calculation("fn.brain.data.ses", ses)
HOLT = Calculation("fn.brain.data.holt", holt)
SEASONAL_DECOMPOSE = Calculation("fn.brain.data.seasonal_decompose", seasonal_decompose)
ACF = Calculation("fn.brain.data.acf", acf)
PACF = Calculation("fn.brain.data.pacf", pacf)
AR_FIT = Calculation("fn.brain.data.ar_fit", ar_fit)
AR_FORECAST = Calculation("fn.brain.data.ar_forecast", ar_forecast)

CALCS = {
    c.address: c
    for c in (ROLLING_CALC, DIFFERENCE, INTEGRATE, SES, HOLT, SEASONAL_DECOMPOSE,
              ACF, PACF, AR_FIT, AR_FORECAST)
}
