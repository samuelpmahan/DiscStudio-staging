"""Day 1 experiment tests for the grouped ablation (run with python3 -m unittest)."""

from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from calculations import REGISTRY  # noqa: E402
from features import FEATURES, GROUPS  # noqa: E402
from run import (  # noqa: E402
    AUTHORING_FILES,
    WATCHED_PATHS,
    commit_sha,
    dirty_paths,
    failed_variants,
    jsonable,
    main,
    ranking,
    resolve_out_dir,
    run_experiment,
    saved_work,
    write_evidence,
)

SEEDS = (7, 11, 13)
EXPECTED_TOP = ["drop_g3", "drop_g0", "drop_g1"]
UNINFORMATIVE = ("drop_g2", "drop_g4")
FORBIDDEN_TOKENS = ("lambda", "<function")
COMMIT_LINE = re.compile(r"^[0-9a-f]{40}(-dirty)?\n$")
GIT_IDENTITY = ("-c", "user.name=grouped-ablation-test", "-c", "user.email=grouped-ablation-test@example.invalid")


def _fit_score_testimonies(testimony: dict) -> list[dict]:
    return [
        calc
        for tick in testimony["ticks"]
        for calc in tick["calculations"]
        if calc["id"].startswith("fit.") or calc["id"].startswith("score.")
    ]


class GroupedAblationRanking(unittest.TestCase):
    """Kill criterion: planted ranking recovered deterministically across seeds 7, 11, 13."""

    @classmethod
    def setUpClass(cls):
        cls.results = {seed: run_experiment(seed, 400) for seed in SEEDS}

    def test_ranking_drop_g3_then_g0_then_g1_across_seeds(self):
        for seed, result in self.results.items():
            with self.subTest(seed=seed):
                self.assertEqual(ranking(result["comparison"])[:3], EXPECTED_TOP)

    def test_groups_without_planted_weight_are_uninformative(self):
        for seed, result in self.results.items():
            deltas = {row["variant"]: row["delta_vs_baseline"] for row in result["comparison"]}
            for key in UNINFORMATIVE:
                with self.subTest(seed=seed, variant=key):
                    self.assertLess(abs(deltas[key]), 0.05)

    def test_failed_variants_are_retained_not_hidden(self):
        for seed, result in self.results.items():
            with self.subTest(seed=seed):
                flagged = {row["variant"] for row in failed_variants(result["comparison"])}
                self.assertEqual(flagged, set(UNINFORMATIVE))
                self.assertTrue(flagged <= set(ranking(result["comparison"])))

    def test_ranking_is_deterministic_for_same_seed(self):
        again = run_experiment(7, 400)
        self.assertEqual(again["comparison"], self.results[7]["comparison"])
        self.assertEqual(again["testimony"], self.results[7]["testimony"])


