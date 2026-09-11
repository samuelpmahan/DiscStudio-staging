"""hypothesis tests, each returning a json-able verdict.

every test returns at least ``{"statistic", "pvalue"}`` and adds the degrees of
freedom it used where it has any. ``args["backend"]`` is "py" (pure python on
``stats.special``, the reference statement of each formula) or "sp"
(scipy.stats). the p-value is always computed from the same null distribution on
both paths, so a backend that disagrees is a bug and the oracle Parts say so.

``alternative`` is "two-sided" (default), "less" or "greater", following scipy.
"""

import math

from pyto import Calculation

from stats.distributions import _cdf_py
from stats.special import betainc, ndtr, ndtri

ALTERNATIVES = ("two-sided", "less", "greater")


def _backend(args):
    backend = args.get("backend", "py")
    if backend not in ("py", "sp"):
        raise ValueError("unknown backend %r for a hypothesis test: py or sp" % (backend,))
    return backend


def _alternative(args):
    alternative = args.get("alternative", "two-sided")
    if alternative not in ALTERNATIVES:
        raise ValueError("alternative must be one of %s, got %r" % (ALTERNATIVES, alternative))
    return alternative


def _sample(args, key, least=2):
    values = [float(v) for v in args[key]]
    if len(values) < least:
        raise ValueError("%s needs at least %d observations, got %d" % (key, least, len(values)))
    return values


def _mean(values):
    return math.fsum(values) / len(values)


def _var(values, ddof=1):
    centre = _mean(values)
    return math.fsum((v - centre) ** 2 for v in values) / (len(values) - ddof)


def _t_pvalue(statistic, df, alternative):
    cdf = _cdf_py("t", {"df": df}, statistic)
    if alternative == "less":
        return cdf
    if alternative == "greater":
        return 1.0 - cdf
    return 2.0 * min(cdf, 1.0 - cdf)


def _f_sf(statistic, df1, df2):
    """the upper tail of the f distribution, from the regularised incomplete beta."""
    if statistic <= 0.0:
        return 1.0
    x = df2 / (df2 + df1 * statistic)
    return betainc(df2 / 2.0, df1 / 2.0, x)


def _chi2_sf(statistic, df):
    return 1.0 - _cdf_py("chi2", {"df": float(df)}, statistic)


def ttest_1samp(args):
    """one-sample t test of the mean against ``popmean``. reference: scipy.stats.ttest_1samp."""
    values = _sample(args, "values")
    popmean = float(args.get("popmean", 0.0))
    alternative = _alternative(args)
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.ttest_1samp(values, popmean, alternative=alternative)
        return {"statistic": float(out.statistic), "pvalue": float(out.pvalue),
                "df": float(len(values) - 1)}
    n = len(values)
    spread = math.sqrt(_var(values) / n)
    if spread == 0.0:
        raise ValueError("a one-sample t test needs a sample with spread")
    statistic = (_mean(values) - popmean) / spread
    df = float(n - 1)
    return {"statistic": statistic, "pvalue": _t_pvalue(statistic, df, alternative), "df": df}


def ttest_ind(args):
    """two-sample t test; ``equal_var=False`` is welch's. reference: scipy.stats.ttest_ind."""
    x = _sample(args, "x")
    y = _sample(args, "y")
    equal_var = bool(args.get("equal_var", True))
    alternative = _alternative(args)
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.ttest_ind(x, y, equal_var=equal_var, alternative=alternative)
        return {"statistic": float(out.statistic), "pvalue": float(out.pvalue),
                "df": float(out.df)}
    nx, ny = len(x), len(y)
    vx, vy = _var(x), _var(y)
    if equal_var:
        df = float(nx + ny - 2)
        pooled = ((nx - 1) * vx + (ny - 1) * vy) / df
        spread = math.sqrt(pooled * (1.0 / nx + 1.0 / ny))
    else:
        a, b = vx / nx, vy / ny
        spread = math.sqrt(a + b)
        df = (a + b) ** 2 / (a * a / (nx - 1) + b * b / (ny - 1))
    if spread == 0.0:
        raise ValueError("a two-sample t test needs samples with spread")
    statistic = (_mean(x) - _mean(y)) / spread
    return {"statistic": statistic, "pvalue": _t_pvalue(statistic, df, alternative), "df": float(df)}


