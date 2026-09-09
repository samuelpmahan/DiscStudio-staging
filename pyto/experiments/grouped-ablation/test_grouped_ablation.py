"""Day 1 experiment tests for the grouped ablation (run with python3 -m unittest)."""

from __future__ import annotations

import dataclasses
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from calculations import REGISTRY  # noqa: E402
from features import FEATURES, GROUPS  # noqa: E402
from run import failed_variants, jsonable, ranking, run_experiment, write_evidence  # noqa: E402

SEEDS = (7, 11, 13)
EXPECTED_TOP = ["drop_g3", "drop_g0", "drop_g1"]
UNINFORMATIVE = ("drop_g2", "drop_g4")
FORBIDDEN_TOKENS = ("lambda", "<function")


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


if __name__ == "__main__":
    unittest.main()
