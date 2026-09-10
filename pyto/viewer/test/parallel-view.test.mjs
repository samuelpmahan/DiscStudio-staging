/**
 * Parallel you can see: the Tick viewer draws a Tick's Calculations side by side
 * when they are parallel branches, prints the Tick's work against its latency and
 * the run's work against its critical path, and shows the placement and budget a
 * record carries -- never requiring any of it.
 *
 * The assertions are on the rendered tree and on exact printed text, against the
 * same minimal document shim the other render tests use (no jsdom, no dependency).
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, join } from 'node:path';

import { fromPytoRecord } from '../adapters.js';
import { renderRecord, isParallelTick, tickWorkMs, tickLatencyMs, runWorkMs, runCriticalPathMs } from '../tick-viewer.js';
import { composePage, buildPage, PAGE_SOURCES } from '../embed.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const VIEWER = resolve(HERE, '..');
const readJson = (path) => JSON.parse(readFileSync(path, 'utf8'));

// The record the students homework actually wrote: four Ticks, the second (Stats)
// holding mean and median, which both bind Parse's roster and neither of which
// reads the other (experiments/students/README.md, experiments/tick-laws/README.md).
const STUDENTS = resolve(VIEWER, '..', 'experiments', 'students', 'evidence', 'run-1', 'record.json');
const students = fromPytoRecord(readJson(STUDENTS));
// Hand-made, and the only record here carrying the placement/latency/parallel/budget
// contract: a runtime that reports them renders them, a runtime that does not is
// rendered exactly as before.
const demo = fromPytoRecord(readJson(resolve(VIEWER, 'fixtures', 'parallel-demo.json')));

/* ---------------------------------------------------------------- */
/* the shim                                                          */
/* ---------------------------------------------------------------- */

function createStubDocument() {
  return {
    createElement(tagName) {
      return {
        tagName: String(tagName).toLowerCase(),
        className: '',
        textContent: '',
        attributes: Object.create(null),
        children: [],
        appendChild(child) {
          this.children.push(child);
          return child;
        },
        setAttribute(name, value) {
          this.attributes[name] = String(value);
        },
        getAttribute(name) {
          return name in this.attributes ? this.attributes[name] : null;
        }
      };
    }
  };
}

function* walk(node) {
  yield node;
  for (const child of node.children) yield* walk(child);
}

const withClass = (root, className) => [...walk(root)].filter((node) => String(node.className).split(/\s+/).includes(className));
const textOf = (node) => [...walk(node)].map((n) => n.textContent).join(' ');
const doc = createStubDocument();

/** The invocation cards of one Tick section, in render order. */
const cardsOf = (section) => withClass(section, 'inv');
/** The branch columns of one Tick section: empty for a Tick drawn serially. */
const branchesOf = (section) => withClass(section, 'branch');

/* ---------------------------------------------------------------- */
/* (a) the students record: one parallel Tick, three serial ones     */
/* ---------------------------------------------------------------- */

test('the students record draws Stats as two side-by-side branches and the other three Ticks as one card each', () => {
  const root = renderRecord(students, { doc });
  const sections = withClass(root, 'tick');
  assert.deepEqual(sections.map((s) => withClass(s, 'tick-name')[0].textContent), ['Parse', 'Stats', 'Letters', 'Histogram']);

  // Stats is the row of columns; every other Tick keeps its cards as direct children.
  assert.deepEqual(sections.map((s) => branchesOf(s).length), [0, 2, 0, 0]);
  assert.deepEqual(sections.map((s) => cardsOf(s).length), [1, 2, 1, 1]);
  assert.deepEqual(sections.map((s) => s.getAttribute('data-parallel')), ['no', 'yes', 'no', 'no']);

  const stats = sections[1];
  assert.deepEqual(cardsOf(stats).map((card) => card.getAttribute('data-invocation')), ['mean', 'median']);
  // Each branch column holds exactly one card, so the two are laid out beside
  // each other rather than one under the other.
  assert.deepEqual(branchesOf(stats).map((branch) => cardsOf(branch).length), [1, 1]);
  assert.equal(withClass(stats, 'tick-mode')[0].textContent, 'parallel · 2 branches');

  // The numbers tick_laws.py prints for this record, printed under the Tick:
  // Tick 1 Stats work_ms=0.040953... latency_ms=0.025237...
  assert.equal(withClass(stats, 'tick-meta')[0].textContent, '2 invocations · work 0.041 ms · latency 0.025 ms');
  assert.equal(withClass(sections[0], 'tick-meta')[0].textContent, '1 invocation · work 0.030 ms · latency 0.030 ms');
  assert.equal(withClass(root, 'run-timing')[0].textContent, 'work 0.110 ms · critical path 0.095 ms');

  // Stats is the one Tick whose work exceeds its latency; the others spend exactly
  // as much time as work (experiments/students/README.md says this in words).
  students.ticks.forEach((tick, index) => {
    const work = tickWorkMs(tick);
    const latency = tickLatencyMs(tick);
    if (index === 1) assert.ok(work > latency, 'Stats does more work than it takes time');
    else assert.equal(work, latency, tick.name);
  });
  assert.ok(runCriticalPathMs(students) < runWorkMs(students));
});