def ttest_rel(args):
    """paired t test over the differences. reference: scipy.stats.ttest_rel."""
    x = _sample(args, "x")
    y = _sample(args, "y")
    if len(x) != len(y):
        raise ValueError("a paired t test needs equal lengths, got %d and %d" % (len(x), len(y)))
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.ttest_rel(x, y, alternative=_alternative(args))
        return {"statistic": float(out.statistic), "pvalue": float(out.pvalue),
                "df": float(len(x) - 1)}
    return ttest_1samp({"values": [a - b for a, b in zip(x, y)], "popmean": 0.0,
                        "alternative": _alternative(args), "backend": "py"})


def chisquare(args):
    """chi-square goodness of fit against ``expected`` (uniform when absent). reference: scipy.stats.chisquare."""
    observed = [float(v) for v in args["observed"]]
    if len(observed) < 2:
        raise ValueError("a goodness-of-fit test needs at least 2 categories")
    total = math.fsum(observed)
    expected = args.get("expected")
    if expected is None:
        expected = [total / len(observed)] * len(observed)
    else:
        expected = [float(v) for v in expected]
        if len(expected) != len(observed):
            raise ValueError("observed and expected must have the same number of categories")
    if any(v <= 0.0 for v in expected):
        raise ValueError("every expected count must be positive")
    ddof = int(args.get("ddof", 0))
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.chisquare(observed, expected, ddof=ddof)
        return {"statistic": float(out.statistic), "pvalue": float(out.pvalue),
                "df": float(len(observed) - 1 - ddof)}
    statistic = math.fsum((o - e) ** 2 / e for o, e in zip(observed, expected))
    df = float(len(observed) - 1 - ddof)
    return {"statistic": statistic, "pvalue": _chi2_sf(statistic, df), "df": df}


def chi2_contingency(args):
    """chi-square test of independence over a table of counts. reference: scipy.stats.chi2_contingency."""
    table = [[float(v) for v in row] for row in args["table"]]
    if len(table) < 2 or len(table[0]) < 2:
        raise ValueError("a test of independence needs at least a 2x2 table")
    if len({len(row) for row in table}) != 1:
        raise ValueError("every row of the table must be the same length")
    correction = bool(args.get("correction", True))
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.chi2_contingency(table, correction=correction)
        return {"statistic": float(out.statistic), "pvalue": float(out.pvalue),
                "df": float(out.dof),
                "expected": [[float(v) for v in row] for row in out.expected_freq]}
    total = math.fsum(math.fsum(row) for row in table)
    if total == 0.0:
        raise ValueError("a test of independence needs a table with counts in it")
    row_totals = [math.fsum(row) for row in table]
    column_totals = [math.fsum(row[j] for row in table) for j in range(len(table[0]))]
    expected = [[r * c / total for c in column_totals] for r in row_totals]
    if any(e <= 0.0 for row in expected for e in row):
        raise ValueError("a test of independence needs every marginal to be positive")
    df = float((len(table) - 1) * (len(table[0]) - 1))
    yates = correction and df == 1.0
    statistic = 0.0
    for row, expected_row in zip(table, expected):
        for o, e in zip(row, expected_row):
            delta = abs(o - e)
            if yates:
                delta = max(0.0, delta - 0.5)
            statistic += delta * delta / e
    return {"statistic": statistic, "pvalue": _chi2_sf(statistic, df), "df": df,
            "expected": expected}


