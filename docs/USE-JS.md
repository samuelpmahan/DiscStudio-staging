# Using the studio from JavaScript

Ten minutes, top to bottom. Every `js` block below is run by `tests/use-js.test.js`
in a fresh `node` process and its printed output is compared byte for byte with the
text block underneath it. If a paragraph here lies, that test is red and it names
the paragraph.

Each block is a self-contained ES module. Its imports are written the way a file one
directory below the repository root writes them -- `../src/core/exec.js` -- so you can
paste a block into `docs/scratch.mjs` and run `node docs/scratch.mjs`.

There are five things and they arrive in this order: a **store** (the PxC board), a
**PQL document** (a PrincipleComponentRender, its Ticks, their Calculations), the
**run**, the **receipt** the run leaves at `px.receipt.<name>`, and the **run record**
that receipt exports to. `px.undo.<scope>` is the sixth, and it is only more of the
same: undo is a Calculation, not a second history.

An address has three roots: `px` for values, `fn` for pure Calculations, `oc` for
effects. `px.receipt.<name>`, `px.pql.<name>` and `px.run.<name>` are the three
reserved second segments a run writes for you.

## 1. The store

The board is one map with manners. A value lives at a dotted **address**; `set` puts
one there, `get` takes it out and **refuses** when nobody produced it, `has` asks
without refusing, `keys` lists what is there. `pxKey(address)` and `pxFn(address)` are
frozen handles -- a Part and a Calculation by name -- and everywhere the board takes
one it also takes the bare string, because identity is the address and nothing else.

`register` puts a Calculation on the board under its `fn.` address, and `call` invokes
it with one object of named inputs. `fork` gives you a copy you can scribble on.

```js
import { createExecBoard, pxFn, pxKey } from '../src/core/exec.js';

const pxc = createExecBoard();
const PRICES = pxKey('px.order.prices');

pxc.set(PRICES, [250, 175, 90]);
pxc.set('px.order.note', 'walk-in');

console.log('has prices:  ', pxc.has(PRICES));
console.log('prices:      ', pxc.get('px.order.prices'));
console.log('has total:   ', pxc.has('px.order.total'));
console.log('keys:        ', pxc.keys());
try {
  pxc.get('px.order.total');
} catch (refused) {
  console.log('get total:   ', refused.message);
}

pxc.register(pxFn('fn.order.total'), ({ prices }) => prices.reduce((a, b) => a + b, 0));
console.log('call:        ', pxc.call(pxFn('fn.order.total'), { prices: pxc.get(PRICES) }));
try {
  pxc.call(pxFn('fn.order.tax'), {});
} catch (refused) {
  console.log('unregistered:', refused.message);
}

const scratch = pxc.fork();
scratch.set('px.order.note', 'league night');
console.log('fork:        ', scratch.get('px.order.note'), '| original:', pxc.get('px.order.note'));
console.log('a handle is the address:', pxKey('px.order.prices').address, pxFn('fn.order.total').address);
```

```text
has prices:   true
prices:       [ 250, 175, 90 ]
has total:    false
keys:         [ 'px.order.prices', 'px.order.note' ]
get total:    exec board: slot 'px.order.total' not produced yet.
call:         515
unregistered: PxC: calculation 'fn.order.tax' is not registered.
fork:         league night | original: walk-in
a handle is the address: px.order.prices fn.order.total
```

`get` on an address nobody produced is the whole point of the store: a screen that
reads something no Calculation wrote stops there, instead of carrying `undefined`
into a card. `keys` answers in the order the addresses were first written; when you
want an answer that does not depend on write order, ask a prefix query (section 3).

## 2. A PQL document

A **PQL document** is data, not code: a `PrincipleComponentRender` (the name of the
render) and a list of `Ticks`, each a `name` and a list of `Calculations`. One
Calculation is `call` (a registered `fn.` address), `with` (named inputs bound to
addresses), `args` (the constants of this invocation) and `into` (the address it
publishes, or an array of them).

`readPql(source, parse)` reads that document and refuses the bad ones **before**
anything runs. It takes the parser explicitly -- the studio hands it `JSON.parse`, so
the core carries no YAML dependency -- and it fills in the parts you left out: a
Calculation with no `with` and no `args` gets empty ones, never `undefined`.

