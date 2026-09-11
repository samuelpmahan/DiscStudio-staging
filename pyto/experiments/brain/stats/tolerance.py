"""the one tolerance rule every oracle Part in this vertical records against.

relative to the magnitude of the expected value, absolute near zero; walks
dicts and lists so a bundled result is compared field by field. strings, bools
and ``None`` must be equal exactly.
"""


def close(got, expected, tolerance=1e-9):
    """true when ``got`` agrees with ``expected`` inside ``tolerance``."""
    if isinstance(expected, bool):
        return isinstance(got, bool) and got == expected
    if expected is None or isinstance(expected, str):
        return got == expected
    if isinstance(expected, dict):
        return (isinstance(got, dict) and set(got) == set(expected)
                and all(close(got[k], expected[k], tolerance) for k in expected))
    if isinstance(expected, (list, tuple)):
        return (isinstance(got, (list, tuple)) and len(got) == len(expected)
                and all(close(a, b, tolerance) for a, b in zip(got, expected)))
    if isinstance(got, (str, bool, dict, list, tuple)) or got is None:
        return False
    scale = max(abs(float(expected)), 1.0)
    return abs(float(got) - float(expected)) <= tolerance * scale


def canonical(value, digits=12):
    """every float in a value rounded to ``digits`` significant digits.

    a committed store document is a claim about a calculation, not about the
    machine that ran it: a fresh build on another BLAS, another numpy or another
    python differs in the last bit or two of a float, and a byte comparison of
    the two documents then fails for no reason anybody cares about. twelve
    significant digits is far inside every tolerance this vertical records
    (1e-9 relative, 1e-7 for the one case that says why) and far outside that
    noise, so rounding there makes the document reproducible without making it
    less true. walks dicts and lists; leaves ints, bools, strings and None alone.
    """
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")) or value == 0.0:
            return value
        import math

        exponent = math.floor(math.log10(abs(value)))
        return round(value, max(0, digits - 1 - exponent)) if exponent < digits else \
            float(round(value, 0))
    if isinstance(value, dict):
        return {key: canonical(inner, digits) for key, inner in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonical(inner, digits) for inner in value]
    return value