def f_oneway(args):
    """one-way anova over two or more groups. reference: scipy.stats.f_oneway."""
    groups = [[float(v) for v in group] for group in args["groups"]]
    if len(groups) < 2:
        raise ValueError("a one-way anova needs at least 2 groups")
    if any(len(group) < 1 for group in groups):
        raise ValueError("every group in a one-way anova needs at least one observation")
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.f_oneway(*groups)
        n = sum(len(g) for g in groups)
        return {"statistic": float(out.statistic), "pvalue": float(out.pvalue),
                "df_between": float(len(groups) - 1), "df_within": float(n - len(groups))}
    n = sum(len(group) for group in groups)
    grand = math.fsum(math.fsum(group) for group in groups) / n
    between = math.fsum(len(group) * (_mean(group) - grand) ** 2 for group in groups)
    centres = [_mean(group) for group in groups]
    within = math.fsum(math.fsum((v - centre) ** 2 for v in group)
                       for group, centre in zip(groups, centres))
    df_between = float(len(groups) - 1)
    df_within = float(n - len(groups))
    if df_within <= 0.0:
        raise ValueError("a one-way anova needs more observations than groups")
    if within == 0.0:
        raise ValueError("a one-way anova needs variation inside the groups")
    statistic = (between / df_between) / (within / df_within)
    return {"statistic": statistic, "pvalue": _f_sf(statistic, df_between, df_within),
            "df_between": df_between, "df_within": df_within}


def _ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    ties = []
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


def mannwhitneyu(args):
    """the mann-whitney u test, normal approximation with tie and continuity correction.

    reference: scipy.stats.mannwhitneyu(..., method="asymptotic").
    """
    x = _sample(args, "x", least=1)
    y = _sample(args, "y", least=1)
    alternative = _alternative(args)
    continuity = bool(args.get("use_continuity", True))
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.mannwhitneyu(x, y, alternative=alternative, method="asymptotic",
                                    use_continuity=continuity)
        return {"statistic": float(out.statistic), "pvalue": float(out.pvalue)}
    n1, n2 = len(x), len(y)
    ranks, ties = _ranks(x + y)
    u1 = math.fsum(ranks[:n1]) - n1 * (n1 + 1) / 2.0
    u2 = n1 * n2 - u1
    n = n1 + n2
    tie_term = math.fsum(t ** 3 - t for t in ties)
    spread = math.sqrt(n1 * n2 / 12.0 * ((n + 1) - tie_term / (n * (n - 1.0))))
    if spread == 0.0:
        raise ValueError("the mann-whitney u test needs some variation across the two samples")
    if alternative == "two-sided":
        statistic = max(u1, u2)
    elif alternative == "greater":
        statistic = u1
    else:
        statistic = u1
    numerator = (statistic if alternative != "less" else u2) - n1 * n2 / 2.0
    if continuity:
        numerator -= 0.5
    z = numerator / spread
    tail = 1.0 - ndtr(z)
    pvalue = min(1.0, 2.0 * tail) if alternative == "two-sided" else tail
    return {"statistic": float(u1), "pvalue": float(pvalue)}


_ROYSTON_C1 = (0.0, 0.221157, -0.147981, -2.071190, 4.434685, -2.706056)
_ROYSTON_C2 = (0.0, 0.042981, -0.293762, -1.752461, 5.682633, -3.582633)


def _poly(coefficients, x):
    return math.fsum(c * x ** i for i, c in enumerate(coefficients))


