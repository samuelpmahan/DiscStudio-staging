"""Executable spec of the Day 3 Tick materializer (ULTRACODE-WEEK.md Day 3, lane A).

`pyto.materialize` is the missing join named in research/tick-observability-ledger.md:60-85:
`PcrRun.ticks` (the Tick boundary), `PcrRun.receipts` (writer, reads, duration, digest)
and `PcrRun.results` (the value) become one `pyto-run-record@1` document, specified in
pyto/viewer/RECORD.md and read by both runtimes.

The module is additive: it only reads a `PcrRun`, so the bytes consumers embed in
compositionEvidence -- `json.dumps([asdict(t) for t in run.ticks])`
(consumers/discstudio-card/card_composition.py:177, app.py:53) -- are identical before
and after materializing. `TestimonyBytesUnchangedByMaterializing` is that oracle.

Every Calculation body is a named module-level function; no lambdas
(experiments/CAPTURE.md, rule 2).
"""

from __future__ import annotations

import hashlib
import io
import json
import random
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import asdict

from pyto import Calculation, Part, PCR, PxC
from pyto import materialize as materialize_module
from pyto.materialize import (
    ARRAY_CAP,
    SCHEMA,
    VALUE_CAP_BYTES,
    _png_budget,
    _stable_repr,
    render_value,
    run_record,
    tick_sheets,
    write_record,
)
from pyto.pcr import array_sha256

# Intra-repo sys.path insert (experiments/CAPTURE.md): the Day 1 program lives in
# experiments/grouped-ablation/ and its modules import each other by top-level name.
# Announced on stderr so it appears in the test log, exactly as tests/test_receipts.py does.
PYTO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPERIMENT_DIR = os.path.join(PYTO_ROOT, "experiments", "grouped-ablation")
if EXPERIMENT_DIR not in sys.path:
    print(f"[tests/test_materialize] sys.path.insert(0, {EXPERIMENT_DIR!r})", file=sys.stderr)
    sys.path.insert(0, EXPERIMENT_DIR)

from calculations import select_variants  # noqa: E402
from features import GROUPS, make_data  # noqa: E402
from program import GROUPS as GROUPS_PART, ROWS, build_program  # noqa: E402

# The second reader of the shared format. viewer/test/record_schema.py is a Python
# validator transcribed from RECORD.md independently of both adapters.js and
# pyto.materialize, so running this producer's output through it is a check by
# something other than the producer -- which is what the receipt-less document
# lacked when it claimed a schema the reference reader refuses.
VIEWER_TEST_DIR = os.path.join(PYTO_ROOT, "viewer", "test")
if VIEWER_TEST_DIR not in sys.path:
    print(f"[tests/test_materialize] sys.path.insert(0, {VIEWER_TEST_DIR!r})", file=sys.stderr)
    sys.path.insert(0, VIEWER_TEST_DIR)

from record_schema import RecordSchemaError  # noqa: E402
from record_schema import validate as validate_record  # noqa: E402

SEED, N = 7, 400  # run.py:main defaults; evidence/run-1/comparison.json records seed 7, n 400

# The committed Day 1 evidence: the shipped bytes of a real run, read here as a
# record rather than regenerated, so the rule is checked against what was published.
RUN_1_RECORD = os.path.join(EXPERIMENT_DIR, "evidence", "run-1", "record.json")

SVG_DOCUMENT = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8">'
    '<rect width="8" height="8" fill="#39ff14"/></svg>'
)

try:  # Pillow is optional for the record; only the sheet tests need it.
    from PIL import Image

    PILLOW = True
except ImportError:  # pragma: no cover - Pillow is installed in this checkout
    PILLOW = False

try:  # numpy is optional too; only the array-value tests need it.
    import numpy

    NUMPY = True
except ImportError:  # pragma: no cover - numpy is installed in this checkout
    NUMPY = False


# --- module-level calculation bodies (named functions only) --------------------


def emit_svg(args):
    return SVG_DOCUMENT


def emit_set(args):
    return {"b", "a", "c"}


def emit_long_list(args):
    return list(range(1000))


def emit_text(args):
    return "not an svg, just text"


def emit_big_text(args):
    return "x" * 300000


def emit_image(args):
    return Image.new("RGBA", (4, 3), (255, 0, 255, 255))


def emit_big_noise_image(args):
    """A 512x512 RGB noise image: nothing compresses it under the value cap."""
    pixels = random.Random(11).randbytes(512 * 512 * 3)
    return Image.frombytes("RGB", (512, 512), pixels)


def emit_array(args):
    return numpy.arange(24, dtype="uint8").reshape(2, 4, 3)


def emit_long_array(args):
    return numpy.arange(5000, dtype="int32")


def emit_object_array(args):
    return numpy.array([{"a": 1}, {"b": 2}], dtype=object)


def read_part(args):
    return args["seeded"]


def emit_cycle(args):
    node = {"name": "node"}
    node["self"] = node
    return node


def bump_counter(args):
    return {"n": args["counter"]["n"] + 1}


def join_two_parts(args):
    # Two Part bindings whose parameter names sort the other way round from the
    # order they were bound in, so "binding order" and "sorted by name" disagree.
    return {"z": args["zebra"], "a": args["alpha"]}


def emit_undecodable_png_data_url(args):
    # RECORD.md:109-110 fixes the prefix, not the payload; this exact string is the
    # repo's own JS render fixture (viewer/test/render.test.mjs:218), where the
    # viewer renders it as an <img> without complaint.
    return "data:image/png;base64,iVBORw0KGgo="


def _day_one_run():
    """The Day 1 program executed with observe=True; returns (run, pxc, preexisting)."""
    rows = make_data(SEED, N)
    pxc = PxC()
    pxc.set(ROWS, rows)
    pxc.set(GROUPS_PART, GROUPS)
    preexisting = set(pxc.addresses())
    pcr = build_program(select_variants({"groups": GROUPS}))
    return pcr.run(pxc, observe=True), pxc, preexisting


def _one_calc_run(calculation, *, seeded=None):
    """A one-invocation PCR whose result is `calculation`'s return value."""
    pxc = PxC()
    pcr = PCR("materialize.spec")
    if seeded is None:
        pcr.calc("Only", calculation, id="only", into="scratch.spec.value")
    else:
        pxc.set(Part("input.spec.seeded"), seeded)
        pcr.calc(
            "Only",
            calculation,
            id="only",
            seeded=Part("input.spec.seeded"),
            into="scratch.spec.value",
        )
    preexisting = set(pxc.addresses())
    return pcr.run(pxc, observe=True), pxc, preexisting


