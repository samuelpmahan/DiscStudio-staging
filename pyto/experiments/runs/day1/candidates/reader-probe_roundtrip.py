"""Can a composition (PCR/Pcr/PQL) be selected and manipulated by another calculation? Probe both directions."""
import dataclasses, json
from pyto import Calculation, Part, PCR, PQL, PxC, Pcr, PcrRun

print("### Are PQL / PCR / Pcr Parts?")
for cls in (PQL, PCR, Pcr, PcrRun):
    print(f"   {cls.__name__}: subclass of Part? {issubclass(cls, Part)}; has 'address'? {'address' in getattr(cls, '__slots__', ()) or hasattr(cls, 'address')}")

print("### Serialization surface")
print("   PCR methods:", [m for m in dir(PCR) if not m.startswith('_')])
print("   Pcr methods:", [m for m in dir(Pcr) if not m.startswith('_')])
print("   PCR has from_dict/to_dict/load?", any(m in dir(PCR) for m in ('to_dict','from_dict','to_json','from_json','load')))
print("   Pcr has from_pcr_dict?", hasattr(Pcr, 'from_pcr_dict'))
print("   PCR <-> Pcr bridge function anywhere?", [n for n in dir(__import__('pyto')) if 'bridge' in n.lower() or 'convert' in n.lower()])

print("### Round trip attempt 1: store an executable PCR as a PxC value, select it with PQL, have a Calculation extend & run it")
pxc = PxC()
src = Part("px.src"); pxc.set(src, 5)
double = Calculation("fn.double", lambda a: a["value"] * 2)
inner = PCR("inner"); inner.calc("A", double, id="d", value=src, into="px.doubled")
pxc.set("pcr.inner", inner)   # PxC stores Any -> a PCR object is just a value
selected = PQL.prefix("pcr.").one(pxc)
print("   PQL selected:", type(selected).__name__, selected.name, "is inner:", selected is inner)

def extend_and_run(args):
    prog = args["program"]; store = args["store"]
    prog.calc("B", Calculation("fn.inc", lambda a: a["value"] + 1), id="inc", value=Part("px.doubled"), into="px.result")
    return prog.run(store)
meta = Calculation("fn.meta.extendAndRun", extend_and_run)
outer = PCR("outer")
outer.calc("Meta", meta, id="run-inner", program=Part("pcr.inner"), args={"store": pxc}, into="px.inner.run")
outer_run = outer.run(pxc)
inner_run = pxc.get("px.inner.run")
print("   outer testimony:", dataclasses.asdict(outer_run.ticks[0].calculations[0]))
print("   inner PcrRun produced inside outer:", json.dumps(dataclasses.asdict(inner_run), default=str))
print("   px.result:", pxc.get("px.result"))
print("   NOTE: the inner run's testimony is NOT nested in outer's testimony; outer only records 'px:pcr.inner' as an input ref and 'px.inner.run' as into.")
print("   NOTE: the store had to be passed via args (side channel); PCR.run gives a Calculation no access to the PxC it runs in.")

print("### Round trip attempt 2: graph Pcr JSON -> back to Pcr or PCR?")
g = Pcr("g"); g.calc("A", "fn.double", id="d", value=g.part("px.src"), into="px.doubled")
d = g.to_pcr_dict(); print("   Pcr JSON:", json.dumps(d))
try:
    Pcr.from_pcr_dict(d)
except AttributeError as e:
    print("   Pcr.from_pcr_dict MISSING:", e)
print("   PCR JSON export MISSING; Pcr cannot execute (call is a str, no callable):", type(d["Ticks"][0]["Calculations"][0]["call"]))

print("### Round trip attempt 3: same graph authored in PCR and Pcr -> mermaid equal?")
p = PCR("g"); p.calc("A", double, id="d", value=Part("px.src"), into="px.doubled")
print("   mermaid identical:", p.mermaid() == g.to_mermaid())

print("### Can a Calculation be selected? Calculations live in PxC._calculations (private); PQL only reads _values")
print("   PQL.prefix('fn.').matches(pxc) ->", PQL.prefix("fn.").matches(pxc))
print("   pxc._calculations keys:", sorted(pxc._calculations))
print("   public accessor for registered calculations?", [m for m in dir(PxC) if 'calc' in m.lower() and not m.startswith('_')])