```js
import { readPql } from '../src/core/exec.js';

const read = (document) => readPql(JSON.stringify(document), JSON.parse);

// The smallest document that is worth writing: one Tick, one Calculation.
const composition = read({
  PrincipleComponentRender: 'order',
  Ticks: [{
    name: 'Sum',
    Calculations: [{ call: 'fn.order.total', with: { prices: 'px.order.prices' }, into: 'px.order.subtotal' }]
  }]
});

console.log('render:', composition.PrincipleComponentRender);
console.log('ticks: ', composition.Ticks.map((tick) => tick.name));
const only = composition.Ticks[0].Calculations[0];
console.log('call:  ', only.call);
console.log('with:  ', only.with);
console.log('args:  ', only.args, '(filled in, not undefined)');
console.log('into:  ', only.into);

const bare = read({ PrincipleComponentRender: 'p', Ticks: [{ name: 'T', Calculations: [{ call: 'fn.x', into: 'px.a' }] }] });
console.log('bare:  ', bare.Ticks[0].Calculations[0]);

for (const [label, document] of [
  ['no render name', { Ticks: [] }],
  ['no ticks      ', { PrincipleComponentRender: 'p' }],
  ['call is a name', { PrincipleComponentRender: 'p', Ticks: [{ name: 'T', Calculations: [{ call: 'order.total', into: 'px.a' }] }] }],
  ['no into       ', { PrincipleComponentRender: 'p', Ticks: [{ name: 'T', Calculations: [{ call: 'fn.x' }] }] }],
  ['into is empty ', { PrincipleComponentRender: 'p', Ticks: [{ name: 'T', Calculations: [{ call: 'fn.x', into: [] }] }] }]
]) {
  try {
    read(document);
  } catch (refused) {
    console.log(`${label}:`, refused.message);
  }
}
```

```text
render: order
ticks:  [ 'Sum' ]
call:   fn.order.total
with:   { prices: 'px.order.prices' }
args:   {} (filled in, not undefined)
into:   px.order.subtotal
bare:   { call: 'fn.x', with: {}, args: {}, into: 'px.a' }
no render name: PQL PrincipleComponentRender: expected a nonempty string.
no ticks      : PQL Ticks: expected a sequence.
call is a name: PQL T.Calculations[0].call: expected a registered fn. address.
no into       : PQL T.Calculations[0].into: expected a nonempty string.
into is empty : PQL T.Calculations[0].into: expected at least one address; a Calculation that publishes nothing has no place in this grammar.
```

Every refusal names the path it was reading -- `Sum.Calculations[0].into` -- so a
document you generated from a screen tells you which Tick to look at, not which
library.

## 3. Running it

`invokePql(composition, { pxc })` walks the Ticks in order and, inside a Tick, the
Calculations in order. For each one it resolves `with` against the board, merges
`args`, calls the Calculation, and publishes the result at `into`.

Three things are worth knowing:

- **`into` may be an array.** One pass, several Parts. The Calculation then returns
  either an object keyed by those addresses or an array of values in the declared
  order, and nothing is published unless every declared address is there.
- **A `with` value ending in `.*` is a prefix query.** It reads every Part under the
  prefix as one object, sorted by address, so the answer never depends on write order.
- **The run is itself a Part**, at `px.pql.<name>`, holding what each Calculation was
  actually called with and what it produced.

