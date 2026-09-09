"""Probe every fail-loud rule and silent behavior in pyto core. Each block prints an outcome."""
import dataclasses, json
from pyto import Calculation, Part, PCR, PQL, PxC, Pcr, ResultRef, Tick
from pyto.pcr import Invocation

def expect(label, fn, exc=None):
    try:
        out = fn()
    except Exception as e:
        print(f"[{label}] RAISED {type(e).__name__}: {e}")
        return e
    else:
        print(f"[{label}] {'SILENT/OK' if exc else 'ok'} -> {out!r}")
        return out

print("### FAIL-LOUD: constructors")
expect("Part('') empty", lambda: Part(""), True)
expect("Calculation addr without fn.", lambda: Calculation("double", lambda a: a), True)
expect("Part addr any prefix accepted", lambda: Part("no.prefix.rule"))

print("### FAIL-LOUD / SILENT: PxC")
pxc = PxC()
expect("PxC.get missing", lambda: pxc.get("px.missing"), True)
expect("PxC.set new", lambda: pxc.set("px.a", 1))
expect("PxC.set REPLACEMENT is silent, returns PxWrite kind", lambda: pxc.set("px.a", 2))
c1 = Calculation("fn.x", lambda a: 1); c2 = Calculation("fn.x", lambda a: 2)
pxc.register(c1)
expect("register same object twice (idempotent)", lambda: pxc.register(c1))
expect("register same address, different callable", lambda: pxc.register(c2), True)
expect("call by string, unregistered", lambda: pxc.call("fn.nope", {}), True)
expect("call by Calculation object, unregistered -> auto-registers silently", lambda: pxc.call(Calculation("fn.auto", lambda a: 'auto'), {}))
print("   registered now:", sorted(pxc._calculations))

print("### FAIL-LOUD: PCR declaration")
pcr = PCR("p"); src = Part("px.src"); out = Part("px.out")
ident = Calculation("fn.identity", lambda a: a["value"])
pcr.calc("A", ident, id="one", value=src, into=out)
expect("duplicate id across ticks", lambda: pcr.calc("B", ident, id="one", value=src), True)
expect("multiple writers", lambda: pcr.calc("B", ident, id="two", value=src, into=out), True)
expect("duplicate id in Tick.calc directly", lambda: pcr.tick("A").calc(ident, id="one", value=src), True)

print("### SILENT: bypass via Tick.calc (no PCR-level writer/id bookkeeping)")
pcr2 = PCR("bypass"); pcr2.calc("A", ident, id="w1", value=src, into=out)
r = expect("Tick.calc second writer for px.out in tick B (NOT rejected)", lambda: pcr2.tick("B").calc(Calculation("fn.const", lambda a: 'B-wins'), id="w2", into=out))
r = expect("Tick.calc reuse id 'w1' in tick B (NOT rejected -> results dict overwrite)", lambda: pcr2.tick("B").calc(Calculation("fn.const2", lambda a: 'dup-id'), id="w1", into=None))
px2 = PxC(); px2.set(src, "orig")
run2 = pcr2.run(px2)
print("   results keys:", list(run2.results), "results['w1'] =", run2.results["w1"], "| px.out =", px2.get(out))
print("   _writers only knows:", pcr2._writers)

print("### SILENT: args override resolved inputs (call_args.update)")
pcr3 = PCR("override"); px3 = PxC(); px3.set(src, "from-part")
pcr3.calc("A", ident, id="i", value=src, args={"value": "from-args"})
print("   result:", pcr3.run(px3).results["i"], "| testimony inputs/args:", dataclasses.asdict(pcr3.run(px3).ticks[0].calculations[0]))

print("### SILENT: PQL.where description truncation; PQL misc")
q = PQL.prefix("px.").where(lambda m: True).where(lambda m: "a" in m.address)
print("   description:", repr(q.description))
expect("PQL.prefix('')", lambda: PQL.prefix(""), True)
expect("PQL.part missing -> matches empty (silent)", lambda: PQL.part("px.nope").matches(pxc))
expect("PQL.part missing .one()", lambda: PQL.part("px.nope").one(pxc), True)
expect("PQL.optional >1", lambda: PQL.prefix("px").optional(px2), True)
print("   PQL selection order is sorted address:", [m.address for m in PQL.prefix("px").matches(px2)])

