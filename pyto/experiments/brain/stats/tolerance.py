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