```js
import { createExecBoard, invokePql, pxFn, queryPrefix, readPql } from '../src/core/exec.js';

const pxc = createExecBoard();
pxc.set('px.order.prices', [250, 175, 90]);

const cents = (value) => Math.round(value * 100) / 100;
pxc.register(pxFn('fn.order.total'), ({ prices }) => prices.reduce((a, b) => a + b, 0));
// Several `into`: one pass over the subtotal, two Parts out of it.
pxc.register(pxFn('fn.order.split'), ({ subtotal, rate }) => ({
  'px.order.tax': cents(subtotal * rate),
  'px.order.total': cents(subtotal * (1 + rate))
}));
// A prefix query arrives as one object: address -> value, sorted by address.
pxc.register(pxFn('fn.order.line'), ({ order }) => Object.entries(order).map(([address, value]) => `${address.slice('px.order.'.length)}=${value}`).join(' '));

const composition = readPql(JSON.stringify({
  PrincipleComponentRender: 'order',
  Ticks: [
    { name: 'Sum', Calculations: [{ call: 'fn.order.total', with: { prices: 'px.order.prices' }, into: 'px.order.subtotal' }] },
    { name: 'Split', Calculations: [{ call: 'fn.order.split', with: { subtotal: 'px.order.subtotal' }, args: { rate: 0.08 }, into: ['px.order.tax', 'px.order.total'] }] },
    { name: 'Say', Calculations: [{ call: 'fn.order.line', with: { order: 'px.order.*' } , into: 'px.order.line' }] }
  ]
}), JSON.parse);

const run = invokePql(composition, { pxc });

console.log('subtotal: ', pxc.get('px.order.subtotal'));
console.log('tax:      ', pxc.get('px.order.tax'), '| total:', pxc.get('px.order.total'));
console.log('line:     ', pxc.get('px.order.line'));
console.log('produces: ', run.Ticks.flatMap((tick) => tick.Calculations.map((one) => `${tick.name}: ${one.produces.join(' + ')}`)).join(' | '));
console.log('inputs of Split:', run.Ticks[1].Calculations[0].inputs);
console.log('args of Split:  ', run.Ticks[1].Calculations[0].args);
console.log('board:    ', pxc.keys().sort().join(' '));
console.log('the run is a Part at px.pql.order:', pxc.has('px.pql.order'));
console.log('by hand:  ', Object.keys(queryPrefix(pxc, 'px.order.*')).join(' '));
console.log('no match: ', queryPrefix(pxc, 'px.nothing.*'));
```

```text
subtotal:  515
tax:       41.2 | total: 556.2
line:      prices=250,175,90 subtotal=515 tax=41.2 total=556.2
produces:  Sum: px.order.subtotal | Split: px.order.tax + px.order.total | Say: px.order.line
inputs of Split: { subtotal: 515 }
args of Split:   { rate: 0.08 }
board:     px.order.line px.order.prices px.order.subtotal px.order.tax px.order.total px.pql.order
the run is a Part at px.pql.order: true
by hand:   px.order.line px.order.prices px.order.subtotal px.order.tax px.order.total
no match:  {}
```

The Calculations of one Tick are parallel branches: none of them reads what another
one in the same Tick writes. That is why `Split` is its own Tick rather than a second
Calculation next to `Sum` -- it reads `px.order.subtotal`, which `Sum` publishes.

## 4. The receipt

`createStudioRuntime(world)` is the studio's own board: the same core, with the
domain Calculations already registered, the world published as Parts under
`px.domain.*`, and a memo ring so a second render of an unchanged card reuses the
material instead of recomputing it.

Every execution leaves a **receipt** at `px.receipt.<name>`, and it carries four
fields: the `composition` that ran, one `trace` row per invocation, and the `computed`
and `reused` counts. A trace row is the Calculation's own testimony -- which Tick,
which `fn.` address, what it read, what it published, whether it was reused, and the
**material** it produced, a `<tag>:<8 hex>` label over the inputs rather than a hash of
the bytes.