class GroupedAblationTestimony(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_experiment(7, 400)
        cls.testimony = cls.result["testimony"]

    def test_ticks_are_prepare_fit_score_compare(self):
        self.assertEqual([tick["name"] for tick in self.testimony["ticks"]], ["Prepare", "Fit", "Score", "Compare"])

    def test_all_twelve_fit_and_score_invocations_consume_fn_split(self):
        calcs = _fit_score_testimonies(self.testimony)
        self.assertEqual(len(calcs), 12)
        for calc in calcs:
            with self.subTest(id=calc["id"]):
                self.assertEqual(calc["inputs"]["split"], "fn:split")

    def test_score_consumes_fn_fit_and_compare_consumes_fn_scores(self):
        by_id = {calc["id"]: calc for tick in self.testimony["ticks"] for calc in tick["calculations"]}
        for variant in self.result["variants"]:
            key = variant["key"]
            self.assertEqual(by_id[f"score.{key}"]["inputs"]["model"], f"fn:fit.{key}")
            self.assertEqual(by_id["compare"]["inputs"][key], f"fn:score.{key}")
        self.assertEqual(by_id["split"]["inputs"], {"rows": "px:input.ablation.rows"})

    def test_no_args_key_collides_with_a_bound_input_name(self):
        # pcr.py:159-160 call_args.update(invocation.args) silently overrides same-named inputs.
        for tick in self.testimony["ticks"]:
            for calc in tick["calculations"]:
                with self.subTest(id=calc["id"]):
                    self.assertEqual(set(calc["args"]) & set(calc["inputs"]), set())

    def test_testimony_json_round_trip_equals_asdict(self):
        run = self.result["run"]
        as_dict = {"pcr": run.pcr, "ticks": [dataclasses.asdict(tick) for tick in run.ticks]}
        # asdict keeps the tuple field (pcr.py:73); the only difference after JSON is tuple -> list.
        self.assertIsInstance(as_dict["ticks"][0]["calculations"], tuple)
        self.assertEqual(json.loads(json.dumps(self.testimony)), self.testimony)
        self.assertEqual(json.loads(json.dumps(as_dict)), jsonable(as_dict))
        self.assertEqual(self.testimony, jsonable(as_dict))
        for tick_json, tick in zip(self.testimony["ticks"], run.ticks):
            self.assertEqual(tuple(tick_json["calculations"]), tuple(dataclasses.asdict(c) for c in tick.calculations))


class GroupedAblationVariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_experiment(7, 400)

    def test_exactly_five_ablation_variants_never_32768(self):
        variants = self.result["variants"]
        ablations = [v for v in variants if v["kind"] == "ablation"]
        self.assertEqual(len(ablations), 5)
        self.assertEqual(len(variants), 6)  # 5 leave-one-group-out + baseline 'all'
        self.assertNotEqual(len(variants), 2 ** len(FEATURES))
        self.assertLess(len(variants), 32768)
        for variant in ablations:
            self.assertEqual(len(variant["drop"]), 1)
            self.assertEqual(len(variant["columns"]), 12)
        self.assertEqual([v["key"] for v in variants], ["all"] + [f"drop_{g}" for g in GROUPS])

    def test_registry_is_module_functions_without_lambdas(self):
        self.assertEqual(
            sorted(REGISTRY),
            ["fn.ablation.compare", "fn.ablation.fit", "fn.ablation.score", "fn.ablation.selectVariants", "fn.ablation.split"],
        )
        for address, calculation in REGISTRY.items():
            self.assertEqual(calculation.address, address)
            self.assertNotEqual(calculation.calculate.__name__, "<lambda>")
            self.assertEqual(calculation.calculate.__module__, "calculations")


class GroupedAblationEvidence(unittest.TestCase):
    EXPECTED_FILES = [
        "commit.txt", "comparison.json", "comparison.md", "failed-variants.md", "mermaid.mmd",
        "saved-work.json", "testimony.json", "timings.json", "variants.json",
    ]

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="grouped-ablation-")
        cls.result = run_experiment(7, 400)
        cls.files = write_evidence(cls.result, cls.tmp)

    def _read(self, name: str) -> str:
        with open(os.path.join(self.tmp, name), encoding="utf-8") as fh:
            return fh.read()

    def test_evidence_file_set(self):
        self.assertEqual(self.files, self.EXPECTED_FILES)

    def test_evidence_contains_no_lambda_or_function_repr(self):
        for name in self.files:
            text = self._read(name)
            for token in FORBIDDEN_TOKENS:
                with self.subTest(file=name, token=token):
                    self.assertNotIn(token, text)

    def test_testimony_file_is_pcr_and_ticks_only(self):
        payload = json.loads(self._read("testimony.json"))
        self.assertEqual(sorted(payload), ["pcr", "ticks"])
        self.assertEqual(payload, self.result["testimony"])

    def test_saved_work_counts_match_run(self):
        payload = json.loads(self._read("saved-work.json"))
        self.assertEqual(payload["calculations_authored"], len(REGISTRY))
        self.assertEqual(payload["invocations_executed"], sum(len(t["calculations"]) for t in self.result["testimony"]["ticks"]))
        self.assertEqual(payload["ablation_variants"], 5)
        self.assertGreater(payload["authoring_lines_total"], 0)
        self.assertGreater(payload["wall_ms"]["pcr.run"], 0)

    def test_saved_work_run_label_is_the_out_dir_basename_with_no_prior(self):
        """run.py saved_work: `run` is basename(out_dir) and Day 1 has no prior ledger (round 2, finding 2).
        Mutation (scratch copy of run.py): `"run": os.path.basename(os.path.normpath(out_dir))` ->
        `"run": "run-1 baseline"` fails the first assertion."""
        payload = json.loads(self._read("saved-work.json"))
        self.assertEqual(payload["run"], os.path.basename(self.tmp))
        self.assertIsNone(payload["prior_run"])
        self.assertEqual(payload["inherited_calculations"], 0)
        self.assertEqual(payload["inherited_addresses"], [])

    def test_saved_work_carries_no_literal_reuse_counts(self):
        """invocations_skipped and ms_saved need Day 2's result digests; run-1 must not write them as literal zeros.
        Mutation: re-adding `"invocations_skipped": 0,` to the saved_work dict fails this test."""
        payload = json.loads(self._read("saved-work.json"))
        self.assertNotIn("invocations_skipped", payload)
        self.assertNotIn("ms_saved", payload)

    def test_saved_work_binds_authoring_files_by_sha256(self):
        """saved-work.json carries sha256 of features.py, calculations.py, program.py so the evidence binds
        to file content regardless of commit state (round 2, finding 1).
        Mutation: `hashlib.sha256(fh.read())` -> `hashlib.sha256(path.encode())` in run._sha256 fails this test."""
        payload = json.loads(self._read("saved-work.json"))
        expected = {}
        for name in AUTHORING_FILES:
            with open(os.path.join(HERE, name), "rb") as fh:
                expected[name] = hashlib.sha256(fh.read()).hexdigest()
        self.assertEqual(sorted(expected), ["calculations.py", "features.py", "program.py"])
        self.assertEqual(payload["authoring_sha256"], expected)

    def test_saved_work_derives_inheritance_from_a_prior_ledger(self):
        """inherited_calculations = len(REGISTRY & prior addresses), not a literal; the prior's own name is recorded.
        Mutation: `len(inherited)` -> `len(prior_addresses)` gives 3 here and fails; `"prior_run": None if prior is None
        else prior["run"]` -> `"prior_run": None` fails the second assertion."""
        prior = {"run": "run-0-fake", "calculation_addresses": ["fn.ablation.fit", "fn.ablation.split", "fn.other.notHere"]}
        payload = saved_work(self.result, "/nowhere/run-9", prior)
        self.assertEqual(payload["run"], "run-9")
        self.assertEqual(payload["prior_run"], "run-0-fake")
        self.assertEqual(payload["inherited_calculations"], 2)
        self.assertEqual(payload["inherited_addresses"], ["fn.ablation.fit", "fn.ablation.split"])
        self.assertEqual(payload["calculations_authored"], len(REGISTRY))
        self.assertEqual(saved_work(self.result, "/nowhere/run-9/", None)["run"], "run-9")

    def test_commit_txt_is_head_sha_with_dirty_marker_iff_watched_paths_changed(self):
        """commit.txt = `git rev-parse HEAD` plus `-dirty` exactly when this experiment dir or pyto/src differs
        from HEAD (round 2, finding 1), so a bare sha means the producing code is in that commit.
        Mutation: `WATCHED_PATHS = (HERE, SRC_DIR)` -> `WATCHED_PATHS = (HERE,)` (stop watching the library) fails the
        WATCHED_PATHS assertion unconditionally; `return f"{sha}-dirty" if ... else sha` -> `return sha` fails the
        iff assertion whenever the tree is dirty (state-dependent; CommitShaDirtyMarker kills it unconditionally)."""
        text = self._read("commit.txt")
        self.assertRegex(text, COMMIT_LINE)
        self.assertEqual(text, commit_sha() + "\n")
        self.assertEqual(text.endswith("-dirty\n"), bool(dirty_paths()))
        self.assertEqual(WATCHED_PATHS, (HERE, os.path.normpath(os.path.join(HERE, "..", "..", "src"))))
        self.assertTrue(all(os.path.isdir(p) for p in WATCHED_PATHS))

    def test_comparison_md_lists_drop_g3_first(self):
        text = self._read("comparison.md")
        first_row = [line for line in text.splitlines() if line.startswith("| 1 |")][0]
        self.assertIn("drop_g3", first_row)

    def test_mermaid_names_every_invocation_and_split_edges(self):
        text = self._read("mermaid.mmd")
        self.assertTrue(text.startswith("flowchart TD"))
        for variant in self.result["variants"]:
            self.assertIn(f"split -->|split| fit.{variant['key']}", text)
            self.assertIn(f"split -->|split| score.{variant['key']}", text)

    def test_checked_in_run_1_matches_seed_7(self):
        run1 = os.path.join(HERE, "evidence", "run-1")
        if not os.path.isdir(run1):
            self.skipTest("evidence/run-1 not generated yet; run run.py")
        with open(os.path.join(run1, "comparison.json"), encoding="utf-8") as fh:
            payload = json.load(fh)
        if payload["seed"] != 7 or payload["n"] != 400:
            self.skipTest(f"evidence/run-1 was generated with seed={payload['seed']} n={payload['n']}")
        self.assertEqual(payload["rows"], self.result["comparison"])