class DayOneRecord(unittest.TestCase):
    """The record of the Day 1 grouped ablation: shape, Tick join, and the hit ledger."""

    @classmethod
    def setUpClass(cls):
        run, pxc, preexisting = _day_one_run()
        cls.day_one = run  # not `cls.run`: TestCase.run is the runner method
        cls.record = run_record(run, pxc, preexisting=preexisting)

    def test_schema_and_pcr_name(self):
        self.assertEqual(self.record["schema"], SCHEMA)
        self.assertEqual(self.record["schema"], "pyto-run-record@1")
        self.assertEqual(self.record["pcr"], "ablation.grouped")
        self.assertEqual(self.record["source"]["runtime"], "pyto")
        self.assertIsNone(self.record["source"]["commit"])

    def test_four_ticks_and_fifteen_invocations(self):
        self.assertEqual(len(self.record["ticks"]), 4)
        self.assertEqual(
            [tick["name"] for tick in self.record["ticks"]],
            ["Prepare", "Fit", "Score", "Compare"],
        )
        self.assertEqual([tick["index"] for tick in self.record["ticks"]], [0, 1, 2, 3])
        invocations = [inv for tick in self.record["ticks"] for inv in tick["invocations"]]
        self.assertEqual(len(invocations), 15)
        self.assertEqual(self.record["counters"]["invocations"], 15)

    def test_pcr_name_can_be_overridden_for_the_viewer(self):
        run, pxc, preexisting = _day_one_run()
        record = run_record(run, pxc, preexisting=preexisting, pcr_name="grouped-ablation")
        self.assertEqual(record["pcr"], "grouped-ablation")

    def test_every_fit_and_score_reads_fn_split_and_is_not_a_hit(self):
        seen = 0
        for tick in self.record["ticks"]:
            for invocation in tick["invocations"]:
                if not invocation["id"].startswith(("fit.", "score.")):
                    continue
                seen += 1
                with self.subTest(invocation=invocation["id"]):
                    # pcr.py:112-116 rewrote the Part binding into the writer's
                    # ResultRef, which is the shared-intermediate evidence Day 1 exists
                    # to show -- and why no fit/score reads a preexisting Part.
                    self.assertEqual(invocation["inputs"]["split"], "fn:split")
                    self.assertFalse(invocation["hit"])
        self.assertEqual(seen, 12)

    def test_the_two_invocations_reading_a_preseeded_part_are_the_hits(self):
        hits = [
            invocation["id"]
            for tick in self.record["ticks"]
            for invocation in tick["invocations"]
            if invocation["hit"]
        ]
        self.assertEqual(hits, ["select", "split"])
        self.assertEqual(self.record["counters"]["hits"], 2)
        self.assertEqual(self.record["counters"]["computed"], 13)
        prepare = {inv["id"]: inv for inv in self.record["ticks"][0]["invocations"]}
        self.assertEqual(prepare["split"]["inputs"], {"rows": "px:input.ablation.rows"})
        self.assertTrue(self.record["parts"]["input.ablation.rows"]["preexisting"])

    def test_receipt_fields_are_joined_by_invocation_id(self):
        split = self.record["ticks"][0]["invocations"][1]
        receipt = self.day_one.receipts["split"]
        self.assertEqual(split["id"], "split")
        self.assertEqual(split["calculation"]["address"], "fn.ablation.split")
        self.assertEqual(
            split["calculation"]["implementation_sha256"],
            receipt.calculation.implementation_sha256,
        )
        self.assertEqual(split["calculation"]["identity_scope"], "runtime-function-body")
        self.assertEqual(split["declared_consumes"], ["px:input.ablation.rows"])
        self.assertEqual(split["actual_consumes"], ["input.ablation.rows"])
        self.assertEqual(split["actual_produces"], ["scratch.ablation.split"])
        self.assertEqual(
            split["writes"], [{"address": "scratch.ablation.split", "kind": "new-address"}]
        )
        self.assertEqual(split["duration_ms"], receipt.duration_ms)
        self.assertEqual(split["result_sha256"], receipt.result_sha256)
        self.assertEqual(split["into"], "scratch.ablation.split")

    def test_parts_map_lists_the_twelve_fn_readers_of_the_split_part(self):
        part = self.record["parts"]["scratch.ablation.split"]
        self.assertEqual(part["written_by"], "split")
        self.assertFalse(part["preexisting"])
        self.assertEqual(len(part["read_by"]), 12)
        self.assertIn("fit.all", part["read_by"])
        self.assertIn("score.drop_g3", part["read_by"])
        self.assertEqual(self.record["parts"]["input.ablation.rows"]["written_by"], None)
        self.assertEqual(self.record["parts"]["input.ablation.rows"]["read_by"], ["split"])

    def test_wall_ms_is_the_sum_of_the_receipt_durations(self):
        total = sum(receipt.duration_ms for receipt in self.day_one.receipts.values())
        self.assertAlmostEqual(self.record["counters"]["wall_ms"], total, places=9)

    def test_without_observe_run_record_refuses_instead_of_emitting_nulls(self):
        """A document is `pyto-run-record@1` or it is not tagged as one.

        RECORD.md marks its nullable fields explicitly (`"<hex or null>"`,
        `"<sha or null>"`) and marks none of `calculation.identity_scope`,
        `actual_consumes`, `actual_produces`, `writes`, so RECORD.md:114 ("missing
        fields are null, never invented") does not license nulling them: the
        reference reader (adapters.js `validate`) refuses the result, and so does
        the independent Python validator. Emitting it anyway was a document that
        claimed the shared schema and no reader of that schema would take. The
        only caller, experiments/grouped-ablation/materialize_run.py:107-112,
        already passes observe=True, so nothing downstream changes.
        """
        rows = make_data(SEED, N)
        pxc = PxC()
        pxc.set(ROWS, rows)
        pxc.set(GROUPS_PART, GROUPS)
        preexisting = set(pxc.addresses())
        pcr = build_program(select_variants({"groups": GROUPS}))
        run = pcr.run(pxc)  # no observe: PcrRun.receipts is empty (pcr.py:130-145)
        self.assertEqual(run.receipts, {})
        with self.assertRaises(ValueError) as caught:
            run_record(run, pxc, preexisting=preexisting)
        message = str(caught.exception)
        self.assertIn("observe=True", message)
        self.assertIn("15 of 15 invocation(s) have none", message)
        self.assertIn("identity_scope", message)

    def test_the_shape_it_refuses_to_emit_is_the_shape_a_reader_refuses(self):
        """Why the refusal above is a refusal and not a null-filled document."""
        record = json.loads(json.dumps(self.record))
        validate_record(record)  # the observed document is readable
        invocation = record["ticks"][0]["invocations"][0]
        invocation["calculation"]["identity_scope"] = None
        with self.assertRaises(RecordSchemaError) as caught:
            validate_record(record)
        self.assertEqual(caught.exception.path, "ticks[0].invocations[0].calculation.identity_scope")
        invocation["calculation"]["identity_scope"] = "runtime-function-body"
        for field in ("actual_consumes", "actual_produces", "writes"):
            with self.subTest(field=field):
                keep = invocation[field]
                invocation[field] = None
                with self.assertRaises(RecordSchemaError) as caught:
                    validate_record(record)
                self.assertEqual(caught.exception.path, f"ticks[0].invocations[0].{field}")
                invocation[field] = keep
        validate_record(record)


