/**
 * Every adapter output passes validate; hit derivation matches RECORD.md; a
 * schema violation throws with the path that names it.
 *
 * The DiscStudio case is checked twice: against the committed fixture and
 * against a live run of ../../../src/runtime.js, so the fixture cannot drift
 * away from the runtime it claims to come from.
 *
 * The pyto fixture is the byte-for-byte file `pyto.materialize.run_record`
 * wrote for grouped-ablation run-1, not a transcription of it: the first test
 * below compares the two files and fails if they diverge. Its values are all
 * `json`, which is what that run actually produces, so the four other value
 * kinds are covered by `pyto-value-kinds.json` -- a synthetic record, named as
 * one, used only where the real run has nothing to show.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

import {
  SCHEMA, MAX_ARRAY_ENTRIES, MAX_VALUE_BYTES, PNG_DATA_URL_PREFIX,
  validate, RecordSchemaError, materialize, deriveHit, derivePartIndex, bareAddress,
  parseBinding, produceAddresses,
  tickLatencyMsFromRecord, invocationPlacement, runSchedule,
  fromPytoRecord, fromDiscStudioReceipt, fromChessLabReceipts, fromWumpusRecords
} from '../adapters.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const fixture = (name) => JSON.parse(readFileSync(resolve(HERE, '..', 'fixtures', name), 'utf8'));

const pytoDoc = fixture('pyto-grouped-ablation.json');
const valueKindsDoc = fixture('pyto-value-kinds.json');
const dsDoc = fixture('discstudio-display-card.json');
const chessDoc = fixture('chesslab-s0-s1.json');
const wumpusDoc = fixture('wumpus-belief-tick.json');

const invocations = (record) => record.ticks.flatMap((tick) => tick.invocations);
const byId = (record, id) => invocations(record).find((invocation) => invocation.id === id);

/** The file pyto.materialize.run_record wrote, as committed under experiments/. */
const REAL_RECORD = resolve(HERE, '..', '..', 'experiments', 'grouped-ablation', 'evidence', 'run-1', 'record.json');

/* ---------------------------------------------------------------- */

test('the pyto fixture is the Python materializer output byte for byte', () => {
  // Not "equivalent JSON": the same bytes. RECORD.md asks for sorted keys and
  // two-space indentation, so a record that round-trips through both runtimes
  // has one spelling, and the viewer is tested against the producer's own file
  // rather than against a transcription that can quietly drift from it.
  assert.equal(
    readFileSync(resolve(HERE, '..', 'fixtures', 'pyto-grouped-ablation.json'), 'utf8'),
    readFileSync(REAL_RECORD, 'utf8'),
    'fixtures/pyto-grouped-ablation.json must be a copy of experiments/grouped-ablation/evidence/run-1/record.json'
  );
});

test('every adapter output passes validate', () => {
  const records = [
    fromPytoRecord(pytoDoc),
    fromPytoRecord(valueKindsDoc),
    fromDiscStudioReceipt(dsDoc.first.pql, dsDoc.first.receipt, { version: 'transcribed-82f8fc9' }),
    fromDiscStudioReceipt(dsDoc.second.pql, dsDoc.second.receipt),
    fromChessLabReceipts(chessDoc.receipts, { pcr: 'chesslab.debugger' }),
    fromWumpusRecords(wumpusDoc.records, { pcr: 'wumpus.belief' })
  ];
  for (const record of records) {
    assert.equal(validate(record), record);
    assert.equal(record.schema, SCHEMA);
    record.ticks.forEach((tick, index) => assert.equal(tick.index, index));
  }
  assert.deepEqual(records.map((r) => r.source.runtime), ['pyto', 'pyto', 'discstudio', 'discstudio', 'chesslab', 'wumpus']);
});

test('fromPytoRecord is a validating pass-through, from an object or a string', () => {
  const fromObject = fromPytoRecord(pytoDoc);
  const fromText = fromPytoRecord(JSON.stringify(pytoDoc));
  assert.deepEqual(fromText, fromObject);
  assert.equal(fromObject, pytoDoc, 'the same object is returned, not a copy');
  assert.throws(() => fromPytoRecord({ ...pytoDoc, schema: 'pyto-run-record@2' }), /schema: expected "pyto-run-record@1"/);
});

/* ---------------------------------------------------------------- */
/* hit derivation                                                    */
/* ---------------------------------------------------------------- */

test('deriveHit: a px: binding not produced earlier in the run is a hit', () => {
  const produced = new Set(['scratch.ablation.split']);
  assert.equal(deriveHit(['px:input.ablation.rows'], produced), true, 'preexisting Part read');
  assert.equal(deriveHit(['px:scratch.ablation.split'], produced), false, 'produced by this run');
  assert.equal(deriveHit(['fn:split'], produced), false, 'a result ref is not a Part read');
  assert.equal(deriveHit([], produced), false, 'reads nothing');
  assert.equal(deriveHit([], produced, true), true, 'the runtime reported reuse');
});

test('deriveHit: an address this run overwrote is not a hit, however it started life', () => {
  // The reference rule for the one shape the two runtimes disagreed on: a Part
  // that existed before the run, was refined by an earlier invocation of it, and
  // is then read again. Nothing was reused -- the reader sees the freshly
  // computed value -- and RECORD.md:104-105 excludes it in its own parenthetical
  // ("whose address was not produced by an earlier invocation of the same run").
  // deriveHit never consults a preexisting set, so `produced` alone decides;
  // pyto.materialize.run_record now says the same, pinned in
  // pyto/tests/test_materialize.py
  // (HitLedger.test_re_reading_a_part_this_run_overwrote_is_not_a_hit_as_in_javascript).
  const before = new Set();
  assert.equal(deriveHit(['px:shared.counter'], before), true, 'first read: nothing produced it yet');
  const after = new Set(['shared.counter']);
  assert.equal(deriveHit(['px:shared.counter'], after), false, 'this run wrote it; nothing was reused');
});

test('pyto record: hits are exactly the invocations that read a preexisting Part', () => {
  const record = fromPytoRecord(pytoDoc);
  const hits = invocations(record).filter((invocation) => invocation.hit).map((invocation) => invocation.id);
  assert.deepEqual(hits, ['select', 'split']);
  assert.equal(record.counters.hits, 2);
  assert.equal(record.counters.hits + record.counters.computed, record.counters.invocations);
  // The twelve fit/score invocations read `fn:split`, a result of this run, and
  // `compare` reads only score results, so none of them is a hit -- the two
  // px: readers of the seeded input Parts are.
  assert.deepEqual(invocations(record).filter((i) => !i.hit).map((i) => i.id).length, 13);
  assert.equal(byId(record, 'fit.all').hit, false);
  assert.equal(byId(record, 'compare').hit, false);
});

