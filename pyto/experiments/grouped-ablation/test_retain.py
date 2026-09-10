"""Day 2 lane B tests: retained programs, local change explanation, PQL documents.

Run with `python3 -m unittest discover -s experiments/grouped-ablation -p 'test_*.py'`.

sys.path (docs: experiments/CAPTURE.md, "sys.path: what is logged and what is
forbidden"): this file makes two intra-repo inserts and logs both to stderr, and
`test_sys_path_inserts_are_intra_repo` asserts each inserted path is inside this
repository. Nothing here reaches outside the repository and nothing sets
PYTHONPATH.
"""

from __future__ import annotations

import ast
import contextlib
import copy
import hashlib
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
DISC_STATS = os.path.join(REPO, "pyto", "consumers", "discstudio-card", "experiments", "disc-stats")
EVIDENCE = os.path.join(HERE, "evidence")
SIDECAR_RECORD = os.path.join(EVIDENCE, "disc-stats-sidecar.json")
CANDIDATES = os.path.join(HERE, "candidates")
INSERTED: list[str] = []

for _path, _why in (
    (HERE, "this experiment's own modules (retain, compare_local, pql_document, calculations)"),
    (DISC_STATS, "run_experiment.py imports stats.py by top-level name (disc-stats/run_experiment.py:4)"),
):
    if _path not in sys.path:
        sys.path.insert(0, _path)
    INSERTED.append(_path)
    print(f"[grouped-ablation] sys.path.insert(0, {_path!r})  # {_why}", file=sys.stderr)

import compare_local  # noqa: E402
import pql_document  # noqa: E402
import retain  # noqa: E402
from pyto import PCR, Calculation, Part, Pcr, PxC  # noqa: E402
from calculations import REGISTRY  # noqa: E402
from features import GROUPS, make_data  # noqa: E402
from program import GROUPS as GROUPS_PART, ROWS, build_program  # noqa: E402
from run import testimony_of  # noqa: E402

SEED, ROWS_N = 7, 400
FORBIDDEN_TOKENS = ("lambda", "<function")
PROBE_CALLS: list[dict] = []


def probe(args: dict) -> dict:
    PROBE_CALLS.append(dict(args))
    return {"seen": sorted(args)}


def echo(args: dict) -> dict:
    return {"v": args.get("v")}


PROBE = Calculation("fn.probe.record", probe)
ECHO = Calculation("fn.probe.echo", echo)


def day1_run():
    pxc = PxC()
    pxc.set(ROWS, make_data(SEED, ROWS_N))
    pxc.set(GROUPS_PART, GROUPS)
    from calculations import select_variants

    pcr = build_program(select_variants({"groups": GROUPS}))
    return pxc, pcr, pcr.run(pxc)


def day1_record(**kwargs):
    pxc, pcr, run = day1_run()
    record = retain.retain_run(
        pxc, run, [ROWS.address, GROUPS_PART.address], registry=REGISTRY, **kwargs
    )
    return pxc, pcr, run, record


class SysPathDiscipline(unittest.TestCase):
    def test_sys_path_inserts_are_intra_repo(self):
        self.assertEqual(len(INSERTED), 2)
        for path in INSERTED:
            self.assertTrue(os.path.abspath(path).startswith(REPO + os.sep), path)
            self.assertTrue(os.path.isdir(path), path)
        self.assertIsNone(os.environ.get("PYTHONPATH"))


class ToProgram(unittest.TestCase):
    """The retained entries are the testimony entries, with no translation layer."""

    @classmethod
    def setUpClass(cls):
        cls.pxc, cls.pcr, cls.pcr_run = day1_run()
        cls.program = retain.to_program(cls.pcr_run)
        cls.testimony = testimony_of(cls.pcr_run)

    def test_program_entries_are_the_testimony_entries_after_json(self):
        after_json = json.loads(json.dumps(self.program))
        self.assertEqual(
            json.dumps(after_json["ticks"], sort_keys=True),
            json.dumps(self.testimony["ticks"], sort_keys=True),
        )
        self.assertEqual(after_json["name"], self.testimony["pcr"])

    def test_authoring_pcr_and_run_export_the_same_program(self):
        self.assertEqual(
            json.dumps(retain.to_program(self.pcr), sort_keys=True),
            json.dumps(self.program, sort_keys=True),
        )

    def test_fn_and_px_refs_are_both_present(self):
        refs = [ref for tick in self.program["ticks"] for entry in tick["calculations"] for ref in entry["inputs"].values()]
        self.assertTrue(any(ref.startswith("px:") for ref in refs))
        self.assertTrue(any(ref == "fn:split" for ref in refs))

    def test_to_program_rejects_anything_else(self):
        with self.assertRaises(TypeError):
            retain.to_program({"name": "x", "ticks": []})


