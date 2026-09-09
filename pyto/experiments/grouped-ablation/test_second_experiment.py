"""Day 2 lane C tests: run_regrouped.py, run_reinput.py, run_from_retained.py.

Run with `python3 -m unittest discover -s experiments/grouped-ablation -p 'test_*.py'`.

sys.path (docs: experiments/CAPTURE.md, "sys.path: what is logged and what is
forbidden"): this file makes one intra-repo insert, logged to stderr, and
`test_sys_path_insert_is_intra_repo` asserts it is inside this repository.
Nothing here reaches outside the repository and nothing sets PYTHONPATH.

**Nothing here writes under evidence/** (fixer round 3, finding 1): every run this
file regenerates goes into a temp directory, and the committed evidence is read as
an oracle. `EvidenceIsNeverRewritten` asserts that directly, and
`test_replay.py::CheckAllLeavesTheTreeClean` asserts it for this module and
test_replay.py together by running both in a child interpreter and reading
`git status --porcelain`.
"""

from __future__ import annotations

import contextlib
import copy
import io
import json
import os
import shutil
import subprocess
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
COMMITTED_RUNS = ("run-1", "run-2-regroup", "run-3-reinput", "run-4-from-retained")
FORBIDDEN_TOKENS = ("lambda", "<function")

# Fields that are expected to differ across two regenerations of the same run:
# wall-clock timing only (kill criteria, Day 2: "regenerating each run is
# deterministic except timings"). Everything else must be byte-identical.
TIMING_ONLY_FILES = {"receipts.json", "timings.json"}

# The two wall-clock fields of pyto.pcr.Receipt (src/pyto/pcr.py:119-120). Everything
# else a Receipt carries -- the frozen calculation, the declared/actual Part sets, the
# writes, result_sha256, the effective arg keys, the shadowed inputs -- is a statement
# about the program and its values, so it must reproduce exactly (finding 5).
RECEIPT_TIMING_KEYS = ("started_ms", "duration_ms")


def receipts_without_timings(payload: dict) -> dict:
    """`receipts.json` with the two wall-clock fields dropped from every receipt."""
    return {
        invocation_id: {k: v for k, v in receipt.items() if k not in RECEIPT_TIMING_KEYS}
        for invocation_id, receipt in payload.items()
    }


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

    def test_the_diff_base_is_recorded_and_is_an_ancestor_of_head(self):
        """Fixer round 1, finding 11: the zero must be measured against the DAY's base.

        HEAD moves as the day's checkpoints land, so a HEAD-based diff would report 0
        even if a checkpoint had committed a program.py edit. The base is recorded in
        saved-work.json and re-verified here against git.
        """
        for out in (self.regroup, self.reinput, self.from_retained):
            with self.subTest(out=os.path.basename(out)):
                base = _load(out, "saved-work.json")["program_lines_changed_base"]
                self.assertEqual(base, se.DAY2_BASE)
                ancestor = subprocess.run(
                    ["git", "merge-base", "--is-ancestor", base, "HEAD"], cwd=HERE
                )
                self.assertEqual(ancestor.returncode, 0, f"{base} is not an ancestor of HEAD")
                diff = subprocess.run(
                    ["git", "diff", "--numstat", base, "--",
                     os.path.join(HERE, "program.py"), os.path.join(HERE, "calculations.py")],
                    cwd=HERE, capture_output=True, text=True, check=True,
                )
                self.assertEqual(diff.stdout.strip(), "")

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
        "program_lines_changed", "program_lines_changed_base", "input_parts_changed",
        "invocations_skippable_by_digest", "ms_saved", "ms_saved_by_invocation",
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
        # run-4 both drops an input Part (rows: it consumes run-1's retained split
        # instead) and adds one (the split itself). Both halves of that boundary move
        # are reported, because both are differences between the two records'
        # external maps (second_experiment.input_parts_changed).
        self._check(self.from_retained, ["input.ablation.rows", "scratch.ablation.split"])
        payload = _load(self.from_retained, "saved-work.json")
        self.assertEqual(payload["invocations_skippable_by_digest"], ["split"])
        self.assertEqual(payload["skip_reason"], "removed")
        self.assertGreater(payload["ms_saved"], 0)
        self.assertEqual(payload["ms_saved_by_invocation"]["split"], self.receipts_1["split"]["duration_ms"])


