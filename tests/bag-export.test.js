import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { bagExport } from '../src/formats/bag-export.js';
import { createSeed } from '../src/seed.js';
import { createStudioRuntime } from '../src/runtime.js';
import { pxFn, readPql, invokePql } from '../src/core/exec.js';

const fixture = JSON.parse(readFileSync(new URL('./fixtures/bag-export.json', import.meta.url)));

test('bag export is deterministic and preserves Bag order, identity and optional values', () => {
  const first = bagExport(fixture.input), second = bagExport(structuredClone(fixture.input));
  assert.deepEqual(first, second);
  assert.equal(first.kind, 'BagExport');
  assert.equal(first.format, 'disc.format.bagExport');
  assert.equal(first.bagId, 'bag-z');
  assert.equal(first.rowCount, 2);
  for (const name of ['json', 'csv']) assert.equal(createHash('sha256').update(first[name]).digest('hex'), fixture.expectedSha256[name]);
  const payload = JSON.parse(first.json);
  assert.deepEqual(payload.rows.map(row => row['disc.id']), ['disc-b', 'disc-a']);
  assert.equal(payload.rows[0]['disc.photo'], null, 'unsafe photos are not exported');
  assert.equal(payload.rows[1]['disc.photo'], 'data:image/png;base64,AA==');
  assert.equal(payload.rows[0]['mold.flight.glide'], null);
  assert.equal(payload.rows[0]['disc.newFlag'], true);
  assert.equal(payload.rows[1]['disc.custom.edition'], 'First');
  assert.equal(payload.rows[1]['disc.custom.odd%20key%2Ewith%2Edot.%CE%A9'], 'yes');
  assert.equal(payload.rows[1]['disc.custom.array'], '["x",2]');
});

test('CSV has sorted dotted columns, explicit quoting and blank optional cells', () => {
  const result = bagExport(fixture.input), lines = result.csv.split('\n');
  assert.equal(lines.at(-1), '');
  const header = lines[0];
  assert.ok(header.indexOf('"bag.discIds"') < header.indexOf('"mold.name"'));
  assert.match(result.csv, /"Zed, ""daily"""/);
  assert.match(result.csv, /"Star, ""special"""/);
  assert.match(result.csv, /"line 1\nline 2"/);
  assert.match(result.csv, /,"",/); // null/undefined optional values are empty cells
});

test('missing physical references fail loudly instead of being silently omitted', () => {
  const input = structuredClone(fixture.input);
  input.bag.discIds = ['missing'];
  assert.throws(() => bagExport(input), /missing physical disc/);
});

test('bag export does not infer winner or comparison state', () => {
  const input = structuredClone(fixture.input);
  input.battle = { winners: ['disc-a'], scores: { 'disc-a': 99 } };
  const output = JSON.parse(bagExport(input).json);
  assert.equal(Object.keys(output.rows[0]).some(key => key.includes('winner')), false);
  assert.equal(Object.keys(output.rows[0]).some(key => key.includes('score')), false);
});

test('production runtime exposes bag export as a PQL Calculation and record', () => {
  const world = createSeed(), runtime = createStudioRuntime(world), bag = world.objects.Bag['luna-bag'];
  const input = { bag, discs: world.objects.Disc, molds: world.objects.Mold, manufacturers: world.objects.Manufacturer };
  // Parent integration registers this address in runtime.js; this assertion guards
  // the public production path rather than only testing the helper directly.
  assert.doesNotThrow(() => runtime.pxc.call(pxFn('fn.disc.format.bagExport'), input));
  for (const [name, value] of Object.entries(input)) runtime.pxc.set(`px.input.${name}`, value);
  const composition = readPql(JSON.stringify({ PrincipleComponentRender: 'disc-bag-export', Ticks: [{ name: 'BagExport', Calculations: [{ call: 'fn.disc.format.bagExport', with: { bag: 'px.input.bag', discs: 'px.input.discs', molds: 'px.input.molds', manufacturers: 'px.input.manufacturers' }, into: 'px.format.bagExport' }] }] }), JSON.parse);
  const run = invokePql(composition, { pxc: runtime.pxc });
  assert.equal(run.Ticks[0].Calculations[0].actualCall, 'fn.disc.format.bagExport');
  assert.equal(runtime.pxc.get('px.pql.disc-bag-export').PrincipleComponentRender, 'disc-bag-export');
  assert.equal(runtime.pxc.get('px.format.bagExport').json, bagExport(input).json);
  assert.equal(runtime.pxc.get('px.format.bagExport').csv, bagExport(input).csv);
});
