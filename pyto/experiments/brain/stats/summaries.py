"""the robust summaries: what you reach for when the mean is the wrong answer.

trimmed and winsorised samples, the median absolute deviation, the geometric and
harmonic means, shannon entropy and a histogram. "py" is the pure statement,
"sp"/"np" is the library, and scipy is the named authority for every one.
"""

import math

from pyto import Calculation


def _backend(args, allowed=("py", "sp")):
    backend = args.get("backend", "py")
    if backend not in allowed:
        raise ValueError("unknown backend %r for a summary: %s"
                         % (backend, " or ".join(allowed)))
    return backend


def _sample(args, key="values", least=1):
    values = [float(v) for v in args[key]]
    if len(values) < least:
        raise ValueError("%s needs at least %d observations, got %d" % (key, least, len(values)))
    return values


def _proportion(args, key="proportiontocut", default=0.1):
    cut = float(args.get(key, default))
    if not 0.0 <= cut < 0.5:
        raise ValueError("%s must be in [0, 0.5), got %r" % (key, cut))
    return cut


def trimmed_mean(args):
    """the mean of the sample with ``proportiontocut`` cut off each end.

    reference: scipy.stats.trim_mean, which cuts ``int(n * cut)`` from each end.
    """
    values = _sample(args)
    cut = _proportion(args)
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        return float(sp_stats.trim_mean(values, cut))
    ordered = sorted(values)
    drop = int(len(ordered) * cut)
    kept = ordered[drop:len(ordered) - drop]
    if not kept:
        raise ValueError("trimming %g from each end of %d values leaves nothing"
                         % (cut, len(values)))
    return math.fsum(kept) / len(kept)


def winsorize(args):
    """the sample with its tails pulled in to the cut points, in the original order.

    reference: scipy.stats.mstats.winsorize.
    """
    values = _sample(args)
    lower = _proportion(args, "limits_low", float(args.get("limits", 0.1)))
    upper = _proportion(args, "limits_high", float(args.get("limits", 0.1)))
    if _backend(args) == "sp":
        import numpy as np
        from scipy.stats import mstats

        return [float(v) for v in mstats.winsorize(np.asarray(values, dtype=float),
                                                   limits=(lower, upper))]
    ordered = sorted(values)
    n = len(ordered)
    low_at = int(n * lower)
    high_at = n - int(n * upper) - 1
    if low_at > high_at:
        raise ValueError("those limits leave nothing between them")
    floor, ceiling = ordered[low_at], ordered[high_at]
    return [min(max(v, floor), ceiling) for v in values]


def median_abs_deviation(args):
    """the median of |x - median(x)|, scaled by ``scale`` (1.0, or "normal" = 1/0.6744898).

    reference: scipy.stats.median_abs_deviation.
    """
    values = _sample(args)
    scale = args.get("scale", 1.0)
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        return float(sp_stats.median_abs_deviation(values, scale=scale))
    middle = _median(values)
    deviation = _median([abs(v - middle) for v in values])
    if scale == "normal":
        return deviation / 0.6744897501960817
    return deviation / float(scale)


def _median(values):
    ordered = sorted(values)
    half = len(ordered) // 2
    return ordered[half] if len(ordered) % 2 else (ordered[half - 1] + ordered[half]) / 2.0


def gmean(args):
    """the geometric mean; every value must be positive. reference: scipy.stats.gmean."""
    values = _sample(args)
    if any(v <= 0.0 for v in values):
        raise ValueError("a geometric mean needs every value to be positive")
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        return float(sp_stats.gmean(values))
    return math.exp(math.fsum(math.log(v) for v in values) / len(values))


def hmean(args):
    """the harmonic mean; every value must be positive. reference: scipy.stats.hmean."""
    values = _sample(args)
    if any(v <= 0.0 for v in values):
        raise ValueError("a harmonic mean needs every value to be positive")
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        return float(sp_stats.hmean(values))
    return len(values) / math.fsum(1.0 / v for v in values)


def entropy(args):
    """shannon entropy of a distribution, or the kullback-leibler divergence against ``qk``.

    the counts are normalised first. ``base`` defaults to e.
    reference: scipy.stats.entropy.
    """
    counts = _sample(args, "values")
    if any(v < 0.0 for v in counts):
        raise ValueError("an entropy needs non-negative weights")
    total = math.fsum(counts)
    if total <= 0.0:
        raise ValueError("an entropy needs some weight somewhere")
    other = args.get("qk")
    base = args.get("base")
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        return float(sp_stats.entropy(counts, other, base=base) if other is not None
                     else sp_stats.entropy(counts, base=base))
    p = [v / total for v in counts]
    if other is None:
        value = -math.fsum(one * math.log(one) for one in p if one > 0.0)
    else:
        q = [float(v) for v in other]
        if len(q) != len(p):
            raise ValueError("the two distributions must be the same length")
        if any(v < 0.0 for v in q):
            raise ValueError("a divergence needs non-negative weights")
        q_total = math.fsum(q)
        if q_total <= 0.0:
            raise ValueError("the second distribution has no weight in it")
        q = [v / q_total for v in q]
        value = 0.0
        for one, two in zip(p, q):
            if one == 0.0:
                continue
            if two == 0.0:
                return float("inf")
            value += one * math.log(one / two)
    return value / math.log(base) if base else value


def histogram(args):
    """counts per bin over ``bins`` equal-width bins, with the edges.

    reference: numpy.histogram. returns ``{"counts", "edges", "density"}``.
    """
    values = _sample(args)
    bins = int(args.get("bins", 10))
    if bins < 1:
        raise ValueError("a histogram needs at least one bin")
    low = float(args["range"][0]) if args.get("range") else min(values)
    high = float(args["range"][1]) if args.get("range") else max(values)
    if high <= low:
        high = low + 1.0
    backend = _backend(args, ("py", "np"))
    if backend == "np":
        import numpy as np

        counts, edges = np.histogram(values, bins=bins, range=(low, high))
        counts = [int(c) for c in counts]
        edges = [float(e) for e in edges]
    else:
        width = (high - low) / bins
        edges = [low + width * i for i in range(bins)] + [high]
        counts = [0] * bins
        for value in values:
            if value < low or value > high:
                continue
            place = int((value - low) / width)
            counts[min(place, bins - 1)] += 1
    total = sum(counts)
    widths = [edges[i + 1] - edges[i] for i in range(bins)]
    density = [(c / total / w) if total and w else 0.0 for c, w in zip(counts, widths)]
    return {"counts": counts, "edges": edges, "density": density}


TRIMMED_MEAN = Calculation("fn.brain.stats.trimmed_mean", trimmed_mean)
WINSORIZE = Calculation("fn.brain.stats.winsorize", winsorize)
MEDIAN_ABS_DEVIATION = Calculation("fn.brain.stats.median_abs_deviation", median_abs_deviation)
GMEAN = Calculation("fn.brain.stats.gmean", gmean)
HMEAN = Calculation("fn.brain.stats.hmean", hmean)
ENTROPY = Calculation("fn.brain.stats.entropy", entropy)
HISTOGRAM = Calculation("fn.brain.stats.histogram", histogram)

CALCS = {c.address: c for c in (TRIMMED_MEAN, WINSORIZE, MEDIAN_ABS_DEVIATION, GMEAN,
                                HMEAN, ENTROPY, HISTOGRAM)}
