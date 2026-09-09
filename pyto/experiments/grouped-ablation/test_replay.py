"""Day 2 Lane D tests: fresh-process replay, tamper, registry-hole, determinism.

Run with `python3 -m unittest discover -s experiments/grouped-ablation -p 'test_*.py'`.

sys.path (docs: experiments/CAPTURE.md, "sys.path: what is logged and what is
forbidden"): this file makes one intra-repo insert (this experiment's own
directory, already inserted by `replay.py` on import) and asserts it is inside
this repository; `replay.py` itself logs the *child* processes' inserts to
stderr, which lands in tests.txt via check_all.sh's `-v` capture.

These tests spawn real subprocesses (`python3 -I`, `python3 -s -P`, plain
`python3` with an overridden `PYTHONPATH`); each is a genuinely separate
interpreter, not a `unittest.mock` stand-in, per the Day 2 brief and critic gap
9. Every check writes its own evidence file under evidence/ so a failure here
always leaves a citable artifact, not just a traceback.
"""

from __future__ import annotations

import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
    print(f"[grouped-ablation] sys.path.insert(0, {HERE!r})  # this experiment's own modules (replay, retain, calculations)", file=sys.stderr)

import replay  # noqa: E402
import retain  # noqa: E402
from calculations import REGISTRY  # noqa: E402


class SysPathDiscipline(unittest.TestCase):
    def test_the_intra_repo_insert_is_inside_this_repository(self):
        self.assertTrue(os.path.isdir(REPO))
        self.assertTrue(os.path.abspath(HERE).startswith(os.path.abspath(REPO) + os.sep))


class RetainedRecordIsDeterministic(unittest.TestCase):
    """Two independent builds of the Day 1 record are byte-identical.

    replay.build_retained_record() re-derives the record from features.make_data
    with the fixed seed=7 (run.py main() default); nothing in the record depends
    on wall-clock time or process identity (unlike testimony.json's sibling
    evidence files, which run.py deliberately protects from silent regeneration
    because commit.txt/timings.json/saved-work.json vary run to run -- retain.py's
    record carries none of those).
    """

    def test_two_independent_builds_are_byte_identical(self):
        first = json.dumps(replay.build_retained_record(), sort_keys=True)
        second = json.dumps(replay.build_retained_record(), sort_keys=True)
        self.assertEqual(first, second)

    def test_ensure_retained_record_writes_lf_json_matching_a_fresh_build(self):
        written = replay.ensure_retained_record()
        with open(replay.RETAINED_PATH, "rb") as handle:
            raw = handle.read()
        self.assertNotIn(b"\r\n", raw)
        fresh = replay.build_retained_record()
        self.assertEqual(json.dumps(written, sort_keys=True), json.dumps(fresh, sort_keys=True))

    def test_retained_program_ticks_equal_the_committed_day1_testimony_ticks(self):
        """evidence/run-1/testimony.json needs no conversion to become the program (gap 18d)."""
        record = replay.ensure_retained_record()
        with open(os.path.join(replay.RUN1, "testimony.json"), encoding="utf-8") as handle:
            testimony = json.load(handle)
        self.assertEqual(
            json.dumps(record["program"]["ticks"], sort_keys=True),
            json.dumps(testimony["ticks"], sort_keys=True),
        )

    def test_result_digests_agree_with_the_committed_comparison(self):
        record = replay.ensure_retained_record()
        with open(replay.COMPARISON_PATH, encoding="utf-8") as handle:
            committed = json.load(handle)
        _pxc, run = retain.replay(record, REGISTRY)
        self.assertEqual(run.results["compare"], committed["rows"])
        for invocation_id, digest in record["results"].items():
            self.assertEqual(digest, retain.digest_of(run.results[invocation_id]), invocation_id)