class ExportRefusals(unittest.TestCase):
    def test_shadowing_arg_is_refused_at_export_naming_the_invocation(self):
        pxc = PxC()
        pxc.set(Part("px.probe.v"), "from-part")
        pcr = PCR("shadow.probe")
        pcr.calc("T", ECHO, id="echo-1", v=Part("px.probe.v"), args={"v": "from-args"}, into="px.probe.out")
        run = pcr.run(pxc)
        # pyto lets the arg win silently (pcr.py:331-332) while the testimony still
        # says the value came from the Part: exactly the record that must not exist.
        self.assertEqual(pxc.get("px.probe.out"), {"v": "from-args"})
        self.assertEqual(run.ticks[0].calculations[0].inputs, {"v": "px:px.probe.v"})
        for source in (pcr, run):
            with self.assertRaises(retain.ShadowedInputError) as caught:
                retain.to_program(source)
            self.assertIn("echo-1", str(caught.exception))
            self.assertIn("exec.js:45", str(caught.exception))

    def test_callable_in_args_is_refused_naming_the_invocation(self):
        pcr = PCR("leak.probe")
        pcr.calc("T", ECHO, id="leak-1", args={"post": echo}, into="px.leak")
        with self.assertRaises(retain.RetainError) as caught:
            retain.to_program(pcr)
        self.assertIn("leak-1", str(caught.exception))
        self.assertIn("PYTHON-LAB-STEWARDSHIP.md:39", str(caught.exception))

    def test_input_named_like_a_pcr_calc_parameter_is_refused(self):
        """An input called `args`/`into`/`id` cannot be rebuilt through PCR.calc.

        PCR.calc takes those as keyword-only parameters (pcr.py:252-256), so
        `**inputs` can never carry them: such a program is only reachable by
        hand-editing retained JSON, which is exactly when a silent misbinding
        would be worst. Both directions refuse.
        """
        pcr = PCR("reserved.probe")
        pcr.calc("T", PROBE, id="reserved-1", v=Part("px.probe.v"))
        invocation = pcr.ticks[0].calculations[0]
        invocation.bindings = {"args": invocation.bindings["v"]}
        with self.assertRaises(retain.RetainError) as caught:
            retain.to_program(pcr)
        self.assertIn("reserved-1", str(caught.exception))
        self.assertIn("pcr.py:252-256", str(caught.exception))

        hand_written = {"name": "reserved.probe", "ticks": [{"name": "T", "calculations": [
            {"id": "reserved-1", "calculation": "fn.probe.record",
             "inputs": {"args": "px:px.probe.v"}, "args": {}, "into": None}]}]}
        with self.assertRaises(retain.RetainError) as caught:
            retain.from_program(hand_written, {"fn.probe.record": PROBE})
        self.assertIn("reserved-1", str(caught.exception))


