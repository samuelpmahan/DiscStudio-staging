"""`neat equiv`: the trust path (pyto/src/pyto/neat/equiv.py).

The canonical rule gets the most of this suite, because the whole trust rests on
it: if two different values ever canonicalize to the same bytes, a witness says
`trusted: true` about a candidate that is wrong. The array here is duck-typed and
built in the test -- the rule must hold without numpy, which the kernel does not
import.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from pyto.neat import equiv


class Dtype:
    def __init__(self, itemsize: int, kind: str) -> None:
        self.itemsize, self.kind = itemsize, kind


class Array:
    """The smallest thing that quacks like an ndarray: bytes, a dtype and a shape."""

    def __init__(self, data: bytes, shape: tuple[int, ...], kind: str = "u", itemsize: int = 1) -> None:
        self._data, self.shape, self.dtype = bytes(data), shape, Dtype(itemsize, kind)

    def tobytes(self) -> bytes:
        return self._data

    def tolist(self) -> list:
        return list(self._data)


def invocation(id: str, calculation: str, value: dict, inputs: dict | None = None,
               args: dict | None = None, into: str = "px.demo.out") -> dict:
    return {
        "id": id, "calculation": {"address": calculation}, "duration_ms": 1.0, "value": value,
        "inputs": inputs or {}, "args": args or {}, "into": into, "hit": False,
        "result_sha256": "0" * 64, "writes": [{"address": into}],
    }


def record(*invocations: dict) -> dict:
    return {"schema": "pyto-run-record@1", "pcr": "demo", "counters": {}, "parts": {},
            "ticks": [{"name": "Tick", "invocations": list(invocations)}]}


def json_value(data, note: str | None = None) -> dict:
    return {"kind": "json", "data": data, "note": note}


class TheCanonicalRule(unittest.TestCase):
    """The same values, not the same Python object."""

    def test_a_byte_array_and_the_list_of_ints_it_holds_are_one_value(self) -> None:
        self.assertEqual(equiv.canonical(Array(bytes([0, 1, 255]), (3,))), equiv.canonical([0, 1, 255]))

    def test_a_shaped_array_and_the_flat_list_are_one_value(self) -> None:
        """The shape is deliberately not in the bytes: the pixels are the pixels."""
        flat = [1, 2, 3, 4, 5, 6]
        self.assertEqual(equiv.canonical(Array(bytes(flat), (2, 3))), equiv.canonical(flat))

    def test_a_rectangular_nested_list_and_the_flat_one_are_one_value(self) -> None:
        self.assertEqual(equiv.canonical([[1, 2, 3], [4, 5, 6]]), equiv.canonical([1, 2, 3, 4, 5, 6]))

    def test_bytes_are_the_same_value_too(self) -> None:
        self.assertEqual(equiv.canonical(b"\x00\x01\xff")[0], equiv.canonical([0, 1, 255])[0])

    def test_the_byte_path_says_how_it_answered(self) -> None:
        self.assertEqual(equiv.canonical([0, 1, 255])[1], "bytes")
        self.assertEqual(equiv.canonical({"a": 1})[1], "json")

    def test_different_pixels_are_different_bytes(self) -> None:
        self.assertNotEqual(equiv.canonical([1, 2, 3]), equiv.canonical([1, 2, 4]))

    def test_a_ragged_list_is_not_an_array(self) -> None:
        self.assertEqual(equiv.canonical([[1, 2], [3]])[1], "json")

    def test_a_number_outside_a_byte_takes_the_json_path(self) -> None:
        self.assertEqual(equiv.canonical([0, 256])[1], "json")
        self.assertEqual(equiv.canonical([0.5, 1.5])[1], "json")

    def test_flags_are_not_pixels(self) -> None:
        """True is an int in Python; a list of flags must not canonicalize as bytes."""
        self.assertEqual(equiv.canonical([True, False])[1], "json")
        self.assertNotEqual(equiv.canonical([True, False]), equiv.canonical([1, 0]))

    def test_an_array_of_another_dtype_goes_through_its_values(self) -> None:
        wide = Array(bytes([1, 2]), (2,), kind="f", itemsize=8)
        self.assertEqual(equiv.canonical(wide), equiv.canonical_json([1, 2]))

    def test_the_two_paths_can_never_collide(self) -> None:
        """A JSON payload that happens to read like bytes is still a different value."""
        self.assertNotEqual(equiv.canonical("\x00\x01")[0], equiv.canonical([0, 1])[0])

    def test_the_json_path_is_the_bytes_the_record_digests(self) -> None:
        self.assertEqual(equiv.json_payload_sha({"b": 1, "a": 2}),
                         equiv.json_payload_sha({"a": 2, "b": 1}))


class RebuildingTheInputs(unittest.TestCase):
    def test_an_input_bound_to_a_sibling_is_that_receipt_s_recorded_value(self) -> None:
        document = record(
            invocation("spec", "fn.demo.bind", json_value({"gain": 2}), into="px.demo.spec"),
            invocation("tint", "fn.demo.tint", json_value([2, 4]), inputs={"spec": "fn:spec"}),
        )
        by_id, writer = equiv.index(document)
        call, refusals, from_store = equiv.rebuild(by_id["tint"], by_id, writer, {})
        self.assertEqual((call, refusals, from_store), ({"spec": {"gain": 2}}, [], False))

    def test_args_are_handed_to_the_candidate_beside_the_inputs(self) -> None:
        document = record(invocation("bind", "fn.demo.bind", json_value({}), args={"index": 3}))
        by_id, writer = equiv.index(document)
        call, _, _ = equiv.rebuild(by_id["bind"], by_id, writer, {})
        self.assertEqual(call, {"index": 3})

    def test_an_input_bound_to_a_part_the_record_does_not_carry_comes_from_the_store(self) -> None:
        document = record(invocation("tint", "fn.demo.tint", json_value([1]), inputs={"field": "px:px.demo.field"}))
        by_id, writer = equiv.index(document)
        call, refusals, from_store = equiv.rebuild(by_id["tint"], by_id, writer, {"px.demo.field": [7]})
        self.assertEqual((call, refusals, from_store), ({"field": [7]}, [], True))

    def test_an_input_that_is_nowhere_is_a_refusal_naming_what_was_needed(self) -> None:
        document = record(invocation("tint", "fn.demo.tint", json_value([1]), inputs={"field": "px:px.demo.field"}))
        by_id, writer = equiv.index(document)
        _, refusals, _ = equiv.rebuild(by_id["tint"], by_id, writer, {})
        self.assertEqual(refusals[0]["input"], "field")
        self.assertEqual(refusals[0]["needed"], "px.demo.field")
        self.assertIn("--store does not hold px.demo.field", refusals[0]["had"])

    def test_a_truncated_sibling_value_is_not_believed(self) -> None:
        document = record(
            invocation("field", "fn.demo.field", json_value(
                [0] * 200, "1 array(s) truncated to the first 200 entries; original lengths: [20000]"),
                into="px.demo.field"),
            invocation("tint", "fn.demo.tint", json_value([1]), inputs={"field": "fn:field"}),
        )
        by_id, writer = equiv.index(document)
        _, refusals, _ = equiv.rebuild(by_id["tint"], by_id, writer, {})
        self.assertIn("truncated", refusals[0]["had"])


class TheWitness(unittest.TestCase):
    def dense(self) -> dict:
        """One receipt per genome: a spec in, a list of pixels out."""
        rows = []
        for n in (1, 2):
            rows.append(invocation(f"bind_{n}", "fn.demo.bind", json_value({"gain": n}), into=f"px.demo.spec.{n}"))
            rows.append(invocation(f"tint_{n}", "fn.demo.tint", json_value([n, n * 2, n * 3]),
                                   inputs={"spec": f"fn:bind_{n}"}, into=f"px.demo.tint.{n}"))
        return record(*rows)

    @staticmethod
    def sparse(args):
        gain = args["spec"]["gain"]
        return Array(bytes([gain, gain * 2, gain * 3]), (3,))

    @staticmethod
    def wrong(args):
        gain = args["spec"]["gain"]
        return Array(bytes([gain * 3, gain * 2, gain]), (3,))

    @staticmethod
    def raises(args):
        raise ValueError("no such palette")

    def witness(self, candidate) -> dict:
        checked = equiv.check(self.dense(), "fn.demo.tint", candidate, record_path="demo.json")
        return equiv.judge({**checked, "candidate": equiv.describe(candidate)})

    def test_an_array_candidate_that_reproduces_every_receipt_is_trusted(self) -> None:
        part = self.witness(self.sparse)
        self.assertTrue(part["trusted"])
        self.assertEqual(part["counts"], {"receipts": 2, "matched": 2, "mismatched": 0, "not_rebuildable": 0})
        self.assertEqual(part["rows"], [])
        self.assertIn("2/2 receipts of fn.demo.tint reproduced by", part["reason"])

    def test_a_wrong_candidate_is_every_receipt_a_row(self) -> None:
        part = self.witness(self.wrong)
        self.assertFalse(part["trusted"])
        self.assertEqual(part["counts"]["matched"], 0)
        self.assertEqual([row["id"] for row in part["rows"]], ["tint_1", "tint_2"])
        self.assertEqual(part["rows"][0]["via"], "canonical bytes")
        self.assertNotEqual(part["rows"][0]["expected"], part["rows"][0]["actual"])

    def test_a_candidate_that_raises_is_a_row_and_not_a_crash(self) -> None:
        part = self.witness(self.raises)
        self.assertFalse(part["trusted"])
        self.assertIn("ValueError: no such palette", part["rows"][0]["reason"])

    def test_a_receipt_that_cannot_be_rebuilt_is_never_counted_as_matched(self) -> None:
        document = record(invocation("tint", "fn.demo.tint", json_value([1, 2, 3]),
                                     inputs={"field": "px:px.demo.field"}))
        checked = equiv.check(document, "fn.demo.tint", self.sparse)
        part = equiv.judge({**checked, "candidate": equiv.describe(self.sparse)})
        self.assertFalse(part["trusted"])
        self.assertEqual(part["counts"]["not_rebuildable"], 1)
        self.assertEqual(part["rows"][0]["state"], "not-rebuildable")
        self.assertIn("needed px.demo.field", part["rows"][0]["reason"])

    def test_no_receipt_of_that_calculation_is_not_a_witness(self) -> None:
        checked = equiv.check(self.dense(), "fn.demo.nothing", self.sparse)
        part = equiv.judge({**checked, "candidate": equiv.describe(self.sparse)})
        self.assertFalse(part["trusted"])
        self.assertIn("nothing was compared", part["reason"])

    def test_an_over_cap_result_is_compared_against_the_sha_in_its_note(self) -> None:
        payload = json.dumps([1, 2, 3], sort_keys=True, separators=(",", ":"))
        sha = equiv.hashlib.sha256(payload.encode("utf-8")).hexdigest()
        document = record(
            invocation("bind", "fn.demo.bind", json_value({"gain": 1}), into="px.demo.spec"),
            invocation("tint", "fn.demo.tint",
                       {"kind": "omitted", "data": None,
                        "note": f"json value is 900000 bytes, over the 262144 byte cap; sha256 = {sha}"},
                       inputs={"spec": "fn:bind"}),
        )
        checked = equiv.check(document, "fn.demo.tint", self.sparse)
        part = equiv.judge({**checked, "candidate": equiv.describe(self.sparse)})
        self.assertTrue(part["trusted"], part["reason"])
        row = equiv.check(document, "fn.demo.tint", self.sparse)["rows"][0]
        self.assertIn("over-cap note", row["via"])

    def test_an_omitted_result_with_no_digest_is_not_comparable(self) -> None:
        document = record(
            invocation("bind", "fn.demo.bind", json_value({"gain": 1}), into="px.demo.spec"),
            invocation("tint", "fn.demo.tint",
                       {"kind": "omitted", "data": None, "note": "not JSON-serializable (ndarray: ...)"},
                       inputs={"spec": "fn:bind"}),
        )
        checked = equiv.check(document, "fn.demo.tint", self.sparse)
        part = equiv.judge({**checked, "candidate": equiv.describe(self.sparse)})
        self.assertFalse(part["trusted"])
        self.assertEqual(part["counts"]["not_rebuildable"], 1)
        self.assertEqual(part["rows"][0]["state"], "not-comparable")

    def test_the_witness_names_the_candidate_and_its_implementation_sha(self) -> None:
        part = self.witness(self.sparse)
        sha = equiv.describe(self.sparse)["implementation_sha256"]
        self.assertEqual(len(sha), 64)
        self.assertEqual(part["address"], f"px.exp.neat.equiv.fn.demo.tint.{sha[:8]}")
        self.assertEqual(part["candidate"]["function"], "TheWitness.sparse")

    def test_the_witness_is_published_through_a_pcr_with_its_own_record(self) -> None:
        checked = equiv.check(self.dense(), "fn.demo.tint", self.sparse, record_path="demo.json")
        candidate = equiv.describe(self.sparse)
        with tempfile.TemporaryDirectory() as where:
            path = os.path.join(where, "witness.record.json")
            part = equiv.run_equiv(checked, candidate, path)
            with open(path, encoding="utf-8") as handle:
                receipt = json.load(handle)
        self.assertTrue(part["trusted"])
        self.assertEqual(
            [inv["calculation"]["address"] for tick in receipt["ticks"] for inv in tick["invocations"]],
            ["fn.neat.equiv.judge"],
        )

    def test_the_table_says_what_was_matched_and_whether_it_is_trusted(self) -> None:
        drawn = equiv.table(self.witness(self.wrong))
        self.assertIn("matched 0/2", drawn)
        self.assertIn("trusted: false", drawn)
        self.assertIn("tint_1", drawn)

    def test_the_store_is_only_named_as_used_when_it_supplied_something(self) -> None:
        self.assertFalse(equiv.check(self.dense(), "fn.demo.tint", self.sparse)["store_used"])
        document = record(invocation("tint", "fn.demo.tint", json_value([1, 2, 3]),
                                     inputs={"spec": "px:px.demo.spec"}))
        checked = equiv.check(document, "fn.demo.tint", self.sparse, store={"px.demo.spec": {"gain": 1}})
        self.assertTrue(checked["store_used"])
        self.assertEqual(checked["rows"][0]["state"], "match")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
