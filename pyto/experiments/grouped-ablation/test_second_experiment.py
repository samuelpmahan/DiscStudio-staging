"""Day 2 lane C tests: run_regrouped.py, run_reinput.py, run_from_retained.py.

Run with `python3 -m unittest discover -s experiments/grouped-ablation -p 'test_*.py'`.

sys.path (docs: experiments/CAPTURE.md, "sys.path: what is logged and what is
forbidden"): this file makes one intra-repo insert, logged to stderr, and
`test_sys_path_insert_is_intra_repo` asserts it is inside this repository.
Nothing here reaches outside the repository and nothing sets PYTHONPATH.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
EVIDENCE = os.path.join(HERE, "evidence")

if HERE not in sys.path:
    sys.path.insert(0, HERE)
print(f"[grouped-ablation] sys.path.insert(0, {HERE!r})  # this experiment's own modules", file=sys.stderr)

import run_regrouped  # noqa: E402
import run_reinput  # noqa: E402
import run_from_retained  # noqa: E402
import second_experiment as se  # noqa: E402
from calculations import REGISTRY  # noqa: E402

RUN_1 = os.path.join(EVIDENCE, "run-1")
FORBIDDEN_TOKENS = ("lambda", "<function")

# Fields that are expected to differ across two regenerations of the same run:
# wall-clock timing only (kill criteria, Day 2: "regenerating each run is
# deterministic except timings"). Everything else must be byte-identical.
TIMING_ONLY_FILES = {"receipts.json", "timings.json"}


def _run_into(main, out_dir: str, force: bool = True) -> int:
    args = ["--out", out_dir] + (["--force"] if force else [])
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        rc = main(args)
    return rc


def _load(out_dir: str, name: str):
    with open(os.path.join(out_dir, name), encoding="utf-8") as handle:
        return json.load(handle)


def _read(out_dir: str, name: str) -> str:
    with open(os.path.join(out_dir, name), encoding="utf-8") as handle:
        return handle.read()


class SysPathDiscipline(unittest.TestCase):
    def test_sys_path_insert_is_intra_repo(self):
        self.assertTrue(HERE.startswith(REPO + os.sep))
        self.assertTrue(os.path.isdir(HERE))
        self.assertIsNone(os.environ.get("PYTHONPATH"))


@unittest.skipUnless(os.path.isdir(RUN_1), "evidence/run-1 not generated yet; run run.py --out evidence/run-1 --force")
class ThreeRunsGenerated(unittest.TestCase):
    """Regenerate all three runs once into temp dirs and share them across the test classes below."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="second-experiment-")
        cls.regroup = os.path.join(cls.tmp, "run-2-regroup")
        cls.reinput = os.path.join(cls.tmp, "run-3-reinput")
        cls.from_retained = os.path.join(cls.tmp, "run-4-from-retained")
        for main, out in (
            (run_regrouped.main, cls.regroup),
            (run_reinput.main, cls.reinput),
            (run_from_retained.main, cls.from_retained),
        ):
            rc = _run_into(main, out)
            assert rc == 0, (main, out, rc)
        cls.record_1 = _load(RUN_1, "retained.json")
        cls.receipts_1 = _load(RUN_1, "receipts.json")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)


class NoReconstruction(ThreeRunsGenerated):
    """Kill criterion: build_program, family and REGISTRY are imported unchanged; program.py
    and calculations.py are never edited by any of the three scripts. The real check is
    program_lines_changed (git diff --numstat against HEAD, computed at run time, gap 18b);
    it is 0 for every run below."""

    def test_program_lines_changed_is_zero_for_all_three_runs(self):
        for out in (self.regroup, self.reinput, self.from_retained):
            with self.subTest(out=os.path.basename(out)):
                payload = _load(out, "saved-work.json")
                self.assertEqual(payload["program_lines_changed"]["total"], 0)
                self.assertEqual(payload["program_lines_changed"]["program.py"], 0)
                self.assertEqual(payload["program_lines_changed"]["calculations.py"], 0)

    def test_no_reconstruction_required_files_were_written(self):
        for out in (self.regroup, self.reinput, self.from_retained):
            self.assertFalse(os.path.exists(os.path.join(out, "RECONSTRUCTION-REQUIRED.md")))
        self.assertFalse(os.path.exists(os.path.join(HERE, "RECONSTRUCTION-REQUIRED.md")))


