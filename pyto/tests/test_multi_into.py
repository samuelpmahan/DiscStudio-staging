"""Executable spec of multi-produce Calculations: one pass, several Parts, one receipt.

The decision this pins is the owner's, 2026-09-10, closing `{?} WhatIsATick` in
pyto/questions.md: "Obviously a Calculation can produce multiple parts." Until
then `calc(..., into=)` took one address, which the session had promoted to the
rule "a Calculation has one result"; the record contract never said so
(`actual_produces` and `writes` were lists from Day 1), and the store-level
sharing the question was really about (two Calculations reading one roster) was
never the constraint.

What is asserted here, claim by claim:

- `into=[a, b]` publishes one Part per address from one invocation, in the order
  given, and the Calculation says which is which by returning a mapping keyed by
  the addresses or a sequence in that order (`pcr.py` `_split_produces`);
- one receipt lists every produce, one write per address with its kind, and one
  digest per produce beside the whole-result digest (`Receipt.produce_sha256`);
- a reference to such an invocation names the produce it means -- `ref[address]`
  or `ref.part(address)` -- and a bare reference is refused with the addresses in
  the message, at bind time and at resolve time;
- the testimony bytes consumers embed are the same with observe on or off, as
  they have to be for every seam here (tests/test_receipts.py);
- a one-address call is byte for byte what it was before this change: its record
  is identical and its receipt differs only by the added `produce_sha256`, pinned
  against `fixtures/single_into_pre_change.json`, which was generated from the
  commit before it.

Every Calculation body is a named module-level function; no lambdas
(experiments/CAPTURE.md, rule 2).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import unittest
from dataclasses import asdict

from pyto import Calculation, PCR, Part, PxC, PxWrite
from pyto.materialize import run_record
from pyto.pcr import ResultRef

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if TESTS_DIR not in sys.path:
    print(f"[tests/test_multi_into] sys.path.insert(0, {TESTS_DIR!r})", file=sys.stderr)
    sys.path.insert(0, TESTS_DIR)

import fixture_single_into  # noqa: E402  the one-address program the fixture pins

FIXTURE = os.path.join(TESTS_DIR, "fixtures", "single_into_pre_change.json")


# --- module-level calculation bodies (named functions only) --------------------


def split_stats(args):
    """Two Parts from one pass over one input: the shape the owner asked for."""
    rows = args["rows"]
    return {"out.mean": sum(rows) / len(rows), "out.count": len(rows)}


def split_pair(args):
    """The same two values as a sequence, in the declared order."""
    rows = args["rows"]
    return [sum(rows) / len(rows), len(rows)]


def take_value(args):
    return args["value"]


def wrong_keys(args):
    return {"out.mean": 1, "out.elsewhere": 2}


def missing_key(args):
    return {"out.mean": 1}


def extra_key(args):
    return {"out.mean": 1, "out.count": 2, "out.spare": 3}


def short_sequence(args):
    return [1]


def not_a_container(args):
    return 7


def opaque_pair(args):
    """A pair whose second value has no canonical JSON form (a set: gap 10)."""
    return {"out.mean": 2.0, "out.tags": {"a", "b"}}


SPLIT_STATS = Calculation("fn.multi.splitStats", split_stats)
SPLIT_PAIR = Calculation("fn.multi.splitPair", split_pair)
TAKE_VALUE = Calculation("fn.multi.takeValue", take_value)
WRONG_KEYS = Calculation("fn.multi.wrongKeys", wrong_keys)
MISSING_KEY = Calculation("fn.multi.missingKey", missing_key)
EXTRA_KEY = Calculation("fn.multi.extraKey", extra_key)
SHORT_SEQUENCE = Calculation("fn.multi.shortSequence", short_sequence)
NOT_A_CONTAINER = Calculation("fn.multi.notAContainer", not_a_container)
OPAQUE_PAIR = Calculation("fn.multi.opaquePair", opaque_pair)

PRODUCES = ["out.mean", "out.count"]


def canonical_sha256(value) -> str:
    """The digest the seam must produce (tests/test_receipts.py:canonical_sha256)."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def two_output_program(calculation=SPLIT_STATS, produces=None):
    """`stats` publishes two Parts; `report` reads one of them by name."""
    pxc = PxC()
    pxc.set(Part("in.rows"), [1, 2, 3, 4])
    pcr = PCR("multi")
    stats = pcr.calc(
        "Prepare", calculation, id="stats", rows=Part("in.rows"),
        into=PRODUCES if produces is None else produces,
    )
    pcr.calc("Report", TAKE_VALUE, id="report", value=stats["out.count"], into="out.reported")
    return pcr, pxc, stats


