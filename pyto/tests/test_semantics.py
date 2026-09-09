"""Characterization tests for pyto 0.1.0's fail-loud and silent rules (ULTRACODE-WEEK Day 1, lane B).

Every test docstring names the library lines it characterizes and the one-line
library mutation (file, line, change) that makes the test fail.  The mutation
lens applies each mutation to a scratch copy of src/pyto (never the repo) and
requires the named test to fail against it; a test that survives its mutation
is deleted, not kept (ULTRACODE-WEEK.md kill criteria, Day 1).

Sources: scratchpad/probe_rules.py, probe_projection.py, probe_roundtrip.py
(reader phase), core.py, pcr.py, pql.py, graph.py at a4dc559.

Every Calculation body is a named module-level function held in REGISTRY; no anonymous functions.
"""

from __future__ import annotations

import dataclasses
import unittest

from pyto import (
    Calculation,
    Part,
    PCR,
    Pcr,
    PcrRun,
    PQL,
    PxC,
    PxWrite,
    ResultRef,
)


# --- module-level calculation bodies (named functions only) --------------------


def identity(args):
    return args["value"]


def const_one(args):
    return 1


def const_two(args):
    return 2


def const_auto(args):
    return "auto"


def const_b_wins(args):
    return "B-wins"


def const_dup_id(args):
    return "dup-id"


def boom(args):
    raise RuntimeError("boom")


def render_disc(args):
    return f"<svg data-disc='{args['request']['disc']}' />"


def compose_single(args):
    return {"layout": args["layout"], "art": args["art"]}


def compose_battle(args):
    return {"layout": args["layout"], "leftArt": args["art"]}


def address_contains_a(match):
    return "a" in match.address


REGISTRY = {
    "fn.identity": Calculation("fn.identity", identity),
    "fn.one": Calculation("fn.one", const_one),
    "fn.auto": Calculation("fn.auto", const_auto),
    "fn.const.b": Calculation("fn.const.b", const_b_wins),
    "fn.const.dup": Calculation("fn.const.dup", const_dup_id),
    "fn.boom": Calculation("fn.boom", boom),
    "fn.disc.render": Calculation("fn.disc.render", render_disc),
    "fn.card.single.compose": Calculation("fn.card.single.compose", compose_single),
    "fn.card.battle.compose": Calculation("fn.card.battle.compose", compose_battle),
}

IDENT = REGISTRY["fn.identity"]
SRC = Part("px.src")
OUT = Part("px.out")


def fanout_pcr():
    """The examples/shared_result_fanout.py program authored with executable PCR."""
    disc_request = Part("input.disc.request")
    disc_art = Part("px.disc.art.svg")
    program = PCR("disc-cards")
    program.calc("Art", REGISTRY["fn.disc.render"], id="render-disc", request=disc_request, into=disc_art)
    program.calc(
        "Cards",
        REGISTRY["fn.card.single.compose"],
        id="single-card",
        art=disc_art,
        args={"layout": "art-above-numbers"},
        into=Part("px.card.single"),
    )
    program.calc(
        "Cards",
        REGISTRY["fn.card.battle.compose"],
        id="battle-card",
        art=disc_art,
        args={"layout": "side-by-side"},
        into=Part("px.card.battle"),
    )
    return program


def fanout_graph():
    """The same program authored with the non-executing graph Pcr (graph.py)."""
    graph = Pcr("disc-cards")
    graph.calc("Art", "fn.disc.render", id="render-disc", request=graph.part("input.disc.request"), into="px.disc.art.svg")
    graph.calc(
        "Cards",
        "fn.card.single.compose",
        id="single-card",
        art=graph.part("px.disc.art.svg"),
        args={"layout": "art-above-numbers"},
        into="px.card.single",
    )
    graph.calc(
        "Cards",
        "fn.card.battle.compose",
        id="battle-card",
        art=graph.part("px.disc.art.svg"),
        args={"layout": "side-by-side"},
        into="px.card.battle",
    )
    return graph


