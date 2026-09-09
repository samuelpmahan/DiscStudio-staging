import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createSeed } from '../src/seed.js';
import { shelfSheet } from '../src/formats/shelf-sheet.js';
import { pxFn, readPql, invokePql } from '../src/core/exec.js';
import { createStudioRuntime } from '../src/runtime.js';

const fixture = JSON.parse(readFileSync(new URL('./fixtures/shelf-sheet.json', import.meta.url)));

test('shelf sheet is deterministic and matches the committed byte fixture', () => {
  const first = shelfSheet(fixture.input), second = shelfSheet(fixture.input);
  assert.equal(first.svg, second.svg);
  assert.equal(first.svg, fixture.expectedSvg);
  assert.equal(first.discCount, 3);
  assert.match(first.svg, /96/);
  assert.match(first.svg, /Buzzz|Luna|Zone/);
});

test('shelf sheet is registered by the production runtime and leaves a PQL record', () => {
  const world = createSeed(), runtime = createStudioRuntime(world), input = fixture.input;
  assert.doesNotThrow(() => runtime.pxc.call(pxFn('fn.disc.format.shelfSheet'), input), 'Luna A must register the Calculation in runtime.js');
  for (const [name, value] of Object.entries({ bag: input.bag, discs: input.discs, molds: input.molds, manufacturers: input.manufacturers })) runtime.pxc.set(`px.input.${name}`, value);
  const composition = readPql(JSON.stringify({ PrincipleComponentRender: 'disc-shelf-sheet', Ticks: [{ name: 'ShelfSheet', Calculations: [{ call: 'fn.disc.format.shelfSheet', with: { bag: 'px.input.bag', discs: 'px.input.discs', molds: 'px.input.molds', manufacturers: 'px.input.manufacturers' }, into: 'px.format.shelfSheet' }] }] }), JSON.parse);
  const run = invokePql(composition, { pxc: runtime.pxc });
  assert.equal(runtime.pxc.get('px.format.shelfSheet').svg, fixture.expectedSvg);
  assert.equal(runtime.pxc.get('px.pql.disc-shelf-sheet').PrincipleComponentRender, 'disc-shelf-sheet');
  assert.equal(run.Ticks[0].Calculations[0].actualCall, 'fn.disc.format.shelfSheet');
});

test('seed bag fields can be passed directly from shared domain Parts', () => {
  const world = createSeed(), bag = world.objects.Bag['luna-bag'];
  const result = shelfSheet({ bag, discs: world.objects.Disc, molds: world.objects.Mold, manufacturers: world.objects.Manufacturer });
  assert.equal(result.bagId, bag.id);
  assert.ok(result.svg.includes('3 PHYSICAL DISCS'));
});

test('shelf sheet preserves a safe original disc photo in the tile', () => {
  const input = structuredClone(fixture.input);
  input.discs['luna-mint'].photo = 'data:image/png;base64,AA==';
  const result = shelfSheet(input);
  assert.match(result.svg, /href="data:image\/png;base64,AA=="/);
  assert.doesNotMatch(result.svg, /SAMPLE · NOT YOUR PHOTO/);
});
