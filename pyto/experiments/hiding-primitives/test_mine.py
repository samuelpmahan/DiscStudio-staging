#!/usr/bin/env python3
"""Tests for the miner, mutation-checked: each mutation below is named, applied to a fresh
copy of the module (the file on disk is never touched, so restoring is running the same
check against the real module again), and has to break the check it names."""
import ast, os, types, unittest
import graphs, mine, subdue
HERE = os.path.dirname(os.path.abspath(__file__))
NOISE = ["N%d" % i for i in range(6)]
def snippet(g, source):
    builder = g.Builder("m", "f", ["math"])
    builder.body(ast.parse(source).body[0].body, None)
    return builder.g
def mutant(filename, old, new):
    """The module with one edit, executed into a namespace of its own."""
    path = os.path.join(HERE, filename)
    source = open(path, encoding="utf-8").read()
    assert old in source, "mutation target is gone from %s" % filename
    module = types.ModuleType(filename[:-3] + "_mutant"); module.__file__ = path
    exec(compile(source.replace(old, new, 1), path, "exec"), module.__dict__)
    return module
def check_arity_label(g):
    assert "math.cos/1" in snippet(g, "def f():\n    x = math.cos(1)\n").labels
def check_next_edge(g):
    assert (0, 1, "next") in snippet(g, "def f():\n    a()\n    b()\n").edges
def check_disjoint(s):
    idx = s.index_graph(["A", "A", "A"], [(0, 1, "next"), (1, 2, "next")])
    seen = [v for m in s.find_instances(idx, s.Sub(("A", "A"), ((0, 1, "next"),))) for v in m]
    assert len(seen) == len(set(seen)), "instances overlap"
def check_one_instance_does_not_pay(s):
    """No substructure with one instance compresses -- including one whose instance carries
    edges beyond `sub.edges`, which `compress` also deletes and `score` therefore charges."""
    labels, sub = ["A", "B"] + NOISE, s.Sub(("A", "B"), ((0, 1, "next"),))
    edges = [(0, 1, "next")] + [(i, i + 1, "next") for i in range(2, len(labels) - 1)]
    bits, _ = s.score(labels, edges, sub, s.find_instances(s.index_graph(labels, edges), sub))
    assert bits <= 0.0, "one instance scored as compression"
    thick = ["A", "B", "C", "D", "C", "D"]                 # A->B carries four extra edges
    twisted = [(0, 1, "next"), (1, 0, "arg"), (0, 1, "in"), (1, 0, "k4"), (0, 1, "k5"),
               (2, 3, "next"), (4, 5, "next")]
    idx = s.index_graph(thick, twisted)
    one = s.find_instances(idx, sub)
    two = s.find_instances(idx, s.Sub(("C", "D"), ((0, 1, "next"),)))
    assert len(one) == 1 and len(two) == 2
    lonely = s.score(thick, twisted, sub, one)[0]
    paired = s.score(thick, twisted, s.Sub(("C", "D"), ((0, 1, "next"),)), two)[0]
    assert lonely <= 0.0, "one instance with extra internal edges scored as compression"
    assert paired > lonely, "one instance outranked two of the same size"
def check_matcher_reads_labels(s):
    idx = s.index_graph(["A", "B", "A", "C"], [(0, 1, "next"), (2, 3, "next")])
    assert len(s.find_instances(idx, s.Sub(("A", "B"), ((0, 1, "next"),)))) == 1
MUTATIONS = [
    ("arity-bucket-dropped", "graphs.py",
     'return "%s/%s" % (self.callee(node), count if count < 3 else "3+")',
     "return self.callee(node)", check_arity_label),
    ("next-edges-dropped", "graphs.py",
     'self.g.link(container, entry, "in"); self.g.link(prev, entry, "next")',
     'self.g.link(container, entry, "in")', check_next_edge),
    ("instances-may-overlap", "subdue.py",
     "if not any(vertex in taken for vertex in match):", "if True:", check_disjoint),
    ("substructure-cost-ignored", "subdue.py",
     "return whole - (part + rest), (part + rest) / whole",
     "return whole - rest, (part + rest) / whole", check_one_instance_does_not_pay),
    ("dropped-edges-uncharged", "subdue.py",
     "lost = len(edges) - len(small_edges) - len(instances) * len(sub.edges)",
     "lost = 0", check_one_instance_does_not_pay),
    ("matcher-ignores-labels", "subdue.py",
     'if cand in used or cand in seen or idx["labels"][cand] != sub.labels[vertex]:',
     "if cand in used or cand in seen:", check_matcher_reads_labels),
]
class Miner(unittest.TestCase):
    def test_two_instances_pay_and_one_does_not(self):
        labels = ["A", "B", "A", "B"] + NOISE
        edges = [(0, 1, "next"), (2, 3, "next")] + [(i, i + 1, "next")
                                                    for i in range(4, len(labels) - 1)]
        sub = subdue.Sub(("A", "B"), ((0, 1, "next"),))
        idx = subdue.index_graph(labels, edges)
        instances = subdue.find_instances(idx, sub)
        self.assertEqual(len(instances), 2)
        self.assertGreater(subdue.score(labels, edges, sub, instances)[0], 0.0)
        check_one_instance_does_not_pay(subdue)
    def test_instances_survive_relabelling_of_unrelated_nodes(self):
        labels = ["A", "B", "A", "B"] + NOISE
        edges = [(0, 1, "next"), (2, 3, "next"), (1, 4, "arg"), (5, 3, "arg")]
        sub = subdue.Sub(("A", "B"), ((0, 1, "next"),))
        before = subdue.find_instances(subdue.index_graph(labels, edges), sub)
        renamed = labels[:4] + ["Z%d" % i for i in range(len(NOISE))]
        after = subdue.find_instances(subdue.index_graph(renamed, edges), sub)
        self.assertEqual(before, after)
        self.assertEqual(len(after), 2)
    def test_planted_motif_is_the_top_result(self):
        labels, edges = [], []
        for copy in range(6):                      # six A->B->C chains, one noise tail each
            base = len(labels); labels += ["A", "B", "C", "N%d" % copy]
            edges += [(base, base + 1, "next"), (base + 1, base + 2, "next"),
                      (base + 2, base + 3, "arg")]
        top = subdue.mine(labels, edges, iterations=1)[0][0]
        self.assertEqual(top.sub, subdue.canon(("A", "B", "C"),
                                               ((0, 1, "next"), (1, 2, "next"))))
        self.assertEqual(len(top.instances), 6)
    def test_the_report_is_deterministic(self):
        self.assertEqual(mine.build_report(), mine.build_report())
    def test_reads_stay_inside_the_studio(self):
        seen, real = [], open
        def spy(path, *args, **kwargs):
            seen.append(os.path.abspath(path)); return real(path, *args, **kwargs)
        graphs.open = mine.open = spy
        try:
            mine.build_report()
        finally:
            del graphs.open, mine.open
        self.assertTrue(seen)
        for path in seen:
            self.assertTrue(path.startswith(graphs.STUDIO + os.sep), path)
class Mutations(unittest.TestCase):
    def test_every_mutation_is_killed(self):
        real = {"graphs.py": graphs, "subdue.py": subdue}
        for name, filename, old, new, check in MUTATIONS:
            with self.subTest(mutation=name):
                check(real[filename])                          # holds on the real module
                with self.assertRaises(AssertionError):
                    check(mutant(filename, old, new))          # and not on the mutant
                check(real[filename])                          # nothing on disk changed
if __name__ == "__main__":  unittest.main()
