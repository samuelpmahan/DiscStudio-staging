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
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import asdict

from pyto import Calculation, Part, PCR, PxC
from pyto.materialize import SCHEMA, render_value, run_record, tick_sheets, write_record

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

SEED, N = 7, 400  # run.py:main defaults; evidence/run-1/comparison.json records seed 7, n 400

SVG_DOCUMENT = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8">'
    '<rect width="8" height="8" fill="#39ff14"/></svg>'
)

try:  # Pillow is optional for the record; only the sheet tests need it.
    from PIL import Image

    PILLOW = True
except ImportError:  # pragma: no cover - Pillow is installed in this checkout
    PILLOW = False


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


def read_part(args):
    return args["seeded"]


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

    def test_without_observe_the_observed_fields_are_null_not_guessed(self):
        rows = make_data(SEED, N)
        pxc = PxC()
        pxc.set(ROWS, rows)
        pxc.set(GROUPS_PART, GROUPS)
        preexisting = set(pxc.addresses())
        pcr = build_program(select_variants({"groups": GROUPS}))
        record = run_record(pcr.run(pxc), pxc, preexisting=preexisting)
        split = record["ticks"][0]["invocations"][1]
        self.assertIsNone(split["calculation"]["implementation_sha256"])
        self.assertIsNone(split["calculation"]["identity_scope"])
        self.assertIsNone(split["actual_consumes"])
        self.assertIsNone(split["writes"])
        self.assertIsNone(split["duration_ms"])
        self.assertIsNone(split["result_sha256"])
        self.assertIsNone(record["counters"]["wall_ms"])
        # The authored half is still there: address, declared reads, hit, value.
        self.assertEqual(split["calculation"]["address"], "fn.ablation.split")
        self.assertEqual(split["declared_consumes"], ["px:input.ablation.rows"])
        self.assertTrue(split["hit"])
        self.assertEqual(split["value"]["kind"], "json")


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
    """RECORD.md:59-64: json | text | svg | png-data-url | omitted, with the caps."""

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

        RECORD.md:53-56 -- a `px:` binding whose address was not produced by an earlier
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


if __name__ == "__main__":
    unittest.main()
