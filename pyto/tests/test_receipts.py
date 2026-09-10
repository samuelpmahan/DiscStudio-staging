"""Executable spec of the Day 2 receipts seam (ULTRACODE-WEEK.md Day 2, lane A).

The seam is a transfer, not an invention: `Receipt` is the LAB Tick receipt
(reference/lab/chesslab-lab/contract.ts:127-141 `Receipt`, contract.ts:60-68
`FrozenCalculation`, contract.ts:71-74 `PxWriteTestimony`) with the observation
mechanism of reference/lab/wumpus-core/execute.js:10-47 and the tracked board of
/home/user/DiscStudio-staging/src/core/exec.js:22-33 `trackAccess`
(research/lab-transfer-ledger.md:35-41).

The seam is additive and lives in `PcrRun.receipts`, so the bytes consumers embed
in compositionEvidence -- `json.dumps([asdict(t) for t in run.ticks])` at
consumers/discstudio-card/card_composition.py:177 and consumers/discstudio-card/app.py:53
-- are unchanged with `observe` on or off. Two tests below are that oracle: one
compares observe on/off in-process, one compares against the Day 1 bytes retained
at experiments/grouped-ablation/evidence/run-1/testimony.json.

Every Calculation body is a named module-level function; no lambdas
(experiments/CAPTURE.md, rule 2).
"""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import os
import sys
import unittest
from dataclasses import asdict

from pyto import Calculation, Part, PCR, PQL, PxC, PxWrite
from pyto.core import RECEIPT_PREFIX
from pyto.materialize import run_record
from pyto.pcr import FrozenCalculation, Receipt, receipt_address  # __init__.py does not export these (see CHANGES.md)

# Intra-repo sys.path insert (experiments/CAPTURE.md, "sys.path: what is logged and what
# is forbidden"): the Day 1 program lives in experiments/grouped-ablation/ and its modules
# import each other by top-level name (program.py imports `calculations`), so the directory
# must be importable under its own name. The path is inside this repository; the insert is
# announced on stderr so it appears in tests.txt, and asserted in-repo by
# TestimonyBytesUnchanged.test_experiment_path_is_inside_this_repository.
PYTO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPERIMENT_DIR = os.path.join(PYTO_ROOT, "experiments", "grouped-ablation")
RUN_1 = os.path.join(EXPERIMENT_DIR, "evidence", "run-1", "testimony.json")
if EXPERIMENT_DIR not in sys.path:
    print(f"[tests/test_receipts] sys.path.insert(0, {EXPERIMENT_DIR!r})", file=sys.stderr)
    sys.path.insert(0, EXPERIMENT_DIR)

from calculations import REGISTRY as ABLATION_REGISTRY, select_variants  # noqa: E402
from features import GROUPS, make_data  # noqa: E402
from program import GROUPS as GROUPS_PART, ROWS, build_program  # noqa: E402
from run import run_experiment  # noqa: E402

SEED, N = 7, 400  # run.py:main defaults; evidence/run-1/comparison.json records seed 7, n 400


# --- module-level calculation bodies (named functions only) --------------------


def take_value(args):
    return args["value"]


def bump(args):
    return args["current"] + 1


def const_seven(args):
    return 7


def make_set(args):
    return {"a", "b"}


def make_pxc(args):
    return PxC()


def mold_counts(args):
    """A dict with tuple keys: the disc-stats result shape.

    consumers/discstudio-card/experiments/disc-stats/stats.py:34
    distinct_discs_by_mold -> dict[tuple[str, str], int].
    """
    return {("Innova", "Destroyer"): 2, ("Discraft", "Buzzz"): 1}


TAKE_VALUE = Calculation("fn.receipt.takeValue", take_value)
BUMP = Calculation("fn.receipt.bump", bump)
CONST_SEVEN = Calculation("fn.receipt.constSeven", const_seven)
MAKE_SET = Calculation("fn.receipt.makeSet", make_set)
MAKE_PXC = Calculation("fn.receipt.makePxc", make_pxc)
MOLD_COUNTS = Calculation("fn.receipt.moldCounts", mold_counts)
BUILTIN = Calculation("fn.receipt.builtin", len)  # a C builtin: inspect.getsource raises