class SplitDigestByGrouping(ThreeRunsGenerated):
    """The digest test the plan names explicitly: equal across a regroup, different across a reinput."""

    def test_split_digest_equal_between_run_1_and_run_2_regroup(self):
        record_2 = _load(self.regroup, "retained.json")
        self.assertEqual(record_2["results"]["split"], self.record_1["results"]["split"])

    def test_split_digest_different_for_run_3_reinput(self):
        record_3 = _load(self.reinput, "retained.json")
        self.assertNotEqual(record_3["results"]["split"], self.record_1["results"]["split"])
        self.assertIsNotNone(record_3["results"]["split"])

    def test_run_4_from_retained_has_no_split_invocation_but_joins_it_by_digest(self):
        record_4 = _load(self.from_retained, "retained.json")
        ids = [entry["id"] for tick in record_4["program"]["ticks"] for entry in tick["calculations"]]
        self.assertNotIn("split", ids)
        self.assertNotIn("split", record_4["results"])
        # The provenance join: run_from_retained.py asserts this internally before writing
        # any evidence (ProvenanceMismatch), and repeats the recomputation here independently.
        rows = self.record_1["external"][run_from_retained.ROWS.address]
        recomputed = run_from_retained.split_fn({"rows": rows})
        self.assertEqual(run_from_retained.retain.digest_of(recomputed), self.record_1["results"]["split"])


class Rankings(ThreeRunsGenerated):
    def test_regroup_ranking_has_three_cross_cutting_variants(self):
        comparison = _load(self.regroup, "comparison.json")
        self.assertEqual(set(comparison["ranking"]), {"drop_h0", "drop_h1", "drop_h2"})
        self.assertEqual(len(comparison["ranking"]), 3)

    def test_reinput_ranking_still_recovers_the_planted_order(self):
        comparison = _load(self.reinput, "comparison.json")
        self.assertEqual(comparison["ranking"][:3], ["drop_g3", "drop_g0", "drop_g1"])

    def test_from_retained_ranking_equals_run_1s_committed_ranking(self):
        comparison = _load(self.from_retained, "comparison.json")
        committed = _load(RUN_1, "comparison.json")
        self.assertEqual(comparison["ranking"], committed["ranking"])
        self.assertEqual(comparison["rows"], committed["rows"])


class SavedWorkFields(ThreeRunsGenerated):
    REQUIRED_KEYS = {
        "run", "prior_run", "calculations_inherited", "calculations_added",
        "program_lines_changed", "input_parts_changed", "invocations_skippable_by_digest",
        "ms_saved", "ms_saved_by_invocation",
    }

    def _check(self, out_dir: str, expect_input_parts_changed: list[str]):
        payload = _load(out_dir, "saved-work.json")
        self.assertTrue(self.REQUIRED_KEYS <= set(payload))
        self.assertEqual(payload["prior_run"], "run-1")
        self.assertIsInstance(payload["calculations_inherited"], list)
        self.assertTrue(set(payload["calculations_inherited"]) <= set(REGISTRY))
        self.assertEqual(payload["calculations_added"], [])
        self.assertIsInstance(payload["input_parts_changed"], list)
        self.assertEqual(payload["input_parts_changed"], expect_input_parts_changed)
        self.assertIsInstance(payload["invocations_skippable_by_digest"], list)
        self.assertIsInstance(payload["ms_saved"], (int, float))
        self.assertGreaterEqual(payload["ms_saved"], 0)
        for invocation_id, ms in payload["ms_saved_by_invocation"].items():
            with self.subTest(invocation_id=invocation_id):
                self.assertIsInstance(ms, (int, float))
                self.assertGreaterEqual(ms, 0)
        # Every ms_saved entry must be traceable to run-1's receipts.json (gap 18b:
        # every number computed, never literal).
        for invocation_id, ms in payload["ms_saved_by_invocation"].items():
            self.assertEqual(ms, self.receipts_1[invocation_id]["duration_ms"])
        self.assertAlmostEqual(payload["ms_saved"], round(sum(payload["ms_saved_by_invocation"].values()), 3))

    def test_regroup_saved_work(self):
        self._check(self.regroup, ["input.ablation.groups"])
        payload = _load(self.regroup, "saved-work.json")
        self.assertEqual(payload["invocations_skippable_by_digest"], ["split"])
        self.assertEqual(payload["skip_reason"], "unchanged_upstream")

    def test_reinput_saved_work(self):
        self._check(self.reinput, ["input.ablation.rows"])
        payload = _load(self.reinput, "saved-work.json")
        self.assertEqual(payload["invocations_skippable_by_digest"], ["select"])
        self.assertEqual(payload["skip_reason"], "unchanged_upstream")

    def test_from_retained_saved_work(self):
        payload = _load(self.from_retained, "saved-work.json")
        self.assertEqual(payload["input_parts_changed"], ["scratch.ablation.split"])
        self.assertEqual(payload["invocations_skippable_by_digest"], ["split"])
        self.assertEqual(payload["skip_reason"], "removed")
        self.assertGreater(payload["ms_saved"], 0)
        self.assertEqual(payload["ms_saved_by_invocation"]["split"], self.receipts_1["split"]["duration_ms"])