class TwoPartsFromOnePass(unittest.TestCase):
    """One invocation, two Parts, in the order the program declared."""

    def test_both_parts_are_published_with_their_own_values(self):
        """pcr.py PCR.run: `for part, part_value in zip(produce_parts, produced_values)`.

        Mutation: publish `value` at every address (the pre-change `board.set(into,
        value)` applied in a loop) -- both Parts hold the whole mapping and the two
        assertions below fail.
        """
        pcr, pxc, _ = two_output_program()
        pcr.run(pxc)
        self.assertEqual(pxc.get(Part("out.mean")), 2.5)
        self.assertEqual(pxc.get(Part("out.count")), 4)

    def test_a_sequence_return_is_read_in_the_declared_order(self):
        """pcr.py `_split_produces`: a sequence is positional, in `into` order.

        Mutation: `return tuple(reversed(value))` -- out.mean holds 4 and out.count
        holds 2.5, which is what the ordering claim exists to catch.
        """
        pcr, pxc, _ = two_output_program(SPLIT_PAIR)
        pcr.run(pxc)
        self.assertEqual(pxc.get(Part("out.mean")), 2.5)
        self.assertEqual(pxc.get(Part("out.count")), 4)

    def test_a_mapping_return_is_read_by_address_not_by_position(self):
        """pcr.py `_split_produces`: `value[address]`, so a mapping in another order
        still lands correctly.

        Mutation: `tuple(value.values())` -- the reversed mapping below publishes the
        count as the mean.
        """
        pxc = PxC()
        pxc.set(Part("in.rows"), [1, 2, 3, 4])
        pcr = PCR("by-key")
        pcr.calc("T", REVERSED_KEYS, id="stats", rows=Part("in.rows"), into=PRODUCES)
        pcr.run(pxc)
        self.assertEqual(pxc.get(Part("out.mean")), 2.5)
        self.assertEqual(pxc.get(Part("out.count")), 4)

    def test_the_whole_returned_value_is_still_the_invocation_result(self):
        """`results[id]` is what the Calculation returned, so the record's `value`
        block and `result_sha256` keep their meaning for a multi-produce invocation.
        """
        pcr, pxc, _ = two_output_program()
        run = pcr.run(pxc, observe=True)
        self.assertEqual(run.results["stats"], {"out.mean": 2.5, "out.count": 4})
        self.assertEqual(
            run.receipts["stats"].result_sha256,
            canonical_sha256({"out.mean": 2.5, "out.count": 4}),
        )

    def test_one_invocation_files_one_receipt(self):
        """Several Parts, one pass, one receipt: the point of the decision."""
        pcr, pxc, _ = two_output_program()
        run = pcr.run(pxc, observe=True)
        self.assertEqual(sorted(run.receipts), ["report", "stats"])
        self.assertEqual(
            [a for a in pxc.addresses() if a.startswith("px.receipt.")],
            ["px.receipt.multi.Prepare.stats", "px.receipt.multi.Report.report"],
        )


def reversed_keys(args):
    rows = args["rows"]
    return {"out.count": len(rows), "out.mean": sum(rows) / len(rows)}


REVERSED_KEYS = Calculation("fn.multi.reversedKeys", reversed_keys)