class ConstructorRulesTest(unittest.TestCase):
    def test_constructor_rules_part_address_non_empty(self):
        """core.py:18-19: Part('') raises ValueError; any non-empty prefix is accepted (no 'px.' rule).

        Mutation: core.py:18 `if not self.address:` -> `if False:` (Part('') is then accepted).
        """
        with self.assertRaisesRegex(ValueError, "non-empty"):
            Part("")
        self.assertEqual(Part("no.prefix.rule").address, "no.prefix.rule")
        self.assertEqual(str(Part("px.a")), "px.a")

    def test_constructor_rules_calculation_fn_prefix(self):
        """core.py:33-34: Calculation address must start with 'fn.'; the callable is not inspected.

        Mutation: core.py:33 `startswith("fn.")` -> `startswith("")` (a bare 'double' address is accepted).
        """
        with self.assertRaisesRegex(ValueError, "must start with 'fn.'"):
            Calculation("double", identity)
        self.assertEqual(Calculation("fn.double", identity)({"value": 3}), 3)


class PxCRulesTest(unittest.TestCase):
    def test_pxc_get_missing_raises_keyerror(self):
        """core.py:58-59: PxC.get of an unproduced address raises KeyError (fail-loud); has() stays False.

        Mutation: core.py:59 `raise KeyError(...)` -> `return None`.
        """
        pxc = PxC()
        self.assertFalse(pxc.has("px.missing"))
        with self.assertRaisesRegex(KeyError, "has not been produced"):
            pxc.get("px.missing")
        with self.assertRaises(KeyError):
            pxc.get(Part("px.missing"))

    def test_pxc_set_kinds_new_address_then_replacement_without_versioning(self):
        """core.py:62-66: set returns PxWrite kind 'new-address' first, 'replacement' after; the old value
        is overwritten in place (one address, no version history).

        Mutation: core.py:64 swap the kinds (`"new-address" if address in self._values else "replacement"`).
        """
        pxc = PxC()
        self.assertEqual(pxc.set("px.a", 1), PxWrite("px.a", "new-address"))
        self.assertEqual(pxc.set(Part("px.a"), 2), PxWrite("px.a", "replacement"))
        self.assertEqual(pxc.get("px.a"), 2)
        self.assertEqual(pxc.addresses(), ("px.a",))

    def test_pxc_register_same_callable_is_idempotent(self):
        """core.py:68-72: re-registering the same object, or a new Calculation wrapping the same callable,
        is accepted silently.

        Mutation: core.py:70 `current is not None and current.calculate is not calculation.calculate`
        -> `current is not None` (any second registration raises).
        """
        pxc = PxC()
        first = Calculation("fn.x", const_one)
        pxc.register(first)
        pxc.register(first)
        pxc.register(Calculation("fn.x", const_one))
        self.assertEqual(pxc.call("fn.x", {}), 1)

    def test_pxc_register_conflict_on_different_callable(self):
        """core.py:70-71: registering a different callable under an already-registered address raises
        ValueError and leaves the first registration in place.

        Mutation: core.py:70 `if current is not None and ...:` -> `if False:` (silent overwrite).
        """
        pxc = PxC()
        pxc.register(Calculation("fn.x", const_one))
        with self.assertRaisesRegex(ValueError, "already registered"):
            pxc.register(Calculation("fn.x", const_two))
        self.assertEqual(pxc.call("fn.x", {}), 1)

    def test_pxc_call_unregistered_string_raises(self):
        """core.py:81-82: PxC.call by address string with nothing registered raises KeyError.

        Mutation: core.py:82 `raise KeyError(...)` -> `return None`.
        """
        pxc = PxC()
        with self.assertRaisesRegex(KeyError, "not registered"):
            pxc.call("fn.nope", {})

    def test_pxc_call_autoregisters_object_but_not_string(self):
        """core.py:77-80: PxC.call with an unregistered Calculation object registers it as a side effect,
        so a later call by string succeeds.

        Mutation: core.py:79 `self.register(calculation)` -> `pass` (the follow-up string call raises).
        """
        pxc = PxC()
        self.assertEqual(pxc.call(REGISTRY["fn.auto"], {}), "auto")
        self.assertEqual(pxc.call("fn.auto", {}), "auto")