class InputPartsChangedIsComputed(ThreeRunsGenerated):
    """Finding 4: `input_parts_changed` is derived from the records, never asserted.

    Each of the three scripts used to hand `second_experiment.saved_work` a literal
    list naming what its author believed the run had changed. The field therefore
    agreed with the script's intent by construction: a script that changed a
    DIFFERENT input Part, or none at all, would have published the same sentence.
    It is now computed from the two retained records' external digests, and
    `saved_work` no longer accepts it as a parameter at all -- which is what makes
    "never passed as a literal" checkable rather than a convention.
    """

    def test_saved_work_has_no_input_parts_changed_parameter(self):
        """Kills: re-adding the parameter. A keyword nobody may pass cannot be a literal."""
        import inspect

        parameters = inspect.signature(se.saved_work).parameters
        self.assertNotIn("input_parts_changed", parameters)
        for name in ("record_prior", "record_this"):
            self.assertIn(name, parameters)

    def test_no_run_script_names_the_field(self):
        for name in ("run_regrouped.py", "run_reinput.py", "run_from_retained.py"):
            with self.subTest(script=name):
                with open(os.path.join(HERE, name), encoding="utf-8") as handle:
                    self.assertNotIn("input_parts_changed", handle.read())

    def test_each_run_reports_exactly_what_the_two_records_disagree_on(self):
        for out, prior in (
            (self.regroup, self.record_1),
            (self.reinput, self.record_1),
            (self.from_retained, self.record_1),
        ):
            with self.subTest(out=os.path.basename(out)):
                record = _load(out, "retained.json")
                self.assertEqual(
                    _load(out, "saved-work.json")["input_parts_changed"],
                    se.input_parts_changed(prior, record),
                )

    def test_external_digests_are_the_same_measurement_as_the_records_results(self):
        """The digest an external carries is `retain.digest_of` over canonical JSON,
        the same function that produced `record['results']` -- not a separate notion."""
        digests = se.external_digests(self.record_1)
        self.assertEqual(sorted(digests), sorted(self.record_1["external"]))
        for address, value in self.record_1["external"].items():
            self.assertEqual(digests[address], run_regrouped.retain.digest_of(value))

    def test_an_unchanged_input_part_is_not_listed(self):
        """A record compared with itself changes nothing."""
        self.assertEqual(se.input_parts_changed(self.record_1, self.record_1), [])

    def test_a_changed_value_at_an_unchanged_address_is_detected(self):
        """Kills: comparing address SETS instead of digests. Both records here declare
        exactly the same two external addresses; only one value moved."""
        forged = copy.deepcopy(self.record_1)
        forged["external"]["input.ablation.rows"][0][1] += 1.0
        self.assertEqual(
            sorted(forged["external"]), sorted(self.record_1["external"])
        )
        self.assertEqual(
            se.input_parts_changed(self.record_1, forged), ["input.ablation.rows"]
        )

    def test_a_sidecar_external_is_compared_by_its_recorded_digest(self):
        """A value JSON cannot inline is referenced as {"digest", "ref"}; the digest is
        the comparison, so a sidecar whose bytes changed is a changed input Part and a
        sidecar merely renamed is not."""
        left = copy.deepcopy(self.record_1)
        right = copy.deepcopy(self.record_1)
        left["external"]["input.ablation.rows"] = {"digest": "a" * 64, "ref": "left.json"}
        right["external"]["input.ablation.rows"] = {"digest": "a" * 64, "ref": "right.json"}
        self.assertEqual(se.input_parts_changed(left, right), [])
        right["external"]["input.ablation.rows"] = {"digest": "b" * 64, "ref": "right.json"}
        self.assertEqual(se.input_parts_changed(left, right), ["input.ablation.rows"])


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

    def test_regroup_interpretation_records_the_refuted_prediction_with_both_numbers(self):
        """Fixer round 1, finding 10: the +0.9 sentence used to glue a computed False to a
        because-clause of literals. Every supporting number is now read from evidence."""
        text = _read(self.regroup, "interpretation.md")
        comparison = _load(self.regroup, "comparison.json")
        biggest = max(abs(row["delta_vs_baseline"]) for row in comparison["rows"] if row["variant"] != "all")
        run_1_rows = _load(RUN_1, "comparison.json")["rows"]
        run_1_biggest = max(abs(row["delta_vs_baseline"]) for row in run_1_rows if row["variant"] != "all")
        verdict = "held" if biggest <= 0.9 else "REFUTED by measurement"
        self.assertIn(f"The predicted bound is {verdict}: {biggest:.4f} against the predicted <= 0.9.", text)
        self.assertIn(
            f"Run-1's largest |delta vs baseline| (evidence/run-1/comparison.json): {run_1_biggest:.4f}.",
            text,
        )
        weights = run_regrouped.planted_weight_per_group(run_regrouped.CROSS_GROUPS)
        self.assertIn(f"this run (CROSS_GROUPS): {weights}", text)
        self.assertIn(f"cross-cutting {max(weights.values())}", text)

    def test_regroup_interpretation_reports_shared_changed_ids_from_explain_changes(self):
        """Fixer round 1, finding 9: it used to assert 'added/removed ids, not a digest
        drift on a shared id' while its own ledger listed three shared ids that drifted."""
        text = _read(self.regroup, "interpretation.md")
        saved = _load(self.regroup, "saved-work.json")
        explanation = saved["explain_changes"]
        shared_changed = {i: explanation["reason"][i] for i in explanation["changed"]}
        self.assertTrue(shared_changed, "expected at least one shared id to have changed")
        self.assertIn(f"computed: {shared_changed}", text)
        self.assertIn(f"Ids only in this run (added): {explanation['added']}", text)
        self.assertIn(f"Ids only in run-1 (removed): {explanation['removed']}", text)
        self.assertNotIn("not a digest drift on a shared id", text)

    def test_reinput_interpretation_names_n_from_the_fixture_not_a_literal(self):
        text = _read(self.reinput, "interpretation.md")
        self.assertIn(f"n={run_reinput.N}", text)
        self.assertIn(f"seed={run_reinput.SEED}", text)