```js
import { createStudioRuntime } from '../src/runtime.js';
import { createSeed } from '../src/seed.js';

const studio = createStudioRuntime(createSeed());
const context = { bagId: 'everyday', competitionId: 'putterwarz', roundId: 'hole-1' };
const rendered = studio.card('buzzz-mint', 'broadcast', context);

const receipt = studio.pxc.get('px.receipt.display-card');
console.log('fields:  ', Object.keys(receipt));
console.log('render:  ', receipt.composition.PrincipleComponentRender);
console.log('computed:', receipt.computed, '| reused:', receipt.reused);
const material = (row) => `${row.material.split(':')[0]}:<8 hex>`;
for (const row of receipt.trace) {
  console.log(`  ${row.tick.padEnd(18)} ${row.call.padEnd(20)} -> ${row.output.padEnd(38)} reused=${row.reused} ${material(row)}`);
}
console.log('digests are 8 hex:', receipt.trace.every((row) => /^[a-z.]+:[0-9a-f]{8}$/.test(row.material)));
console.log('the card is a Part:', rendered.part, '| width:', rendered.width);

// The second render of an unchanged card recomputes nothing.
const again = studio.card('buzzz-mint', 'broadcast', context);
const second = studio.pxc.get('px.receipt.display-card');
console.log('again:   ', 'computed:', second.computed, '| reused:', second.reused, '| same svg:', again.svg === rendered.svg);

// Every receipt is itself readable through the prefix query px.receipt.*
const listed = studio.receipts();
console.log('receipts:', listed.rows.map((row) => `${row.name} (${row.invocations})`));
console.log('summary: ', { ...listed.summary, digest: '<8 hex>' });
```

```text
fields:   [ 'composition', 'trace', 'computed', 'reused' ]
render:   display-card
computed: 4 | reused: 0
  Fields:buzzz-mint  fn.domain.fields     -> px.render.single.buzzz-mint.fields     reused=false domain.fields:<8 hex>
  Art:buzzz-mint     fn.disc.art          -> px.render.single.buzzz-mint.art        reused=false disc.art:<8 hex>
  Card:buzzz-mint    fn.card.compose      -> px.render.single.buzzz-mint.card       reused=false card.compose:<8 hex>
  CardSvg:buzzz-mint fn.card.svg          -> px.render.single.buzzz-mint.svg        reused=false card.svg:<8 hex>
digests are 8 hex: true
the card is a Part: px.render.single.buzzz-mint.svg | width: 400
again:    computed: 0 | reused: 4 | same svg: true
receipts: [ 'display-card (4)' ]
summary:  { receipts: 1, invocations: 4, produces: 4, digest: '<8 hex>' }
```

`reused: true` is the studio saying it recognised the material, not that it skipped a
check: the memo key is `{ revision, inputs }`, so an edit anywhere upstream produces a
different material and the Calculation runs again.

## 5. The run record

`studio.runRecord(name)` turns the two Parts an execution already wrote --
`px.pql.<name>` and `px.receipt.<name>` -- into one `pyto-run-record@1` document
through `fromDiscStudioReceipt` (`pyto/viewer/adapters.js`), validates it with the
shared `validate`, and keeps it at `px.run.<name>`. It is the same document
`pyto.materialize.run_record` writes on the Python side, field for field
(`pyto/viewer/RECORD.md`), which is why the standalone Tick viewer renders either one.

```js
import { createStudioRuntime } from '../src/runtime.js';
import { createSeed } from '../src/seed.js';
import { fromDiscStudioReceipt, validate } from '../pyto/viewer/adapters.js';

const studio = createStudioRuntime(createSeed());
studio.card('buzzz-mint', 'broadcast', { bagId: 'everyday', competitionId: 'putterwarz', roundId: 'hole-1' });

const { address, record } = studio.runRecord('display-card');
console.log('kept at:  ', address);
console.log('schema:   ', record.schema, '| pcr:', record.pcr);
console.log('source:   ', record.source);
console.log('counters: ', record.counters);
console.log('ticks:    ', record.ticks.map((tick) => `${tick.index}:${tick.name}`).join(' '));

const first = record.ticks[0].invocations[0];
console.log('invocation fields:', Object.keys(first).join(' '));
console.log('  id:              ', first.id);
console.log('  calculation:     ', first.calculation.address, '|', first.calculation.identity_scope);
console.log('  inputs:          ', first.inputs);
console.log('  declared_consumes:', first.declared_consumes);
console.log('  actual_produces: ', first.actual_produces);
console.log('  writes:          ', JSON.stringify(first.writes));
console.log('  hit:             ', first.hit, '| duration_ms:', first.duration_ms, '| value.kind:', first.value.kind);
for (const [at, part] of Object.entries(record.parts)) console.log(`  part ${at.padEnd(38)} written_by=${String(part.written_by).padEnd(38)} preexisting=${part.preexisting}`);

// The adapter is the whole of it: the same two Parts, by hand, are the same document.
const byHand = fromDiscStudioReceipt(studio.pxc.get('px.pql.display-card'), studio.pxc.get('px.receipt.display-card'));
console.log('by hand == runRecord:', JSON.stringify(byHand) === JSON.stringify(record));
console.log('validate returns it: ', validate(record) === record);
try {
  validate({ ...record, schema: 'something-else@1' });
} catch (refused) {
  console.log('validate refuses:    ', refused.message);
}
```