class PQLRulesTest(unittest.TestCase):
    def test_pql_part_missing_is_silent_until_one(self):
        """pql.py:31-33,63-67,69-73: PQL.part of an unproduced address matches nothing (silent);
        one() raises ValueError; optional() returns None.

        Mutation: pql.py:65 `if len(matches) != 1:` -> `if len(matches) > 1:` (one() on zero matches
        then raises IndexError instead of ValueError).
        """
        pxc = PxC()
        query = PQL.part(Part("px.nope"))
        self.assertEqual(query.matches(pxc), ())
        self.assertIsNone(query.optional(pxc))
        with self.assertRaisesRegex(ValueError, "expected exactly 1 match; got 0"):
            query.one(pxc)

    def test_pql_one_and_optional_reject_multiple_matches(self):
        """pql.py:63-67,69-73: with two matches both one() and optional() raise ValueError; values()
        returns all.

        Mutation: pql.py:71 `if len(matches) > 1:` -> `if len(matches) > 2:` (optional() returns the
        first of two).
        """
        pxc = PxC()
        pxc.set("px.a", 1)
        pxc.set("px.b", 2)
        query = PQL.prefix("px.")
        self.assertEqual(query.values(pxc), (1, 2))
        with self.assertRaisesRegex(ValueError, "expected exactly 1 match; got 2"):
            query.one(pxc)
        with self.assertRaisesRegex(ValueError, "expected at most 1 match; got 2"):
            query.optional(pxc)

    def test_pql_prefix_must_be_non_empty(self):
        """pql.py:39-40: PQL.prefix('') raises ValueError at construction.

        Mutation: pql.py:39 `if not prefix:` -> `if False:`.
        """
        with self.assertRaisesRegex(ValueError, "prefix must be non-empty"):
            PQL.prefix("")

    def test_pql_where_refines_and_matches_are_sorted_by_address(self):
        """pql.py:42-45,49-55 and core.py:88-89: prefix selection iterates PxC.items(), which is sorted by
        address regardless of insertion order; where() refines in ordinary Python.

        Mutation: core.py:89 `for address in sorted(self._values)` -> `for address in self._values`
        (insertion order leaks through).
        """
        pxc = PxC()
        pxc.set("px.b", "B")
        pxc.set("px.a", "A")
        pxc.set("other.c", "C")
        self.assertEqual([m.address for m in PQL.prefix("px.").matches(pxc)], ["px.a", "px.b"])
        refined = PQL.prefix("px.").where(address_contains_a)
        self.assertEqual(refined.values(pxc), ("A",))
        self.assertEqual(refined.description, "px.* where \u2026")

    def test_pql_cannot_see_calculations(self):
        """pql.py:42-45 read only PxC.items() (core.py:88-89, the _values dict); registration goes to
        _calculations (core.py:72), so PQL.prefix('fn.') is empty even with calculations registered.

        Mutation: core.py:72 `self._calculations[calculation.address] = calculation`
        -> `self._values[calculation.address] = calculation` (registry folded into the store).
        """
        pxc = PxC()
        pxc.register(REGISTRY["fn.one"])
        pxc.call(REGISTRY["fn.auto"], {})
        self.assertEqual(PQL.prefix("fn.").matches(pxc), ())
        self.assertEqual(pxc.addresses(), ())
        self.assertEqual(pxc.call("fn.one", {}), 1)


