/**
 * The LAB Stages on the studio runtime: the same modules node runs in
 * tests/lab-s*.test.js, registered as `fn.lab.*` on the studio's own board and
 * run as one composition per Stage, each leaving `px.pql.lab-*`, a receipt and a
 * run record the Inspect page and the Tick viewer already draw.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createStudioRuntime } from '../src/runtime.js';
import { createSeed } from '../src/seed.js';

const studio = () => createStudioRuntime(createSeed());
const STAGES = ['lab-s0', 'lab-s1', 'lab-s2', 'lab-s3', 'lab-holes-nearest', 'lab-s7-course', 'lab-route'];

test('the pipeline runs S0 through the round as one composition per Stage', () => {
  const runtime = studio();
  const state = runtime.lab.pipeline(runtime.lab.sample());
  assert.deepEqual(state.stages.map(stage => stage.status), state.stages.map(() => 'produced'));
  assert.deepEqual(state.stages.map(stage => stage.composition), STAGES);
  assert.equal(state.capture.widthPx, 512);
  // Every declared produce is on the board, and the Part says how many things it holds.
  for (const stage of state.stages) {
    assert.ok(stage.produced.length, stage.stage);
    for (const { address, count } of stage.produced) {
      assert.ok(runtime.pxc.has(address), address);
      assert.ok(count === null || count >= 0, address);
    }
  }
  // The Stages read each other by address: S1 reads S0's canonical pixels, the round reads all three.
  assert.deepEqual(runtime.lab.specs().at(-1).needs, ['px.exp.lab.badges.objects', 'px.exp.lab.baskets', 'px.exp.lab.tees']);
});

test('each Stage leaves the receipt and the run record every other composition leaves', () => {
  const runtime = studio();
  runtime.lab.pipeline(runtime.lab.sample());
  const listed = runtime.receipts().rows.map(row => row.name);
  for (const name of STAGES) {
    assert.ok(listed.includes(name), `${name} is not listed in px.studio.receipts`);
    assert.ok(runtime.pxc.has(`px.receipt.${name}`), name);
    const { address, record } = runtime.runRecord(name);
    assert.equal(address, `px.run.${name}`);
    assert.equal(record.pcr, name);
    assert.ok(record.ticks.length);
  }
  // S1 runs the LAB's own document, Tick for Tick.
  assert.deepEqual(runtime.runRecord('lab-s1').record.ticks.map(tick => tick.name), ['BlackMask', 'WhiteMask', 'BadgeAssembly', 'WhiteDigitRecognition', 'BadgeOutputs']);
});

test('the produce is what the fixture draws: three badges read, two baskets, three tees, a round in badge order', () => {
  const runtime = studio();
  runtime.lab.pipeline(runtime.lab.sample());
  const views = Object.fromEntries(runtime.lab.views().map(view => [view.key, view]));
  assert.deepEqual(views.s1.objects.map(object => object.detail.reading), ['11', '10', '01']);
  assert.equal(views.s2.objects.length, 2);
  assert.equal(views.s3.objects.length, 3);
  // The nearest-anchor fallback names the hole it could not finish rather than guessing a basket for it.
  assert.deepEqual(views['holes-nearest'].objects.map(object => object.label), ['hole 1', 'hole 10', 'hole 11 · missing basket']);
  // S7's obstacle map is derived from the pixels no Stage object owns, and two straight legs cross it.
  assert.ok(views['s7-course'].cells.centres.length > 0);
  assert.deepEqual(runtime.pxc.get('px.exp.lab.course.summary').blockedStraightLegs, ['walk:basket-2->tee-2', 'play:tee-2->basket-1']);
  // The order is the reading, not the position: hole 1 sits lower in the image than hole 10.
  assert.deepEqual(views.route.objects.map(object => object.label), ['hole 1', 'hole 10']);
  assert.equal(views.route.kind, 'path');
  assert.ok(views.route.legs.some(leg => leg.kind === 'play') && views.route.legs.some(leg => leg.kind === 'walk'));
  // Every drawable object names the Part it came from and where it is on the canonical raster.
  for (const view of runtime.lab.views()) for (const object of view.objects) assert.ok(runtime.pxc.has(object.part), object.part);
  const raster = runtime.lab.raster();
  assert.equal(raster.rgba.length, raster.widthPx * raster.heightPx * 4);
});

test('provenance is read off the record: which composition, which Tick, which Calculation', () => {
  const runtime = studio();
  runtime.lab.pipeline(runtime.lab.sample());
  assert.deepEqual(runtime.lab.provenance('px.exp.lab.badges.objects'), {
    composition: 'lab-s1', tick: 'BadgeOutputs', call: 'fn.lab.s1.badges.declareownership',
    inputs: ['px.exp.lab.s1.whitedigits.recognizedbadges']
  });
  assert.equal(runtime.lab.provenance('px.exp.lab.baskets').composition, 'lab-s2');
  assert.equal(runtime.lab.provenance('px.exp.lab.tees').call, 'fn.lab.tee.findpx');
  assert.equal(runtime.lab.provenance('px.domain.Disc.buzzz-mint'), null);
});

test('a Stage that cannot run refuses with its reason, and the Stages after it stay not-run', () => {
  const runtime = studio();
  runtime.lab.begin(runtime.lab.sample());
  assert.throws(() => runtime.lab.stage(1), /S0 has not produced yet/);
  const state = runtime.lab.state();
  assert.equal(state.stages[0].status, 'not-run');
  assert.equal(state.stages[1].status, 'refused');
  assert.match(state.stages[1].reason, /S0 has not produced yet/);
  assert.deepEqual(state.stages.slice(2).map(stage => stage.status), state.stages.slice(2).map(() => 'not-run'));
  // The refusal is on the record as a Part, not only in a message.
  assert.equal(runtime.pxc.get('px.exp.lab.pipeline').stages[1].status, 'refused');
  assert.throws(() => runtime.lab.pipeline({ imageId: 'not-a-capture' }), /a capture is/);
});

test('a Stage still being built joins the pipeline as one spec and runs, draws and inspects like the rest', () => {
  const runtime = studio();
  const HOLES = 'px.exp.lab.stub.holes';
  runtime.lab.addStage({
    key: 'stub', stage: 'S4', title: 'Holes (stub)', composition: 'lab-stub',
    about: 'the wiring point S4/S5/S6 take: one spec, its own Calculation, its own document.',
    needs: ['px.exp.lab.route.labfixture'], produces: [HOLES],
    register: lab => lab.register('fn.lab.stub.holes', ({ round }) => round.holes.map(hole => ({ ...hole }))),
    ticks: () => [{ name: 'Stub.holes', Calculations: [{ call: 'fn.lab.stub.holes', with: { round: 'px.exp.lab.route.labfixture' }, args: {}, into: HOLES }] }],
    view: lab => ({ kind: 'boxes', tone: 'hole', objects: lab.get(HOLES).map((hole, index) => ({ id: `hole-${hole.number}`, label: `hole ${hole.number}`, bbox: [0, 0, 8, 8], at: [4, 4], part: HOLES, index, detail: hole })) })
  });
  const state = runtime.lab.pipeline(runtime.lab.sample());
  assert.equal(state.stages.length, 8);
  assert.equal(state.stages.at(-1).status, 'produced');
  assert.deepEqual(state.stages.at(-1).produced, [{ address: HOLES, count: 2 }]);
  assert.ok(runtime.pxc.has('px.receipt.lab-stub'));
  assert.equal(runtime.runRecord('lab-stub').record.ticks[0].name, 'Stub.holes');
  assert.equal(runtime.lab.views().at(-1).objects.length, 2);
  assert.equal(runtime.lab.provenance(HOLES).composition, 'lab-stub');
  assert.throws(() => runtime.lab.addStage({ key: 'stub', stage: 'S4', title: 'x', composition: 'lab-stub', produces: [HOLES], ticks: () => [] }), /already in this pipeline/);
  assert.throws(() => runtime.lab.addStage({ key: 'bad', stage: 'S9', title: 'x', composition: 'S9', produces: [HOLES], ticks: () => [] }), /named lab-/);
  assert.throws(() => runtime.lab.addStage({ key: 'bad', stage: 'S9', title: 'x', composition: 'lab-bad', produces: ['px.nope'], ticks: () => [] }), /px\.exp\.lab/);
});

test('the lab Calculations are the studio\'s own, and no domain fact is written by a Stage', () => {
  const runtime = studio();
  const before = runtime.parts().filter(part => part.address.startsWith('px.domain.')).length;
  runtime.lab.pipeline(runtime.lab.sample());
  assert.equal(runtime.parts().filter(part => part.address.startsWith('px.domain.')).length, before);
  // Every Stage invocation is on `calls`, so the receipt counts them the way it counts a card's.
  const receipt = runtime.pxc.get('px.receipt.lab-s2');
  assert.equal(receipt.computed, receipt.trace.length);
  assert.ok(receipt.trace.every(step => step.call.startsWith('fn.lab.')));
  // A card still renders after a pipeline: one board, one set of Calculations.
  assert.ok(runtime.card('buzzz-mint', 'discImage', {}).svg.startsWith('<svg'));
});

test('the course arrangement stands the cards at the holes the Stages found', () => {
  const runtime = studio();
  runtime.dispatch({ type: 'layout.set', patch: { arrangement: 'course' } });
  // Before a course exists the comparison refuses in plain words instead of inventing positions.
  assert.throws(() => runtime.scene({ mode: 'battle' }), /No course has been built yet/);
  runtime.lab.pipeline(runtime.lab.sample());
  const scene = runtime.scene({ mode: 'battle' }), overlay = scene.scene;
  assert.equal(overlay.arrangement, 'course');
  assert.deepEqual(overlay.placements.map(placement => placement.anchor.id), ['hole-1', 'hole-10', 'hole-11']);
  // Every anchor is a hole S4 published, and every card is centred on it inside the 1920x1080 frame.
  const holes = runtime.pxc.get('px.exp.lab.holes.objects');
  assert.deepEqual(overlay.anchors.map(anchor => anchor.at), holes.map(hole => (hole.basket ?? hole.tee).at));
  for (const placement of overlay.placements) {
    assert.ok(placement.x >= 0 && placement.y >= 0 && placement.x + placement.card.width * overlay.scale <= 1920 && placement.y + placement.card.height * overlay.scale <= 1080, placement.anchor.id);
    assert.ok(Math.abs(placement.x + (placement.card.width * overlay.scale) / 2 - placement.anchor.x) < 1 || placement.x === 60 || placement.x + placement.card.width * overlay.scale === 1860);
  }
  // The layout Calculation read the Stage's own produce Part; nothing was copied into the layout.
  assert.ok(scene.run.trace.some(step => step.call === 'fn.comparison.layout' && step.inputs.course === 'px.exp.lab.holes.objects'));
  // Same overlay, same cards, same materialize: one group per entry.
  assert.equal((scene.svg.match(/data-entry="entry-/g) ?? []).length, scene.cardCount);
  assert.equal(runtime.lab.anchorAddress(), 'px.exp.lab.holes.objects');
});

test('the anchors come from whichever Part the Stages published', async () => {
  const { courseAnchors } = await import('../src/presentation.js');
  const fromS4 = courseAnchors([{ number: 3, tee: { at: [10, 10] }, basket: { at: [30, 40] } }, { number: 4, tee: { at: [50, 60] }, basket: null }]);
  assert.deepEqual(fromS4.anchors, [{ id: 'hole-3', label: 'Hole 3', at: [30, 40] }, { id: 'hole-4', label: 'Hole 4', at: [50, 60] }]);
  const fromRound = courseAnchors({ waypoints: [{ id: 'tee-1', at: [4, 5] }, { id: 'basket-1', at: [9, 9] }], legs: [] });
  assert.deepEqual(fromRound.anchors.map(anchor => anchor.id), ['tee-1', 'basket-1']);
  // Only S5's graph carries the raster it was measured in; the others are framed by their own extent.
  const fromGraph = courseAnchors({ frame: { widthPx: 512, heightPx: 920, cellPx: 16 }, holes: [{ number: 1, tee: { at: [1, 2] }, basket: { at: [3, 4] } }] });
  assert.equal(fromGraph.frame.widthPx, 512);
  assert.ok(fromRound.frame.widthPx < 512);
  assert.throws(() => courseAnchors(null), /No course has been built yet/);
  assert.throws(() => courseAnchors([]), /no hole a card could stand at/);
});
