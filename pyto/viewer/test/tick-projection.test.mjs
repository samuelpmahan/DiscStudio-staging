/**
 * The Tick projection agrees between languages: `adapters.js` `tickProjection`
 * and `pyto.px`'s `tick_projection` (pyto/src/pyto/px.py) read the same four
 * facts -- consumes, internal, produces, calculations -- off the same record.
 * `px tick --json` emits Python's side; this file calls it as a subprocess
 * (the way `viewer/test/test_record_schema.py` calls `validate_cases.mjs` in
 * the other direction, `emit_adapter_records.mjs`/`record_schema.py` bridging
 * the other way again) and compares it, Tick by Tick, against the JavaScript
 * reader over the students and parallel-demo fixtures.
 *
 * `latency_ms` is compared rounded to 3 decimal places rather than exactly:
 * when a Tick carries no explicit `latency_ms` of its own (every Tick of the
 * students record), the Python fallback (`record_schema.tick_latency_ms`)
 * sums raw durations while the JavaScript fallback
 * (`adapters.js tickLatencyMsFromRecord`) rounds that sum to 3 decimals -- a
 * pre-existing difference between the two shared readers neither this task
 * nor any other test exercises on that path before now
 * (`{?} TickProjectionLatencyRounding`). `consumes`, `internal`, `produces`
 * and `calculations` -- the four facts the projection exists for -- are
 * compared exactly, with no tolerance.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

import { fromPytoRecord, tickProjection } from '../adapters.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const VIEWER = resolve(HERE, '..');
const PYTO = resolve(VIEWER, '..');
const readJson = (path) => JSON.parse(readFileSync(path, 'utf8'));

const STUDENTS = resolve(PYTO, 'experiments', 'students', 'evidence', 'run-1', 'record.json');
const PARALLEL_DEMO = resolve(VIEWER, 'fixtures', 'parallel-demo.json');

/** The first of PYTHON, python3, python that actually runs here, or null. */
function findPython() {
  for (const candidate of [process.env.PYTHON, 'python3', 'python']) {
    if (!candidate) continue;
    try {
      execFileSync(candidate, ['--version'], { stdio: 'ignore' });
      return candidate;
    } catch {
      // try the next candidate
    }
  }
  return null;
}

const PYTHON = findPython();
const needsPython = { skip: PYTHON ? false : 'no python interpreter is on PATH' };

/** `px tick <record> --json`, the way `tests/test_px.py` `run_px` calls it: a
 * subprocess with `PYTHONPATH` pointed at `src`, so this runs unmodified
 * whether or not pyto is installed. */
function pythonTickProjections(recordPath) {
  const stdout = execFileSync(PYTHON, ['-m', 'pyto.px', 'tick', recordPath, '--json'], {
    cwd: PYTO,
    env: { ...process.env, PYTHONPATH: resolve(PYTO, 'src') },
    encoding: 'utf8'
  });
  return JSON.parse(stdout);
}

const round3 = (value) => (typeof value === 'number' ? Math.round(value * 1000) / 1000 : value);
const normalize = (projection) => ({ ...projection, latency_ms: round3(projection.latency_ms) });

for (const [label, path] of [['students', STUDENTS], ['parallel-demo', PARALLEL_DEMO]]) {
  test(`tickProjection agrees with px tick --json on ${label}`, needsPython, () => {
    const record = fromPytoRecord(readJson(path));
    const python = pythonTickProjections(path).map(normalize);
    const javascript = record.ticks.map((_, index) => normalize(tickProjection(record, index)));
    assert.equal(python.length, record.ticks.length, 'not vacuous: every Tick came back');
    assert.deepEqual(javascript, python);
  });

  test(`tickProjection's four compared facts need no rounding on ${label}`, needsPython, () => {
    // The claim behind the tolerance above, stated so a reader need not infer it
    // from a diff: without normalizing latency_ms, consumes/internal/produces/
    // calculations already agree exactly -- only the schedule fallback differs.
    const record = fromPytoRecord(readJson(path));
    const python = pythonTickProjections(path);
    const javascript = record.ticks.map((_, index) => tickProjection(record, index));
    for (const facet of ['index', 'name', 'consumes', 'internal', 'produces', 'calculations']) {
      assert.deepEqual(javascript.map((p) => p[facet]), python.map((p) => p[facet]), facet);
    }
  });
}

test('tickProjection throws a named error for an out-of-range index', () => {
  const record = fromPytoRecord(readJson(STUDENTS));
  assert.throws(() => tickProjection(record, 99), /no Tick at index 99 \(record has 4\)/);
});

test('tickProjection: internal is the intersection of reads and this Tick\'s own produces', () => {
  // Stats (index 1) reads Parse's roster and produces mean/median: nothing it
  // reads is also something it produced, so internal is empty and consumes
  // carries the one external read -- the students record chains no Tick.
  const record = fromPytoRecord(readJson(STUDENTS));
  const stats = tickProjection(record, 1);
  assert.deepEqual(stats.internal, []);
  assert.deepEqual(stats.consumes, ['px.students.roster']);
  assert.deepEqual(stats.calculations, ['fn.students.mean@52c2348bf909', 'fn.students.median@e40b65bbc48b']);
});

test('tickProjection: a sibling that reads an earlier sibling\'s produce is internal, not consumes', () => {
  // The same mutation pyto/tests/test_px.py makes for the Python side: median
  // reads mean's result, so px.students.mean moves from consumes to internal.
  const record = fromPytoRecord(readJson(STUDENTS));
  const chained = structuredClone(record);
  chained.ticks[1].invocations[1].inputs = { roster: 'fn:mean' };
  const stats = tickProjection(chained, 1);
  assert.deepEqual(stats.internal, ['px.students.mean']);
  assert.deepEqual(stats.consumes, ['px.students.roster']);
});
