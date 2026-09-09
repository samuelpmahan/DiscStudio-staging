#!/usr/bin/env python3
"""Run the graph builder over the paint studio, run SUBDUE, write `report.md`.  `python3
mine.py` rewrites the report; `--check` re-mines and exits non-zero if the report on disk
differs, so the report is evidence and not a note.  Every read stays inside the studio."""
from __future__ import annotations
import os, re, sys
import graphs, subdue
REPORT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report.md")
CORE = os.path.join(graphs.STUDIO, "port", "painter", "core.mjs")
EXPORT = re.compile(r"^export (?:function|class) ([A-Za-z_][A-Za-z0-9_]*)", re.M)
PARAMS = dict(iterations=20, beam=4, min_instances=2, max_size=5)
# What each helper the hand port pulled into core.mjs is called in the studio
# sources.  An empty tuple means the port made a helper out of something that is
# not a call in Python at all -- an operator, or an f-string format spec.
PORT_PY = {
    # PyRandom is the class and its methods, so the studio's `rng.uniform(...)` is it too.
    "PyRandom": ("random.Random", "uniform", "randrange", "random", "choice"),
    "fmt": ("format",), "fmt1": (), "fmt2": (), "fmt3": (),
    "pyRound": ("round",), "pyRoundInt": ("round", "int"), "pyMod": (), "pyFloorDiv": (),
    "pyStr": ("str",), "pyNum": (), "hypot": ("math.hypot",), "atan2": ("math.atan2",),
    "sin": ("math.sin",), "cos": ("math.cos",), "escape": ("html.escape",),
    "degrees": ("math.degrees",), "radians": ("math.radians",), "xy": ("xy", "_xy"),
    # `stroke_for` is `max(source, round(...))` (_families_botanical.py:78-81), the
    # `strokeText` shape; bare `ValueError` is not a hex check, so `checkHex` keeps only
    # spellings that name the check itself.
    "strokeFloor": ("_floor_width",),
    "strokeText": ("_sw", "_stroke", "stroke", "stroke_for"),
    "checkHex": ("_check", "_guard", "fullmatch"),
}
def port_exports():
    """(helper, core.mjs line) for every function or class core.mjs exports."""
    with open(CORE, encoding="utf-8") as handle:
        text = handle.read()
    return [(m.group(1), text.count("\n", 0, m.start()) + 1) for m in EXPORT.finditer(text)]
def callees(labels, expand):
    """The callee names a substructure's node labels stand for, SUB-nodes expanded."""
    names = set()
    for label in labels:
        names |= (expand[label] if label in expand else
                  {label.rsplit("/", 1)[0]} if "/" in label else set())
    return names
def render_sub(sub):
    return ("%s ; %s" % (", ".join("v%d=%s" % (i, l) for i, l in enumerate(sub.labels)),
                         ", ".join("v%d-%s->v%d" % (a, k, b) for a, b, k in sub.edges)))
def brief(items, keep):
    return ", ".join(items[:keep]) + (" +%d" % (len(items) - keep) if len(items) > keep else "")
def collect(**params):
    """Mine the studio; return (rows, whole graph, per-substructure callee sets)."""
    order, per_function, slugs = graphs.build_studio()
    whole = graphs.union(order, per_function)
    settings = dict(PARAMS, **params)
    rows, expand = [], {}
    for rank, (found, instances) in enumerate(subdue.mine(whole.labels, whole.edges,
                                                          **settings), 1):
        verts = sorted({v for inst in instances for v in inst})
        sites = sorted({"%s.py:%d" % (whole.where[v][0], whole.where[v][2]) for v in verts})
        families = sorted({s for v in verts
                           for s in slugs[(whole.where[v][0], whole.where[v][1])]})
        names = callees(found.sub.labels, expand)
        expand["SUB%d" % rank] = names
        rows.append(dict(rank=rank, sub=found.sub, instances=len(instances), sites=sites,
                         families=families, bits=found.value, ratio=found.ratio, callees=names))
    return rows, whole, len(order), settings
