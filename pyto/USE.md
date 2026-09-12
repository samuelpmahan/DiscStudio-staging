# Using pyto

Ten minutes, top to bottom. Every Python block below is run by `tests/test_use.py`
in a fresh process, and its printed output is compared byte for byte with the text
block underneath it. If a paragraph here lies, that test is red and it names the
paragraph.

You need five things, and they arrive in this order: a **store** (`PxC`), a
**Part**, a **Calculation**, a **program** (`PCR`), and the **record** a run
leaves behind. `PQL` reads the store back. Nothing else is required to write a
real program.

## 1. The store

`PxC` is one dictionary with manners: a value lives at a dotted **address**, and
the store refuses to guess. `set` puts a value there, `get` takes it out and
raises when it was never produced, `has` asks without raising, `addresses` lists
what is there, sorted.

An address has three roots and only three: `px` for values, `fn` for pure
calculations, `oc` for effects. `pyto.address.check` describes that rule; it is a
reader, not a gate, so nothing in the kernel refuses an address for it today
(only a Calculation's `fn.`/`oc.` prefix is enforced, in section 3).

```python
from pyto import Part, PxC
from pyto.address import ROOTS, check

pxc = PxC()
prices = Part("px.order.prices")
pxc.set(prices, [250, 175, 90])

print("roots:      ", ROOTS)
print("has prices: ", pxc.has(prices))
print("prices:     ", pxc.get(prices))
print("has total:  ", pxc.has("px.order.total"))
print("addresses:  ", pxc.addresses())
try:
    pxc.get("px.order.total")
except KeyError as missing:
    print("get total:  ", missing)
print("check:      ", check("px.order.total"))
print("check:      ", check("stuff.total"))
```

```text
roots:       ('px', 'fn', 'oc')
has prices:  True
prices:      [250, 175, 90]
has total:   False
addresses:   ('px.order.prices',)
get total:   "PxC: Part 'px.order.total' has not been produced"
check:       ()
check:       ("unknown root 'stuff': the only roots are px, fn, oc (px for values, fn for pure, oc for effects)",)
```

`get` on a missing address is the whole point of the store: a program that reads
something nobody computed stops there instead of carrying a `None` forward.

## 2. A Part

A `Part` is a name, not a value. It is a frozen dataclass whose only field is the
address, so **identity is the address**: two `Part` objects with the same address
are equal, name the same cell, and are interchangeable with the bare string
everywhere the store takes one. The value is in the store and changes; the Part
does not.

```python
from pyto import Part, PxC

total = Part("px.order.total")
also_total = Part("px.order.total")
print("equal:      ", total == also_total)
print("same object:", total is also_total)
print("str:        ", str(total), "| address:", total.address)

pxc = PxC()
pxc.set(total, 515)
print("through the other Part:  ", pxc.get(also_total))
print("through the bare address:", pxc.get("px.order.total"))

write = pxc.set("px.order.total", 999)
print("write:      ", write)
print("now:        ", pxc.get(total))

try:
    Part("")
except ValueError as refused:
    print("empty:      ", refused)
```

```text
equal:       True
same object: False
str:         px.order.total | address: px.order.total
through the other Part:   515
through the bare address: 515
write:       PxWrite(address='px.order.total', kind='replacement')
now:         999
empty:       Part address must be non-empty
```

`set` hands back a `PxWrite` saying which address it touched and whether the
address was new or replaced. That is the same fact a receipt records in section 3.

## 3. A Calculation

A `Calculation` is a named pure function of **one argument**: a mapping of named
inputs. Its address must start with `fn.` (pure) or with `oc.` — that is the one
address rule the kernel enforces, and it is what makes a calculation
distinguishable from a value at a glance.

An `oc.` address is an **OperationalCalculation**: the one kind that may touch
the world, and only through the `Effects` handle the run hands it as
`args["effects"]` — `write_text`, `read_text`, `now_ms`, `random`, `env`, every
path relative to the run's `effects_root`, and an `fn.` Calculation gets no
handle at all. Every effect it performs is appended to a ledger that lands on the
invocation's receipt and in the run record, so a replay plays the recorded value
back instead of re-running the effect and refuses a ledger that does not match;
`src/pyto/effects.py` is the whole syscall table and says what each verb records.

A Calculation returns **one result**, published at the one address in `into`; or
it declares **several** addresses with `into=[...]` and returns them together, as
a mapping keyed by those addresses or as a sequence in the declared order. Both
are checked: a missing key, a spare key or a wrong length is refused rather than
published.

With `observe=True` a run also leaves a **receipt** per invocation: what it
resolved, what it wrote, and a digest per published address.

```python
from pyto import Calculation, PCR, Part, PxC


def add_up(args):
    return sum(args["prices"])


def split_bill(args):
    tax = round(args["subtotal"] * args["rate"], 2)
    return {"px.order.tax": tax, "px.order.total": round(args["subtotal"] + tax, 2)}


ADD_UP = Calculation("fn.order.add_up", add_up)
SPLIT = Calculation("fn.order.split", split_bill)

print("by hand:         ", ADD_UP({"prices": [250, 175, 90]}))

pxc = PxC()
pxc.register(ADD_UP)
print("through the store:", pxc.call("fn.order.add_up", {"prices": [1, 2]}))

try:
    Calculation("order.add_up", add_up)
except ValueError as refused:
    print("no prefix:       ", refused)

pxc.set(Part("px.order.prices"), [250, 175, 90])
pcr = PCR("order")
pcr.calc("Sum", ADD_UP, id="sum", into=Part("px.order.subtotal"), prices=Part("px.order.prices"))
pcr.calc(
    "Split", SPLIT, id="split",
    into=[Part("px.order.tax"), Part("px.order.total")],
    subtotal=Part("px.order.subtotal"), args={"rate": 0.08},
)
run = pcr.run(pxc, observe=True)

print("one result:      ", run.results["sum"], "->", pxc.get("px.order.subtotal"))
print("several results: ", run.results["split"])
print("published:       ", pxc.get("px.order.tax"), pxc.get("px.order.total"))

receipt = run.receipts["sum"]
print("declared_consumes:", receipt.declared_consumes)
print("actual_consumes:  ", receipt.actual_consumes)
print("declared_produces:", receipt.declared_produces)
print("writes:           ", receipt.writes)
print("effective_arg_keys:", run.receipts["split"].effective_arg_keys)
for address, digest in run.receipts["split"].produce_sha256.items():
    print("produce_sha256:   ", address, digest[:16])
print("the receipt is a Part:", pxc.has("px.receipt.order.Sum.sum"))
```

```text
by hand:          515
through the store: 3
no prefix:        Calculation address must start with 'fn.' (pure) or with 'oc.' (an OperationalCalculation: the syscall table, the only place an effect happens)
one result:       515 -> 515
several results:  {'px.order.tax': 41.2, 'px.order.total': 556.2}
published:        41.2 556.2
declared_consumes: ('px.order.prices',)
actual_consumes:   ('px.order.prices',)
declared_produces: ('px.order.subtotal',)
writes:            (PxWrite(address='px.order.subtotal', kind='new-address'),)
effective_arg_keys: ('subtotal', 'rate')
produce_sha256:    px.order.tax 19bcebe1fec328bc
produce_sha256:    px.order.total 845e7d137b67e401
the receipt is a Part: True
```

`args` is the constants of an invocation — the rubric, the rate, the width — and
bindings are its inputs. They arrive in the Calculation as one mapping, so a
Calculation never knows which of its inputs came from the store and which was
written at the call site. `effective_arg_keys` is what it actually got.

The receipt of `split` records no store read: `split` binds
`px.order.subtotal`, which `sum` published in this same run, so it reads a
*result* and not the store. Section 4 is that rule.

## 4. A program

A `PCR` is a named sequence of **Ticks**; a Tick is a named group of invocations.
`pcr.calc(tick, calculation, id=..., into=..., args=..., **inputs)` adds one
invocation, and returns a `ResultRef` you can bind later.

An input is bound either **by Part** — `prices=PRICES`, read from the store — or
**by result** — `subtotal=totals`, the `ResultRef` an earlier `calc` returned. If
that invocation published several Parts, say which: `split[TOTAL]` (or
`split.part(TOTAL)`). Binding a Part this same PCR already writes is the same
thing as binding the writer's result, and `PCR` rewrites it for you.

**Inside a Tick the Calculations are a sequence in declared order, and the Tick
boundary is where that sequence becomes inspectable.** A later Calculation may
bind an earlier sibling's result -- that is a chain -- and the owner's own words
for it are on `questions.md` (ChainsInsideATick: "your existing ChainSpot program
deliberately chains dependent Calculations inside a Tick. Your definition was the
moment that sequence becomes inspectable"). A Tick in which no Calculation reads
a sibling may run its Calculations at once. Two things are refused when you
author the program, not when you run it: a read of a Part a *later* sibling
produces, and two siblings producing one Part.

```python
from pyto import Calculation, PCR, Part, PxC

PRICES = Part("px.order.prices")
SUBTOTAL = Part("px.order.subtotal")
COUNT = Part("px.order.count")
TAX = Part("px.order.tax")
TOTAL = Part("px.order.total")
LINE = Part("px.order.line")


def add_up(args):
    return sum(args["prices"])


def count_items(args):
    return len(args["prices"])


def split_bill(args):
    tax = round(args["subtotal"] * args["rate"], 2)
    return {"px.order.tax": tax, "px.order.total": round(args["subtotal"] + tax, 2)}


def one_line(args):
    return f"{args['count']} items, total {args['total']}"


ADD_UP = Calculation("fn.order.add_up", add_up)
COUNT_OF = Calculation("fn.order.count", count_items)
SPLIT = Calculation("fn.order.split", split_bill)
LINE_OF = Calculation("fn.order.line", one_line)

pcr = PCR("order")
# One Tick, three Calculations. `sum` and `count` read no sibling, so they may run
# at once; `split` binds `sum`'s result, so this Tick is a chain and runs in order.
totals = pcr.calc("Sum", ADD_UP, id="sum", into=SUBTOTAL, prices=PRICES)
counted = pcr.calc("Sum", COUNT_OF, id="count", into=COUNT, prices=PRICES)
# Bound to a sibling's result, and publishing two Parts from one pass.
split = pcr.calc("Sum", SPLIT, id="split", into=[TAX, TOTAL], subtotal=totals, args={"rate": 0.08})
# `split` published two Parts, so this binding names the one it means.
pcr.calc("Say", LINE_OF, id="line", into=LINE, count=counted, total=split[TOTAL])

pxc = PxC()
pxc.set(PRICES, [250, 175, 90])
run = pcr.run(pxc)

print("ticks:  ", [tick.name for tick in pcr.ticks])
print("chained:", [tick.chained() for tick in pcr.ticks])
print("ids:    ", [inv.id for tick in pcr.ticks for inv in tick.calculations])
print("results:", run.results["sum"], run.results["count"], run.results["split"])
print("line:   ", pxc.get(LINE))
print("store:  ", pxc.addresses())
print("testimony:", run.ticks[1].calculations[0])
```

```text
ticks:   ['Sum', 'Say']
chained: [True, False]
ids:     ['sum', 'count', 'split', 'line']
results: 515 3 {'px.order.tax': 41.2, 'px.order.total': 556.2}
line:    3 items, total 556.2
store:   ('px.order.count', 'px.order.line', 'px.order.prices', 'px.order.subtotal', 'px.order.tax', 'px.order.total')
testimony: CalculationTestimony(id='line', calculation='fn.order.line', inputs={'count': 'fn:count', 'total': 'fn:split#px.order.total'}, args={}, into='px.order.line')
```

`run` returns a `PcrRun`: `results` by invocation id, `ticks` as testimony —
that last line is the whole program written down, `fn:count` for a result and
`fn:split#px.order.total` for one of several — and, with `observe=True`, one
`Receipt` per id. The store is left holding every published Part.

`run` also takes `parallel=True` (a Tick with no sibling reads runs its
invocations side by side; a chained Tick runs in order on one worker either
way) and `budget_ms=...` (stop at a Tick boundary). Neither changes `ticks`:
scheduling is not the program.

`pyto.Pcr` — lowercase — is a different thing and is not on this path: it is the
authoring graph that *emits* a PCR document (JSON, Mermaid) without executing
anything, where `PCR` is the executable program you just ran.

## 5. The record

`pyto.materialize.run_record(run, pxc, preexisting=...)` turns an observed run
into one `pyto-run-record@1` document: every Tick, every invocation, its inputs,
its `into`, its writes, its digests, its value, and which addresses were there
before the run started. `write_record(record, path)` puts it on disk.

A value the record cannot hold whole says what it is instead of pretending. A
long array carries its first 200 entries and a note with the full length; a value
over 256 KB is dropped for its size, digest and all; an image whose PNG would not
fit is never encoded (the encoder is stopped at the block that passes the cap) and
keeps a digest of its pixels; and an **array Part -- an ndarray -- is never spelled
out as JSON numbers at all**: the record keeps its dtype, its shape, the sha256 of
its buffer, the first 200 values, and, when you say where to put them, the raw
bytes beside the record.

    record = run_record(run, pxc, preexisting=preexisting, values_dir="out/record.values")
    write_record(record, "out/record.json")
    # out/record.json          the document, one {dtype, shape, digest, preview, path} per array
    # out/record.values/*.bin  the buffers, one file per published address

The digest is the point: an array is digested from its dtype, its shape and its
raw bytes, once, by the receipt (`result_sha256`), and the record reuses that
number. Before this an ndarray was not JSON, so it had no digest, no cache key and
an `omitted` line in every record. Everything else keeps one canonical
serialization per value: the receipt's digest is the proof the value is JSON, so
the materializer does not dump it a second time to find out.

That document is what a fresh process replays: it never imports your program, and
`px` reads it as a process table. A wall clock reaches two of its fields and no
others — `counters.wall_ms`, and `duration_ms` per invocation — and the `source`
block names the commit. Drop those and two runs of the same
program produce the same bytes, which is what the last line below checks against
a copy committed months ago.

```python
import json
from pyto import Calculation, PCR, Part, PxC
from pyto.materialize import run_record
from pyto.px import main

PRICES = Part("px.order.prices")
SUBTOTAL = Part("px.order.subtotal")
TAX = Part("px.order.tax")
TOTAL = Part("px.order.total")


def add_up(args):
    return sum(args["prices"])


def split_bill(args):
    tax = round(args["subtotal"] * args["rate"], 2)
    return {"px.order.tax": tax, "px.order.total": round(args["subtotal"] + tax, 2)}


def without_the_clock(document):
    """The record minus every field a wall clock or a checkout reaches."""
    trimmed = json.loads(json.dumps(document))
    trimmed.pop("source", None)
    trimmed["counters"].pop("wall_ms", None)
    for tick in trimmed["ticks"]:
        for invocation in tick["invocations"]:
            invocation.pop("duration_ms", None)
    return trimmed


ADD_UP = Calculation("fn.order.add_up", add_up)
SPLIT = Calculation("fn.order.split", split_bill)

pcr = PCR("order")
pcr.calc("Sum", ADD_UP, id="sum", into=SUBTOTAL, prices=PRICES)
pcr.calc("Split", SPLIT, id="split", into=[TAX, TOTAL], subtotal=SUBTOTAL, args={"rate": 0.08})

pxc = PxC()
pxc.set(PRICES, [250, 175, 90])
preexisting = set(pxc.addresses())
run = pcr.run(pxc, observe=True)
record = run_record(run, pxc, preexisting=preexisting)

counters = record["counters"]
print("schema:", record["schema"], "| pcr:", record["pcr"])
print("counters:", {name: counters[name] for name in ("invocations", "hits", "computed")})
for address in sorted(record["parts"]):
    part = record["parts"][address]
    print(f"part: {address:22} written_by={str(part['written_by']):6} preexisting={part['preexisting']}")
print()

# What a process that never saw the program above can do with the document alone:
main(["ps", "tests/fixtures/use/order-record.json"])
print()
with open("tests/fixtures/use/order-record.json", encoding="utf-8") as handle:
    committed = json.load(handle)
print("this run is that document:", without_the_clock(record) == without_the_clock(committed))
```

```text
schema: pyto-run-record@1 | pcr: order
counters: {'invocations': 2, 'hits': 1, 'computed': 1}
part: px.order.prices        written_by=None   preexisting=True
part: px.order.subtotal      written_by=sum    preexisting=False
part: px.order.tax           written_by=split  preexisting=False
part: px.order.total         written_by=split  preexisting=False

TICK  TICK-NAME  ID     CALCULATION      INTO                         STATE
0     Sum        sum    fn.order.add_up  px.order.subtotal            hit
1     Split      split  fn.order.split   px.order.tax,px.order.total  computed

this run is that document: True
```

`hit` is the one word worth learning here: an invocation is a *hit* when it read
a Part this run did not compute — the run's real inputs. Everything else was
computed in front of you. `px` has more subcommands over the same document:
`px ls` (every address and who produced it), `px cat` (one value), `px receipts`
(declared versus actual), `px diff` (two records), `px laws` (the node law over a
record). They are all `python -m pyto.px <command> <record.json>`.

## 6. PQL

`PQL` reads the store back. Two selectors are first-class — `PQL.part(address)`
for an exact Part and `PQL.prefix("px.order.")` for a subtree — and refinement
stays ordinary Python through `where(predicate)`. A query answers in four
spellings — `matches` (the `Match(address, value)` pairs), `values`, `addresses`,
and `one`/`optional`, the two strict ones: `one` raises unless there is exactly one, `optional` returns `None` for
none and raises for more than one.

`PQL.receipts(pxc, pcr=..., tick=...)` is the same thing with the receipt address
scheme spelled once: receipts are Parts under `px.receipt.<pcr>.<tick>.<id>`, so
reading them is not a separate mechanism.

```python
from pyto import Calculation, PCR, PQL, Part, PxC


def add_up(args):
    return sum(args["prices"])


def is_a_number(match):
    return isinstance(match.value, int)


ADD_UP = Calculation("fn.order.add_up", add_up)

pxc = PxC()
pxc.set(Part("px.order.prices"), [250, 175, 90])
pxc.set(Part("px.order.note"), "walk-in")
pcr = PCR("order")
pcr.calc("Sum", ADD_UP, id="sum", into=Part("px.order.subtotal"), prices=Part("px.order.prices"))
pcr.run(pxc, observe=True)

subtree = PQL.prefix("px.order.")
print("part:     ", PQL.part("px.order.subtotal").matches(pxc))
print("missing:  ", PQL.part("px.order.tip").matches(pxc))
print("prefix:   ", subtree.addresses(pxc))
print("values:   ", subtree.values(pxc))
print("where:    ", subtree.where(is_a_number).addresses(pxc))
print("one:      ", PQL.part("px.order.subtotal").one(pxc))
print("optional: ", PQL.part("px.order.tip").optional(pxc))
try:
    subtree.one(pxc)
except ValueError as refused:
    print("one of 3: ", refused)
print("repr:     ", subtree.where(is_a_number))

receipts = PQL.receipts(pxc, pcr="order")
print("receipts: ", [match.address for match in receipts])
print("by tick:  ", [match.address for match in PQL.receipts(pxc, tick="Sum")])
print("inside:   ", receipts[0].value.declared_produces)
```

```text
part:      (Match(address='px.order.subtotal', value=515),)
missing:   ()
prefix:    ('px.order.note', 'px.order.prices', 'px.order.subtotal')
values:    ('walk-in', [250, 175, 90], 515)
where:     ('px.order.subtotal',)
one:       515
optional:  None
one of 3:  PQL 'px.order.*' expected exactly 1 match; got 3
repr:      PQL('px.order.* where …')
receipts:  ['px.receipt.order.Sum.sum']
by tick:   ['px.receipt.order.Sum.sum']
inside:    ('px.order.subtotal',)
```

A `PQL` is a value: build it once, name it, refine it, hand it around. It selects
nothing until you give it a store, and a prefix query walks the store in address
order, so its answers are sorted without asking.

## 7. The worked example

`experiments/students/homework.py` is exactly the five things above, at the size a
person actually writes. One Part holds the input — a CSV of names and scores — and
four Ticks turn it into a grade sheet: `Parse` makes a roster; `Stats` holds two
Calculations side by side, a mean and a median, because neither reads the other
and the node law therefore lets them be one step; `Letters` grades every student
from cutoffs handed in as `args` rather than baked into the function; `Histogram`
draws a bar chart from the letters. It runs with `observe=True`, so it has
receipts; it calls `run_record` with the addresses it captured *before* the run as
`preexisting`, so the document knows the CSV was the one real input and everything
else was computed; and it writes that document next to its receipts as committed
evidence. `experiments/students/grade.py` then re-runs the program and compares
the fresh record against the committed one field by field, having first dropped
`duration_ms`, `counters.wall_ms` and the `source` block — the same three
wall-clock fields section 5 drops, for the same reason. Read it after this page:
there is nothing in it that is not on this page, only more of it.

## 8. What not to do

Three mistakes the kernel refuses, with the message you get. All three are
refused when you *write* the program, not when you run it, which is why they cost
seconds instead of an afternoon.

```python
from pyto import Calculation, PCR, Part, PxC


def add_up(args):
    return sum(args["prices"])


def double(args):
    return args["subtotal"] * 2


# 1. A Calculation whose address starts with neither `fn.` nor `oc.`.
try:
    Calculation("order.add_up", add_up)
except ValueError as refused:
    print("1:", refused)

# 2. A backwards read: inside a Tick the Calculations run in the order written,
# so `double` may read `sum`'s result only if `sum` is written first. Here it is
# written second, and the kernel refuses it when `sum` claims the address.
ADD_UP = Calculation("fn.order.add_up", add_up)
DOUBLE = Calculation("fn.order.double", double)
pcr = PCR("order")
pcr.calc(
    "Sum", DOUBLE, id="double", into=Part("px.order.double"), subtotal=Part("px.order.subtotal")
)
try:
    pcr.calc(
        "Sum", ADD_UP, id="sum", into=Part("px.order.subtotal"), prices=Part("px.order.prices")
    )
except ValueError as refused:
    print("2:", refused)

# 3. A write under the reserved receipt segment from your own code.
pxc = PxC()
try:
    pxc.set("px.receipt.order.Sum.sum", "mine")
except ValueError as refused:
    print("3:", refused)
```

```text
1: Calculation address must start with 'fn.' (pure) or with 'oc.' (an OperationalCalculation: the syscall table, the only place an effect happens)
2: PCR 'order' calculation 'sum' produces 'px.order.subtotal', which its sibling 'double' in Tick 'Sum' reads as 'subtotal': a Calculation may read what an earlier sibling produced, not a later one (the sequence runs in declared order, {?} ChainsInsideATick); declare 'sum' before 'double'
3: PxC: 'px.receipt.order.Sum.sum' is under the reserved 'px.receipt.' segment, which only a run may write (pyto.pcr, or inside receipt_writes_allowed(), or set(..., _from_run=True))
```

The fix for 2 is the order: write `sum` before `double` and the same two
Calculations are a chain inside one Tick, which is allowed and ordinary (the
owner's ChainSpot programs chain dependent Calculations inside a Tick; the Tick
boundary is where the sequence becomes inspectable). The message names both ids
so you do not have to go looking. And 3 is why a
receipt is worth reading: nothing but a run can write one, so a receipt in the
store is testimony and not a claim.

## 9. crisp

Everything above builds a program by hand. `crisp` (`pyto/src/pyto/crisp.py`,
`python -m pyto.crisp`, or `neat crisp` from `pyto/scripts/neat.sh`) has one tiny
job: turn a capability sentence, a store and a registry into **a composition
proposal** — one Part, `capabilityDelta`/`why`/`existingParts`/`proposedParts`/
`existingCalculations`/`proposedCalculations`/`PQL`/`inspection`/`verification`/
`decisions`/`limits` — and it is the only door into the store: `crisp import`
runs a proposal's PQL and writes what it produces, and refuses whatever
`--mode force` would refuse. Three commands, in order: `template` emits one
proposal; `vary` makes new options from it by changing one binding or
substituting one Calculation with the same produce shape ("variation through
PxC"); `import` runs one and writes its Parts.

The fixture below (`tests/fixtures/crisp/`) is built on the Blok color-study
fixture from section 6's neighbourhood (`tests/fixtures/blok/`): the same
`fn.colorStudy.coordinates` Calculation and the same `px.color.swatch.anchor`
swatch, plus two more swatches, a non-colour Part, and two more Calculations —
one with the same two-Part produce shape as `coordinates` and one with a
different shape.

`crisp template`, given the Blok root document as its `--pql`, in `--mode
force`: every name it reads resolves, so the proposal it writes carries no
`"{?}"` slot anywhere.

```python
from pyto import crisp

crisp.main([
    "template", "Derive the coordinates for the anchor swatch.",
    "--store", "tests/fixtures/crisp/store.json",
    "--registry", "tests.fixtures.crisp.registry:REGISTRY",
    "--set", "blok", "--mode", "force",
    "--pql", "tests/fixtures/crisp/root.pql.json",
    "--out", "tests/fixtures/crisp/out",
])
```

```text
address: proposal.neat.composition.blok.root.af8434cc0302
wrote:   tests/fixtures/crisp/out/blok.root.af8434cc0302.json
{
  "PQL": {
    "Ticks": [
      {
        "Calculations": [
          {
            "args": {},
            "call": "fn.colorStudy.coordinates",
            "into": [
              "px.exp.astar.blok.color.rgb",
              "px.exp.astar.blok.color.hsl"
            ],
            "with": {
              "hex": "px.color.swatch.anchor"
            }
          }
        ],
        "name": "Coordinates"
      }
    ],
    "labels": [
      "One color, two representations"
    ]
  },
  "basis": [],
  "capabilityDelta": "Derive the coordinates for the anchor swatch.",
  "decisions": [],
  "existingCalculations": [
    {
      "address": "fn.colorStudy.coordinates",
      "sha256": "cddeef00dbf3c44038d2ed20200b294784e415dd9b74cb37ef6fb15297d0554a"
    }
  ],
  "existingParts": [
    {
      "address": "px.color.swatch.anchor",
      "sha256": "4e4cfda60bfc10692677d5224c93e788fa827b60e2bdd3f5bafe4b78b69497e1"
    }
  ],
  "inspection": [],
  "limits": [],
  "pnc": "902d7a6764bccf7f7e755406302c780f83b2d62d169a4f9b99dd4313b3029bfd",
  "proposedCalculations": [],
  "proposedParts": [],
  "provisional": false,
  "review": "af8434cc0302676cef1a2d65da8f40f1203813dfa83fbcb9aef52773c944df3a",
  "verification": [],
  "why": "a PQL document handed to `crisp template` in force mode: 'Derive the coordinates for the anchor swatch.'"
}
```

Two digests are on every proposal, card and option (task 75): `pnc` is sha256
over the mechanism alone — the PQL's Ticks, `existingParts`, `proposedParts`,
`existingCalculations`, `proposedCalculations` — and `review` is sha256 over
the whole value, labels included. The address revision is `review`'s first 12
hex; a label change moves `review` and never `pnc`, and `basis`/`provisional`
name whether any binding here stands on a part (below, "partness propagates").

`crisp vary` reads that proposal back and makes one new option per way to
change it and stay the same shape: Variation A swaps the `hex` binding for
every other store address holding a string (`px.color.swatch.paper` and
`px.color.swatch.ink` — never `px.canvas.width`, a number); Variation B swaps
`fn.colorStudy.coordinates` for every other registered Calculation that
publishes the same two Parts when called the same way (`coordinatesInverted`,
never `luma`, which publishes one). Each option is written as its own proposal
Part, named `a<n>-<address>`/`b<n>-<address>`.

```python
import io
from contextlib import redirect_stdout

from pyto import crisp

with redirect_stdout(io.StringIO()) as hidden:
    crisp.main([
        "template", "Derive the coordinates for the anchor swatch.",
        "--store", "tests/fixtures/crisp/store.json",
        "--registry", "tests.fixtures.crisp.registry:REGISTRY",
        "--set", "blok", "--mode", "force",
        "--pql", "tests/fixtures/crisp/root.pql.json",
        "--out", "tests/fixtures/crisp/out",
    ])
address = hidden.getvalue().splitlines()[0][len("address: "):]
digest = address.rsplit(".", 1)[-1]
proposal_path = f"tests/fixtures/crisp/out/blok.root.{digest}.json"

crisp.main([
    "vary", proposal_path,
    "--store", "tests/fixtures/crisp/store.json",
    "--registry", "tests.fixtures.crisp.registry:REGISTRY",
])
```

```text
proposal.neat.composition.blok.a1-ink.f12fe5a05630  binding hex: px.color.swatch.anchor -> px.color.swatch.ink  digest=f12fe5a05630c7f2b0a1219c12a39fdc6dc9f5bcd8d1df8869a3bb6224d8f739
proposal.neat.composition.blok.a2-paper.ce8145250cb5  binding hex: px.color.swatch.anchor -> px.color.swatch.paper  digest=ce8145250cb501c0b4932da236ec0e5e1b00ef7fd69072db6f5bc7c246454f4c
proposal.neat.composition.blok.b1-coordinatesInverted.e993fa404441  call: fn.colorStudy.coordinates -> fn.colorStudy.coordinatesInverted  digest=e993fa404441b49c322337aafe82198db48e54dc3318de24507ab45b0dd9d4f0
```

`crisp import` is the one door into the store: it runs the proposal's PQL
through `pyto.neat.diff.run_document` (the same builder section 6's PQL reads
from, reused rather than rewritten), writes a `pyto-run-record@1` at `--out`,
and writes every Part the run produced — value and digest — to `store-after`.

```python
import io
from contextlib import redirect_stdout

from pyto import crisp

with redirect_stdout(io.StringIO()) as hidden:
    crisp.main([
        "template", "Derive the coordinates for the anchor swatch.",
        "--store", "tests/fixtures/crisp/store.json",
        "--registry", "tests.fixtures.crisp.registry:REGISTRY",
        "--set", "blok", "--mode", "force",
        "--pql", "tests/fixtures/crisp/root.pql.json",
        "--out", "tests/fixtures/crisp/out",
    ])
address = hidden.getvalue().splitlines()[0][len("address: "):]
digest = address.rsplit(".", 1)[-1]
proposal_path = f"tests/fixtures/crisp/out/blok.root.{digest}.json"

crisp.main([
    "import", proposal_path,
    "--store", "tests/fixtures/crisp/store.json",
    "--registry", "tests.fixtures.crisp.registry:REGISTRY",
    "--out", "tests/fixtures/crisp/out/run.json",
])
```

```text
ran:         crisp.import (1 invocation(s))
record:      tests/fixtures/crisp/out/run.json
store-after: tests/fixtures/crisp/out/store-after.json
  px.exp.astar.blok.color.hsl  sha256=03d972fb43342565012e359a459c818dc40e6678bfd8205385a11a984b8e5d75
  px.exp.astar.blok.color.rgb  sha256=bbf9926d0f47244b1f9acf2a9e947fd2f6b3fccf64fe98ac2007377c8ad8945c
```

`crisp template` without `--pql` writes a skeleton instead, in `--mode imply`
only: `existingParts`/`existingCalculations` come from whatever the sentence
names (verbatim, or by a store or registry address's last segment), the PQL's
`with` bindings are filled from them by declared input name, and anything
`crisp` cannot resolve — an output address, a plan for `inspection`,
`verification`, `decisions`, `limits` — is a `"{?}"` slot for a person to fill
in, never a guess. `--mode force` refuses a skeleton outright: with nothing to
resolve against, there is nothing for force mode to verify.

`crisp cards` reads a proposal (or the whole set directory `template` and
`vary` wrote into together) and emits one Blok card set — root labelled, root
unlabelled, then every option present — as its own Part, alongside a static
HTML rendering (no script anywhere) in the same style: a card per candidate,
both digests on each. The root labelled and root unlabelled cards are
otherwise identical, which is the label/`pnc`/`review` rule made concrete: the
same `pnc`, a different `review`.

```python
import io
from contextlib import redirect_stdout

from pyto import crisp

with redirect_stdout(io.StringIO()) as hidden:
    crisp.main([
        "template", "Derive the coordinates for the anchor swatch.",
        "--store", "tests/fixtures/crisp/store.json",
        "--registry", "tests.fixtures.crisp.registry:REGISTRY",
        "--set", "blok", "--mode", "force",
        "--pql", "tests/fixtures/crisp/root.pql.json",
        "--out", "tests/fixtures/crisp/out",
    ])
address = hidden.getvalue().splitlines()[0][len("address: "):]
digest = address.rsplit(".", 1)[-1]
proposal_path = f"tests/fixtures/crisp/out/blok.root.{digest}.json"

with redirect_stdout(io.StringIO()):
    crisp.main([
        "vary", proposal_path,
        "--store", "tests/fixtures/crisp/store.json",
        "--registry", "tests.fixtures.crisp.registry:REGISTRY",
    ])

crisp.main([
    "cards", "tests/fixtures/crisp/out",
    "--store", "tests/fixtures/crisp/store.json",
    "--labels", "One color, two representations",
    "--out", "tests/fixtures/crisp/out/cards.json",
])
```

```text
address: proposal.neat.cards.blok.17ecb2fca4fa
wrote:   tests/fixtures/crisp/out/cards.json
html:    tests/fixtures/crisp/out/cards.html
  One color, two representations  pnc=902d7a6764bc  review=6756d72e9d42
  (unlabelled)  pnc=902d7a6764bc  review=6d3a1e5e1c6e
  (unlabelled)  pnc=0e5a23fbb161  review=0839ab630fee
  (unlabelled)  pnc=9db618d9624f  review=0ba360b7e759
  (unlabelled)  pnc=31337aa6b3aa  review=0a16b629e9ef
```

A `with` binding may be a plain address (live: whatever the store holds now)
or `{"address": ..., "sha256": ...}` (pinned): `template` and `--mode force`
accept either, always writing the plain address into `PQL` — the grammar the
studio reads has no third shape for `with` — with every pin collected beside
it, under `pins`. `crisp import` is where a pin is actually checked, against
the store it is about to read: the exact digest it names imports; anything
else refuses by name.

```python
from pyto import crisp
from pyto.crisp import _digest_of, _load_json

store = _load_json("tests/fixtures/crisp/store.json")
document = _load_json("tests/fixtures/crisp/root.pql.json")
document["Ticks"][0]["Calculations"][0]["with"]["hex"] = {
    "address": "px.color.swatch.anchor",
    "sha256": _digest_of(store["px.color.swatch.anchor"]),
}
crisp._write_json(document, "tests/fixtures/crisp/out/pinned/pinned.pql.json")

crisp.main([
    "template", "Derive the coordinates for the anchor swatch.",
    "--store", "tests/fixtures/crisp/store.json",
    "--registry", "tests.fixtures.crisp.registry:REGISTRY",
    "--set", "blok", "--mode", "force",
    "--pql", "tests/fixtures/crisp/out/pinned/pinned.pql.json",
    "--out", "tests/fixtures/crisp/out/pinned",
])
```

```text
address: proposal.neat.composition.blok.root.7586d6ab1108
wrote:   tests/fixtures/crisp/out/pinned/blok.root.7586d6ab1108.json
{
  "PQL": {
    "Ticks": [
      {
        "Calculations": [
          {
            "args": {},
            "call": "fn.colorStudy.coordinates",
            "into": [
              "px.exp.astar.blok.color.rgb",
              "px.exp.astar.blok.color.hsl"
            ],
            "with": {
              "hex": "px.color.swatch.anchor"
            }
          }
        ],
        "name": "Coordinates"
      }
    ],
    "labels": [
      "One color, two representations"
    ]
  },
  "basis": [],
  "capabilityDelta": "Derive the coordinates for the anchor swatch.",
  "decisions": [],
  "existingCalculations": [
    {
      "address": "fn.colorStudy.coordinates",
      "sha256": "cddeef00dbf3c44038d2ed20200b294784e415dd9b74cb37ef6fb15297d0554a"
    }
  ],
  "existingParts": [
    {
      "address": "px.color.swatch.anchor",
      "sha256": "4e4cfda60bfc10692677d5224c93e788fa827b60e2bdd3f5bafe4b78b69497e1"
    }
  ],
  "inspection": [],
  "limits": [],
  "pins": {
    "px.color.swatch.anchor": "4e4cfda60bfc10692677d5224c93e788fa827b60e2bdd3f5bafe4b78b69497e1"
  },
  "pnc": "902d7a6764bccf7f7e755406302c780f83b2d62d169a4f9b99dd4313b3029bfd",
  "proposedCalculations": [],
  "proposedParts": [],
  "provisional": false,
  "review": "7586d6ab1108f0e95765a49853c2eac1bbfffdfebcd46200ad45b86783f4c580",
  "verification": [],
  "why": "a PQL document handed to `crisp template` in force mode: 'Derive the coordinates for the anchor swatch.'"
}
```

An A-Star study (the local PoC shape: `known`, `unresolved`, `references`,
`possibilities`, `return_when`) seeds a proposal directly: a `known` entry
naming a store or registry address becomes an `existingPart`/
`existingCalculation`, each `unresolved` entry becomes a `"{?}"` slot in
`decisions`, and `return_when` becomes `limits`. `--mode force` refuses while
any `unresolved` entry remains (the fixture's does: "which representation the
site shows"); `--mode imply` writes it as it stands.

```python
from pyto import crisp

crisp.main([
    "template", "Derive the coordinates for the anchor swatch.",
    "--store", "tests/fixtures/crisp/store.json",
    "--registry", "tests.fixtures.crisp.registry:REGISTRY",
    "--set", "blok", "--mode", "imply",
    "--astar", "tests/fixtures/crisp/astar-blok.json",
    "--out", "tests/fixtures/crisp/out/astar",
])
```

```text
address: proposal.neat.composition.blok.root.e5837595ea56
wrote:   tests/fixtures/crisp/out/astar/blok.root.e5837595ea56.json
{
  "PQL": {
    "Ticks": [
      {
        "Calculations": [],
        "name": "blok"
      }
    ]
  },
  "basis": [],
  "capabilityDelta": "Derive the coordinates for the anchor swatch.",
  "decisions": [
    "{?} which representation the site shows"
  ],
  "existingCalculations": [
    {
      "address": "fn.colorStudy.coordinates",
      "sha256": "cddeef00dbf3c44038d2ed20200b294784e415dd9b74cb37ef6fb15297d0554a"
    }
  ],
  "existingParts": [
    {
      "address": "px.color.swatch.anchor",
      "sha256": "4e4cfda60bfc10692677d5224c93e788fa827b60e2bdd3f5bafe4b78b69497e1"
    }
  ],
  "inspection": [
    "{?} Inspection: what a person would see or do is not yet specified"
  ],
  "limits": [
    "Return when the site has settled on one representation to show."
  ],
  "pnc": "e4be4850b75c7cb4d713c62700e2a8ec089d52d6514570ba441ca45e06065fcc",
  "proposedCalculations": [],
  "proposedParts": [],
  "provisional": false,
  "review": "e5837595ea56d8262cb46464a655904a2298452f78e17751ba78f5a013c0124b",
  "verification": [
    "{?} Verification: what would be checked, and what it protects, is not yet specified"
  ],
  "why": "an A-Star study handed to `crisp template` in imply mode: 'Derive the coordinates for the anchor swatch.'"
}
```

Partness propagates instead of refusing: a `with` binding to a part (any
address under `proposal.*` or `px.exp.*`) is never refused in force mode,
even when the store does not hold it yet — it is recorded as the proposal's
`basis`, and `provisional` turns `true`. `px ls`/`px tick` show the same rule
over a run record once such a proposal imports (`pyto/src/pyto/px.py`
`part_basis`): a Part computed from a part is a part.

## 10. neat delta

Two ways to build one capability are compared as **end states**, not as diffs
read side by side. `neat delta <a> <b>` (`pyto/src/pyto/neat/delta.py`) measures
landing `a` alone and the tree after both `a` and `b` from `a`'s base, from
each landing's receipt (its verifier pass count and `check_all` counts: what
runs green) and its git diff (Calculations registered, user actions, prefix
queries; lines, files, pages, new `px.<x>.<y>` address roots, assertions moved
in pre-existing tests, fixtures regenerated), then `fn.neat.delta.evaluate`,
pure over the two measurements, publishes `px.exp.neat.delta.<a>.<b>` under
`pyto/experiments/review/deltas` with its run record: more verified behaviour
wins, then more capability points, then the cheaper end state, and `rework` counts the lines `b`
tore out of `a`. What counts is the repository's own manifest,
`pyto/experiments/delta/patterns.json`. The first record is task 78 (a second
page built beside the PxC composer) against task 79 (the composer refined).

## 11. pyto study

One command, a table you actually have, and an honest study of it. Every step is
a `Calculation` from the brain (`experiments/brain`) run through an observed
`PCR`, so what comes back is Parts with receipts rather than a printout.

```sh
bash pyto/scripts/neat.sh study shelf.csv                     # or: python -m pyto.study shelf.csv
bash pyto/scripts/neat.sh study shelf.csv --target weight --out shelf-study
bash pyto/scripts/neat.sh study --example shelf --out shelf-study    # the worked example below
bash pyto/scripts/neat.sh study --example planted --out planted      # and its oracle
bash pyto/scripts/neat.sh study rows.csv --delimiter ";" --missing "-,n/a"
```

Under `--out` (default `study/`):

| File | What it is |
|---|---|
| `store.json` | every Part the study wrote, canonical, addressed `px.exp.study.<name>.*` |
| `records/study_read.json`, `records/study_weigh.json`, `records/study.json` | the three observed runs, `pyto-run-record@1` |
| `study.html` | the summary, then the Tick viewer with those records baked in (one file, no server) |
| `px.exp.study.<name>.map` | what ran, what was refused and why, which engine each step used |

The study reads the table (`oc.brain.data.load`, through the run's effects
handle), profiles every column (`describe`, the iqr outlier rule, shapiro-wilk),
correlates what is numeric and puts a p-value beside each pair, tests the one
hypothesis the table invites, clusters and takes the principal components, and
with `--target` cross-validates every model the brain owns on the same folds and
the same seed. `backend="auto"` everywhere the brain's plan Part has an entry, so
shapiro runs on scipy and k-means on the gram expansion without anyone saying so.

**Four rules, and they are the whole design.**

*Every number is a Part.* The summary is `px.exp.study.<name>.summary`, and every
line in it carries `cites`: the address, the key and the value it printed.
`tests/test_study.py` walks them and checks the prose against the store.

*A step that does not fit is refused, not forced.* Too few rows, a non-numeric
column, a t test whose normality check failed: each is a row in the plan and a
Part of its own (`px.exp.study.<name>.skipped.*`) with its `needed` and its
`had`, and the page ends with **what this study would not say**.

*Nothing is chosen by its answer.* The group column is the first one that splits
the rows, never the one with the smallest p-value; the number of clusters is the
one the recorded silhouette prefers; the model is the one the recorded
cross-validated score prefers, and if none of them beats predicting the mean the
study names no predictor and says so.

*And nothing expensive is silent.* Past 1200 complete rows the clustering is
fitted and scored on a seeded sample of them -- the silhouette compares every row
with every other one, so its cost is quadratic -- and past 2000 rows the model
comparison is too. Both samples are Parts, named in the plan and in the summary
and reproducible from the seed; neither is a quiet narrowing of the claim.

The worked example is the studio's own shelf -- twelve discs, their molds' flight
numbers, and what they weigh:

```sh
bash pyto/scripts/neat.sh study --example shelf --out shelf-study
```

```text
== the hypothesis
  - weight across maker: Discraft (n=8, mean 174), Innova (n=4, mean 173.75).
  - normality (shapiro-wilk): Discraft p=0.014, Innova p=0.31 -- fails at 0.05.
  - equal variance (levene): p=0.187 -- passes at 0.05.
  - so the study ran fn.brain.stats.mannwhitneyu: normality is not established
    (shapiro-wilk rejects it), so the ranks are compared instead of the means.
  - mannwhitneyu: statistic 22, p = 0.332 -- no difference this test can tell from chance at 0.05.

== the clusters
  - k = 3 of the 3 tried scores best: silhouette 0.547 -- the clusters are real.

== the best predictor
  - knn wins on r2: -0.4997, ahead of forest by 1.7412.
  - but it does NOT clear the baseline (0: predicting the mean of the training rows),
    so this study names no predictor: on these rows, nothing here beats the obvious guess.

== what this study would not say
  - model.winner: no candidate beat the baseline, so the study names no predictor.
```

The three records are ordinary `pyto-run-record@1` documents, so the shell over
records reads a study back without importing anything:

```sh
python -m pyto.px ps shelf-study/records/study.json      # every Tick, every Calculation, hit or computed
python -m pyto.px cat shelf-study/records/study.json px.exp.study.shelf.summary
```

The second example is the check on the study itself: `--example planted` writes a
table with three planted clusters, a planted linear target, a decoy column of
pure noise and a constant column, all before the study sees it, and then compares
what the study said with what was planted -- the right number of clusters, the
decoy left out of the findings, the constant column refused, the planted group
difference found, and a linear model winning because the truth is linear.

## 12. neat hot and neat equiv

Two verbs over a run record: one names what a run spent itself on and the shape
that made it expensive, the other is how a faster way earns being believed. The
owner, 2026-09-12, after a generation of 32 renders kept every render as a list
of 196,608 ints and paid per pixel in every stage: "come up with some
compiler-ish efficiency pass to prevent things like this? Encode a path to
trusting the sparsification of things."

```sh
bash pyto/scripts/neat.sh hot observed/record.json                       # or: python -m pyto.neat.hot ...
bash pyto/scripts/neat.sh equiv observed/record.json --calc fn.evo.render \
    --candidate exp/evo-pxc/fast_render.py:render --store observed/parts.json
```

`neat hot` (`pyto/src/pyto/neat/hot.py`) reads one `pyto-run-record@1` and
nothing else -- no clock, no import of the program that made it -- and publishes
`px.exp.neat.hot.<record-stem>` under `pyto/experiments/review/hot` with its own
run record. Per invocation it takes the receipt's `duration_ms` and the shape of
its value: the kind, the bytes, the elements when the value is a list (flattened;
a rectangular nested list is an array written the long way, and a record written
with the default array cap is measured at the lengths its truncation note
carries), and the duration per element -- its own elements, or the largest list
its recorded inputs handed it, because a receipt that returns one dict still paid
per element when it read 196,608 of them. Then the findings, each naming the
Calculation, its numbers and its `for`: **dense-list** (a result that is a list of
more than 4096 numbers and would be an array), **per-element** (more than 50 ns
per element over at least 1024 elements), **over-cap** (a value omitted over the
record's cap, or kept only because the run raised it, with the bytes it costs),
**repeat-input** (two or more receipts of one Calculation with the same resolved
input digests and args: a cache that isn't there), and **hot** (the top three
Calculations by total duration, always).

The 50 ns is calibrated on the generation this was written for: dense, every
stage trips it (render 1358 ns per pixel, fitness 345, encode 86); rewritten over
arrays, nothing does. 50 ns is about one Python bytecode's worth of work per
element -- above it the elements are being walked in Python, below it they are
being moved in one pass.

`neat equiv` (`pyto/src/pyto/neat/equiv.py`) is the trust path, and it is the
owner's own test: what made him believe the faster renderer was that it
reproduced all 32 result hashes of the recorded run. For every receipt of one
Calculation it rebuilds the inputs that receipt was given -- from the record
first, then from `--store` for an input bound to a Part the record does not carry
-- runs the candidate on them, and compares the results. An input that is neither
is a refusal naming the receipt, the input, what was needed and what was had:
nothing is claimed over a receipt that could not be rebuilt. The answer is
`px.exp.neat.equiv.<calc>.<candidate-sha-prefix>` under
`pyto/experiments/review/equiv`, `trusted: true` only when every receipt matched
and none was left unrebuilt, and per-receipt rows when they did not.

**The whole trust rests on one function**, `equiv.canonical`, so it is one
function with its own tests: two results are the same when they are the same
*values*, not the same Python object. An ndarray of single-byte integers
(duck-typed on `tobytes`/`dtype`/`shape` -- this kernel imports no numpy) and a
flat or rectangular nested list of ints in 0..255 both canonicalize to the raw
bytes in C order, so a `(256, 256, 3)` uint8 array and the 196,608-int list the
same render wrote are one value. Everything else canonicalizes to canonical
JSON. When the record omitted a result over the value cap, its note carries the
sha256 of the JSON payload and the comparison runs against that, saying so.

```python
from pyto import Calculation, PCR, Part, PxC
from pyto.materialize import run_record
from pyto.neat.equiv import canonical, check, describe, judge
from pyto.neat.hot import evaluate, measure

FIELD = Part("px.demo.field")
TINT = Part("px.demo.tint")


def tint(args):
    """The dense way: 20,000 ints in, Python arithmetic per element, 20,000 ints out."""
    out = []
    for value in args["field"]:
        lit = value * 0.35 + 12.5
        out.append(min(255, max(0, int(round(lit)))))
    return out


def tint_sparse(args):
    """The candidate: the same formula, the pixels kept as bytes instead of a list of ints."""
    return bytes(min(255, max(0, int(round(value * 0.35 + 12.5)))) for value in args["field"])


pxc = PxC()
pxc.set(FIELD, [(index * 37) % 256 for index in range(20000)])
pcr = PCR("demo")
pcr.calc("Tint", Calculation("fn.demo.tint", tint), id="tint", into=TINT, field=FIELD)
run = pcr.run(pxc, observe=True)
record = run_record(run, pxc, preexisting={"px.demo.field"}, array_cap=20000)

# the pass: what is hot here, and the shape that made it hot
found = evaluate({"measured": measure(record, path="demo-record.json"), "stem": "demo"})
print("hot:      ", [f["calculation"] for f in found["findings"] if f["finding"] == "hot"])
print("findings: ", [(f["finding"], f["calculation"]) for f in found["findings"] if f["finding"] != "hot"])
print("elements: ", [f["elements"] for f in found["findings"] if f["finding"] == "dense-list"])

# the canonical rule: the same values, not the same object
print("canonical:", canonical([0, 1, 255])[1], canonical(b"\x00\x01\xff") == canonical([0, 1, 255]))

# the trust path: every receipt rebuilt, the candidate run on it, the results compared
checked = check(record, "fn.demo.tint", tint_sparse, store={"px.demo.field": pxc.get(FIELD)})
witness = judge({**checked, "candidate": describe(tint_sparse)})
print("counts:   ", witness["counts"])
print("trusted:  ", witness["trusted"], "|", witness["reason"])
```

```text
hot:       ['fn.demo.tint']
findings:  [('dense-list', 'fn.demo.tint'), ('per-element', 'fn.demo.tint')]
elements:  [20000]
canonical: bytes True
counts:    {'receipts': 1, 'matched': 1, 'mismatched': 0, 'not_rebuildable': 0}
trusted:   True | 1/1 receipts of fn.demo.tint reproduced by __main__:tint_sparse, value for value
```

Over the generation itself: `neat hot` on the dense record names `fn.evo.render`
(78.6% of the run), `fn.evo.fitness` and `fn.evo.encode` as hot, the render's
196,608-number list as `dense-list`, all three as `per-element`, and 19,169,813
bytes of over-cap value; on the array record it is quiet but for `hot`. `neat
equiv --calc fn.evo.render --candidate fast_render.py:render` witnesses 32/32
`trusted: true` from the record alone, and the same renderer with the palette
swapped witnesses 0/32 with a row per receipt.

## Where to go next

- `experiments/students/homework.py` — section 7, as a program you can run.
- `viewer/RECORD.md` — the record document, field by field.
- `tests/test_first_class.py`, `tests/test_pql.py`, `tests/test_semantics.py` —
  the executable spec of everything above.
- `python -m pyto.px --help` — the shell over records.