test('DiscStudio: reused === true makes every invocation of the second run a hit', () => {
  const first = fromDiscStudioReceipt(dsDoc.first.pql, dsDoc.first.receipt);
  const second = fromDiscStudioReceipt(dsDoc.second.pql, dsDoc.second.receipt);
  // Task 78: the card chain carries the Cascade Tick (fn.cards.effective then
  // fn.cards.apply), so a display-card run is six invocations, not four.
  assert.equal(dsDoc.first.receipt.computed, 6);
  assert.equal(dsDoc.second.receipt.reused, 6);
  assert.equal(second.counters.hits, 6);
  assert.equal(second.counters.computed, 0);
  assert.ok(invocations(second).every((invocation) => invocation.hit));
  // First run: nothing is reused, so only the reads of Parts seeded before the
  // run count. CardSvg reads only the card this run produced -> computed.
  const cardSvg = byId(first, 'px.render.single.buzzz-mint.svg');
  assert.equal(cardSvg.hit, false);
  assert.deepEqual(cardSvg.declared_consumes, ['px:px.render.single.buzzz-mint.card']);
  assert.equal(first.counters.hits, 5, 'Fields, Art, Card and both Cascade steps read a Part seeded before the run');
});

test('DiscStudio: material identity, memo revision and the SVG wrapper survive the mapping', () => {
  const first = fromDiscStudioReceipt(dsDoc.first.pql, dsDoc.first.receipt);
  const art = byId(first, 'px.render.single.buzzz-mint.art');
  assert.equal(art.calculation.address, 'fn.disc.art');
  assert.equal(art.calculation.implementation_sha256, null, 'runtime.js hashes the memo signature, never the body');
  assert.equal(art.calculation.identity_scope, 'registered-address-and-revision:1');
  assert.match(art.result_sha256, /^disc\.art:[0-9a-f]+$/);
  assert.equal(art.duration_ms, null, 'runtime.js records no durations');

  const svg = byId(first, 'px.render.single.buzzz-mint.svg');
  assert.equal(svg.value.kind, 'svg');
  assert.ok(svg.value.data.startsWith('<svg'));
  assert.match(svg.value.note, /DiscStudio card wrapper/);
});

test('DiscStudio adapter also accepts a live run of src/runtime.js', async () => {
  const { createStudioRuntime } = await import('../../../src/runtime.js');
  const { createSeed } = await import('../../../src/seed.js');
  const runtime = createStudioRuntime(createSeed());
  const context = { bagId: 'everyday', competitionId: 'putterwarz', roundId: 'hole-1' };
  runtime.card('buzzz-mint', 'broadcast', context);
  const live = fromDiscStudioReceipt(runtime.pxc.get('px.pql.display-card'), runtime.pxc.get('px.receipt.display-card'));
  validate(live);
  assert.equal(live.pcr, 'display-card');
  const fromFixture = fromDiscStudioReceipt(dsDoc.first.pql, dsDoc.first.receipt);
  assert.deepEqual(live.ticks.map((t) => t.name), fromFixture.ticks.map((t) => t.name));
  assert.deepEqual(invocations(live).map((i) => i.id), invocations(fromFixture).map((i) => i.id));
  assert.deepEqual(live.counters, fromFixture.counters);
});

test('ChessLab: one invocation per frozen Calculation, values omitted, divergence preserved', () => {
  const record = fromChessLabReceipts(chessDoc.receipts, { pcr: 'chesslab.debugger' });
  assert.deepEqual(record.ticks.map((tick) => tick.name), ['chess.s0.materializeObjects', 'chess.s1.analyzeSides', 'chess.s1.scoreCandidates']);
  assert.deepEqual(record.ticks[0].invocations.map((i) => i.id), ['chess.s0.materializeObjects#0', 'chess.s0.materializeObjects#1']);
  assert.ok(invocations(record).every((i) => i.value.kind === 'omitted'));
  assert.match(invocations(record)[0].value.note, /retain no Part values/);

  const s1 = byId(record, 'chess.s1.analyzeSides');
  assert.deepEqual(s1.declared_consumes, ['px:px.chess.objects']);
  assert.deepEqual(s1.actual_consumes, ['px.chess.frame', 'px.chess.objects']);
  assert.equal(s1.hit, false, 'px.chess.objects was produced by S0 in this record');
  assert.equal(s1.calculation.implementation_sha256.length, 64);

  // A receipt with no frozenCalculations still yields one invocation, with a
  // null address rather than an invented one.
  const scored = byId(record, 'chess.s1.scoreCandidates');
  assert.equal(scored.calculation.address, null);
  assert.deepEqual(scored.writes, [{ address: 'px.chess.analysis', kind: 'refinement' }]);
});

test('Wumpus: values are present and the SVG Part is classified as svg', () => {
  const record = fromWumpusRecords(wumpusDoc.records, { pcr: 'wumpus.belief' });
  assert.deepEqual(record.ticks.map((tick) => tick.name), ['Sense', 'Believe', 'Render']);
  const sense = byId(record, 'tick-1');
  assert.equal(sense.calculation.address, 'fn.wumpus.sense');
  assert.equal(sense.calculation.identity_scope, 'registered-address-only');
  assert.deepEqual(sense.value.data, { breeze: false, stench: false, glitter: false });
  assert.deepEqual(sense.writes, [{ address: 'px.agent.percept', kind: 'new-address' }]);
  assert.deepEqual(Object.keys(sense.args), ['grid', 'at'], 'the calculation input map becomes args');

  const render = byId(record, 'tick-3');
  assert.equal(render.value.kind, 'svg');
  assert.ok(render.value.data.startsWith('<svg'));
  assert.equal(typeof render.duration_ms, 'number');
});

/* ---------------------------------------------------------------- */
/* materialize                                                       */
/* ---------------------------------------------------------------- */

