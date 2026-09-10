import json, os, shutil, subprocess, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mine, molecules, transitions  # noqa: E402
STUDENTS = os.path.join(molecules.PYTO, "experiments", "students", "evidence", "run-1", "record.json")
class TestGraph(unittest.TestCase):
    def test_students_graph(self):
        g = molecules.build_graph([STUDENTS], "exact")
        # 5 invocations + 6 Parts (scores_csv, roster, mean, median, letters, histogram)
        self.assertEqual(len(g.labels), 11)
        # reads: parse<-csv, mean<-roster, median<-roster, letters<-roster, histogram<-letters (5)
        # writes: 5; next: mean->median (1)
        self.assertEqual(len(g.edges), 11)
        self.assertEqual(sum(1 for e in g.edges if e[2] == "next"), 1)
        node = {w[2]: i for i, w in enumerate(g.where)}
        roster = node["px.students.roster"]
        for inv in ("mean", "median"):
            self.assertIn((roster, node[inv], "reads"), g.edges)
        self.assertIn((node["mean"], node["median"], "next"), g.edges)
        shape = molecules.build_graph([STUDENTS], "shape")
        self.assertEqual(shape.labels[node["mean"]], "fn/1->1")
        self.assertEqual(shape.labels[roster], "part")
class TestMining(unittest.TestCase):
    def test_report_is_deterministic(self):
        self.assertEqual(mine.build_report(), mine.build_report())
    def test_every_instance_embeds_and_documents_obey_the_chain_rule(self):
        for scheme in mine.SCHEMES:
            graph, found = mine.collect(scheme)
            self.assertTrue(found)
            for mol in found:
                self.assertGreaterEqual(len(mol.instances), 2)
                if mol.note:  continue
                for inst in mol.instances:
                    self.assertTrue(molecules.embeds(graph, mol.sub, inst), (scheme, mol.rank, inst))
                self.assertEqual(molecules.chain_rule(mol.document), [])
                calcs = mol.document["Ticks"][0]["Calculations"]
                self.assertTrue(all(c["call"] and c["into"] for c in calcs))
    def test_chain_rule_catches_a_backwards_read(self):
        doc = {"Ticks": [{"name": "t", "Calculations": [
            {"call": "fn.a", "with": {"x": "p.b"}, "into": "p.a"},
            {"call": "fn.b", "with": {"x": "p.in"}, "into": "p.b"}]}]}
        self.assertTrue(molecules.chain_rule(doc))
        doc["Ticks"][0]["Calculations"][1]["into"] = "p.a"
        self.assertTrue(any("two producers" in f for f in molecules.chain_rule(doc)))
    def test_rarest_transition_bound_holds_for_every_molecule(self):
        # Every instance of `mol.sub` is one vertex-disjoint occurrence of every one of
        # its edges, so no edge in it can be counted, over the graph it was mined from,
        # fewer times than there are instances -- rarest is a lower bound, not a guess.
        for scheme in mine.SCHEMES:
            _, found = mine.collect(scheme)
            self.assertTrue(found)
            for mol in found:
                if mol.rarest is None:  continue
                self.assertGreaterEqual(mol.rarest, len(mol.instances), (scheme, mol.rank))
class TestTransitions(unittest.TestCase):
    def test_counts_sum_equals_the_graphs_edge_count(self):
        paths = mine.record_paths()
        graph = molecules.build_graph(paths, "exact")
        counted = transitions.transitions({"paths": paths})
        self.assertEqual(counted["total"], len(graph.edges))
        self.assertEqual(sum(e["count"] for e in counted["edges"]), len(graph.edges))
    def test_same_records_same_table(self):
        paths = mine.record_paths()
        first = transitions.transitions({"paths": paths})
        second = transitions.transitions({"paths": paths})
        self.assertEqual(
            json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
    def test_edges_are_sorted_by_count_then_from_to_kind(self):
        counted = transitions.transitions({"paths": mine.record_paths()})
        keys = [(-e["count"], e["from"], e["to"], e["kind"]) for e in counted["edges"]]
        self.assertEqual(keys, sorted(keys))
    def test_part_digest_matches_the_one_digest_rule(self):
        value = transitions.transitions({"paths": mine.record_paths()})
        part = transitions.to_part(value)
        self.assertEqual(part["address"], transitions.ADDRESS)
        self.assertEqual(part["sha256"], transitions.digest_of(value))
class TestCheck(unittest.TestCase):
    def run_check(self, *args):
        return subprocess.run([sys.executable, os.path.join(HERE, "mine.py"), "--check", *args],
                              capture_output=True, text=True).returncode
    def test_check_passes_on_committed_report_and_fails_on_one_byte(self):
        self.assertEqual(self.run_check(), 0)
        with tempfile.TemporaryDirectory() as tmp:
            copy = os.path.join(tmp, "report.md")
            shutil.copy(mine.REPORT, copy)
            with open(copy, "rb") as handle:
                data = handle.read()
            with open(copy, "wb") as handle:
                handle.write(data[:-1] + (b"X" if data[-1:] != b"X" else b"Y"))
            self.assertNotEqual(self.run_check(copy), 0)
if __name__ == "__main__":  unittest.main()
