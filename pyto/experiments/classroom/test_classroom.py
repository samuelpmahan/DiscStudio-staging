"""The classroom experiment's suite: the class builds, the page is a function.

Three claims, and each one is the whole point of the file it guards:

  make_class.sh   a class repository and a private desk can be built from nothing,
                  and one command from the class grades the desk with the class's own
                  verifier and writes the score into the landing receipt and the board.
  tutor.py        the tutoring page is a pure function of the desk's own record:
                  the same desk twice is the same bytes, and no absolute path and no
                  clock reading gets onto it.
  cold_reader.py  the cold reader's answer is checked by the same rule grade.py check
                  4 applies to the hand-off, pointed the other way.

The build is done once for the whole suite (setUpClass): it is four seconds of git,
and every test below reads the same class and the same desk, which is also the
honest thing to test -- the desk a tutor reads is the desk a landing left behind.

Mutation-checked, 2026-09-10 (each mutation was made, the suite was run, the named
test failed, the mutation was reverted):

  1. tutor.py `scrub()` made to return its argument unchanged
     -> test_the_page_prints_no_path_from_outside_the_desk FAILED with the desk's
        temp directory in the refusal line ("...the page names /tmp/...").
        Everything else stayed green, so that test is the only thing holding the
        no-absolute-paths claim up.
  2. make_class.sh's grader made to print `score: $passed of $((checks + 1))` -- the
     total widened while the checks stayed as they were
     -> three tests FAILED, and they are three different readings of the same number:
        test_the_landing_receipt_keeps_the_score_and_the_cold_read (the receipt no
        longer says "total": 4), test_the_class_board_records_the_grade (the board
        line no longer says score 4/4) and test_the_selftest_passes (make_class.sh's
        own assertion caught it too). The receipt and the board are written by
        separate code paths in land.sh, so neither test alone is the claim.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PYTO_ROOT = os.path.dirname(os.path.dirname(HERE))
STUDENTS = os.path.join(PYTO_ROOT, "experiments", "students")
MAKE_CLASS = os.path.join(HERE, "make_class.sh")
TUTOR = os.path.join(HERE, "tutor.py")
COLD_READER = os.path.join(HERE, "cold_reader.py")
CANNED_ANSWER = os.path.join(HERE, "cold-reader.txt")
STUDENT_HANDOFF = os.path.join(STUDENTS, "HANDOFF.md")

# The interpreter this suite is running under is the one that can import pyto, and
# the class's grader replays the student's record in a fresh process three levels
# down (make_class.sh -> neat.sh -> land.sh -> grader.sh -> grade.py -> a child).
# Handing it down explicitly is what keeps that child off whatever `python3` on PATH
# happens to be.
ENV = dict(os.environ, PYTHON=sys.executable)


def run(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(
        command, capture_output=True, text=True, env=ENV, timeout=600, **kwargs
    )


class ClassroomTests(unittest.TestCase):
    """One class, one desk, built once."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.mkdtemp(prefix="classroom-suite-")
        cls.dir = os.path.join(cls.tmp, "class-and-desk")
        cls.built = run(["bash", MAKE_CLASS, "--selftest", cls.dir])
        cls.desk = os.path.join(cls.dir, "desk")
        cls.klass = os.path.join(cls.dir, "class")

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def output(self) -> str:
        return self.built.stdout + self.built.stderr

    # --- (a) the class builds and grades itself ----------------------------------

    def test_the_selftest_passes(self):
        """`make_class.sh --selftest` exits 0 with every one of its checks passing."""
        self.assertEqual(
            self.built.returncode, 0,
            "make_class.sh --selftest exited %d:\n%s" % (self.built.returncode, self.output()),
        )
        self.assertIn("selftest: all checks passed", self.output())
        self.assertNotIn(": FAIL", self.output())
        # It has to actually have checked things: an empty selftest also never fails.
        self.assertGreaterEqual(len(re.findall(r"^selftest .*: pass$", self.output(), re.M)), 8)

    def test_the_class_board_records_the_grade(self):
        """The gradebook is the board: one Today line, scored, and marked graded here."""
        with open(os.path.join(self.klass, ".neat", "BOARD.md"), encoding="utf-8") as handle:
            board = handle.read()
        today = [line for line in board.split("## Today", 1)[1].splitlines() if line.startswith("- ")]
        self.assertEqual(len(today), 1, "the class board should hold exactly one landing:\n%s" % today)
        self.assertIn("**landed** `task-0` score 4/4", today[0])
        self.assertIn("graded here", today[0])
        self.assertIn("exp/0", today[0])

    def test_the_landing_receipt_keeps_the_score_and_the_cold_read(self):
        """The receipt is the grade record; the verifier output beside it is the rest."""
        landings = os.path.join(self.klass, ".neat", "landings")
        found = sorted(
            name for name in os.listdir(landings)
            if name.endswith("-task-0") and os.path.isdir(os.path.join(landings, name))
        )
        self.assertTrue(found, "no landing directory for task-0 in %s" % os.listdir(landings))
        with open(os.path.join(landings, found[-1], "receipt.json"), encoding="utf-8") as handle:
            receipt = handle.read()
        self.assertIn('"passed": 4', receipt)
        self.assertIn('"total": 4', receipt)
        self.assertIn('"result": "verified"', receipt)
        with open(os.path.join(landings, found[-1], "verifier.txt"), encoding="utf-8") as handle:
            verifier = handle.read()
        self.assertIn("cold reader: 13 of 13 named", verifier)
        self.assertIn("combined: 17 of 17", verifier)
        self.assertIn("score: 4 of 4", verifier)

    def test_the_submission_landed_under_the_one_allowed_path(self):
        """What the class got, and nothing beside it."""
        submission = os.path.join(self.klass, "submissions", "ada")
        for name in ("homework.py", "HANDOFF.md", "cold-reader.txt",
                     "evidence/run-1/record.json", "evidence/run-1/receipts.json",
                     "evidence/run-1/tick-viewer.html"):
            self.assertTrue(os.path.isfile(os.path.join(submission, *name.split("/"))),
                            "the class is missing submissions/ada/%s" % name)
        # The desk's own tasks and notes are the student's; they do not travel.
        self.assertFalse(os.path.exists(os.path.join(self.klass, "notes")))

    def test_the_desk_is_untouched_by_the_landing(self):
        """Private by default: the class read the desk's branch and wrote nothing."""
        status = run(["git", "-C", self.desk, "status", "--porcelain", "--untracked-files=all"])
        self.assertEqual(status.stdout.strip(), "", "the desk is dirty after the landing")
        self.assertFalse(os.path.exists(os.path.join(self.desk, "assignments")))
        self.assertFalse(os.path.exists(os.path.join(self.desk, "submissions")))

    # --- (b) the tutoring page is a pure function of the desk --------------------

    def render_tutor(self) -> str:
        done = run([sys.executable, TUTOR, self.desk])
        self.assertEqual(done.returncode, 0, "tutor.py exited %d: %s" % (done.returncode, done.stderr))
        return done.stdout

    def test_the_page_is_byte_identical_on_a_rerun(self):
        """Two runs over the same desk are the same bytes, or it is not a function."""
        first, second = self.render_tutor(), self.render_tutor()
        self.assertEqual(first, second, "tutor.py rendered two different pages from one desk")
        self.assertGreater(len(first), 2000)

    def test_the_page_names_the_scores_the_desk_earned(self):
        """The refusal and the retry, with the numbers the verifier printed."""
        page = self.render_tutor()
        self.assertIn("What they retried", page)
        self.assertIn("1/2", page)
        self.assertIn("2/2", page)
        self.assertIn("task-1", page)
        self.assertIn("bash tools/check_notes.sh", page)

    def test_the_page_names_the_question_lines(self):
        """Where they wrote {?}: their packets, their notes, their hand-off."""
        page = self.render_tutor()
        self.assertIn("Where they wrote", page)
        for label in ("Rounding:", "ColdReaderAnswer:", "OneQuestion:", "Ticks:", "Timings:"):
            self.assertIn(label, page, "the page never names the {?} line %r" % label)
        # Once each: neat copies a packet's Uncertain section onto the hand-off it
        # generates, and counting both would double every question a student wrote.
        self.assertEqual(page.count("OneQuestion:"), 1)

    def test_the_page_names_what_they_undid_and_what_they_killed(self):
        page = self.render_tutor()
        self.assertIn("What they undid", page)
        self.assertIn("task-3", page)
        self.assertIn("1 killed", page)

    def test_the_page_shows_how_long_each_tick_took(self):
        """From the submitted record, per Tick, work beside latency."""
        page = self.render_tutor()
        for tick in ("Parse", "Stats", "Letters", "Histogram"):
            self.assertIn(">%s<" % tick, page, "the page never names the Tick %r" % tick)
        self.assertIn("mean, median", page)
        self.assertIn("work ms", page)
        self.assertIn("latency ms", page)

    def test_the_page_prints_no_path_from_outside_the_desk(self):
        """No absolute path, and none of this machine's temp directory."""
        page = self.render_tutor()
        self.assertNotIn(self.tmp, page)
        self.assertNotIn(os.path.abspath(self.desk), page)
        for match in re.findall(r'>[^<]*</', page):
            self.assertNotRegex(match, r"(?<![A-Za-z0-9.])/(tmp|home|Users|var)/")

    def test_the_page_reads_no_clock(self):
        """A page that is a function of the desk cannot call one."""
        with open(TUTOR, encoding="utf-8") as handle:
            source = handle.read()
        for forbidden in ("time.time(", "datetime.now", "utcnow", "os.path.getmtime", "os.stat("):
            self.assertNotIn(forbidden, source, "tutor.py reads a clock: %r" % forbidden)

    # --- (c) the cold reader ------------------------------------------------------

    def read_cold(self, answer_text: str) -> subprocess.CompletedProcess:
        path = os.path.join(self.tmp, "answer.txt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(answer_text)
        return run([sys.executable, COLD_READER, STUDENT_HANDOFF, path])

    def test_a_full_answer_names_every_tick_and_every_file(self):
        """The four Ticks the students page lists, plus the nine files it names."""
        with open(CANNED_ANSWER, encoding="utf-8") as handle:
            answer = handle.read()
        done = self.read_cold(answer)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("ticks: 4 of 4 (Parse, Stats, Letters, Histogram)", done.stdout)
        self.assertIn("files: 9 of 9", done.stdout)
        self.assertIn("cold reader: 13 of 13 named", done.stdout)

    def test_an_answer_that_skips_a_step_is_named_and_refused(self):
        """Leave the Histogram out and the check says so, by name, and exits 1."""
        with open(CANNED_ANSWER, encoding="utf-8") as handle:
            answer = handle.read()
        done = self.read_cold(re.sub(r"(?i)histogram", "the last step", answer))
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("Histogram", done.stdout)
        self.assertIn("the answer never names the Tick 'Histogram'", done.stdout)
        self.assertIn("cold reader: 12 of 13 named", done.stdout)

    def test_an_empty_answer_names_everything_it_left_out(self):
        done = self.read_cold("I did not read it.\n")
        self.assertEqual(done.returncode, 1)
        self.assertIn("cold reader: 0 of 13 named", done.stdout)
        self.assertIn("homework.py", done.stdout)

    def test_the_rule_is_grade_pys_rule(self):
        """The Ticks the cold reader asks for are the Ticks the hand-off lists.

        `grade.py` check 4 requires the hand-off to give every Tick in the record a
        list line of its own; this file requires the reader to name every Tick the
        hand-off lists. If the two ever read that list differently, the assignment
        would be graded by one rule and read by another.
        """
        sys.path.insert(0, HERE)
        sys.path.insert(0, STUDENTS)
        try:
            import cold_reader
            import grade
        finally:
            sys.path.remove(HERE)
            sys.path.remove(STUDENTS)
        with open(STUDENT_HANDOFF, encoding="utf-8") as handle:
            text = handle.read()
        self.assertEqual(cold_reader.tick_list_lines(text), grade.tick_list_lines(text))
        for name in cold_reader.tick_names(text):
            self.assertTrue(
                any(grade.names_tick(bullet, name) for bullet in grade.tick_list_lines(text)),
                "grade.py would not accept the Tick name %r that cold_reader.py read out" % name,
            )


if __name__ == "__main__":
    unittest.main()