test('materialize classifies text, svg, png data URLs and JSON', () => {
  assert.equal(materialize('plain').kind, 'text');
  assert.equal(materialize('<svg xmlns="http://www.w3.org/2000/svg"></svg>').kind, 'svg');
  assert.equal(materialize('  \n<svg/>').kind, 'svg');
  assert.equal(materialize('<?xml version="1.0"?><svg/>').kind, 'svg');
  assert.equal(materialize('data:image/png;base64,iVBORw0KGgo=').kind, 'png-data-url');
  assert.equal(materialize({ a: 1 }).kind, 'json');
  assert.equal(materialize(undefined).kind, 'omitted');
  assert.match(materialize(undefined).note, /did not retain/);
});

test('an array value is validated on its description, not on its numbers', () => {
  // pyto emits kind "array" for an ndarray Part: the numbers are not in the
  // record, the buffer is beside it (RECORD.md, kind `array`). A JS runtime has
  // no arrays to emit, so all this side owes the kind is to read one without
  // refusing it -- and to refuse a malformed one.
  const record = JSON.parse(JSON.stringify(pytoDoc));
  const value = {
    kind: 'array',
    data: {
      dtype: 'uint8',
      shape: [2, 4, 3],
      digest: 'a'.repeat(64),
      preview: [0, 1, 2],
      path: 'record.values/px.evo.render.01.bin'
    },
    note: '24 uint8 value(s), shape (2, 4, 3); raw bytes at record.values/px.evo.render.01.bin'
  };
  record.ticks[0].invocations[0].value = value;
  const validated = validate(record);
  assert.equal(validated.ticks[0].invocations[0].value.data.dtype, 'uint8');

  const broken = [
    [{ ...value.data, shape: [2, -1] }, /shape\[1\]/],
    [{ ...value.data, digest: 'not-a-digest' }, /digest/],
    [{ ...value.data, dtype: 7 }, /dtype/],
    [{ dtype: 'uint8', shape: [1], digest: null, preview: null }, /path/]
  ];
  for (const [data, expected] of broken) {
    const bad = JSON.parse(JSON.stringify(record));
    bad.ticks[0].invocations[0].value = { ...value, data };
    assert.throws(() => validate(bad), expected);
  }

  const noNote = JSON.parse(JSON.stringify(record));
  noNote.ticks[0].invocations[0].value = { ...value, note: null };
  assert.throws(() => validate(noNote), /must say what the array is/);
});

test('materialize honours RECORD.md size and array caps', () => {
  const long = Array.from({ length: MAX_ARRAY_ENTRIES + 55 }, (_, i) => i);
  const truncated = materialize(long);
  assert.equal(truncated.kind, 'json');
  assert.equal(truncated.data.length, MAX_ARRAY_ENTRIES);
  assert.equal(
    truncated.note,
    `1 array(s) truncated to the first ${MAX_ARRAY_ENTRIES} entries; original lengths: [${long.length}]`
  );

  const huge = 'x'.repeat(MAX_VALUE_BYTES + 1);
  const omitted = materialize(huge, { digest: 'abc123' });
  assert.equal(omitted.kind, 'omitted');
  assert.equal(omitted.data, null);
  assert.match(omitted.note, new RegExp(`${MAX_VALUE_BYTES + 1} bytes over the ${MAX_VALUE_BYTES}-byte cap; digest abc123`));

  const circular = {};
  circular.self = circular;
  assert.equal(materialize(circular).kind, 'omitted');
});

/**
 * RECORD.md caps arrays at 200 entries without qualifying the cap by depth
 * ("arrays longer than 200 entries carry the first 200 and a note with the full
 * length", RECORD.md:113 as it now stands),
 * so the two runtimes have to cut the same arrays and write the same note. The
 * expectation below is Python's own output, not a transcription of it, produced
 * once with:
 *
 *   .venv/bin/python -c 'import json
 *   from pyto.materialize import render_value
 *   cases = {"nested-1000": {"rows": list(range(1000))},
 *            "deep-300": {"a": {"b": [list(range(300))]}},
 *            "two-arrays": {"p": list(range(1000)), "q": {"r": list(range(300))}, "s": [1, 2, 3]},
 *            "short-first": {"a": list(range(300)), "z": list(range(1000))},
 *            "top-level-255": list(range(255))}
 *   print(json.dumps({k: render_value(v) for k, v in cases.items()}, sort_keys=True, separators=(",", ":")))'
 *
 * Before the fix JS truncated only a TOP-LEVEL array, so `{"rows": [0..999]}`
 * was a 200-row record in pyto and a 1000-row record with note null in the
 * browser (pyto/experiments/runs/day3/verdicts/adversarial-values.json:12).
 */
const PYTHON_TRUNCATION_EXPECTATION = JSON.parse(
  '{"deep-300":{"data":{"a":{"b":[[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199]]}},"kind":"json","note":"1 array(s) truncated to the first 200 entries; original lengths: [300]"},"nested-1000":{"data":{"rows":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199]},"kind":"json","note":"1 array(s) truncated to the first 200 entries; original lengths: [1000]"},"short-first":{"data":{"a":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199],"z":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199]},"kind":"json","note":"2 array(s) truncated to the first 200 entries; original lengths: [1000, 300]"},"top-level-255":{"data":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199],"kind":"json","note":"1 array(s) truncated to the first 200 entries; original lengths: [255]"},"two-arrays":{"data":{"p":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199],"q":{"r":[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199]},"s":[1,2,3]},"kind":"json","note":"2 array(s) truncated to the first 200 entries; original lengths: [1000, 300]"}}'
);

const TRUNCATION_INPUTS = {
  'nested-1000': { rows: Array.from({ length: 1000 }, (_, i) => i) },
  'deep-300': { a: { b: [Array.from({ length: 300 }, (_, i) => i)] } },
  'two-arrays': {
    p: Array.from({ length: 1000 }, (_, i) => i),
    q: { r: Array.from({ length: 300 }, (_, i) => i) },
    s: [1, 2, 3]
  },
  // Traversal meets 300 first; the note still has to read [1000, 300], because
  // materialize.py:238 sorts the lengths descending rather than reporting them
  // in the order it found them.
  'short-first': {
    a: Array.from({ length: 300 }, (_, i) => i),
    z: Array.from({ length: 1000 }, (_, i) => i)
  },
  'top-level-255': Array.from({ length: 255 }, (_, i) => i)
};