test('a record that carries no placement, latency, parallel or budget field renders none of them', () => {
  const root = renderRecord(students, { doc });
  assert.equal(withClass(root, 'placement').length, 0, 'no worker labels invented');
  assert.equal(withClass(root, 'budget-banner').length, 0, 'no budget banner invented');
  assert.equal(withClass(root, 'run-mode').length, 0, 'no parallel claim invented');
  // The latency printed above is derived from the durations, not read from a field.
  assert.ok(students.ticks.every((tick) => !('latency_ms' in tick)));
});

/* ---------------------------------------------------------------- */
/* (b) the contract, rendered: worker, budget, header numbers        */
/* ---------------------------------------------------------------- */

test('the parallel-demo record prints its worker labels, its budget banner and its header numbers exactly', () => {
  const root = renderRecord(demo, { doc });

  assert.equal(withClass(root, 'run-timing')[0].textContent, 'work 6.500 ms · critical path 4.500 ms');
  assert.equal(withClass(root, 'run-mode')[0].textContent, 'parallel: the branches inside a Tick ran at once');
  assert.equal(withClass(root, 'budget-banner')[0].textContent, 'budget: stopped after tick "Score" · limit 5.000 ms');

  // One label per card, in render order: Fan's two branches sat on two workers.
  assert.deepEqual(withClass(root, 'placement').map((node) => node.textContent), ['worker 0', 'worker 0', 'worker 1', 'worker 0']);
  const fan = withClass(root, 'tick')[1];
  assert.deepEqual(branchesOf(fan).map((branch) => withClass(branch, 'placement')[0].textContent), ['worker 0', 'worker 1']);
  assert.equal(withClass(fan, 'placement')[0].getAttribute('title'), 'started 1.000 ms');
  assert.equal(withClass(fan, 'tick-meta')[0].textContent, '2 invocations · work 5.000 ms · latency 3.000 ms');
  assert.deepEqual(withClass(root, 'tick').map((s) => branchesOf(s).length), [0, 2, 0]);
});

test('a Tick prints the latency the record recorded, not the longest branch, when the two differ', () => {
  const withLatency = structuredClone(demo);
  // A real run's Tick is slower than its longest branch: hand-off, scheduling, a
  // worker that started late. `latency_ms` is what the runtime measured, so it wins.
  withLatency.ticks[1].latency_ms = 4.25;
  const root = renderRecord(withLatency, { doc });
  assert.equal(withClass(withClass(root, 'tick')[1], 'tick-meta')[0].textContent, '2 invocations · work 5.000 ms · latency 4.250 ms');
  assert.equal(withClass(root, 'run-timing')[0].textContent, 'work 6.500 ms · critical path 5.750 ms');

  const withoutLatency = structuredClone(demo);
  for (const tick of withoutLatency.ticks) delete tick.latency_ms;
  const bare = renderRecord(withoutLatency, { doc });
  assert.equal(withClass(withClass(bare, 'tick')[1], 'tick-meta')[0].textContent, '2 invocations · work 5.000 ms · latency 3.000 ms');
});

test('a budget the run completed is not a banner; an incomplete one always names where it stopped', () => {
  const completed = structuredClone(demo);
  completed.budget = { limit_ms: 5.0, stopped_after_tick: null, completed: true };
  assert.equal(withClass(renderRecord(completed, { doc }), 'budget-banner').length, 0);

  const noLimit = structuredClone(demo);
  noLimit.budget = { limit_ms: null, stopped_after_tick: 'Fan', completed: false };
  assert.equal(
    withClass(renderRecord(noLimit, { doc }), 'budget-banner')[0].textContent,
    'budget: stopped after tick "Fan" · no limit recorded'
  );
});

/* ---------------------------------------------------------------- */
/* (c) a sibling read is not a parallel Tick                         */
/* ---------------------------------------------------------------- */