@unittest.skipUnless(os.path.isdir(RUN_1), "evidence/run-1 not generated yet")
class CommittedEvidenceResolvesToCommittedRunOne(unittest.TestCase):
    """The COMMITTED run-2/3/4 ledgers must resolve against the COMMITTED run-1 receipts.

    Fixer round 2, finding 7 and finding 12: `ms_saved` / `ms_saved_by_invocation` are
    wall-clock durations read out of `evidence/run-1/receipts.json`
    (second_experiment.py:230-248), and they sit in `saved-work.json`, which
    `Determinism` byte-compares. `TimingsAndSavedWork` already asserts the same
    equality -- but only against runs it regenerates itself into temp dirs, so run-1
    could be (and was) regenerated on its own, leaving all three committed ledgers
    quoting a duration that appears in no retained receipts file, and
    `interpretation.md` stating it as a fact about a file it no longer matched.
    Nothing in the suite noticed, because two fresh regenerations read the same frozen
    run-1 and agreed with each other.

    This class reads only what is on disk. Regenerating run-1 without regenerating
    runs 2-4 fails here, naming the command (see CHANGES.md, "run-1 first").
    """

    @classmethod
    def setUpClass(cls):
        cls.receipts_1 = _load(RUN_1, "receipts.json")

    def _committed(self, name: str) -> str:
        path = os.path.join(EVIDENCE, name)
        self.assertTrue(os.path.isdir(path), f"committed evidence/{name} is missing")
        return path

    def test_every_committed_ms_saved_entry_is_a_committed_run_1_duration(self):
        for name in ("run-2-regroup", "run-3-reinput", "run-4-from-retained"):
            with self.subTest(run=name):
                out = self._committed(name)
                payload = _load(out, "saved-work.json")
                by_invocation = payload["ms_saved_by_invocation"]
                self.assertTrue(by_invocation, f"{name} claims no saved work at all")
                for invocation_id, ms in by_invocation.items():
                    self.assertIn(invocation_id, self.receipts_1, f"{name}/{invocation_id}")
                    self.assertEqual(
                        ms,
                        self.receipts_1[invocation_id]["duration_ms"],
                        f"evidence/{name}/saved-work.json is stale against "
                        f"evidence/run-1/receipts.json; regenerate it with "
                        f"`python3 run_regrouped.py|run_reinput.py|run_from_retained.py "
                        f"--out evidence/{name} --force`",
                    )
                self.assertEqual(
                    payload["ms_saved"], round(sum(by_invocation.values()), 3)
                )

    def test_every_committed_interpretation_quotes_its_own_ms_saved(self):
        """run_regrouped.py:123, run_reinput.py:54 and run_from_retained.py:92 print
        `ms saved (...): <n>` into interpretation.md; the ledger and the prose must be
        the same number."""
        for name in ("run-2-regroup", "run-3-reinput", "run-4-from-retained"):
            with self.subTest(run=name):
                out = self._committed(name)
                ms_saved = _load(out, "saved-work.json")["ms_saved"]
                text = _read(out, "interpretation.md")
                line = next(l for l in text.splitlines() if "ms saved (" in l)
                self.assertEqual(line.rsplit(": ", 1)[1], str(ms_saved), line)

    def test_the_committed_prior_run_is_the_one_this_pin_reads(self):
        for name in ("run-2-regroup", "run-3-reinput", "run-4-from-retained"):
            with self.subTest(run=name):
                self.assertEqual(_load(self._committed(name), "saved-work.json")["prior_run"], "run-1")