test('materialize truncates nested arrays exactly as the Python materializer does', () => {
  for (const [name, input] of Object.entries(TRUNCATION_INPUTS)) {
    assert.deepEqual(
      materialize(input),
      PYTHON_TRUNCATION_EXPECTATION[name],
      `JS materialize disagrees with pyto render_value on ${name}`
    );
  }
  // Named separately so a regression reads as what it is rather than as a diff
  // of two 200-entry arrays.
  assert.equal(materialize(TRUNCATION_INPUTS['nested-1000']).data.rows.length, MAX_ARRAY_ENTRIES);
  assert.equal(materialize(TRUNCATION_INPUTS['deep-300']).data.a.b[0].length, MAX_ARRAY_ENTRIES);
  assert.equal(
    materialize(TRUNCATION_INPUTS['two-arrays']).note,
    `2 array(s) truncated to the first ${MAX_ARRAY_ENTRIES} entries; original lengths: [1000, 300]`
  );
});

test('materialize still reaches omitted for a cycle hidden past the array cap', () => {
  // The serializability check runs on the whole value, before truncation, so a
  // bad entry at index 900 cannot be sliced out of sight.
  const cyclic = {};
  cyclic.self = cyclic;
  const long = Array.from({ length: 1000 }, (_, i) => i);
  long[900] = cyclic;
  assert.equal(materialize({ rows: long }).kind, 'omitted');
});

test('materialize counts UTF-8 bytes, not characters', () => {
  const emoji = '🥏'.repeat(MAX_VALUE_BYTES / 4);
  assert.equal(emoji.length, MAX_VALUE_BYTES / 2, 'half as many UTF-16 units as the cap');
  assert.equal(materialize(emoji).kind, 'text', 'exactly at the cap');
  assert.equal(materialize(emoji + '🥏').kind, 'omitted', 'one code point over');
});

/* ---------------------------------------------------------------- */
/* part index                                                        */
/* ---------------------------------------------------------------- */

test('derivePartIndex names the writer, the readers and what preexisted', () => {
  const record = fromPytoRecord(pytoDoc);
  const parts = derivePartIndex(record.ticks);
  assert.deepEqual(parts['input.ablation.rows'], { written_by: null, read_by: ['split'], preexisting: true });
  // A fn: binding counts as a read of the Part the producing invocation wrote:
  // the twelve fit/score invocations of the real experiment all consume
  // 'fn:split', and the index has to show that they consume the split Part.
  assert.deepEqual(parts['scratch.ablation.split'], {
    written_by: 'split',
    read_by: [
      'fit.all', 'fit.drop_g0', 'fit.drop_g1', 'fit.drop_g2', 'fit.drop_g3', 'fit.drop_g4',
      'score.all', 'score.drop_g0', 'score.drop_g1', 'score.drop_g2', 'score.drop_g3', 'score.drop_g4'
    ],
    preexisting: false
  });
  assert.deepEqual(parts['scratch.ablation.model.all'], { written_by: 'fit.all', read_by: ['score.all'], preexisting: false });
  assert.deepEqual(parts['scratch.ablation.comparison'], { written_by: 'compare', read_by: [], preexisting: false });
  // scratch.ablation.variants is written and never read: the index says so
  // instead of omitting the address.
  assert.deepEqual(parts['scratch.ablation.variants'], { written_by: 'select', read_by: [], preexisting: false });
  assert.deepEqual(parts, record.parts, 'the Python index and the JavaScript derivation agree');
});

test('bareAddress strips only the testimony marker', () => {
  assert.equal(bareAddress('px:a.b'), 'a.b');
  assert.equal(bareAddress('fn:split'), 'split');
  assert.equal(bareAddress('a.b'), 'a.b');
  assert.equal(bareAddress(undefined), '');
});

/* ---------------------------------------------------------------- */
/* validate: every violation names its path                          */
/* ---------------------------------------------------------------- */

/** node's assert.throws returns undefined, so capture the error directly. */
const caught = (fn) => {
  try {
    fn();
  } catch (error) {
    return error;
  }
  throw new assert.AssertionError({ message: 'expected a RecordSchemaError, none was thrown' });
};

const mutateIn = (document, path, value) => {
  const clone = structuredClone(document);
  const keys = path.split('.');
  let node = clone;
  for (const key of keys.slice(0, -1)) node = node[/^\d+$/.test(key) ? Number(key) : key];
  const last = keys.at(-1);
  if (value === undefined) delete node[last];
  else node[/^\d+$/.test(last) ? Number(last) : last] = value;
  return clone;
};

const mutate = (path, value) => mutateIn(pytoDoc, path, value);

const cases = [
  ['schema', 'nope', 'schema'],
  ['pcr', 42, 'pcr'],
  ['source.runtime', 'matlab', 'source.runtime'],
  ['source.commit', 7, 'source.commit'],
  ['ticks.0.index', 3, 'ticks[0].index'],
  ['ticks.0.name', null, 'ticks[0].name'],
  ['ticks.0.invocations.0.id', '', 'ticks[0].invocations[0].id'],
  ['ticks.0.invocations.0.calculation.identity_scope', undefined, 'ticks[0].invocations[0].calculation.identity_scope'],
  ['ticks.0.invocations.0.inputs.groups', 'input.ablation.groups', 'ticks[0].invocations[0].inputs.groups'],
  ['ticks.0.invocations.0.declared_consumes.0', 'input.ablation.groups', 'ticks[0].invocations[0].declared_consumes[0]'],
  ['ticks.0.invocations.0.actual_consumes', 'input.ablation.groups', 'ticks[0].invocations[0].actual_consumes'],
  ['ticks.0.invocations.0.writes.0.kind', 'clobber', 'ticks[0].invocations[0].writes[0].kind'],
  ['ticks.0.invocations.0.writes.0.kind', undefined, 'ticks[0].invocations[0].writes[0].kind'],
  ['ticks.0.invocations.0.duration_ms', 'fast', 'ticks[0].invocations[0].duration_ms'],
  ['ticks.0.invocations.0.hit', 'yes', 'ticks[0].invocations[0].hit'],
  ['ticks.0.invocations.0.value.kind', 'binary', 'ticks[0].invocations[0].value.kind'],
  ['counters.invocations', 99, 'counters.invocations'],
  ['counters.hits', 1, 'counters.hits'],
  ['counters.computed', 1, 'counters.computed'],
  ['counters.wall_ms', 'quick', 'counters.wall_ms']
];