def _px_subset(inputs):
    """The rule as RECORD.md states it: the `px:` bindings, in binding order."""
    return [binding for binding in inputs.values() if binding.startswith("px:")]


def _rule_violations(record):
    """Every invocation whose `declared_consumes` is not the `px:` subset of `inputs`."""
    return [
        (invocation["id"], invocation["declared_consumes"], _px_subset(invocation["inputs"]))
        for tick in record["ticks"]
        for invocation in tick["invocations"]
        if invocation["declared_consumes"] != _px_subset(invocation["inputs"])
    ]


class DeclaredConsumesIsThePartSubsetOfInputs(unittest.TestCase):
    """RECORD.md field rules, after the Day 3 amendment.

    `inputs` is the complete binding map; `declared_consumes` is the producing
    runtime's declared *Part* reads only -- the `px:` bindings, in binding order --
    so it is empty wherever every binding is an `fn:` result ref. The earlier text
    ("declared_consumes repeats them in binding order") described a document pyto
    has never emitted: pcr.py:308-315 fills Receipt.declared_consumes from bindings
    whose source is a Part and from nothing else, and materialize.py:416 only adds
    the `px:` prefix. Both reference readers already union the two fields
    (viewer/adapters.js:385-390, viewer/test/record_schema.py:290-299), so the
    contract text was the only thing out of step. These tests pin the shipped
    convention on both sides of it: the published bytes, and the producer.
    """

    def test_the_committed_evidence_record_carries_only_the_px_bindings(self):
        if not os.path.isfile(RUN_1_RECORD):  # pragma: no cover - the evidence is committed
            self.skipTest(f"{RUN_1_RECORD} is not present")
        with open(RUN_1_RECORD, encoding="utf-8") as handle:
            record = json.load(handle)
        self.assertEqual(_rule_violations(record), [])
        invocations = [inv for tick in record["ticks"] for inv in tick["invocations"]]
        self.assertEqual(len(invocations), 15)
        # The shape that made the old sentence false: an invocation bound only to
        # results declares no Part read at all, so the field is empty, not a copy
        # of `inputs`. 13 of the 15 -- everything downstream of `split`.
        empty = [inv["id"] for inv in invocations if not inv["declared_consumes"]]
        self.assertEqual(len(empty), 13)
        self.assertEqual(
            [inv["id"] for inv in invocations if inv["declared_consumes"]], ["select", "split"]
        )
        for invocation in invocations:
            if not invocation["declared_consumes"]:
                with self.subTest(invocation=invocation["id"]):
                    self.assertTrue(invocation["inputs"])
                    self.assertTrue(
                        all(b.startswith("fn:") for b in invocation["inputs"].values())
                    )

    def test_a_freshly_materialized_day_one_record_obeys_the_same_rule(self):
        run, pxc, preexisting = _day_one_run()
        record = run_record(run, pxc, preexisting=preexisting)
        self.assertEqual(_rule_violations(record), [])
        by_id = {inv["id"]: inv for tick in record["ticks"] for inv in tick["invocations"]}
        self.assertEqual(by_id["split"]["declared_consumes"], ["px:input.ablation.rows"])
        self.assertEqual(by_id["fit.all"]["inputs"], {"split": "fn:split"})
        self.assertEqual(by_id["fit.all"]["declared_consumes"], [])
        # `fn:` is served from the run's results, never from the store, so the
        # actuals are empty too -- which is why a part index needs the union.
        self.assertEqual(by_id["fit.all"]["actual_consumes"], [])
        self.assertEqual(by_id["compare"]["declared_consumes"], [])

    def test_two_part_bindings_keep_binding_order_not_alphabetical_order(self):
        pxc = PxC()
        pxc.set(Part("input.spec.zebra"), 1)
        pxc.set(Part("input.spec.alpha"), 2)
        preexisting = set(pxc.addresses())
        pcr = PCR("materialize.order")
        pcr.calc(
            "Only",
            Calculation("fn.spec.join", join_two_parts),
            id="only",
            zebra=Part("input.spec.zebra"),
            alpha=Part("input.spec.alpha"),
            into="scratch.spec.joined",
        )
        record = run_record(pcr.run(pxc, observe=True), pxc, preexisting=preexisting)
        invocation = record["ticks"][0]["invocations"][0]
        self.assertEqual(
            invocation["declared_consumes"], ["px:input.spec.zebra", "px:input.spec.alpha"]
        )
        self.assertEqual(_rule_violations(record), [])
        # Named so a sorted() creeping into the collection is a failure and not a
        # coincidence: alphabetical order is the other answer here.
        self.assertNotEqual(
            invocation["declared_consumes"], sorted(invocation["declared_consumes"])
        )


class TestimonyBytesUnchangedByMaterializing(unittest.TestCase):
    """The record is derived; producing it must not touch the testimony consumers embed."""

    def test_asdict_bytes_are_identical_before_and_after(self):
        run, pxc, preexisting = _day_one_run()
        before = json.dumps([asdict(tick) for tick in run.ticks])
        record = run_record(run, pxc, preexisting=preexisting)
        out_dir = tempfile.mkdtemp(prefix="materialize-testimony-")
        self.addCleanup(shutil.rmtree, out_dir, ignore_errors=True)
        write_record(record, os.path.join(out_dir, "record.json"))
        if PILLOW:
            tick_sheets(record, os.path.join(out_dir, "ticks"))
        after = json.dumps([asdict(tick) for tick in run.ticks])
        self.assertEqual(before, after)
        self.assertEqual(run.pcr, "ablation.grouped")


