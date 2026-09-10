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

**The node law: the Calculations of one Tick are parallel branches, so none of
them may read another's produce and no two of them may write the same Part.**
That is what makes a Tick safe to run on a pool, and it is refused when you
author it, not when you run it.

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
# One Tick, two Calculations: neither reads the other, so they are parallel branches.
totals = pcr.calc("Sum", ADD_UP, id="sum", into=SUBTOTAL, prices=PRICES)
counted = pcr.calc("Sum", COUNT_OF, id="count", into=COUNT, prices=PRICES)
# Bound to a result, and publishing two Parts from one pass.
split = pcr.calc("Split", SPLIT, id="split", into=[TAX, TOTAL], subtotal=totals, args={"rate": 0.08})
# `split` published two Parts, so this binding names the one it means.
pcr.calc("Say", LINE_OF, id="line", into=LINE, count=counted, total=split[TOTAL])

pxc = PxC()
pxc.set(PRICES, [250, 175, 90])
run = pcr.run(pxc)

print("ticks:  ", [tick.name for tick in pcr.ticks])
print("ids:    ", [inv.id for tick in pcr.ticks for inv in tick.calculations])
print("results:", run.results["sum"], run.results["count"], run.results["split"])
print("line:   ", pxc.get(LINE))
print("store:  ", pxc.addresses())
print("testimony:", run.ticks[2].calculations[0])
```

```text
ticks:   ['Sum', 'Split', 'Say']
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

`run` also takes `parallel=True` (the invocations of a Tick run side by side —
the node law is what makes that safe) and `budget_ms=...` (stop at a Tick
boundary). Neither changes `ticks`: scheduling is not the program.

`pyto.Pcr` — lowercase — is a different thing and is not on this path: it is the
authoring graph that *emits* a PCR document (JSON, Mermaid) without executing
anything, where `PCR` is the executable program you just ran.

## 5. The record

`pyto.materialize.run_record(run, pxc, preexisting=...)` turns an observed run
into one `pyto-run-record@1` document: every Tick, every invocation, its inputs,
its `into`, its writes, its digests, its value, and which addresses were there
before the run started. `write_record(record, path)` puts it on disk.

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

## Where to go next

- `experiments/students/homework.py` — section 7, as a program you can run.
- `viewer/RECORD.md` — the record document, field by field.
- `tests/test_first_class.py`, `tests/test_pql.py`, `tests/test_semantics.py` —
  the executable spec of everything above.
- `python -m pyto.px --help` — the shell over records.