for (const [path, value, expectedPath] of cases) {
  test(`validate rejects ${path} and names ${expectedPath}`, () => {
    const error = caught(() => validate(mutate(path, value)));
    assert.ok(error instanceof RecordSchemaError, `expected RecordSchemaError, got ${error}`);
    assert.equal(error.path, expectedPath, error.message);
    assert.ok(error.message.startsWith(`${SCHEMA} ${expectedPath}: `), error.message);
  });
}

// The real run's values are all `json`, so the kind-specific rules of RECORD.md
// are exercised against the synthetic record that carries the other four kinds:
// ticks[3] is the svg/png Materialize Tick, ticks[4] the omitted Retain Tick.
const kindCases = [
  ['ticks.3.invocations.0.value.data', 12, 'ticks[3].invocations[0].value.data'],
  ['ticks.3.invocations.1.value.data', null, 'ticks[3].invocations[1].value.data'],
  ['ticks.4.invocations.0.value.note', null, 'ticks[4].invocations[0].value.note'],
  ['ticks.4.invocations.0.value.data', 'something', 'ticks[4].invocations[0].value.data']
];

for (const [path, value, expectedPath] of kindCases) {
  test(`validate rejects ${path} in the value-kinds record and names ${expectedPath}`, () => {
    const error = caught(() => validate(mutateIn(valueKindsDoc, path, value)));
    assert.ok(error instanceof RecordSchemaError, `expected RecordSchemaError, got ${error}`);
    assert.equal(error.path, expectedPath, error.message);
  });
}

test('the synthetic record carries the four value kinds the real run never produces', () => {
  const kinds = invocations(fromPytoRecord(valueKindsDoc)).map((invocation) => invocation.value.kind);
  assert.deepEqual([...new Set(kinds)].sort(), ['json', 'omitted', 'png-data-url', 'svg', 'text']);
  const real = invocations(fromPytoRecord(pytoDoc)).map((invocation) => invocation.value.kind);
  assert.deepEqual([...new Set(real)], ['json'], 'grouped-ablation run-1 materializes JSON only');
});

// RECORD.md:83-86 makes declared_consumes exactly the `px:` bindings of inputs.
// Each of its two halves is violated on its own here, so each test names one
// branch of viewer/adapters.js:162-167 and no other check can stand in for it.
test('validate rejects a declared_consumes entry spelled fn:, naming the path', () => {
  const clone = structuredClone(pytoDoc);
  // `fn:split` IS an inputs value on fit.all, so only the `px:` rule can reject it.
  clone.ticks[1].invocations[0].declared_consumes = ['fn:split'];
  const error = caught(() => validate(clone));
  assert.ok(error instanceof RecordSchemaError, `expected RecordSchemaError, got ${error}`);
  assert.equal(error.path, 'ticks[1].invocations[0].declared_consumes[0]', error.message);
  assert.match(error.message, /declared_consumes carries Part bindings only/);
});

test('validate rejects a declared_consumes entry that inputs does not carry, naming the path', () => {
  const clone = structuredClone(pytoDoc);
  // Correctly spelled `px:`, so only the subset-of-inputs rule can reject it.
  clone.ticks[0].invocations[1].declared_consumes = ['px:input.ablation.unbound'];
  const error = caught(() => validate(clone));
  assert.ok(error instanceof RecordSchemaError, `expected RecordSchemaError, got ${error}`);
  assert.equal(error.path, 'ticks[0].invocations[1].declared_consumes[0]', error.message);
  assert.match(error.message, /subset of inputs\.values\(\)/);
});

test('validate rejects a duplicate invocation id, because ids anchor annotations', () => {
  const clone = structuredClone(pytoDoc);
  clone.ticks[1].invocations[0].id = 'split';
  const error = caught(() => validate(clone));
  assert.ok(error instanceof RecordSchemaError, `expected RecordSchemaError, got ${error}`);
  assert.equal(error.path, 'ticks[1].invocations[0].id');
  assert.match(error.message, /duplicate invocation id "split"/);
});

test('validate rejects a malformed parts entry with the address in the path', () => {
  const clone = structuredClone(pytoDoc);
  clone.parts['scratch.ablation.split'].read_by = 'split';
  const error = caught(() => validate(clone));
  assert.ok(error instanceof RecordSchemaError, `expected RecordSchemaError, got ${error}`);
  assert.equal(error.path, 'parts["scratch.ablation.split"].read_by');
});

test('validate rejects a non-object document', () => {
  assert.throws(() => validate(null), /document: expected an object/);
  assert.throws(() => validate([]), /document: expected an object/);
});

/* ---------------------------------------------------------------- */
/* the Python materializer's own output                              */
/* ---------------------------------------------------------------- */

test('the record pyto.materialize wrote for grouped-ablation run-1 validates unchanged', () => {
  const record = fromPytoRecord(JSON.parse(readFileSync(REAL_RECORD, 'utf8')));
  assert.equal(record.source.runtime, 'pyto');
  assert.equal(record.counters.invocations, 15);
  // The same hit rule the viewer applies to every runtime: exactly the two
  // invocations that read a Part seeded before the run.
  const hits = invocations(record).filter((invocation) => invocation.hit).map((invocation) => invocation.id);
  assert.deepEqual(hits, ['select', 'split']);
  assert.equal(record.counters.hits, 2);
  assert.deepEqual(derivePartIndex(record.ticks), record.parts, 'the writer/reader index agrees with the invocations');
});

/* ---------------------------------------------------------------- */
/* hostile record data                                               */
/* ---------------------------------------------------------------- */