class ValueKinds(unittest.TestCase):
    """RECORD.md:108-113: json | text | svg | png-data-url | omitted, with the caps."""

    def _value(self, calculation_address, body):
        run, pxc, preexisting = _one_calc_run(Calculation(calculation_address, body))
        record = run_record(run, pxc, preexisting=preexisting)
        return record["ticks"][0]["invocations"][0]["value"]

    def test_svg_is_kind_svg_and_the_document_is_not_modified(self):
        value = self._value("fn.spec.svg", emit_svg)
        self.assertEqual(value["kind"], "svg")
        self.assertEqual(value["data"], SVG_DOCUMENT)
        self.assertIsNone(value["note"])

    def test_xml_prologue_before_the_svg_root_is_still_svg(self):
        rendered = render_value('<?xml version="1.0"?>\n' + SVG_DOCUMENT)
        self.assertEqual(rendered["kind"], "svg")
        self.assertTrue(rendered["data"].endswith("</svg>"))

    def test_a_plain_string_is_text(self):
        value = self._value("fn.spec.text", emit_text)
        self.assertEqual(value["kind"], "text")
        self.assertEqual(value["data"], "not an svg, just text")

    def test_a_string_that_is_already_a_png_data_url_is_png_data_url_as_in_javascript(self):
        # adapters.js:262-264 is the reference (ULTRACODE-WEEK.md Reframing 4,
        # "JS is first class") and viewer/test/adapters.test.mjs pins it there.
        # Without this branch the same Part reads as a picture from a DiscStudio
        # record and as a wall of base64 from a pyto one.
        url = "data:image/png;base64,iVBORw0KGgo="
        rendered = render_value(url)
        self.assertEqual(rendered["kind"], "png-data-url")
        self.assertEqual(rendered["data"], url)
        self.assertIsNone(rendered["note"])
        # The test is on the raw string, not a stripped one: `data` is what a
        # viewer puts in an <img src>, and RECORD.md:109-110 fixes those bytes.
        self.assertEqual(render_value("   " + url)["kind"], "text")
        self.assertEqual(render_value("data:image/svg+xml,<svg/>")["kind"], "text")
        # An SVG document still wins, in that order.
        self.assertEqual(render_value(SVG_DOCUMENT)["kind"], "svg")

    def test_a_set_is_omitted_with_a_note_and_a_digest(self):
        value = self._value("fn.spec.set", emit_set)
        self.assertEqual(value["kind"], "omitted")
        self.assertIsNone(value["data"])
        self.assertIn("not JSON-serializable (set", value["note"])
        self.assertIn("sha256", value["note"])
        # The digest is of a *canonical* repr -- sets and dict keys ordered -- so it
        # does not depend on set iteration order. Pinned as the literal digest of the
        # documented rendering, not as "whatever repr() said in this process".
        canonical = hashlib.sha256("{'a', 'b', 'c'}".encode("utf-8")).hexdigest()
        self.assertIn(canonical, value["note"])
        self.assertEqual(value["note"], render_value({"c", "b", "a"})["note"])

    def test_the_omitted_digest_is_the_same_in_a_process_with_a_different_hash_seed(self):
        """PYTHONHASHSEED salts str hashing, so set iteration order differs per process.

        Two child processes with different seeds must still report the same digest for
        the same set; a digest of the raw `repr` would not (research/ULTRACODE-WEEK.md
        critic gap 10 makes the same point about process-dependent digests).
        """
        program = (
            "from pyto.materialize import render_value;"
            "print(render_value({'alpha', 'beta', 'gamma', 'delta'})['note'])"
        )
        notes = []
        for seed in ("0", "1", "12345"):
            environment = dict(os.environ, PYTHONHASHSEED=seed)
            completed = subprocess.run(
                [sys.executable, "-c", program], capture_output=True, text=True, env=environment
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            notes.append(completed.stdout.strip())
        self.assertEqual(len(set(notes)), 1, notes)
        self.assertIn("sha256", notes[0])

    def test_a_thousand_element_list_keeps_two_hundred_entries_and_says_so(self):
        value = self._value("fn.spec.long", emit_long_list)
        self.assertEqual(value["kind"], "json")
        self.assertEqual(len(value["data"]), 200)
        self.assertEqual(value["data"][:3], [0, 1, 2])
        self.assertIn("truncated to the first 200 entries", value["note"])
        self.assertIn("1000", value["note"])

    def test_the_array_cap_is_a_parameter_and_applies_inside_a_dict(self):
        rendered = render_value({"rows": list(range(50))}, array_cap=10)
        self.assertEqual(len(rendered["data"]["rows"]), 10)
        self.assertIn("original lengths: [50]", rendered["note"])

    def test_a_value_over_the_cap_is_omitted_with_size_and_digest(self):
        value = self._value("fn.spec.big", emit_big_text)
        self.assertEqual(value["kind"], "omitted")
        self.assertIn("300000 bytes", value["note"])
        self.assertIn("over the 262144 byte cap", value["note"])
        self.assertIn("sha256", value["note"])

    @unittest.skipUnless(PILLOW, "Pillow is not installed")
    def test_a_pil_image_becomes_a_png_data_url(self):
        value = self._value("fn.spec.image", emit_image)
        self.assertEqual(value["kind"], "png-data-url")
        self.assertTrue(value["data"].startswith("data:image/png;base64,"))
        self.assertIsNone(value["note"])

    def test_a_non_serializable_value_never_gets_a_json_kind(self):
        for candidate in (object(), {1, 2}, {(1, 2): "tuple key"}):
            with self.subTest(candidate=type(candidate).__name__):
                self.assertEqual(render_value(candidate)["kind"], "omitted")

    def test_a_cyclic_value_is_omitted_with_a_note_not_a_recursion_error(self):
        """RECORD.md:111 assigns "not serializable" to `omitted`, cycles included.

        The JS reference does exactly that (adapters.js:281-295 materialize returns
        `{kind: 'omitted', note: 'value is not JSON serializable: Converting
        circular structure to JSON...'}`), so a cyclic Part value must not be the
        one input on which the two runtimes' records differ -- and it must not take
        the whole document down: json.dumps raises ValueError on a cycle, and a
        rendering with no cycle memo then raised RecursionError straight out of
        run_record.
        """
        node = {"name": "node"}
        node["self"] = node
        rendered = render_value(node)
        self.assertEqual(rendered["kind"], "omitted")
        self.assertIsNone(rendered["data"])
        self.assertIn("not JSON-serializable (dict", rendered["note"])
        self.assertIn("sha256", rendered["note"])
        # The canonical rendering marks a repeated container the way repr() does.
        self.assertEqual(_stable_repr(node), "{'name': 'node', 'self': {...}}")
        self.assertEqual(_stable_repr(node), repr(node))

        ring = [1]
        ring.append(ring)
        self.assertEqual(render_value(ring)["kind"], "omitted")
        self.assertEqual(_stable_repr(ring), repr(ring))

        # A container repeated but not cyclic is still rendered in full: the memo
        # is the recursion stack, not a seen-set.
        shared = {"k": 1}
        self.assertEqual(_stable_repr([shared, shared]), "[{'k': 1}, {'k': 1}]")

    def test_a_value_nested_past_the_recursion_limit_is_omitted_not_fatal(self):
        """json.dumps raises RecursionError -- neither TypeError nor ValueError."""
        deep: list = []
        inner = deep
        for _ in range(6000):
            nested: list = []
            inner.append(nested)
            inner = nested
        rendered = render_value(deep)
        self.assertEqual(rendered["kind"], "omitted")
        self.assertIsNone(rendered["data"])
        self.assertIn("RecursionError", rendered["note"])

    def test_a_cyclic_part_value_leaves_the_rest_of_the_record_intact(self):
        """The failure this guards is not one value: it was the whole document."""
        pxc = PxC()
        pcr = PCR("materialize.cyclic")
        pcr.calc("One", Calculation("fn.spec.cycle", emit_cycle), id="cyclic", into="scratch.spec.cycle")
        pcr.calc("One", Calculation("fn.spec.text", emit_text), id="fine", into="scratch.spec.fine")
        record = run_record(pcr.run(pxc, observe=True), pxc, preexisting=set())
        cyclic, fine = record["ticks"][0]["invocations"]
        self.assertEqual(cyclic["value"]["kind"], "omitted")
        self.assertEqual(fine["value"], {"kind": "text", "data": "not an svg, just text", "note": None})
        validate_record(record)


class HitLedger(unittest.TestCase):
    """The owner's definition (ULTRACODE-WEEK.md:79-82): a Part being used is a hit."""

    def test_reading_a_preseeded_part_is_a_hit(self):
        run, pxc, preexisting = _one_calc_run(
            Calculation("fn.spec.read", read_part), seeded={"n": 1}
        )
        record = run_record(run, pxc, preexisting=preexisting)
        invocation = record["ticks"][0]["invocations"][0]
        self.assertTrue(invocation["hit"])
        self.assertEqual(invocation["inputs"], {"seeded": "px:input.spec.seeded"})
        self.assertEqual(record["counters"]["hits"], 1)
        self.assertEqual(record["counters"]["computed"], 0)
        self.assertTrue(record["parts"]["input.spec.seeded"]["preexisting"])

    def test_a_part_no_invocation_produced_is_a_hit_even_with_an_empty_preexisting_set(self):
        """The second half of the rule: `preexisting` is not the only evidence.

        RECORD.md:104-107 -- a `px:` binding whose address was not produced by an earlier
        invocation of the same run is a hit. A caller that cannot supply the pre-run
        store (or supplies an empty one) still gets the Day 1 answer, because nothing
        in the run wrote `input.ablation.rows`.
        """
        run, pxc, _preexisting = _day_one_run()
        record = run_record(run, pxc, preexisting=set())
        hits = [
            invocation["id"]
            for tick in record["ticks"]
            for invocation in tick["invocations"]
            if invocation["hit"]
        ]
        self.assertEqual(hits, ["select", "split"])

    def test_an_address_produced_earlier_in_the_run_is_not_a_hit(self):
        pxc = PxC()
        pcr = PCR("materialize.chain")
        pcr.calc("A", Calculation("fn.spec.text", emit_text), id="first", into="scratch.spec.a")
        # Bound by address, but pcr.py:112-116 rewrites it: the record must still show
        # that the reader consumed a Part this run produced, so it is not a hit.
        pcr.calc(
            "B",
            Calculation("fn.spec.read", read_part),
            id="second",
            seeded=Part("scratch.spec.a"),
            into="scratch.spec.b",
        )
        run = pcr.run(pxc, observe=True)
        record = run_record(run, pxc, preexisting=set())
        second = record["ticks"][1]["invocations"][0]
        self.assertEqual(second["inputs"], {"seeded": "fn:first"})
        self.assertFalse(second["hit"])
        self.assertEqual(record["parts"]["scratch.spec.a"]["read_by"], ["second"])
        self.assertEqual(record["counters"]["hits"], 0)

    def test_re_reading_a_part_this_run_overwrote_is_not_a_hit_as_in_javascript(self):
        """The one shape on which the two runtimes used to disagree.

        RECORD.md:104-105 states the rule with its own exclusion -- "a `px:` binding
        whose address was not produced by an earlier invocation of the same run" --
        and adapters.js:244-249 `deriveHit` implements exactly that: it never
        consults a preexisting set. `bump` reads a Part nothing had produced (a
        hit) and refines it; `read` then binds the same address, which this run has
        now written, so nothing is reused and it is not a hit. ORing in
        `address in preexisting` reported it as a hit while the value it shows is
        the freshly computed one, and validate() cannot catch that -- the counters
        stay self-consistent either way. The JS side pins the same shape in
        viewer/test/adapters.test.mjs.
        """
        pxc = PxC()
        pxc.set(Part("shared.counter"), {"n": 1})
        preexisting = set(pxc.addresses())
        pcr = PCR("materialize.overwrite")
        pcr.calc(
            "One",
            Calculation("fn.spec.bump", bump_counter),
            id="bump",
            counter=Part("shared.counter"),
            into="shared.counter",
        )
        # Tick.calc (pcr.py:37-60), not PCR.calc: the Tick's own binder does not
        # rewrite a Part binding into the writer's ResultRef, so `read` really does
        # carry `px:shared.counter` after this run has overwritten that address.
        pcr.tick("Two").calc(
            Calculation("fn.spec.read", read_part),
            id="read",
            seeded=Part("shared.counter"),
            into="scratch.spec.out",
        )
        run = pcr.run(pxc, observe=True)
        record = run_record(run, pxc, preexisting=preexisting)
        validate_record(record)

        bump = record["ticks"][0]["invocations"][0]
        read = record["ticks"][1]["invocations"][0]
        self.assertEqual(bump["writes"], [{"address": "shared.counter", "kind": "refinement"}])
        self.assertTrue(bump["hit"], "bump read a Part no invocation of this run had produced")
        self.assertEqual(read["inputs"], {"seeded": "px:shared.counter"})
        self.assertFalse(read["hit"], "this run wrote shared.counter; nothing was reused")
        self.assertEqual(read["value"], {"kind": "json", "data": {"n": 2}, "note": None})
        self.assertEqual(record["counters"]["hits"], 1)
        self.assertEqual(record["counters"]["computed"], 1)
        # preexisting is still reported, on the Part where it belongs.
        self.assertTrue(record["parts"]["shared.counter"]["preexisting"])


class Determinism(unittest.TestCase):
    def test_two_records_of_two_runs_differ_only_in_durations(self):
        first_run, first_pxc, first_pre = _day_one_run()
        second_run, second_pxc, second_pre = _day_one_run()
        first = run_record(first_run, first_pxc, preexisting=first_pre)
        second = run_record(second_run, second_pxc, preexisting=second_pre)
        self.assertNotEqual(first, second)  # durations really do differ
        self.assertEqual(_without_durations(first), _without_durations(second))

    def test_materializing_the_same_run_twice_is_byte_identical(self):
        run, pxc, preexisting = _day_one_run()
        once = json.dumps(run_record(run, pxc, preexisting=preexisting), sort_keys=True)
        twice = json.dumps(run_record(run, pxc, preexisting=preexisting), sort_keys=True)
        self.assertEqual(once, twice)


def _without_durations(record):
    """The record with every wall-clock field dropped: what determinism can be asserted on."""
    copy = json.loads(json.dumps(record))
    copy["counters"]["wall_ms"] = None
    for tick in copy["ticks"]:
        for invocation in tick["invocations"]:
            invocation["duration_ms"] = None
    return copy


class WriteRecord(unittest.TestCase):
    def setUp(self):
        self.out_dir = tempfile.mkdtemp(prefix="materialize-write-")
        self.addCleanup(shutil.rmtree, self.out_dir, ignore_errors=True)

    def test_round_trips_through_json_load_with_sorted_keys_and_lf(self):
        run, pxc, preexisting = _day_one_run()
        record = run_record(run, pxc, preexisting=preexisting)
        path = write_record(record, os.path.join(self.out_dir, "nested", "record.json"))
        with open(path, encoding="utf-8") as handle:
            self.assertEqual(json.load(handle), record)
        with open(path, "rb") as handle:
            raw = handle.read()
        self.assertNotIn(b"\r\n", raw)
        self.assertTrue(raw.endswith(b"\n"))
        text = raw.decode("utf-8")
        self.assertTrue(text.startswith("{\n  \"counters\": {"), text[:40])
        self.assertLess(text.index('"counters"'), text.index('"pcr"'))
        self.assertLess(text.index('"pcr"'), text.index('"schema"'))


@unittest.skipUnless(PILLOW, "Pillow is not installed")
class TickSheets(unittest.TestCase):
    def setUp(self):
        self.out_dir = tempfile.mkdtemp(prefix="materialize-sheets-")
        self.addCleanup(shutil.rmtree, self.out_dir, ignore_errors=True)

    def test_one_png_per_tick_of_the_day_one_program(self):
        run, pxc, preexisting = _day_one_run()
        record = run_record(run, pxc, preexisting=preexisting)
        paths = tick_sheets(record, self.out_dir)
        names = sorted(os.path.basename(path) for path in paths)
        self.assertEqual(
            names,
            [
                "tick-000-Prepare.png",
                "tick-001-Fit.png",
                "tick-002-Score.png",
                "tick-003-Compare.png",
            ],
        )
        for path in paths:
            with Image.open(path) as image:
                self.assertEqual(image.format, "PNG")
                self.assertGreater(image.width, 100)

    def test_an_svg_value_is_written_beside_the_sheet_unmodified(self):
        run, pxc, preexisting = _one_calc_run(Calculation("fn.spec.svg", emit_svg))
        record = run_record(run, pxc, preexisting=preexisting)
        paths = tick_sheets(record, self.out_dir)
        svg_paths = [path for path in paths if path.endswith(".svg")]
        self.assertEqual([os.path.basename(path) for path in svg_paths], ["tick-000-Only.only.svg"])
        with open(svg_paths[0], encoding="utf-8") as handle:
            self.assertEqual(handle.read(), SVG_DOCUMENT)
        self.assertEqual(len([path for path in paths if path.endswith(".png")]), 1)

    def test_a_png_data_url_that_will_not_decode_degrades_to_its_text_panel(self):
        """Drawing degrades per panel; it never aborts mid-directory.

        RECORD.md:109-110 fixes the `data:image/png;base64,` prefix, not the payload,
        so a truncated or non-PNG payload is a legal record -- adapters.js accepts
        it and the viewer renders it as an <img> without complaint
        (viewer/test/render.test.mjs:218 uses this exact string). An unguarded
        Image.open raised UnidentifiedImageError out of tick_sheets and left a
        half-written ticks/ directory: Tick One's sheet on disk, Tick Two's and
        Tick Three's missing.
        """
        pxc = PxC()
        pcr = PCR("materialize.badpng")
        pcr.calc("One", Calculation("fn.spec.text", emit_text), id="first", into="scratch.spec.a")
        pcr.calc(
            "Two",
            Calculation("fn.spec.badpng", emit_undecodable_png_data_url),
            id="broken",
            into="scratch.spec.b",
        )
        pcr.calc("Three", Calculation("fn.spec.text", emit_text), id="last", into="scratch.spec.c")
        record = run_record(pcr.run(pxc, observe=True), pxc, preexisting=set())
        validate_record(record)
        self.assertEqual(record["ticks"][1]["invocations"][0]["value"]["kind"], "png-data-url")

        paths = tick_sheets(record, self.out_dir)
        self.assertEqual(
            sorted(os.path.basename(path) for path in paths),
            ["tick-000-One.png", "tick-001-Two.png", "tick-002-Three.png"],
        )
        self.assertEqual(sorted(os.listdir(self.out_dir)), sorted(os.path.basename(p) for p in paths))
        for path in paths:
            with Image.open(path) as image:
                self.assertEqual(image.format, "PNG")

    def test_an_image_value_is_drawn_into_the_sheet(self):
        run, pxc, preexisting = _one_calc_run(Calculation("fn.spec.image", emit_image))
        record = run_record(run, pxc, preexisting=preexisting)
        with_image = tick_sheets(record, self.out_dir)
        text_only = tick_sheets(
            run_record(*_one_calc_run(Calculation("fn.spec.text", emit_text))[:2], preexisting=set()),
            os.path.join(self.out_dir, "text"),
        )
        with Image.open(with_image[0]) as drawn, Image.open(text_only[0]) as plain:
            self.assertGreater(drawn.height, plain.height)


class ReadableByTheOtherRuntimesValidator(unittest.TestCase):
    """Every document this producer emits is read back by an independent reader.

    viewer/test/record_schema.py is transcribed from RECORD.md clause by clause,
    independently of both adapters.js and pyto.materialize; the JS reference
    `validate` refuses the same shapes at the same paths (the viewer suite pins
    that). A producer checked only by its own tests is not checked against the
    contract at all -- which is how a receipt-less document went on claiming
    `pyto-run-record@1` while neither reader would take it.
    """

    def test_the_day_one_record_validates(self):
        run, pxc, preexisting = _day_one_run()
        validate_record(run_record(run, pxc, preexisting=preexisting))

    def test_a_record_of_every_value_kind_validates(self):
        bodies = [
            ("fn.spec.text", emit_text, "text"),
            ("fn.spec.svg", emit_svg, "svg"),
            ("fn.spec.set", emit_set, "omitted"),
            ("fn.spec.big", emit_big_text, "omitted"),
            ("fn.spec.long", emit_long_list, "json"),
            ("fn.spec.badpng", emit_undecodable_png_data_url, "png-data-url"),
            ("fn.spec.cycle", emit_cycle, "omitted"),
        ]
        if PILLOW:
            bodies.append(("fn.spec.image", emit_image, "png-data-url"))
        for address, body, kind in bodies:
            with self.subTest(kind=kind, calculation=address):
                run, pxc, preexisting = _one_calc_run(Calculation(address, body))
                record = run_record(run, pxc, preexisting=preexisting)
                self.assertEqual(record["ticks"][0]["invocations"][0]["value"]["kind"], kind)
                validate_record(record)

    def test_the_committed_evidence_record_still_validates(self):
        path = os.path.join(EXPERIMENT_DIR, "evidence", "run-1", "record.json")
        if not os.path.isfile(path):  # pragma: no cover - the evidence is committed
            self.skipTest(f"{path} is not present")
        with open(path, encoding="utf-8") as handle:
            validate_record(json.load(handle))


class CountingJson:
    """`json` with its `dumps` counted, so "serialize once" is a guard and not a note."""

    def __init__(self, module):
        self._json = module
        self.dumps_calls = 0
        self.dump_calls = 0

    def dumps(self, *args, **keywords):
        self.dumps_calls += 1
        return self._json.dumps(*args, **keywords)

    def dump(self, *args, **keywords):
        self.dump_calls += 1
        return self._json.dump(*args, **keywords)

    def __getattr__(self, name):
        return getattr(self._json, name)


class WhatMaterializingCosts(unittest.TestCase):
    """One serialization per value, and no encoding of an image that cannot fit.

    Not a timing test -- nothing here measures a clock. It counts the work: a
    genome's render was dumped to test that it is JSON, copied, dumped again to
    measure it and digested a third time for the receipt, and a 1024x1024 image
    was encoded to PNG, base64'd, measured and thrown away. The counters below are
    what keeps that from coming back; `pyto/scripts/bench_record.py` is what says
    what it was worth in seconds.
    """

    def test_a_json_value_is_serialized_once_in_the_whole_record(self):
        run, pxc, preexisting = _one_calc_run(Calculation("fn.spec.long", emit_long_list))
        counter = CountingJson(materialize_module.json)
        original = materialize_module.json
        materialize_module.json = counter
        try:
            record = run_record(run, pxc, preexisting=preexisting)
        finally:
            materialize_module.json = original
        # One: the dump that measures the rendered value against the cap. The test
        # that the value is JSON at all is the receipt's own digest, which pcr
        # already took over this same object.
        self.assertEqual(counter.dumps_calls, 1)
        self.assertEqual(record["ticks"][0]["invocations"][0]["value"]["kind"], "json")

    def test_a_value_with_no_receipt_digest_is_still_dumped_to_say_why(self):
        """The digest is proof of JSON; the absence of one is not proof of the opposite.

        `pcr._result_sha256` dumps with `sort_keys=True`, which also refuses a dict
        whose keys cannot be compared with one another -- something plain
        `json.dumps` accepts. So a value with no digest still takes the old path:
        it is dumped here, once, and what the dump raises is what the note says.
        """
        run, pxc, preexisting = _one_calc_run(Calculation("fn.spec.set", emit_set))
        self.assertIsNone(run.receipts["only"].result_sha256)
        counter = CountingJson(materialize_module.json)
        original = materialize_module.json
        materialize_module.json = counter
        try:
            record = run_record(run, pxc, preexisting=preexisting)
        finally:
            materialize_module.json = original
        self.assertEqual(counter.dumps_calls, 1)
        value = record["ticks"][0]["invocations"][0]["value"]
        self.assertEqual(value["kind"], "omitted")
        self.assertIn("not JSON-serializable", value["note"])

    @unittest.skipUnless(PILLOW, "Pillow is not installed")
    def test_an_image_that_cannot_fit_the_cap_is_never_encoded_whole(self):
        seen = []
        original = materialize_module._png_data_url

        def spy(image, limit=None):
            seen.append(limit)
            return original(image, limit=limit)

        materialize_module._png_data_url = spy
        try:
            value = render_value(emit_big_noise_image({}))
        finally:
            materialize_module._png_data_url = original
        # Called once, with the PNG budget the cap implies, and it came back with
        # nothing: the encode stopped instead of producing a data URL to discard.
        self.assertEqual(seen, [_png_budget(VALUE_CAP_BYTES)])
        self.assertEqual(value["kind"], "omitted")
        self.assertIsNone(value["data"])

    @unittest.skipUnless(PILLOW, "Pillow is not installed")
    def test_the_encoder_is_stopped_at_the_block_that_passes_the_cap(self):
        image = emit_big_noise_image({})
        whole = io.BytesIO()
        image.save(whole, format="PNG")
        written = []
        original = materialize_module._CappedSink

        class Spy(original):
            def __init__(self, limit):
                super().__init__(limit)
                written.append(self)

        materialize_module._CappedSink = Spy
        try:
            self.assertIsNone(materialize_module._png_data_url(image, limit=_png_budget(VALUE_CAP_BYTES)))
        finally:
            materialize_module._CappedSink = original
        self.assertEqual(len(written), 1)
        sink = written[0]
        self.assertGreater(len(whole.getvalue()), _png_budget(VALUE_CAP_BYTES))
        self.assertLess(sink.size, len(whole.getvalue()))

    @unittest.skipUnless(PILLOW, "Pillow is not installed")
    def test_an_over_cap_image_carries_a_digest_of_its_pixels(self):
        image = emit_big_noise_image({})
        value = render_value(image)
        expected = hashlib.sha256()
        expected.update(f"{image.mode} {image.size[0]}x{image.size[1]} ".encode("utf-8"))
        expected.update(image.tobytes())
        self.assertIn(f"sha256 of the raw pixels = {expected.hexdigest()}", value["note"])
        self.assertIn("over the 262144 byte cap", value["note"])

    @unittest.skipUnless(PILLOW, "Pillow is not installed")
    def test_an_image_that_fits_is_still_a_png_data_url(self):
        """The cheap path decides `omitted`; it does not decide `png-data-url`.

        A small or flat image compresses far under the cap however many pixels it
        has, and it is still encoded and still drawn in the viewer -- which is why
        the budget is the encoder's own output length and not a guess about how
        well an image compresses.
        """
        value = render_value(Image.new("RGB", (512, 512), (9, 9, 9)))
        self.assertEqual(value["kind"], "png-data-url")
        self.assertTrue(value["data"].startswith("data:image/png;base64,"))
        self.assertIsNone(value["note"])

    def test_the_png_budget_is_exactly_what_base64_fits_under_the_cap(self):
        budget = _png_budget(VALUE_CAP_BYTES)
        import base64 as base64_module

        url = "data:image/png;base64," + base64_module.b64encode(b"\0" * budget).decode("ascii")
        self.assertLessEqual(len(url), VALUE_CAP_BYTES)
        one_more = "data:image/png;base64," + base64_module.b64encode(b"\0" * (budget + 1)).decode("ascii")
        self.assertGreater(len(one_more), VALUE_CAP_BYTES)


@unittest.skipUnless(NUMPY, "numpy is not installed")
class ArrayValues(unittest.TestCase):
    """RECORD.md, kind `array`: an array Part is described, digested and kept, not spelled out."""

    def setUp(self):
        self.out_dir = tempfile.mkdtemp(prefix="pyto-array-")
        self.addCleanup(shutil.rmtree, self.out_dir, True)

    def _record(self, body, **keywords):
        run, pxc, preexisting = _one_calc_run(Calculation("fn.spec.array", body))
        record = run_record(run, pxc, preexisting=preexisting, **keywords)
        return run, record, record["ticks"][0]["invocations"][0]["value"]

    def test_an_array_is_its_dtype_shape_digest_and_a_preview(self):
        run, record, value = self._record(emit_array)
        self.assertEqual(value["kind"], "array")
        self.assertEqual(value["data"]["dtype"], "uint8")
        self.assertEqual(value["data"]["shape"], [2, 4, 3])
        self.assertEqual(value["data"]["preview"], list(range(24)))
        self.assertIsNone(value["data"]["path"])
        self.assertIn("24 uint8 value(s), shape (2, 4, 3)", value["note"])
        validate_record(record)

    def test_the_record_and_the_receipt_carry_the_same_digest_taken_once(self):
        run, record, value = self._record(emit_array)
        expected = array_sha256(emit_array({}))
        self.assertEqual(value["data"]["digest"], expected)
        self.assertEqual(run.receipts["only"].result_sha256, expected)
        self.assertEqual(run.receipts["only"].produce_sha256["scratch.spec.value"], expected)

    def test_the_digest_is_of_the_buffer_and_says_dtype_and_shape(self):
        first = numpy.arange(6, dtype="uint8")
        self.assertEqual(array_sha256(first), array_sha256(numpy.arange(6, dtype="uint8")))
        self.assertNotEqual(array_sha256(first), array_sha256(first.reshape(2, 3)))
        self.assertNotEqual(array_sha256(first), array_sha256(first.astype("int8")))
        self.assertIsNone(array_sha256([0, 1, 2, 3, 4, 5]))

    def test_the_raw_bytes_are_written_beside_the_record(self):
        values_dir = os.path.join(self.out_dir, "record.values")
        run, record, value = self._record(emit_array, values_dir=values_dir)
        self.assertEqual(value["data"]["path"], "record.values/scratch.spec.value.bin")
        written = os.path.join(values_dir, "scratch.spec.value.bin")
        with open(written, "rb") as handle:
            self.assertEqual(handle.read(), emit_array({}).tobytes())
        self.assertIn("raw bytes at record.values/scratch.spec.value.bin", value["note"])
        write_record(record, os.path.join(self.out_dir, "record.json"))
        validate_record(record)

    def test_without_a_values_directory_the_bytes_are_not_kept_and_it_says_so(self):
        run, record, value = self._record(emit_array)
        self.assertIn("the raw bytes were not kept", value["note"])
        self.assertEqual(os.listdir(self.out_dir), [])

    def test_the_preview_is_never_longer_than_the_array_cap_the_record_fixes(self):
        """A caller's `array_cap` can lower the preview and cannot raise it.

        The owner's own generation passes `array_cap=250000` so that no render is
        truncated; under the other reading that writes every one of a render's
        196,608 numbers back into the record and the kind buys nothing
        ({?} ArrayPreviewCap).
        """
        run, record, value = self._record(emit_long_array, array_cap=250000)
        self.assertEqual(len(value["data"]["preview"]), ARRAY_CAP)
        self.assertIn(f"preview holds the first {ARRAY_CAP} of 5000", value["note"])
        rendered = render_value(emit_long_array({}), array_cap=5)
        self.assertEqual(rendered["data"]["preview"], [0, 1, 2, 3, 4])

    def test_an_array_over_the_cap_loses_its_preview_and_keeps_its_description(self):
        value = render_value(emit_long_array({}), value_cap_bytes=64)
        self.assertEqual(value["kind"], "array")
        self.assertIsNone(value["data"]["preview"])
        self.assertEqual(value["data"]["shape"], [5000])
        self.assertIsNotNone(value["data"]["digest"])
        self.assertIn("over the 64 byte cap", value["note"])

    def test_a_dtype_that_is_not_json_is_described_without_a_preview(self):
        value = render_value(numpy.zeros(3, dtype="complex128"))
        self.assertEqual(value["kind"], "array")
        self.assertIsNone(value["data"]["preview"])
        self.assertIn("no preview: dtype complex128 does not render as JSON", value["note"])

    def test_an_object_array_is_not_an_array_value(self):
        """Its buffer is a row of pointers, which is the unstable digest pcr refuses."""
        value = render_value(emit_object_array({}))
        self.assertEqual(value["kind"], "omitted")
        self.assertIsNone(array_sha256(emit_object_array({})))


if __name__ == "__main__":
    unittest.main()