class PCRDeclarationRulesTest(unittest.TestCase):
    def test_pcr_duplicate_id_rejected_across_ticks(self):
        """pcr.py:109-110: PCR.calc rejects an id already used in any tick of the same PCR.

        Mutation: pcr.py:109 `if id in self._ids:` -> `if False:` (the Tick-level check at pcr.py:43 only
        sees its own tick, so the cross-tick duplicate is then accepted).
        """
        pcr = PCR("p")
        pcr.calc("A", IDENT, id="one", value=SRC, into=OUT)
        with self.assertRaisesRegex(ValueError, "duplicate calculation id 'one'"):
            pcr.calc("B", IDENT, id="one", value=SRC)

    def test_pcr_multiple_writers_rejected(self):
        """pcr.py:118-123: a second invocation declaring the same `into` address raises ValueError.

        Mutation: pcr.py:121 `if prior is not None:` -> `if False:`.
        """
        pcr = PCR("p")
        pcr.calc("A", IDENT, id="one", value=SRC, into=OUT)
        with self.assertRaisesRegex(ValueError, "multiple writers for 'px.out'"):
            pcr.calc("B", IDENT, id="two", value=SRC, into="px.out")

    def test_part_binding_rewritten_to_result_ref_when_writer_declared_first(self):
        """pcr.py:112-116: consuming a Part that already has a writer in this PCR rewrites the binding to
        ResultRef(writer id) at declaration time; testimony then records 'fn:<id>' (pcr.py:157).

        Mutation: pcr.py:114 `and source.address in self._writers` -> `and False`.
        """
        pcr = PCR("postwrite")
        pcr.calc("T1", IDENT, id="writer", value=SRC, into="px.mid")
        pcr.calc("T2", IDENT, id="reader", value=Part("px.mid"))
        binding = pcr.ticks[1].calculations[0].bindings["value"].source
        self.assertEqual(binding, ResultRef("writer"))
        pxc = PxC()
        pxc.set(SRC, "s")
        run = pcr.run(pxc)
        self.assertEqual(run.ticks[1].calculations[0].inputs, {"value": "fn:writer"})

    def test_part_binding_not_rewritten_when_writer_declared_after_consumer(self):
        """Silent rule, pcr.py:112-116: the rewrite happens only at the consumer's declaration, so a
        writer declared later leaves the consumer bound to the Part; at run (pcr.py:147-149) it reads the
        stale PxC value and testifies 'px:'.

        Mutation: pcr.py:149 `input_refs[name] = f"px:{source.address}"` ->
        `input_refs[name] = f"fn:{self._writers[source.address]}" if source.address in self._writers
        else f"px:{source.address}"` (testimony claims fn: provenance the reader never received).
        """
        pcr = PCR("prewrite")
        pcr.calc("T1", IDENT, id="reader", value=Part("px.mid"), into="px.reader.out")
        pcr.calc("T2", IDENT, id="writer", value=SRC, into="px.mid")
        self.assertEqual(pcr.ticks[0].calculations[0].bindings["value"].source, Part("px.mid"))
        pxc = PxC()
        pxc.set(SRC, "s")
        pxc.set("px.mid", "STALE")
        run = pcr.run(pxc)
        self.assertEqual(run.ticks[0].calculations[0].inputs, {"value": "px:px.mid"})
        self.assertEqual(run.results["reader"], "STALE")
        self.assertEqual(pxc.get("px.mid"), "s")

    def test_non_part_binding_source_fails_at_run(self):
        """Silent rule (critic gap 13): PCR.calc (pcr.py:112-116) and Tick.calc (pcr.py:46) accept any
        object as a binding source; only run (pcr.py:147-151) discriminates Part vs 'else', so a PQL
        source fails at run with AttributeError (no .calculation_id).

        Mutation: insert after pcr.py:113 `if not isinstance(source, (Part, ResultRef)): raise
        TypeError(name)` (declaration then fails loudly, as graph.py:63-64 does).
        """
        pcr = PCR("badinput")
        ref = pcr.calc("A", IDENT, id="q", value=PQL.part(SRC))
        self.assertEqual(ref, ResultRef("q"))
        pxc = PxC()
        pxc.set(SRC, 1)
        with self.assertRaises(AttributeError):
            pcr.run(pxc)

    def test_tick_calc_rejects_duplicate_id_within_tick(self):
        """pcr.py:43-44: Tick.calc rejects an id already present in that same tick.

        Mutation: pcr.py:43 `if any(existing.id == id for existing in self.calculations):` -> `if False:`.
        """
        pcr = PCR("p")
        pcr.calc("A", IDENT, id="one", value=SRC, into=OUT)
        with self.assertRaisesRegex(ValueError, "Tick 'A' has duplicate calculation id 'one'"):
            pcr.tick("A").calc(IDENT, id="one", value=SRC)

    def test_tick_calc_bypasses_pcr_duplicate_id_rule(self):
        """Silent rule, pcr.py:33-56 vs 109-110,132: pcr.tick(name).calc skips PCR._ids, so an id used in
        another tick is accepted and run overwrites results[id] (pcr.py:162).

        Mutation: pcr.py:162 `results[invocation.id] = value` -> `results.setdefault(invocation.id, value)`.
        """
        pcr = PCR("bypass")
        pcr.calc("A", IDENT, id="w1", value=SRC, into=OUT)
        pcr.tick("B").calc(REGISTRY["fn.const.dup"], id="w1")
        pxc = PxC()
        pxc.set(SRC, "orig")
        run = pcr.run(pxc)
        self.assertEqual([c.id for t in run.ticks for c in t.calculations], ["w1", "w1"])
        self.assertEqual(run.results["w1"], "dup-id")

    def test_tick_calc_bypasses_pcr_multiple_writer_rule(self):
        """Silent rule, pcr.py:33-56 vs 118-123: pcr.tick(name).calc skips PCR._writers, so a second
        writer for the same Part is accepted and the last invocation's value wins in the PxC (pcr.py:164).

        Mutation: pcr.py:164 `pxc.set(invocation.into, value)` ->
        `pxc.has(invocation.into) or pxc.set(invocation.into, value)` (first writer wins).
        """
        pcr = PCR("bypass")
        pcr.calc("A", IDENT, id="w1", value=SRC, into=OUT)
        pcr.tick("B").calc(REGISTRY["fn.const.b"], id="w2", into=OUT)
        pxc = PxC()
        pxc.set(SRC, "orig")
        run = pcr.run(pxc)
        self.assertEqual(run.results, {"w1": "orig", "w2": "B-wins"})
        self.assertEqual(pxc.get(OUT), "B-wins")


