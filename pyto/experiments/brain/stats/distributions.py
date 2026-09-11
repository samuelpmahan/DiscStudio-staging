"""five distributions behind one facade: pdf/pmf, cdf, ppf and a sampler.

``fn.brain.stats.pdf`` / ``.cdf`` / ``.ppf`` take ``{"dist", "params", "x"}``
(or ``"q"`` for ppf) and ``args["backend"]``: "py" (pure python on
``stats.special``, the reference statement) or "sp" (scipy.stats).

sampling is an effect, so it is ``oc.brain.stats.sample``: it asks the run's
effects handle for uniform draws and pushes them through the same ppf. the
effects ledger therefore carries the draws, and a replay of the record produces
the same sample without drawing again.
"""

import math

from pyto import Calculation

from stats.special import bisect, betainc, gammainc, ndtr, ndtri

CONTINUOUS = ("normal", "t", "chi2")
DISCRETE = ("binomial", "poisson")
FAMILIES = CONTINUOUS + DISCRETE

_SCIPY_NAME = {
    "normal": "scipy.stats.norm",
    "t": "scipy.stats.t",
    "chi2": "scipy.stats.chi2",
    "binomial": "scipy.stats.binom",
    "poisson": "scipy.stats.poisson",
}


def _family(args):
    dist = args.get("dist")
    if dist not in FAMILIES:
        raise ValueError("unknown distribution %r: one of %s" % (dist, ", ".join(FAMILIES)))
    return dist


def _backend(args):
    backend = args.get("backend", "py")
    if backend not in ("py", "sp"):
        raise ValueError("unknown backend %r for a distribution: py or sp" % (backend,))
    return backend


def _params(dist, params):
    params = dict(params or {})
    if dist == "normal":
        mu = float(params.get("mu", 0.0))
        sigma = float(params.get("sigma", 1.0))
        if sigma <= 0.0:
            raise ValueError("the normal needs sigma > 0, got %r" % (sigma,))
        return {"mu": mu, "sigma": sigma}
    if dist == "t":
        df = float(params["df"])
        if df <= 0.0:
            raise ValueError("the t needs df > 0, got %r" % (df,))
        return {"df": df}
    if dist == "chi2":
        df = float(params["df"])
        if df <= 0.0:
            raise ValueError("chi2 needs df > 0, got %r" % (df,))
        return {"df": df}
    if dist == "binomial":
        n = int(params["n"])
        p = float(params["p"])
        if n < 0:
            raise ValueError("the binomial needs n >= 0, got %r" % (n,))
        if not 0.0 <= p <= 1.0:
            raise ValueError("the binomial needs p in [0, 1], got %r" % (p,))
        return {"n": n, "p": p}
    mu = float(params["mu"])
    if mu < 0.0:
        raise ValueError("the poisson needs mu >= 0, got %r" % (mu,))
    return {"mu": mu}


def _scipy(dist, params):
    from scipy import stats as sp_stats

    if dist == "normal":
        return sp_stats.norm(loc=params["mu"], scale=params["sigma"])
    if dist == "t":
        return sp_stats.t(df=params["df"])
    if dist == "chi2":
        return sp_stats.chi2(df=params["df"])
    if dist == "binomial":
        return sp_stats.binom(n=params["n"], p=params["p"])
    return sp_stats.poisson(mu=params["mu"])


def _many(value):
    return isinstance(value, (list, tuple))


def _density_py(dist, params, x):
    if dist == "normal":
        z = (x - params["mu"]) / params["sigma"]
        return math.exp(-0.5 * z * z) / (params["sigma"] * math.sqrt(2.0 * math.pi))
    if dist == "t":
        df = params["df"]
        norm = math.exp(math.lgamma((df + 1.0) / 2.0) - math.lgamma(df / 2.0)) / \
            math.sqrt(df * math.pi)
        return norm * (1.0 + x * x / df) ** (-(df + 1.0) / 2.0)
    if dist == "chi2":
        df = params["df"]
        if x < 0.0:
            return 0.0
        if x == 0.0:
            return 0.0 if df > 2.0 else (0.5 if df == 2.0 else float("inf"))
        return math.exp((df / 2.0 - 1.0) * math.log(x) - x / 2.0
                        - (df / 2.0) * math.log(2.0) - math.lgamma(df / 2.0))
    if dist == "binomial":
        n, p = params["n"], params["p"]
        k = int(round(x))
        if k != x or k < 0 or k > n:
            return 0.0
        if p == 0.0:
            return 1.0 if k == 0 else 0.0
        if p == 1.0:
            return 1.0 if k == n else 0.0
        log = (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
               + k * math.log(p) + (n - k) * math.log1p(-p))
        return math.exp(log)
    mu = params["mu"]
    k = int(round(x))
    if k != x or k < 0:
        return 0.0
    if mu == 0.0:
        return 1.0 if k == 0 else 0.0
    return math.exp(k * math.log(mu) - mu - math.lgamma(k + 1))


def _cdf_py(dist, params, x):
    if dist == "normal":
        return ndtr((x - params["mu"]) / params["sigma"])
    if dist == "t":
        df = params["df"]
        if x * x <= df:
            # near the centre the tail form cancels to nothing, so add the
            # half-tail to 0.5 instead of subtracting two numbers that agree.
            half = 0.5 * betainc(0.5, df / 2.0, x * x / (df + x * x))
            return 0.5 + half if x >= 0.0 else 0.5 - half
        half = betainc(df / 2.0, 0.5, df / (df + x * x))
        return 1.0 - 0.5 * half if x >= 0.0 else 0.5 * half
    if dist == "chi2":
        if x <= 0.0:
            return 0.0
        return gammainc(params["df"] / 2.0, x / 2.0)
    if dist == "binomial":
        n = params["n"]
        k = math.floor(x)
        if k < 0:
            return 0.0
        if k >= n:
            return 1.0
        return math.fsum(_density_py(dist, params, i) for i in range(int(k) + 1))
    k = math.floor(x)
    if k < 0:
        return 0.0
    if params["mu"] == 0.0:
        return 1.0
    return 1.0 - gammainc(k + 1.0, params["mu"])


