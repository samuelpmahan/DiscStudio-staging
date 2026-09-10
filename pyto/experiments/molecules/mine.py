#!/usr/bin/env python3
"""Mine the committed run records for molecules and write `report.md`.  `python mine.py`
rewrites the report; `--check [path]` re-mines and exits non-zero if the report differs
byte for byte.  Paths in the report are relative to the pyto root; no timestamps."""
from __future__ import annotations
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))  # `import pyto` without the venv, as the README's bare commands run it
import molecules
REPORT = os.path.join(molecules.HERE, "report.md")
RECORDS = ["experiments/students/evidence/run-1/record.json",
           "experiments/grouped-ablation/evidence/run-1/record.json",
           "tests/fixtures/use/order-record.json",
           "viewer/fixtures/parallel-demo.json",
           "viewer/fixtures/effects-demo.json",
           "viewer/fixtures/pyto-grouped-ablation.json",
           "viewer/fixtures/pyto-value-kinds.json",
           "tests/fixtures/px/effects-record.json"]
SCHEMES = ("exact", "shape")
def record_paths():
    return [os.path.join(molecules.PYTO, p) for p in RECORDS]
def collect(scheme, **params):
    paths = record_paths()
    graph = molecules.build_graph(paths, scheme)
    return graph, molecules.mine(graph, molecules.load_records(paths), **params)
def render_query(prefix):
    if prefix is None:  return "none (no Parts)"
    from pyto.pql import PQL
    return "`PQL.prefix(%r)` -> `%r`" % (prefix, PQL.prefix(prefix))
def sites(graph, instance):
    path, _, _ = graph.where[instance[0]]
    ticks = sorted({graph.where[v][1] for v in instance if graph.where[v][1]})
    ids = [graph.where[v][2] for v in instance]
    return "%s [%s] %s" % (path, ", ".join(ticks), ", ".join(ids))
def build_report():
    paths = record_paths()
    out = ["# Molecules: SUBDUE over the run records", "",
           "A molecule is a repeated chain of Calculations over Parts: a substructure of "
           "the run graph (invocations, the Parts they read and write, and the declared "
           "order inside a Tick) that occurs at least twice, vertex-disjoint, and pays for "
           "itself under minimum description length -- the graph plus the substructure is "
           "fewer bits than the graph alone.  It is what \"molecular synthesis\" names "
           "({?} ChainsInsideATick): the unit a program keeps re-composing, mined rather "
           "than declared.  Each is spelled as SUBDUE's canonical form, as a PQL document "
           "that runs the first instance as one Tick of chained Calculations in declared "
           "order (the chain rule of task 57 is checked on every emission), and as a PQL "
           "query that finds its Parts in a store.  Miner: `experiments/hiding-primitives/"
           "subdue.py` with `%s`.  Rebuild with `python mine.py`; `--check` fails if this "
           "file drifts." % ", ".join("%s=%s" % kv for kv in sorted(molecules.PARAMS.items())),
           "", "## Records", "", "| record | nodes | edges | note |", "| --- | ---: | ---: | --- |"]
    for path, nodes, edges, note in molecules.graph_sizes(paths):
        out.append("| `%s` | %d | %d | %s |" % (path, nodes, edges, note or ""))
    readings = {}
    for scheme in SCHEMES:
        graph, found = collect(scheme)
        out += ["", "## Scheme `%s` (%d nodes, %d edges)" % (scheme, len(graph.labels),
                                                             len(graph.edges)), "",
                "| rank | substructure | instances | records | bits | ratio |",
                "| ---: | --- | ---: | --- | ---: | ---: |"]
        for mol in found:
            recs = sorted({graph.where[v][0] for inst in mol.instances for v in inst})
            out.append("| %d | `%s` | %d | %s | %.1f | %.4f |" % (
                mol.rank, molecules.render_sub(mol.sub), len(mol.instances),
                ", ".join("`%s`" % r for r in recs), mol.bits, mol.ratio))
        for mol in found:
            out += ["", "### %s rank %d" % (scheme, mol.rank), ""]
            for inst in mol.instances:
                out.append("- %s" % sites(graph, inst))
            if mol.note:
                out += ["", mol.note]; continue
            out += ["", "```json", json.dumps(mol.document, indent=2), "```", "",
                    "Query: %s" % render_query(mol.query)]
        readings[scheme] = found
    out += ["", "## Reading", "",
            "Under the exact scheme the top molecule is the ablation's fit-fit-score triple "
            "over one split (two fits reading `scratch.ablation.split`, the first one's "
            "model scored), found once in each of the three ablation records; every later "
            "exact rank is that molecule grown by another sibling, and the students record "
            "has no exact molecule because each of its Calculations runs once.  Under the "
            "shape scheme the top molecule is a produce-then-consume pair -- a one-input "
            "Calculation writing a Part that a two-input Calculation reads before writing "
            "its own -- sixteen times: split-then-score and fit-then-score in the ablations, "
            "left-then-score in the parallel demo, sheet-then-retain in the value-kinds "
            "run; rank 2 is the single read-a-Part-write-a-Part step every record has, and "
            "rank 5 is the students' mean and median over one roster beside the demo's "
            "right and the ablation's snapshot.  The exact scheme names a program's "
            "molecule; the shape scheme names the studio's.", ""]
    return "\n".join(out)
def main(argv):
    text = build_report()
    if "--check" in argv:
        rest = [a for a in argv if a != "--check"]
        target = rest[0] if rest else REPORT
        shown = molecules.rel(target)
        if not os.path.exists(target):
            print("%s is missing; run `python mine.py`" % shown); return 1
        with open(target, encoding="utf-8", newline="") as handle:
            if handle.read() != text:
                print("%s differs from a fresh mine; run `python mine.py`" % shown); return 1
        print("%s matches a fresh mine" % shown); return 0
    with open(REPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("wrote %s" % molecules.rel(REPORT)); return 0
if __name__ == "__main__":  sys.exit(main(sys.argv[1:]))