test('a Tick whose Calculation reads a sibling\'s produce is drawn serially, never side by side', () => {
  const serial = structuredClone(demo);
  // `right` now binds `left`'s result: the two are a chain inside one Tick, which
  // the node law refuses and the page must not draw as branches.
  serial.ticks[1].invocations[1].inputs = { rows: 'fn:load', left: 'fn:left' };
  const record = fromPytoRecord(serial);

  assert.equal(isParallelTick(record.ticks[1]), false);
  const fan = withClass(renderRecord(record, { doc }), 'tick')[1];
  assert.equal(branchesOf(fan).length, 0, 'no branch columns');
  assert.equal(cardsOf(fan).length, 2, 'both cards still shown, one under the other');
  assert.equal(withClass(fan, 'tick-mode').length, 0, 'no parallel badge');
  assert.equal(fan.getAttribute('data-parallel'), 'no');
  assert.ok(textOf(fan).includes('fn:left'), 'the sibling read is on the page');

  // The same Tick is parallel again once that binding goes back to Parse's result.
  const restored = fromPytoRecord(structuredClone(demo));
  assert.equal(isParallelTick(restored.ticks[1]), true);

  // A store read of a sibling's Part counts too, not only a result read.
  const viaStore = structuredClone(demo);
  viaStore.ticks[1].invocations[1].actual_consumes = ['px.demo.left'];
  assert.equal(isParallelTick(fromPytoRecord(viaStore).ticks[1]), false);
});

/* ---------------------------------------------------------------- */
/* (d) the same record renders to the same bytes                     */
/* ---------------------------------------------------------------- */

test('composePage is a pure function of its sources: the same record twice is the same bytes', () => {
  const [html, adapters, viewer] = PAGE_SOURCES.map((name) => readFileSync(resolve(VIEWER, name), 'utf8'));
  for (const record of [students, demo]) {
    const first = composePage({ html, adapters, viewer, record });
    const second = composePage({ html, adapters, viewer, record });
    assert.equal(first, second, `${record.pcr}: two builds, one byte string`);
    assert.equal(Buffer.compare(Buffer.from(first, 'utf8'), Buffer.from(second, 'utf8')), 0);
    assert.ok(first.includes('class="branches"') === false, 'the page ships the renderer, not a rendering');
    // The record itself is in the page, so the bytes cover the record as well as the code.
    assert.ok(first.includes(JSON.stringify(record.pcr).slice(1, -1)));
  }

  // Two records that differ produce different bytes -- the equality above is not
  // an artefact of composePage ignoring what it was handed.
  const one = composePage({ html, adapters, viewer, record: students });
  const other = composePage({ html, adapters, viewer, record: demo });
  assert.notEqual(one, other);
});

test('rendering the same record twice builds the same tree, and rendering never mutates the record', () => {
  const before = JSON.stringify(demo);
  const shape = (node) => ({
    tag: node.tagName,
    className: node.className,
    text: node.textContent,
    attrs: { ...node.attributes },
    children: node.children.map(shape)
  });
  assert.deepEqual(shape(renderRecord(demo, { doc })), shape(renderRecord(demo, { doc })));
  assert.equal(JSON.stringify(demo), before, 'the renderer reads the record and writes nothing back');
});

test('the standalone page keeps the contract fields and its inlined bundle is one valid module', () => {
  const page = buildPage(demo);
  // The page is what somebody opens with no server: the fields it renders have to
  // survive being baked into it, and the two modules have to concatenate into one
  // script that actually parses (a name declared by both would be a SyntaxError
  // nobody sees until the page is opened).
  for (const field of ['"placement"', '"latency_ms"', '"parallel"', '"budget"', '"stopped_after_tick"']) {
    assert.ok(page.includes(field), `the embedded record keeps ${field}`);
  }
  assert.ok(page.includes('.branches {'), 'the page carries the side-by-side layout');

  const open = '<script type="module">\n/* adapters.js + tick-viewer.js, inlined by embed.mjs. No imports, no network. */\n';
  const start = page.indexOf(open);
  assert.ok(start > -1, 'the page carries the inlined bundle');
  const end = page.indexOf('</script>', start);
  const bundle = page.slice(start + open.length, end).replaceAll('<\\/script', '</script');
  const file = join(mkdtempSync(join(tmpdir(), 'tick-bundle-')), 'bundle.mjs');
  writeFileSync(file, bundle);
  execFileSync(process.execPath, ['--check', file]);
});
