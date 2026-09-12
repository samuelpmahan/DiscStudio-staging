"""`python -m pyto.study`, executed: the two worked examples, end to end.

The study is a claim about a table, so what this suite checks is the claim: the
summary's sentences against the Parts they cite, the planted example's answers
against what was planted in it before it ran, and the refusals against the rows
that were too few. Nothing here re-implements a statistic; the oracle for a
number is the Part the study wrote it from, and the oracle for the whole study
is `study.planted`.

The two examples are written into a temporary directory and studied there, so
the suite writes nothing the repository tracks.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

PYTO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PYTO_ROOT not in sys.path:
    sys.path.insert(0, PYTO_ROOT)

from pyto import PQL, Part, PxC  # noqa: E402
from pyto import study as study_module  # noqa: E402

sys.path.insert(0, os.path.join(PYTO_ROOT, "viewer", "test"))
import record_schema  # noqa: E402


def read(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def store_of(directory):
    """the study's store.json back as a `PxC`, which is what PQL reads."""
    pxc = PxC()
    for address, value in read(os.path.join(directory, "store.json")).items():
        pxc.set(Part(address), value)
    return pxc


def at(value, path):
    """the value at a summary citation's `path`, lists indexed by position."""
    for step in path:
        value = value[int(step)] if isinstance(value, list) else value[step]
    return value


class OneStudy:
    """one `pyto study` run, shared by every test that reads it."""

    directory = None
    name = None

    @classmethod
    def build(cls):
        cls.directory = tempfile.mkdtemp(prefix=f"study-{cls.name}-")
        cls.produce()
        cls.store = store_of(cls.directory)
        cls.parts = read(os.path.join(cls.directory, "store.json"))
        cls.prefix = f"px.exp.study.{cls.name}."
        cls.summary = cls.parts[cls.prefix + "summary"]
        cls.map = cls.parts[cls.prefix + "map"]
        cls.plan = cls.parts[cls.prefix + "plan"]

    @classmethod
    def drop(cls):
        shutil.rmtree(cls.directory, ignore_errors=True)


