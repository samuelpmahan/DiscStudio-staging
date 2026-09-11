"""the distribution-free tests: kolmogorov-smirnov, wilcoxon signed-rank, and the
p-value that belongs beside a pearson correlation.

same rule as the rest of the vertical: "py" is the pure-python reference
statement of the formula, "sp" is scipy, and both answer to the same oracle. the
p-values here are the asymptotic ones (scipy's ``method="asymp"`` /
``method="approx"``), because the exact small-sample nulls are their own
combinatorial tables and are named as stubs on the map.
"""

import math

from pyto import Calculation

from stats.distributions import _cdf_py
from stats.special import ndtr


def _backend(args):
    backend = args.get("backend", "py")
    if backend not in ("py", "sp"):
        raise ValueError("unknown backend %r for a distribution-free test: py or sp" % (backend,))
    return backend


def _alternative(args, allowed=("two-sided", "less", "greater")):
    alternative = args.get("alternative", "two-sided")
    if alternative not in allowed:
        raise ValueError("alternative must be one of %s, got %r" % (allowed, alternative))
    return alternative


def _sample(args, key, least=1):
    values = [float(v) for v in args[key]]
    if len(values) < least:
        raise ValueError("%s needs at least %d observations, got %d" % (key, least, len(values)))
    return values


def kolmogorov_sf(x):
    """the limiting kolmogorov distribution's upper tail. reference: scipy.stats.kstwobign.sf.

    Q(x) = 2 sum_{k>=1} (-1)^(k-1) exp(-2 k^2 x^2), summed until the terms vanish.
    """
    if x <= 0.0:
        return 1.0
    if x < 0.04:
        return 1.0
    total = 0.0
    for k in range(1, 200):
        term = (-1.0) ** (k - 1) * math.exp(-2.0 * k * k * x * x)
        total += term
        if abs(term) < 1e-18:
            break
    return max(0.0, min(1.0, 2.0 * total))


def ksone_sf(d, n):
    """the exact one-sided one-sample KS tail (birnbaum-tingey). reference: scipy.stats.ksone.sf.

    Q = d * sum_{j=0}^{floor(n(1-d))} C(n, j) (d + j/n)^(j-1) (1 - d - j/n)^(n-j),
    summed in logs so the binomial coefficient cannot overflow.
    """
    if d <= 0.0:
        return 1.0
    if d >= 1.0:
        return 0.0
    total = 0.0
    top = int(math.floor(n * (1.0 - d)))
    for j in range(0, top + 1):
        left = d + j / float(n)
        right = 1.0 - d - j / float(n)
        if right < 0.0:
            continue
        log = math.lgamma(n + 1) - math.lgamma(j + 1) - math.lgamma(n - j + 1)
        if j == 0:
            term = math.exp(log + (n - j) * math.log(right) if right > 0.0 else -1e308) / left
        else:
            if left <= 0.0:
                continue
            log += (j - 1) * math.log(left)
            log += (n - j) * math.log(right) if right > 0.0 else -1e308
            term = math.exp(log)
        total += term
    return max(0.0, min(1.0, d * total))


def hodges_sf(d, n1, n2):
    """the one-sided two-sample KS tail, hodges' approximation. reference: scipy.stats.ks_2samp."""
    larger, smaller = max(n1, n2), min(n1, n2)
    en = larger * smaller / float(larger + smaller)
    z = math.sqrt(en) * d
    exponent = (-2.0 * z * z
                - 2.0 * z * (larger + 2.0 * smaller)
                / math.sqrt(larger * smaller * (larger + smaller)) / 3.0)
    return max(0.0, min(1.0, math.exp(exponent)))


def _ecdf_gap(values, cdf_at):
    """the two one-sided KS distances of a sorted sample against a cdf."""
    n = len(values)
    ordered = sorted(values)
    plus = minus = 0.0
    for i, value in enumerate(ordered):
        theory = cdf_at(value)
        plus = max(plus, (i + 1) / n - theory)
        minus = max(minus, theory - i / n)
    return plus, minus


