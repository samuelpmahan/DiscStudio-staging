/** The map and the findings: Parts, in the store, with their `for`. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { STORE } from '../src/lab/lab.js';
import { buildMap } from '../src/lab/map.js';

test('the map names only Parts the run wrote, and every stub says why', () => {
  const lab = buildMap();
  const map = lab.get('px.exp.lab.map');
  assert.ok(map.for);
  for (const address of map.built) assert.ok(lab.has(address), address);
  assert.ok(map.built.includes('px.exp.lab.course.canonicalpixels'));
  assert.ok(map.built.includes('px.exp.lab.badges.objects'));
  assert.ok(map.built.some(address => address.startsWith('px.exp.lab.path.')));
  for (const stub of map.stubbed) assert.ok(stub.why.length > 20, stub.address);
  for (const next of map.next) assert.ok(next.for.length > 10, next.what);
});

test('every finding is lowercase, kinded and carries its for', () => {
  const lab = buildMap();
  const findings = lab.addresses().filter(address => address.startsWith('proposal.lab.'));
  assert.ok(findings.length >= 7);
  for (const address of findings) {
    assert.equal(address, address.toLowerCase());
    const finding = lab.get(address);
    assert.ok(['strength', 'friction', 'finding'].includes(finding.kind), address);
    assert.ok(finding.for && finding.text, address);
  }
});

test('the store is written where a PQL reader can find it', () => {
  buildMap();
  const store = JSON.parse(readFileSync(join(STORE, 'lab.json'), 'utf8'));
  assert.ok(store.parts['px.exp.lab.map']);
  assert.ok(store.parts['proposal.lab.pql.directresult']);
  for (const name of ['S0', 'S1']) assert.ok(existsSync(join(STORE, 'records', `${name}.json`)), name);
  // A raster Part is stored by its digest, not by a million samples.
  assert.equal(store.parts['px.exp.lab.course.canonicalpixels'].rgba.kind, 'numbers');
});