class Shelf(OneStudy, unittest.TestCase):
    """the built-in example: the studio's twelve discs, no flags but --target."""

    name = "shelf"

    @classmethod
    def setUpClass(cls):
        cls.build()

    @classmethod
    def tearDownClass(cls):
        cls.drop()

    @classmethod
    def produce(cls):
        cls.source = study_module.write_shelf_csv(os.path.join(cls.directory, "shelf.csv"))
        study_module.study(cls.source, target="weight", out_dir=cls.directory, quiet=True)

    def test_one_command_writes_a_store_records_and_a_page(self):
        for name in ("store.json", "study.html", "records/study_read.json",
                     "records/study_weigh.json", "records/study.json"):
            self.assertTrue(os.path.isfile(os.path.join(self.directory, name)), name)

    def test_the_table_is_the_shelf(self):
        self.assertEqual(self.plan["rows"], 12)
        self.assertEqual(self.plan["numeric"], ["weight", "speed", "glide", "turn", "fade"])
        self.assertEqual([one["name"] for one in self.plan["categorical"]],
                         ["disc", "mold", "maker", "category", "plastic"])

    def test_the_group_column_is_chosen_by_position_and_not_by_its_p_value(self):
        """disc and mold have too many levels; maker is the first that can be split."""
        where = self.plan["hypothesis"]
        self.assertEqual((where["group"], where["value"]), ("maker", "weight"))
        self.assertEqual(where["levels"], ["Discraft", "Innova"])
        self.assertIn("never by which pair gives the smallest p-value", self.plan["rule"])

    def test_the_assumption_checks_chose_the_test_and_are_on_the_record(self):
        choice = self.parts[self.prefix + "choice"]
        normality = self.parts[self.prefix + "normality"]
        self.assertEqual(choice["calc"], "fn.brain.stats.mannwhitneyu")
        self.assertFalse(normality["normal"])
        self.assertIn("normality", choice["refused"])
        self.assertTrue(self.store.has(self.prefix + "test"))
        self.assertEqual(sorted(one["name"] for one in choice["assumptions"]),
                         ["equal variance", "normality"])

    def test_the_clusters_are_weighed_and_not_assumed(self):
        clusters = self.parts[self.prefix + "clusters"]
        self.assertEqual(clusters["by"], "the mean silhouette")
        for one in clusters["ranking"]:
            scored = self.parts[self.prefix + "silhouette.k" + one["name"]]
            self.assertAlmostEqual(one["score"], scored["mean"], places=12)
        self.assertEqual(clusters["chosen"], max(clusters["ranking"], key=lambda one: one["score"])["name"])

    def test_twelve_rows_buy_no_predictor_and_the_study_says_so(self):
        best = self.parts[self.prefix + "model.best"]
        self.assertFalse(best["beats_floor"])
        self.assertEqual(best["floor"]["score"], 0.0)
        self.assertIn("model.winner", [one["what"] for one in self.map["skipped"]])
        refused = [section for section in self.summary["sections"]
                   if section["title"] == "what this study would not say"][0]
        self.assertTrue(any("names no predictor" in line["text"] for line in refused["lines"]))

    def test_every_summary_number_equals_the_part_it_cites(self):
        """the one test that makes the prose checkable: no number is written twice."""
        seen = 0
        for section in self.summary["sections"]:
            for line in section["lines"]:
                for citation in line["cites"]:
                    address = citation["address"]
                    self.assertTrue(self.store.has(address), f"{address} is cited and not in the store")
                    self.assertEqual(at(self.store.get(address), citation["path"]), citation["value"],
                                     f"{address}{citation['path']} in {section['title']!r}")
                    seen += 1
        self.assertGreater(seen, 20, "the summary cites almost nothing")

    def test_the_map_is_what_pql_reads(self):
        matched = PQL.prefix(self.prefix).matches(self.store)
        self.assertGreater(len(matched), 40)
        self.assertEqual(self.map["counts"]["steps"], len(self.map["ran"]))
        for one in self.map["ran"]:
            self.assertTrue(one["calc"].startswith(("fn.", "oc.")), one["calc"])
            self.assertTrue(self.store.has(one["into"]), one["into"])
        for one in self.map["skipped"]:
            self.assertTrue(self.store.has(self.prefix + "skipped." + study_module.slug(one["what"])))

    def test_the_engine_came_from_the_benchmark_parts(self):
        engines = self.map["engines"]
        self.assertEqual(engines["stats.shapiro"]["from"], "plan")
        self.assertEqual(engines["stats.shapiro"]["engine"], "sp")
        self.assertTrue(any(one["from"] == "plan" for one in engines.values()))
        ran = {one["id"]: one for one in self.map["ran"]}
        self.assertIn("normal_weight", ran)

    def test_every_part_is_the_studys_own_and_lowercase(self):
        for address in self.parts:
            self.assertTrue(address.startswith(("px.exp.study.", "proposal.study.")), address)
            self.assertEqual(address, address.lower())

    def test_the_records_validate_as_pyto_run_record_at_1(self):
        for name in ("study_read", "study_weigh", "study"):
            document = read(os.path.join(self.directory, "records", f"{name}.json"))
            record_schema.validate(document)
            self.assertEqual(document["schema"], "pyto-run-record@1")
            self.assertEqual(document["pcr"], name)

    def test_the_record_is_the_program_the_map_declares(self):
        recorded = []
        for name in ("study_read", "study_weigh", "study"):
            document = read(os.path.join(self.directory, "records", f"{name}.json"))
            for tick in document["ticks"]:
                for invocation in tick["invocations"]:
                    recorded.append(invocation["id"])
        self.assertEqual([one["id"] for one in self.map["ran"]], recorded)

    def test_the_page_carries_the_summary_and_the_viewer(self):
        with open(os.path.join(self.directory, "study.html"), encoding="utf-8") as handle:
            page = handle.read()
        self.assertIn('class="study-summary"', page)
        self.assertIn("what this study would not say", page)
        for section in self.summary["sections"]:
            self.assertIn(section["title"], page)
        self.assertIn("application/json", page)

    def test_the_findings_are_lowercase_proposals_with_their_for(self):
        findings = {a: v for a, v in self.parts.items() if a.startswith("proposal.study.")}
        self.assertGreaterEqual(len(findings), 5)
        for address, value in findings.items():
            self.assertIn(value["kind"], ("strength", "friction"))
            self.assertTrue(value["for"], address)