print("### SILENT: PCR.run re-run recomputes and replaces; results not keyed by tick; aliasing")
px4 = PxC(); px4.set(src, [1])
pcr4 = PCR("rerun"); pcr4.calc("T1", ident, id="a", value=src, into="px.a"); pcr4.calc("T2", ident, id="b", value=Part("px.a"), into="px.b")
run_a = pcr4.run(px4); run_b = pcr4.run(px4)
print("   run twice, identical testimony:", run_a.ticks == run_b.ticks, "| results keys (flat, no tick):", list(run_a.results))
print("   no run id/timestamp fields:", [f.name for f in dataclasses.fields(run_a)])
run_a.results["a"].append(99)
print("   mutating results['a'] mutates PxC px.src:", px4.get(src), "(aliasing, no copy)")
print("   PcrRun frozen but results dict mutable:", type(run_a.results))

print("### SILENT: PCR.calc does not type-check inputs (Pcr.calc does)")
pcr5 = PCR("badinput")
expect("PCR.calc with a PQL as input source (accepted at declaration)", lambda: pcr5.calc("A", ident, id="q", value=PQL.part(src)))
expect("... fails only at run", lambda: pcr5.run(px4), True)
expect("Pcr.calc with str input rejects at declaration", lambda: Pcr("g").calc("A", "fn.x", id="q", value="px.src"), True)

print("### FAIL-LOUD at run only: order/availability, missing Part, conflicting Calculation address")
pcr6 = PCR("order")
later = ResultRef("declared-later")
pcr6.calc("A", ident, id="uses-later", value=later)           # references result declared later in tick A
pcr6.calc("A", ident, id="declared-later", value=src)
expect("ResultRef to later calc in same tick", lambda: pcr6.run(px4), True)
pcr7 = PCR("order2")
pcr7.calc("B", ident, id="consumer", value=ResultRef("producer"))  # tick B declared first
pcr7.calc("A", ident, id="producer", value=src)                    # tick A declared second but runs... ?
expect("tick order = first-mention order (B before A) -> unavailable", lambda: pcr7.run(px4), True)
pcr8 = PCR("missing"); pcr8.calc("A", ident, id="m", value=Part("px.absent"))
expect("missing Part at run", lambda: pcr8.run(px4), True)
pcr9 = PCR("conflict"); pcr9.calc("A", Calculation("fn.same", lambda a: 1), id="c1", value=src); pcr9.calc("A", Calculation("fn.same", lambda a: 2), id="c2", value=src)
expect("two Calculations same address different lambdas -> run raises", lambda: pcr9.run(px4), True)

print("### Part consumed BEFORE its writer is declared stays px: (declaration-order normalization)")
pcr10 = PCR("prewrite"); px10 = PxC(); px10.set(src, "s"); px10.set("px.mid", "STALE")
pcr10.calc("T1", ident, id="reader", value=Part("px.mid"), into="px.reader.out")
pcr10.calc("T2", ident, id="writer", value=src, into="px.mid")
r10 = pcr10.run(px10)
print("   reader testimony inputs:", r10.ticks[0].calculations[0].inputs, "| reader got:", r10.results["reader"], "| px.mid after:", px10.get("px.mid"))
pcr11 = PCR("postwrite"); pcr11.calc("T1", ident, id="writer", value=src, into="px.mid"); pcr11.calc("T2", ident, id="reader", value=Part("px.mid"))
print("   reversed declaration -> reader testimony:", pcr11.run(px10).ticks[1].calculations[0].inputs)

print("### Reuse across PCRs: second PCR reading a Part written by first sees px: not fn:")
pcrA = PCR("first"); pcrA.calc("A", ident, id="w", value=src, into="px.shared")
pcrB = PCR("second"); pcrB.calc("A", ident, id="r", value=Part("px.shared"))
pxAB = PxC(); pxAB.set(src, "v"); pcrA.run(pxAB); rb = pcrB.run(pxAB)
print("   second PCR testimony:", rb.ticks[0].calculations[0].inputs, "-> provenance across PCRs is by address only, no version/digest")