def ks_1samp(args):
    """the one-sample kolmogorov-smirnov test against a named distribution.

    reference: scipy.stats.kstest(..., method="asymp"). ``dist`` and ``params``
    are the distribution facade's own, so the null is a Part like any other.
    """
    values = _sample(args, "values", least=2)
    dist = args.get("dist", "normal")
    params = dict(args.get("params") or {})
    alternative = _alternative(args)
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        from stats.distributions import _params, _scipy

        frozen = _scipy(dist, _params(dist, params))
        out = sp_stats.kstest(values, frozen.cdf, alternative=alternative, method="asymp")
        return {"statistic": float(out.statistic), "pvalue": float(out.pvalue),
                "n": len(values), "alternative": alternative}
    from stats.distributions import _params

    checked = _params(dist, params)
    plus, minus = _ecdf_gap(values, lambda v: _cdf_py(dist, checked, v))
    n = len(values)
    if alternative == "two-sided":
        statistic = max(plus, minus)
        pvalue = kolmogorov_sf(math.sqrt(n) * statistic)
    else:
        statistic = plus if alternative == "greater" else minus
        pvalue = ksone_sf(statistic, n)
    return {"statistic": statistic, "pvalue": max(0.0, min(1.0, pvalue)),
            "n": n, "alternative": alternative}


def ks_2samp(args):
    """the two-sample kolmogorov-smirnov test, asymptotic tails.

    the statistic is scipy's own. the two-sided p-value is the LIMITING
    kolmogorov tail (``scipy.stats.kstwobign.sf``), not scipy's
    ``ks_2samp(method="asymp")``, which quietly evaluates the exact two-sided
    distribution at an effective sample size: that exact tail is its own
    algorithm and is a stub on the map. both backends here compute the same
    limiting tail, so they agree by construction. the one-sided tail is hodges'
    approximation, which is exactly what scipy's asymptotic path uses.
    """
    x = _sample(args, "x", least=2)
    y = _sample(args, "y", least=2)
    alternative = _alternative(args)
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.ks_2samp(x, y, alternative=alternative, method="asymp")
        statistic = float(out.statistic)
        if alternative == "two-sided":
            root = math.sqrt(len(x) * len(y) / float(len(x) + len(y)))
            pvalue = float(sp_stats.kstwobign.sf(root * statistic))
        else:
            pvalue = float(out.pvalue)
        return {"statistic": statistic, "pvalue": max(0.0, min(1.0, pvalue)),
                "n1": len(x), "n2": len(y), "alternative": alternative}
    n1, n2 = len(x), len(y)
    ordered_x = sorted(x)
    ordered_y = sorted(y)
    everything = sorted(set(ordered_x) | set(ordered_y))
    plus = minus = 0.0
    for value in everything:
        left = _share_at_or_below(ordered_x, value) / n1
        right = _share_at_or_below(ordered_y, value) / n2
        plus = max(plus, left - right)
        minus = max(minus, right - left)
    root = math.sqrt(n1 * n2 / float(n1 + n2))
    if alternative == "two-sided":
        statistic = max(plus, minus)
        pvalue = kolmogorov_sf(root * statistic)
    else:
        statistic = plus if alternative == "greater" else minus
        pvalue = hodges_sf(statistic, n1, n2)
    return {"statistic": statistic, "pvalue": max(0.0, min(1.0, pvalue)),
            "n1": n1, "n2": n2, "alternative": alternative}


def _share_at_or_below(ordered, value):
    low, high = 0, len(ordered)
    while low < high:
        middle = (low + high) // 2
        if ordered[middle] <= value:
            low = middle + 1
        else:
            high = middle
    return float(low)


