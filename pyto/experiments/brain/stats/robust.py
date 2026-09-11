"""simple regression, three ways: the least-squares verdict and two robust slopes.

``fn.brain.stats.linregress`` is the whole one-predictor verdict in one place
(slope, intercept, r, its p-value and the two standard errors).
``fn.brain.stats.theil_sen`` and ``fn.brain.stats.siegel_slopes`` are the
medians-of-slopes estimators that do not care about a handful of bad points,
which is exactly what OLS does care about.
"""

import math

from pyto import Calculation

from stats.distributions import _cdf_py, _ppf_py


def _backend(args):
    backend = args.get("backend", "py")
    if backend not in ("py", "sp"):
        raise ValueError("unknown backend %r for a robust regression: py or sp" % (backend,))
    return backend


def _pair(args, least=3):
    y = [float(v) for v in args["y"]]
    x = args.get("x")
    x = list(range(len(y))) if x is None else [float(v) for v in x]
    x = [float(v) for v in x]
    if len(x) != len(y):
        raise ValueError("x and y must be the same length, got %d and %d" % (len(x), len(y)))
    if len(x) < least:
        raise ValueError("this regression needs at least %d points, got %d" % (least, len(x)))
    return x, y


def _median(values):
    ordered = sorted(values)
    half = len(ordered) // 2
    return ordered[half] if len(ordered) % 2 else (ordered[half - 1] + ordered[half]) / 2.0


def linregress(args):
    """the whole simple-regression verdict. reference: scipy.stats.linregress.

    ``{"slope", "intercept", "r", "pvalue", "stderr", "intercept_stderr", "n", "df"}``.
    """
    x, y = _pair(args)
    alternative = args.get("alternative", "two-sided")
    if alternative not in ("two-sided", "less", "greater"):
        raise ValueError("alternative must be two-sided, less or greater, got %r" % (alternative,))
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.linregress(x, y, alternative=alternative)
        return {"slope": float(out.slope), "intercept": float(out.intercept),
                "r": float(out.rvalue), "pvalue": float(out.pvalue),
                "stderr": float(out.stderr), "intercept_stderr": float(out.intercept_stderr),
                "n": len(x), "df": float(len(x) - 2)}
    n = len(x)
    mx = math.fsum(x) / n
    my = math.fsum(y) / n
    sxx = math.fsum((v - mx) ** 2 for v in x)
    syy = math.fsum((v - my) ** 2 for v in y)
    sxy = math.fsum((a - mx) * (b - my) for a, b in zip(x, y))
    if sxx == 0.0:
        raise ValueError("a simple regression needs x to vary")
    slope = sxy / sxx
    intercept = my - slope * mx
    r = sxy / math.sqrt(sxx * syy) if syy > 0.0 else 0.0
    r = max(-1.0, min(1.0, r))
    df = float(n - 2)
    if df <= 0.0:
        raise ValueError("a simple regression needs more than two points for a p-value")
    if abs(r) >= 1.0:
        statistic = float("inf")
        pvalue = 0.0
        stderr = 0.0
    else:
        statistic = r * math.sqrt(df / (1.0 - r * r))
        cdf = _cdf_py("t", {"df": df}, statistic)
        if alternative == "less":
            pvalue = cdf
        elif alternative == "greater":
            pvalue = 1.0 - cdf
        else:
            pvalue = 2.0 * min(cdf, 1.0 - cdf)
        stderr = math.sqrt((1.0 - r * r) * syy / sxx / df)
    return {"slope": slope, "intercept": intercept, "r": r,
            "pvalue": max(0.0, min(1.0, pvalue)), "stderr": stderr,
            "intercept_stderr": stderr * math.sqrt(math.fsum(v * v for v in x) / n),
            "n": n, "df": df}


def theil_sen(args):
    """the median of every pairwise slope, with its confidence interval.

    reference: scipy.stats.theilslopes. ``{"slope", "intercept", "low", "high",
    "level"}``; the intercept is median(y) - slope * median(x), which is what
    scipy's default ``method="separate"`` computes.
    """
    x, y = _pair(args)
    level = float(args.get("level", 0.95))
    if not 0.0 < level < 1.0:
        raise ValueError("a confidence level is in (0, 1), got %r" % (level,))
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.theilslopes(y, x, alpha=level)
        return {"slope": float(out.slope), "intercept": float(out.intercept),
                "low": float(out.low_slope), "high": float(out.high_slope),
                "level": level, "n": len(x)}
    n = len(x)
    slopes = []
    for i in range(n):
        for j in range(i + 1, n):
            if x[j] != x[i]:
                slopes.append((y[j] - y[i]) / (x[j] - x[i]))
    if not slopes:
        raise ValueError("every pair of points shares an x; there is no slope to take")
    slopes.sort()
    slope = _median(slopes)
    intercept = _median(y) - slope * _median(x)
    # the same interval scipy takes: a normal approximation to the kendall
    # statistic's spread, turned into a rank either side of the median slope.
    counts = {}
    for value in x:
        counts[value] = counts.get(value, 0) + 1
    ties_x = math.fsum(t * (t - 1) * (2 * t + 5) for t in counts.values())
    counts = {}
    for value in y:
        counts[value] = counts.get(value, 0) + 1
    ties_y = math.fsum(t * (t - 1) * (2 * t + 5) for t in counts.values())
    spread = math.sqrt((n * (n - 1) * (2 * n + 5) - ties_x - ties_y) / 18.0)
    total = len(slopes)
    # sen (1968), equation 2.6, and the same two ranks scipy takes from it.
    z = _ppf_py("normal", {"mu": 0.0, "sigma": 1.0}, (1.0 - level) / 2.0)
    high_at = min(int(round((total - z * spread) / 2.0)), total - 1)
    low_at = max(int(round((total + z * spread) / 2.0)) - 1, 0)
    return {"slope": slope, "intercept": intercept, "low": slopes[low_at],
            "high": slopes[high_at], "level": level, "n": n}


def siegel_slopes(args):
    """siegel's repeated-median slope: a median of medians, so it survives more.

    reference: scipy.stats.siegelslopes (``method="hierarchical"`` is the default
    there and is what this computes).
    """
    x, y = _pair(args)
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.siegelslopes(y, x)
        return {"slope": float(out.slope), "intercept": float(out.intercept), "n": len(x)}
    n = len(x)
    medians = []
    for i in range(n):
        slopes = [(y[j] - y[i]) / (x[j] - x[i]) for j in range(n) if x[j] != x[i]]
        if slopes:
            medians.append(_median(slopes))
    if not medians:
        raise ValueError("every point shares its x with every other; there is no slope to take")
    slope = _median(medians)
    intercept = _median([b - slope * a for a, b in zip(x, y)])
    return {"slope": slope, "intercept": intercept, "n": n}


LINREGRESS = Calculation("fn.brain.stats.linregress", linregress)
THEIL_SEN = Calculation("fn.brain.stats.theil_sen", theil_sen)
SIEGEL_SLOPES = Calculation("fn.brain.stats.siegel_slopes", siegel_slopes)

CALCS = {c.address: c for c in (LINREGRESS, THEIL_SEN, SIEGEL_SLOPES)}