class FromProgram(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pxc, cls.pcr, cls.pcr_run = day1_run()
        cls.program = json.loads(json.dumps(retain.to_program(cls.pcr_run)))
        cls.testimony = json.dumps(testimony_of(cls.pcr_run), sort_keys=True)

    def test_round_trip_reproduces_testimony_and_result_digests(self):
        rebuilt = retain.from_program(self.program, REGISTRY)
        pxc = PxC()
        pxc.set(ROWS, self.pxc.get(ROWS))
        pxc.set(GROUPS_PART, self.pxc.get(GROUPS_PART))
        replayed = rebuilt.run(pxc)
        self.assertEqual(json.dumps(testimony_of(replayed), sort_keys=True), self.testimony)
        self.assertEqual(
            {k: retain.digest_of(v) for k, v in replayed.results.items()},
            {k: retain.digest_of(v) for k, v in self.pcr_run.results.items()},
        )

    def test_missing_registry_address_raises_keyerror_before_any_execution(self):
        PROBE_CALLS.clear()
        registry = dict(REGISTRY)
        registry["fn.ablation.split"] = PROBE  # would record a call if anything ran
        del registry["fn.ablation.score"]
        record = {"program": self.program, "external": {}, "provider": {}, "results": {}}
        with self.assertRaises(KeyError) as caught:
            retain.replay(record, registry)
        self.assertIn("fn.ablation.score", str(caught.exception))
        self.assertEqual(PROBE_CALLS, [])

    def test_pcr_projection_is_rejected_citing_stewardship(self):
        graph = Pcr("ablation.grouped")
        graph.calc("Prepare", "fn.ablation.split", id="split", rows=graph.part("input.ablation.rows"), into="scratch.ablation.split")
        with self.assertRaises(retain.NotAProgramError) as caught:
            retain.from_program(graph.to_pcr_dict(), REGISTRY)
        message = str(caught.exception)
        self.assertIn("PYTHON-LAB-STEWARDSHIP.md:19", message)
        self.assertIn("graph.py:29-31", message)

    def test_writer_and_id_rules_re_apply_on_import(self):
        duplicate = copy.deepcopy(self.program)
        duplicate["ticks"][0]["calculations"].append(dict(duplicate["ticks"][0]["calculations"][0]))
        with self.assertRaises(ValueError) as caught:
            retain.from_program(duplicate, REGISTRY)
        self.assertIn("duplicate calculation id", str(caught.exception))

        two_writers = copy.deepcopy(self.program)
        entry = dict(two_writers["ticks"][0]["calculations"][1])
        entry["id"] = "split-again"
        two_writers["ticks"][0]["calculations"].append(entry)
        with self.assertRaises(ValueError) as caught:
            retain.from_program(two_writers, REGISTRY)
        self.assertIn("multiple writers", str(caught.exception))

    def test_the_committed_run_1_testimony_is_itself_a_program(self):
        """Day 1's retained evidence needs no conversion to become a replayable program.

        evidence/run-1/testimony.json is {pcr, ticks} (run.py:59-61, critic gap 18d);
        the retained program is {name, ticks} over the same entries, so the Day 1
        evidence file replays through the registry as it stands.
        """
        with open(os.path.join(EVIDENCE, "run-1", "testimony.json"), encoding="utf-8") as handle:
            retained = json.load(handle)
        program = {"name": retained["pcr"], "ticks": retained["ticks"]}
        self.assertEqual(json.dumps(program, sort_keys=True), json.dumps(self.program, sort_keys=True))
        rebuilt = retain.from_program(program, REGISTRY)
        pxc = PxC()
        pxc.set(ROWS, self.pxc.get(ROWS))
        pxc.set(GROUPS_PART, self.pxc.get(GROUPS_PART))
        replayed = rebuilt.run(pxc)
        self.assertEqual(json.dumps(testimony_of(replayed), sort_keys=True), self.testimony)

    def test_replaying_run_1_reproduces_its_committed_comparison(self):
        """The replayed comparison equals evidence/run-1/comparison.json's rows."""
        with open(os.path.join(EVIDENCE, "run-1", "comparison.json"), encoding="utf-8") as handle:
            committed = json.load(handle)
        rebuilt = retain.from_program(self.program, REGISTRY)
        pxc = PxC()
        pxc.set(ROWS, self.pxc.get(ROWS))
        pxc.set(GROUPS_PART, self.pxc.get(GROUPS_PART))
        replayed = rebuilt.run(pxc)
        self.assertEqual(replayed.results["compare"], committed["rows"])

    def test_bad_ref_prefix_is_rejected(self):
        broken = copy.deepcopy(self.program)
        broken["ticks"][0]["calculations"][0]["inputs"]["groups"] = "input.ablation.groups"
        with self.assertRaises(retain.NotAProgramError) as caught:
            retain.from_program(broken, REGISTRY)
        self.assertIn("px:", str(caught.exception))


class RetainRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pxc, cls.pcr, cls.pcr_run, cls.record = day1_record()

    def test_record_keys_and_external_values(self):
        self.assertEqual(
            sorted(self.record), ["external", "program", "provider", "results", "retained"]
        )
        self.assertEqual(sorted(self.record["external"]), [GROUPS_PART.address, ROWS.address])
        self.assertEqual(self.record["external"][GROUPS_PART.address], GROUPS)

    def test_retained_block_separates_retained_at_from_ran_at(self):
        """Fixer round 1, finding 5: `provider` is the library that RETAINED the record.

        Nothing in retain.py derives the commit; a caller that knows it passes
        `retained_at={"commit": ...}` (run.py, second_experiment.py, replay.py all do),
        and this record -- retained by day1_record() with no caller -- carries None
        rather than a value invented here.
        """
        retained = self.record["retained"]
        self.assertEqual(sorted(retained), ["commit", "provider_is"])
        self.assertIsNone(retained["commit"])
        self.assertIn("not necessarily the ones that produced the evidence beside it", retained["provider_is"])
        passed = retain.retain_run(
            self.pxc, self.pcr_run, [ROWS.address, GROUPS_PART.address],
            registry=REGISTRY, retained_at={"commit": "deadbeef"},
        )
        self.assertEqual(passed["retained"]["commit"], "deadbeef")

    def test_check_record_refuses_an_external_the_program_claims_to_compute(self):
        """Fixer round 1, finding 1 (the milder form of the pre-seeding attack)."""
        forged = copy.deepcopy(self.record)
        forged["external"]["scratch.ablation.split"] = ["pre-seeded"]
        with self.assertRaises(retain.ContradictoryRecordError) as caught:
            retain.check_record(forged)
        self.assertIn("scratch.ablation.split", str(caught.exception))
        with self.assertRaises(retain.ContradictoryRecordError):
            retain.replay(forged, REGISTRY)

    def test_check_record_refuses_results_that_are_not_the_programs_invocation_ids(self):
        missing = copy.deepcopy(self.record)
        missing["results"].pop("split")
        with self.assertRaises(retain.ContradictoryRecordError) as caught:
            retain.check_record(missing)
        self.assertIn("split", str(caught.exception))
        extra = copy.deepcopy(self.record)
        extra["results"]["ghost"] = None
        with self.assertRaises(retain.ContradictoryRecordError):
            retain.check_record(extra)

    def test_check_record_accepts_the_honest_record_and_reports_what_it_checked(self):
        checked = retain.check_record(self.record)
        ids = sorted(
            entry["id"] for tick in self.record["program"]["ticks"] for entry in tick["calculations"]
        )
        self.assertEqual(checked["invocation_ids"], ids)
        self.assertEqual(checked["external_addresses"], sorted([GROUPS_PART.address, ROWS.address]))
        self.assertEqual(set(checked["into_addresses"]) & set(checked["external_addresses"]), set())

    def test_verify_provider_reports_agreement_and_names_every_disagreement(self):
        """Fixer round 1, finding 3: the comparison the provider docstring promises."""
        agreeing = retain.verify_provider(self.record, REGISTRY)
        self.assertTrue(agreeing["agrees"])
        self.assertTrue(agreeing["pyto"]["agrees"])
        self.assertEqual(agreeing["disagreeing_addresses"], [])
        self.assertEqual(sorted(agreeing["registry"]), sorted(REGISTRY))

        falsified = copy.deepcopy(self.record)
        falsified["provider"]["pyto"]["version"] = "0.0.0-FAKE"
        for entry in falsified["provider"]["registry"].values():
            entry["source_sha256"] = "1" * 64
        report = retain.verify_provider(falsified, REGISTRY)
        self.assertFalse(report["agrees"])
        self.assertFalse(report["pyto"]["agrees"])
        self.assertEqual(report["disagreeing_addresses"], sorted(REGISTRY))
        # Reporting only: replay still runs, which is what the LF-source-drift probe needs.
        _pxc, run = retain.replay(falsified, REGISTRY)
        self.assertEqual({k: retain.digest_of(v) for k, v in run.results.items()}, self.record["results"])

    def test_result_digests_are_computed_from_the_values(self):
        expected = {}
        for invocation_id, value in self.pcr_run.results.items():
            text = json.dumps(value, sort_keys=True, separators=(",", ":"))
            expected[invocation_id] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self.assertEqual(self.record["results"], expected)
        self.assertEqual(len(expected), sum(len(t["calculations"]) for t in self.record["program"]["ticks"]))

    def test_provider_names_the_library_and_every_registry_module(self):
        provider = self.record["provider"]
        self.assertEqual(provider["pyto"]["package"], "pyto-lab")
        self.assertEqual(provider["pyto"]["version"], "0.1.0")
        for name in retain.PROVIDER_MODULES:
            self.assertRegex(provider["pyto"]["modules"][name], r"^[0-9a-f]{64}$")
        self.assertEqual(sorted(provider["registry"]), sorted(REGISTRY))
        for address, entry in provider["registry"].items():
            self.assertEqual(entry["module"], "calculations", address)
            self.assertRegex(entry["source_sha256"], r"^[0-9a-f]{64}$")

    def test_record_holds_no_code(self):
        text = json.dumps(self.record, sort_keys=True)
        for token in FORBIDDEN_TOKENS:
            self.assertNotIn(token, text)

    def test_replay_from_the_record_reproduces_testimony(self):
        _, replayed = retain.replay(self.record, REGISTRY)
        self.assertEqual(
            json.dumps(testimony_of(replayed), sort_keys=True),
            json.dumps(testimony_of(self.pcr_run), sort_keys=True),
        )

    def test_missing_external_address_fails_loud(self):
        with self.assertRaises(KeyError):
            retain.retain_run(self.pxc, self.pcr_run, ["input.ablation.absent"], registry=REGISTRY)

    def test_write_record_is_lf_json(self):
        tmp = tempfile.mkdtemp(prefix="retain-record-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        path = retain.write_record(self.record, os.path.join(tmp, "record.json"))
        with open(path, "rb") as handle:
            raw = handle.read()
        self.assertNotIn(b"\r\n", raw)
        self.assertEqual(json.loads(raw.decode("utf-8"))["program"], self.record["program"])


class Digests(unittest.TestCase):
    def test_non_json_value_digests_to_none_without_repr_fallback(self):
        self.assertIsNone(retain.digest_of({("M1", "P1"): 2}))
        self.assertIsNone(retain.digest_of(object()))
        self.assertIsNotNone(retain.digest_of({"a": [1, 2.5, None, True]}))

    def test_describe_refuses_a_callable_and_an_undescribable_object(self):
        with self.assertRaises(retain.RetainError) as caught:
            retain.describe(echo, "external['x']")
        self.assertIn("PYTHON-LAB-STEWARDSHIP.md:39", str(caught.exception))
        with self.assertRaises(retain.RetainError):
            retain.describe(object(), "external['x']")

    def test_describe_is_order_independent_for_dicts_and_sets(self):
        left = retain.describe({"b": 1, "a": {2, 1}}, "x")
        right = retain.describe({"a": {1, 2}, "b": 1}, "x")
        self.assertEqual(retain.canonical_json(left), retain.canonical_json(right))


class ExplainChanges(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, _, cls.pcr_run, cls.record = day1_record()

    def _mutate(self, edit, results_edit=None, external_edit=None):
        other = copy.deepcopy(self.record)
        for tick in other["program"]["ticks"]:
            for entry in tick["calculations"]:
                edit(entry)
        if results_edit:
            results_edit(other["results"])
        if external_edit:
            external_edit(other["external"])
        return other

    def test_identical_records_change_nothing(self):
        out = compare_local.explain_changes(self.record, copy.deepcopy(self.record))
        self.assertEqual(out["changed"], [])
        self.assertEqual(out["downstream_affected"], [])
        self.assertEqual(out["added"], [])
        self.assertEqual(out["removed"], [])
        self.assertEqual(len(out["unchanged_upstream"]), len(self.record["results"]))

    def test_changed_args_reports_args_and_the_downstream_closure(self):
        def edit(entry):
            if entry["id"] == "fit.all":
                entry["args"] = dict(entry["args"], variant="all-v2")

        out = compare_local.explain_changes(self.record, self._mutate(edit))
        self.assertEqual(out["changed"], ["fit.all"])
        self.assertEqual(out["reason"], {"fit.all": "args"})
        # score.all reads fit.all's Part; compare reads score.all's result.
        self.assertEqual(out["downstream_affected"], ["score.all", "compare"])
        self.assertNotIn("fit.all", out["unchanged_upstream"])
        self.assertIn("split", out["unchanged_upstream"])

    def test_changed_calculation_address_outranks_everything(self):
        def edit(entry):
            if entry["id"] == "score.all":
                entry["calculation"] = "fn.ablation.rmse"
                entry["args"] = {"changed": True}

        out = compare_local.explain_changes(self.record, self._mutate(edit))
        self.assertEqual(out["reason"]["score.all"], "calculation")

    def test_changed_binding_reports_input(self):
        def edit(entry):
            if entry["id"] == "score.all":
                entry["inputs"] = dict(entry["inputs"], split="px:scratch.ablation.split")

        out = compare_local.explain_changes(self.record, self._mutate(edit))
        self.assertEqual(out["reason"]["score.all"], "input")

    def test_result_digest_alone_reports_digest(self):
        def keep(entry):
            return None

        def results_edit(results):
            results["split"] = "0" * 64

        out = compare_local.explain_changes(self.record, self._mutate(keep, results_edit))
        self.assertEqual(out["changed"], ["split"])
        self.assertEqual(out["reason"], {"split": "digest"})
        self.assertIn("fit.all", out["downstream_affected"])

    def test_false_unchanged_shadowing_arg_is_reported_as_args_not_missed(self):
        """A shadowing args key changes the value while `inputs` is untouched.

        retain.to_program refuses to export such a program, so this record is
        hand-written; the point is that a comparison over `inputs` alone would
        call the invocation unchanged (pcr.py:331-332 lets args win silently).
        """
        def edit(entry):
            if entry["id"] == "score.all":
                entry["args"] = {"split": {"train": [[], []], "test": [[], []]}}

        other = self._mutate(edit)
        out = compare_local.explain_changes(self.record, other)
        self.assertEqual(out["reason"]["score.all"], "args")
        by_inputs_only = [
            entry["id"]
            for tick_a, tick_b in zip(self.record["program"]["ticks"], other["program"]["ticks"])
            for entry, entry_b in zip(tick_a["calculations"], tick_b["calculations"])
            if entry["inputs"] != entry_b["inputs"]
        ]
        self.assertEqual(by_inputs_only, [])  # the false-unchanged view
        with self.assertRaises(retain.ShadowedInputError):
            retain.from_program(other["program"], REGISTRY)

    def test_false_unchanged_same_program_changed_external_digest(self):
        """Identical program, identical result digests, different input data."""
        def keep(entry):
            return None

        def external_edit(external):
            external[ROWS.address] = {"digest": "1" * 64, "ref": "rows.json"}

        other = self._mutate(keep, None, external_edit)
        self.assertEqual(
            json.dumps(other["program"], sort_keys=True),
            json.dumps(self.record["program"], sort_keys=True),
        )
        self.assertEqual(other["results"], self.record["results"])
        out = compare_local.explain_changes(self.record, other)
        self.assertEqual(out["changed"], ["split"])
        self.assertEqual(out["reason"], {"split": "external"})
        self.assertIn("compare", out["downstream_affected"])
        self.assertNotIn("split", out["unchanged_upstream"])

    def test_added_and_removed_ids_are_listed_separately(self):
        other = copy.deepcopy(self.record)
        dropped = other["program"]["ticks"][1]["calculations"].pop()
        extra = dict(dropped, id="fit.extra", into="scratch.ablation.model.extra")
        other["program"]["ticks"][1]["calculations"].append(extra)
        out = compare_local.explain_changes(self.record, other)
        self.assertEqual(out["added"], ["fit.extra"])
        self.assertEqual(out["removed"], [dropped["id"]])

    def test_consumers_of_fn_and_px_refs(self):
        program = self.record["program"]
        self.assertIn("fit.all", compare_local.consumers_of(program, "fn:split"))
        self.assertEqual(
            compare_local.consumers_of(program, "px:input.ablation.rows"), ["split"]
        )
        self.assertEqual(compare_local.consumers_of(program, "fn:compare"), [])
        with self.assertRaises(ValueError):
            compare_local.consumers_of(program, "split")

    def test_render_counts_come_from_the_explanation(self):
        def edit(entry):
            if entry["id"] == "fit.all":
                entry["args"] = dict(entry["args"], variant="all-v2")

        out = compare_local.explain_changes(self.record, self._mutate(edit))
        text = compare_local.render(out)
        self.assertIn(f"changed {len(out['changed'])}", text)
        self.assertIn("fit.all: args", text)


class PqlDocument(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.day1 = retain.to_program(day1_run()[2])
        cls.fanout, cls.fanout_registry = cls.build_fanout()

    @staticmethod
    def build_fanout():
        registry = {
            "fn.discArt.render": Calculation("fn.discArt.render", echo),
            "fn.card.single": Calculation("fn.card.single", echo),
            "fn.card.battle": Calculation("fn.card.battle", echo),
        }
        pxc = PxC()
        pxc.set(Part("px.disc.request"), {"seed": SEED})
        first = PCR("fanout.render")
        first.calc("Render", registry["fn.discArt.render"], id="render-disc", v=Part("px.disc.request"), into="px.disc.art")
        first.run(pxc)
        second = PCR("fanout.cards")
        second.calc("Cards", registry["fn.card.single"], id="single-card", v=Part("px.disc.art"), into="px.card.single")
        second.calc("Cards", registry["fn.card.battle"], id="battle-card", v=Part("px.disc.art"), into="px.card.battle")
        return retain.to_program(second.run(pxc)), registry

    def test_px_only_program_renders_the_readpql_shape(self):
        document = pql_document.to_pql_document(self.fanout)
        self.assertEqual(sorted(document), ["PrincipleComponentRender", "Ticks"])
        self.assertEqual(document["PrincipleComponentRender"], "fanout.cards")
        calculations = document["Ticks"][0]["Calculations"]
        self.assertEqual(sorted(calculations[0]), ["args", "call", "into", "with"])
        self.assertEqual(calculations[0]["with"], {"v": "px.disc.art"})
        self.assertEqual(calculations[0]["into"], "px.card.single")

    def test_day1_program_is_refused_naming_the_first_offending_invocation(self):
        with self.assertRaises(pql_document.PqlDocumentError) as caught:
            pql_document.to_pql_document(self.day1)
        message = str(caught.exception)
        self.assertIn("Fit.fit.all", message)
        self.assertIn("fn:split", message)
        self.assertIn("exec.js:44-46", message)
        accepted, why = pql_document.can_render(self.day1)
        self.assertFalse(accepted)
        self.assertEqual(why, message)

    def test_unpublished_invocation_is_refused(self):
        program = copy.deepcopy(self.fanout)
        program["ticks"][0]["calculations"][1]["into"] = None
        with self.assertRaises(pql_document.PqlDocumentError) as caught:
            pql_document.to_pql_document(program)
        self.assertIn("battle-card", str(caught.exception))
        self.assertIn("exec.js:46", str(caught.exception))

    def test_shadowing_arg_is_refused(self):
        program = copy.deepcopy(self.fanout)
        program["ticks"][0]["calculations"][0]["args"] = {"v": 1}
        with self.assertRaises(pql_document.PqlDocumentError) as caught:
            pql_document.to_pql_document(program)
        self.assertIn("exec.js:45", str(caught.exception))

    def test_non_fn_call_address_is_refused(self):
        program = copy.deepcopy(self.fanout)
        program["ticks"][0]["calculations"][0]["calculation"] = "card.single"
        with self.assertRaises(pql_document.PqlDocumentError) as caught:
            pql_document.to_pql_document(program)
        self.assertIn("exec.js:43", str(caught.exception))


@unittest.skipIf(shutil.which("node") is None, "node is not installed")
class NodeReadPql(unittest.TestCase):
    """The browser reader itself judges the documents this experiment writes."""

    def _run(self, cases):
        tmp = tempfile.mkdtemp(prefix="readpql-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        path = os.path.join(tmp, "cases.json")
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump({"cases": cases}, handle)
        proc = subprocess.run(
            ["node", os.path.join(CANDIDATES, "readpql_check.mjs"), path],
            capture_output=True, text=True, cwd=CANDIDATES,
        )
        lines = [json.loads(line) for line in proc.stdout.splitlines() if line.startswith("{")]
        return proc, lines

    def test_node_accepts_the_px_only_fanout_document(self):
        document = pql_document.to_pql_document(PqlDocument.build_fanout()[0])
        proc, lines = self._run([{"name": "fanout", "kind": "accept", "document": document}])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(lines[-1]["ok"], lines)
        self.assertIn("2 calculation(s)", lines[0]["detail"])

    def test_node_reads_a_degraded_fn_binding_as_an_address_and_fails_at_invoke(self):
        program = retain.to_program(day1_run()[2])
        naive = {
            "PrincipleComponentRender": program["name"],
            "Ticks": [
                {"name": tick["name"], "Calculations": [
                    {"call": entry["calculation"],
                     "with": {name: (ref[3:] if ref.startswith("px:") else ref)
                              for name, ref in entry["inputs"].items()},
                     "args": entry["args"], "into": entry["into"]}
                    for entry in tick["calculations"]]}
                for tick in program["ticks"]
            ],
        }
        proc, lines = self._run([{
            "name": "degraded_fn_binding", "kind": "invoke_fails",
            "expect": "slot 'fn:split' not produced yet",
            "seed": {ROWS.address: [], GROUPS_PART.address: {}},
            "document": naive,
        }])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("fn:split", lines[0]["detail"])


class CandidateRecord(unittest.TestCase):
    def test_candidates_readme_matches_a_fresh_lens_run(self):
        if shutil.which("node") is None:
            self.skipTest("node is not installed; the README records node verdicts")
        proc = subprocess.run(
            [sys.executable, os.path.join(CANDIDATES, "refute.py"), "--check"],
            capture_output=True, text=True, cwd=HERE,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_candidates_define_no_lambda(self):
        """CAPTURE.md rule 2: Calculations are named module-level functions.

        Parsed, not grepped: refute.py mentions the token because the leakage lens
        looks for it, which a substring check would report as a violation.
        """
        checked = 0
        for name in sorted(os.listdir(CANDIDATES)):
            path = os.path.join(CANDIDATES, name)
            if not os.path.isfile(path) or not name.endswith(".py"):
                continue
            with open(path, encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
            self.assertEqual([], [n for n in ast.walk(tree) if isinstance(n, ast.Lambda)], name)
            checked += 1
        self.assertEqual(checked, 4)


class DiscStatsSidecar(unittest.TestCase):
    """Critic gap 12: the disc-stats run is retained, with a sidecar and a None digest."""

    @classmethod
    def setUpClass(cls):
        with contextlib.redirect_stdout(io.StringIO()):
            import run_experiment  # noqa: PLC0415 - module-level code runs the experiment

        cls.module = run_experiment
        cls.registry = retain.registry_from_pcr(run_experiment.pcr)
        os.makedirs(EVIDENCE, exist_ok=True)
        cls.record = retain.retain_run(
            run_experiment.pxc,
            run_experiment.run,
            [run_experiment.source.address],
            registry=cls.registry,
            record_path=SIDECAR_RECORD,
        )
        cls.sidecar_ref = cls.record["external"][run_experiment.source.address]["ref"]
        # Written only when the bytes change: a verification run must not dirty
        # committed evidence (Day 1 fixer round 1, finding 2).
        text = json.dumps(cls.record, indent=2, sort_keys=True) + "\n"
        current = None
        if os.path.exists(SIDECAR_RECORD):
            with open(SIDECAR_RECORD, encoding="utf-8") as handle:
                current = handle.read()
        if current != text:
            retain.write_record(cls.record, SIDECAR_RECORD)

    def test_registry_comes_from_the_program_that_ran(self):
        self.assertEqual(sorted(self.registry), ["fn.discStats"])
        self.assertEqual(
            self.record["provider"]["registry"]["fn.discStats"]["module"], "run_experiment"
        )

    def test_non_json_external_becomes_digest_and_ref(self):
        address = self.module.source.address
        entry = self.record["external"][address]
        self.assertEqual(sorted(entry), ["digest", "ref"])
        self.assertRegex(entry["digest"], r"^[0-9a-f]{64}$")
        self.assertFalse(retain.is_jsonable(self.module.pxc.get(address)))

    def test_sidecar_file_exists_and_its_bytes_are_the_digest(self):
        path = os.path.join(EVIDENCE, self.sidecar_ref)
        self.assertTrue(os.path.exists(path), path)
        with open(path, "rb") as handle:
            raw = handle.read()
        self.assertNotIn(b"\r\n", raw)
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            self.record["external"][self.module.source.address]["digest"],
        )
        described = json.loads(raw.decode("utf-8"))
        text = json.dumps(described)
        self.assertIn("$dataclass", text)
        self.assertIn("$date", text)
        for token in FORBIDDEN_TOKENS:
            self.assertNotIn(token, text)

    def test_result_digest_is_none_because_json_cannot_hold_tuple_keys(self):
        self.assertEqual(self.record["results"], {"annotate": None})
        value = self.module.pxc.get(self.module.output)
        self.assertIsInstance(next(iter(value["mold_counts"])), tuple)
        with self.assertRaises(TypeError):
            json.dumps(value)

    def test_the_program_still_round_trips_through_the_registry(self):
        rebuilt = retain.from_program(self.record["program"], self.registry)
        pxc = PxC()
        pxc.set(self.module.source, self.module.pxc.get(self.module.source))
        replayed = rebuilt.run(pxc)
        self.assertEqual(
            json.dumps(testimony_of(replayed), sort_keys=True),
            json.dumps(testimony_of(self.module.run), sort_keys=True),
        )

    def test_evidence_record_is_on_disk_and_names_its_sidecar(self):
        with open(SIDECAR_RECORD, encoding="utf-8") as handle:
            written = json.load(handle)
        self.assertEqual(written["program"], self.record["program"])
        self.assertEqual(
            written["external"][self.module.source.address]["ref"], self.sidecar_ref
        )


def multi_stats(args: dict) -> dict:
    """Two Parts from one pass: the shape the owner decided ({?} WhatIsATick)."""
    rows = args["rows"]
    return {"scratch.multi.mean": sum(rows) / len(rows), "scratch.multi.count": len(rows)}


def multi_take(args: dict):
    return args["value"]


MULTI_REGISTRY = {
    "fn.multi.stats": Calculation("fn.multi.stats", multi_stats),
    "fn.multi.take": Calculation("fn.multi.take", multi_take),
}
MULTI_PRODUCES = ["scratch.multi.mean", "scratch.multi.count"]


class RetainingAMultiProduceProgram(unittest.TestCase):
    """A program whose invocation publishes several Parts retains and replays.

    Before this, `_entry_from_invocation` read `invocation.into.address` and
    `check_record` put `entry["into"]` in a set, so a multi-produce program
    raised AttributeError on the first and TypeError on the second: the retain
    path was the one reader the kernel change had left behind
    (`{?} SingleIntoReaders`, now decided).
    """

    def build(self):
        pxc = PxC()
        pxc.set(Part("scratch.multi.rows"), [1, 2, 3, 4])
        pcr = PCR("multi")
        stats = pcr.calc(
            "Prepare", MULTI_REGISTRY["fn.multi.stats"], id="stats",
            rows=Part("scratch.multi.rows"), into=MULTI_PRODUCES,
        )
        pcr.calc(
            "Report", MULTI_REGISTRY["fn.multi.take"], id="report",
            value=stats["scratch.multi.count"], into="scratch.multi.reported",
        )
        return pcr, pxc

    def test_the_program_retains_with_every_produce_and_the_qualified_binding(self):
        """retain.py `_entry_from_invocation`: `into` is the list of addresses and a
        result binding carries the produce it read.

        Mutation: `invocation.into.address` as before -- AttributeError on a tuple;
        `f"{FN}{source.calculation_id}"` without the produce -- the rebuilt program
        below binds the whole mapping and PCR.calc refuses it as a bare reference.
        """
        pcr, _ = self.build()
        program = retain.to_program(pcr)
        stats, report = program["ticks"][0]["calculations"][0], program["ticks"][1]["calculations"][0]
        self.assertEqual(stats["into"], MULTI_PRODUCES)
        self.assertEqual(report["inputs"], {"value": "fn:stats#scratch.multi.count"})
        self.assertEqual(report["into"], "scratch.multi.reported")
        self.assertEqual(json.loads(json.dumps(program)), program)  # JSON, not tuples

    def test_the_authoring_and_testimony_exports_agree(self):
        """`to_program(run)["ticks"] == asdict(run.ticks)` still holds when `into` is a
        list: both paths normalize the tuple to a JSON array.
        """
        pcr, pxc = self.build()
        run = pcr.run(pxc)
        self.assertEqual(retain.to_program(pcr)["ticks"], retain.to_program(run)["ticks"])

    def test_the_retained_program_rebuilds_and_replays_to_the_same_values(self):
        """retain.py `_result_ref`: `fn:<id>#<address>` parses back to the produce it
        names, so the replay reads the same Part the original did.

        Mutation: `ResultRef(body)` for every `fn:` ref -- the rebuilt program binds a
        bare reference to a multi-produce invocation and PCR.calc refuses it.
        """
        pcr, pxc = self.build()
        original = pcr.run(pxc)
        rebuilt = retain.from_program(retain.to_program(pcr), MULTI_REGISTRY)
        fresh = PxC()
        fresh.set(Part("scratch.multi.rows"), [1, 2, 3, 4])
        replayed = rebuilt.run(fresh)
        self.assertEqual(replayed.results["report"], 4)
        self.assertEqual(fresh.get(Part("scratch.multi.mean")), 2.5)
        self.assertEqual(fresh.get(Part("scratch.multi.count")), 4)
        self.assertEqual(
            json.dumps(testimony_of(replayed), sort_keys=True),
            json.dumps(testimony_of(original), sort_keys=True),
        )

    def test_the_record_round_trips_and_check_record_reads_every_produce(self):
        """retain.py `check_record`: the computed addresses are the union of every
        entry's produces, so a list `into` is neither unhashable nor half-read.

        Mutation: `{entry.get("into") for entry in entries ...}` as before --
        TypeError: unhashable type 'list'. Read as one address only, the second
        refusal below (pre-seeding a Part the program computes) would not fire.
        """
        pcr, pxc = self.build()
        run = pcr.run(pxc, observe=True)
        with tempfile.TemporaryDirectory(prefix="retain-multi-") as tmp:
            record = retain.retain_run(
                pxc, run, ["scratch.multi.rows"],
                registry=MULTI_REGISTRY,
                record_path=os.path.join(tmp, "retained.json"),
            )
            checked = retain.check_record(record)
            self.assertEqual(
                checked["into_addresses"],
                sorted(MULTI_PRODUCES + ["scratch.multi.reported"]),
            )
            for address in MULTI_PRODUCES:
                with self.subTest(address=address):
                    forged = copy.deepcopy(record)
                    forged["external"][address] = 0
                    with self.assertRaises(retain.ContradictoryRecordError) as caught:
                        retain.check_record(forged)
                    self.assertIn(address, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
