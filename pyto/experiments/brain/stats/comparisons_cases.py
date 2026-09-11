"""oracle and benchmark cases for the comparison toolbox.

scipy is the authority for all of them, and for the multiple-comparison
corrections it is the authority for benjamini-hochberg
(``scipy.stats.false_discovery_control``); bonferroni and holm have no scipy
function, so their cases name the published definition written out below.
"""

from scipy import stats as sp_stats

import stats.comparisons as comparisons
from stats.hypothesis_cases import GROUPS, draw

SPREADS = [draw(16, 701, 10.0, 1.0), draw(19, 702, 10.0, 3.5), draw(14, 703, 10.0, 2.0)]
PVALUES = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.6]
TABLE22 = [[8, 2], [1, 5]]
TABLE22_BIG = [[30, 14], [18, 26]]


def brute_bonferroni(pvalues):
    """the published definition: every p-value times how many were asked, capped at one."""
    return [min(1.0, p * len(pvalues)) for p in pvalues]


def brute_holm(pvalues):
    """holm's step-down: (m - rank) * p, made monotone from the smallest up."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    out = [0.0] * m
    running = 0.0
    for place, i in enumerate(order):
        running = max(running, (m - place) * pvalues[i])
        out[i] = min(1.0, running)
    return out


def _case(calc, case, backend, args, reference, expected, tolerance=1e-9, project=None):
    return {"calc": calc, "case": case, "backend": backend,
            "args": dict(args, backend=backend), "reference": reference,
            "expected": expected, "tolerance": tolerance, "project": project}


def _both(calc, case, args, reference, expected, tolerance=1e-9, project=None):
    return [_case(calc, "%s.py" % case, "py", args, reference, expected, tolerance, project),
            _case(calc, "%s.sp" % case, "sp", args, reference, expected, tolerance, project)]


def _verdict(out, df=None):
    value = {"statistic": float(out.statistic), "pvalue": float(out.pvalue)}
    if df is not None:
        value["df"] = float(df)
    return value


def _only(*keys):
    return lambda got: {key: got[key] for key in keys}


ORACLE_CASES = []
ORACLE_CASES += _both(
    "fn.brain.stats.kruskal", "three.groups", {"groups": GROUPS},
    "scipy.stats.kruskal", lambda: _verdict(sp_stats.kruskal(*GROUPS), len(GROUPS) - 1))
ORACLE_CASES += _both(
    "fn.brain.stats.kruskal", "tied",
    {"groups": [[1.0, 2.0, 2.0, 3.0], [2.0, 3.0, 3.0, 4.0], [3.0, 4.0, 4.0, 5.0]]},
    "scipy.stats.kruskal",
    lambda: _verdict(sp_stats.kruskal([1.0, 2.0, 2.0, 3.0], [2.0, 3.0, 3.0, 4.0],
                                      [3.0, 4.0, 4.0, 5.0]), 2))
for _center in ("median", "mean"):
    ORACLE_CASES += _both(
        "fn.brain.stats.levene", "spreads.%s" % _center,
        {"groups": SPREADS, "center": _center},
        "scipy.stats.levene",
        (lambda center=_center: _verdict(sp_stats.levene(*SPREADS, center=center))),
        1e-9, _only("statistic", "pvalue"))
ORACLE_CASES += _both(
    "fn.brain.stats.bartlett", "spreads", {"groups": SPREADS},
    "scipy.stats.bartlett",
    lambda: _verdict(sp_stats.bartlett(*SPREADS), len(SPREADS) - 1))
for _alt in ("two-sided", "less", "greater"):
    ORACLE_CASES += _both(
        "fn.brain.stats.binom_test", "thirteen.of.forty.%s" % _alt,
        {"successes": 13, "n": 40, "p": 0.5, "alternative": _alt},
        "scipy.stats.binomtest",
        (lambda alt=_alt: {"pvalue": float(sp_stats.binomtest(13, 40, 0.5,
                                                              alternative=alt).pvalue)}),
        1e-9, _only("pvalue"))
    ORACLE_CASES += _both(
        "fn.brain.stats.binom_test", "biased.coin.%s" % _alt,
        {"successes": 7, "n": 9, "p": 0.3, "alternative": _alt},
        "scipy.stats.binomtest",
        (lambda alt=_alt: {"pvalue": float(sp_stats.binomtest(7, 9, 0.3,
                                                              alternative=alt).pvalue)}),
        1e-9, _only("pvalue"))
    ORACLE_CASES += _both(
        "fn.brain.stats.fisher_exact", "small.%s" % _alt,
        {"table": TABLE22, "alternative": _alt},
        "scipy.stats.fisher_exact",
        (lambda alt=_alt: {"odds_ratio": float(sp_stats.fisher_exact(TABLE22, alternative=alt)[0]),
                           "pvalue": float(sp_stats.fisher_exact(TABLE22, alternative=alt)[1])}),
        1e-9, _only("odds_ratio", "pvalue"))
    ORACLE_CASES += _both(
        "fn.brain.stats.fisher_exact", "bigger.%s" % _alt,
        {"table": TABLE22_BIG, "alternative": _alt},
        "scipy.stats.fisher_exact",
        (lambda alt=_alt: {
            "odds_ratio": float(sp_stats.fisher_exact(TABLE22_BIG, alternative=alt)[0]),
            "pvalue": float(sp_stats.fisher_exact(TABLE22_BIG, alternative=alt)[1])}),
        1e-9, _only("odds_ratio", "pvalue"))
ORACLE_CASES += _both(
    "fn.brain.stats.multipletests", "benjamini.hochberg",
    {"pvalues": PVALUES, "method": "benjamini-hochberg"},
    "scipy.stats.false_discovery_control(method='bh')",
    lambda: [float(v) for v in sp_stats.false_discovery_control(PVALUES, method="bh")],
    1e-9, (lambda got: got["adjusted"]))
ORACLE_CASES += _both(
    "fn.brain.stats.multipletests", "bonferroni",
    {"pvalues": PVALUES, "method": "bonferroni"},
    "stats.comparisons_cases.brute_bonferroni (the published definition; scipy has no bonferroni)",
    lambda: brute_bonferroni(PVALUES), 1e-9, (lambda got: got["adjusted"]))
ORACLE_CASES += _both(
    "fn.brain.stats.multipletests", "holm",
    {"pvalues": PVALUES, "method": "holm"},
    "stats.comparisons_cases.brute_holm (the published step-down; scipy has no holm)",
    lambda: brute_holm(PVALUES), 1e-9, (lambda got: got["adjusted"]))

_BIG = [draw(1200, 800 + i, 10.0, 1.0 + i) for i in range(3)]
_MID = [group[:200] for group in _BIG]

BENCH_CASES = []
for _backend in ("py", "sp"):
    for _size, _groups in (("n=600", _MID), ("n=3600", _BIG)):
        for _calc in ("fn.brain.stats.kruskal", "fn.brain.stats.levene",
                      "fn.brain.stats.bartlett"):
            BENCH_CASES.append({
                "calc": _calc, "backend": _backend, "size": _size,
                "make_args": (lambda groups=_groups, backend=_backend:
                              {"groups": groups, "backend": backend})})

CALCS = comparisons.CALCS
