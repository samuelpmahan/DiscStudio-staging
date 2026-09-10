"""Executable spec of PQL and of the reserved receipt segment.

Two things live here because they are one thing: receipts are Parts
(`pyto/questions.md` `{?} EverythingIsAPart`), so *reading* them is PQL's job and
nothing new, and *writing* them is the store's to refuse. `PQL.receipts` is the
thin, named layer over `PQL.prefix` that spells the address scheme once; `PxC.set`
is where the segment stops being reserved only against programs and becomes
reserved against callers (`experiments/tasks/22/packet.md`
`{?} ReceiptStoreSetUnguarded`).

Every run below is a real `PCR.run(..., observe=True)`, not a hand-built store:
the addresses under test are the ones `pcr.py` actually writes.

Every Calculation body is a named module-level function; no lambdas
(`experiments/CAPTURE.md`, rule 2).
"""

from __future__ import annotations

import unittest

from pyto import Calculation, Part, PCR, PQL, PxC
from pyto.core import RECEIPT_PREFIX, receipt_writes_allowed
from pyto.pcr import Receipt, receipt_address


# --- module-level calculation bodies ------------------------------------------


def _take_value(args):
    return args["value"]


def _double(args):
    return args["value"] * 2


TAKE = Calculation("fn.pql.take", _take_value)
DOUBLE = Calculation("fn.pql.double", _double)


def two_tick_run(name: str = "counted", *, observe: bool = True) -> tuple[PxC, object]:
    """A PCR with two Ticks and three invocations, run for real."""
    pxc = PxC()
    pxc.set(Part("input.v"), 3)
    pcr = PCR(name)
    pcr.calc("Prepare", TAKE, id="take", value=Part("input.v"), into=Part("out.v"))
    pcr.calc("Prepare", DOUBLE, id="twice", value=Part("input.v"), into=Part("out.twice"))
    pcr.calc("Report", TAKE, id="report", value=Part("out.v"), into=Part("out.report"))
    return pxc, pcr.run(pxc, observe=observe)


# --- PQL, the parts that existed before -----------------------------------------


class PqlSelection(unittest.TestCase):
    """`part`, `prefix`, `where`, `matches`, `values`, `one`, `optional`."""

    def setUp(self):
        self.pxc = PxC()
        self.pxc.set(Part("px.students.mean"), 80.5)
        self.pxc.set(Part("px.students.median"), 82.5)
        self.pxc.set(Part("px.staff.mean"), 41.0)

    def test_part_selects_one_and_a_missing_part_selects_none(self):
        self.assertEqual(PQL.part("px.students.mean").values(self.pxc), (80.5,))
        self.assertEqual(PQL.part(Part("px.students.absent")).matches(self.pxc), ())

    def test_prefix_selects_in_address_order(self):
        """`pxc.items()` is sorted, so every PQL walk is deterministic; the whole
        `px` shell and `PQL.receipts` below inherit their ordering from this line.

        Mutation: core.py `items`, drop `sorted` -- this fails, and so does every
        committed `px ls` fixture.
        """
        self.assertEqual(
            [m.address for m in PQL.prefix("px.students.").matches(self.pxc)],
            ["px.students.mean", "px.students.median"],
        )

    def test_prefix_refuses_an_empty_prefix(self):
        with self.assertRaises(ValueError):
            PQL.prefix("")

    def test_where_refines_and_one_and_optional_are_strict(self):
        older = PQL.prefix("px.").where(lambda match: match.value > 81)
        self.assertEqual(older.values(self.pxc), (82.5,))
        self.assertEqual(older.one(self.pxc), 82.5)
        self.assertIsNone(PQL.part("px.students.absent").optional(self.pxc))
        with self.assertRaises(ValueError):
            PQL.prefix("px.").one(self.pxc)
        with self.assertRaises(ValueError):
            PQL.prefix("px.").optional(self.pxc)


# --- PQL.receipts ----------------------------------------------------------------


