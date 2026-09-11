"""oracle and benchmark cases for the distribution-free tests.

scipy is the authority for every one of them, but two cases name a NARROWER
scipy than the obvious one, and say why: ``ks_2samp``'s two-sided tail is
``scipy.stats.kstwobign.sf`` (the limiting kolmogorov distribution), because
``scipy.stats.ks_2samp(method="asymp")`` quietly evaluates the exact two-sided
distribution at an effective sample size -- a different definition, not a
different backend.
"""

import math

from scipy import stats as sp_stats

import stats.nonparametric as nonparametric
from stats.hypothesis_cases import A, B, SKEWED

ZEROS = [round(v - 10.0, 3) for v in A] + [0.0, 0.0, 1.5, 1.5, 1.5]
CHI2_LIKE = [abs(v - 10.0) ** 2 / 4.0 for v in A]


def _case(calc, case, backend, args, reference, expected, tolerance=1e-9, project=None):
    return {"calc": calc, "case": case, "backend": backend,
            "args": dict(args, backend=backend), "reference": reference,
            "expected": expected, "tolerance": tolerance, "project": project}


def _both(calc, case, args, reference, expected, tolerance=1e-9, project=None):
    return [_case(calc, "%s.py" % case, "py", args, reference, expected, tolerance, project),
            _case(calc, "%s.sp" % case, "sp", args, reference, expected, tolerance, project)]


def _verdict(statistic, pvalue):
    return {"statistic": float(statistic), "pvalue": float(pvalue)}


def _only(got):
    return {"statistic": got["statistic"], "pvalue": got["pvalue"]}


def _ks_2samp_reference(alternative):
    out = sp_stats.ks_2samp(A, B, alternative=alternative, method="asymp")
    statistic = float(out.statistic)
    if alternative == "two-sided":
        root = math.sqrt(len(A) * len(B) / float(len(A) + len(B)))
        return _verdict(statistic, float(sp_stats.kstwobign.sf(root * statistic)))
    return _verdict(statistic, float(out.pvalue))


ORACLE_CASES = []
for _alt in ("two-sided", "less", "greater"):
    ORACLE_CASES += _both(
        "fn.brain.stats.ks_1samp", "normal.%s" % _alt,
        {"values": [v - 10.0 for v in A], "dist": "normal", "alternative": _alt},
        "scipy.stats.kstest(..., method='asymp')",
        (lambda alt=_alt: _verdict(
            *(lambda out: (out.statistic, out.pvalue))(
                sp_stats.kstest([v - 10.0 for v in A], sp_stats.norm().cdf,
                                alternative=alt, method="asymp")))),
        1e-9, _only)
    ORACLE_CASES += _both(
        "fn.brain.stats.ks_2samp", "two.samples.%s" % _alt,
        {"x": A, "y": B, "alternative": _alt},
        "scipy.stats.ks_2samp for the statistic, scipy.stats.kstwobign.sf for the two-sided tail",
        (lambda alt=_alt: _ks_2samp_reference(alt)), 1e-9, _only)
    for _correction in (False, True):
        ORACLE_CASES += _both(
            "fn.brain.stats.wilcoxon",
            "signed.rank.%s.%s" % (_alt, "cc" if _correction else "plain"),
            {"values": ZEROS, "alternative": _alt, "correction": _correction},
            "scipy.stats.wilcoxon(..., method='approx', zero_method='wilcox')",
            (lambda alt=_alt, correction=_correction: _verdict(
                *(lambda out: (out.statistic, out.pvalue))(
                    sp_stats.wilcoxon(ZEROS, alternative=alt, method="approx",
                                      correction=correction, zero_method="wilcox")))),
            1e-9, _only)
    ORACLE_CASES += _both(
        "fn.brain.stats.pearson_p", "paired.%s" % _alt,
        {"x": A[:34], "y": B, "alternative": _alt},
        "scipy.stats.pearsonr",
        (lambda alt=_alt: {"r": float(sp_stats.pearsonr(A[:34], B, alternative=alt).statistic),
                           "pvalue": float(sp_stats.pearsonr(A[:34], B,
                                                             alternative=alt).pvalue)}),
        1e-9, (lambda got: {"r": got["r"], "pvalue": got["pvalue"]}))

ORACLE_CASES += _both(
    "fn.brain.stats.ks_1samp", "chi2.null",
    {"values": CHI2_LIKE, "dist": "chi2", "params": {"df": 2.0}},
    "scipy.stats.kstest(..., method='asymp')",
    lambda: _verdict(*(lambda out: (out.statistic, out.pvalue))(
        sp_stats.kstest(CHI2_LIKE, sp_stats.chi2(2.0).cdf, method="asymp"))),
    1e-9, _only)
ORACLE_CASES += _both(
    "fn.brain.stats.wilcoxon", "paired", {"x": A[:34], "y": B},
    "scipy.stats.wilcoxon(..., method='approx', zero_method='wilcox')",
    lambda: _verdict(*(lambda out: (out.statistic, out.pvalue))(
        sp_stats.wilcoxon(A[:34], B, method="approx", zero_method="wilcox"))),
    1e-9, _only)
ORACLE_CASES += _both(
    "fn.brain.stats.ks_1samp", "skewed.normal",
    {"values": SKEWED, "dist": "normal", "params": {"mu": 1.0, "sigma": 2.0}},
    "scipy.stats.kstest(..., method='asymp')",
    lambda: _verdict(*(lambda out: (out.statistic, out.pvalue))(
        sp_stats.kstest(SKEWED, sp_stats.norm(loc=1.0, scale=2.0).cdf, method="asymp"))),
    1e-9, _only)

_BIG_A = [v for v in A] * 30
_BIG_B = [v for v in B] * 30
_MID_A, _MID_B = _BIG_A[:400], _BIG_B[:400]

BENCH_CASES = []
for _backend in ("py", "sp"):
    for _size, _pair in (("n=400", (_MID_A, _MID_B)), ("n=1000", (_BIG_A[:1000], _BIG_B[:1000]))):
        BENCH_CASES.append({
            "calc": "fn.brain.stats.ks_2samp", "backend": _backend, "size": _size,
            "make_args": (lambda pair=_pair, backend=_backend:
                          {"x": pair[0], "y": pair[1], "backend": backend})})
        BENCH_CASES.append({
            "calc": "fn.brain.stats.wilcoxon", "backend": _backend, "size": _size,
            "make_args": (lambda pair=_pair, backend=_backend:
                          {"values": [a - b for a, b in zip(pair[0], pair[1])],
                           "backend": backend})})

CALCS = nonparametric.CALCS
