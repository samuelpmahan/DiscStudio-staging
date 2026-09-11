"""the rest of the comparison toolbox: rank anova, spread tests, exact counts,
and what to do once you have run more than one test.

as everywhere in this vertical, "py" is the pure-python statement of the
definition and "sp" is scipy, and both answer to the same oracle.
"""

import math

from pyto import Calculation

from stats.distributions import _cdf_py
from stats.hypothesis import _f_sf, _ranks

METHODS = ("bonferroni", "holm", "benjamini-hochberg")


def _backend(args):
    backend = args.get("backend", "py")
    if backend not in ("py", "sp"):
        raise ValueError("unknown backend %r for a comparison: py or sp" % (backend,))
    return backend


def _groups(args, least_per_group=1):
    groups = [[float(v) for v in group] for group in args["groups"]]
    if len(groups) < 2:
        raise ValueError("this test needs at least 2 groups, got %d" % len(groups))
    for index, group in enumerate(groups):
        if len(group) < least_per_group:
            raise ValueError("group %d needs at least %d observation(s), got %d"
                             % (index, least_per_group, len(group)))
    return groups


def _chi2_sf(statistic, df):
    return 1.0 - _cdf_py("chi2", {"df": float(df)}, statistic)


def kruskal(args):
    """the kruskal-wallis H test: a one-way anova on ranks. reference: scipy.stats.kruskal."""
    groups = _groups(args)
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.kruskal(*groups)
        return {"statistic": float(out.statistic), "pvalue": float(out.pvalue),
                "df": float(len(groups) - 1)}
    everything = [v for group in groups for v in group]
    n = len(everything)
    if n < 3:
        raise ValueError("a kruskal-wallis test needs at least 3 observations in total")
    ranks, ties = _ranks(everything)
    at = 0
    total = 0.0
    for group in groups:
        block = ranks[at:at + len(group)]
        at += len(group)
        total += math.fsum(block) ** 2 / len(group)
    statistic = 12.0 / (n * (n + 1.0)) * total - 3.0 * (n + 1.0)
    tie_term = math.fsum(t ** 3 - t for t in ties)
    correction = 1.0 - tie_term / (n ** 3 - n) if n > 1 else 1.0
    if correction == 0.0:
        raise ValueError("a kruskal-wallis test needs more than one distinct value")
    statistic /= correction
    df = float(len(groups) - 1)
    return {"statistic": statistic, "pvalue": _chi2_sf(statistic, df), "df": df}


def levene(args):
    """levene's test of equal variances, centred on the median by default.

    reference: scipy.stats.levene (``center`` is "median", "mean" or "trimmed").
    """
    groups = _groups(args, least_per_group=2)
    center = args.get("center", "median")
    if center not in ("median", "mean"):
        raise ValueError("levene's center must be median or mean, got %r" % (center,))
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.levene(*groups, center=center)
        n = sum(len(g) for g in groups)
        return {"statistic": float(out.statistic), "pvalue": float(out.pvalue),
                "df_between": float(len(groups) - 1), "df_within": float(n - len(groups))}
    spreads = []
    for group in groups:
        middle = _median(group) if center == "median" else math.fsum(group) / len(group)
        spreads.append([abs(v - middle) for v in group])
    n = sum(len(group) for group in spreads)
    grand = math.fsum(math.fsum(group) for group in spreads) / n
    between = math.fsum(len(group) * (math.fsum(group) / len(group) - grand) ** 2
                        for group in spreads)
    centres = [math.fsum(group) / len(group) for group in spreads]
    within = math.fsum(math.fsum((v - centre) ** 2 for v in group)
                       for group, centre in zip(spreads, centres))
    df_between = float(len(groups) - 1)
    df_within = float(n - len(groups))
    if within == 0.0:
        raise ValueError("levene's test needs some spread inside the groups")
    statistic = (between / df_between) / (within / df_within)
    return {"statistic": statistic, "pvalue": _f_sf(statistic, df_between, df_within),
            "df_between": df_between, "df_within": df_within}


