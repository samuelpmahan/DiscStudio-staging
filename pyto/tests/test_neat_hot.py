"""`neat hot`: the efficiency pass over one run record (pyto/src/pyto/neat/hot.py).

The record under test is built here, in the test, with its durations written
down rather than measured: this suite checks what the pass *says* about a shape,
and a suite that timed anything would be red on a slow machine and green on a
fast one for reasons that are not the code's.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from pyto.neat import hot


def invocation(id: str, calculation: str, duration_ms: float, value: dict,
               inputs: dict | None = None, args: dict | None = None,
               into: str = "px.demo.out", result_sha256: str | None = None) -> dict:
    return {
        "id": id, "calculation": {"address": calculation}, "duration_ms": duration_ms,
        "value": value, "inputs": inputs or {}, "args": args or {}, "into": into,
        "result_sha256": result_sha256 or ("0" * 64), "hit": False, "writes": [{"address": into}],
    }


def record(*invocations: dict, tick: str = "Tick") -> dict:
    return {
        "schema": "pyto-run-record@1", "pcr": "demo",
        "counters": {"invocations": len(invocations), "wall_ms": 1.0},
        "parts": {}, "ticks": [{"name": tick, "invocations": list(invocations)}],
    }


def json_value(data, note: str | None = None) -> dict:
    return {"kind": "json", "data": data, "note": note}


def part_of(document: dict, **knobs) -> dict:
    return hot.evaluate({"measured": hot.measure(document, path="demo.json"), "stem": "demo", **knobs})


def findings(part: dict, name: str) -> list[dict]:
    return [finding for finding in part["findings"] if finding["finding"] == name]


class TheShapeOfAValue(unittest.TestCase):
    def test_a_flat_list_of_numbers_is_its_own_length(self) -> None:
        self.assertEqual(hot.flatten([1, 2, 3]), (3, [3], True))

    def test_a_rectangular_nested_list_is_an_array_written_the_long_way(self) -> None:
        self.assertEqual(hot.flatten([[[1, 2, 3]] * 2] * 4), (24, [4, 2, 3], True))

    def test_a_ragged_list_has_no_shape(self) -> None:
        elements, shape, numeric = hot.flatten([[1, 2], [3]])
        self.assertEqual((elements, shape), (3, None))
        self.assertTrue(numeric)

    def test_a_list_of_flags_is_not_numeric(self) -> None:
        self.assertFalse(hot.flatten([True, False])[2])

    def test_a_truncated_value_is_measured_at_the_length_its_note_carries(self) -> None:
        shape = hot.value_shape(json_value(
            [0] * 200, "1 array(s) truncated to the first 200 entries; original lengths: [196608]"))
        self.assertEqual(shape["elements"], 196608)
        self.assertTrue(shape["truncated"])

    def test_an_omitted_over_cap_value_carries_its_bytes_and_its_cap(self) -> None:
        shape = hot.value_shape({"kind": "omitted", "data": None, "note":
                                 "json value is 900000 bytes, over the 262144 byte cap; sha256 = " + "a" * 64})
        self.assertEqual(shape["over_cap"], {"bytes": 900000, "cap": 262144, "kept": False})


class TheFindings(unittest.TestCase):
    def test_a_dense_list_result_names_the_calculation_and_its_elements(self) -> None:
        part = part_of(record(invocation("a", "fn.demo.tint", 1.0, json_value(list(range(5000))))))
        dense = findings(part, "dense-list")
        self.assertEqual([f["calculation"] for f in dense], ["fn.demo.tint"])
        self.assertEqual(dense[0]["elements"], 5000)
        self.assertIn("would be an array", dense[0]["for"])

    def test_a_list_under_the_threshold_is_not_dense(self) -> None:
        part = part_of(record(invocation("a", "fn.demo.tint", 1.0, json_value(list(range(4096))))))
        self.assertEqual(findings(part, "dense-list"), [])

    def test_per_element_fires_over_the_threshold(self) -> None:
        # 10,000 elements in 2 ms is 200 ns each: written down, not timed.
        part = part_of(record(invocation("a", "fn.demo.tint", 2.0, json_value([1] * 10000))))
        per = findings(part, "per-element")
        self.assertEqual([f["ns_per_element"] for f in per], [200.0])
        self.assertIn("walking them in Python", per[0]["for"])

    def test_per_element_is_quiet_under_the_threshold(self) -> None:
        # 10,000 elements in 0.2 ms is 20 ns each.
        part = part_of(record(invocation("a", "fn.demo.tint", 0.2, json_value([1] * 10000))))
        self.assertEqual(findings(part, "per-element"), [])

    def test_a_small_list_never_trips_per_element_however_slow(self) -> None:
        part = part_of(record(invocation("a", "fn.demo.select", 50.0, json_value([1] * 16))))
        self.assertEqual(findings(part, "per-element"), [])

    def test_a_receipt_that_returns_a_dict_is_measured_on_what_it_read(self) -> None:
        """fitness returned six keys and still walked 10,000 pixels."""
        part = part_of(record(
            invocation("render", "fn.demo.render", 1.0, json_value([1] * 10000), into="px.demo.rgb"),
            invocation("fitness", "fn.demo.fitness", 2.0, json_value({"valid": True}),
                       inputs={"rgb": "fn:render"}, into="px.demo.fitness"),
        ))
        per = {f["calculation"]: f["ns_per_element"] for f in findings(part, "per-element")}
        self.assertEqual(per["fn.demo.fitness"], 200.0)

    def test_over_cap_reports_an_omitted_value_with_its_size(self) -> None:
        part = part_of(record(invocation("a", "fn.demo.render", 1.0, {
            "kind": "omitted", "data": None,
            "note": "json value is 900000 bytes, over the 262144 byte cap; sha256 = " + "b" * 64})))
        over = findings(part, "over-cap")
        self.assertEqual([f["bytes"] for f in over], [900000])
        self.assertFalse(over[0]["kept"])
        self.assertIn("the record kept a note, not the value", over[0]["for"])

    def test_over_cap_also_reports_the_value_a_raised_cap_kept(self) -> None:
        part = part_of(record(invocation("a", "fn.demo.render", 1.0, json_value(list(range(100000))))))
        over = findings(part, "over-cap")
        self.assertTrue(over[0]["kept"])
        self.assertGreater(over[0]["total_bytes"], hot.CAP_BYTES)
        self.assertIn("because the run raised the cap", over[0]["for"])

    def test_repeat_input_counts_receipts_with_the_same_inputs(self) -> None:
        rows = [
            invocation("source", "fn.demo.load", 1.0, json_value({"seed": 1}), into="px.demo.input"),
            *[invocation(f"tint_{n}", "fn.demo.tint", 1.0, json_value([1] * 16),
                         inputs={"spec": "fn:source"}, into=f"px.demo.tint.{n}") for n in (1, 2, 3)],
        ]
        part = part_of(record(*rows))
        repeat = findings(part, "repeat-input")
        self.assertEqual([f["calculation"] for f in repeat], ["fn.demo.tint"])
        self.assertEqual((repeat[0]["invocations"], repeat[0]["repeats"]), (3, 1))
        self.assertIn("a cache that isn't there", repeat[0]["for"])

    def test_args_make_two_receipts_different_inputs(self) -> None:
        """bind reads one population thirty-two times and is told a different index each time."""
        rows = [
            invocation("source", "fn.demo.load", 1.0, json_value({"seed": 1}), into="px.demo.input"),
            *[invocation(f"bind_{n}", "fn.demo.bind", 1.0, json_value({"n": n}),
                         inputs={"input": "fn:source"}, args={"index": n}, into=f"px.demo.spec.{n}")
              for n in (1, 2, 3)],
        ]
        self.assertEqual(findings(part_of(record(*rows)), "repeat-input"), [])

    def test_hot_is_the_top_three_by_total_duration_and_is_always_said(self) -> None:
        rows = [invocation(name, f"fn.demo.{name}", ms, json_value({"ok": True}))
                for name, ms in (("a", 4.0), ("b", 3.0), ("c", 2.0), ("d", 1.0))]
        part = part_of(record(*rows))
        self.assertEqual([f["calculation"] for f in findings(part, "hot")],
                         ["fn.demo.a", "fn.demo.b", "fn.demo.c"])
        self.assertTrue(part["quiet"])
        self.assertIn("fix here first", findings(part, "hot")[0]["for"])

    def test_a_record_with_nothing_to_fix_says_only_hot(self) -> None:
        part = part_of(record(invocation("a", "fn.demo.tint", 1.0, {
            "kind": "omitted", "data": None, "note": "not JSON-serializable (ndarray: ...)"})))
        self.assertEqual([f["finding"] for f in part["findings"]], ["hot"])
        self.assertTrue(part["quiet"])


class ThePartAndTheTable(unittest.TestCase):
    def test_the_part_is_published_through_a_pcr_with_its_own_record(self) -> None:
        document = record(invocation("a", "fn.demo.tint", 2.0, json_value([1] * 10000)))
        with tempfile.TemporaryDirectory() as where:
            path = os.path.join(where, "demo.record.json")
            part = hot.run_hot(hot.measure(document, path="demo.json"), "demo", path)
            with open(path, encoding="utf-8") as handle:
                receipt = json.load(handle)
        self.assertEqual(part["address"], "px.exp.neat.hot.demo")
        self.assertEqual(receipt["schema"], "pyto-run-record@1")
        self.assertEqual(
            [inv["calculation"]["address"] for tick in receipt["ticks"] for inv in tick["invocations"]],
            ["fn.neat.hot.evaluate"],
        )

    def test_the_pass_reads_the_record_and_nothing_else(self) -> None:
        """Same document, same Part: the findings are a function of the record."""
        document = record(invocation("a", "fn.demo.tint", 2.0, json_value([1] * 10000)))
        self.assertEqual(part_of(document), part_of(json.loads(json.dumps(document))))

    def test_the_table_names_every_finding_and_the_record(self) -> None:
        part = part_of(record(invocation("a", "fn.demo.tint", 2.0, json_value([1] * 10000))))
        drawn = hot.table(part)
        self.assertIn("fn.demo.tint", drawn)
        for finding in part["findings"]:
            self.assertIn(finding["for"], drawn)

    def test_the_stem_is_the_address(self) -> None:
        self.assertEqual(hot.stem_of("observed/record.json"), "record")
        self.assertEqual(hot.stem_of("x.json", "evo dense"), "evo-dense")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
