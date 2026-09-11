"""oracle and benchmark cases for the intervals, the bootstrap and the effect sizes.

the closed-form intervals answer to scipy: ``scipy.stats.t.interval``,
``scipy.stats.binomtest(...).proportion_ci``, ``scipy.stats.chi2.ppf``. the
bootstrap does not -- a resample is a draw, and scipy's resample is not ours --
so its case names the ledger it was fed and an independent recomputation, and a
property test does the rest. the effect sizes are textbook formulas computed
with numpy, and cramer's v and the rank-biserial ride on scipy's own
``chi2_contingency`` and ``mannwhitneyu``.
"""

import math

import numpy as np
from scipy import stats as sp_stats

import stats.intervals as intervals
from stats.regression_cases import draw

SAMPLE = [12.0 + v for v in draw(45, 501, low=-6.0, high=6.0)]
OTHER = [14.5 + v for v in draw(38, 502, low=-9.0, high=9.0)]
GROUPS = [[10.0 + v for v in draw(14, 511, -3.0, 3.0)],
          [12.0 + v for v in draw(17, 512, -4.0, 4.0)],
          [11.0 + v for v in draw(13, 513, -3.5, 3.5)]]
TABLE = [[30, 14, 22], [18, 26, 19]]
LEDGER = [((i * 7919 + 104729) % 100003) / 100003.0 for i in range(200 * 45)]


class Ledger:
    """a stand-in for the effects handle: fixed uniforms, so the interval is a fact."""

    def __init__(self, draws):
        self.draws = list(draws)
        self.asked = []

    def random(self, n):
        self.asked.append(n)
        out, self.draws = self.draws[:n], self.draws[n:]
        if len(out) != n:
            raise AssertionError("the ledger ran out of draws")
        return out


def brute_bootstrap(values, draws, statistic, resamples, level, method="percentile"):
    """the same resample, recomputed with numpy: the second opinion on the interval."""
    n = len(values)
    estimates = []
    for r in range(resamples):
        block = draws[r * n:(r + 1) * n]
        picked = np.asarray([values[min(n - 1, int(u * n))] for u in block], dtype=float)
        if statistic == "mean":
            estimates.append(float(picked.mean()))
        elif statistic == "median":
            estimates.append(float(np.median(picked)))
        else:
            estimates.append(float(picked.std(ddof=1)))
    estimates = np.sort(np.asarray(estimates))
    low = float(np.quantile(estimates, (1.0 - level) / 2.0))
    high = float(np.quantile(estimates, 0.5 + level / 2.0))
    return {"low": low, "high": high}


def _case(calc, case, backend, args, reference, expected, tolerance=1e-9, project=None):
    return {"calc": calc, "case": case, "backend": backend,
            "args": dict(args, backend=backend), "reference": reference,
            "expected": expected, "tolerance": tolerance, "project": project}


def _bounds(got):
    return {"low": got["low"], "high": got["high"]}


ORACLE_CASES = []
for _level in (0.90, 0.95, 0.99):
    ORACLE_CASES.append(_case(
        "fn.brain.stats.ci_mean", "level%d" % int(_level * 100), "py",
        {"values": SAMPLE, "level": _level},
        "scipy.stats.t.interval",
        (lambda level=_level: dict(zip(
            ("low", "high"),
            [float(v) for v in sp_stats.t.interval(
                level, len(SAMPLE) - 1, loc=float(np.mean(SAMPLE)),
                scale=float(sp_stats.sem(SAMPLE)))]))), 1e-9, _bounds))
ORACLE_CASES.append(_case(
    "fn.brain.stats.ci_diff_means", "welch", "py", {"x": SAMPLE, "y": OTHER},
    "scipy.stats.ttest_ind(equal_var=False).confidence_interval",
    lambda: dict(zip(("low", "high"), [float(v) for v in sp_stats.ttest_ind(
        SAMPLE, OTHER, equal_var=False).confidence_interval(0.95)])), 1e-9, _bounds))
ORACLE_CASES.append(_case(
    "fn.brain.stats.ci_proportion", "thirty.of.a.hundred.wilson", "py",
    {"successes": 30, "n": 100, "method": "wilson"},
    "scipy.stats.binomtest(...).proportion_ci(method='wilson')",
    lambda: dict(zip(("low", "high"), [float(v) for v in sp_stats.binomtest(
        30, 100).proportion_ci(method="wilson")])), 1e-9, _bounds))
ORACLE_CASES.append(_case(
    "fn.brain.stats.ci_proportion", "thirty.of.a.hundred.wald", "py",
    {"successes": 30, "n": 100, "method": "wald"},
    "scipy.stats.norm.ppf on the wald half-width",
    lambda: {"low": float(0.3 - sp_stats.norm.ppf(0.975) * math.sqrt(0.3 * 0.7 / 100)),
             "high": float(0.3 + sp_stats.norm.ppf(0.975) * math.sqrt(0.3 * 0.7 / 100))},
    1e-9, _bounds))
