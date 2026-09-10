"""Tests for the students experiment: the homework, and the four checks that grade it.

Every test says in its docstring which line it guards, and each of the four
mechanical checks is exercised twice -- once passing on the committed evidence,
once failing on a single engineered defect -- so a check that stopped checking
anything is caught rather than reported green.

Mutation-checked claims (one-line edits applied to a scratch copy, never to the
repository; see pyto/experiments/tasks/23/packet.md):

    grade.py:compared drops duration_ms and nothing else   -> also drop
        `result_sha256` and TamperedRecord.test_flipping_one_result_digest_fails_the_replay
        stops failing: killed.
    grade.py:check_handoff looks for a Tick's own list      -> loosen `missing_ticks`
        line, not the Tick's name anywhere on the page          in `def check_handoff`
        back to the task-29 rule (`name not in handoff_text`) and Handoff.test_a_-
        missing_stats_line_fails_check_four_even_though_the_prose_says_stats stops
        failing -- the Stats bullet is gone, but "Stats" is still in the prose below
        it: killed.
    grade.py:names_tick wants the bullet to *start* with    -> loosen the `return` of
        the Tick's name, not merely contain it                  `def names_tick` to a
        substring test (`return name in bullet`) and Handoff.test_the_three_accepted_-
        bullet_forms_and_nothing_else fails on "*Mean* and *Median* live in Stats":
        killed.
    grade.py:check_handoff tests the Tick names at all       -> compare against an
        empty list of Ticks and both Handoff missing-Tick tests stop failing: killed.
    homework.py:parse_scores sorts the roster by name       -> return the rows
        unsorted and CommittedEvidence.test_grade_exits_zero_on_the_committed_evidence
        fails on check 2 (the fresh process no longer reproduces the record): killed.
    homework.py:build_program puts mean and median in one   -> name them "Mean" and
        Tick                                                   "Median" again, re-run
        `python homework.py --out evidence/run-1`, and TickLaws.test_the_stats_tick_-
        does_more_work_than_it_takes_time fails (there is no Stats Tick, and no Tick
        has work above latency): killed.
    homework.py:build_program's mean and median do not read -> bind `mean=MEAN` on the
        each other                                             median invocation, re-run,
        and the same test fails: Stats is then a chain (tick_laws reports its mode as
        `chain`, not a violation, and its latency equals its work), so
        `assertGreater(stats["work_ms"], stats["latency_ms"])` fails: killed.
"""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
PYTO_ROOT = os.path.dirname(os.path.dirname(HERE))
VIEWER_TEST_DIR = os.path.join(PYTO_ROOT, "viewer", "test")
TICK_LAWS_DIR = os.path.join(PYTO_ROOT, "experiments", "tick-laws")

# Three intra-repo sys.path inserts, stated and printed so they appear in the suite log
# (pyto/experiments/CAPTURE.md, "sys.path: what is logged and what is forbidden").
# tick-laws is imported by path for the same reason grade.py imports the validator by
# path: the directory name has a hyphen in it, so it is not an importable package.
for _directory, _why in (
    (HERE, "this experiment's own homework.py and grade.py"),
    (VIEWER_TEST_DIR, "the independent record validator (record_schema.py)"),
    (TICK_LAWS_DIR, "the Tick node/loop law checker (tick_laws.py)"),
):
    if _directory not in sys.path:
        print(f"[students/test] sys.path.insert(0, {_directory!r})  # intra-repo: {_why}", file=sys.stderr)
        sys.path.insert(0, _directory)

from pyto import PxC  # noqa: E402
from pyto.pcr import receipt_address  # noqa: E402

import grade  # noqa: E402
import homework  # noqa: E402
import tick_laws  # noqa: E402
from record_schema import validate as validate_record  # noqa: E402

RUN_1 = os.path.join(HERE, "evidence", "run-1")
HANDOFF = os.path.join(HERE, "HANDOFF.md")


def run_grade(run_dir: str, handoff: str) -> subprocess.CompletedProcess:
    """`python grade.py --run <run_dir> --handoff <handoff>` as its own process."""
    return subprocess.run(
        [sys.executable, os.path.join(HERE, "grade.py"), "--run", run_dir, "--handoff", handoff],
        capture_output=True, text=True, timeout=300,
    )