class PCRRunRulesTest(unittest.TestCase):
    def test_args_silently_override_same_named_bound_inputs(self):
        """Silent rule, pcr.py:159-160: call_args.update(invocation.args) lets an args key shadow a bound
        input of the same name; testimony still records both the input ref and the arg.

        Mutation: pcr.py:160 `call_args.update(invocation.args)` ->
        `call_args = {**invocation.args, **call_args}` (bound inputs win).
        """
        pcr = PCR("override")
        pcr.calc("A", IDENT, id="i", value=SRC, args={"value": "from-args"})
        pxc = PxC()
        pxc.set(SRC, "from-part")
        run = pcr.run(pxc)
        self.assertEqual(run.results["i"], "from-args")
        testimony = run.ticks[0].calculations[0]
        self.assertEqual(testimony.inputs, {"value": "px:px.src"})
        self.assertEqual(testimony.args, {"value": "from-args"})

    def test_result_ref_to_unavailable_id_fails_only_at_run(self):
        """pcr.py:151-155: a ResultRef to an id not yet in results is accepted at declaration and raises
        ValueError at run, even when the producer is declared later in the same tick.

        Mutation: pcr.py:151 `if source.calculation_id not in results:` -> `if False:` (a KeyError from
        pcr.py:156 replaces the ValueError).
        """
        pcr = PCR("order")
        ref = pcr.calc("A", IDENT, id="uses-later", value=ResultRef("declared-later"))
        self.assertEqual(ref, ResultRef("uses-later"))
        pcr.calc("A", IDENT, id="declared-later", value=SRC)
        pxc = PxC()
        pxc.set(SRC, 1)
        with self.assertRaisesRegex(ValueError, "unavailable result 'declared-later'"):
            pcr.run(pxc)

    def test_tick_order_is_first_mention_not_producer_declaration(self):
        """pcr.py:91-96,139: ticks execute in the order they were first named, so a consumer in tick B
        declared before its producer in tick A runs first and fails with 'unavailable result'.

        Mutation: pcr.py:95 `self.ticks.append(tick)` -> `self.ticks.insert(0, tick)`.
        """
        pcr = PCR("order2")
        pcr.calc("B", IDENT, id="consumer", value=ResultRef("producer"))
        pcr.calc("A", IDENT, id="producer", value=SRC)
        self.assertEqual([t.name for t in pcr.ticks], ["B", "A"])
        pxc = PxC()
        pxc.set(SRC, 1)
        with self.assertRaisesRegex(ValueError, "unavailable result 'producer'"):
            pcr.run(pxc)

    def test_missing_part_fails_only_at_run(self):
        """pcr.py:147-148 -> core.py:58-59: a Part binding with no PxC value is accepted at declaration and
        raises KeyError at run.

        Mutation: pcr.py:148 `resolved_inputs[name] = pxc.get(source)` ->
        `resolved_inputs[name] = pxc._values.get(source.address)`.
        """
        pcr = PCR("missing")
        pcr.calc("A", IDENT, id="m", value=Part("px.absent"))
        with self.assertRaisesRegex(KeyError, "has not been produced"):
            pcr.run(PxC())

    def test_run_registers_calculations_and_rejects_conflicting_address(self):
        """pcr.py:142 registers every invocation's Calculation on the PxC (core.py:68-72), so two
        Calculation objects sharing an address with different callables make run raise ValueError.

        Mutation: pcr.py:142 `pxc.register(invocation.calculation)` -> `pass` (PxC.call at pcr.py:161
        then silently runs the first callable for the second invocation).
        """
        pcr = PCR("conflict")
        pcr.calc("A", Calculation("fn.same", const_one), id="c1", value=SRC)
        pcr.calc("A", Calculation("fn.same", const_two), id="c2", value=SRC)
        pxc = PxC()
        pxc.set(SRC, 1)
        with self.assertRaisesRegex(ValueError, "already registered"):
            pcr.run(pxc)

    def test_failure_mid_run_leaves_prior_writes(self):
        """Critic gap 13, pcr.py:161-164: a Calculation raising mid-run propagates its own exception, no
        PcrRun is returned, and `into` writes made by earlier invocations stay in the PxC (no rollback).

        Mutation: pcr.py:164 `pxc.set(invocation.into, value)` ->
        `results.setdefault("__pending__", {}).update({invocation.into.address: value})`
        (publication deferred until the run completes, i.e. rollback on failure).
        """
        pcr = PCR("failing")
        pcr.calc("A", IDENT, id="first", value=SRC, into="px.first")
        pcr.calc("B", REGISTRY["fn.boom"], id="second", value=SRC, into="px.second")
        pcr.calc("C", IDENT, id="third", value=SRC, into="px.third")
        pxc = PxC()
        pxc.set(SRC, "s")
        with self.assertRaisesRegex(RuntimeError, "boom"):
            pcr.run(pxc)
        self.assertEqual(pxc.get("px.first"), "s")
        self.assertFalse(pxc.has("px.second"))
        self.assertFalse(pxc.has("px.third"))

    def test_results_keyed_by_id_not_tick_and_rerun_replaces(self):
        """pcr.py: PcrRun.results is a flat dict keyed by invocation id (no tick segment); PcrRun
        carries no run id and no run-level timestamp; rerunning yields equal testimony.

        Day 2 seam (CHANGES.md): PcrRun gained one trailing, defaulted field, `receipts`.
        The first three fields and their order are unchanged, which is what keeps
        json.dumps([asdict(t) for t in run.ticks]) byte-identical for consumers
        (tests/test_receipts.py::TestimonyBytesUnchanged).

        Mutation: pcr.py:162 `results[invocation.id] = value` ->
        `results[f"{tick.name}/{invocation.id}"] = value`.
        """
        pcr = PCR("rerun")
        pcr.calc("T1", IDENT, id="a", value=SRC, into="px.a")
        pcr.calc("T2", IDENT, id="b", value=SRC, into="px.b")
        pxc = PxC()
        pxc.set(SRC, [1])
        run = pcr.run(pxc)
        self.assertEqual(sorted(run.results), ["a", "b"])
        fields = tuple(f.name for f in dataclasses.fields(PcrRun))
        self.assertEqual(fields[:3], ("pcr", "ticks", "results"))
        self.assertEqual(fields, ("pcr", "ticks", "results", "receipts"))
        self.assertEqual(run.receipts, {})  # observe defaults to False
        self.assertEqual(pcr.run(pxc).ticks, run.ticks)

    def test_cross_pcr_consumer_records_px_not_fn(self):
        """Critic gap 12, pcr.py:88,118-123: the writers map is per PCR, so a second PCR reading a Part
        produced by the first PCR (over the same PxC) binds it as a Part and testifies 'px:', not 'fn:'.

        Mutation: pcr.py:88 `self._writers: dict[str, str] = {}` ->
        `self._writers: dict[str, str] = PCR.__dict__.setdefault("_shared", {})` (writers shared across
        PCRs, the consumer then testifies 'fn:w').
        """
        first = PCR("first")
        first.calc("A", IDENT, id="w", value=SRC, into="px.shared")
        second = PCR("second")
        second.calc("A", IDENT, id="r", value=Part("px.shared"))
        pxc = PxC()
        pxc.set(SRC, "v")
        first.run(pxc)
        run = second.run(pxc)
        self.assertEqual(run.ticks[0].calculations[0].inputs, {"value": "px:px.shared"})
        self.assertEqual(run.results["r"], "v")