class OneReceiptEveryProduce(unittest.TestCase):
    """The receipt lists every address, every write, and one digest per produce."""

    def receipt(self):
        pcr, pxc, _ = two_output_program()
        return pcr.run(pxc, observe=True).receipts["stats"]

    def test_declared_and_actual_produces_list_every_address(self):
        """pcr.py: `declared_produces=produce_addresses` (was `(into.address,)`).

        Mutation: `declared_produces=produce_addresses[:1]` -- the receipt claims one
        Part where the store holds two.
        """
        receipt = self.receipt()
        self.assertEqual(receipt.declared_produces, ("out.mean", "out.count"))
        self.assertEqual(receipt.actual_produces, ("out.mean", "out.count"))

    def test_writes_carry_one_entry_per_address_with_its_kind(self):
        """_TrackedPxC.set is called once per address, so `writes` is per Part and
        each kind is decided against the store as it stood at that moment.
        """
        pxc = PxC()
        pxc.set(Part("in.rows"), [1, 2, 3, 4])
        pxc.set(Part("out.count"), 0)  # already there, and not bound -> replacement
        pcr = PCR("kinds")
        pcr.calc("T", SPLIT_STATS, id="stats", rows=Part("in.rows"), into=PRODUCES)
        receipt = pcr.run(pxc, observe=True).receipts["stats"]
        self.assertEqual(
            receipt.writes,
            (PxWrite("out.mean", "new-address"), PxWrite("out.count", "replacement")),
        )

    def test_one_digest_per_produce_beside_the_whole_result_digest(self):
        """pcr.py: `produce_sha256={address: _result_sha256(part_value)}`.

        Mutation: digest `value` instead of `part_value` -- every produce reports the
        digest of the whole mapping and the two distinct digests below collapse.
        """
        receipt = self.receipt()
        self.assertEqual(
            receipt.produce_sha256,
            {"out.mean": canonical_sha256(2.5), "out.count": canonical_sha256(4)},
        )
        self.assertEqual(list(receipt.produce_sha256), ["out.mean", "out.count"])
        self.assertNotIn(receipt.result_sha256, receipt.produce_sha256.values())

    def test_a_produce_without_a_canonical_json_form_has_no_digest(self):
        """`_result_sha256` per produce, so gap 10 holds per Part: a set has no digest
        rather than a process-dependent one, and its sibling still has its own.
        """
        pxc = PxC()
        pxc.set(Part("in.rows"), [1, 2])
        pcr = PCR("opaque")
        pcr.calc("T", OPAQUE_PAIR, id="pair", rows=Part("in.rows"), into=["out.mean", "out.tags"])
        receipt = pcr.run(pxc, observe=True).receipts["pair"]
        self.assertEqual(receipt.produce_sha256["out.mean"], canonical_sha256(2.0))
        self.assertIsNone(receipt.produce_sha256["out.tags"])
        self.assertIsNone(receipt.result_sha256)  # the whole mapping is not JSON either

    def test_a_one_address_invocation_digests_its_one_produce(self):
        """The compatibility half of the digest decision: `result_sha256` unchanged,
        `produce_sha256` = {into: result_sha256}.
        """
        pxc = PxC()
        pxc.set(Part("in.v"), 3)
        pcr = PCR("single")
        pcr.calc("T", TAKE_VALUE, id="take", value=Part("in.v"), into="out.v")
        receipt = pcr.run(pxc, observe=True).receipts["take"]
        self.assertEqual(receipt.result_sha256, canonical_sha256(3))
        self.assertEqual(receipt.produce_sha256, {"out.v": canonical_sha256(3)})

    def test_an_invocation_without_into_has_no_produce_digests(self):
        pcr = PCR("none")
        pcr.calc("T", NOT_A_CONTAINER, id="seven")
        receipt = pcr.run(PxC(), observe=True).receipts["seven"]
        self.assertEqual(receipt.declared_produces, ())
        self.assertEqual(receipt.produce_sha256, {})
        self.assertEqual(receipt.writes, ())