def _median(values):
    ordered = sorted(values)
    half = len(ordered) // 2
    return ordered[half] if len(ordered) % 2 else (ordered[half - 1] + ordered[half]) / 2.0


def bartlett(args):
    """bartlett's test of equal variances, which assumes normality. reference: scipy.stats.bartlett."""
    groups = _groups(args, least_per_group=2)
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.bartlett(*groups)
        return {"statistic": float(out.statistic), "pvalue": float(out.pvalue),
                "df": float(len(groups) - 1)}
    n = sum(len(group) for group in groups)
    k = len(groups)
    variances = []
    for group in groups:
        centre = math.fsum(group) / len(group)
        variances.append(math.fsum((v - centre) ** 2 for v in group) / (len(group) - 1))
    if any(v <= 0.0 for v in variances):
        raise ValueError("bartlett's test needs every group to have spread")
    pooled = math.fsum((len(group) - 1) * variance
                       for group, variance in zip(groups, variances)) / (n - k)
    top = (n - k) * math.log(pooled) - math.fsum(
        (len(group) - 1) * math.log(variance)
        for group, variance in zip(groups, variances))
    bottom = 1.0 + (math.fsum(1.0 / (len(group) - 1) for group in groups)
                    - 1.0 / (n - k)) / (3.0 * (k - 1))
    statistic = top / bottom
    df = float(k - 1)
    return {"statistic": statistic, "pvalue": _chi2_sf(statistic, df), "df": df}


def binom_test(args):
    """the exact binomial test of a proportion. reference: scipy.stats.binomtest."""
    successes = int(args["successes"])
    n = int(args["n"])
    p = float(args.get("p", 0.5))
    alternative = args.get("alternative", "two-sided")
    if alternative not in ("two-sided", "less", "greater"):
        raise ValueError("alternative must be two-sided, less or greater, got %r" % (alternative,))
    if n <= 0:
        raise ValueError("a binomial test needs n > 0")
    if not 0 <= successes <= n:
        raise ValueError("successes must be between 0 and n")
    if not 0.0 <= p <= 1.0:
        raise ValueError("a binomial test needs p in [0, 1]")
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.binomtest(successes, n, p, alternative=alternative)
        return {"statistic": successes / n, "pvalue": float(out.pvalue), "n": n}
    mass = [_binom_pmf(k, n, p) for k in range(n + 1)]
    if alternative == "less":
        pvalue = math.fsum(mass[:successes + 1])
    elif alternative == "greater":
        pvalue = math.fsum(mass[successes:])
    else:
        observed = mass[successes]
        # the same rule scipy uses: every outcome no more likely than the one seen,
        # with a relative slack so floating point does not drop a tied tail.
        pvalue = math.fsum(m for m in mass if m <= observed * (1.0 + 1e-7))
    return {"statistic": successes / n, "pvalue": max(0.0, min(1.0, pvalue)), "n": n}


def _binom_pmf(k, n, p):
    if p == 0.0:
        return 1.0 if k == 0 else 0.0
    if p == 1.0:
        return 1.0 if k == n else 0.0
    log = (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
           + k * math.log(p) + (n - k) * math.log1p(-p))
    return math.exp(log)