class RetainedDigestsEqualReceiptDigests(unittest.TestCase):
    """Finding 6, on the COMMITTED evidence: `retained.json`'s `results[id]` equals
    `receipts.json`'s `result_sha256[id]`, for every id of every run.

    They are the same measurement of one object taken at two moments (documented at
    `retain.retain_run`): `pcr.py:334-336` publishes the value a Calculation returned
    into `run.results[id]` -- and into the PxC, when there is an `into` -- as the very
    same object, with no copy; `pyto.pcr._result_sha256` digests it at the instant the
    invocation returns, and `retain.digest_of` digests the same alias once the run has
    finished. Both are sha256 over `json.dumps(value, sort_keys=True,
    separators=(",", ":"))` with no `default=`.

    So an inequality here is not a formatting difference to reconcile: it means
    something mutated the object between the two moments. Nothing in this registry
    does, and this test is what would say so if something started.
    """

    def test_every_committed_run_agrees_id_by_id(self):
        for name in COMMITTED_RUNS:
            with self.subTest(run=name):
                out = os.path.join(EVIDENCE, name)
                record = _load(out, "retained.json")
                receipts = _load(out, "receipts.json")
                self.assertEqual(sorted(record["results"]), sorted(receipts))
                for invocation_id, digest in record["results"].items():
                    self.assertEqual(
                        digest,
                        receipts[invocation_id]["result_sha256"],
                        f"{name}/{invocation_id}: retained.json's digest and "
                        f"receipts.json's result_sha256 describe the same object at two "
                        f"moments; regenerate the run if this is an intended change",
                    )

    def test_the_run_ids_are_the_programs_invocation_ids(self):
        """Neither file may quietly cover a different set of invocations than the program."""
        for name in COMMITTED_RUNS:
            with self.subTest(run=name):
                out = os.path.join(EVIDENCE, name)
                record = _load(out, "retained.json")
                ids = sorted(
                    entry["id"]
                    for tick in record["program"]["ticks"]
                    for entry in tick["calculations"]
                )
                self.assertEqual(sorted(record["results"]), ids)
                self.assertEqual(sorted(_load(out, "receipts.json")), ids)

    def test_the_aliasing_is_documented_where_the_digest_is_taken(self):
        """The claim above must live in the code, not only in a test name."""
        doc = run_regrouped.retain.retain_run.__doc__
        self.assertIn("same measurement of one object taken at two moments", doc)
        self.assertIn("result_sha256", doc)

    def test_run_4_has_no_split_in_either_file(self):
        """The one run whose invocation set differs: split is an external Part there,
        so it is absent from both the digests and the receipts rather than zeroed."""
        out = os.path.join(EVIDENCE, "run-4-from-retained")
        self.assertNotIn("split", _load(out, "retained.json")["results"])
        self.assertNotIn("split", _load(out, "receipts.json"))


