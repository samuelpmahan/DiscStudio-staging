"""The walk: every landing on the board is a step, the page is the same bytes twice, and it carries
the seven words, no absolute path and no CR byte. walk.py is imported by path; git is read once per
build (one log pass over every landing commit), so the whole suite stays well under 40 seconds."""
from __future__ import annotations

import importlib.util
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PYTO = os.path.dirname(HERE)
ROOT = os.path.dirname(PYTO)

spec = importlib.util.spec_from_file_location("walk", os.path.join(PYTO, "scripts", "walk.py"))
walk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(walk)

SEVEN = ["Part", "PxC", "Calculation", "PCR and Tick", "receipt", "PQL", "neat"]


class TheWalk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.steps, cls.problems = walk.build_steps()
        cls.page = walk.build_page(cls.steps)

    def test_check_passes_on_this_tree(self):
        self.assertEqual(self.problems, [])
        self.assertEqual(walk.main(["--check"]), 0)

    def test_every_landed_line_is_a_step(self):
        with open(os.path.join(PYTO, "BOARD.md"), encoding="utf-8") as f:
            today = f.read().split("\n## Today", 1)[1]
        landed = [l for l in today.splitlines() if walk.LANDED.match(l)]
        self.assertGreater(len(landed), 0)
        self.assertEqual(len(self.steps), len(landed))
        self.assertEqual([s["n"] for s in self.steps], list(range(1, len(landed) + 1)))
        self.assertEqual(self.page.count('<section class="step"'), len(landed))
        for s in self.steps:
            self.assertIsNotNone(s["receipt"], s["package"])
            self.assertIsNotNone(s["commit"], s["package"])

    def test_same_bytes_twice(self):
        again = walk.build_page(walk.build_steps()[0])
        self.assertEqual(self.page, again)

    def test_text_for_task_55_names_its_files_and_a_concept(self):
        step = next(s for s in self.steps if s["package"] == "task-55")
        text = walk.step_text(step, len(self.steps))
        for path in ("pyto/tests/test_use.py", "pyto/tests/test_parallel.py"):
            self.assertIn(path, text)
        concepts = text.split("concepts touched:\n", 1)[1].split("files changed", 1)[0]
        self.assertTrue(any(re.match(r"  [\w ]+: ", l) for l in concepts.splitlines()))
        self.assertTrue(text.endswith(f"next: python scripts/walk.py --text {step['n'] + 1}\n"))
        self.assertIn("To undo this one, say: undo task 55", text)
        self.assertTrue(all(len(l) <= 100 for l in text.splitlines() if not l.startswith(("diff: ", "  +"))))

    def test_strip_names_all_seven(self):
        strip = self.page.split('<div class="pin">', 1)[1].split("</div>", 1)[0]
        for name in SEVEN:
            self.assertIn(f"<dt>{name}</dt>", strip)
        for s in self.steps:
            for c in s["concepts"]:
                self.assertTrue(c in walk.DEFINITION or c in walk.OTHER, c)

    def test_no_absolute_path_and_no_cr(self):
        self.assertNotIn("\r", self.page)
        self.assertNotIn(ROOT, self.page)
        self.assertIsNone(re.search(r"(?<![\w/.])/(?:home|Users|root|tmp)/", self.page))
        self.assertIsNone(re.search(r"(?<![\w/.])[A-Za-z]:[/\\]", self.page))


if __name__ == "__main__":
    unittest.main()
