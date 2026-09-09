"""Day 2 Lane D tests: fresh-process replay, tamper, registry-hole, determinism.

Run with `python3 -m unittest discover -s experiments/grouped-ablation -p 'test_*.py'`.

sys.path (docs: experiments/CAPTURE.md, "sys.path: what is logged and what is
forbidden"): this file makes one intra-repo insert (this experiment's own
directory, already inserted by `replay.py` on import) and asserts it is inside
this repository; `replay.py` itself logs the *child* processes' inserts to
stderr, which lands in tests.txt via check_all.sh's `-v` capture.

These tests spawn real subprocesses (`python3 -I -B`, `python3 -s -P`); each is a
genuinely separate interpreter, not a `unittest.mock` stand-in, per the Day 2 brief
and critic gap 9. **No test here sets PYTHONPATH**: the one probe that needs a
scratch PYTHONPATH (the LF-converted `pyto` copy) was moved out of the discovered
suite into `python3 replay.py`, and `LfSourceDriftProbe` asserts on its committed
evidence/lf-source-drift.log instead (fixer round 1, finding 4). Every check writes
its own evidence file under evidence/ so a failure here always leaves a citable
artifact, not just a traceback.
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
    print(f"[grouped-ablation] sys.path.insert(0, {HERE!r})  # this experiment's own modules (replay, retain, calculations)", file=sys.stderr)

import replay  # noqa: E402
import retain  # noqa: E402
from calculations import REGISTRY, split as split_fn  # noqa: E402
from program import SPLIT  # noqa: E402


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

    def test_log_carries_the_four_checks_the_child_makes_before_trusting_the_record(self):
        """Kills: dropping any of the guards added in fixer round 1 (findings 1, 3, 6)."""
        with open(replay.FRESH_PROCESS_LOG, encoding="utf-8") as handle:
            text = handle.read()
        for marker in (
            "record program ticks identical to the committed evidence/run-1/testimony.json ticks: True",
            "equal the declared inputs",
            "provider identity accepted (retain.verify_provider): True",
            "calculations.py sha256 the record claims",
            "child failed checks: []",
        ):
            self.assertIn(marker, text)

    def test_the_child_neither_read_nor_wrote_bytecode(self):
        """`python3 -B` plus the parent's __pycache__ purge: a stale .pyc whose
        timestamp and size still match a tampered source cannot serve the replay."""
        self.assertTrue(self.report["dont_write_bytecode"])
        self.assertIn("-B", replay.run_fresh_process_replay.__doc__)
        with open(replay.FRESH_PROCESS_LOG, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("__pycache__ directories purged under the experiment before the spawn:", text)
        self.assertIn("child sys.dont_write_bytecode (python3 -B): True", text)

    def test_the_child_read_the_same_module_sources_the_parent_sees_on_disk(self):
        parent = replay._source_sha256(("retain.py", "calculations.py", "features.py"))
        self.assertEqual(self.report["source_sha256"], parent)
        self.assertEqual(
            self.report["claimed_provider_source_sha256"], [parent["calculations.py"]]
        )

    def test_provider_identity_was_compared_and_agreed(self):
        """The docstring at retain.provider_identity now promises a comparison exists;
        this is it (fixer round 1, finding 3)."""
        self.assertTrue(self.report["provider_agrees"])
        self.assertTrue(self.report["provider_pyto_agrees"])
        self.assertEqual(self.report["provider_disagreeing_addresses"], [])
        report = retain.verify_provider(self.record, REGISTRY)
        self.assertTrue(report["agrees"])
        self.assertEqual(sorted(report["registry"]), sorted(REGISTRY))

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
    """The fresh-process boundary cannot be satisfied by leaked in-process state, nor
    by a record that hides state in its own `external` map.

    Mutating the REGISTRY dict *after* retaining a record must not change what a
    fresh child process resolves each address to -- the child imports its own
    `calculations` module and builds its own REGISTRY from source, so a mutation
    in this (parent) process's dict is invisible to it.

    The three forgery tests below are fixer round 1, finding 1: pre-seeding an
    `into` address, a results map that does not describe the program, and the full
    step-deletion attack (delete `split`, pre-seed `scratch.ablation.split`, rebind
    the consumers, drop the real input) which reproduces run-1's committed
    comparison byte for byte in-process and is nonetheless refused by the child.
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

    # ------------------------------------------------------------------ forged records

    @staticmethod
    def _preseeded_record(record: dict) -> dict:
        """ATTACK 2: keep the `split` invocation, but also hand the replay its output.

        The program still declares `into = scratch.ablation.split`, so the record
        contradicts itself: it claims to compute an address it also supplies.
        """
        forged = copy.deepcopy(record)
        forged["external"][SPLIT.address] = split_fn(
            {"rows": forged["external"]["input.ablation.rows"]}
        )
        return forged

    @staticmethod
    def _step_deleted_record(record: dict) -> dict:
        """ATTACK 3: delete the `split` step, pre-seed its output as an 'external',
        rebind every `fn:split` consumer to that address, drop the real input and the
        step's retained digest.

        The result is self-consistent -- externals no longer intersect any `into`,
        and results keys still equal the program's invocation ids -- which is exactly
        why retain.check_record alone cannot catch it and the fresh-process child also
        compares the program against the committed testimony and the external address
        set against the declared inputs (fixer round 1, finding 1).
        """
        forged = copy.deepcopy(record)
        forged["external"][SPLIT.address] = split_fn(
            {"rows": forged["external"]["input.ablation.rows"]}
        )
        for tick in forged["program"]["ticks"]:
            tick["calculations"] = [e for e in tick["calculations"] if e["id"] != "split"]
        for tick in forged["program"]["ticks"]:
            for entry in tick["calculations"]:
                entry["inputs"] = {
                    name: (f"px:{SPLIT.address}" if ref == "fn:split" else ref)
                    for name, ref in entry["inputs"].items()
                }
        forged["results"].pop("split")
        forged["external"].pop("input.ablation.rows")
        return forged

    def test_a_record_that_preseeds_an_address_the_program_computes_is_refused(self):
        """Kills: dropping the external-vs-into check in retain.check_record."""
        forged = self._preseeded_record(replay.ensure_retained_record())
        with self.assertRaises(retain.ContradictoryRecordError) as caught:
            retain.replay(forged, REGISTRY)
        self.assertIn(SPLIT.address, str(caught.exception))
        self.assertIn("claims to compute", str(caught.exception))

    def test_a_record_whose_results_keys_are_not_the_programs_ids_is_refused(self):
        """Kills: dropping the results-keys check in retain.check_record."""
        forged = copy.deepcopy(replay.ensure_retained_record())
        forged["results"]["ghost"] = "0" * 64
        with self.assertRaises(retain.ContradictoryRecordError) as caught:
            retain.replay(forged, REGISTRY)
        self.assertIn("ghost", str(caught.exception))

    def test_a_step_deleted_record_replays_in_process_but_the_fresh_child_refuses_it(self):
        """The whole point of the fresh-process boundary: a forged record that reproduces
        run-1's committed comparison byte for byte is still refused, because it is not
        run-1's program and its externals are not run-1's declared inputs."""
        record = replay.ensure_retained_record()
        forged = self._step_deleted_record(record)
        tmp = tempfile.mkdtemp(prefix="forged-record-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        forged_path = retain.write_record(forged, os.path.join(tmp, "retained.json"))

        # In-process it runs and reproduces run-1's comparison exactly -- that is the attack.
        _pxc, forged_run = retain.replay(forged, REGISTRY)
        with open(replay.COMPARISON_PATH, encoding="utf-8") as handle:
            committed_rows = json.load(handle)["rows"]
        self.assertEqual(forged_run.results["compare"], committed_rows)
        self.assertNotIn("split", forged_run.results)

        with self.assertRaises(AssertionError) as caught:
            replay.run_fresh_process_replay(
                forged, record_path=forged_path, log_path=replay.FORGED_REPLAY_LOG
            )
        message = str(caught.exception)
        self.assertIn("program_matches_committed_testimony", message)
        self.assertIn("externals_match_declared_inputs", message)
        with open(replay.FORGED_REPLAY_LOG, "rb") as handle:
            raw = handle.read()
        self.assertNotIn(b"\r\n", raw)
        text = raw.decode("utf-8")
        self.assertIn("record program ticks identical to the committed evidence/run-1/testimony.json ticks: False", text)
        self.assertIn("child failed checks: ['program_matches_committed_testimony', 'externals_match_declared_inputs']", text)

    def test_the_honest_record_is_restored_after_the_forgery_tests(self):
        """The forged record was written to a temp path and logged to its own file;
        evidence/run-1/retained.json and evidence/replay/fresh-process.log are untouched."""
        record = replay.ensure_retained_record()
        retain.check_record(record)
        with open(replay.FRESH_PROCESS_LOG, encoding="utf-8") as handle:
            self.assertIn("child failed checks: []", handle.read())


class ReplayDoesNotMutateTheRecord(unittest.TestCase):
    """retain.replay seeds the PxC from deep copies (fixer round 1, finding 2).

    pcr.py:334-336 publishes one object as both run.results[id] and the PxC value, so
    without the copy a Calculation that mutated an input in place would rewrite the
    retained record it was replaying -- and run_tamper_check, which takes its baseline
    from that record, would inherit the mutation on both sides and report 'clean'.
    """

    def test_two_replays_of_one_record_object_agree_and_leave_it_byte_identical(self):
        record = replay.ensure_retained_record()
        before = json.dumps(record, sort_keys=True)
        _pxc_a, run_a = retain.replay(record, REGISTRY)
        _pxc_b, run_b = retain.replay(record, REGISTRY)
        digests_a = {k: retain.digest_of(v) for k, v in run_a.results.items()}
        digests_b = {k: retain.digest_of(v) for k, v in run_b.results.items()}
        self.assertEqual(digests_a, digests_b)
        self.assertEqual(digests_a, record["results"])
        self.assertEqual(json.dumps(record, sort_keys=True), before)

    def test_the_seeded_value_is_not_the_records_own_object(self):
        record = replay.ensure_retained_record()
        pxc, run = retain.replay(record, REGISTRY)
        seeded = pxc.get("input.ablation.rows")
        retained = record["external"]["input.ablation.rows"]
        self.assertEqual(seeded, retained)
        self.assertIsNot(seeded, retained)
        self.assertIsNot(run.results["split"], record["external"].get("scratch.ablation.split"))


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

    def test_the_baseline_replay_left_the_record_byte_identical(self):
        """Fixer round 1, finding 2: the two sides of this report must be independent."""
        self.assertTrue(self.report["record_unchanged_by_baseline_replay"])

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

    def test_the_five_seeds_produce_five_distinct_hashes(self):
        """Kills: a seed that stopped taking effect.

        Every other assertion in this class is a WITHIN-seed equality. On a build or
        platform where PYTHONHASHSEED were ignored and str hashing were seed-independent,
        all five rows would collapse to one hash value and each of them would still pass
        (fixer round 1, finding 7). Distinctness across seeds is the only line that
        cannot (it is computed in run_determinism_matrix and printed into the log).
        """
        rows = self.result["hashseed_rows"]
        self.assertEqual(len({row["first"]["hash_pyto"] for row in rows}), len(rows))
        self.assertEqual(self.result["distinct_hashes"], len(rows))
        with open(replay.DETERMINISM_LOG, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn(f"distinct hash('pyto') across the {len(rows)} seeds: {len(rows)} ", text)

    def test_the_matrix_sets_no_pythonpath(self):
        """The LF-copy row, the only one needing a scratch PYTHONPATH, was moved out of
        the discovered suite (fixer round 1, finding 4; experiments/CAPTURE.md forbids a
        scratch PYTHONPATH for anything scripts/check_all.sh runs)."""
        self.assertNotIn("lf_row", self.result)
        for row in self.result["hashseed_rows"]:
            for half in ("first", "second"):
                self.assertNotIn("PYTHONPATH", row[half]["stderr"])
        with open(replay.DETERMINISM_LOG, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("No PYTHONPATH is set by any row below", text)
        self.assertIn("evidence/lf-source-drift.log", text)


class LfSourceDriftProbe(unittest.TestCase):
    """The committed evidence of the one probe the suite must not run itself.

    `replay.run_lf_source_drift_probe` sets PYTHONPATH to a scratch copy of the `pyto`
    package, which experiments/CAPTURE.md forbids inside scripts/check_all.sh; it runs
    only from `python3 experiments/grouped-ablation/replay.py`. These tests read its
    committed log, and `record_results_sha256` makes a stale log fail here rather than
    drift unnoticed.
    """

    @classmethod
    def setUpClass(cls):
        with open(replay.LF_DRIFT_LOG, "rb") as handle:
            cls.raw = handle.read()
        cls.text = cls.raw.decode("utf-8")

    def test_log_is_lf_and_names_the_pythonpath_it_used(self):
        self.assertNotIn(b"\r\n", self.raw)
        self.assertIn("PYTHONPATH (scratch, removed after the run): ", self.text)
        self.assertIn("`python3 experiments/grouped-ablation/replay.py` ONLY", self.text)

    def test_no_test_module_in_this_directory_calls_the_probe(self):
        """The needles are assembled at run time so this file does not match itself."""
        needles = ["run_lf_source_drift" + "_probe(", "_run_lf_copy" + "_row("]
        checked = []
        for name in sorted(os.listdir(HERE)):
            if not (name.startswith("test_") and name.endswith(".py")):
                continue
            checked.append(name)
            with open(os.path.join(HERE, name), encoding="utf-8") as handle:
                source = handle.read()
            for needle in needles:
                self.assertNotIn(needle, source, f"{name} calls the LF probe")
        self.assertIn("test_replay.py", checked)
        # It is reachable from replay.main() -- the standalone entry point -- and only there:
        # exactly two occurrences in replay.py, one `def` and one call.
        with open(os.path.join(HERE, "replay.py"), encoding="utf-8") as handle:
            replay_source = handle.read()
        self.assertEqual(replay_source.count(needles[0]), 2)
        self.assertEqual(replay_source.count("def " + needles[0]), 1)

    def test_module_sources_drifted_by_construction_while_digests_did_not(self):
        for name in ("core.py", "pcr.py"):
            self.assertRegex(self.text, rf"{name} source sha256: .*differs_by_construction=True")
        self.assertIn("replay result digests identical to run-1 despite the source-hash drift: True", self.text)
        self.assertIn("used editable install instead of the LF copy: False", self.text)

    def test_the_log_was_produced_against_the_current_retained_record(self):
        """A stale log (someone regenerated retained.json without re-running the probe)
        fails here, naming the command to re-run."""
        import hashlib

        record = replay.ensure_retained_record()
        expected = hashlib.sha256(
            json.dumps(record["results"], sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        line = next(l for l in self.text.splitlines() if l.startswith("record_results_sha256"))
        self.assertEqual(
            line.split(": ", 1)[1], expected,
            "evidence/lf-source-drift.log is stale; re-run `python3 experiments/grouped-ablation/replay.py`",
        )


if __name__ == "__main__":
    unittest.main()