class ReferencesNameTheProduce(unittest.TestCase):
    """A ResultRef to a multi-produce invocation says which Part it means."""

    def test_ref_by_address_reads_that_part(self):
        """pcr.py PCR.run: `resolved_inputs[name] = available[source.produce]`.

        Mutation: resolve every ref to `results[id]` (the whole mapping) -- `report`
        receives {'out.mean': 2.5, 'out.count': 4} instead of 4.
        """
        pcr, pxc, _ = two_output_program()
        run = pcr.run(pxc, observe=True)
        self.assertEqual(run.results["report"], 4)
        self.assertEqual(pxc.get(Part("out.reported")), 4)

    def test_ref_part_is_the_same_reference_as_item_access(self):
        ref = ResultRef("stats")
        self.assertEqual(ref["out.count"], ResultRef("stats", "out.count"))
        self.assertEqual(ref.part(Part("out.count")), ResultRef("stats", "out.count"))
        self.assertIsNone(ref.produce)

    def test_the_testimony_and_the_record_show_the_resolved_read(self):
        """`_ref_spelling`: a produce-qualified binding is `fn:<id>#<address>`, and
        materialize resolves it back to that one address in the part index.

        Mutation: `_ref_spelling` returning `fn:{calculation_id}` always -- the record
        below says `fn:stats` and the part index credits `report` with reading
        out.mean as well, which is a read the program never declared.
        """
        pcr, pxc, _ = two_output_program()
        run = pcr.run(pxc, observe=True)
        report = [
            calc
            for tick in run.ticks
            for calc in tick.calculations
            if calc.id == "report"
        ][0]
        self.assertEqual(report.inputs, {"value": "fn:stats#out.count"})
        record = run_record(run, pxc, preexisting={"in.rows"})
        invocation = record["ticks"][1]["invocations"][0]
        self.assertEqual(invocation["inputs"], {"value": "fn:stats#out.count"})
        self.assertEqual(invocation["declared_consumes"], [])  # a result read, not a store read
        self.assertEqual(record["parts"]["out.count"]["read_by"], ["report"])
        self.assertEqual(record["parts"]["out.mean"]["read_by"], [])
        self.assertEqual(record["parts"]["out.count"]["written_by"], "stats")

    def test_the_record_carries_every_produce(self):
        """materialize.py: `into` is a list for a multi-produce invocation, and
        actual_produces and writes -- lists already -- carry both addresses.
        """
        pcr, pxc, _ = two_output_program()
        record = run_record(pcr.run(pxc, observe=True), pxc, preexisting={"in.rows"})
        stats = record["ticks"][0]["invocations"][0]
        self.assertEqual(stats["into"], ["out.mean", "out.count"])
        self.assertEqual(stats["actual_produces"], ["out.mean", "out.count"])
        self.assertEqual(
            stats["writes"],
            [
                {"address": "out.mean", "kind": "new-address"},
                {"address": "out.count", "kind": "new-address"},
            ],
        )
        self.assertEqual(json.loads(json.dumps(stats["into"])), ["out.mean", "out.count"])

    def test_a_part_binding_on_a_produced_address_resolves_to_that_produce(self):
        """PCR.calc rewrites a Part already written by this PCR into its writer's
        ResultRef; when the writer publishes several, the address the program wrote
        is exactly which produce it meant.

        Mutation: `ResultRef(writer)` with no produce -- binding `Part("out.mean")`
        raises as a bare reference instead of resolving.
        """
        pxc = PxC()
        pxc.set(Part("in.rows"), [1, 2, 3, 4])
        pcr = PCR("rewrite")
        pcr.calc("T", SPLIT_STATS, id="stats", rows=Part("in.rows"), into=PRODUCES)
        pcr.calc("U", TAKE_VALUE, id="reader", value=Part("out.mean"), into="out.copy")
        run = pcr.run(pxc, observe=True)
        self.assertEqual(run.results["reader"], 2.5)
        reader = run.ticks[1].calculations[0]
        self.assertEqual(reader.inputs, {"value": "fn:stats#out.mean"})
        self.assertEqual(run.receipts["reader"].declared_consumes, ())

    def test_a_bare_ref_to_a_multi_produce_invocation_is_refused_at_bind_time(self):
        """pcr.py `_refuse_bare_multi_ref`, called from PCR.calc.

        Mutation: drop the `source.produce is None` branch in PCR.calc -- the program
        below binds a mapping nobody asked for and the failure moves to whatever the
        Calculation does with it.
        """
        pxc = PxC()
        pxc.set(Part("in.rows"), [1, 2, 3, 4])
        pcr = PCR("bare")
        stats = pcr.calc("T", SPLIT_STATS, id="stats", rows=Part("in.rows"), into=PRODUCES)
        with self.assertRaises(ValueError) as caught:
            pcr.calc("U", TAKE_VALUE, id="reader", value=stats, into="out.copy")
        message = str(caught.exception)
        self.assertIn("produces 2 Parts", message)
        self.assertIn("out.mean, out.count", message)
        self.assertIn("ref['out.mean']", message)
        self.assertIn("ref.part('out.mean')", message)

    def test_a_bare_ref_is_refused_at_resolve_time_too(self):
        """The same refusal from PCR.run, for a program built through `Tick.calc`,
        which has no PCR-wide writer index to check at bind time.

        Mutation: delete the `multi_ids` branch in PCR.run -- this program runs and
        `reader` silently receives the whole mapping.
        """
        pxc = PxC()
        pxc.set(Part("in.rows"), [1, 2, 3, 4])
        pcr = PCR("bare-run")
        stats = pcr.tick("T").calc(SPLIT_STATS, id="stats", rows=Part("in.rows"), into=PRODUCES)
        pcr.tick("U").calc(TAKE_VALUE, id="reader", value=stats, into=Part("out.copy"))
        with self.assertRaises(ValueError) as caught:
            pcr.run(pxc)
        self.assertIn("binds the whole result of 'stats'", str(caught.exception))
        self.assertFalse(pxc.has(Part("out.copy")))

    def test_a_ref_to_an_address_that_invocation_does_not_publish_is_refused(self):
        pxc = PxC()
        pxc.set(Part("in.rows"), [1, 2, 3, 4])
        pcr = PCR("wrong-produce")
        stats = pcr.calc("T", SPLIT_STATS, id="stats", rows=Part("in.rows"), into=PRODUCES)
        with self.assertRaises(ValueError) as caught:
            pcr.calc("U", TAKE_VALUE, id="reader", value=stats["out.nowhere"], into="out.copy")
        self.assertIn("out.nowhere", str(caught.exception))
        self.assertIn("out.mean, out.count", str(caught.exception))

    def test_a_bare_ref_to_a_one_address_invocation_is_still_the_whole_result(self):
        """The compatibility half: nothing changes for a one-address producer, and its
        testimony spelling stays `fn:<id>`.
        """
        pxc = PxC()
        pxc.set(Part("in.v"), 3)
        pcr = PCR("bare-single")
        first = pcr.calc("T", TAKE_VALUE, id="first", value=Part("in.v"), into="mid.v")
        pcr.calc("U", TAKE_VALUE, id="second", value=first, into="out.v")
        run = pcr.run(pxc)
        self.assertEqual(run.results["second"], 3)
        self.assertEqual(run.ticks[1].calculations[0].inputs, {"value": "fn:first"})