class FreshProcessReplay(unittest.TestCase):
    """`python3 -I` from a cwd outside the repo, env stripped to PATH only."""

    @classmethod
    def setUpClass(cls):
        cls.record = replay.ensure_retained_record()
        cls.report = replay.run_fresh_process_replay(cls.record)

    def test_log_was_written_with_the_command_line_and_module_dump(self):
        self.assertTrue(os.path.isfile(replay.FRESH_PROCESS_LOG))
        with open(replay.FRESH_PROCESS_LOG, "rb") as handle:
            raw = handle.read()
        self.assertNotIn(b"\r\n", raw)
        text = raw.decode("utf-8")
        for marker in ("command:", "cwd (outside repo):", "sys.path before:", "sys.path after:", "sys.modules after replay", "new modules introduced"):
            self.assertIn(marker, text)

    def test_cwd_was_outside_the_repository(self):
        with open(replay.FRESH_PROCESS_LOG, encoding="utf-8") as handle:
            text = handle.read()
        cwd_line = next(line for line in text.splitlines() if line.startswith("cwd (outside repo): "))
        cwd = cwd_line.split(": ", 1)[1]
        self.assertFalse(os.path.abspath(cwd).startswith(os.path.abspath(REPO) + os.sep))

    def test_env_was_stripped_to_path_only(self):
        with open(replay.FRESH_PROCESS_LOG, encoding="utf-8") as handle:
            text = handle.read()
        env_line = next(line for line in text.splitlines() if line.startswith("env: "))
        self.assertEqual(sorted(eval(env_line[len("env: "):])), ["PATH"])

    def test_exactly_one_intra_repo_path_was_inserted_and_it_is_this_directory(self):
        added = [p for p in self.report["sys_path_after"] if p not in self.report["sys_path_before"]]
        self.assertEqual(added, [HERE])

    def test_no_modules_leaked_beyond_pyto_calculations_features_retain(self):
        leaked = sorted(
            name.split(".")[0]
            for name in self.report["new_modules"]
            if name.split(".")[0] not in replay._ALLOWED_TOP_LEVEL_MODULES
        )
        self.assertEqual(leaked, [])

    def test_comparison_rows_are_byte_identical_to_run_1(self):
        with open(replay.COMPARISON_PATH, encoding="utf-8") as handle:
            committed_rows = json.load(handle)["rows"]
        self.assertEqual(
            json.dumps(self.report["comparison_rows"], sort_keys=True),
            json.dumps(committed_rows, sort_keys=True),
        )

    def test_result_digests_are_identical_to_the_retained_record(self):
        self.assertEqual(self.report["result_digests"], self.record["results"])


class HiddenStateAuditor(unittest.TestCase):
    """The fresh-process boundary cannot be satisfied by leaked in-process state.

    Mutating the REGISTRY dict *after* retaining a record must not change what a
    fresh child process resolves each address to -- the child imports its own
    `calculations` module and builds its own REGISTRY from source, so a mutation
    in this (parent) process's dict is invisible to it.
    """

    def test_mutating_this_process_registry_after_retain_does_not_affect_a_fresh_child(self):
        record = replay.ensure_retained_record()
        original = REGISTRY["fn.ablation.compare"]
        REGISTRY["fn.ablation.compare"] = REGISTRY["fn.ablation.split"]  # corrupt this process's dict
        try:
            report = replay.run_fresh_process_replay(record)
        finally:
            REGISTRY["fn.ablation.compare"] = original
        with open(replay.COMPARISON_PATH, encoding="utf-8") as handle:
            committed_rows = json.load(handle)["rows"]
        self.assertEqual(
            json.dumps(report["comparison_rows"], sort_keys=True),
            json.dumps(committed_rows, sort_keys=True),
        )


class Tamper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = replay.ensure_retained_record()
        cls.report = replay.run_tamper_check(cls.record)

    def test_report_was_written(self):
        self.assertTrue(os.path.isfile(replay.TAMPER_REPORT))
        self.assertTrue(os.path.isfile(replay.TAMPER_RECORD))
        with open(replay.TAMPER_RECORD, "rb") as handle:
            self.assertNotIn(b"\r\n", handle.read())

    def test_only_the_tampered_variant_and_compare_changed(self):
        self.assertEqual(sorted(self.report["changed"]), sorted(self.report["expected_to_change"]))
        self.assertEqual(self.report["unexpected_changes"], [])
        self.assertEqual(self.report["missing_expected_changes"], [])

    def test_untouched_variants_kept_their_digests(self):
        untouched = [
            key for key in self.report["baseline_digests"]
            if key not in ("fit.drop_g0", "score.drop_g0", "compare")
        ]
        self.assertGreater(len(untouched), 0)
        for key in untouched:
            self.assertEqual(
                self.report["baseline_digests"][key], self.report["tampered_digests"][key], key
            )

    def test_record_holds_no_code(self):
        with open(replay.TAMPER_RECORD, encoding="utf-8") as handle:
            text = handle.read()
        for token in ("lambda", "<function"):
            self.assertNotIn(token, text)


