"""What survives the only projection pyto offers (PxC.items()/PcrRun) when its rows are reused in PxC?"""
import dataclasses, json, runpy
ns = runpy.run_path("/home/user/DiscStudio-staging/pyto/examples/shared_result_fanout.py")
run, pxc = ns["run"], ns["pxc"]
from pyto import PxC, PQL, Part, Calculation, PCR

rows = [{"address": a, "value": v} for a, v in pxc.items()]          # table of PxC
print("PxC table columns:", sorted(rows[0]), "| rows:", len(rows))
tt = [{"tick": t.name, **dataclasses.asdict(c)} for t in run.ticks for c in t.calculations]  # table of testimony
print("testimony table columns:", sorted(tt[0]))
print("join key between the two tables: testimony.into == pxc.address ->",
      [(r["into"], any(x["address"] == r["into"] for x in rows)) for r in tt])
print("what the testimony table lacks: resolved input VALUES, result value, input version/digest, run id, timestamp, tick index in results")
print("what the PxC table lacks: producer id, calculation address, run membership ->", "no such columns")
# re-use projection rows in a fresh PxC
fresh = PxC()
for r in rows: fresh.set(r["address"], r["value"])
print("re-inserted into fresh PxC; PQL sees same addresses:", [m.address for m in PQL.prefix("px.card.").matches(fresh)])
print("value identity preserved (same object, no copy):", fresh.get("px.card.single") is pxc.get("px.card.single"))
print("provenance after re-insert: PxC has no per-address writer/producer record ->", [m for m in dir(fresh) if not m.startswith('__')])
# JSON round trip of PcrRun testimony (what compositionEvidence does): results dropped or stringified
js = json.dumps({"pcr": run.pcr, "ticks": [dataclasses.asdict(t) for t in run.ticks]})
back = json.loads(js)
print("testimony JSON round trip keeps:", sorted(back["ticks"][1]["calculations"][0]), "| drops: results")
print("PcrRun.results JSON-able here?", end=" ")
try: json.dumps(run.results); print("yes (this example only has str/dict values)")
except TypeError as e: print("no:", e)