class ReceiptsDeterminism(unittest.TestCase):
    """Finding 5: receipts.json is deterministic apart from its two wall-clock fields.

    `Determinism` below already asserts that receipts.json TEXT differs across two
    regenerations -- but text-differs is satisfied by a single changed millisecond and
    says nothing about the rest of the receipt. This parses both files, drops
    `started_ms` and `duration_ms` from every receipt, and requires the remainder --
    the frozen calculation and its implementation digest, declared/actual consumes and
    produces, writes, result_sha256, effective arg keys, shadowed inputs -- to be
    equal, while requiring the timings themselves to differ so the comparison is not
    trivially satisfied by a frozen clock.
    """

    def _two_regenerations(self, main, run_label: str) -> tuple[dict, dict]:
        parent = tempfile.mkdtemp(prefix="receipts-determinism-")
        self.addCleanup(shutil.rmtree, parent, ignore_errors=True)
        a = os.path.join(parent, "a", run_label)
        b = os.path.join(parent, "b", run_label)
        self.assertEqual(_run_into(main, a), 0)
        self.assertEqual(_run_into(main, b), 0)
        return _load(a, "receipts.json"), _load(b, "receipts.json")

    def _check(self, main, run_label: str):
        first, second = self._two_regenerations(main, run_label)
        self.assertEqual(sorted(first), sorted(second))
        self.assertEqual(
            receipts_without_timings(first),
            receipts_without_timings(second),
            f"{run_label}: receipts.json differs across two regenerations in a field "
            f"that is not a timing",
        )
        differing = [
            invocation_id
            for invocation_id in first
            if any(first[invocation_id][key] != second[invocation_id][key] for key in RECEIPT_TIMING_KEYS)
        ]
        self.assertTrue(
            differing,
            f"{run_label}: no receipt's started_ms or duration_ms differed across two "
            f"real runs, so the equality above proves nothing about what was dropped",
        )
        # The keys that were dropped are exactly the two named, and both really are
        # present on every receipt (a renamed field would silently stop being dropped).
        for invocation_id, receipt in first.items():
            for key in RECEIPT_TIMING_KEYS:
                self.assertIn(key, receipt, invocation_id)

    @unittest.skipUnless(os.path.isdir(RUN_1), "evidence/run-1 not generated yet")
    def test_run_regrouped_receipts_are_deterministic_apart_from_timings(self):
        self._check(run_regrouped.main, "run-2-regroup")

    @unittest.skipUnless(os.path.isdir(RUN_1), "evidence/run-1 not generated yet")
    def test_run_reinput_receipts_are_deterministic_apart_from_timings(self):
        self._check(run_reinput.main, "run-3-reinput")

    @unittest.skipUnless(os.path.isdir(RUN_1), "evidence/run-1 not generated yet")
    def test_run_from_retained_receipts_are_deterministic_apart_from_timings(self):
        self._check(run_from_retained.main, "run-4-from-retained")

    @unittest.skipUnless(os.path.isdir(RUN_1), "evidence/run-1 not generated yet")
    def test_the_committed_receipts_survive_the_same_comparison(self):
        """A regeneration of run-2 must agree with the COMMITTED run-2 receipts too,
        modulo timings -- otherwise the committed file is stale and the comparison
        above only proves two fresh runs agree with each other."""
        first, _second = self._two_regenerations(run_regrouped.main, "run-2-regroup")
        committed = _load(os.path.join(EVIDENCE, "run-2-regroup"), "receipts.json")
        self.assertEqual(
            receipts_without_timings(first),
            receipts_without_timings(committed),
            "evidence/run-2-regroup/receipts.json is stale; regenerate it with "
            "`python3 run_regrouped.py --out evidence/run-2-regroup --force`",
        )


class EvidenceIsNeverRewritten(unittest.TestCase):
    """Finding 1, from this module's side: regenerating runs must not touch evidence/.

    `test_replay.py::CheckAllLeavesTheTreeClean` is the end-to-end version (it runs
    both modules in a child interpreter and reads git status). This is the fast,
    local one: run all three scripts the way the tests do and require the committed
    evidence directories to be byte-identical afterwards.
    """

    @unittest.skipUnless(os.path.isdir(RUN_1), "evidence/run-1 not generated yet")
    def test_regenerating_all_three_runs_leaves_the_committed_evidence_alone(self):
        before = {}
        for name in COMMITTED_RUNS:
            directory = os.path.join(EVIDENCE, name)
            for entry in sorted(os.listdir(directory)):
                path = os.path.join(directory, entry)
                if os.path.isfile(path):
                    with open(path, "rb") as handle:
                        before[f"{name}/{entry}"] = handle.read()
        tmp = tempfile.mkdtemp(prefix="never-rewritten-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        for main, label in (
            (run_regrouped.main, "run-2-regroup"),
            (run_reinput.main, "run-3-reinput"),
            (run_from_retained.main, "run-4-from-retained"),
        ):
            self.assertEqual(_run_into(main, os.path.join(tmp, label)), 0)
        after = {}
        for key in before:
            name, entry = key.split("/", 1)
            with open(os.path.join(EVIDENCE, name, entry), "rb") as handle:
                after[key] = handle.read()
        changed = sorted(key for key in before if before[key] != after[key])
        self.assertEqual(changed, [], f"regenerating into a temp dir modified {changed}")


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
