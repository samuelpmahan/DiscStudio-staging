"""oracle and benchmark cases for the hypothesis tests.

the shapiro-wilk cases carry a looser tolerance and say why: AS R94's normalising
polynomials are published to seven figures, so the pure-python path reproduces
scipy's fortran to about 5e-9 relative and no closer.
"""

from scipy import stats as sp_stats

import stats.hypothesis as hypothesis


def draw(n, seed, centre=0.0, spread=1.0):
    """a deterministic normal-ish sample: an lcg through a box-muller pair."""
    import math

    state = (seed * 6364136223846793005 + 1442695040888963407) % (2 ** 64)
    out = []
    while len(out) < n:
        pair = []
        for _ in range(2):
            state = (state * 6364136223846793005 + 1442695040888963407) % (2 ** 64)
            pair.append(max(1e-12, (state >> 11) / float(2 ** 53)))
        radius = math.sqrt(-2.0 * math.log(pair[0]))
        out.append(centre + spread * radius * math.cos(2.0 * math.pi * pair[1]))
        if len(out) < n:
            out.append(centre + spread * radius * math.sin(2.0 * math.pi * pair[1]))
    return out


A = draw(40, 91, centre=10.0, spread=3.0)
B = draw(34, 92, centre=11.6, spread=4.2)
PAIRED = draw(34, 93, centre=10.4, spread=3.1)
SKEWED = [abs(v) ** 1.9 for v in draw(28, 94)]
GROUPS = [draw(15, 95, 9.0, 2.0), draw(18, 96, 10.5, 2.4), draw(12, 97, 11.2, 2.1)]
COUNTS = [16, 18, 16, 14, 12, 12]
EXPECTED = [16.0, 16.0, 16.0, 16.0, 12.0, 8.0]
TABLE = [[10, 20, 30], [6, 9, 17]]
TABLE22 = [[10, 20], [6, 9]]
SHAPIRO_TOLERANCE = 1e-7


def _case(calc, case, backend, args, reference, expected, tolerance=1e-9):
    return {"calc": calc, "case": case, "backend": backend,
            "args": dict(args, backend=backend), "reference": reference,
            "expected": expected, "tolerance": tolerance}


def _both(calc, case, args, reference, expected, tolerance=1e-9):
    return [_case(calc, "%s.py" % case, "py", args, reference, expected, tolerance),
            _case(calc, "%s.sp" % case, "sp", args, reference, expected, tolerance)]


def _t(out, df):
    return {"statistic": float(out.statistic), "pvalue": float(out.pvalue), "df": float(df)}


ORACLE_CASES = []
for _alt in ("two-sided", "less", "greater"):
    ORACLE_CASES += _both(
        "fn.brain.stats.ttest_1samp", "one.%s" % _alt,
        {"values": A, "popmean": 9.5, "alternative": _alt},
        "scipy.stats.ttest_1samp",
        (lambda alt=_alt: _t(sp_stats.ttest_1samp(A, 9.5, alternative=alt), len(A) - 1)))
ORACLE_CASES += _both(
    "fn.brain.stats.ttest_ind", "pooled", {"x": A, "y": B},
    "scipy.stats.ttest_ind",
    lambda: _t(sp_stats.ttest_ind(A, B), len(A) + len(B) - 2))
ORACLE_CASES += _both(
    "fn.brain.stats.ttest_ind", "welch", {"x": A, "y": B, "equal_var": False},
    "scipy.stats.ttest_ind",
    lambda: _t(sp_stats.ttest_ind(A, B, equal_var=False),
               sp_stats.ttest_ind(A, B, equal_var=False).df))
ORACLE_CASES += _both(
    "fn.brain.stats.ttest_ind", "welch.greater",
    {"x": A, "y": B, "equal_var": False, "alternative": "greater"},
    "scipy.stats.ttest_ind",
    lambda: _t(sp_stats.ttest_ind(A, B, equal_var=False, alternative="greater"),
               sp_stats.ttest_ind(A, B, equal_var=False, alternative="greater").df))
ORACLE_CASES += _both(
    "fn.brain.stats.ttest_rel", "paired", {"x": B, "y": PAIRED},
    "scipy.stats.ttest_rel",
    lambda: _t(sp_stats.ttest_rel(B, PAIRED), len(B) - 1))
ORACLE_CASES += _both(
    "fn.brain.stats.chisquare", "uniform", {"observed": COUNTS},
    "scipy.stats.chisquare",
    lambda: _t(sp_stats.chisquare(COUNTS), len(COUNTS) - 1))
ORACLE_CASES += _both(
    "fn.brain.stats.chisquare", "expected.ddof",
    {"observed": COUNTS, "expected": EXPECTED, "ddof": 1},
    "scipy.stats.chisquare",
    lambda: _t(sp_stats.chisquare(COUNTS, EXPECTED, ddof=1), len(COUNTS) - 2))