def _ppf_py(dist, params, q):
    if not 0.0 <= q <= 1.0:
        raise ValueError("ppf needs q in [0, 1], got %r" % (q,))
    if dist == "normal":
        if q == 0.0:
            return float("-inf")
        if q == 1.0:
            return float("inf")
        return params["mu"] + params["sigma"] * ndtri(q)
    if dist in CONTINUOUS:
        if q == 0.0:
            return 0.0 if dist == "chi2" else float("-inf")
        if q == 1.0:
            return float("inf")
        low = 0.0 if dist == "chi2" else -1.0
        high = 1.0
        while _cdf_py(dist, params, high) < q:
            high *= 2.0
            if high > 1e18:
                break
        if dist != "chi2":
            while _cdf_py(dist, params, low) > q:
                low *= 2.0
                if low < -1e18:
                    break
        return bisect(lambda v: _cdf_py(dist, params, v), q, low, high)
    top = params["n"] if dist == "binomial" else max(60, int(params["mu"] + 40 * math.sqrt(params["mu"] + 1)))
    if q == 0.0:
        return 0
    total = 0.0
    k = 0
    while k <= top:
        total += _density_py(dist, params, k)
        if total >= q - 1e-12:
            return k
        k += 1
    while dist == "poisson":
        total += _density_py(dist, params, k)
        if total >= q - 1e-12 or k > 10 ** 7:
            return k
        k += 1
    return top


def _apply(dist, params, xs, py, sp, backend):
    if backend == "py":
        return [py(dist, params, v) for v in xs]
    frozen = _scipy(dist, params)
    return [float(sp(frozen, v)) for v in xs]


def pdf(args):
    """the density (continuous) or mass (discrete) at x. reference: the family's scipy .pdf/.pmf."""
    dist = _family(args)
    params = _params(dist, args.get("params"))
    backend = _backend(args)
    x = args["x"]
    xs = [float(v) for v in x] if _many(x) else [float(x)]
    out = _apply(dist, params, xs, _density_py,
                 (lambda f, v: f.pdf(v)) if dist in CONTINUOUS else (lambda f, v: f.pmf(v)),
                 backend)
    return out if _many(x) else out[0]


def cdf(args):
    """the cumulative distribution function at x. reference: the family's scipy .cdf."""
    dist = _family(args)
    params = _params(dist, args.get("params"))
    backend = _backend(args)
    x = args["x"]
    xs = [float(v) for v in x] if _many(x) else [float(x)]
    out = _apply(dist, params, xs, _cdf_py, lambda f, v: f.cdf(v), backend)
    return out if _many(x) else out[0]


def sf(args):
    """the survival function 1 - cdf. reference: the family's scipy .sf."""
    got = cdf(args)
    return [1.0 - v for v in got] if isinstance(got, list) else 1.0 - got


def ppf(args):
    """the quantile function: the smallest x whose cdf reaches q. reference: the family's scipy .ppf."""
    dist = _family(args)
    params = _params(dist, args.get("params"))
    backend = _backend(args)
    q = args["q"]
    qs = [float(v) for v in q] if _many(q) else [float(q)]
    if backend == "py":
        out = [_ppf_py(dist, params, v) for v in qs]
    else:
        frozen = _scipy(dist, params)
        out = [float(frozen.ppf(v)) for v in qs]
        if dist in DISCRETE:
            out = [int(v) for v in out]
    return out if _many(q) else out[0]


def sample(args):
    """``n`` draws from the distribution, by inverse transform on the effects handle's uniforms.

    an effect, so this is an ``oc.``: every draw lands on the run's ledger and a
    replay reproduces the sample exactly.
    """
    effects = args.get("effects")
    if effects is None:
        raise ValueError(
            "oc.brain.stats.sample needs the run's effects handle in args['effects']")
    dist = _family(args)
    params = _params(dist, args.get("params"))
    n = args.get("n", 1)
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        raise ValueError("sample needs a non-negative integer n, got %r" % (n,))
    uniforms = effects.random(n)
    backend = _backend(args)
    drawn = ppf({"dist": dist, "params": params, "q": list(uniforms), "backend": backend})
    return {"dist": dist, "params": params, "n": n, "values": list(drawn)}


def support(args):
    """what the family is, what it needs and where it lives -- readable, json-able."""
    dist = _family(args)
    return {
        "dist": dist,
        "kind": "continuous" if dist in CONTINUOUS else "discrete",
        "reference": _SCIPY_NAME[dist],
        "params": sorted(_params(dist, args.get("params", _DEFAULTS[dist]))),
    }


_DEFAULTS = {
    "normal": {"mu": 0.0, "sigma": 1.0},
    "t": {"df": 10.0},
    "chi2": {"df": 3.0},
    "binomial": {"n": 10, "p": 0.4},
    "poisson": {"mu": 3.0},
}

PDF = Calculation("fn.brain.stats.pdf", pdf)
CDF = Calculation("fn.brain.stats.cdf", cdf)
SF = Calculation("fn.brain.stats.sf", sf)
PPF = Calculation("fn.brain.stats.ppf", ppf)
SUPPORT = Calculation("fn.brain.stats.support", support)
SAMPLE = Calculation("oc.brain.stats.sample", sample)

CALCS = {c.address: c for c in (PDF, CDF, SF, PPF, SUPPORT, SAMPLE)}
