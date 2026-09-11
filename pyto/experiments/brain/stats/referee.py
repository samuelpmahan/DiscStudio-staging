"""the scorer of the stats vertical's brackets. it did not build any candidate.

it never looks inside a solver to decide: it reads the oracle Parts the store
already holds, the benchmark Parts the store already holds, one conditioning
measurement it takes itself through the public Calculation address, and the line
count of the candidate's function. every number it scores on goes into the
judgment's note, so the whole bracket can be recomputed from the store.
"""

import inspect

import harness

NAME = "referee"


def _oracles_for(store, calc):
    """every oracle Part in the store that belongs to this calculation.

    an oracle Part names its calculation by the segment its address carries --
    the calculation's own name, not its whole dotted address.
    """
    prefix = "px.exp.brain.oracle.stats."
    out = []
    for address in store.brain_addresses():
        if not address.startswith(prefix):
            continue
        value = store.get(address)
        if value.get("calc") == calc:
            out.append(value)
    return out


def _benches_for(store, calc, backend):
    prefix = "px.exp.brain.bench.stats."
    out = []
    for address in store.brain_addresses():
        if not address.startswith(prefix):
            continue
        value = store.get(address)
        if value.get("calc") == calc and value.get("backend") == backend:
            out.append(value)
    return out


def _lines(function):
    return len(inspect.getsource(function).splitlines())


def _size_number(size):
    digits = "".join(c for c in str(size) if c.isdigit())
    return int(digits) if digits else 0


def _polynomial_probe(degree=8, rows=80):
    """the design that separates the three solvers: powers of x, badly conditioned.

    forming X'X squares the condition number, so a solver that builds the gram
    matrix loses about half its digits here and a solver that does not, does not.
    the fitted values (not the coefficients) are compared, because the
    coefficients of a near-singular design are not a well-posed thing to compare.
    """
    import numpy as np

    design = [[(1.0 + i / float(rows - 1)) ** (k + 1) for k in range(degree)]
              for i in range(rows)]
    target = [sum(0.5 * (k + 1) * row[k] for k in range(degree)) + 1.0 for row in design]
    a = np.asarray([[1.0] + row for row in design], dtype=float)
    b = np.asarray(target, dtype=float)
    reference = [float(v) for v in a @ np.linalg.lstsq(a, b, rcond=None)[0]]
    return design, target, reference, float(np.linalg.cond(a))


def score_ols(store, branch, quick=False):
    """score one OLS candidate on the four criteria the bracket recorded."""
    import numpy as np

    import stats.regression as regression

    address = "fn.brain.stats.ols_%s" % branch
    name = "ols_%s" % branch
    calc = regression.CALCS[address]
    backend = "np" if branch == "lstsq" else "py"

    oracles = _oracles_for(store, name)
    correct = sum(1 for one in oracles if one["pass"])
    correctness = (correct / len(oracles)) if oracles else 0.0

    design, target, reference, condition = _polynomial_probe()
    _, conditioning = harness.close(
        calc({"x": design, "y": target, "backend": backend})["fitted"], reference, 0.0)

    benches = _benches_for(store, name, backend)
    biggest = max(benches, key=lambda one: _size_number(one["size"]), default=None)
    speed = biggest["wall_ms_median"] if biggest else 0.0

    clarity = _lines(calc.calculate)

    note = ("read %d oracle Part(s) (%d passed), benchmark %s on the %s backend "
            "(%.4f ms median), conditioning on a degree-8 polynomial design "
            "(condition number %.3e, worst relative disagreement with lstsq %.3e), "
            "solver body %d lines"
            % (len(oracles), correct, biggest["size"] if biggest else "none", backend,
               speed, condition, conditioning, clarity))
    return ({"correctness": correctness, "conditioning": conditioning,
             "speed": speed, "clarity": float(clarity)}, note)