class TheReturnMustAnswerForEveryAddress(unittest.TestCase):
    """pcr.py `_split_produces`: strict in both directions, and nothing is published
    unless every declared address has its value ({?} MultiReturnStrict)."""

    def refuse(self, calculation, produces=None):
        pxc = PxC()
        pxc.set(Part("in.rows"), [1, 2, 3, 4])
        pcr = PCR("strict")
        pcr.calc(
            "T", calculation, id="bad", rows=Part("in.rows"),
            into=PRODUCES if produces is None else produces,
        )
        with self.assertRaises(ValueError) as caught:
            pcr.run(pxc)
        self.assertEqual(pxc.addresses(), ("in.rows",))  # nothing published
        return str(caught.exception)

    def test_a_mapping_missing_an_address_is_refused(self):
        self.assertIn("no entry for out.count", self.refuse(MISSING_KEY))

    def test_a_mapping_keyed_by_the_wrong_addresses_is_refused(self):
        """A mapping that answers for `out.elsewhere` instead of `out.count` fails on
        the address it does not carry, which is the half a reader needs named.
        """
        self.assertIn("no entry for out.count", self.refuse(WRONG_KEYS))

    def test_a_mapping_with_a_spare_entry_is_refused(self):
        """Strict the other way too: an extra key is a produce the program did not
        declare, so it is refused rather than dropped ({?} MultiReturnStrict).
        """
        self.assertIn("out.spare", self.refuse(EXTRA_KEY))

    def test_a_sequence_of_the_wrong_length_is_refused(self):
        self.assertIn("returned a sequence of 1", self.refuse(SHORT_SEQUENCE))

    def test_a_value_that_is_neither_a_mapping_nor_a_sequence_is_refused(self):
        message = self.refuse(NOT_A_CONTAINER)
        self.assertIn("must return a mapping keyed by those addresses", message)
        self.assertIn("it returned int", message)