class RecordShape(unittest.TestCase):
    def test_a_fresh_run_produces_a_record_that_validates(self):
        """homework.py:run -- the record it returns is a `pyto-run-record@1` document.

        Guards homework.run's `observe=True` and its `run_record(...)` call
        (homework.py, `def run`): without receipts the materializer raises, and a
        document that claimed the schema without them is exactly what the
        independent validator refuses.
        """
        record = homework.run()["record"]
        validate_record(record)  # raises RecordSchemaError if it is not one
        self.assertEqual(record["schema"], "pyto-run-record@1")
        self.assertEqual(record["pcr"], homework.PCR_NAME)
        self.assertEqual(
            [tick["name"] for tick in record["ticks"]],
            ["Parse", "Stats", "Letters", "Histogram"],
        )
        # Four Ticks, five invocations: Stats holds mean and median side by side.
        self.assertEqual(
            [[inv["id"] for inv in tick["invocations"]] for tick in record["ticks"]],
            [["parse"], ["mean", "median"], ["letters"], ["histogram"]],
        )
        self.assertEqual(record["counters"]["invocations"], 5)
        # The seeded CSV is the run's one preexisting Part, so `parse` is the one hit.
        self.assertEqual(record["counters"]["hits"], 1)
        self.assertTrue(record["parts"][homework.SCORES_CSV.address]["preexisting"])

    def test_the_run_writes_a_record_receipts_and_a_viewer_page(self):
        """homework.py:write_evidence -- the three files `--out` is documented to write.

        Guards `def write_evidence` in homework.py. tick-viewer.html is asserted only
        when node is on PATH, which is the same condition write_viewer skips on.
        """
        with tempfile.TemporaryDirectory() as scratch:
            written = homework.write_evidence(homework.run(), scratch)
            names = sorted(os.path.basename(path) for path in written)
            expected = ["receipts.json", "record.json"]
            if shutil.which("node") is not None:
                expected.append("tick-viewer.html")
            self.assertEqual(names, sorted(expected))
            with open(os.path.join(scratch, "receipts.json"), encoding="utf-8") as handle:
                receipts = json.load(handle)
            self.assertEqual(sorted(receipts), sorted(homework.SOURCE_OF))


class CommittedEvidence(unittest.TestCase):
    def test_grade_exits_zero_on_the_committed_evidence(self):
        """grade.py:main -- the four checks all pass on evidence/run-1 and HANDOFF.md.

        Guards `def grade` in grade.py and, through it, all four checks against the
        bytes that are actually committed rather than against a record made here.
        """
        completed = run_grade(RUN_1, HANDOFF)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        for name in ("1 contract", "2 replay", "3 receipts", "4 hand-off"):
            self.assertIn(f"PASS  {name}", completed.stdout)
        self.assertIn("mechanical: 4 of 4 checks passed", completed.stdout)

    def test_the_report_says_the_plain_words_half_is_not_automated(self):
        """grade.py:grade -- the report refuses to imply it graded the explanation.

        Guards the two closing lines of `def grade` (the "not mechanical" line and
        the caveat line) and the "for the cold reader" block: the experiment's whole
        claim is that a passing exit code is not a grade.
        """
        completed = run_grade(RUN_1, HANDOFF)
        self.assertIn("not automated here", completed.stdout)
        self.assertIn("identical digests prove the same computation, not the right answer", completed.stdout)
        self.assertIn("--- for the cold reader ---", completed.stdout)
        self.assertIn("--- the question ---", completed.stdout)
        with open(HANDOFF, encoding="utf-8") as handle:
            handoff_text = handle.read()
        # The reader gets the hand-off's own words, not a summary of them.
        self.assertIn(handoff_text.strip().splitlines()[0], completed.stdout)