ORACLE_CASES.append(_case(
    "fn.brain.stats.ci_variance", "level95", "py", {"values": SAMPLE},
    "scipy.stats.chi2.ppf",
    lambda: {"low": float((len(SAMPLE) - 1) * np.var(SAMPLE, ddof=1)
                          / sp_stats.chi2.ppf(0.975, len(SAMPLE) - 1)),
             "high": float((len(SAMPLE) - 1) * np.var(SAMPLE, ddof=1)
                           / sp_stats.chi2.ppf(0.025, len(SAMPLE) - 1))}, 1e-9, _bounds))
for _statistic in ("mean", "median", "std"):
    ORACLE_CASES.append(_case(
        "oc.brain.stats.bootstrap", "ledger200.%s" % _statistic, "py",
        {"values": SAMPLE, "statistic": _statistic, "resamples": 200, "level": 0.95},
        "stats.intervals_cases.brute_bootstrap (the same ledger, recomputed with numpy)",
        (lambda statistic=_statistic: brute_bootstrap(SAMPLE, LEDGER, statistic, 200, 0.95)),
        1e-9, _bounds))
ORACLE_CASES.append(_case(
    "fn.brain.stats.cohens_d", "two.samples", "py", {"x": SAMPLE, "y": OTHER},
    "numpy: (mean(x) - mean(y)) / pooled sd",
    lambda: float((np.mean(SAMPLE) - np.mean(OTHER)) / math.sqrt(
        ((len(SAMPLE) - 1) * np.var(SAMPLE, ddof=1)
         + (len(OTHER) - 1) * np.var(OTHER, ddof=1))
        / (len(SAMPLE) + len(OTHER) - 2)))))
ORACLE_CASES.append(_case(
    "fn.brain.stats.hedges_g", "two.samples", "py", {"x": SAMPLE, "y": OTHER},
    "numpy: cohen's d times the small-sample correction",
    lambda: float((np.mean(SAMPLE) - np.mean(OTHER)) / math.sqrt(
        ((len(SAMPLE) - 1) * np.var(SAMPLE, ddof=1)
         + (len(OTHER) - 1) * np.var(OTHER, ddof=1))
        / (len(SAMPLE) + len(OTHER) - 2))
        * (1.0 - 3.0 / (4.0 * (len(SAMPLE) + len(OTHER) - 2) - 1.0)))))
ORACLE_CASES.append(_case(
    "fn.brain.stats.glass_delta", "two.samples", "py", {"x": SAMPLE, "y": OTHER},
    "numpy: (mean(x) - mean(y)) / sd(y)",
    lambda: float((np.mean(SAMPLE) - np.mean(OTHER)) / np.std(OTHER, ddof=1))))
ORACLE_CASES.append(_case(
    "fn.brain.stats.eta_squared", "three.groups", "py", {"groups": GROUPS},
    "numpy: SSB / SST",
    lambda: _eta(GROUPS)))
ORACLE_CASES.append(_case(
    "fn.brain.stats.omega_squared", "three.groups", "py", {"groups": GROUPS},
    "numpy: (SSB - df_between * MSW) / (SST + MSW)",
    lambda: _omega(GROUPS)))
for _backend in ("py", "sp"):
    ORACLE_CASES.append(_case(
        "fn.brain.stats.cramers_v", "two.by.three.%s" % _backend, _backend, {"table": TABLE},
        "scipy.stats.chi2_contingency(correction=False)",
        lambda: float(math.sqrt(
            sp_stats.chi2_contingency(TABLE, correction=False).statistic
            / (np.sum(TABLE) * (min(len(TABLE), len(TABLE[0])) - 1))))))
    ORACLE_CASES.append(_case(
        "fn.brain.stats.rank_biserial", "two.samples.%s" % _backend, _backend,
        {"x": SAMPLE, "y": OTHER},
        "scipy.stats.mannwhitneyu: 2U/(n1 n2) - 1",
        lambda: float(2.0 * sp_stats.mannwhitneyu(
            SAMPLE, OTHER, method="asymptotic").statistic
            / (len(SAMPLE) * len(OTHER)) - 1.0)))


def _eta(groups):
    flat = np.concatenate([np.asarray(g, dtype=float) for g in groups])
    grand = float(flat.mean())
    between = float(sum(len(g) * (np.mean(g) - grand) ** 2 for g in groups))
    total = float(((flat - grand) ** 2).sum())
    return between / total


def _omega(groups):
    flat = np.concatenate([np.asarray(g, dtype=float) for g in groups])
    grand = float(flat.mean())
    between = float(sum(len(g) * (np.mean(g) - grand) ** 2 for g in groups))
    within = float(sum(((np.asarray(g, dtype=float) - np.mean(g)) ** 2).sum() for g in groups))
    df_between = len(groups) - 1
    df_within = len(flat) - len(groups)
    mean_within = within / df_within
    return (between - df_between * mean_within) / (between + within + mean_within)


BENCH_CASES = []
for _size, _n in (("n=45", 45), ("n=450", 450)):
    _values = [12.0 + v for v in draw(_n, 601, low=-6.0, high=6.0)]
    for _backend in ("py",):
        BENCH_CASES.append({
            "calc": "fn.brain.stats.ci_mean", "backend": _backend, "size": _size,
            "make_args": (lambda values=_values, backend=_backend:
                          {"values": values, "backend": backend})})

CALCS = intervals.CALCS