class DeclaringTheAddresses(unittest.TestCase):
    """What `into=` accepts, and what it refuses."""

    def test_addresses_may_be_strings_or_parts_mixed(self):
        pxc = PxC()
        pxc.set(Part("in.rows"), [1, 2, 3, 4])
        pcr = PCR("mixed")
        pcr.calc("T", SPLIT_STATS, id="stats", rows=Part("in.rows"), into=("out.mean", Part("out.count")))
        pcr.run(pxc)
        self.assertEqual(pxc.get(Part("out.count")), 4)

    def test_the_same_address_twice_is_refused(self):
        """pcr.py `_normalize_into`: one invocation publishes each address once.

        Mutation: drop the duplicate check -- the second value silently overwrites the
        first and the receipt lists one address twice.
        """
        pcr = PCR("dup")
        with self.assertRaises(ValueError) as caught:
            pcr.calc("T", SPLIT_STATS, id="stats", into=["out.mean", "out.mean"])
        self.assertIn("twice", str(caught.exception))

    def test_an_empty_list_is_refused(self):
        pcr = PCR("empty")
        with self.assertRaises(ValueError) as caught:
            pcr.calc("T", SPLIT_STATS, id="stats", into=[])
        self.assertIn("never an empty list", str(caught.exception))

    def test_the_receipt_segment_is_refused_inside_a_list(self):
        """`_refuse_receipt_into` is applied to every address, not just to the first:
        the reserved segment stays written by observation and by nothing else.

        Mutation: check only `into[0]` -- the program below forges its own testimony
        through the second address.
        """
        pcr = PCR("forge")
        with self.assertRaises(ValueError) as caught:
            pcr.calc("T", SPLIT_STATS, id="stats", into=["out.mean", "px.receipt.forge.T.stats"])
        self.assertIn("no Calculation may produce into it", str(caught.exception))

    def test_two_invocations_may_not_both_write_one_address(self):
        """The multiple-writers rule is per address, so it holds across the list.

        In a *later* Tick, because two writers in one Tick are the node law's
        business now (task 39) and are refused with the sibling message the next
        test pins; the PCR-wide rule this test guards is the one that holds
        whatever Tick the second writer is in.
        """
        pcr = PCR("writers")
        pcr.calc("T", SPLIT_STATS, id="stats", into=["out.mean", "out.count"])
        with self.assertRaises(ValueError) as caught:
            pcr.calc("T2", TAKE_VALUE, id="other", into="out.count")
        self.assertIn("multiple writers for 'out.count'", str(caught.exception))

    def test_two_siblings_may_not_both_write_one_address_of_the_list(self):
        """Inside one Tick the same collision is the node law, naming both ids."""
        pcr = PCR("writers-same-tick")
        pcr.calc("T", SPLIT_STATS, id="stats", into=["out.mean", "out.count"])
        with self.assertRaises(ValueError) as caught:
            pcr.calc("T", TAKE_VALUE, id="other", into="out.count")
        message = str(caught.exception)
        self.assertIn("'stats'", message)
        self.assertIn("'other'", message)
        self.assertIn("out.count", message)
        self.assertIn("node law", message)

    def test_a_one_entry_list_is_the_multi_produce_form(self):
        """The shape decides, not the count ({?} OneElementList): `into=[a]` asks for a
        mapping or a sequence, so a program cannot slide between the two meanings by
        the length of a computed list.
        """
        pxc = PxC()
        pxc.set(Part("in.v"), 3)
        pcr = PCR("one-entry")
        pcr.calc("T", TAKE_VALUE, id="take", value=Part("in.v"), into=["out.v"])
        with self.assertRaises(ValueError) as caught:
            pcr.run(pxc)
        self.assertIn("declares 1 produces", str(caught.exception))