def wilcoxon(args):
    """the wilcoxon signed-rank test, normal approximation.

    reference: scipy.stats.wilcoxon(..., method="approx", zero_method="wilcox").
    one sample against ``popmean`` (default 0) or two paired samples in ``x``
    and ``y``. zeros are dropped, ties share their mean rank and the variance is
    corrected for both.
    """
    if "y" in args and args["y"] is not None:
        x = _sample(args, "x")
        y = _sample(args, "y")
        if len(x) != len(y):
            raise ValueError("a signed-rank test needs equal lengths, got %d and %d"
                             % (len(x), len(y)))
        differences = [a - b for a, b in zip(x, y)]
    else:
        differences = [v - float(args.get("popmean", 0.0)) for v in _sample(args, "values")]
    alternative = _alternative(args)
    correction = bool(args.get("correction", False))
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.wilcoxon(differences, alternative=alternative, method="approx",
                                correction=correction, zero_method="wilcox")
        return {"statistic": float(out.statistic), "pvalue": float(out.pvalue),
                "n": int(sum(1 for d in differences if d != 0.0)),
                "alternative": alternative}
    kept = [d for d in differences if d != 0.0]
    n = len(kept)
    if n == 0:
        raise ValueError("a signed-rank test needs at least one non-zero difference")
    ranks, ties = _ranks([abs(d) for d in kept])
    r_plus = math.fsum(rank for rank, d in zip(ranks, kept) if d > 0.0)
    r_minus = math.fsum(rank for rank, d in zip(ranks, kept) if d < 0.0)
    if alternative == "two-sided":
        statistic = min(r_plus, r_minus)
    elif alternative == "greater":
        statistic = r_plus
    else:
        statistic = r_plus
    centre = n * (n + 1) / 4.0
    tie_term = math.fsum(t ** 3 - t for t in ties)
    spread = math.sqrt(n * (n + 1) * (2 * n + 1) / 24.0 - tie_term / 48.0)
    if spread == 0.0:
        raise ValueError("a signed-rank test needs some variation in the differences")
    if alternative == "two-sided":
        numerator = statistic - centre
        if correction:
            numerator = numerator + 0.5 * (1 if numerator < 0 else -1)
        pvalue = min(1.0, 2.0 * (1.0 - ndtr(abs(numerator) / spread)))
    else:
        numerator = r_plus - centre
        if correction:
            numerator -= 0.5 if alternative == "greater" else -0.5
        z = numerator / spread
        pvalue = 1.0 - ndtr(z) if alternative == "greater" else ndtr(z)
    return {"statistic": float(statistic), "pvalue": max(0.0, min(1.0, pvalue)),
            "n": n, "alternative": alternative}


def _ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    ties = []
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        shared = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = shared
        ties.append(j - i + 1)
        i = j + 1
    return ranks, ties


def pearson_p(args):
    """the pearson correlation with the t-based p-value beside it.

    reference: scipy.stats.pearsonr. the coefficient alone is
    ``fn.brain.stats.pearson``; this is the one that answers "and is it real".
    """
    from stats.correlation import pearson

    x = _sample(args, "x", least=3)
    y = _sample(args, "y", least=3)
    if len(x) != len(y):
        raise ValueError("x and y must be the same length, got %d and %d" % (len(x), len(y)))
    alternative = _alternative(args)
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.pearsonr(x, y, alternative=alternative)
        return {"r": float(out.statistic), "pvalue": float(out.pvalue),
                "n": len(x), "df": float(len(x) - 2), "alternative": alternative}
    r = pearson({"x": x, "y": y, "backend": "py"})
    n = len(x)
    df = float(n - 2)
    if abs(r) >= 1.0:
        return {"r": r, "pvalue": 0.0, "n": n, "df": df, "alternative": alternative}
    statistic = r * math.sqrt(df / (1.0 - r * r))
    cdf = _cdf_py("t", {"df": df}, statistic)
    if alternative == "less":
        pvalue = cdf
    elif alternative == "greater":
        pvalue = 1.0 - cdf
    else:
        pvalue = 2.0 * min(cdf, 1.0 - cdf)
    return {"r": r, "pvalue": max(0.0, min(1.0, pvalue)), "n": n, "df": df,
            "alternative": alternative}


KS_1SAMP = Calculation("fn.brain.stats.ks_1samp", ks_1samp)
KS_2SAMP = Calculation("fn.brain.stats.ks_2samp", ks_2samp)
WILCOXON = Calculation("fn.brain.stats.wilcoxon", wilcoxon)
PEARSON_P = Calculation("fn.brain.stats.pearson_p", pearson_p)

CALCS = {c.address: c for c in (KS_1SAMP, KS_2SAMP, WILCOXON, PEARSON_P)}