class PqlReceipts(unittest.TestCase):
    """The named layer over the receipt address scheme."""

    def test_every_receipt_of_a_real_run_address_sorted(self):
        pxc, run = two_tick_run()
        matches = PQL.receipts(pxc)
        self.assertEqual(
            [match.address for match in matches],
            [
                "px.receipt.counted.Prepare.take",
                "px.receipt.counted.Prepare.twice",
                "px.receipt.counted.Report.report",
            ],
        )
        self.assertEqual([m.address for m in matches], sorted(m.address for m in matches))
        for match in matches:
            self.assertIsInstance(match.value, Receipt)

    def test_the_values_are_the_run_s_own_receipt_objects(self):
        """Not a projection of them: the Part *is* the Receipt (`pcr.py:647`)."""
        pxc, run = two_tick_run()
        by_address = {match.address: match.value for match in PQL.receipts(pxc)}
        for invocation_id, receipt in run.receipts.items():
            with self.subTest(id=invocation_id):
                address = next(a for a in by_address if a.endswith(f".{invocation_id}"))
                self.assertIs(by_address[address], receipt)

    def test_pcr_narrows_by_segment_not_by_string_prefix(self):
        """`pcr='count'` must not match the PCR named `counted`.

        Mutation: pql.py `PQL.receipts`, return `PQL.prefix(RECEIPT_PREFIX + pcr)`
        without the trailing dot and without `narrows` -- this fails.
        """
        pxc, _ = two_tick_run()
        self.assertEqual(len(PQL.receipts(pxc, pcr="counted")), 3)
        self.assertEqual(PQL.receipts(pxc, pcr="count"), ())
        self.assertEqual(PQL.receipts(pxc, pcr="countedd"), ())

    def test_tick_narrows_on_the_second_segment_with_or_without_a_pcr(self):
        """`tick` alone cannot narrow the walk to a prefix -- the PCR name is in
        front of it -- so it is a filter, and it must land on the right segment.

        Mutation: pql.py `PQL.receipts`, index `wanted` from 0 for a lone `tick`
        -- `tick='Prepare'` matches nothing, because segment 0 is the PCR name.
        """
        pxc, _ = two_tick_run()
        self.assertEqual(
            [m.address for m in PQL.receipts(pxc, tick="Prepare")],
            ["px.receipt.counted.Prepare.take", "px.receipt.counted.Prepare.twice"],
        )
        self.assertEqual(
            [m.address for m in PQL.receipts(pxc, pcr="counted", tick="Report")],
            ["px.receipt.counted.Report.report"],
        )
        self.assertEqual(PQL.receipts(pxc, tick="counted"), ())
        self.assertEqual(PQL.receipts(pxc, pcr="counted", tick="Prep"), ())

    def test_an_empty_segment_is_refused_rather_than_matching_everything(self):
        pxc, _ = two_tick_run()
        with self.assertRaises(ValueError):
            PQL.receipts(pxc, pcr="")
        with self.assertRaises(ValueError):
            PQL.receipts(pxc, tick="")

    def test_observe_off_leaves_nothing_for_it_to_read(self):
        pxc, run = two_tick_run(observe=False)
        self.assertEqual(PQL.receipts(pxc), ())
        self.assertEqual(run.receipts, {})

    def test_it_is_prefix_with_a_name_and_reads_only_the_reserved_segment(self):
        """The docstring's claim: a thin layer, so an ordinary address that merely
        mentions `receipt` is not one.
        """
        pxc, _ = two_tick_run()
        pxc.set(Part("px.receipts.note"), "not under the reserved segment")
        pxc.set(Part("px.receipt_like.note"), "nor this")
        addresses = [match.address for match in PQL.receipts(pxc)]
        self.assertTrue(all(address.startswith(RECEIPT_PREFIX) for address in addresses))
        self.assertEqual(addresses, [m.address for m in PQL.prefix(RECEIPT_PREFIX).matches(pxc)])


# --- the store guard -------------------------------------------------------------


