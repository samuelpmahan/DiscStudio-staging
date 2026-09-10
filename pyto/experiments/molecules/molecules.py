"""Molecules: SUBDUE over pyto-run-record@1 files.

One labelled directed graph is built from a list of records.  Nodes: one per invocation,
labelled by its Calculation address; one per Part address a run touched.  Edges:
(Part -> invocation, "reads") for every ``px:`` binding and for every ``fn:`` binding
resolved through the producer's ``into`` ({?} ResultReadsAreReads); (invocation -> Part,
"writes") for every produce; (invocation -> next invocation in the same Tick, "next") in
declared order -- the chain.  Two label schemes: ``exact`` keeps full addresses; ``shape``
calls every Part "part" and a Calculation "<fn|oc>/<inputs>-><produces>".

The miner is ``experiments/hiding-primitives/subdue.py`` (Cook and Holder 1994).  A mined
substructure with at least two vertex-disjoint instances that compresses the graph is a
molecule: a repeated chain of Calculations over Parts, the thing "molecular synthesis"
names ({?} ChainsInsideATick)."""
from __future__ import annotations
import json, os, sys
from collections import Counter, namedtuple
HERE = os.path.dirname(os.path.abspath(__file__))
PYTO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(PYTO, "experiments", "hiding-primitives"))
import subdue  # noqa: E402
SCHEMA = "pyto-run-record@1"
Graph = namedtuple("Graph", "labels edges where kinds")
# `rarest` is the least-counted transition among `sub`'s own edges, counted over the graph
# state `sub` was mined from ({?} ChainsInsideATick's counting-before-mining half): every
# instance is one vertex-disjoint occurrence of every edge in `sub`, so `rarest` is never
# less than `len(instances)` -- counting is what proves the bound, not what checks it.
Molecule = namedtuple("Molecule", "rank sub instances bits ratio document query note rarest")
PARAMS = dict(iterations=8, beam=4, min_instances=2, max_size=5)
def rel(path):
    return os.path.relpath(os.path.abspath(path), PYTO).replace(os.sep, "/")
def load(path):
    """(record, note) -- the record when it is a pyto-run-record@1 with ticks, else None."""
    with open(path, encoding="utf-8") as handle:
        record = json.load(handle)
    if record.get("schema") != SCHEMA:
        return None, "skipped: schema is %r, not %s" % (record.get("schema"), SCHEMA)
    if not isinstance(record.get("ticks"), list) or not record["ticks"]:
        return None, "skipped: no ticks"
    return record, None
def produces(invocation):
    into = invocation.get("into")
    if into is None:  return []
    return list(into) if isinstance(into, list) else [into]
def resolve(binding, by_id):
    """Addresses one binding reads: px:<address>, fn:<id>, fn:<id>#<address>."""
    if binding.startswith("px:"):
        return [binding[3:]]
    if binding.startswith("fn:"):
        text = binding[3:]
        if text in by_id:
            return produces(by_id[text])
        if "#" in text:
            producer, _, address = text.rpartition("#")
            if producer in by_id:
                return [address]
    return []
def shape_label(invocation):
    address = invocation["calculation"]["address"]
    kind = address.split(".", 1)[0]
    return "%s/%d->%d" % (kind, len(invocation.get("inputs") or {}), len(produces(invocation)))
def build_graph(paths, scheme="exact"):
    """The graph over the given records in the given order; `where` maps a node to
    (record path relative to the pyto root, tick name, invocation id or Part address)."""
    labels, edges, where, kinds = [], [], [], []
    for path in paths:
        record, note = load(path)
        if record is None:  continue
        by_id = {inv["id"]: inv for tick in record["ticks"] for inv in tick["invocations"]}
        nodes, part_reads, part_writes, touched = {}, [], [], set()
        for tick in record["ticks"]:
            previous = None
            for inv in tick["invocations"]:
                node = len(labels)
                nodes[inv["id"]] = node
                labels.append(inv["calculation"]["address"] if scheme == "exact"
                              else shape_label(inv))
                where.append((rel(path), tick.get("name"), inv["id"])); kinds.append("invocation")
                for binding in (inv.get("inputs") or {}).values():
                    for address in resolve(binding, by_id):
                        part_reads.append((address, node)); touched.add(address)
                for address in produces(inv):
                    part_writes.append((node, address)); touched.add(address)
                if previous is not None:
                    edges.append((previous, node, "next"))
                previous = node
        parts = {}
        for address in sorted(touched):
            parts[address] = len(labels)
            labels.append(address if scheme == "exact" else "part")
            where.append((rel(path), None, address)); kinds.append("part")
        seen = set()
        for address, node in part_reads:
            edge = (parts[address], node, "reads")
            if edge not in seen:  seen.add(edge); edges.append(edge)
        for node, address in part_writes:
            edge = (node, parts[address], "writes")
            if edge not in seen:  seen.add(edge); edges.append(edge)
    return Graph(labels, edges, where, kinds)
def graph_sizes(paths, scheme="exact"):
    """[(relative path, nodes, edges, note)] per record."""
    rows = []
    for path in paths:
        record, note = load(path)
        if record is None:
            rows.append((rel(path), 0, 0, note)); continue
        graph = build_graph([path], scheme)
        rows.append((rel(path), len(graph.labels), len(graph.edges), None))
    return rows
def count_transitions(labels, edges):
    """{(from_label, to_label, kind): count} over every edge of a labels/edges pair --
    any Graph's, or `mine`'s current working graph mid-compression, whose labels may
    already include an earlier rank's "SUB<rank>" node standing for a compressed
    substructure. Counting first, mining second: this is the shared arithmetic behind
    both `fn.molecules.transitions` (transitions.py, over the uncompressed exact-scheme
    graph) and every molecule's `rarest` bound below (over whichever graph it was found
    in)."""
    counts = Counter()
    for a, b, kind in edges:
        counts[(labels[a], labels[b], kind)] += 1
    return counts