class RegistryHole(unittest.TestCase):
    def test_removing_a_used_address_raises_keyerror_naming_it_before_execution(self):
        record = replay.ensure_retained_record()
        replay.PROBE_CALLS.clear()
        message = replay.run_registry_hole_check(record)
        self.assertIn("fn.ablation.score", message)
        self.assertEqual(replay.PROBE_CALLS, [])

    def test_log_was_written(self):
        self.assertTrue(os.path.isfile(replay.REGISTRY_HOLE_LOG))
        with open(replay.REGISTRY_HOLE_LOG, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("KeyError raised:", text)
        self.assertIn("probe calculation (a still-present address) was never called: True", text)

    def test_requested_address_from_the_brief_is_not_actually_in_the_registry(self):
        """Documents why the log substitutes an address (see replay.py docstring)."""
        self.assertNotIn("fn.ablation.rmse", REGISTRY)
        self.assertIn("fn.ablation.score", REGISTRY)


class DeterminismMatrix(unittest.TestCase):
    """PYTHONHASHSEED 0..4 (no `-I`) plus one LF-converted-package row."""

    @classmethod
    def setUpClass(cls):
        cls.record = replay.ensure_retained_record()
        cls.result = replay.run_determinism_matrix(cls.record)

    def test_log_was_written_as_lf(self):
        self.assertTrue(os.path.isfile(replay.DETERMINISM_LOG))
        with open(replay.DETERMINISM_LOG, "rb") as handle:
            self.assertNotIn(b"\r\n", handle.read())

    def test_seed_zero_reports_hash_randomization_disabled(self):
        row = next(r for r in self.result["hashseed_rows"] if r["seed"] == 0)
        self.assertEqual(row["first"]["hash_randomization"], 0)
        self.assertEqual(row["second"]["hash_randomization"], 0)

    def test_every_seed_is_reproducible_across_two_independent_processes(self):
        for row in self.result["hashseed_rows"]:
            self.assertEqual(row["first"]["hash_pyto"], row["second"]["hash_pyto"], row["seed"])
            self.assertTrue(row["reproducible_hash"], row["seed"])

    def test_result_digests_are_identical_across_every_hashseed_row_and_the_baseline(self):
        for row in self.result["hashseed_rows"]:
            self.assertEqual(row["first"]["result_digests"], self.record["results"], row["seed"])
            self.assertEqual(row["second"]["result_digests"], self.record["results"], row["seed"])

    def test_nonzero_seeds_do_not_report_hash_randomization_disabled(self):
        """Corrects the plan's 'confirmed not gaps' note for n != 0 (replay.py docstring)."""
        for row in self.result["hashseed_rows"]:
            if row["seed"] == 0:
                continue
            self.assertEqual(row["first"]["hash_randomization"], 1, row["seed"])

    def test_lf_copy_used_the_lf_package_not_the_editable_install(self):
        self.assertFalse(self.result["lf_row"]["used_editable_install"])
        self.assertTrue(self.result["lf_row"]["converted_files"])

    def test_lf_copy_module_source_hashes_drift_but_result_digests_do_not(self):
        with open(replay.RETAINED_PATH, encoding="utf-8") as handle:
            record = json.load(handle)
        provider_modules = record["provider"]["pyto"]["modules"]
        lf_modules = self.result["lf_row"]["modules"]
        for name in ("core.py", "pcr.py"):
            self.assertNotEqual(provider_modules[name], lf_modules[name], name)
        self.assertEqual(self.result["lf_row"]["result_digests"], self.record["results"])


if __name__ == "__main__":
    unittest.main()
