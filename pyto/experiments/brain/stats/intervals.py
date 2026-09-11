"""confidence intervals, the bootstrap, and effect sizes.

the intervals are closed form and pure. the bootstrap is not: a resample is a
draw, so it is ``oc.brain.stats.bootstrap`` and every draw goes through the
run's effects handle -- which means the ledger carries the resample and a replay
reproduces the interval exactly instead of re-rolling it.
"""

import math

from pyto import Calculation

from stats.distributions import ppf as distribution_ppf

STATISTICS = ("mean", "median", "std", "var", "trimmed_mean", "sum", "min", "max")


def _sample(args, key="values", least=2):
    values = [float(v) for v in args[key]]
    if len(values) < least:
        raise ValueError("%s needs at least %d observations, got %d" % (key, least, len(values)))
    return values


def _level(args):
    level = float(args.get("level", 0.95))
    if not 0.0 < level < 1.0:
        raise ValueError("a confidence level is in (0, 1), got %r" % (level,))
    return level


def _mean(values):
    return math.fsum(values) / len(values)


def _var(values, ddof=1):
    centre = _mean(values)
    return math.fsum((v - centre) ** 2 for v in values) / (len(values) - ddof)


def _statistic(kind, values, trim=0.1):
    if kind == "mean":
        return _mean(values)
    if kind == "sum":
        return math.fsum(values)
    if kind == "min":
        return min(values)
    if kind == "max":
        return max(values)
    if kind == "median":
        ordered = sorted(values)
        half = len(ordered) // 2
        return ordered[half] if len(ordered) % 2 else (ordered[half - 1] + ordered[half]) / 2.0
    if kind == "trimmed_mean":
        ordered = sorted(values)
        cut = int(len(ordered) * trim)
        kept = ordered[cut:len(ordered) - cut] or ordered
        return math.fsum(kept) / len(kept)
    if len(values) < 2:
        return None
    variance = _var(values)
    return variance if kind == "var" else math.sqrt(variance)


def ci_mean(args):
    """the t interval for a mean. reference: scipy.stats.t.interval on the same sample."""
    values = _sample(args)
    level = _level(args)
    n = len(values)
    centre = _mean(values)
    spread = math.sqrt(_var(values) / n)
    critical = distribution_ppf({"dist": "t", "params": {"df": float(n - 1)},
                                 "q": 0.5 + level / 2.0})
    return {"estimate": centre, "low": centre - critical * spread,
            "high": centre + critical * spread, "level": level, "n": n,
            "standard_error": spread, "df": float(n - 1)}


def ci_diff_means(args):
    """welch's interval for a difference of means."""
    x = _sample(args, "x")
    y = _sample(args, "y")
    level = _level(args)
    a, b = _var(x) / len(x), _var(y) / len(y)
    spread = math.sqrt(a + b)
    if spread == 0.0:
        raise ValueError("a difference of means needs samples with spread")
    df = (a + b) ** 2 / (a * a / (len(x) - 1) + b * b / (len(y) - 1))
    centre = _mean(x) - _mean(y)
    critical = distribution_ppf({"dist": "t", "params": {"df": df}, "q": 0.5 + level / 2.0})
    return {"estimate": centre, "low": centre - critical * spread,
            "high": centre + critical * spread, "level": level,
            "standard_error": spread, "df": df}


def ci_proportion(args):
    """an interval for a proportion: wilson (default), or the wald normal approximation."""
    successes = int(args["successes"])
    n = int(args["n"])
    if n <= 0:
        raise ValueError("a proportion needs n > 0")
    if not 0 <= successes <= n:
        raise ValueError("successes must be between 0 and n")
    level = _level(args)
    method = args.get("method", "wilson")
    if method not in ("wilson", "wald"):
        raise ValueError("a proportion interval is wilson or wald, got %r" % (method,))
    z = distribution_ppf({"dist": "normal", "q": 0.5 + level / 2.0})
    p = successes / n
    if method == "wald":
        spread = z * math.sqrt(p * (1.0 - p) / n)
        return {"estimate": p, "low": max(0.0, p - spread), "high": min(1.0, p + spread),
                "level": level, "n": n, "method": method}
    denominator = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denominator
    return {"estimate": p, "low": max(0.0, centre - half), "high": min(1.0, centre + half),
            "level": level, "n": n, "method": method}


