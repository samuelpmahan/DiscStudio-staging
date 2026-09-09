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
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
    print(f"[grouped-ablation] sys.path.insert(0, {HERE!r})  # this experiment's own modules (replay, retain, calculations)", file=sys.stderr)

import replay  # noqa: E402
import retain  # noqa: E402
from pyto import Calculation  # noqa: E402
from calculations import REGISTRY, fit as fit_fn, score as score_fn, split as split_fn  # noqa: E402
from program import SPLIT  # noqa: E402

REFUSALS_DIR = os.path.join(replay.REPLAY_DIR, "refusals")


def _refusal_log(name: str) -> str:
    """A committed, citable artifact per refusal (one per parent-side check)."""
    os.makedirs(REFUSALS_DIR, exist_ok=True)
    return os.path.join(REFUSALS_DIR, f"{name}.log")


def _verdict_line(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read().rstrip("\n").splitlines()[-1]


def same_module_impostor(args: dict) -> dict:
    """Not `calculations.score`, but claiming to live in its module.

    Used by ProviderIdentityIsModuleGranular. A named module-level function, never a
    lambda (docs/PYTHON-LAB-STEWARDSHIP.md:39).
    """
    honest = score_fn(args)
    return {"rmse": honest["rmse"] * 1.5, "n": honest["n"]}


# The whole forgery is this one line: `inspect.getmodule` resolves `__module__` through
# sys.modules and `retain._module_source_sha256` (retain.py:401-407) digests that
# MODULE's source file, so the impostor now presents calculations.py's digest as its
# provider identity and is indistinguishable from the honest Calculation there.
same_module_impostor.__module__ = "calculations"

POPPED: list[str] = []


def popping_fit(args: dict) -> dict:
    """A Calculation that mutates the list it was handed, then delegates.

    Named, module-level, and it records that it actually ran so the test cannot pass
    by never reaching it.
    """
    POPPED.append(args.get("variant") or "?")
    args["columns"].pop()
    return fit_fn(args)


def mutating_replay(record: dict, registry):
    """A `replay_fn` that edits the record it is handed, for the tamper-flag test."""
    record["program"]["name"] = record["program"]["name"] + "-mutated"
    return retain.replay(record, registry)


def _load_json(path: str):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _fit_all_columns(record: dict) -> list:
    entry = next(
        e
        for tick in record["program"]["ticks"]
        for e in tick["calculations"]
        if e["id"] == "fit.all"
    )
    return entry["args"]["columns"]


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

    def test_the_terminal_line_is_the_verdict_and_it_accepted_this_record(self):
        """`child failed checks: []` is NOT the verdict (fixer round 2, finding 3).

        Two forgeries reach the child cleanly and produce a log whose `child failed
        checks:` line reads `[]` while the record is refused: a value-forged record
        with recomputed digests (rows differ) and a registry-forged record whose
        provider block is byte-identical to the honest one (digests differ). Both are
        exercised in ParentSideRefusals and ProviderIdentityIsModuleGranular below.
        The single line that separates accepted from refused is the last one.
        """
        self.assertEqual(_verdict_line(replay.FRESH_PROCESS_LOG), "VERDICT: accepted")

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
        verdict = _verdict_line(replay.FORGED_REPLAY_LOG)
        self.assertTrue(verdict.startswith("VERDICT: refused ("), verdict)
        self.assertIn(
            "child failed checks ['program_matches_committed_testimony', "
            "'externals_match_declared_inputs']",
            verdict,
        )
        self.assertIn("child returncode 3", verdict)
        # The attack reproduces run-1's comparison byte for byte and its results map is
        # self-consistent, so NEITHER parent-side row/digest refusal fires here: this
        # forgery is caught by the child's own checks alone.
        self.assertNotIn("comparison rows differ", verdict)
        self.assertNotIn("result digests differ", verdict)

    def test_the_honest_record_is_restored_after_the_forgery_tests(self):
        """The forged record was written to a temp path and logged to its own file;
        evidence/run-1/retained.json and evidence/replay/fresh-process.log are untouched.

        Asserted on the VERDICT line, not on `child failed checks: []`, which a
        refused record can also print (fixer round 2, finding 3).
        """
        record = replay.ensure_retained_record()
        retain.check_record(record)
        self.assertEqual(_verdict_line(replay.FRESH_PROCESS_LOG), "VERDICT: accepted")


class ParentSideRefusals(unittest.TestCase):
    """One test per refusal `run_fresh_process_replay` makes AFTER the child reports.

    Before fixer round 2, finding 2, four of these five refusals were unguarded:
    deleting `if not rows_equal: raise`, `if not digests_equal: raise`,
    `if leaked: raise` or the parent/child source-sha comparison left the whole
    test_replay.py suite green, and two of them are the only thing that defeats a
    forgery the child accepts. Each test below engineers a record or an environment
    that trips exactly one of them, asserts the AssertionError names it, and leaves a
    citable log under evidence/replay/refusals/ whose terminal line is the VERDICT.
    """

    @classmethod
    def setUpClass(cls):
        cls.record = replay.ensure_retained_record()

    def _refuse(self, name, **kwargs):
        log_path = _refusal_log(name)
        with self.assertRaises(AssertionError) as caught:
            replay.run_fresh_process_replay(log_path=log_path, **kwargs)
        return str(caught.exception), _verdict_line(log_path)

    # (a) rows_equal -------------------------------------------------------------

    @staticmethod
    def _value_forged_record(record: dict) -> dict:
        """Nudge one input row and recompute `results` so every other check passes.

        The program is untouched (so the child's testimony check passes), the external
        address set is untouched (externals check passes), the registry and provider are
        honest (provider check passes) -- and the digests are recomputed from the forged
        input, so `digests_equal` passes too. Only the comparison rows move.
        """
        forged = copy.deepcopy(record)
        forged["external"]["input.ablation.rows"][0][1] += 1.0
        _pxc, run = retain.replay(forged, REGISTRY)
        forged["results"] = {k: retain.digest_of(v) for k, v in run.results.items()}
        return forged

    def test_a_value_forged_record_with_recomputed_digests_is_refused_on_the_rows(self):
        """Kills: dropping `if not rows_equal`. The child accepts this record."""
        forged = self._value_forged_record(self.record)
        tmp = tempfile.mkdtemp(prefix="value-forged-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        path = retain.write_record(forged, os.path.join(tmp, "retained.json"))
        message, verdict = self._refuse(
            "value-forged-rows", record=forged, record_path=path
        )
        self.assertIn("comparison rows differ from the committed comparison.json", message)
        self.assertIn("comparison rows differ from the committed comparison.json", verdict)
        # ... and it got past every check the child makes, which is the point.
        with open(_refusal_log("value-forged-rows"), encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("child failed checks: []", text)
        self.assertIn("result digests identical to record['results']: True", text)
        self.assertIn("comparison.json rows byte-identical: False", text)

    # (b) digests_equal ----------------------------------------------------------

    def test_a_record_whose_retained_digest_is_forged_is_refused_on_the_digests(self):
        """Kills: dropping `if not digests_equal`. Rows still match, so nothing else fires."""
        forged = copy.deepcopy(self.record)
        forged["results"]["split"] = "0" * 64
        tmp = tempfile.mkdtemp(prefix="digest-forged-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        path = retain.write_record(forged, os.path.join(tmp, "retained.json"))
        message, verdict = self._refuse(
            "digest-forged", record=forged, record_path=path
        )
        self.assertIn("result digests differ from record['results']", message)
        self.assertEqual(
            verdict, "VERDICT: refused (result digests differ from record['results'])"
        )
        with open(_refusal_log("digest-forged"), encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("child failed checks: []", text)
        self.assertIn("comparison.json rows byte-identical: True", text)

    # (c) leaked -----------------------------------------------------------------

    def test_a_module_outside_the_allowed_set_is_refused(self):
        """Kills: dropping `if leaked`.

        The child is the honest one; the allow-list is narrowed instead of importing
        something foreign in it, so the assertion is on the real report the real child
        produced -- `retain`, which the child genuinely imports, becomes a leak.
        """
        narrowed = set(replay._ALLOWED_TOP_LEVEL_MODULES) - {"retain"}
        with unittest.mock.patch.object(replay, "_ALLOWED_TOP_LEVEL_MODULES", narrowed):
            message, verdict = self._refuse(
                "module-leak", record=self.record, record_path=replay.RETAINED_PATH
            )
        self.assertIn("modules leaked beyond the allowed set: ['retain']", message)
        self.assertIn("modules leaked beyond the allowed set: ['retain']", verdict)

    # (d) parent/child source sha ------------------------------------------------

    @staticmethod
    def _wrong_source_sha256(names):
        """A parent that reads different bytes for retain.py than the child does."""
        return {name: "f" * 64 for name in names}

    def test_a_parent_child_source_sha_mismatch_is_refused(self):
        """Kills: dropping the `parent_source_sha256 != report['source_sha256']` raise."""
        with unittest.mock.patch.object(replay, "_source_sha256", self._wrong_source_sha256):
            message, verdict = self._refuse(
                "source-sha-mismatch", record=self.record, record_path=replay.RETAINED_PATH
            )
        self.assertIn("child read different module sources than the parent", message)
        self.assertIn("child read different module sources than the parent", verdict)

    # (e) the child's own checks, for completeness -------------------------------

    def test_the_honest_record_is_still_accepted_after_all_of_the_above(self):
        report = replay.run_fresh_process_replay(self.record)
        self.assertEqual(report["failed_checks"], [])
        self.assertEqual(_verdict_line(replay.FRESH_PROCESS_LOG), "VERDICT: accepted")


class ProviderIdentityIsModuleGranular(unittest.TestCase):
    """`retain.provider_identity` identifies the module SOURCE FILE, not the function.

    A registry whose address resolves to a different callable of the same module
    produces a provider block byte-identical to the honest one, and
    `verify_provider` agrees with it (fixer round 2, finding 3). The limitation is
    stated in `retain.provider_identity`'s docstring the way
    `pyto.pcr.FrozenCalculation.limitation` states its own; these tests pin both the
    hole and the refusal that actually catches it -- the result digests.
    """

    def setUp(self):
        self.record = replay.ensure_retained_record()
        self.corrupt = dict(REGISTRY)
        self.corrupt["fn.ablation.score"] = Calculation(
            "fn.ablation.score", same_module_impostor
        )

    def test_the_corrupted_registry_produces_a_byte_identical_provider_block(self):
        honest_provider = retain.provider_identity(REGISTRY)
        forged_provider = retain.provider_identity(self.corrupt)
        self.assertEqual(
            json.dumps(forged_provider, sort_keys=True),
            json.dumps(honest_provider, sort_keys=True),
        )
        self.assertEqual(
            json.dumps(forged_provider, sort_keys=True),
            json.dumps(self.record["provider"], sort_keys=True),
        )

    def test_verify_provider_agrees_with_the_corrupted_registry(self):
        report = retain.verify_provider(self.record, self.corrupt)
        self.assertTrue(report["agrees"])
        self.assertEqual(report["disagreeing_addresses"], [])

    def test_the_limitation_is_stated_in_the_docstring(self):
        doc = retain.provider_identity.__doc__
        self.assertIn("module source file, not function", doc)
        self.assertIn("FrozenCalculation", doc)

    def test_a_registry_forged_record_is_refused_by_the_digests_not_the_provider(self):
        _pxc, run = retain.replay(self.record, self.corrupt)
        forged = copy.deepcopy(self.record)
        forged["provider"] = retain.provider_identity(self.corrupt)
        forged["results"] = {k: retain.digest_of(v) for k, v in run.results.items()}
        tmp = tempfile.mkdtemp(prefix="registry-forged-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        path = retain.write_record(forged, os.path.join(tmp, "retained.json"))
        log_path = _refusal_log("registry-forged")
        with self.assertRaises(AssertionError) as caught:
            replay.run_fresh_process_replay(forged, record_path=path, log_path=log_path)
        message = str(caught.exception)
        self.assertIn("result digests differ from record['results']", message)
        with open(log_path, encoding="utf-8") as handle:
            text = handle.read()
        # The provider check accepted it; the digests did not.
        self.assertIn("provider identity accepted (retain.verify_provider): True", text)
        self.assertIn("child failed checks: []", text)
        self.assertIn("result digests identical to record['results']: False", text)
        self.assertTrue(_verdict_line(log_path).startswith("VERDICT: refused ("))


class LaneCCrossVerification(unittest.TestCase):
    """The plan's Day 2 cross-verification gate over lane C's runs, not only run-1.

    "Lane (c)'s outputs must be reproduced by lane (b)'s fresh-process replay
    carrying lane (a)'s digests." Run-1 had retained evidence and a test; run-2/3/4
    had neither, so nothing in the repository replayed them (fixer round 2, finding
    13). Each is replayed against its own committed comparison.json, testimony.json
    and retained.json["results"].
    """

    @classmethod
    def setUpClass(cls):
        cls.reports = replay.cross_verify_lane_c_runs()

    def test_every_lane_c_run_was_replayed(self):
        self.assertEqual(
            sorted(self.reports),
            ["run-2-regroup", "run-3-reinput", "run-4-from-retained"],
        )

    def test_each_run_has_its_own_log_ending_in_an_accepted_verdict(self):
        for label, _directory, _externals in replay.LANE_C_RUNS:
            with self.subTest(run=label):
                path = replay.lane_c_log_path(label)
                self.assertTrue(os.path.isfile(path))
                with open(path, "rb") as handle:
                    self.assertNotIn(b"\r\n", handle.read())
                self.assertEqual(_verdict_line(path), "VERDICT: accepted")

    def test_each_child_reproduced_its_own_committed_comparison_and_digests(self):
        for label, directory, _externals in replay.LANE_C_RUNS:
            with self.subTest(run=label):
                report = self.reports[label]
                with open(os.path.join(directory, "comparison.json"), encoding="utf-8") as handle:
                    committed_rows = json.load(handle)["rows"]
                with open(os.path.join(directory, "retained.json"), encoding="utf-8") as handle:
                    record = json.load(handle)
                self.assertEqual(
                    json.dumps(report["comparison_rows"], sort_keys=True),
                    json.dumps(committed_rows, sort_keys=True),
                )
                self.assertEqual(report["result_digests"], record["results"])
                self.assertEqual(report["failed_checks"], [])

    def test_run_4_declares_a_different_external_boundary_than_runs_1_to_3(self):
        """run-4 replays from a retained split, so its declared inputs are not
        run.EXTERNAL_ADDRESSES; the gate carries each run's own boundary rather than
        assuming one."""
        by_label = {label: externals for label, _dir, externals in replay.LANE_C_RUNS}
        self.assertEqual(
            sorted(by_label["run-4-from-retained"]),
            ["input.ablation.groups", "scratch.ablation.split"],
        )
        self.assertNotEqual(
            sorted(by_label["run-4-from-retained"]),
            sorted(by_label["run-2-regroup"]),
        )


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

    def test_a_calculation_that_mutates_its_args_in_place_leaves_the_record_alone(self):
        """Fixer round 2, finding 5: `args` were shallow-copied all the way down.

        `retain.from_program` did `dict(entry.get("args") or {})` and `PCR.calc` keeps
        `dict(args or {})` (pcr.py:56), both shallow, so
        `invocation.args["columns"]` WAS the caller's
        `record["program"]["ticks"][i]["calculations"][j]["args"]["columns"]` list. A
        Calculation that popped from it rewrote the retained record it was replaying,
        in memory. Only `external` was deep-copied. With retain.py:297 deep-copying
        args this fails closed; without it, this test fails.
        """
        record = replay.ensure_retained_record()
        before = json.dumps(record, sort_keys=True)
        columns_before = len(_fit_all_columns(record))

        mutating = dict(REGISTRY)
        mutating["fn.ablation.fit"] = Calculation("fn.ablation.fit", popping_fit)
        _pxc, run = retain.replay(record, mutating)

        self.assertTrue(POPPED, "the mutating calculation never ran, so this proves nothing")
        self.assertEqual(json.dumps(record, sort_keys=True), before)
        self.assertEqual(len(_fit_all_columns(record)), columns_before)
        self.assertIn("compare", run.results)

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

    def test_the_flag_is_false_when_the_baseline_replay_does_mutate(self):
        """Fixer round 2, finding 4: the flag used to be unfalsifiable.

        `run_tamper_check` replayed `copy.deepcopy(record)` and then compared the
        CALLER's `record` before and after -- an object the baseline replay was never
        handed -- so the comparison was `json.dumps(record) == json.dumps(record)` and
        could not be False. It now compares the copy that was actually handed in, and a
        `replay_fn` that mutates that copy drives the flag to False and the check to a
        raise. Nothing in the registry mutates today; this is what makes the report a
        check rather than a constant.
        """
        record = replay.ensure_retained_record()
        before = json.dumps(record, sort_keys=True)
        # The refusal gets its own citable artifact; evidence/tamper/report.json stays
        # the honest run's.
        report_path = os.path.join(replay.TAMPER_DIR, "mutating-baseline-refused.json")
        record_path = os.path.join(replay.TAMPER_DIR, "mutating-baseline-refused-record.json")
        with unittest.mock.patch.object(replay, "TAMPER_REPORT", report_path), \
                unittest.mock.patch.object(replay, "TAMPER_RECORD", record_path):
            with self.assertRaises(AssertionError) as caught:
                replay.run_tamper_check(record, replay_fn=mutating_replay)
        self.assertIn("mutated the record it was handed", str(caught.exception))
        report = _load_json(report_path)
        self.assertFalse(report["record_unchanged_by_baseline_replay"])
        # The caller's own record is still untouched: only the handed copy moved.
        self.assertEqual(json.dumps(record, sort_keys=True), before)
        # ...and the honest report is still the honest one.
        self.assertTrue(_load_json(replay.TAMPER_REPORT)["record_unchanged_by_baseline_replay"])

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