def rarest_transition_count(sub, counts):
    """The minimum, over every edge of substructure `sub`, of that edge's count in
    `counts`. None for an edgeless substructure (nothing to bound)."""
    values = [counts.get((sub.labels[a], sub.labels[b], kind), 0) for a, b, kind in sub.edges]
    return min(values) if values else None
def render_sub(sub):
    return ("%s ; %s" % (", ".join("v%d=%s" % (i, l) for i, l in enumerate(sub.labels)),
                         ", ".join("v%d-%s->v%d" % (a, k, b) for a, b, k in sub.edges)))
def common_prefix(addresses):
    """Longest common address prefix, by segment, spelled for PQL.prefix."""
    if not addresses:  return None
    split = [a.split(".") for a in addresses]
    common = []
    for parts in zip(*split):
        if len(set(parts)) != 1:  break
        common.append(parts[0])
    if len(addresses) == 1:  return addresses[0]
    if not common:  return None
    return ".".join(common) + "."
def document(graph, records, instance, name):
    """The PQL document that runs an instance as one Tick of chained Calculations, in
    declared order, from the instance's real addresses and input names."""
    invs = sorted((v for v in instance if graph.kinds[v] == "invocation"))
    calcs = []
    for node in invs:
        path, tick_name, inv_id = graph.where[node]
        record = records[path]
        by_id = {inv["id"]: inv for tick in record["ticks"] for inv in tick["invocations"]}
        inv = by_id[inv_id]
        with_ = {}
        for name_, binding in (inv.get("inputs") or {}).items():
            addresses = resolve(binding, by_id)
            with_[name_] = addresses[0] if len(addresses) == 1 else addresses
        calcs.append({"call": inv["calculation"]["address"], "with": with_,
                      "into": inv.get("into")})
    return {"Ticks": [{"name": name, "Calculations": calcs}]}
def chain_rule(doc):
    """Task 57's rule: every `with` names a Part outside the Tick or one an EARLIER sibling
    produces; two siblings producing one address is refused.  Returns a list of faults."""
    faults, produced, producers = [], set(), {}
    for tick in doc["Ticks"]:
        produced_in_tick = set()
        for calc in tick["Calculations"]:
            into = calc["into"]
            outs = into if isinstance(into, list) else ([] if into is None else [into])
            for address in outs:
                if address in producers:
                    faults.append("two producers for %s" % address)
            produced_in_tick.update(outs)
        seen = set()
        for calc in tick["Calculations"]:
            for name, address in calc["with"].items():
                for one in (address if isinstance(address, list) else [address]):
                    if one in produced_in_tick and one not in seen:
                        faults.append("backwards read of %s by %s" % (one, calc["call"]))
            into = calc["into"]
            outs = into if isinstance(into, list) else ([] if into is None else [into])
            for address in outs:
                if address in seen:  faults.append("two producers for %s" % address)
                seen.add(address); producers[address] = calc["call"]
    return faults
def mine(graph, records, **params):
    """Iterative compression by hand (subdue.mine keeps only origin unions; the document
    needs the vertex mapping of the first instance).  Returns [Molecule]."""
    settings = dict(PARAMS, **params)
    labels, edges = list(graph.labels), list(graph.edges)
    origin, vertex_ref, out = [(v,) for v in range(len(labels))], len(labels), []
    for rank in range(1, settings["iterations"] + 1):
        found = subdue.best_substructure(labels, edges, settings["beam"],
                                         settings["min_instances"], settings["max_size"],
                                         vertex_ref=vertex_ref)
        if found is None or found.value <= 0.0:  break
        rarest = rarest_transition_count(found.sub, count_transitions(labels, edges))
        primitive = not any(l.startswith("SUB") for l in found.sub.labels)
        if primitive:
            instances = [tuple(origin[w][0] for w in inst) for inst in found.instances]
            doc = document(graph, records, instances[0], "molecule-%d" % rank)
            faults = chain_rule(doc)
            if faults:
                raise AssertionError("emission broke the chain rule: %s" % faults)
            parts = sorted({graph.where[v][2] for v in instances[0]
                            if graph.kinds[v] == "part"})   # the first instance's Parts
            if not parts:
                parts = sorted({a for calc in doc["Ticks"][0]["Calculations"]
                                for a in ([calc["into"]] if isinstance(calc["into"], str)
                                          else calc["into"] or [])})
            prefix = common_prefix(parts)
            note = None
        else:
            instances = [tuple(sorted({v for w in inst for v in origin[w]}))
                         for inst in found.instances]
            doc, prefix = None, None
            note = "compound: built on an earlier rank's SUB node; no document emitted"
        out.append(Molecule(rank, found.sub, instances, found.value, found.ratio, doc,
                            prefix, note, rarest))
        labels, edges, origin = subdue.compress(labels, edges, found.instances,
                                                "SUB%d" % rank, origin)
    return out
def embeds(graph, sub, instance):
    """True when `instance` (sub vertex i -> graph node) really is `sub` in the graph."""
    present = set(graph.edges)
    if len(set(instance)) != len(instance):  return False
    if any(graph.labels[v] != l for v, l in zip(instance, sub.labels)):  return False
    return all((instance[a], instance[b], k) in present for a, b, k in sub.edges)
def load_records(paths):
    records = {}
    for path in paths:
        record, _ = load(path)
        if record is not None:  records[rel(path)] = record
    return records
