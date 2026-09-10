"""fn.molecules.transitions: every invocation-to-invocation and Part-to-invocation
transition in the run-record graph, counted once, sorted, and published before any
mining looks for a repeated structure among them.

The owner: "Find meaningful differentiation either through pure calculation or
questions"; "The first mathematics is counting. Structure mining comes after
observations accumulate." SUBDUE (`molecules.mine`) is the structure-mining half of
this experiment; this module is the counting that has to come first -- the same
(from, to, kind) edges `molecules.build_graph` already draws, tallied rather than
searched, so `report.md` opens with a table nobody had to search for.

`fn.molecules.transitions` takes the same record path list `mine.py` mines
(`args["paths"]`), builds the *exact*-scheme graph -- always exact, never shape:
shape's labels ("part", "fn/1->1", ...) collapse addresses the owner would want
told apart in a count -- and publishes one Part, `px.exp.molecules.transitions`,
whose value is::

    {"edges": [{"from": <label>, "to": <label>, "kind": "reads"|"writes"|"next",
                "count": <int>}, ...],   # sorted (-count, from, to, kind)
     "total": <int>}                    # sum of every edge's count

Same record files, same bytes: nothing here reads the clock or a human, so two
calls over the same paths return equal dicts, and their canonical JSON is one
sha256 (`digest_of`, the same one-rule digest `retain.py` and `pyto.neat.diff`
both reuse rather than reinventing a second time).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PYTO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(PYTO, "src"))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from pyto import Calculation  # noqa: E402

import molecules  # noqa: E402

ADDRESS = "px.exp.molecules.transitions"


def _edges_from_counts(counts):
    """The counted dict as the sorted list the Part's value carries."""
    edges = [
        {"from": frm, "to": to, "kind": kind, "count": count}
        for (frm, to, kind), count in counts.items()
    ]
    edges.sort(key=lambda e: (-e["count"], e["from"], e["to"], e["kind"]))
    return edges


def transitions(args):
    """fn.molecules.transitions. args: {"paths": [record path, ...]} -- the same list
    `mine.record_paths()` gives `mine.py`. Builds the exact-scheme graph
    (`molecules.build_graph`) and counts every edge by (from, to, kind)
    (`molecules.count_transitions`, the shared arithmetic `mine()` also uses per
    rank for a molecule's `rarest` bound)."""
    paths = args["paths"]
    graph = molecules.build_graph(paths, "exact")
    counts = molecules.count_transitions(graph.labels, graph.edges)
    edges = _edges_from_counts(counts)
    return {"edges": edges, "total": sum(edge["count"] for edge in edges)}


TRANSITIONS = Calculation("fn.molecules.transitions", transitions)


def canonical_json(value):
    """The one digest rule's input form (retain.py `canonical_json`, reused)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest_of(value):
    """sha256 hex of the canonical JSON (retain.py `digest_of`, reused, not
    reinvented)."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def to_part(value):
    """The Part on disk shape: `{"address", "value", "sha256"}`."""
    return {"address": ADDRESS, "value": value, "sha256": digest_of(value)}


def main(argv):
    paths = argv or None
    if paths is None:
        import mine  # local import: mine.py imports this module, so this stays lazy

        paths = mine.record_paths()
    value = transitions({"paths": paths})
    print(json.dumps(to_part(value), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