class CommitShaDirtyMarker(unittest.TestCase):
    """commit_sha(repo_dir, watch) in a throwaway git repository: the -dirty marker follows the watched paths
    (modified, staged, untracked), and a change outside the watch list leaves the sha bare.
    Mutation (scratch copy of run.py): `return f"{sha}-dirty" if dirty_paths(repo_dir, watch) else sha` -> `return sha`
    fails test_dirty_marker_follows_modified_and_untracked_files; `[line[3:] for line in ...]` -> `[]` fails it too."""

    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="grouped-ablation-git-")
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        self.watched = os.path.join(self.repo, "watched")
        os.makedirs(self.watched)
        self._git("init", "-q")
        self._write("watched/a.txt", "one\n")
        self._write("outside.txt", "one\n")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")

    def _git(self, *args: str) -> str:
        proc = subprocess.run(["git", *GIT_IDENTITY, *args], capture_output=True, text=True, cwd=self.repo, check=True)
        return proc.stdout

    def _write(self, rel: str, text: str) -> None:
        with open(os.path.join(self.repo, rel), "w", encoding="utf-8") as fh:
            fh.write(text)

    def test_dirty_marker_follows_modified_and_untracked_files(self):
        head = self._git("rev-parse", "HEAD").strip()
        self.assertEqual(commit_sha(self.repo, (self.watched,)), head)
        self.assertEqual(dirty_paths(self.repo, (self.watched,)), [])

        self._write("watched/a.txt", "two\n")
        self.assertEqual(commit_sha(self.repo, (self.watched,)), head + "-dirty")
        self.assertEqual(dirty_paths(self.repo, (self.watched,)), ["watched/a.txt"])

        self._git("commit", "-q", "-am", "edit")
        head2 = self._git("rev-parse", "HEAD").strip()
        self.assertNotEqual(head2, head)
        self.assertEqual(commit_sha(self.repo, (self.watched,)), head2)

        self._write("watched/b.txt", "new\n")  # untracked counts: code not in any commit
        self.assertEqual(commit_sha(self.repo, (self.watched,)), head2 + "-dirty")
        self.assertEqual(dirty_paths(self.repo, (self.watched,)), ["watched/b.txt"])

    def test_change_outside_the_watch_list_leaves_the_sha_bare(self):
        head = self._git("rev-parse", "HEAD").strip()
        self._write("outside.txt", "two\n")
        self.assertEqual(commit_sha(self.repo, (self.watched,)), head)
        self.assertEqual(commit_sha(self.repo, (self.watched, self.repo)), head + "-dirty")
        self.assertEqual(dirty_paths(self.repo, (self.repo,)), ["outside.txt"])

    def test_write_evidence_records_the_dirty_marker_in_commit_txt(self):
        """The wiring: write_evidence's commit.txt is commit_sha(repo_dir, watch), so a dirty watched tree reaches the file.
        Mutation: `commit_sha(repo_dir, watch) + "\\n"` in write_evidence -> `commit_sha(repo_dir, watch).removesuffix("-dirty") + "\\n"`
        fails the second assertion."""
        head = self._git("rev-parse", "HEAD").strip()
        result = run_experiment(7, 400)
        out = tempfile.mkdtemp(prefix="grouped-ablation-evidence-")
        self.addCleanup(shutil.rmtree, out, ignore_errors=True)
        write_evidence(result, out, None, self.repo, (self.watched,))
        with open(os.path.join(out, "commit.txt"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), head + "\n")
        self._write("watched/a.txt", "two\n")
        write_evidence(result, out, None, self.repo, (self.watched,))
        with open(os.path.join(out, "commit.txt"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), head + "-dirty\n")
        with open(os.path.join(out, "saved-work.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["run"], os.path.basename(out))

    def test_outside_a_repository_reports_unavailable_instead_of_a_sha(self):
        bare = tempfile.mkdtemp(prefix="grouped-ablation-nogit-")
        self.addCleanup(shutil.rmtree, bare, ignore_errors=True)
        env_free = dict(os.environ, GIT_CEILING_DIRECTORIES=os.path.dirname(bare))
        with unittest.mock.patch.dict(os.environ, env_free):
            self.assertTrue(commit_sha(bare, (bare,)).startswith("unavailable: "))


def _snapshot(directory: str) -> dict[str, bytes]:
    """name -> bytes for every file in directory ({} when it does not exist)."""
    if not os.path.isdir(directory):
        return {}
    out = {}
    for name in sorted(os.listdir(directory)):
        with open(os.path.join(directory, name), "rb") as fh:
            out[name] = fh.read()
    return out


class GroupedAblationOutDir(unittest.TestCase):
    """run.py never rewrites the tracked evidence/run-1 by accident (Day 1 fixer round 1, finding 2):
    the default --out is a fresh temp dir and an existing non-empty --out is refused without --force.
    Mutations (scratch copy of run.py): resolve_out_dir's `if ... and not force:` -> `if False:` kills
    test_existing_non_empty_out_is_refused_without_force; `tempfile.mkdtemp(...)` ->
    `os.path.join(HERE, "evidence", "run-1")` kills test_main_without_out_leaves_tracked_run_1_untouched."""

    RUN_1 = os.path.join(HERE, "evidence", "run-1")

    def test_default_out_is_a_fresh_empty_directory_outside_evidence(self):
        out_dir = resolve_out_dir(None, False)
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        self.assertTrue(os.path.isdir(out_dir))
        self.assertEqual(os.listdir(out_dir), [])
        self.assertFalse(out_dir.startswith(os.path.join(HERE, "evidence")))

    def test_main_without_out_leaves_tracked_run_1_untouched(self):
        before = _snapshot(self.RUN_1)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            rc = main([])
        self.assertEqual(rc, 0)
        wrote = [line for line in stdout.getvalue().splitlines() if line.startswith("wrote ")]
        self.assertEqual(len(wrote), 1)
        out_dir = wrote[0].split()[1]
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        self.assertFalse(out_dir.startswith(os.path.join(HERE, "evidence")))
        self.assertEqual(sorted(os.listdir(out_dir)), GroupedAblationEvidence.EXPECTED_FILES)
        self.assertEqual(_snapshot(self.RUN_1), before)
        self.assertIn("| 1 | drop_g3 |", stdout.getvalue())

    def test_existing_non_empty_out_is_refused_without_force(self):
        tmp = tempfile.mkdtemp(prefix="grouped-ablation-existing-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        sentinel = os.path.join(tmp, "commit.txt")
        with open(sentinel, "w", encoding="utf-8") as fh:
            fh.write("keep me\n")
        with self.assertRaises(FileExistsError):
            resolve_out_dir(tmp, False)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            rc = main(["--out", tmp])
        self.assertEqual(rc, 2)
        self.assertIn("--force", stderr.getvalue())
        self.assertEqual(os.listdir(tmp), ["commit.txt"])
        with open(sentinel, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "keep me\n")

    def test_force_overwrites_and_an_empty_existing_dir_is_accepted(self):
        tmp = tempfile.mkdtemp(prefix="grouped-ablation-force-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.assertEqual(resolve_out_dir(tmp, False), tmp)  # empty: nothing to protect
        with open(os.path.join(tmp, "commit.txt"), "w", encoding="utf-8") as fh:
            fh.write("stale\n")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = main(["--out", tmp, "--force"])
        self.assertEqual(rc, 0)
        self.assertEqual(sorted(os.listdir(tmp)), GroupedAblationEvidence.EXPECTED_FILES)
        with open(os.path.join(tmp, "commit.txt"), encoding="utf-8") as fh:
            self.assertNotEqual(fh.read(), "stale\n")


if __name__ == "__main__":
    unittest.main()