def build_report():
    """The whole report as text.  Same studio, same text."""
    rows, whole, functions, settings = collect()
    total = len(graphs.roots(*graphs.parse_studio()[:2]))
    out = ["# Hiding primitives: SUBDUE over the paint studio", "",
           "Mined from %d function graphs (%d nodes, %d edges) covering the %d families "
           "`art_registry.py` addresses, by `subdue.mine(%s)`.  Rebuild with `python3 "
           "mine.py`; `--check` fails if this file drifts." % (
               functions, len(whole.labels), len(whole.edges), total,
               ", ".join("%s=%s" % kv for kv in sorted(settings.items()))), "",
           "## Mined substructures", "",
           "| rank | substructure | inst | families | lines | bits | ratio |",
           "| ---: | --- | ---: | --- | --- | ---: | ---: |"]
    for row in rows:
        out.append("| %d | `%s` | %d | %d/%d: %s | %s | %.1f | %.4f |" % (
            row["rank"], render_sub(row["sub"]), row["instances"], len(row["families"]),
            total, brief(row["families"], 3), brief(row["sites"], 3), row["bits"],
            row["ratio"]))
    out += ["", "## Beside the port", "",
            "`port/painter/core.mjs` is what a human pulled out of these same sources by "
            "hand.  A mined substructure corresponds to a helper when its callees are that "
            "helper's studio spellings and nothing else.", "",
            "| core.mjs helper | line | studio callees | mined |",
            "| --- | ---: | --- | --- |"]
    claimed, helpers_hit = set(), 0
    for helper, line in port_exports():
        alts, hits = set(PORT_PY.get(helper, ())), []
        for row in rows:
            if row["callees"] and row["callees"] <= alts:
                hits.append(row["rank"])
                claimed.add(row["rank"])
        helpers_hit += 1 if hits else 0
        hit = ("n/a (an operator or a format spec, never a call)" if not alts else
               "rank" + ("s " if len(hits) > 1 else " ")
               + ", ".join(str(r) for r in hits) if hits else "not mined")
        out.append("| `%s` | %d | %s | %s |" % (helper, line,
                                                ", ".join(sorted(alts)) or "--", hit))
    out += ["", "Mined substructures with no port helper -- compositions the hand port "
            "did not give a name:", ""]
    for row in rows:
        if row["rank"] in claimed:
            continue
        out.append("- rank %d (%d instances, %.0f bits): `%s` -- callees: %s" % (
            row["rank"], row["instances"], row["bits"], render_sub(row["sub"]),
            ", ".join(sorted(row["callees"])) or "none, pure control and emission"))
    out += ["", "## What this proves", "",
            "The units that pay for themselves in bits are compositions -- a formatter "
            "feeding a tag, a stroke floor formatted into a path, an emission inside a "
            "counted loop -- not the single-call shims `core.mjs` exports: %d of its %d "
            "helpers come back as a mined substructure, and %d of the %d mined "
            "substructures answer to no helper the hand port named.  Those %d are the "
            "candidates, each with its evidence attached: how many instances, which of "
            "the %d families, and the lines they were read off.  It proves nothing about "
            "behaviour -- a substructure is a shape in the call graph, not a promise that "
            "replacing it keeps a single byte of SVG the same." % (
                helpers_hit, len([h for h, _ in port_exports()]), len(rows) - len(claimed),
                len(rows), len(rows) - len(claimed), total), ""]
    return "\n".join(out)
def main(argv):
    text = build_report()
    if "--check" in argv:
        if not os.path.exists(REPORT) or open(REPORT, encoding="utf-8").read() != text:
            print("report.md differs from a fresh mine; run `python3 mine.py`"); return 1
        print("report.md matches a fresh mine"); return 0
    open(REPORT, "w", encoding="utf-8", newline="\n").write(text)
    print("wrote %s" % REPORT); return 0
if __name__ == "__main__":  sys.exit(main(sys.argv[1:]))