def fisher_exact(args):
    """fisher's exact test on a 2x2 table. reference: scipy.stats.fisher_exact.

    the two-sided p-value is the sum of every table, with the same margins, whose
    hypergeometric probability is no greater than the observed one.
    """
    table = [[float(v) for v in row] for row in args["table"]]
    if len(table) != 2 or len(table[0]) != 2 or len(table[1]) != 2:
        raise ValueError("fisher's exact test is a 2x2 test; got a %dx%d table"
                         % (len(table), len(table[0])))
    alternative = args.get("alternative", "two-sided")
    if alternative not in ("two-sided", "less", "greater"):
        raise ValueError("alternative must be two-sided, less or greater, got %r" % (alternative,))
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.fisher_exact(table, alternative=alternative)
        return {"odds_ratio": float(out.statistic), "pvalue": float(out.pvalue),
                "total": int(sum(sum(row) for row in table))}
    a, b = int(table[0][0]), int(table[0][1])
    c, d = int(table[1][0]), int(table[1][1])
    row1, row2 = a + b, c + d
    col1 = a + c
    total = row1 + row2
    low = max(0, col1 - row2)
    high = min(row1, col1)
    mass = {k: _hypergeom_pmf(k, row1, row2, col1) for k in range(low, high + 1)}
    if alternative == "less":
        pvalue = math.fsum(mass[k] for k in range(low, a + 1))
    elif alternative == "greater":
        pvalue = math.fsum(mass[k] for k in range(a, high + 1))
    else:
        observed = mass[a]
        pvalue = math.fsum(m for m in mass.values() if m <= observed * (1.0 + 1e-7))
    odds = float("inf") if (b == 0 or c == 0) else (a * d) / float(b * c)
    if a == 0 or d == 0:
        odds = 0.0 if (b and c) else odds
    return {"odds_ratio": odds, "pvalue": max(0.0, min(1.0, pvalue)), "total": total}


def _hypergeom_pmf(k, row1, row2, col1):
    def log_choose(n, r):
        if r < 0 or r > n:
            return float("-inf")
        return math.lgamma(n + 1) - math.lgamma(r + 1) - math.lgamma(n - r + 1)

    log = (log_choose(row1, k) + log_choose(row2, col1 - k)
           - log_choose(row1 + row2, col1))
    return math.exp(log) if log > -700 else 0.0


def multipletests(args):
    """adjust a family of p-values. reference: the published definitions, and
    ``scipy.stats.false_discovery_control`` for benjamini-hochberg.

    returns ``{"method", "alpha", "pvalues", "adjusted", "rejected", "rejections"}``.
    """
    pvalues = [float(v) for v in args["pvalues"]]
    if not pvalues:
        raise ValueError("there is nothing to correct: no p-values")
    if any(not 0.0 <= p <= 1.0 for p in pvalues):
        raise ValueError("every p-value must be in [0, 1]")
    method = args.get("method", "benjamini-hochberg")
    if method not in METHODS:
        raise ValueError("unknown correction %r: one of %s" % (method, ", ".join(METHODS)))
    alpha = float(args.get("alpha", 0.05))
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha is in (0, 1), got %r" % (alpha,))
    _backend(args)
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0] * m
    if method == "bonferroni":
        for i in range(m):
            adjusted[i] = min(1.0, pvalues[i] * m)
    elif method == "holm":
        running = 0.0
        for place, i in enumerate(order):
            running = max(running, (m - place) * pvalues[i])
            adjusted[i] = min(1.0, running)
    else:
        running = 1.0
        for place in range(m - 1, -1, -1):
            i = order[place]
            running = min(running, pvalues[i] * m / (place + 1.0))
            adjusted[i] = min(1.0, running)
    rejected = [value <= alpha for value in adjusted]
    return {"method": method, "alpha": alpha, "pvalues": pvalues, "adjusted": adjusted,
            "rejected": rejected, "rejections": sum(1 for one in rejected if one)}


KRUSKAL = Calculation("fn.brain.stats.kruskal", kruskal)
LEVENE = Calculation("fn.brain.stats.levene", levene)
BARTLETT = Calculation("fn.brain.stats.bartlett", bartlett)
BINOM_TEST = Calculation("fn.brain.stats.binom_test", binom_test)
FISHER_EXACT = Calculation("fn.brain.stats.fisher_exact", fisher_exact)
MULTIPLETESTS = Calculation("fn.brain.stats.multipletests", multipletests)

CALCS = {c.address: c for c in (KRUSKAL, LEVENE, BARTLETT, BINOM_TEST, FISHER_EXACT,
                                MULTIPLETESTS)}