def canonical_sha256(value) -> str:
    """The digest the seam must produce: no default=, so non-JSON values have none (gap 10)."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def source_sha256(function) -> str:
    """The digest the kernel computes: source text with CRLF normalized to LF (pcr.py)."""
    return hashlib.sha256(inspect.getsource(function).replace("\r\n", "\n").encode("utf-8")).hexdigest()


def ticks_json(run) -> str:
    """The exact expression consumers embed (card_composition.py:177, app.py:53)."""
    return json.dumps([asdict(tick) for tick in run.ticks])


def sorted_ticks_json(ticks) -> str:
    """Key-order-independent form, for comparing against a file written with sort_keys=True."""
    return json.dumps(json.loads(json.dumps(ticks)), sort_keys=True)


def build_day1(observe: bool):
    """The Day 1 program on the Day 1 input, mirroring run.py:66-78 (run_experiment)."""
    pxc = PxC()
    pxc.set(ROWS, make_data(SEED, N))
    pxc.set(GROUPS_PART, GROUPS)
    variants = select_variants({"groups": GROUPS})
    pcr = build_program(variants)
    return pcr, pxc, pcr.run(pxc, observe=observe)


class TestimonyBytesUnchanged(unittest.TestCase):
    """The hard rule: the seam changes no byte of the tick payload consumers serialize."""

    def test_observe_on_and_off_produce_identical_tick_bytes(self):
        off = build_day1(observe=False)[2]
        on = build_day1(observe=True)[2]
        self.assertEqual(ticks_json(off), ticks_json(on))

    def test_tick_bytes_equal_the_retained_day_1_testimony(self):
        """Both legs: the retained Day 1 bytes are pinned against an observe=False run
        AND against an observe=True one.

        The unobserved leg has to be built here. `run_experiment` is no longer an
        observe=False caller: this day's change to run.py made it pass observe=True
        (experiments/grouped-ablation/run.py:92), so comparing only `run_experiment`
        against `build_day1(observe=True)` would compare observation on against
        observation on and never touch the retained file's unobserved lineage
        (fixer round 2, finding 11).
        """
        with open(RUN_1, encoding="utf-8") as handle:
            retained = json.load(handle)
        unobserved = build_day1(observe=False)[2]
        run = run_experiment(SEED, N)["run"]  # run.py:92 passes observe=True
        observed = build_day1(observe=True)[2]
        self.assertEqual(retained["pcr"], run.pcr)
        self.assertEqual(retained["pcr"], unobserved.pcr)
        retained_ticks = sorted_ticks_json(retained["ticks"])
        self.assertEqual(retained_ticks, sorted_ticks_json([asdict(t) for t in unobserved.ticks]))
        self.assertEqual(retained_ticks, sorted_ticks_json([asdict(t) for t in run.ticks]))
        self.assertEqual(retained_ticks, sorted_ticks_json([asdict(t) for t in observed.ticks]))
        self.assertEqual(ticks_json(unobserved), ticks_json(observed))
        self.assertEqual(ticks_json(run), ticks_json(observed))

    def test_experiment_path_is_inside_this_repository(self):
        self.assertTrue(os.path.abspath(EXPERIMENT_DIR).startswith(PYTO_ROOT + os.sep))
        self.assertTrue(os.path.isfile(RUN_1))


class ReceiptsAreOptional(unittest.TestCase):
    def test_receipts_empty_when_observe_is_false(self):
        pxc = PxC()
        pxc.set(Part("input.v"), 3)
        pcr = PCR("optional")
        pcr.calc("t", TAKE_VALUE, id="take", value=Part("input.v"), into=Part("out.v"))
        self.assertEqual(pcr.run(pxc).receipts, {})
        self.assertEqual(pcr.run(pxc, observe=False).receipts, {})

    def test_receipts_keyed_by_invocation_id_when_observe_is_true(self):
        pxc = PxC()
        pxc.set(Part("input.v"), 3)
        pcr = PCR("keyed")
        pcr.calc("t", TAKE_VALUE, id="take", value=Part("input.v"), into=Part("out.v"))
        pcr.calc("t", CONST_SEVEN, id="seven", into=Part("out.seven"))
        run = pcr.run(pxc, observe=True)
        self.assertEqual(sorted(run.receipts), ["seven", "take"])
        self.assertIsInstance(run.receipts["take"], Receipt)
        self.assertEqual(run.receipts["take"].invocation_id, "take")
        self.assertEqual(set(run.receipts) & set(run.results), set(run.results))

    def test_day_1_program_gets_one_receipt_per_invocation(self):
        _, _, run = build_day1(observe=True)
        ids = [calc.id for tick in run.ticks for calc in tick.calculations]
        self.assertEqual(sorted(run.receipts), sorted(ids))


class ReceiptsAreParts(unittest.TestCase):
    """Everything is a Part: with observe on, each receipt is also written into the
    store under the reserved `px.receipt.` segment; with observe off nothing is.

    The address scheme is `px.receipt.<pcr>.<tick>.<invocation-id>`
    (pcr.py `receipt_address`, viewer/RECORD.md "Receipts as Parts").
    """

    def two_invocation_run(self, observe):
        pxc = PxC()
        pxc.set(Part("input.v"), 3)
        pcr = PCR("parts")
        pcr.calc("Prepare", TAKE_VALUE, id="take", value=Part("input.v"), into=Part("out.v"))
        pcr.calc("Prepare", CONST_SEVEN, id="seven", into=Part("out.seven"))
        return pxc, pcr.run(pxc, observe=observe)

    def test_receipt_address_is_pcr_tick_and_invocation_id(self):
        """pcr.py `receipt_address`: f"{RECEIPT_PREFIX}{pcr}.{tick}.{invocation_id}".

        Mutation: drop the tick (or the pcr) from the f-string -- the addresses below
        stop being predictable from the PCR and the two-tick case collides.
        """
        pxc, _ = self.two_invocation_run(observe=True)
        self.assertEqual(
            [a for a in pxc.addresses() if a.startswith(RECEIPT_PREFIX)],
            ["px.receipt.parts.Prepare.seven", "px.receipt.parts.Prepare.take"],
        )
        self.assertEqual(receipt_address("parts", "Prepare", "take"), "px.receipt.parts.Prepare.take")

    def test_same_calculation_twice_in_one_tick_gets_two_addresses(self):
        """The scheme keys on the invocation id, which PCR.calc keeps unique, not on the
        Calculation address, which repeats (`fit.all`/`fit.none` in the Day 1 program).

        Mutation: `receipt_address(..., invocation.calculation.address)` -- the second
        invocation overwrites the first and only one receipt Part survives.
        """
        pxc = PxC()
        pxc.set(Part("input.v"), 3)
        pcr = PCR("twice")
        pcr.calc("T", TAKE_VALUE, id="first", value=Part("input.v"), into=Part("out.a"))
        pcr.calc("T", TAKE_VALUE, id="second", value=Part("input.v"), into=Part("out.b"))
        run = pcr.run(pxc, observe=True)
        self.assertEqual(
            [a for a in pxc.addresses() if a.startswith(RECEIPT_PREFIX)],
            ["px.receipt.twice.T.first", "px.receipt.twice.T.second"],
        )
        self.assertIsNot(run.receipts["first"], run.receipts["second"])

    def test_the_stored_part_is_the_receipt_object_pql_reads(self):
        """pcr.py: `pxc.set(receipt_address(...), receipt)` stores the Receipt itself, so
        PQL reads receipts like anything else -- no second, divergent projection.

        Mutation: store `asdict(receipt)` (or the invocation id) -- the identity and the
        attribute reads below fail.
        """
        pxc, run = self.two_invocation_run(observe=True)
        matches = PQL.prefix(RECEIPT_PREFIX).matches(pxc)
        self.assertEqual(len(matches), 2)
        by_address = {match.address: match.value for match in matches}
        self.assertIs(by_address["px.receipt.parts.Prepare.take"], run.receipts["take"])
        stored = PQL.part("px.receipt.parts.Prepare.seven").one(pxc)
        self.assertIsInstance(stored, Receipt)
        self.assertEqual(stored.invocation_id, "seven")
        self.assertEqual(stored.result_sha256, canonical_sha256(7))
        self.assertEqual(
            [m.address for m in PQL.prefix(RECEIPT_PREFIX).where(
                lambda m: m.value.declared_produces == ("out.v",)).matches(pxc)],
            ["px.receipt.parts.Prepare.take"],
        )

    def test_observe_off_leaves_the_store_untouched(self):
        """The intent's second half: with observe off nothing is written, asserted by
        comparing the store's contents before and after.

        pcr.py: the store write lives inside the `isinstance(board, _TrackedPxC)` branch,
        which only observe=True enters.

        Mutation: `def run(self, pxc, *, observe: bool = True)` -- the two unobserved
        runs below file receipts and the comparison sees a store that grew.
        """
        pxc = PxC()
        pxc.set(Part("input.v"), 3)
        pcr = PCR("quiet")
        pcr.calc("Prepare", TAKE_VALUE, id="take", value=Part("input.v"), into=Part("out.v"))
        pcr.run(pxc)  # produce out.v first, so the comparison is of a settled store
        before = pxc.items()
        pcr.run(pxc)
        pcr.run(pxc, observe=False)
        self.assertEqual(pxc.items(), before)
        self.assertEqual(pxc.addresses(), ("input.v", "out.v"))

    def test_the_receipt_write_is_invisible_to_the_receipts_themselves(self):
        """Observation must not leak into the testimony it observes: no receipt address
        appears in any receipt's own declared/actual access or writes.

        This is the invariant behind two decisions rather than a single line: the write
        goes to `pxc` and not to `board` (the tracked view belongs to the invocation, and
        a receipt is not something the invocation produced), and it happens after the
        Receipt is frozen. Filing the receipt through the board *before* freezing it --
        the shape this rules out -- would make every invocation testify that it produced
        its own receipt.
        """
        _, run = self.two_invocation_run(observe=True)
        for invocation_id, receipt in run.receipts.items():
            with self.subTest(id=invocation_id):
                addresses = (
                    receipt.actual_produces
                    + receipt.actual_consumes
                    + receipt.declared_produces
                    + tuple(write.address for write in receipt.writes)
                )
                self.assertEqual([a for a in addresses if a.startswith(RECEIPT_PREFIX)], [])

    def test_a_receipt_part_can_be_read_back_by_a_later_invocation(self):
        """Everything is a Part, in both directions: reading `px.receipt.` is ordinary
        (only producing into it is refused), and run_record does not call this run's own
        receipt a Part that preexisted the run.

        Mutation: materialize.py drop `address not in own_receipts` from the
        `preexisting` fallback -- the receipt row below reports preexisting: true for a
        Part this very run wrote.
        """
        pxc = PxC()
        pxc.set(Part("input.v"), 3)
        pcr = PCR("readback")
        pcr.calc("One", TAKE_VALUE, id="take", value=Part("input.v"), into=Part("out.v"))
        pcr.calc(
            "Two",
            TAKE_VALUE,
            id="reader",
            value=Part("px.receipt.readback.One.take"),
            into=Part("out.copy"),
        )
        run = pcr.run(pxc, observe=True)
        self.assertIs(run.results["reader"], run.receipts["take"])
        record = run_record(run, pxc)  # preexisting inferred, the fallback path
        row = record["parts"]["px.receipt.readback.One.take"]
        self.assertFalse(row["preexisting"])
        self.assertEqual(row["read_by"], ["reader"])
        self.assertTrue(record["parts"]["input.v"]["preexisting"])

    def test_run_record_names_no_receipt_of_its_own(self):
        """The same invariant one layer up: the run record's part index is built from the
        testimony and the receipts, never from the store, so this run's own receipt Parts
        are not rows in it (viewer/RECORD.md, "Receipts as Parts").
        """
        pxc = PxC()
        pxc.set(Part("input.v"), 3)
        pcr = PCR("record")
        pcr.calc("Prepare", TAKE_VALUE, id="take", value=Part("input.v"), into=Part("out.v"))
        record = run_record(pcr.run(pxc, observe=True), pxc)
        self.assertEqual([a for a in record["parts"] if a.startswith(RECEIPT_PREFIX)], [])

    def test_the_day_1_program_writes_one_receipt_part_per_invocation(self):
        _, pxc, run = build_day1(observe=True)
        ids = [calc.id for tick in run.ticks for calc in tick.calculations]
        expected = sorted(
            receipt_address(run.pcr, tick.name, calc.id)
            for tick in run.ticks
            for calc in tick.calculations
        )
        self.assertEqual(sorted(a for a in pxc.addresses() if a.startswith(RECEIPT_PREFIX)), expected)
        self.assertEqual(len(expected), len(ids))
        _, unobserved_pxc, _ = build_day1(observe=False)
        self.assertEqual([a for a in unobserved_pxc.addresses() if a.startswith(RECEIPT_PREFIX)], [])


class ReceiptSegmentIsNotBindable(unittest.TestCase):
    """No Calculation may bind a `px.receipt.` address as its `into`."""

    def test_pcr_calc_refuses_a_receipt_into(self):
        """pcr.py `_refuse_receipt_into`, called from PCR.calc before the writer is recorded.

        Mutation: delete the call in PCR.calc -- the program below binds the segment and
        forges its own testimony.
        """
        pcr = PCR("forge")
        with self.assertRaises(ValueError) as caught:
            pcr.calc("T", CONST_SEVEN, id="forge", into="px.receipt.forge.T.forge")
        message = str(caught.exception)
        self.assertIn("px.receipt.", message)
        self.assertIn("forge", message)
        self.assertIn("no Calculation may produce into it", message)
        # the refusal left no writer and no id behind: the same id still binds elsewhere
        pcr.calc("T", CONST_SEVEN, id="forge", into="out.seven")
        self.assertEqual(pcr.run(PxC()).results["forge"], 7)

    def test_tick_calc_refuses_a_receipt_into(self):
        """pcr.py `_refuse_receipt_into`, called from Tick.calc as well: the Tick's own
        binder is reachable directly (test_materialize.py:667 uses it).

        Mutation: delete the call in Tick.calc -- PCR.calc still refuses, this does not.
        """
        pcr = PCR("forge-tick")
        with self.assertRaises(ValueError):
            pcr.tick("T").calc(CONST_SEVEN, id="forge", into=Part("px.receipt.anything"))
        self.assertEqual(pcr.tick("T").calculations, [])

    def test_an_ordinary_address_that_merely_mentions_receipt_still_binds(self):
        """The rule is the reserved second segment, not the word: `px.receipts.` and
        `px.badges.receipt` are ordinary domain nouns.

        Mutation: test `"receipt" in address` instead of the `px.receipt.` prefix.
        """
        pcr = PCR("ordinary")
        pcr.calc("T", CONST_SEVEN, id="a", into="px.receipts.mine")
        pcr.calc("T", CONST_SEVEN, id="b", into="px.badges.receipt")
        pxc = PxC()
        pcr.run(pxc)
        self.assertEqual(pxc.addresses(), ("px.badges.receipt", "px.receipts.mine"))


class FrozenCalculationIdentity(unittest.TestCase):
    def test_implementation_sha256_is_the_source_digest_and_is_stable(self):
        pcr = PCR("identity")
        pcr.calc("t", CONST_SEVEN, id="seven", into=Part("out.seven"))
        first = pcr.run(PxC(), observe=True).receipts["seven"].calculation
        second = pcr.run(PxC(), observe=True).receipts["seven"].calculation
        self.assertEqual(first.implementation_sha256, source_sha256(const_seven))
        self.assertEqual(first.implementation_sha256, second.implementation_sha256)
        self.assertEqual(first, second)

    def test_implementation_sha256_is_none_for_a_builtin(self):
        pcr = PCR("builtin")
        pcr.calc("t", BUILTIN, id="len", into=Part("out.len"))
        receipt = pcr.run(PxC(), observe=True).receipts["len"]
        self.assertIsNone(receipt.calculation.implementation_sha256)
        self.assertEqual(receipt.calculation.address, "fn.receipt.builtin")

    def test_identity_scope_and_limitation_are_the_chesslab_honesty_fields(self):
        # contract.ts:66-67: the digest is not a transitive source or dependency hash.
        pcr = PCR("honesty")
        pcr.calc("t", CONST_SEVEN, id="seven", into=Part("out.seven"))
        frozen = pcr.run(PxC(), observe=True).receipts["seven"].calculation
        self.assertIsInstance(frozen, FrozenCalculation)
        self.assertEqual(frozen.identity_scope, "runtime-function-body")
        self.assertEqual(frozen.limitation, "called helpers, constants, templates, and assets are not covered")


class ResultDigest(unittest.TestCase):
    def digest_for(self, calculation, calc_id):
        pcr = PCR("digest")
        pcr.calc("t", calculation, id=calc_id, into=Part(f"out.{calc_id}"))
        return pcr.run(PxC(), observe=True).receipts[calc_id].result_sha256

    def test_json_value_digest_is_canonical_json(self):
        self.assertEqual(self.digest_for(CONST_SEVEN, "seven"), canonical_sha256(7))

    def test_non_json_value_yields_none(self):
        # gap 10: no default=, so a set and a PxC have no digest instead of a repr digest.
        self.assertIsNone(self.digest_for(MAKE_SET, "set"))
        self.assertIsNone(self.digest_for(MAKE_PXC, "pxc"))

    def test_tuple_keys_yield_none(self):
        self.assertIsNone(self.digest_for(MOLD_COUNTS, "molds"))


class WriteKinds(unittest.TestCase):
    """contract.ts:71-74 and src/core/exec.js:28: new-address | refinement | replacement."""

    def run_three(self):
        pxc = PxC()
        pxc.set(Part("input.v"), 3)
        pxc.set(Part("shared.counter"), 1)  # bound as input below -> refinement
        pxc.set(Part("shared.other"), 0)  # not bound as input below -> replacement
        pcr = PCR("writes")
        pcr.calc("t", TAKE_VALUE, id="fresh", value=Part("input.v"), into=Part("out.fresh"))
        pcr.calc("t", BUMP, id="refine", current=Part("shared.counter"), into=Part("shared.counter"))
        pcr.calc("t", TAKE_VALUE, id="replace", value=Part("input.v"), into=Part("shared.other"))
        return pcr.run(pxc, observe=True)

    def test_kinds(self):
        receipts = self.run_three().receipts
        self.assertEqual(receipts["fresh"].writes, (PxWrite("out.fresh", "new-address"),))
        self.assertEqual(receipts["refine"].writes, (PxWrite("shared.counter", "refinement"),))
        self.assertEqual(receipts["replace"].writes, (PxWrite("shared.other", "replacement"),))

    def test_declared_and_actual_addresses(self):
        receipts = self.run_three().receipts
        self.assertEqual(receipts["refine"].declared_consumes, ("shared.counter",))
        self.assertEqual(receipts["refine"].actual_consumes, ("shared.counter",))
        self.assertEqual(receipts["refine"].declared_produces, ("shared.counter",))
        self.assertEqual(receipts["refine"].actual_produces, ("shared.counter",))
        self.assertEqual(receipts["fresh"].declared_produces, ("out.fresh",))

    def test_an_invocation_without_into_produces_nothing(self):
        pcr = PCR("no-into")
        pcr.calc("t", CONST_SEVEN, id="seven")
        receipt = pcr.run(PxC(), observe=True).receipts["seven"]
        self.assertEqual(receipt.writes, ())
        self.assertEqual(receipt.declared_produces, ())
        self.assertEqual(receipt.actual_produces, ())

    def test_a_result_ref_input_is_not_a_declared_consume(self):
        # pcr.py:261-265 rewrites a Part bound to an already-written address into a
        # ResultRef; declared_consumes is the bound *Part* addresses only.
        pxc = PxC()
        pxc.set(Part("input.v"), 3)
        pcr = PCR("refs")
        pcr.calc("t", TAKE_VALUE, id="first", value=Part("input.v"), into=Part("mid.v"))
        # 'second' reads what 'first' wrote, so it belongs to a *later* Tick: the node
        # law (pcr.py:_refuse_sibling_bindings, task 39) refuses a sibling result ref.
        pcr.calc("t2", TAKE_VALUE, id="second", value=Part("mid.v"), into=Part("out.v"))
        receipts = pcr.run(pxc, observe=True).receipts
        self.assertEqual(receipts["second"].declared_consumes, ())
        self.assertEqual(receipts["second"].actual_consumes, ())
        self.assertEqual(receipts["second"].effective_arg_keys, ("value",))


class ShadowedInputs(unittest.TestCase):
    def test_args_key_colliding_with_a_bound_input_is_recorded_not_raised(self):
        # pcr.py:331-332 call_args.update(invocation.args) overrides silently; the receipt
        # records it. {?} ShadowRule (research/lab-transfer-ledger.md:65-67) stays open:
        # the JS reader fails loud (src/core/exec.js:58), pyto still does not.
        pxc = PxC()
        pxc.set(Part("input.v"), 3)
        pcr = PCR("shadow")
        pcr.calc("t", TAKE_VALUE, id="shadow", value=Part("input.v"), args={"value": "override"}, into=Part("out.v"))
        run = pcr.run(pxc, observe=True)
        self.assertEqual(run.results["shadow"], "override")
        self.assertEqual(pxc.get(Part("out.v")), "override")
        receipt = run.receipts["shadow"]
        self.assertEqual(receipt.shadowed_inputs, ("value",))
        self.assertEqual(receipt.effective_arg_keys, ("value",))
        self.assertEqual(receipt.declared_consumes, ("input.v",))
        self.assertEqual(receipt.actual_consumes, ("input.v",))

    def test_no_collision_leaves_shadowed_inputs_empty(self):
        pxc = PxC()
        pxc.set(Part("input.v"), 3)
        pcr = PCR("no-shadow")
        pcr.calc("t", TAKE_VALUE, id="plain", value=Part("input.v"), args={"other": 1}, into=Part("out.v"))
        receipt = pcr.run(pxc, observe=True).receipts["plain"]
        self.assertEqual(receipt.shadowed_inputs, ())
        self.assertEqual(sorted(receipt.effective_arg_keys), ["other", "value"])


class Timing(unittest.TestCase):
    def test_duration_is_non_negative_and_started_is_monotonic(self):
        _, _, run = build_day1(observe=True)
        receipts = [run.receipts[calc.id] for tick in run.ticks for calc in tick.calculations]
        for receipt in receipts:
            with self.subTest(id=receipt.invocation_id):
                self.assertGreaterEqual(receipt.duration_ms, 0.0)
                self.assertIsInstance(receipt.duration_ms, float)
                self.assertGreaterEqual(receipt.started_ms, 0.0)
        starts = [receipt.started_ms for receipt in receipts]
        self.assertEqual(starts, sorted(starts))  # perf_counter is monotonic; execution is in order


class ReceiptShape(unittest.TestCase):
    def test_receipt_is_frozen_and_json_serializable_after_asdict(self):
        pxc = PxC()
        pxc.set(Part("input.v"), 3)
        pcr = PCR("shape")
        pcr.calc("t", TAKE_VALUE, id="take", value=Part("input.v"), into=Part("out.v"))
        receipts = pcr.run(pxc, observe=True).receipts
        with self.assertRaises(dataclasses.FrozenInstanceError):
            receipts["take"].invocation_id = "other"
        payload = json.dumps({key: asdict(value) for key, value in receipts.items()}, sort_keys=True)
        self.assertNotIn("<function", payload)  # docs/PYTHON-LAB-STEWARDSHIP.md:39
        self.assertNotIn("lambda", payload)
        self.assertIn("runtime-function-body", payload)

    def test_registry_calculations_are_named_functions_not_lambdas(self):
        for address, calculation in ABLATION_REGISTRY.items():
            with self.subTest(address=address):
                self.assertNotEqual(calculation.calculate.__name__, "<lambda>")


if __name__ == "__main__":
    unittest.main()
