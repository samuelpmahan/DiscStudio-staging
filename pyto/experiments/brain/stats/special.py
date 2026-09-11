"""the special functions the pure-python distribution backend is written on.

regularised incomplete gamma and beta, by series and continued fraction, and
the inverse normal cdf by a rational approximation refined with newton steps.
no numpy, no scipy: this file is what makes the "py" backend a real reference
rather than a wrapper. references: scipy.special.gammainc, scipy.special.betainc,
scipy.special.ndtri.
"""

import math

_MAX_ITERATIONS = 500
_EPSILON = 3.0e-16
_TINY = 1.0e-300


def gammainc(a, x):
    """the regularised lower incomplete gamma P(a, x). reference: scipy.special.gammainc."""
    if a <= 0.0:
        raise ValueError("gammainc needs a > 0, got %r" % (a,))
    if x < 0.0:
        raise ValueError("gammainc needs x >= 0, got %r" % (x,))
    if x == 0.0:
        return 0.0
    if x < a + 1.0:
        return _gamma_series(a, x)
    return 1.0 - _gamma_continued(a, x)


def gammaincc(a, x):
    """the regularised upper incomplete gamma Q(a, x) = 1 - P(a, x)."""
    return 1.0 - gammainc(a, x)


def _gamma_series(a, x):
    ap = a
    total = 1.0 / a
    term = total
    for _ in range(_MAX_ITERATIONS):
        ap += 1.0
        term *= x / ap
        total += term
        if abs(term) < abs(total) * _EPSILON:
            break
    return total * math.exp(-x + a * math.log(x) - math.lgamma(a))


def _gamma_continued(a, x):
    b = x + 1.0 - a
    c = 1.0 / _TINY
    d = 1.0 / b
    h = d
    for i in range(1, _MAX_ITERATIONS + 1):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < _TINY:
            d = _TINY
        c = b + an / c
        if abs(c) < _TINY:
            c = _TINY
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < _EPSILON:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def betainc(a, b, x):
    """the regularised incomplete beta I_x(a, b). reference: scipy.special.betainc."""
    if a <= 0.0 or b <= 0.0:
        raise ValueError("betainc needs a > 0 and b > 0, got %r and %r" % (a, b))
    if not 0.0 <= x <= 1.0:
        raise ValueError("betainc needs x in [0, 1], got %r" % (x,))
    if x == 0.0:
        return 0.0
    if x == 1.0:
        return 1.0
    front = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def _betacf(a, b, x):
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < _TINY:
        d = _TINY
    d = 1.0 / d
    h = d
    for m in range(1, _MAX_ITERATIONS + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < _TINY:
            d = _TINY
        c = 1.0 + aa / c
        if abs(c) < _TINY:
            c = _TINY
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < _TINY:
            d = _TINY
        c = 1.0 + aa / c
        if abs(c) < _TINY:
            c = _TINY
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < _EPSILON:
            break
    return h


_A = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
      1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
_B = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
      6.680131188771972e+01, -1.328068155288572e+01)
_C = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
      -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
_D = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
      3.754408661907416e+00)
_SPLIT_LOW = 0.02425


def ndtri(p):
    """the inverse standard normal cdf. reference: scipy.special.ndtri.

    acklam's rational approximation, then two halley steps against ``ndtr`` --
    which brings it to full double precision.
    """
    if not 0.0 < p < 1.0:
        if p == 0.0:
            return float("-inf")
        if p == 1.0:
            return float("inf")
        raise ValueError("ndtri needs p in [0, 1], got %r" % (p,))
    if p < _SPLIT_LOW:
        q = math.sqrt(-2.0 * math.log(p))
        x = (((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5]) / \
            ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1.0)
    elif p <= 1.0 - _SPLIT_LOW:
        q = p - 0.5
        r = q * q
        x = (((((_A[0] * r + _A[1]) * r + _A[2]) * r + _A[3]) * r + _A[4]) * r + _A[5]) * q / \
            (((((_B[0] * r + _B[1]) * r + _B[2]) * r + _B[3]) * r + _B[4]) * r + 1.0)
    else:
        q = math.sqrt(-2.0 * math.log1p(-p))
        x = -(((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5]) / \
            ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1.0)
    for _ in range(2):
        error = ndtr(x) - p
        density = math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)
        if density == 0.0:
            break
        step = error / density
        x -= step / (1.0 + 0.5 * x * step)
    return x


def ndtr(x):
    """the standard normal cdf. reference: scipy.special.ndtr."""
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def bisect(cdf, target, low, high, tolerance=1e-14, steps=200):
    """the smallest x in [low, high] with cdf(x) >= target, by bisection."""
    for _ in range(steps):
        middle = 0.5 * (low + high)
        if cdf(middle) < target:
            low = middle
        else:
            high = middle
        if high - low <= tolerance * max(1.0, abs(high)):
            break
    return 0.5 * (low + high)
