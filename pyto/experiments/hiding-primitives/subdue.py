"""A small SUBDUE (Cook and Holder, JAIR 1994, cs/9402102).  Candidates are grown by beam
search from single labelled nodes; instances are found by labelled subgraph isomorphism (a
backtracking matcher -- the graphs are small); each is scored by minimum description length,
DL(G) - (DL(S) + DL(G|S)), where G|S replaces every instance with one node and is charged
for every edge that replacement destroyed, so DL(S) + DL(G|S) still accounts for all of G.
The best of an iteration is kept, the graph is compressed by it, and the search runs
again: the paper's iterative compression.  Beam width, iterations and the minimum
instance count are arguments."""
from __future__ import annotations
import itertools
from collections import namedtuple
from math import log2
Sub = namedtuple("Sub", "labels edges")            # labels[i], (i, j, kind) edges
Found = namedtuple("Found", "sub instances value ratio")
def index_graph(labels, edges):
    """Out/in adjacency, an edge set for O(1) tests, and label -> vertices."""
    out, inn, present, by_label = [[] for _ in labels], [[] for _ in labels], set(), {}
    for src, dst, kind in edges:
        out[src].append((dst, kind))
        inn[dst].append((src, kind))
        present.add((src, dst, kind))
    for vertex, label in enumerate(labels):
        by_label.setdefault(label, []).append(vertex)
    return {"labels": labels, "out": out, "in": inn, "set": present, "by": by_label}
def canon(labels, edges):
    """Canonical form: the lexicographic minimum over all vertex permutations."""
    best = None
    for perm in itertools.permutations(range(len(labels))):
        key = (tuple(labels[perm.index(i)] for i in range(len(labels))),
               tuple(sorted((perm[a], perm[b], k) for a, b, k in edges)))
        best = key if best is None or key < best else best
    return Sub(*best)
def _plan(sub):
    """Match order: vertex 0, then always a vertex tied to an already-matched one."""
    order, placed = [(0, None, None, True)], {0}
    while len(placed) < len(sub.labels):
        for src, dst, kind in sub.edges:
            if src in placed and dst not in placed:
                order.append((dst, src, kind, True)); placed.add(dst); break
            if dst in placed and src not in placed:
                order.append((src, dst, kind, False)); placed.add(src); break
        else:                                       # a disconnected piece
            spare = min(set(range(len(sub.labels))) - placed)
            order.append((spare, None, None, True)); placed.add(spare)
    return order
def match_all(idx, sub, limit=20000):
    """Every injective label-preserving embedding of `sub`, by backtracking."""
    order, size = _plan(sub), len(sub.labels)
    mapping, used, results = [-1] * size, set(), []
    def step(depth):
        if len(results) >= limit:  return
        if depth == size:
            results.append(tuple(mapping)); return
        vertex, anchor, kind, forward = order[depth]
        if anchor is None:
            cands = idx["by"].get(sub.labels[vertex], ())
        else:
            side = idx["out"][mapping[anchor]] if forward else idx["in"][mapping[anchor]]
            cands = [w for w, k in side if k == kind]
        seen = set()
        for cand in cands:
            if cand in used or cand in seen or idx["labels"][cand] != sub.labels[vertex]:
                continue
            seen.add(cand)
            ok = True
            for src, dst, kind2 in sub.edges:
                if src == vertex and mapping[dst] >= 0:
                    ok = (cand, mapping[dst], kind2) in idx["set"]
                elif dst == vertex and mapping[src] >= 0:
                    ok = (mapping[src], cand, kind2) in idx["set"]
                if not ok:
                    break
            if ok:
                mapping[vertex] = cand; used.add(cand)
                step(depth + 1)
                used.discard(cand); mapping[vertex] = -1
    step(0)
    return results
def find_instances(idx, sub, limit=20000):
    """A maximal vertex-disjoint set of instances, taken in match order."""
    chosen, taken = [], set()
    for match in match_all(idx, sub, limit):
        if not any(vertex in taken for vertex in match):
            chosen.append(match); taken.update(match)
    return chosen
def compress(labels, edges, instances, new_label, origin=None):
    """Replace each instance with one node.  Returns (labels, edges, origin)."""
    origin = [(v,) for v in range(len(labels))] if origin is None else origin
    ids, new_labels, new_origin = {}, [], []
    member = {v: rank for rank, inst in enumerate(instances) for v in inst}
    for rank, instance in enumerate(instances):
        ids[("i", rank)] = len(new_labels); new_labels.append(new_label)
        new_origin.append(tuple(sorted({v for w in instance for v in origin[w]})))
    for vertex in (v for v in range(len(labels)) if v not in member):
        ids[("v", vertex)] = len(new_labels); new_labels.append(labels[vertex])
        new_origin.append(origin[vertex])
    pick = lambda v: ids[("i", member[v])] if v in member else ids[("v", v)]
    new_edges, seen = [], set()
    for src, dst, kind in edges:
        if src in member and dst in member and member[src] == member[dst]:
            continue                                # internal to one instance
        edge = (pick(src), pick(dst), kind)
        if edge[0] != edge[1] and edge not in seen:
            seen.add(edge); new_edges.append(edge)
    return new_labels, new_edges, new_origin
