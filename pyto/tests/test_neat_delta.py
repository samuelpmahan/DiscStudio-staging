"""Executable spec of neat delta (task 80): two landings' capability delta against cost.

A scratch git repository with two landings is built here: landing A adds a page
beside an existing thing (a route, a new address root, an assertion moved, a
fixture regenerated); landing B refines the thing and tears A's page out. The
measurement is over that history, the evaluation over the measurement, and the
verdict is what the owner said it obviously is: the refinement, at lower cost,
with A's lines counted as rework.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest

from pyto.neat import delta as D


def git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, check=True).stdout.strip()


def write(root, path, text):
    full = os.path.join(root, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as handle:
        handle.write(text)


def commit(root, message):
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)
    return git(root, "rev-parse", "HEAD")


def landing(root, landing_id, package, base, verifier_pass, counts):
    d = os.path.join(root, D.LANDINGS_DIR, landing_id)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "receipt.json"), "w", encoding="utf-8") as handle:
        json.dump({"schema": "pyto-landing-receipt@1", "id": landing_id, "package": package, "base_sha": base,
                   "result": "verified", "check_all": {"exit": 0, "counts": counts}, "result_sha": None}, handle)
    with open(os.path.join(d, "verifier.txt"), "w", encoding="utf-8") as handle:
        handle.write(f"ok 1 - x\n# pass {verifier_pass}\n# fail 0\n")


class DeltaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.root = self.tmp.name
        git(root, "init", "-q", "-b", "main")
        git(root, "config", "user.email", "t@example.com")
        git(root, "config", "user.name", "t")
        write(root, "src/app.js", "const ui = { route: 'shelf' };\nui.route = ['shelf', 'components'].includes(x) ? x : 'shelf';\nbutton('a', 'preset-color');\n// data-control=\"preset-color\"\n")
        write(root, "src/runtime.js", "register('fn.card.compose', composeCard);\npxc.set('px.presentation.x', p);\n")
        write(root, "tests/a.test.js", "assert.equal(count, 14);\n")
        write(root, "tests/fixtures/run.json", "{\"v\": 1}\n")
        write(root, "pyto/experiments/tasks/0/packet.md", "evidence\n")
        base = commit(root, "start")
        # Landing A: a page beside the composer, a new address root, a moved assertion, a fixture regenerated.
        write(root, "src/app.js", "const ui = { route: 'shelf' };\nui.route = ['shelf', 'components', 'cards'].includes(x) ? x : 'shelf';\nbutton('a', 'preset-color');\n// data-control=\"preset-color\"\nfunction cardsPage() { return `<input data-control=\"cascade-token\"><button data-action=\"cascade-reset\">`; }\n")
        write(root, "src/runtime.js", "register('fn.card.compose', composeCard);\npxc.set('px.presentation.x', p);\nregister('fn.cards.effective', eff);\nregister('fn.cards.apply', app);\npxc.set('px.discstudio.cards.global', g);\nqueryPrefix(pxc, 'px.discstudio.cards.instance.*');\n")
        write(root, "tests/a.test.js", "assert.equal(count, 20);\n")
        write(root, "tests/fixtures/run.json", "{\"v\": 2}\n")
        write(root, "pyto/experiments/tasks/1/packet.md", "evidence A\n")
        a = commit(root, "land(task-1): a page beside\n\nLanding receipt: pyto/experiments/landings/20260910T000000Z-task-1/receipt.json")
        landing(root, "20260910T000000Z-task-1", "task-1", base, 57, {"library": 10})
        commit(root, "receipt A: 20260910T000000Z-task-1")
        # Landing B: the composer refined; A's page torn out; no new page, no new root beyond what stays.
        write(root, "src/app.js", "const ui = { route: 'shelf' };\nui.route = ['shelf', 'components'].includes(x) ? x : 'shelf';\nbutton('a', 'preset-color');\n// data-control=\"preset-color\"\n// data-action=\"cascade-reset\" in the whole-card section\n")
        write(root, "src/runtime.js", "register('fn.card.compose', composeCard);\npxc.set('px.presentation.x', p);\nregister('fn.cards.effective', eff);\nregister('fn.cards.apply', app);\npxc.set('px.discstudio.cards.global', g);\nqueryPrefix(pxc, 'px.discstudio.cards.instance.*');\n")
        write(root, "pyto/experiments/tasks/2/packet.md", "evidence B\n")
        b = commit(root, "land(task-2): refined\n\nLanding receipt: pyto/experiments/landings/20260910T010000Z-task-2/receipt.json")
        landing(root, "20260910T010000Z-task-2", "task-2", a, 58, {"library": 10})
        commit(root, "receipt B: 20260910T010000Z-task-2")
        self.base, self.a, self.b = base, a, b

    def tearDown(self):
        self.tmp.cleanup()

    def test_measure_reads_the_receipt_and_the_diff_and_excludes_evidence(self):
        m = D.measure(self.root, "1")
        self.assertEqual((m["package"], m["base_sha"], m["result_sha"]), ("task-1", self.base, self.a))
        self.assertEqual(m["verified"], {"verifier": 57, "check_all": 10})
        self.assertEqual(m["files"], 4, "the packet under pyto/experiments/tasks is excluded")
        self.assertEqual(m["patterns"]["calculations"], {"added": 2, "removed": 0})
        self.assertEqual(m["patterns"]["actions"]["added"], 1, "one added line carries data-control/data-action")
        self.assertEqual(m["patterns"]["queries"], {"added": 1, "removed": 0})
        self.assertEqual(m["patterns"]["pages"], {"added": 1, "removed": 1}, "the route list line moved")
        self.assertEqual(m["patterns"]["moved_assertions"], {"added": 1, "removed": 1})
        self.assertEqual(m["address_roots"], ["px.discstudio.cards"])
        self.assertEqual(m["fixtures"], ["tests/fixtures/run.json"])

    def test_the_pair_measures_end_states_and_rework(self):
        pair = D.measure_pair(self.root, "1", "2")
        self.assertEqual(pair["composite"]["base_sha"], self.base)
        self.assertEqual(pair["composite"]["result_sha"], self.b)
        self.assertEqual(pair["composite"]["patterns"]["pages"], {"added": 0, "removed": 0}, "after both, no page was added")
        self.assertEqual(pair["rework"], 2, "B removed the two lines A added for its page")
        self.assertNotIn("_added_lines", pair["a"])

    def test_evaluate_is_pure_and_prefers_more_verified_then_cheaper(self):
        pair = D.measure_pair(self.root, "1", "2")
        part = D.evaluate(pair)
        again = D.evaluate(json.loads(json.dumps(pair)))
        self.assertEqual(part, again)
        self.assertEqual(part["address"], "px.exp.neat.delta.task-1.task-2")
        after_a, after_b = part["end_states"]["after_a"], part["end_states"]["after_b"]
        self.assertEqual(after_a["capability"]["verified"], 67)
        self.assertEqual(after_b["capability"]["verified"], 68)
        self.assertLess(after_b["cost"]["total"], after_a["cost"]["total"])
        self.assertEqual(after_a["cost"]["pages"], 2)
        self.assertEqual(after_b["cost"]["pages"], 0)
        self.assertEqual(part["verdict"], "b")
        self.assertIn("2 lines a had added", part["reason"])
        # At equal verified behaviour the cheaper end state still wins.
        tied = json.loads(json.dumps(pair)); tied["b"]["verified"]["verifier"] = 57; tied["composite"]["verified"]["verifier"] = 57
        self.assertEqual(D.evaluate(tied)["verdict"], "b")

    def test_the_cli_writes_the_part_and_its_record(self):
        out = os.path.join(self.root, "deltas")
        code = D.main(["1", "2", "--root", self.root, "--out-dir", out])
        self.assertEqual(code, 0)
        with open(os.path.join(out, "task-1-task-2.json"), encoding="utf-8") as handle:
            part = json.load(handle)
        self.assertEqual(part["verdict"], "b")
        with open(os.path.join(out, "task-1-task-2.record.json"), encoding="utf-8") as handle:
            record = json.load(handle)
        self.assertTrue(any("fn.neat.delta.evaluate" in json.dumps(t) for t in record.get("ticks", [])), "the run record names the Calculation")
        self.assertIn("verdict: b", D.table(part))


if __name__ == "__main__":
    unittest.main()
