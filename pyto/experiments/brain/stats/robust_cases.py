"""oracle and benchmark cases for the simple and robust regressions.

scipy is the authority for all three: ``scipy.stats.linregress``,
``scipy.stats.theilslopes`` (slope, intercept AND the two interval ends) and
``scipy.stats.siegelslopes``.
"""

from scipy import stats as sp_stats

import stats.robust as robust
from stats.regression_cases import NOISE, X1, draw

CLEAN_X = [float(i) + 0.01 * v for i, v in enumerate(draw(60, 901))]
CLEAN_Y = [2.5 * v + 3.0 + e for v, e in zip(CLEAN_X, NOISE[:60])]
SPIKED_Y = list(CLEAN_Y)
SPIKED_Y[7] += 40.0
SPIKED_Y[31] -= 35.0
TIED_X = [1.0, 1.0, 2.0, 2.0, 3.0, 4.0, 4.0, 5.0, 5.0, 6.0]
TIED_Y = [2.0, 2.0, 3.0, 5.0, 5.0, 7.0, 7.0, 9.0, 9.0, 11.0]


def _case(calc, case, backend, args, reference, expected, tolerance=1e-9, project=None):
    return {"calc": calc, "case": case, "backend": backend,
            "args": dict(args, backend=backend), "reference": reference,
            "expected": expected, "tolerance": tolerance, "project": project}


def _both(calc, case, args, reference, expected, tolerance=1e-9, project=None):
    return [_case(calc, "%s.py" % case, "py", args, reference, expected, tolerance, project),
            _case(calc, "%s.sp" % case, "sp", args, reference, expected, tolerance, project)]


def _linregress(x, y, alternative="two-sided"):
    out = sp_stats.linregress(x, y, alternative=alternative)
    return {"slope": float(out.slope), "intercept": float(out.intercept),
            "r": float(out.rvalue), "pvalue": float(out.pvalue),
            "stderr": float(out.stderr), "intercept_stderr": float(out.intercept_stderr)}


def _theil(x, y, level=0.95):
    out = sp_stats.theilslopes(y, x, alpha=level)
    return {"slope": float(out.slope), "intercept": float(out.intercept),
            "low": float(out.low_slope), "high": float(out.high_slope)}


def _siegel(x, y):
    out = sp_stats.siegelslopes(y, x)
    return {"slope": float(out.slope), "intercept": float(out.intercept)}


_LINE_KEYS = ("slope", "intercept", "r", "pvalue", "stderr", "intercept_stderr")
_THEIL_KEYS = ("slope", "intercept", "low", "high")


def _keep(keys):
    return lambda got: {key: got[key] for key in keys}


ORACLE_CASES = []
for _alt in ("two-sided", "less", "greater"):
    ORACLE_CASES += _both(
        "fn.brain.stats.linregress", "clean.%s" % _alt,
        {"x": CLEAN_X, "y": CLEAN_Y, "alternative": _alt},
        "scipy.stats.linregress",
        (lambda alt=_alt: _linregress(CLEAN_X, CLEAN_Y, alt)), 1e-9, _keep(_LINE_KEYS))
ORACLE_CASES += _both(
    "fn.brain.stats.linregress", "spiked", {"x": CLEAN_X, "y": SPIKED_Y},
    "scipy.stats.linregress", lambda: _linregress(CLEAN_X, SPIKED_Y), 1e-9, _keep(_LINE_KEYS))
ORACLE_CASES += _both(
    "fn.brain.stats.linregress", "against.position", {"y": X1[:40]},
    "scipy.stats.linregress",
    lambda: _linregress(list(range(40)), X1[:40]), 1e-9, _keep(_LINE_KEYS))
for _level in (0.80, 0.90, 0.95, 0.99):
    ORACLE_CASES += _both(
        "fn.brain.stats.theil_sen", "spiked.level%d" % int(_level * 100),
        {"x": CLEAN_X, "y": SPIKED_Y, "level": _level},
        "scipy.stats.theilslopes",
        (lambda level=_level: _theil(CLEAN_X, SPIKED_Y, level)), 1e-9, _keep(_THEIL_KEYS))
ORACLE_CASES += _both(
    "fn.brain.stats.theil_sen", "tied", {"x": TIED_X, "y": TIED_Y},
    "scipy.stats.theilslopes", lambda: _theil(TIED_X, TIED_Y), 1e-9, _keep(_THEIL_KEYS))
ORACLE_CASES += _both(
    "fn.brain.stats.siegel_slopes", "spiked", {"x": CLEAN_X, "y": SPIKED_Y},
    "scipy.stats.siegelslopes", lambda: _siegel(CLEAN_X, SPIKED_Y), 1e-9,
    _keep(("slope", "intercept")))
ORACLE_CASES += _both(
    "fn.brain.stats.siegel_slopes", "tied", {"x": TIED_X, "y": TIED_Y},
    "scipy.stats.siegelslopes", lambda: _siegel(TIED_X, TIED_Y), 1e-9,
    _keep(("slope", "intercept")))

_BIG_X = [float(i) + 0.01 * v for i, v in enumerate(draw(300, 902))]
_BIG_Y = [1.5 * v + 2.0 for v in _BIG_X]
_MID_X, _MID_Y = _BIG_X[:80], _BIG_Y[:80]

BENCH_CASES = []
for _backend in ("py", "sp"):
    for _size, _pair in (("n=80", (_MID_X, _MID_Y)), ("n=300", (_BIG_X, _BIG_Y))):
        for _calc in ("fn.brain.stats.linregress", "fn.brain.stats.theil_sen",
                      "fn.brain.stats.siegel_slopes"):
            BENCH_CASES.append({
                "calc": _calc, "backend": _backend, "size": _size,
                "make_args": (lambda pair=_pair, backend=_backend:
                              {"x": pair[0], "y": pair[1], "backend": backend})})

CALCS = robust.CALCS