class Planted(OneStudy, unittest.TestCase):
    """the oracle for the study itself: a table whose structure is known first."""

    name = "planted"

    @classmethod
    def setUpClass(cls):
        cls.build()

    @classmethod
    def tearDownClass(cls):
        cls.drop()

    @classmethod
    def produce(cls):
        cls.source = os.path.join(cls.directory, "planted.csv")
        cls.truth = study_module.write_planted_csv(cls.source)
        cls.store_returned = study_module.study(cls.source, target="y", out_dir=cls.directory, quiet=True)

    def test_the_study_said_what_was_planted(self):
        checks = study_module.planted_oracle(self.store_returned, "planted", self.truth)
        failed = [one for one in checks if not one["pass"]]
        self.assertEqual(failed, [], json.dumps(failed, indent=2, default=str))
        self.assertGreaterEqual(len(checks), 8)

    def test_the_constant_column_is_refused_rather_than_described(self):
        self.assertEqual(self.plan["constant"], ["site"])
        self.assertFalse(self.store.has(self.prefix + "column.site.describe"))
        refused = self.parts[self.prefix + "skipped.profile_site"]
        self.assertIn("never changes", refused["why"])

    def test_the_anova_was_chosen_because_the_assumptions_held(self):
        choice = self.parts[self.prefix + "choice"]
        self.assertEqual(choice["calc"], "fn.brain.stats.f_oneway")
        self.assertEqual(choice["refused"], [])
        self.assertLess(self.parts[self.prefix + "test"]["pvalue"], 0.01)

    def test_the_winner_beats_the_baseline_and_the_summary_says_by_how_much(self):
        best = self.parts[self.prefix + "model.best"]
        self.assertTrue(best["beats_floor"])
        self.assertGreater(best["score"], 0.9)
        self.assertEqual(best["ranking"][0]["name"], best["chosen"])
        for one in best["ranking"]:
            scored = self.parts[self.prefix + "model.cv." + study_module.slug(one["name"])]
            self.assertAlmostEqual(one["score"], scored["mean"], places=12)

    def test_every_summary_number_equals_the_part_it_cites(self):
        for section in self.summary["sections"]:
            for line in section["lines"]:
                for citation in line["cites"]:
                    self.assertEqual(at(self.store.get(citation["address"]), citation["path"]),
                                     citation["value"], f"{citation['address']}{citation['path']}")


class TooFewRows(unittest.TestCase):
    """the skip rules, on a table that can support almost nothing."""

    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.mkdtemp(prefix="study-tiny-")
        cls.source = os.path.join(cls.directory, "tiny.csv")
        with open(cls.source, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("name,note,n\na,hello,1\nb,world,\nc,hi,3\n")
        study_module.study(cls.source, out_dir=cls.directory, quiet=True)
        cls.parts = read(os.path.join(cls.directory, "store.json"))
        cls.prefix = "px.exp.study.tiny."

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.directory, ignore_errors=True)

    def test_each_refusal_names_what_it_needed_and_what_it_had(self):
        refusals = {one["what"]: one for one in self.parts[self.prefix + "map"]["skipped"]}
        self.assertEqual(sorted(refusals), ["clustering", "correlation", "hypothesis", "normality.n"])
        for one in refusals.values():
            self.assertTrue(one["why"])
            self.assertIn("needed", one)
            self.assertIn("had", one)

    def test_a_refused_step_left_no_result_behind(self):
        for address in ("correlation", "pairs", "clusters", "pca", "test", "choice"):
            self.assertNotIn(self.prefix + address, self.parts, address)

    def test_what_could_run_ran(self):
        described = self.parts[self.prefix + "column.n.describe"]
        self.assertEqual(described["n"], 2)
        self.assertEqual(self.parts[self.prefix + "missing"]["columns"]["n"]["missing"], 1)

    def test_a_table_with_no_hypothesis_writes_two_records_not_three(self):
        names = sorted(os.listdir(os.path.join(self.directory, "records")))
        self.assertEqual(names, ["study.json", "study_read.json"])


class ASampleWhereTheCostIsQuadratic(unittest.TestCase):
    """past a row count the study samples, and every Part of it says which rows."""

    def setUp(self):
        self.kept = (study_module.CLUSTER_MAX_ROWS, study_module.MODEL_MAX_ROWS)
        study_module.CLUSTER_MAX_ROWS, study_module.MODEL_MAX_ROWS = 40, 60
        self.directory = tempfile.mkdtemp(prefix="study-sample-")

    def tearDown(self):
        study_module.CLUSTER_MAX_ROWS, study_module.MODEL_MAX_ROWS = self.kept
        shutil.rmtree(self.directory, ignore_errors=True)

    def test_the_sample_is_a_part_the_summary_names(self):
        source = os.path.join(self.directory, "planted.csv")
        study_module.write_planted_csv(source)
        study_module.study(source, target="y", out_dir=self.directory, quiet=True, page=False)
        parts = read(os.path.join(self.directory, "store.json"))
        plan = parts["px.exp.study.planted.plan"]
        self.assertEqual(plan["clustering"]["sample"]["rows"], 40)
        self.assertEqual(plan["clustering"]["sample"]["of"], 180)
        self.assertEqual(len(parts["px.exp.study.planted.cluster.rows"]["rows"]), 40)
        self.assertEqual(len(parts["px.exp.study.planted.model.sample"]["rows"]), 60)
        summary = json.dumps(parts["px.exp.study.planted.summary"])
        self.assertIn("a seeded sample of 40 of 180", summary)
        self.assertIn("a seeded sample of 60 of 180", summary)

    def test_a_training_fold_narrower_than_the_fit_is_refused(self):
        study_module.MODEL_MAX_ROWS = 10
        source = study_module.write_shelf_csv(os.path.join(self.directory, "shelf.csv"))
        study_module.study(source, target="weight", out_dir=self.directory, quiet=True, page=False)
        parts = read(os.path.join(self.directory, "store.json"))
        refused = parts["px.exp.study.shelf.skipped.model"]
        self.assertIn("fewer rows than the fit has columns", refused["why"])
        self.assertNotIn("px.exp.study.shelf.model.best", parts)