```text
kept at:   px.run.display-card
schema:    pyto-run-record@1 | pcr: display-card
source:    { runtime: 'discstudio', version: null, commit: null }
counters:  { invocations: 4, hits: 3, computed: 1, wall_ms: null }
ticks:     0:Fields:buzzz-mint 1:Art:buzzz-mint 2:Card:buzzz-mint 3:CardSvg:buzzz-mint
invocation fields: id calculation inputs args into declared_consumes actual_consumes actual_produces writes duration_ms result_sha256 hit value
  id:               px.render.single.buzzz-mint.fields
  calculation:      fn.domain.fields | registered-address-and-revision:1
  inputs:           { material: 'px:px.render.single.buzzz-mint.inputs' }
  declared_consumes: [ 'px:px.render.single.buzzz-mint.inputs' ]
  actual_produces:  [ 'px.render.single.buzzz-mint.fields' ]
  writes:           [{"address":"px.render.single.buzzz-mint.fields","kind":"new-address"}]
  hit:              true | duration_ms: null | value.kind: json
  part px.render.single.buzzz-mint.inputs     written_by=null                                   preexisting=true
  part px.render.single.buzzz-mint.fields     written_by=px.render.single.buzzz-mint.fields     preexisting=false
  part px.domain.Disc.buzzz-mint              written_by=null                                   preexisting=true
  part px.domain.Mold.buzzz                   written_by=null                                   preexisting=true
  part px.domain.Manufacturer.discraft        written_by=null                                   preexisting=true
  part px.render.single.buzzz-mint.art        written_by=px.render.single.buzzz-mint.art        preexisting=false
  part px.presentation.broadcast              written_by=null                                   preexisting=true
  part px.render.single.buzzz-mint.entry      written_by=null                                   preexisting=true
  part px.render.single.buzzz-mint.card       written_by=px.render.single.buzzz-mint.card       preexisting=false
  part px.render.single.buzzz-mint.svg        written_by=px.render.single.buzzz-mint.svg        preexisting=false
by hand == runRecord: true
validate returns it:  true
validate refuses:     pyto-run-record@1 schema: expected "pyto-run-record@1", got "something-else@1"
```

`hit` is the one word worth learning: an invocation is a hit when it read a Part that
already existed before this run, or when the runtime reports reuse. Everything else was
computed in front of you. `duration_ms` and `wall_ms` are null here on purpose -- the
studio records materials and reuse, never a clock, so two runs of the same render
produce the same document byte for byte.

## 6. Undo, as a Part

Undo is not a second history hidden in the app. `fn.undo.push` records the value an
address holds now, `fn.undo.pop` hands back the recorded value, `fn.undo.settle` takes
it off the stack -- three ordinary Calculations over one Part, `px.undo.<scope>`, so
every undo is on the record like everything else.

```js
import { createStudioRuntime } from '../src/runtime.js';
import { createSeed } from '../src/seed.js';

const studio = createStudioRuntime(createSeed());
const stack = () => studio.pxc.get('px.undo.notes');

studio.pxc.set('px.note.title', 'Tuesday league');
console.log('depth:', studio.undo.depth('notes'), '| title:', studio.pxc.get('px.note.title'));

studio.undo.push('px.note.title', 'notes');
studio.pxc.set('px.note.title', 'Tuesday league (edited)');
console.log('after push and edit:', studio.pxc.get('px.note.title'), '| depth:', studio.undo.depth('notes'));
console.log('the stack is a Part:', stack().entries.map((entry) => [entry.depth, entry.address, entry.value]));

const run = studio.undo.pop('px.note.title', 'notes');
console.log('after pop:          ', studio.pxc.get('px.note.title'), '| depth:', studio.undo.depth('notes'));
console.log('pop ran:            ', run.trace.map((row) => `${row.call} -> ${row.output}`));

// A pop with nothing recorded changes nothing, and is still on the record.
const empty = studio.undo.pop('px.note.title', 'notes');
console.log('pop of an empty stack:', studio.pxc.get('px.note.title'), '| depth:', studio.undo.depth('notes'));
console.log('and still a receipt:  ', empty.trace.map((row) => row.call));
console.log('the studio scope is separate:', studio.undo.depth(), studio.pxc.get('px.undo.studio').scope);
```