def ci_variance(args):
    """the chi-square interval for a variance."""
    values = _sample(args)
    level = _level(args)
    n = len(values)
    variance = _var(values)
    df = float(n - 1)
    lower = distribution_ppf({"dist": "chi2", "params": {"df": df}, "q": 0.5 + level / 2.0})
    upper = distribution_ppf({"dist": "chi2", "params": {"df": df}, "q": 0.5 - level / 2.0})
    return {"estimate": variance, "low": df * variance / lower, "high": df * variance / upper,
            "level": level, "n": n, "df": df}


def bootstrap(args):
    """a bootstrap interval for a statistic, resampling through the effects handle.

    ``method``: "percentile" (default) or "basic". ``resamples`` is how many.
    an ``oc.`` because every resample is a draw: the ledger carries them, so the
    same record replays to the same interval.
    """
    effects = args.get("effects")
    if effects is None:
        raise ValueError("oc.brain.stats.bootstrap needs the run's effects handle in args['effects']")
    values = _sample(args)
    kind = args.get("statistic", "mean")
    if kind not in STATISTICS:
        raise ValueError("unknown bootstrap statistic %r: one of %s" % (kind, ", ".join(STATISTICS)))
    resamples = int(args.get("resamples", 200))
    if resamples < 2:
        raise ValueError("a bootstrap needs at least 2 resamples")
    level = _level(args)
    method = args.get("method", "percentile")
    if method not in ("percentile", "basic"):
        raise ValueError("a bootstrap interval is percentile or basic, got %r" % (method,))
    trim = float(args.get("trim", 0.1))
    n = len(values)
    draws = effects.random(resamples * n)
    estimates = []
    for r in range(resamples):
        block = draws[r * n:(r + 1) * n]
        resample = [values[min(n - 1, int(u * n))] for u in block]
        estimates.append(_statistic(kind, resample, trim))
    estimates = [e for e in estimates if e is not None]
    if not estimates:
        raise ValueError("every resample came back empty-handed")
    estimates.sort()
    low_q, high_q = (1.0 - level) / 2.0, 0.5 + level / 2.0
    low = _quantile(estimates, low_q)
    high = _quantile(estimates, high_q)
    observed = _statistic(kind, values, trim)
    if method == "basic":
        low, high = 2.0 * observed - high, 2.0 * observed - low
    return {"statistic": kind, "estimate": observed, "low": low, "high": high,
            "level": level, "resamples": len(estimates), "method": method,
            "standard_error": math.sqrt(_var(estimates)) if len(estimates) > 1 else None}


def _quantile(ordered, q):
    place = (len(ordered) - 1) * q
    low = math.floor(place)
    high = math.ceil(place)
    if low == high:
        return ordered[int(place)]
    return ordered[low] * (high - place) + ordered[high] * (place - low)


def cohens_d(args):
    """the standardised difference of two means, pooled. reference: the textbook definition."""
    x = _sample(args, "x")
    y = _sample(args, "y")
    nx, ny = len(x), len(y)
    pooled = ((nx - 1) * _var(x) + (ny - 1) * _var(y)) / (nx + ny - 2)
    if pooled <= 0.0:
        raise ValueError("cohen's d needs samples with spread")
    return (_mean(x) - _mean(y)) / math.sqrt(pooled)


def hedges_g(args):
    """cohen's d with the small-sample correction J = 1 - 3/(4(n-2)-1)."""
    x = _sample(args, "x")
    y = _sample(args, "y")
    df = len(x) + len(y) - 2
    return cohens_d(args) * (1.0 - 3.0 / (4.0 * df - 1.0))


def glass_delta(args):
    """the difference of means in control standard deviations (y is the control)."""
    x = _sample(args, "x")
    y = _sample(args, "y")
    spread = math.sqrt(_var(y))
    if spread == 0.0:
        raise ValueError("glass's delta needs a control sample with spread")
    return (_mean(x) - _mean(y)) / spread