ORACLE_CASES += _both(
    "fn.brain.stats.chi2_contingency", "two.by.three", {"table": TABLE},
    "scipy.stats.chi2_contingency",
    lambda: {"statistic": float(sp_stats.chi2_contingency(TABLE).statistic),
             "pvalue": float(sp_stats.chi2_contingency(TABLE).pvalue),
             "df": float(sp_stats.chi2_contingency(TABLE).dof),
             "expected": [[float(v) for v in row]
                          for row in sp_stats.chi2_contingency(TABLE).expected_freq]})
ORACLE_CASES += _both(
    "fn.brain.stats.chi2_contingency", "two.by.two.yates", {"table": TABLE22},
    "scipy.stats.chi2_contingency",
    lambda: {"statistic": float(sp_stats.chi2_contingency(TABLE22).statistic),
             "pvalue": float(sp_stats.chi2_contingency(TABLE22).pvalue),
             "df": float(sp_stats.chi2_contingency(TABLE22).dof),
             "expected": [[float(v) for v in row]
                          for row in sp_stats.chi2_contingency(TABLE22).expected_freq]})
ORACLE_CASES += _both(
    "fn.brain.stats.f_oneway", "three.groups", {"groups": GROUPS},
    "scipy.stats.f_oneway",
    lambda: {"statistic": float(sp_stats.f_oneway(*GROUPS).statistic),
             "pvalue": float(sp_stats.f_oneway(*GROUPS).pvalue),
             "df_between": float(len(GROUPS) - 1),
             "df_within": float(sum(len(g) for g in GROUPS) - len(GROUPS))})
for _alt in ("two-sided", "less", "greater"):
    ORACLE_CASES += _both(
        "fn.brain.stats.mannwhitneyu", "ranks.%s" % _alt,
        {"x": A, "y": B, "alternative": _alt},
        "scipy.stats.mannwhitneyu",
        (lambda alt=_alt: {
            "statistic": float(sp_stats.mannwhitneyu(A, B, alternative=alt,
                                                     method="asymptotic").statistic),
            "pvalue": float(sp_stats.mannwhitneyu(A, B, alternative=alt,
                                                  method="asymptotic").pvalue)}))
ORACLE_CASES += _both(
    "fn.brain.stats.mannwhitneyu", "tied",
    {"x": [1.0, 2.0, 2.0, 3.0, 5.0, 5.0, 5.0], "y": [2.0, 3.0, 3.0, 4.0, 5.0, 9.0]},
    "scipy.stats.mannwhitneyu",
    lambda: {"statistic": float(sp_stats.mannwhitneyu(
        [1.0, 2.0, 2.0, 3.0, 5.0, 5.0, 5.0], [2.0, 3.0, 3.0, 4.0, 5.0, 9.0],
        method="asymptotic").statistic),
        "pvalue": float(sp_stats.mannwhitneyu(
            [1.0, 2.0, 2.0, 3.0, 5.0, 5.0, 5.0], [2.0, 3.0, 3.0, 4.0, 5.0, 9.0],
            method="asymptotic").pvalue)})
for _name, _sample in (("normal", A), ("skewed", SKEWED), ("tiny", A[:3]), ("small", A[:8])):
    ORACLE_CASES += _both(
        "fn.brain.stats.shapiro", "royston.%s" % _name, {"values": _sample},
        "scipy.stats.shapiro",
        (lambda sample=_sample: {"statistic": float(sp_stats.shapiro(sample).statistic),
                                 "pvalue": float(sp_stats.shapiro(sample).pvalue)}),
        SHAPIRO_TOLERANCE)

_BIG_A = draw(4000, 981, 10.0, 3.0)
_BIG_B = draw(3600, 982, 10.4, 3.4)
_MID_A, _MID_B = _BIG_A[:600], _BIG_B[:600]

BENCH_CASES = []
for _backend in ("py", "sp"):
    for _size, _pair in (("n=600", (_MID_A, _MID_B)), ("n=4000", (_BIG_A, _BIG_B))):
        BENCH_CASES.append({
            "calc": "fn.brain.stats.ttest_ind", "backend": _backend, "size": _size,
            "make_args": (lambda pair=_pair, backend=_backend:
                          {"x": pair[0], "y": pair[1], "equal_var": False, "backend": backend})})
        BENCH_CASES.append({
            "calc": "fn.brain.stats.mannwhitneyu", "backend": _backend, "size": _size,
            "make_args": (lambda pair=_pair, backend=_backend:
                          {"x": pair[0], "y": pair[1], "backend": backend})})
    for _size, _sample in (("n=600", _MID_A), ("n=4000", _BIG_A)):
        BENCH_CASES.append({
            "calc": "fn.brain.stats.shapiro", "backend": _backend, "size": _size,
            "make_args": (lambda sample=_sample, backend=_backend:
                          {"values": sample, "backend": backend})})

CALCS = hypothesis.CALCS