class TestimonyBytesUnchanged(unittest.TestCase):
    """The rule every seam here is held to: observation changes no testimony byte."""

    def ticks_json(self, run):
        return json.dumps([asdict(tick) for tick in run.ticks])

    def test_observe_on_and_off_produce_identical_tick_bytes(self):
        off = two_output_program()[0:2]
        on = two_output_program()[0:2]
        self.assertEqual(
            self.ticks_json(off[0].run(off[1], observe=False)),
            self.ticks_json(on[0].run(on[1], observe=True)),
        )

    def test_a_multi_produce_into_serializes_as_a_json_array(self):
        pcr, pxc, _ = two_output_program()
        payload = json.loads(self.ticks_json(pcr.run(pxc)))
        self.assertEqual(payload[0]["calculations"][0]["into"], ["out.mean", "out.count"])
        self.assertEqual(payload[1]["calculations"][0]["into"], "out.reported")


class OneAddressCallsAreUnchanged(unittest.TestCase):
    """A one-address call is byte for byte what it was before multi-produce landed.

    `fixtures/single_into_pre_change.json` was written by the commit before this
    change from `tests/fixture_single_into.py`, which both that generator and this
    test import -- so the Calculation body whose source digest the fixture pins is
    literally the same text, not a copy of it.
    """

    def setUp(self):
        with open(FIXTURE, encoding="utf-8") as handle:
            self.pinned = json.load(handle)
        self.now = fixture_single_into.payload()

    def test_the_record_is_byte_identical(self):
        """materialize.py: the record document gained no field. `into` is still a bare
        string for one address, `inputs` still spells a one-address producer `fn:<id>`.

        Mutation: emit `"produce_sha256"` into the record invocation, or `[into]`
        instead of `into` -- the bytes below differ, and so would every record ever
        written (`{?} RecordProduceDigest`).
        """
        self.assertEqual(
            fixture_single_into.dumps(self.now["record"]),
            fixture_single_into.dumps(self.pinned["record"]),
        )

    def test_the_receipt_differs_only_by_the_added_produce_digest(self):
        """pcr.py: every other Receipt field is what it was, and the added fields
        say of a one-address serial invocation exactly what was already true --
        `produce_sha256` is what `result_sha256` already said (task 27), and
        `placement` is None because a serial Tick has no placement (task 39).
        """
        receipt = dict(self.now["receipt"])
        added = {key: receipt.pop(key) for key in list(receipt) if key not in self.pinned["receipt"]}
        self.assertEqual(sorted(added), ["placement", "produce_sha256"])
        self.assertIsNone(added["placement"])
        self.assertEqual(added["produce_sha256"], {"out.v": receipt["result_sha256"]})
        self.assertEqual(
            fixture_single_into.dumps(receipt),
            fixture_single_into.dumps(self.pinned["receipt"]),
        )

    def test_the_fixture_pins_the_shape_this_change_had_to_preserve(self):
        """The fixture is only a guard if it carries both binding spellings and a
        one-address `into`; assert that, so a future edit cannot weaken it silently.
        """
        record = self.pinned["record"]
        self.assertEqual(record["ticks"][0]["invocations"][0]["into"], "out.v")
        self.assertEqual(record["ticks"][0]["invocations"][0]["inputs"], {"value": "px:input.v"})
        self.assertEqual(record["ticks"][1]["invocations"][0]["inputs"], {"value": "fn:take"})
        self.assertNotIn("produce_sha256", record["ticks"][0]["invocations"][0])


if __name__ == "__main__":
    unittest.main()