test('a Part address named __proto__ or constructor is an ordinary row, not a prototype write', () => {
  // Every non-pyto adapter reaches derivePartIndex, and a Part address is data
  // the record chose. On a `{}` index these names resolve to Object.prototype
  // and Object, so the index answers for addresses no run wrote and the page's
  // own prototype chain is what a record edits.
  const record = fromDiscStudioReceipt({
    PrincipleComponentRender: 'hostile',
    Ticks: [{
      name: 'T',
      Calculations: [
        { call: 'fn.a', with: { raw: '__proto__' }, into: 'constructor' },
        { call: 'fn.b', with: { seed: 'constructor' }, into: 'out.clean' }
      ]
    }]
  }, null);

  assert.equal({}.preexisting, undefined, 'Object.prototype was not written through');
  assert.equal({}.written_by, undefined);
  assert.deepEqual(
    Object.keys(record.parts).sort(),
    ['__proto__', 'constructor', 'out.clean'],
    'each hostile address is its own row'
  );
  const row = (address) => Object.getOwnPropertyDescriptor(record.parts, address).value;
  assert.equal(row('__proto__').preexisting, true);
  assert.deepEqual(row('__proto__').read_by, ['constructor']);
  assert.equal(row('constructor').written_by, 'constructor');
  assert.equal(row('constructor').preexisting, false, 'written before it was read in this run');
  // The index is handed back as an own-property map, the same shape a consumer
  // gets from JSON.parse, so the hostile name survives the wire form as a row.
  const round = JSON.parse(JSON.stringify(record)).parts;
  assert.deepEqual(Object.keys(round).sort(), ['__proto__', 'constructor', 'out.clean']);
  assert.deepEqual(derivePartIndex(record.ticks), round, 'the index round-trips through JSON unchanged');

  // The binding *name* is record data too: a `with` key of `__proto__` must land
  // in `inputs` rather than silently setting the prototype of the inputs map.
  // Built through JSON.parse, which is how such a map actually arrives and the
  // only way to spell it: a `{ __proto__: ... }` literal sets the prototype.
  const spelled = fromDiscStudioReceipt(JSON.parse(
    '{"PrincipleComponentRender":"hostile.names","Ticks":[{"name":"T","Calculations":[{"call":"fn.a","with":{"__proto__":"input.rows"},"into":"out"}]}]}'
  ), null);
  assert.deepEqual(Object.entries(spelled.ticks[0].invocations[0].inputs), [['__proto__', 'px:input.rows']]);
  assert.equal({}.preexisting, undefined, 'still no prototype write after the second record');
});

/* ---------------------------------------------------------------- */
/* multi-produce: RECORD.md, `into` may be an array                   */
/* ---------------------------------------------------------------- */

/**
 * One invocation publishing two Parts from one pass, and a second reading one of
 * them by name. Hand-written from RECORD.md, the same document
 * `viewer/test/test_record_schema.py` builds for the Python reader, so the two
 * references are shown answering the same about the same bytes.
 */
const multiProduceDoc = () => ({
  schema: SCHEMA,
  pcr: 'multi',
  source: { runtime: 'pyto', version: '0.1.0', commit: null },
  ticks: [
    {
      index: 0,
      name: 'Prepare',
      invocations: [{
        id: 'stats',
        calculation: { address: 'fn.multi.stats', implementation_sha256: null, identity_scope: 'runtime-function-body' },
        inputs: { rows: 'px:in.rows' },
        args: {},
        into: ['out.mean', 'out.count'],
        declared_consumes: ['px:in.rows'],
        actual_consumes: ['in.rows'],
        actual_produces: ['out.mean', 'out.count'],
        writes: [{ address: 'out.mean', kind: 'new-address' }, { address: 'out.count', kind: 'new-address' }],
        duration_ms: 1.5,
        result_sha256: null,
        hit: true,
        value: { kind: 'json', data: { 'out.mean': 2.5, 'out.count': 4 }, note: null }
      }]
    },
    {
      index: 1,
      name: 'Report',
      invocations: [{
        id: 'report',
        calculation: { address: 'fn.multi.take', implementation_sha256: null, identity_scope: 'runtime-function-body' },
        inputs: { value: 'fn:stats#out.count' },
        args: {},
        into: 'out.reported',
        declared_consumes: [],
        actual_consumes: [],
        actual_produces: ['out.reported'],
        writes: [{ address: 'out.reported', kind: 'new-address' }],
        duration_ms: 0.5,
        result_sha256: null,
        hit: false,
        value: { kind: 'json', data: 4, note: null }
      }]
    }
  ],
  parts: {
    'in.rows': { written_by: null, read_by: ['stats'], preexisting: true },
    'out.mean': { written_by: 'stats', read_by: [], preexisting: false },
    'out.count': { written_by: 'stats', read_by: ['report'], preexisting: false },
    'out.reported': { written_by: 'report', read_by: [], preexisting: false }
  },
  counters: { invocations: 2, hits: 1, computed: 1, wall_ms: 2.0 }
});

test('validate accepts an array `into` and the produce-qualified binding spelling', () => {
  const record = multiProduceDoc();
  assert.equal(validate(record), record);
  assert.deepEqual(produceAddresses(['a', 'b']), ['a', 'b']);
  assert.deepEqual(produceAddresses('a'), ['a']);
  assert.deepEqual(produceAddresses(null), []);
});

test('derivePartIndex credits the produce an fn: binding names, and only that one', () => {
  // The edge {?} ResultReadsAreReads turns on: a result read is a read of the
  // Part the producer published, and when a producer published several, of the
  // one the binding names -- not of all of them.
  const record = multiProduceDoc();
  const index = derivePartIndex(record.ticks);
  assert.deepEqual(index, record.parts);
  assert.deepEqual(index['out.count'].read_by, ['report']);
  assert.deepEqual(index['out.mean'].read_by, []);
});

test('parseBinding reads both spellings and prefers a known invocation id', () => {
  const producedBy = new Map([['stats', ['out.mean', 'out.count']], ['odd#name', ['out.odd']]]);
  assert.deepEqual(parseBinding('px:in.rows', producedBy), ['in.rows']);
  assert.deepEqual(parseBinding('fn:stats#out.count', producedBy), ['out.count']);
  // a bare reference to a producer of several reads all of them; pyto's kernel
  // refuses to write one, and a record that carries one is read, not repaired.
  assert.deepEqual(parseBinding('fn:stats', producedBy), ['out.mean', 'out.count']);
  // a known id wins over the `#` split, so an id carrying a `#` still resolves
  assert.deepEqual(parseBinding('fn:odd#name', producedBy), ['out.odd']);
  assert.deepEqual(parseBinding('fn:nobody#out.x', producedBy), []);
});