def shapiro(args):
    """the shapiro-wilk test of normality (royston's AS R94). reference: scipy.stats.shapiro."""
    values = _sample(args, "values", least=3)
    if _backend(args) == "sp":
        from scipy import stats as sp_stats

        out = sp_stats.shapiro(values)
        return {"statistic": float(out.statistic), "pvalue": float(out.pvalue)}
    n = len(values)
    ordered = sorted(values)
    m = [ndtri((i + 1 - 0.375) / (n + 0.25)) for i in range(n)]
    ssumm2 = math.fsum(v * v for v in m)
    rsn = 1.0 / math.sqrt(n)
    a = [0.0] * n
    if n == 3:
        # AS R94 is exact at n = 3: the weights are fixed and the p-value is closed form.
        a = [-math.sqrt(0.5), 0.0, math.sqrt(0.5)]
    elif n > 5:
        an = _poly(_ROYSTON_C1, rsn) + m[n - 1] / math.sqrt(ssumm2)
        an1 = _poly(_ROYSTON_C2, rsn) + m[n - 2] / math.sqrt(ssumm2)
        phi = (ssumm2 - 2.0 * m[n - 1] ** 2 - 2.0 * m[n - 2] ** 2) / \
            (1.0 - 2.0 * an * an - 2.0 * an1 * an1)
        a[n - 1], a[0] = an, -an
        a[n - 2], a[1] = an1, -an1
        for i in range(2, n - 2):
            a[i] = m[i] / math.sqrt(phi)
    else:
        an = _poly(_ROYSTON_C1, rsn) + m[n - 1] / math.sqrt(ssumm2)
        phi = (ssumm2 - 2.0 * m[n - 1] ** 2) / (1.0 - 2.0 * an * an)
        a[n - 1], a[0] = an, -an
        for i in range(1, n - 1):
            a[i] = m[i] / math.sqrt(phi)
    centre = _mean(ordered)
    ssq = math.fsum((v - centre) ** 2 for v in ordered)
    if ssq == 0.0:
        raise ValueError("shapiro-wilk needs a sample with spread")
    w = math.fsum(ai * v for ai, v in zip(a, ordered)) ** 2 / ssq
    w = min(w, 1.0)
    if n == 3:
        pvalue = max(0.0, min(1.0, 6.0 / math.pi * (math.asin(math.sqrt(w)) - math.asin(math.sqrt(0.75)))))
    elif n <= 11:
        gamma = -2.273 + 0.459 * n
        if gamma - math.log(1.0 - w) <= 0.0:
            pvalue = 0.0
        else:
            y = -math.log(gamma - math.log(1.0 - w))
            mu = _poly((0.5440, -0.39978, 0.025054, -0.0006714), n)
            sigma = math.exp(_poly((1.3822, -0.77857, 0.062767, -0.0020322), n))
            pvalue = 1.0 - ndtr((y - mu) / sigma)
    else:
        ln_n = math.log(n)
        y = math.log(1.0 - w)
        mu = _poly((-1.5861, -0.31082, -0.083751, 0.0038915), ln_n)
        sigma = math.exp(_poly((-0.4803, -0.082676, 0.0030302), ln_n))
        pvalue = 1.0 - ndtr((y - mu) / sigma)
    return {"statistic": float(w), "pvalue": float(max(0.0, min(1.0, pvalue)))}


TTEST_1SAMP = Calculation("fn.brain.stats.ttest_1samp", ttest_1samp)
TTEST_IND = Calculation("fn.brain.stats.ttest_ind", ttest_ind)
TTEST_REL = Calculation("fn.brain.stats.ttest_rel", ttest_rel)
CHISQUARE = Calculation("fn.brain.stats.chisquare", chisquare)
CHI2_CONTINGENCY = Calculation("fn.brain.stats.chi2_contingency", chi2_contingency)
F_ONEWAY = Calculation("fn.brain.stats.f_oneway", f_oneway)
MANNWHITNEYU = Calculation("fn.brain.stats.mannwhitneyu", mannwhitneyu)
SHAPIRO = Calculation("fn.brain.stats.shapiro", shapiro)

CALCS = {
    c.address: c
    for c in (TTEST_1SAMP, TTEST_IND, TTEST_REL, CHISQUARE, CHI2_CONTINGENCY,
              F_ONEWAY, MANNWHITNEYU, SHAPIRO)
}
