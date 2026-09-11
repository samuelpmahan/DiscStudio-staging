"""oracle and benchmark cases for the distribution facade."""

from scipy import stats as sp_stats

import stats.distributions as distributions

FROZEN = {
    "normal": (lambda: sp_stats.norm(loc=2.0, scale=3.0), {"mu": 2.0, "sigma": 3.0}),
    "t": (lambda: sp_stats.t(df=7.0), {"df": 7.0}),
    "chi2": (lambda: sp_stats.chi2(df=5.0), {"df": 5.0}),
    "binomial": (lambda: sp_stats.binom(n=20, p=0.35), {"n": 20, "p": 0.35}),
    "poisson": (lambda: sp_stats.poisson(mu=4.5), {"mu": 4.5}),
}
POINTS = {
    "normal": [-4.5, -1.0, 0.0, 1.7, 8.25],
    "t": [-3.3, -1.4, 0.0, 0.9, 2.6],
    "chi2": [0.2, 1.0, 3.2, 7.7, 15.0],
    "binomial": [0, 3, 7, 12, 20],
    "poisson": [0, 2, 6, 11, 17],
}
QUANTILES = [0.001, 0.05, 0.25, 0.5, 0.75, 0.95, 0.999]
TOLERANCE = {"normal": 1e-9, "t": 1e-9, "chi2": 1e-9, "binomial": 1e-9, "poisson": 1e-9}


def _case(calc, case, backend, args, reference, expected, tolerance):
    return {"calc": calc, "case": case, "backend": backend,
            "args": dict(args, backend=backend), "reference": reference,
            "expected": expected, "tolerance": tolerance}


def _reference_pdf(dist):
    frozen = FROZEN[dist][0]()
    if dist in distributions.CONTINUOUS:
        return [float(frozen.pdf(x)) for x in POINTS[dist]]
    return [float(frozen.pmf(x)) for x in POINTS[dist]]


ORACLE_CASES = []
for _dist, (_make, _params) in FROZEN.items():
    _reference = distributions._SCIPY_NAME[_dist]
    _op = "pdf" if _dist in distributions.CONTINUOUS else "pmf"
    for _backend in ("py", "sp"):
        ORACLE_CASES.append(_case(
            "fn.brain.stats.pdf", "%s.%s.%s" % (_dist, _op, _backend), _backend,
            {"dist": _dist, "params": _params, "x": POINTS[_dist]},
            "%s.%s" % (_reference, _op),
            (lambda dist=_dist: _reference_pdf(dist)), TOLERANCE[_dist]))
        ORACLE_CASES.append(_case(
            "fn.brain.stats.cdf", "%s.cdf.%s" % (_dist, _backend), _backend,
            {"dist": _dist, "params": _params, "x": POINTS[_dist]},
            "%s.cdf" % _reference,
            (lambda make=_make, dist=_dist:
             [float(make().cdf(x)) for x in POINTS[dist]]), TOLERANCE[_dist]))
        ORACLE_CASES.append(_case(
            "fn.brain.stats.sf", "%s.sf.%s" % (_dist, _backend), _backend,
            {"dist": _dist, "params": _params, "x": POINTS[_dist]},
            "%s.sf" % _reference,
            (lambda make=_make, dist=_dist:
             [float(1.0 - make().cdf(x)) for x in POINTS[dist]]), 1e-7),
        )
        ORACLE_CASES.append(_case(
            "fn.brain.stats.ppf", "%s.ppf.%s" % (_dist, _backend), _backend,
            {"dist": _dist, "params": _params, "q": QUANTILES},
            "%s.ppf" % _reference,
            (lambda make=_make, dist=_dist:
             [(int(make().ppf(q)) if dist in distributions.DISCRETE else float(make().ppf(q)))
              for q in QUANTILES]), TOLERANCE[_dist]))

_BIG = [i / 500.0 - 4.0 for i in range(4000)]
_SMALL = _BIG[:1000]

BENCH_CASES = []
for _calc, _key in (("fn.brain.stats.cdf", "x"), ("fn.brain.stats.pdf", "x")):
    for _dist in ("normal", "t", "chi2"):
        for _backend in ("py", "sp"):
            for _size, _points in (("n=1000", _SMALL), ("n=4000", _BIG)):
                BENCH_CASES.append({
                    "calc": _calc, "backend": _backend, "size": "%s.%s" % (_dist, _size),
                    "make_args": (lambda dist=_dist, points=_points, backend=_backend,
                                  params=FROZEN[_dist][1], key=_key:
                                  {"dist": dist, "params": params, key: points,
                                   "backend": backend})})

CALCS = distributions.CALCS
