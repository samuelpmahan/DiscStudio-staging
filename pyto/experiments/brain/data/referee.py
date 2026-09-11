"""the scorer of the data vertical's brackets. it did not build any candidate.

same rule as the stats referee: oracle Parts and benchmark Parts out of the
store, a line count off the candidate function, and every number it scored on
written into the judgment's note.
"""

import inspect

NAME = "referee"


def _parts(store, prefix, calc, backend=None):
    out = []
    for address in store.brain_addresses():
        if not address.startswith(prefix):
            continue
        value = store.get(address)
        if value.get("calc") != calc:
            continue
        if backend is not None and value.get("backend") != backend:
            continue
        out.append(value)
    return out


def _lines(function):
    return len(inspect.getsource(function).splitlines())


def _size_number(size):
    digits = "".join(c for c in str(size) if c.isdigit())
    return int(digits) if digits else 0


def score_group_by(store, branch):
    """score one group-by backend on the three criteria the bracket recorded."""
    import data.frame as frame

    calc = "group_by"  # an oracle Part names its calculation by its address segment
    oracles = [one for one in _parts(store, "px.exp.brain.oracle.data.", calc)
               if one["case"].endswith(branch)]
    correct = sum(1 for one in oracles if one["pass"])
    correctness = (correct / len(oracles)) if oracles else 0.0
    benches = _parts(store, "px.exp.brain.bench.data.", calc, backend=branch)
    biggest = max(benches, key=lambda one: _size_number(one["size"]), default=None)
    speed = biggest["wall_ms_median"] if biggest else 0.0
    if branch == "npsort":
        import data.sorted_groups as sorted_groups

        aggregator = sorted_groups.grouped
    else:
        aggregator = frame._aggregate_np if branch == "np" else frame._aggregate_py
    clarity = _lines(aggregator)
    note = ("read %d oracle Part(s) (%d passed), benchmark %s (%.4f ms median), "
            "aggregation body %d lines"
            % (len(oracles), correct, biggest["size"] if biggest else "none", speed, clarity))
    return ({"correctness": correctness, "speed": speed, "clarity": float(clarity)}, note)