test('validate refuses the malformed shapes of the multi-produce clauses', () => {
  const cases = [
    [(r) => { r.ticks[0].invocations[0].into = []; }, 'ticks[0].invocations[0].into'],
    [(r) => { r.ticks[0].invocations[0].into = ['out.mean', 'out.mean']; }, 'ticks[0].invocations[0].into[1]'],
    [(r) => { r.ticks[0].invocations[0].into = ['out.mean', 7]; }, 'ticks[0].invocations[0].into[1]'],
    [(r) => { r.ticks[0].invocations[0].into = { 0: 'out.mean' }; }, 'ticks[0].invocations[0].into'],
    [(r) => { r.ticks[1].invocations[0].inputs.value = 'fn:stats#'; }, 'ticks[1].invocations[0].inputs.value'],
    [(r) => { r.ticks[1].invocations[0].inputs.value = 'fn:#out.count'; }, 'ticks[1].invocations[0].inputs.value']
  ];
  for (const [mutate, path] of cases) {
    const record = multiProduceDoc();
    mutate(record);
    const error = caught(() => validate(record));
    assert.ok(error instanceof RecordSchemaError, `expected RecordSchemaError at ${path}, got ${error}`);
    assert.equal(error.path, path);
  }
});

test('validate rejects a png-data-url whose data is not a PNG data URL', () => {
  // RECORD.md:109-110 states the shape, and tick-viewer.js puts this string into
  // an <img src>: unchecked, a record chooses an outbound request from a page
  // whose premise is that it makes none.
  for (const data of ['https://evil.example/beacon.gif?record=opened', 'javascript:alert(1)//', 'data:image/svg+xml,<svg/>', '']) {
    const clone = structuredClone(pytoDoc);
    clone.ticks[0].invocations[0].value = { kind: 'png-data-url', data, note: null };
    const error = caught(() => validate(clone));
    assert.ok(error instanceof RecordSchemaError, `expected RecordSchemaError for ${JSON.stringify(data)}, got ${error}`);
    assert.equal(error.path, 'ticks[0].invocations[0].value.data');
    assert.match(error.message, /data:image\/png;base64,/);
  }
  const ok = structuredClone(pytoDoc);
  ok.ticks[0].invocations[0].value = { kind: 'png-data-url', data: `${PNG_DATA_URL_PREFIX}iVBORw0KGgo=`, note: null };
  assert.equal(validate(ok), ok);
});

test('materialize never classifies a string as png-data-url that validate would refuse', () => {
  // The classification is on the raw string, not a trimmed head, so what
  // materialize emits is always readable back by validate.
  const leading = materialize(`   ${PNG_DATA_URL_PREFIX}iVBORw0KGgo=`);
  assert.equal(leading.kind, 'text', 'a leading-whitespace data URL is text, not a png-data-url');
  for (const raw of ['plain', `   ${PNG_DATA_URL_PREFIX}iVBORw0KGgo=`, `${PNG_DATA_URL_PREFIX}iVBORw0KGgo=`]) {
    const block = materialize(raw);
    const clone = structuredClone(pytoDoc);
    clone.ticks[0].invocations[0].value = block;
    assert.equal(validate(clone), clone, `materialize(${JSON.stringify(raw)}) is not a valid value block`);
  }
});

/* ------------------------------------------------------------------ */
/* placement and budget (RECORD.md, "Placement and budget"; task 39)   */
/* ------------------------------------------------------------------ */

/** The committed pyto record with a schedule bolted on, by hand, from RECORD.md. */
function scheduled(record) {
  const clone = JSON.parse(JSON.stringify(record));
  clone.parallel = true;
  clone.budget = { limit_ms: 250, stopped_after_tick: clone.ticks[clone.ticks.length - 1].name, completed: false };
  clone.ticks.forEach((tick, index) => {
    tick.latency_ms = 1.5 + index;
    tick.invocations.forEach((invocation, position) => {
      invocation.placement = { worker: position % 2, started_ms: position * 0.25 };
    });
  });
  return clone;
}

/** Every adapter's output, the same six records the validate test builds. */
const everyAdapterRecord = () => [
  fromPytoRecord(pytoDoc),
  fromPytoRecord(valueKindsDoc),
  fromDiscStudioReceipt(dsDoc.first.pql, dsDoc.first.receipt, { version: 'transcribed-82f8fc9' }),
  fromDiscStudioReceipt(dsDoc.second.pql, dsDoc.second.receipt),
  fromChessLabReceipts(chessDoc.receipts, { pcr: 'chesslab.debugger' }),
  fromWumpusRecords(wumpusDoc.records, { pcr: 'wumpus.belief' })
];

test('every committed fixture reads as a serial, unbudgeted run', () => {
  for (const doc of everyAdapterRecord()) {
    assert.deepEqual(runSchedule(doc), {
      parallel: false,
      budget: { limit_ms: null, stopped_after_tick: null, completed: true }
    });
    for (const invocation of invocations(doc)) assert.equal(invocationPlacement(invocation), null);
  }
});

test('tickLatencyMsFromRecord falls back to the sum of the Tick durations, and to null', () => {
  for (const tick of pytoDoc.ticks) {
    const sum = tick.invocations.reduce((total, invocation) => total + invocation.duration_ms, 0);
    assert.equal(tickLatencyMsFromRecord(tick), Math.round(sum * 1000) / 1000);
  }
  // A null duration makes the Tick's latency unknown, never a partial sum.
  const unknown = JSON.parse(JSON.stringify(pytoDoc.ticks[0]));
  unknown.invocations[0].duration_ms = null;
  assert.equal(tickLatencyMsFromRecord(unknown), null);
  assert.equal(tickLatencyMsFromRecord({ name: 'empty', invocations: [] }), null);
});

test('a scheduled record validates and reads back through both accessors', () => {
  const doc = scheduled(pytoDoc);
  assert.equal(validate(doc), doc);
  assert.deepEqual(runSchedule(doc), {
    parallel: true,
    budget: { limit_ms: 250, stopped_after_tick: doc.ticks[doc.ticks.length - 1].name, completed: false }
  });
  assert.equal(tickLatencyMsFromRecord(doc.ticks[0]), 1.5);
  assert.deepEqual(invocationPlacement(doc.ticks[0].invocations[0]), { worker: 0, started_ms: 0 });
  // An explicit latency wins over the sum: it is measured, the sum is derived.
  assert.notEqual(tickLatencyMsFromRecord(doc.ticks[0]), tickLatencyMsFromRecord(pytoDoc.ticks[0]));
});

test('a null placement is a serial invocation, not a violation', () => {
  const doc = scheduled(pytoDoc);
  doc.ticks[0].invocations[0].placement = null;
  assert.equal(validate(doc), doc);
  assert.equal(invocationPlacement(doc.ticks[0].invocations[0]), null);
});