class ReceiptWritesAreTheRunS(unittest.TestCase):
    """`{?} ReceiptStoreSetUnguarded` (task 22), decided in code: the segment is
    reserved against callers, not only against programs."""

    def test_user_code_cannot_forge_a_receipt(self):
        """The refusal the `{?}` asked for.

        Mutation: core.py `PxC.set`, drop the `address.startswith(RECEIPT_PREFIX)`
        guard -- this fails, and anything holding the store can file a receipt
        that no run ever wrote.
        """
        pxc = PxC()
        with self.assertRaises(ValueError) as caught:
            pxc.set(Part("px.receipt.forged.Tick.id"), "not a Receipt")
        self.assertIn(RECEIPT_PREFIX, str(caught.exception))
        self.assertFalse(pxc.has("px.receipt.forged.Tick.id"))

    def test_an_ordinary_address_is_untouched_by_the_guard(self):
        pxc = PxC()
        for address in ("px.receipts.note", "px.receipt_like.note", "out.v", "px.view.receipt"):
            with self.subTest(address=address):
                self.assertEqual(pxc.set(Part(address), 1).kind, "new-address")

    def test_the_run_files_its_receipts_through_the_same_set(self):
        """`pcr.py` is another team's file and is not edited: the guard recognises
        the run by the module the calling frame belongs to (`core.RUN_MODULE`).
        """
        pxc, run = two_tick_run()
        self.assertEqual(len(run.receipts), 3)
        self.assertEqual(len(PQL.receipts(pxc)), 3)

    def test_the_marker_and_the_context_manager_are_the_two_explicit_ways_in(self):
        pxc = PxC()
        write = pxc.set(Part("px.receipt.marked.T.i"), "by the marker", _from_run=True)
        self.assertEqual(write.kind, "new-address")
        with receipt_writes_allowed():
            pxc.set(Part("px.receipt.opened.T.i"), "inside the block")
        self.assertEqual(
            [m.address for m in PQL.receipts(pxc)],
            ["px.receipt.marked.T.i", "px.receipt.opened.T.i"],
        )

    def test_the_context_manager_closes_again_even_after_a_raise(self):
        pxc = PxC()
        with self.assertRaises(RuntimeError):
            with receipt_writes_allowed():
                raise RuntimeError("boom")
        with self.assertRaises(ValueError):
            pxc.set(Part("px.receipt.after.T.i"), 1)

    def test_the_context_manager_nests(self):
        pxc = PxC()
        with receipt_writes_allowed():
            with receipt_writes_allowed():
                pxc.set(Part("px.receipt.inner.T.i"), 1)
            pxc.set(Part("px.receipt.outer.T.i"), 2)
        with self.assertRaises(ValueError):
            pxc.set(Part("px.receipt.outside.T.i"), 3)


# --- the two task-22 questions decided in code -----------------------------------


class ReceiptsAsInputsAndOnRerun(unittest.TestCase):
    """`{?} ReceiptInputNotRefused` and `{?} ReceiptRerunOverwrite` (task 22)."""

    def test_a_receipt_may_be_bound_as_an_input(self):
        """Decided as it already stands: only *producing* into `px.receipt.` is
        refused, so reading a receipt is ordinary and the guard above does not
        move from `into` to the whole binding map.

        Mutation: `pcr.py:_refuse_receipt_into` applied to bindings as well --
        this fails, and `px receipts` could never be fed back into a program.
        """
        pxc = PxC()
        pxc.set(Part("input.v"), 3)
        pcr = PCR("readback")
        pcr.calc("One", TAKE, id="take", value=Part("input.v"), into=Part("out.v"))
        pcr.calc(
            "Two", TAKE, id="reader",
            value=Part(receipt_address("readback", "One", "take")), into=Part("out.copy"),
        )
        run = pcr.run(pxc, observe=True)
        self.assertIs(run.results["reader"], run.receipts["take"])
        self.assertIsInstance(PQL.part("out.copy").one(pxc), Receipt)

    def test_a_rerun_replaces_the_receipt_part_in_place(self):
        """Decided as it stands: the scheme has no run identity, so one address
        per invocation and the last run's receipt is the one in the store. The
        `{?}` stays open in the packet for whether a run id belongs in the
        address; this test pins what the code does today so the change is visible
        when someone makes it.

        Mutation: give `receipt_address` a run counter -- the address count below
        doubles and `kind` is `new-address` twice.
        """
        pxc = PxC()
        pxc.set(Part("input.v"), 3)
        pcr = PCR("twice")
        pcr.calc("One", TAKE, id="take", value=Part("input.v"), into=Part("out.v"))
        first = pcr.run(pxc, observe=True)
        before = PQL.receipts(pxc)
        second = pcr.run(pxc, observe=True)
        after = PQL.receipts(pxc)
        self.assertEqual([m.address for m in before], [m.address for m in after])
        self.assertEqual(len(after), 1)
        self.assertIs(after[0].value, second.receipts["take"])
        self.assertIsNot(after[0].value, first.receipts["take"])


if __name__ == "__main__":
    unittest.main()