```text
depth: 0 | title: Tuesday league
after push and edit: Tuesday league (edited) | depth: 1
the stack is a Part: [ [ 1, 'px.note.title', 'Tuesday league' ] ]
after pop:           Tuesday league | depth: 0
pop ran:             [ 'fn.undo.pop -> px.note.title', 'fn.undo.settle -> px.undo.notes' ]
pop of an empty stack: Tuesday league | depth: 0
and still a receipt:   [ 'fn.undo.pop', 'fn.undo.settle' ]
the studio scope is separate: 0 studio
```

`studio.undo.push(address)` with no scope records into `px.undo.studio`, which is what
the studio itself pushes before every command it dispatches: pop that scope and the
whole world Part is restored, revalidated and republished.

## 7. What not to do

Three mistakes, with the message you get. The first two are refused when the document
is *read*, before a single Calculation runs; the third is refused mid-run and publishes
nothing at all, which is the point.

```js
import { createExecBoard, invokePql, pxFn, readPql } from '../src/core/exec.js';

const read = (calculations) => readPql(JSON.stringify({ PrincipleComponentRender: 'p', Ticks: [{ name: 'Prepare', Calculations: calculations }] }), JSON.parse);
// invokePql wraps what failed in the Tick that failed, so read the whole chain.
const chain = (error) => { const messages = []; for (let one = error; one; one = one.cause) messages.push(one.message); return messages; };

// 1. A name that is not a registered fn. address.
try {
  read([{ call: 'total', with: {}, into: 'px.a' }]);
} catch (refused) {
  console.log('1:', refused.message);
}

// 2. The same name in `with` and in `args`: which one wins is not a thing to guess.
try {
  read([{ call: 'fn.order.total', with: { rate: 'px.order.rate' }, args: { rate: 0.08 }, into: 'px.a' }]);
} catch (refused) {
  console.log('2:', refused.message);
}

// 3. `into` declares two addresses and the Calculation hands back one of them.
const pxc = createExecBoard();
pxc.set('px.order.prices', [250, 175, 90]);
pxc.register(pxFn('fn.order.split'), ({ prices }) => ({ 'px.order.tax': prices.length }));
const composition = read([{ call: 'fn.order.split', with: { prices: 'px.order.prices' }, into: ['px.order.tax', 'px.order.total'] }]);
try {
  invokePql(composition, { pxc });
} catch (refused) {
  for (const message of chain(refused)) console.log('3:', message);
}
console.log('   published nothing:', pxc.has('px.order.tax'), pxc.has('px.order.total'));
console.log('   board unchanged:  ', pxc.keys());
```

```text
1: PQL Prepare.Calculations[0].call: expected a registered fn. address.
2: PQL Prepare.Calculations[0]: 'rate' appears in both with and args.
3: PQL Prepare: fn.order.split -> px.order.tax, px.order.total failed.
3: PQL Prepare.fn.order.split.into: the output has no key 'px.order.total'; every declared produce must be present, and nothing is silently dropped.
   published nothing: false false
   board unchanged:   [ 'px.order.prices' ]
```

The fix for 3 is always one of two things: return the address the document declared,
or stop declaring it. Nothing is written until every declared address is present, so a
half-published render is not a state you can reach.

{?} ParallelSectionWaitsForTask48

## Where to go next

- `pyto/USE.md` -- the same page for the Python side, and the source of the vocabulary.
- `pyto/viewer/RECORD.md` -- the run record, field by field.
- `tests/core.test.js` -- the executable spec of everything above.
- `tests/use-js.test.js` -- this page, executed.