test('validate rejects a placement that is not one, naming the path', () => {
  const cases = [
    [{ worker: -1, started_ms: 0 }, 'ticks[0].invocations[0].placement.worker'],
    [{ worker: 1.5, started_ms: 0 }, 'ticks[0].invocations[0].placement.worker'],
    [{ worker: 0, started_ms: 'soon' }, 'ticks[0].invocations[0].placement.started_ms'],
    [{ worker: 0, started_ms: 0, thread: 'main' }, 'ticks[0].invocations[0].placement']
  ];
  for (const [placement, path] of cases) {
    const doc = scheduled(pytoDoc);
    doc.ticks[0].invocations[0].placement = placement;
    assert.throws(() => validate(doc), (error) => error instanceof RecordSchemaError && error.path === path);
  }
});

test('validate rejects a budget that contradicts itself, naming the path', () => {
  const cases = [
    [{ limit_ms: 250, stopped_after_tick: 'Prepare', completed: true }, 'budget.stopped_after_tick'],
    [{ limit_ms: 250, stopped_after_tick: 'Nowhere', completed: false }, 'budget.stopped_after_tick'],
    [{ limit_ms: 'soon', stopped_after_tick: null, completed: true }, 'budget.limit_ms'],
    [{ limit_ms: 250, completed: false }, 'budget'],
    [{ limit_ms: 250, stopped_after_tick: null, completed: false, spent_ms: 300 }, 'budget']
  ];
  for (const [budget, path] of cases) {
    const doc = JSON.parse(JSON.stringify(pytoDoc));
    doc.budget = budget;
    assert.throws(() => validate(doc), (error) => error instanceof RecordSchemaError && error.path === path);
  }
  const notABoolean = JSON.parse(JSON.stringify(pytoDoc));
  notABoolean.parallel = 'yes';
  assert.throws(() => validate(notABoolean), (error) => error instanceof RecordSchemaError && error.path === 'parallel');
  const notANumber = JSON.parse(JSON.stringify(pytoDoc));
  notANumber.ticks[0].latency_ms = 'fast';
  assert.throws(() => validate(notANumber), (error) => error instanceof RecordSchemaError && error.path === 'ticks[0].latency_ms');
});

test('the adapters for the other runtimes still write no schedule at all', () => {
  // Absent means serial and unbudgeted: an adapter that invented `parallel: false`
  // would change the bytes of every record those three runtimes ever wrote.
  for (const doc of everyAdapterRecord().slice(2)) {
    assert.equal('parallel' in doc, false);
    assert.equal('budget' in doc, false);
    for (const tick of doc.ticks) assert.equal('latency_ms' in tick, false);
    for (const invocation of invocations(doc)) assert.equal('placement' in invocation, false);
  }
});

/* ------------------------------------------------------------------ */
/* DiscStudio: an array `into`, and the schedule the run reported      */
/* ------------------------------------------------------------------ */

// Kills: `actual_produces: [into]` for an array `into` (adapters.js:648) makes
// actual_produces a list of one list and derivePartIndex indexes no Part;
// writing the schedule fields when `scheduled` is null (adapters.js:536-544)
// puts `parallel`/`budget` on every serial record and test (e) in
// tests/core.test.js -- byte-identical to the pre-change fixture -- fails.

test('an array into publishes several Parts from one invocation, each a write and each indexed', () => {
  const record = fromDiscStudioReceipt({
    PrincipleComponentRender: 'several-into',
    Ticks: [
      { name: 'Split', Calculations: [{ call: 'fn.split', with: { raw: 'px.raw' }, into: ['px.left', 'px.right'] }] },
      { name: 'Join', Calculations: [{ call: 'fn.join', with: { a: 'px.left', b: 'px.right' }, into: 'px.joined' }] }
    ]
  }, null);

  const split = record.ticks[0].invocations[0];
  assert.deepEqual(split.into, ['px.left', 'px.right']);
  assert.deepEqual(split.actual_produces, ['px.left', 'px.right']);
  assert.deepEqual(split.writes, [{ address: 'px.left', kind: 'new-address' }, { address: 'px.right', kind: 'new-address' }]);
  assert.equal(split.id, 'px.left', 'the invocation id is the first address it declares');
  assert.equal(record.parts['px.left'].written_by, 'px.left');
  assert.equal(record.parts['px.right'].written_by, 'px.left');
  assert.deepEqual(record.parts['px.right'].read_by, ['px.joined']);
  assert.equal(record.parts['px.raw'].preexisting, true);
  assert.equal(validate(record), record);
});

test('the four schedule fields come from the run and only when the run reported one', () => {
  const document = {
    PrincipleComponentRender: 'scheduled',
    Ticks: [
      { name: 'Seed', Calculations: [{ call: 'fn.seed', into: 'px.seed' }] },
      { name: 'Fan', Calculations: [
        { call: 'fn.leg', with: { seed: 'px.seed' }, into: 'px.leg.0' },
        { call: 'fn.leg', with: { seed: 'px.seed' }, into: 'px.leg.1' }
      ] }
    ]
  };
  const schedule = {
    parallel: true,
    budget: { limit_ms: 500, stopped_after_tick: 'Fan', completed: false },
    ticks: [
      { name: 'Seed', latency_ms: 1.5, placements: [{ worker: 0, started_ms: 0 }] },
      { name: 'Fan', latency_ms: 4.25, placements: [{ worker: 0, started_ms: 0.1 }, { worker: 1, started_ms: 0.2 }] }
    ]
  };
  const scheduled = fromDiscStudioReceipt(document, { trace: [], schedule });
  assert.equal(scheduled.parallel, true);
  assert.deepEqual(scheduled.budget, { limit_ms: 500, stopped_after_tick: 'Fan', completed: false });
  assert.deepEqual(scheduled.ticks.map((tick) => tick.latency_ms), [1.5, 4.25]);
  assert.deepEqual(scheduled.ticks[1].invocations.map((invocation) => invocation.placement), [{ worker: 0, started_ms: 0.1 }, { worker: 1, started_ms: 0.2 }]);

  // Absent means serial and unbudgeted: the same run without a schedule carries
  // none of the four, and the reader still answers one question of both.
  const plain = fromDiscStudioReceipt(document, { trace: [] });
  assert.equal('parallel' in plain, false);
  assert.equal('budget' in plain, false);
  assert.equal('latency_ms' in plain.ticks[0], false);
  assert.equal('placement' in plain.ticks[0].invocations[0], false);
  assert.equal(validate(plain), plain);
});