class TamperedRecord(unittest.TestCase):
    def test_flipping_one_result_digest_fails_the_replay_check(self):
        """grade.py:check_replay -- an edited record no longer matches a fresh run.

        Guards `def compared` in grade.py (which keeps `result_sha256` in the
        compared fields) and `def check_replay`. The tamper is one hex character of
        one invocation's `result_sha256`: checks 1, 3 and 4 are untouched by it, so
        this test also shows the failure is local to check 2 rather than a record
        that fell apart everywhere.
        """
        with tempfile.TemporaryDirectory() as scratch:
            run_dir = os.path.join(scratch, "run-1")
            shutil.copytree(RUN_1, run_dir)
            record_path = os.path.join(run_dir, "record.json")
            with open(record_path, encoding="utf-8") as handle:
                record = json.load(handle)
            invocation = record["ticks"][1]["invocations"][1]
            self.assertEqual(record["ticks"][1]["name"], "Stats")
            self.assertEqual(invocation["id"], "median")
            digest = invocation["result_sha256"]
            invocation["result_sha256"] = ("b" if digest[0] == "a" else "a") + digest[1:]
            with open(record_path, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(record, handle, indent=2, sort_keys=True)
                handle.write("\n")

            completed = run_grade(run_dir, HANDOFF)
            self.assertEqual(completed.returncode, 1, completed.stdout)
            self.assertIn("FAIL  2 replay", completed.stdout)
            self.assertIn("the fresh process produced a different record", completed.stdout)
            for still_passing in ("PASS  1 contract", "PASS  3 receipts", "PASS  4 hand-off"):
                self.assertIn(still_passing, completed.stdout)
            self.assertIn("mechanical: 3 of 4 checks passed", completed.stdout)

    def test_a_receipt_source_digest_that_is_not_todays_source_fails_check_three(self):
        """grade.py:check_receipts -- a receipt that describes code no longer on disk.

        Guards `def check_receipts` in grade.py, the branch that compares the
        receipt's `implementation_sha256` against `source_digest(function)` computed
        now. This is the check that catches editing homework.py after the run.
        """
        with tempfile.TemporaryDirectory() as scratch:
            run_dir = os.path.join(scratch, "run-1")
            shutil.copytree(RUN_1, run_dir)
            receipts_path = os.path.join(run_dir, "receipts.json")
            with open(receipts_path, encoding="utf-8") as handle:
                receipts = json.load(handle)
            digest = receipts["mean"]["calculation"]["implementation_sha256"]
            receipts["mean"]["calculation"]["implementation_sha256"] = (
                ("b" if digest[0] == "a" else "a") + digest[1:]
            )
            with open(receipts_path, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(receipts, handle, indent=2, sort_keys=True)
                handle.write("\n")

            completed = run_grade(run_dir, HANDOFF)
            self.assertEqual(completed.returncode, 1, completed.stdout)
            self.assertIn("FAIL  3 receipts", completed.stdout)
            self.assertIn("the source changed since the run", completed.stdout)


def handoff_without_bullet(name: str) -> str:
    """HANDOFF.md with the `- **<name>**` bullet, and only it, taken out.

    The bullet runs from its `- ` line to the next bullet or the next blank line,
    whichever comes first, so the indented lines it wraps onto go with it.
    """
    with open(HANDOFF, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    start = next(index for index, line in enumerate(lines) if line.startswith(f"- **{name}**"))
    end = next(
        index
        for index in range(start + 1, len(lines))
        if lines[index].startswith("- ") or not lines[index].strip()
    )
    return "\n".join(lines[:start] + lines[end:])


class Handoff(unittest.TestCase):
    def test_a_missing_stats_line_fails_check_four_even_though_the_prose_says_stats(self):
        """grade.py:names_tick -- the Tick needs a line of its own, not a mention.

        Guards `def tick_list_lines` and `def names_tick` in grade.py, and through
        them the Tick half of `def check_handoff`. The defect is the whole `Stats`
        bullet removed from the "One line per Tick" list and nothing else -- the
        shape of a student quietly omitting the step they did not understand. Stats
        is the interesting one: the name still appears further down the page (the
        honest-reason paragraph, twice, and a `{?}` line), so a check that only
        asked whether "Stats" appears anywhere on the page would pass on a hand-off
        with no Stats step in its list. That is the task 29 gap, and this test is
        what keeps it closed.
        """
        trimmed = handoff_without_bullet("Stats")
        self.assertNotIn("- **Stats**", trimmed)
        self.assertIn("Stats", trimmed)  # still all over the prose: that is the point
        self.assertIn("- **Histogram**", trimmed)  # only the one Tick line went missing

        with tempfile.TemporaryDirectory() as scratch:
            path = os.path.join(scratch, "HANDOFF.md")
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(trimmed + "\n")
            completed = run_grade(RUN_1, path)
            self.assertEqual(completed.returncode, 1, completed.stdout)
            self.assertIn("FAIL  4 hand-off", completed.stdout)
            self.assertIn("no line of its own for Tick 'Stats'", completed.stdout)
            for still_passing in ("PASS  1 contract", "PASS  2 replay", "PASS  3 receipts"):
                self.assertIn(still_passing, completed.stdout)

    def test_a_missing_histogram_line_fails_check_four(self):
        """grade.py:check_handoff -- a hand-off that leaves a Tick out is refused.

        The same defect on the Tick whose name appears exactly once on the page, so
        the failure does not depend on where else the name turns up. Kept beside the
        Stats case because a substring check would also catch this one: the pair is
        what says the new rule is strictly stronger and not merely different.
        """
        trimmed = handoff_without_bullet("Histogram")
        self.assertNotIn("Histogram", trimmed)

        with tempfile.TemporaryDirectory() as scratch:
            path = os.path.join(scratch, "HANDOFF.md")
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(trimmed + "\n")
            completed = run_grade(RUN_1, path)
            self.assertEqual(completed.returncode, 1, completed.stdout)
            self.assertIn("FAIL  4 hand-off", completed.stdout)
            self.assertIn("no line of its own for Tick 'Histogram'", completed.stdout)

    def test_the_three_accepted_bullet_forms_and_nothing_else(self):
        """grade.py:names_tick -- which list lines count as a Tick's own line.

        Guards the three forms the README promises -- `- **Name**`, `- Name:` and
        `- Name ` -- and the refusals that make the rule worth having: a bullet that
        names the Tick somewhere in the middle, and a name that is only the start of
        a longer word.
        """
        for accepted in ("**Stats** -- one step", "Stats: one step", "Stats holds two", "Stats"):
            self.assertTrue(grade.names_tick(accepted, "Stats"), accepted)
        for refused in ("*Mean* and *Median* live in Stats", "Statsville -- not a Tick", ""):
            self.assertFalse(grade.names_tick(refused, "Stats"), refused)

    def test_only_the_tick_section_bullets_are_read(self):
        """grade.py:tick_list_lines -- the list, not the whole page.

        Guards `def tick_list_lines`: bullets under other headings (the files list,
        the `{?}` list) are not Tick lines, and the indented continuations of a
        bullet are not lines of their own.
        """
        with open(HANDOFF, encoding="utf-8") as handle:
            bullets = grade.tick_list_lines(handle.read())
        self.assertEqual(len(bullets), 4)
        self.assertEqual(
            [bullet.split("**")[1] for bullet in bullets],
            ["Parse", "Stats", "Letters", "Histogram"],
        )
        for bullet in bullets:
            self.assertNotIn("homework.py", bullet)  # the files list is a different section

    def test_a_missing_file_fails_check_four(self):
        """grade.py:homework_files -- every file in the directory must be named.

        Guards `def homework_files` and the file half of `def check_handoff`: the
        list is walked off disk, so a file added and not mentioned fails rather than
        going unnoticed.
        """
        files = grade.homework_files()
        self.assertIn("homework.py", files)
        self.assertIn("evidence/run-1/record.json", files)
        with open(HANDOFF, encoding="utf-8") as handle:
            text = handle.read()
        passed, _detail = grade.check_handoff({"ticks": []}, text)
        self.assertTrue(passed)
        passed, detail = grade.check_handoff({"ticks": []}, text.replace("`grade.py`", "`the rubric`"))
        self.assertFalse(passed)
        self.assertIn("the hand-off never names the file 'grade.py'", detail)


class PathsWithNoRelativeForm(unittest.TestCase):
    """grade.py:display_path -- the report's label survives a path off the drive.

    Four of these tests hand grade.py a scratch copy of the run, or a scratch
    HANDOFF.md, under `tempfile`. On a GitHub windows-latest runner the checkout
    is on D: and TEMP is on C:, and `os.path.relpath` has no answer for that pair
    -- ntpath raises `ValueError: path is on mount 'C:', start on mount 'D:'`.
    That call was the report's FIRST line, before check 1 ran, so grade.py died
    with an empty stdout and exit 1 and the four tests reported
    `'FAIL  4 hand-off' not found in ''` (CI run 34429580002, windows job
    102722032579). Nothing about it is Windows-specific except which paths raise,
    so the raise is what is reproduced here.
    """

    def test_ntpath_really_refuses_a_cross_drive_pair(self):
        """The premise, not an assumption: this is the call that used to crash."""
        import ntpath

        with self.assertRaises(ValueError):
            ntpath.relpath(
                r"C:\Users\RUNNER~1\AppData\Local\Temp\tmp0\run-1",
                r"D:\a\DiscStudio-staging\DiscStudio-staging\pyto\experiments\students",
            )

    def test_display_path_answers_with_the_absolute_path_instead_of_raising(self):
        """Kills a `display_path` that is a bare `os.path.relpath` again."""
        boom = ValueError("path is on mount 'C:', start on mount 'D:'")
        with unittest.mock.patch("os.path.relpath", side_effect=boom):
            self.assertEqual(grade.display_path(RUN_1), os.path.abspath(RUN_1))

    def test_the_ordinary_case_is_still_relative(self):
        """And it did not stop being a relative label where one exists."""
        self.assertEqual(grade.display_path(RUN_1), os.path.join("evidence", "run-1"))


class ContractRefusal(unittest.TestCase):
    def test_a_record_missing_a_required_field_fails_check_one(self):
        """grade.py:check_contract -- the independent validator, not the producer.

        Guards `def check_contract` in grade.py. Deleting `result_sha256` from one
        invocation is a field RECORD.md does not declare optional, so the validator
        transcribed from RECORD.md refuses it.
        """
        with open(os.path.join(RUN_1, "record.json"), encoding="utf-8") as handle:
            record = json.load(handle)
        del record["ticks"][0]["invocations"][0]["result_sha256"]
        passed, detail = grade.check_contract(record)
        self.assertFalse(passed)
        self.assertIn("does not validate", detail[0])


class TickLaws(unittest.TestCase):
    def test_the_stats_tick_does_more_work_than_it_takes_time(self):
        """tick-laws/tick_laws.py:analyze_record -- the claim HANDOFF.md makes about Stats.

        Guards `def build_program` in homework.py (the two `pcr.calc("Stats", ...)`
        lines) and the hand-off paragraph that says Mean and Median could run side by
        side. One Tick holding two independent Calculations is exactly a Tick whose
        work (the sum of its branches) exceeds its latency (the longest branch); the
        singleton Ticks have work equal to latency. If the two ever drifted back into
        separate Ticks, or one started reading the other, this fails.
        """
        with open(os.path.join(RUN_1, "record.json"), encoding="utf-8") as handle:
            record = json.load(handle)
        names = [tick["name"] for tick in record["ticks"]]
        self.assertEqual(names, ["Parse", "Stats", "Letters", "Histogram"])

        report = tick_laws.analyze_record(record)
        self.assertTrue(report["valid"], report["violations"])
        self.assertEqual(report["violations"], [])
        self.assertTrue(report["ok"])
        self.assertTrue(report["laws"]["node"]["ok"])
        self.assertTrue(report["laws"]["loop"]["ok"])

        by_index = {tick["tick"]: tick for tick in report["ticks"]}
        self.assertEqual(sorted(by_index), list(range(len(names))))
        stats = by_index[names.index("Stats")]
        self.assertIsNotNone(stats["work_ms"])
        self.assertIsNotNone(stats["latency_ms"])
        self.assertGreater(stats["work_ms"], stats["latency_ms"])
        for index, name in enumerate(names):
            if name == "Stats":
                continue
            tick = by_index[index]
            self.assertEqual(tick["work_ms"], tick["latency_ms"], name)
        # One Tick of two branches is the whole difference between work and the
        # critical path for this run.
        self.assertGreater(report["summary"]["work_ms"], report["summary"]["critical_path_ms"])


class ObserveOnOff(unittest.TestCase):
    def test_the_testimony_is_byte_identical_with_observation_on_and_off(self):
        """pyto/src/pyto/pcr.py:PcrRun -- observation is additive and trailing.

        Guards homework.run's use of `observe=True` (homework.py, `def run`) against
        the PcrRun docstring's claim: turning observation on adds receipts (in
        `run.receipts` and as Parts under `px.receipt.`) and changes not one byte of
        `run.ticks`, which is what consumers embed. If that stopped holding, a
        student's record would depend on whether they were being graded.
        """
        def execute(observe: bool):
            pxc = PxC()
            pxc.set(homework.SCORES_CSV, homework.CLASS_CSV)
            return pxc, homework.build_program().run(pxc, observe=observe)

        pxc_off, run_off = execute(False)
        pxc_on, run_on = execute(True)

        def testimony_bytes(pcr_run):
            return json.dumps([dataclasses.asdict(tick) for tick in pcr_run.ticks], sort_keys=True)

        self.assertEqual(testimony_bytes(run_off), testimony_bytes(run_on))
        self.assertEqual(run_off.results, run_on.results)
        self.assertEqual(run_off.receipts, {})
        self.assertEqual(sorted(run_on.receipts), sorted(homework.SOURCE_OF))

        receipt_parts_off = [a for a in pxc_off.addresses() if a.startswith("px.receipt.")]
        receipt_parts_on = [a for a in pxc_on.addresses() if a.startswith("px.receipt.")]
        self.assertEqual(receipt_parts_off, [])
        self.assertEqual(
            sorted(receipt_parts_on),
            sorted(
                receipt_address(homework.PCR_NAME, tick.name, invocation.id)
                for tick in homework.build_program().ticks
                for invocation in tick.calculations
            ),
        )


if __name__ == "__main__":
    unittest.main()