def dl(vertices, edges, label_count, kind_count, vertex_ref):
    """Bits for the vertex labels plus the edge list.  Edge endpoints are paid at a fixed
    width (`vertex_ref`, the graph's size before compression), so shrinking a graph never
    cheapens its remaining edges.  Together with `score` charging the edges compression
    drops (`lost` there), the edge count is conserved across DL(S) + DL(G|S): the per-edge
    cost cancels, and a one-instance "substructure" is left paying one extra vertex label
    and two extra list headers, so it cannot compress."""
    return (log2(vertices + 1) + vertices * log2(max(label_count, 2)) + log2(edges + 1)
            + edges * (2 * log2(max(vertex_ref, 2)) + log2(max(kind_count, 2))))
def score(labels, edges, sub, instances, vertex_ref=None):
    """(bits saved, compressed/original ratio) for replacing `instances` by `sub`."""
    nl, nk = len(set(labels)), len(set(kind for _, _, kind in edges))
    vertex_ref = len(labels) if vertex_ref is None else vertex_ref
    whole = dl(len(labels), len(edges), nl, nk, vertex_ref)
    part = dl(len(sub.labels), len(sub.edges), nl, nk, vertex_ref)
    small_labels, small_edges, _ = compress(labels, edges, instances, "SUB")
    lost = len(edges) - len(small_edges) - len(instances) * len(sub.edges)
    rest = dl(len(small_labels), len(small_edges) + lost, nl, nk, vertex_ref)
    return whole - (part + rest), (part + rest) / whole
def extensions(idx, sub, instances):
    """Every one-edge growth of `sub` seen in its instances, with raw counts."""
    counts = {}
    for instance in instances:
        for pos, vertex in enumerate(instance):
            for forward, side in ((True, idx["out"][vertex]), (False, idx["in"][vertex])):
                for other, kind in side:
                    if other in instance:
                        mate = instance.index(other)
                        edge = (pos, mate, kind) if forward else (mate, pos, kind)
                        if edge in sub.edges:  continue
                        grown = Sub(sub.labels, tuple(sorted(sub.edges + (edge,))))
                    else:
                        fresh = len(sub.labels)
                        edge = (pos, fresh, kind) if forward else (fresh, pos, kind)
                        grown = Sub(sub.labels + (idx["labels"][other],),
                                    tuple(sorted(sub.edges + (edge,))))
                    key = canon(grown.labels, grown.edges)
                    counts[key] = counts.get(key, 0) + 1
    return counts
def best_substructure(labels, edges, beam=4, min_instances=2, max_size=5, probe=16,
                      vertex_ref=None):
    """The best-compressing connected substructure, by beam search from singletons."""
    idx, best = index_graph(labels, edges), None
    frontier = [Sub((label,), ()) for label in sorted(idx["by"])
                if len(idx["by"][label]) >= min_instances]
    while frontier:
        counts, scored = {}, []
        for sub in frontier:
            for cand, seen in extensions(idx, sub, find_instances(idx, sub)).items():
                counts[cand] = max(counts.get(cand, 0), seen)
        for cand, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:probe]:
            instances = find_instances(idx, cand)
            if len(instances) >= min_instances:
                bits, ratio = score(labels, edges, cand, instances, vertex_ref)
                scored.append(Found(cand, instances, bits, ratio))
        if not scored:  break
        scored.sort(key=lambda f: (-f.value, f.sub))
        best = scored[0] if best is None or scored[0].value > best.value else best
        frontier = [f.sub for f in scored[:beam] if len(f.sub.labels) < max_size]
    return best
def mine(labels, edges, iterations=10, beam=4, min_instances=2, max_size=5, probe=16):
    """`iterations` rounds of: keep the best substructure, compress the graph by it.
    Returns [(Found, instances as original vertex ids)], one entry per round."""
    results, origin = [], [(v,) for v in range(len(labels))]
    vertex_ref, cur_labels, cur_edges = len(labels), list(labels), list(edges)
    for round_no in range(1, iterations + 1):
        found = best_substructure(cur_labels, cur_edges, beam, min_instances, max_size,
                                  probe, vertex_ref)
        if found is None or found.value <= 0.0:  break
        results.append((found, [tuple(sorted({v for w in inst for v in origin[w]}))
                                for inst in found.instances]))
        cur_labels, cur_edges, origin = compress(cur_labels, cur_edges, found.instances,
                                                 "SUB%d" % round_no, origin)
    return results