class ProjectionTest(unittest.TestCase):
    def test_table_projection_drops_provenance(self):
        """Critic gap 13, core.py:85-89: PxC.items() projects to (address, value) rows only; re-inserting
        the rows into a fresh PxC keeps address and object identity (no copy) but nothing in the row or
        the PxC surface names the producing invocation (that lives only in PcrRun testimony 'into').

        Mutation: core.py:89 `self._values[address]` -> `__import__("copy").deepcopy(self._values[address])`
        (identity across the projection is lost).
        """
        pxc = PxC()
        pxc.set("input.disc.request", {"disc": "mako", "color": "blue"})
        run = fanout_pcr().run(pxc)
        rows = pxc.items()
        self.assertTrue(all(len(row) == 2 for row in rows))
        fresh = PxC()
        for address, value in rows:
            fresh.set(address, value)
        self.assertEqual(fresh.addresses(), pxc.addresses())
        self.assertIs(fresh.get("px.card.single"), pxc.get("px.card.single"))
        self.assertEqual(
            [m.address for m in PQL.prefix("px.card.").matches(fresh)],
            ["px.card.battle", "px.card.single"],
        )
        produced = {c.into for t in run.ticks for c in t.calculations}
        self.assertTrue(produced <= set(fresh.addresses()))
        self.assertEqual(tuple(f.name for f in dataclasses.fields(PxWrite)), ("address", "kind"))
        self.assertEqual(
            [m for m in dir(PxC) if not m.startswith("_")],
            ["addresses", "call", "get", "has", "items", "register", "set"],
        )

    def test_pcr_and_pcr_graph_emit_identical_mermaid(self):
        """Critic gap 16, pcr.py:179-219 vs graph.py:116-151: the fan-out example authored as executable
        PCR and as graph Pcr emits byte-identical Mermaid, including the fn: edges from the rewrite.

        Mutation: pcr.py:197 `f'    {node_id}["{address}"]'` -> `f'    {node_id}("{address}")'`.
        """
        executable = fanout_pcr().mermaid()
        graph = fanout_graph().to_mermaid()
        self.assertEqual(executable, graph)
        self.assertIn("    render-disc -->|art| single-card\n", executable)
        self.assertIn("    render-disc -->|art| battle-card\n", executable)


if __name__ == "__main__":
    unittest.main()