def eta_squared(args):
    """the share of variance between groups: SSB / SST."""
    groups = [[float(v) for v in group] for group in args["groups"]]
    if len(groups) < 2:
        raise ValueError("eta squared needs at least 2 groups")
    n = sum(len(g) for g in groups)
    grand = math.fsum(math.fsum(g) for g in groups) / n
    between = math.fsum(len(g) * (_mean(g) - grand) ** 2 for g in groups)
    total = math.fsum(math.fsum((v - grand) ** 2 for v in g) for g in groups)
    if total == 0.0:
        raise ValueError("eta squared needs variation somewhere")
    return between / total


def omega_squared(args):
    """the less biased share of variance between groups."""
    groups = [[float(v) for v in group] for group in args["groups"]]
    if len(groups) < 2:
        raise ValueError("omega squared needs at least 2 groups")
    n = sum(len(g) for g in groups)
    grand = math.fsum(math.fsum(g) for g in groups) / n
    between = math.fsum(len(g) * (_mean(g) - grand) ** 2 for g in groups)
    centres = [_mean(g) for g in groups]
    within = math.fsum(math.fsum((v - centre) ** 2 for v in g)
                       for g, centre in zip(groups, centres))
    df_between = len(groups) - 1
    df_within = n - len(groups)
    if df_within <= 0:
        raise ValueError("omega squared needs more observations than groups")
    mean_within = within / df_within
    total = between + within
    denominator = total + mean_within
    if denominator == 0.0:
        raise ValueError("omega squared needs variation somewhere")
    return (between - df_between * mean_within) / denominator


def cramers_v(args):
    """the association in a contingency table, 0 to 1. reference: the chi-square statistic."""
    from stats.hypothesis import chi2_contingency

    table = args["table"]
    verdict = chi2_contingency({"table": table, "correction": False,
                                "backend": args.get("backend", "py")})
    total = math.fsum(math.fsum(float(v) for v in row) for row in table)
    smallest = min(len(table), len(table[0])) - 1
    if total == 0.0 or smallest <= 0:
        raise ValueError("cramer's v needs a table with counts and at least 2x2")
    return math.sqrt(verdict["statistic"] / (total * smallest))


def rank_biserial(args):
    """the rank-biserial correlation from the mann-whitney u: 1 - 2U/(n1 n2)."""
    from stats.hypothesis import mannwhitneyu

    x = _sample(args, "x", least=1)
    y = _sample(args, "y", least=1)
    verdict = mannwhitneyu({"x": x, "y": y, "backend": args.get("backend", "py")})
    return 2.0 * verdict["statistic"] / (len(x) * len(y)) - 1.0


CI_MEAN = Calculation("fn.brain.stats.ci_mean", ci_mean)
CI_DIFF_MEANS = Calculation("fn.brain.stats.ci_diff_means", ci_diff_means)
CI_PROPORTION = Calculation("fn.brain.stats.ci_proportion", ci_proportion)
CI_VARIANCE = Calculation("fn.brain.stats.ci_variance", ci_variance)
BOOTSTRAP = Calculation("oc.brain.stats.bootstrap", bootstrap)
COHENS_D = Calculation("fn.brain.stats.cohens_d", cohens_d)
HEDGES_G = Calculation("fn.brain.stats.hedges_g", hedges_g)
GLASS_DELTA = Calculation("fn.brain.stats.glass_delta", glass_delta)
ETA_SQUARED = Calculation("fn.brain.stats.eta_squared", eta_squared)
OMEGA_SQUARED = Calculation("fn.brain.stats.omega_squared", omega_squared)
CRAMERS_V = Calculation("fn.brain.stats.cramers_v", cramers_v)
RANK_BISERIAL = Calculation("fn.brain.stats.rank_biserial", rank_biserial)

CALCS = {
    c.address: c
    for c in (CI_MEAN, CI_DIFF_MEANS, CI_PROPORTION, CI_VARIANCE, BOOTSTRAP,
              COHENS_D, HEDGES_G, GLASS_DELTA, ETA_SQUARED, OMEGA_SQUARED,
              CRAMERS_V, RANK_BISERIAL)
}