class NoLambdaOrCode(ThreeRunsGenerated):
    def test_evidence_holds_no_lambda_or_function_repr(self):
        for out in (self.regroup, self.reinput, self.from_retained):
            for name in sorted(os.listdir(out)):
                path = os.path.join(out, name)
                if not os.path.isfile(path):
                    continue
                with open(path, encoding="utf-8") as handle:
                    text = handle.read()
                for token in FORBIDDEN_TOKENS:
                    with self.subTest(out=os.path.basename(out), file=name, token=token):
                        self.assertNotIn(token, text)


class InterpretationFiles(ThreeRunsGenerated):
    def test_each_run_has_an_interpretation_md(self):
        for out in (self.regroup, self.reinput, self.from_retained):
            text = _read(out, "interpretation.md")
            self.assertTrue(text.strip())

    def test_regroup_interpretation_states_whether_any_drop_exceeds_point_nine(self):
        text = _read(self.regroup, "interpretation.md")
        self.assertIn("No single drop exceeds +0.9 RMSE:", text)
        comparison = _load(self.regroup, "comparison.json")
        biggest = max(abs(row["delta_vs_baseline"]) for row in comparison["rows"] if row["variant"] != "all")
        self.assertIn(f"Largest |delta vs baseline| across the three cross-cutting drops: {biggest:.4f}.", text)

    def test_reinput_interpretation_names_n_from_the_fixture_not_a_literal(self):
        text = _read(self.reinput, "interpretation.md")
        self.assertIn(f"n={run_reinput.N}", text)
        self.assertIn(f"seed={run_reinput.SEED}", text)


class Determinism(unittest.TestCase):
    """Regenerating each run twice is byte-identical except receipts.json/timings.json."""

    def _check(self, main, run_label: str):
        parent = tempfile.mkdtemp(prefix="second-experiment-det-")
        self.addCleanup(shutil.rmtree, parent, ignore_errors=True)
        # Same basename (`run_label`) under two different parents: saved-work.json's "run"
        # field is basename(out_dir), and that is not itself a timing -- only receipts.json
        # and timings.json are allowed to differ between the two regenerations.
        tmp_a = os.path.join(parent, "a", run_label)
        tmp_b = os.path.join(parent, "b", run_label)
        self.assertEqual(_run_into(main, tmp_a), 0)
        self.assertEqual(_run_into(main, tmp_b), 0)
        names = sorted(os.listdir(tmp_a))
        self.assertEqual(names, sorted(os.listdir(tmp_b)))
        for name in names:
            with self.subTest(file=name):
                text_a, text_b = _read(tmp_a, name), _read(tmp_b, name)
                if name in TIMING_ONLY_FILES:
                    self.assertNotEqual(text_a, text_b, f"{name} unexpectedly identical across two real runs")
                else:
                    self.assertEqual(text_a, text_b)

    @unittest.skipUnless(os.path.isdir(RUN_1), "evidence/run-1 not generated yet")
    def test_run_regrouped_is_deterministic_except_timings(self):
        self._check(run_regrouped.main, "run-2-regroup")

    @unittest.skipUnless(os.path.isdir(RUN_1), "evidence/run-1 not generated yet")
    def test_run_reinput_is_deterministic_except_timings(self):
        self._check(run_reinput.main, "run-3-reinput")

    @unittest.skipUnless(os.path.isdir(RUN_1), "evidence/run-1 not generated yet")
    def test_run_from_retained_is_deterministic_except_timings(self):
        self._check(run_from_retained.main, "run-4-from-retained")


class OutDirSafety(unittest.TestCase):
    """Mirrors run.py's own not-overwritten-by-accident guarantee (GroupedAblationOutDir)."""

    def test_existing_non_empty_out_is_refused_without_force(self):
        tmp = tempfile.mkdtemp(prefix="second-experiment-existing-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        with open(os.path.join(tmp, "commit.txt"), "w", encoding="utf-8") as handle:
            handle.write("keep me\n")
        for main in (run_regrouped.main, run_reinput.main, run_from_retained.main):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                rc = main(["--out", tmp])
            self.assertEqual(rc, 2)
            self.assertIn("--force", stderr.getvalue())
        with open(os.path.join(tmp, "commit.txt"), encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "keep me\n")


if __name__ == "__main__":
    unittest.main()