class ACsvAPersonActuallyHas(unittest.TestCase):
    """a semicolon separator and a hole spelled the way the exporter spelled it."""

    def test_the_separator_and_the_missing_spelling_are_the_callers(self):
        directory = tempfile.mkdtemp(prefix="study-csv-")
        try:
            source = os.path.join(directory, "euro.csv")
            with open(source, "w", encoding="utf-8", newline="\n") as handle:
                handle.write("name;score;note\n")
                for index in range(8):
                    handle.write(f"row{index};{index * 2};{'-' if index == 3 else 'ok'}\n")
            study_module.study(source, out_dir=directory, quiet=True, page=False,
                               delimiter=";", missing=["-"])
            parts = read(os.path.join(directory, "store.json"))
            table = parts["px.exp.study.euro.table"]
            self.assertEqual(table["columns"], ["name", "score", "note"])
            self.assertEqual(parts["px.exp.study.euro.missing"]["columns"]["note"]["missing"], 1)
            self.assertEqual(parts["px.exp.study.euro.column.score.describe"]["n"], 8)
        finally:
            shutil.rmtree(directory, ignore_errors=True)


class TheCommand(unittest.TestCase):
    """`python -m pyto.study` and `neat study` are the same command."""

    def test_the_module_runs_the_shelf_example_in_one_command(self):
        directory = tempfile.mkdtemp(prefix="study-cli-")
        try:
            done = subprocess.run(
                [sys.executable, "-m", "pyto.study", "--example", "shelf", "--out", directory],
                cwd=PYTO_ROOT, capture_output=True, text=True, timeout=600)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertIn("== the clusters", done.stdout)
            self.assertTrue(os.path.isfile(os.path.join(directory, "study.html")))
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_the_api_is_callable_as_the_first_thing_a_process_does(self):
        """`from pyto.study import study; study(...)` with nothing imported before it."""
        directory = tempfile.mkdtemp(prefix="study-api-")
        try:
            source = study_module.write_shelf_csv(os.path.join(directory, "shelf.csv"))
            done = subprocess.run(
                [sys.executable, "-c",
                 "from pyto.study import study\n"
                 f"study({source!r}, out_dir={directory!r}, page=False, quiet=True)\n"],
                cwd=PYTO_ROOT, capture_output=True, text=True, timeout=600)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertTrue(os.path.isfile(os.path.join(directory, "store.json")))
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_the_page_is_named_after_the_study(self):
        directory = tempfile.mkdtemp(prefix="study-title-")
        try:
            source = study_module.write_shelf_csv(os.path.join(directory, "shelf.csv"))
            study_module.study(source, out_dir=directory, quiet=True)
            with open(os.path.join(directory, "study.html"), encoding="utf-8") as handle:
                page = handle.read()
            self.assertIn("<title>shelf &middot; a pyto study</title>", page)
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_neat_study_forwards_to_the_module(self):
        script = os.path.join(PYTO_ROOT, "scripts", "neat.sh")
        with open(script, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("study) cmd_study", text)
        if os.name == "nt" or shutil.which("bash") is None:
            self.skipTest("neat is a posix shell script; the verb is asserted above")
        directory = tempfile.mkdtemp(prefix="study-neat-")
        try:
            done = subprocess.run(
                ["bash", script, "study", "--example", "shelf", "--out", directory, "--quiet"],
                cwd=os.path.dirname(PYTO_ROOT), capture_output=True, text=True, timeout=600)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertTrue(os.path.isfile(os.path.join(directory, "store.json")))
        finally:
            shutil.rmtree(directory, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
