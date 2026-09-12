#!/usr/bin/env node
/** Headless review of the live ID3 page against an already-built local server. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import process from 'node:process';
import { DIGIT_DATASET, DIGIT_TEST_SAMPLES } from '../src/reference-algorithms/digit-data.js';
import { validate } from '../pyto/viewer/adapters.js';

const supplied = process.argv.indexOf('--url');
const origin = supplied < 0 ? 'http://127.0.0.1:8848/' : process.argv[supplied + 1];
assert.ok(origin, '--url needs a value');
const output = process.env.ID3_BROWSER_OUTPUT || 'test-results/algorithm-references-id3';
const modules = process.env.PLAYWRIGHT_MODULE ? [process.env.PLAYWRIGHT_MODULE] : [
  'playwright',
  '/Users/samuelmahan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
];
let browserApi, importError;
for (const moduleName of modules) {
  try { browserApi = await import(moduleName); break; }
  catch (error) { importError = error; }
}
if (!browserApi) throw new Error(`Playwright unavailable: ${importError.message}`);
const executablePath = process.env.CHROME || process.env.CHROMIUM || process.env.BROWSER_EXECUTABLE
  || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
assert.ok(fs.existsSync(executablePath), `Chrome executable missing: ${executablePath}`);

// Independent arithmetic oracle: it receives retained raw examples, never learner scores.
const entropy = rows => {
  const counts = new Map();
  for (const row of rows) counts.set(row.label, (counts.get(row.label) || 0) + 1);
  return [...counts.values()].reduce((sum, n) => sum - n / rows.length * Math.log2(n / rows.length), 0);
};
const expectedCandidates = Array.from({ length: DIGIT_DATASET.width * DIGIT_DATASET.height }, (_, pixel) => {
  const off = DIGIT_DATASET.samples.filter(row => row.pixels[pixel] < DIGIT_DATASET.threshold);
  const on = DIGIT_DATASET.samples.filter(row => row.pixels[pixel] >= DIGIT_DATASET.threshold);
  const weightedEntropy = (off.length * entropy(off) + on.length * entropy(on)) / DIGIT_DATASET.samples.length;
  return { pixel, off: off.map(row => row.id), on: on.map(row => row.id), weightedEntropy,
    gain: entropy(DIGIT_DATASET.samples) - weightedEntropy };
});
const expectedWinner = [...expectedCandidates].sort((a, b) => b.gain - a.gain || a.pixel - b.pixel)[0];
const close = (actual, expected, label) => assert.ok(Math.abs(actual - expected) < 1e-12, `${label}: ${actual} != ${expected}`);
assert.equal(new Set(DIGIT_DATASET.samples.map(row => row.sourceRow)).size, DIGIT_DATASET.samples.length);
assert.equal(DIGIT_TEST_SAMPLES.some(row => DIGIT_DATASET.samples.some(train => train.sourceRow === row.sourceRow)), false);
assert.match(DIGIT_DATASET.metadata.selection, /source order/);
assert.match(DIGIT_DATASET.metadata.transformation, />= 8/);
assert.match(DIGIT_DATASET.metadata.sourceSha256, /^[0-9a-f]{64}$/);

fs.mkdirSync(output, { recursive: true });
const browser = await browserApi.chromium.launch({ headless: true, executablePath });
try {
  const context = await browser.newContext({ viewport: { width: 1437, height: 789 }, acceptDownloads: true });
  const page = await context.newPage(), errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(new URL('/public/algorithm-references/index.html', origin).href, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => !!window.id3Demo?.session);
  const buildResponse = await page.request.get(new URL('/build-info.json', origin).href);
  assert.equal(buildResponse.ok(), true, 'Tests must identify the actual served build');
  const build = await buildResponse.json();
  if (process.env.SOURCE_COMMIT) assert.equal(build.commit, process.env.SOURCE_COMMIT);
  const root = page.locator('#digit-lab');
  const inspect = () => page.evaluate(() => {
    const demo = window.id3Demo;
    return { state: demo.session.state, frame: demo.session.frame(demo.transport.cursor),
      cursor: demo.transport.cursor, record: demo.session.record,
      receipts: demo.lab.addresses().filter(address => address.startsWith('px.receipt.')) };
  });
  const idle = () => page.waitForFunction(() => !window.id3Demo.busy && !window.id3Demo.transport.busy && !window.id3Demo.transport.playing);
  const next = async () => { await root.locator('[data-id3-next]').click(); await idle(); };
  const dialogOrigins = new Map();
  const dialogFor = name => root.locator(`dialog[data-id3-dialog="${name}"]`);
  const openDialog = async (name, opener = `[data-id3-open="${name}"]`) => {
    const dialog = dialogFor(name);
    if (!await dialog.evaluate(node => node.open)) {
      dialogOrigins.set(name, opener);
      await root.locator(opener).click();
    }
    assert.equal(await dialog.evaluate(node => node.open), true);
    assert.equal(await dialog.isVisible(), true);
    assert.equal(await dialog.evaluate(node => node.contains(document.activeElement)), true,
      `Opening ${name} must move keyboard focus into its modal`);
    return dialog;
  };
  const closeDialog = async (name, escape = false) => {
    if (escape) await page.keyboard.press('Escape');
    else await dialogFor(name).locator('[data-id3-close]').click();
    assert.equal(await dialogFor(name).evaluate(node => node.open), false);
    assert.equal(await dialogFor(name).isVisible(), false);
    assert.equal(await root.locator(dialogOrigins.get(name) || `[data-id3-open="${name}"]`).evaluate(node => node === document.activeElement), true,
      `Closing ${name} must return focus to its opener`);
  };
  const actualParts = () => page.evaluate(() => {
    const { lab, session, transport } = window.id3Demo, frame = session.frame(transport.cursor);
    return { dataset: lab.get(frame.datasetAddress), tree: lab.get(frame.treeAddress),
      scores: frame.scoresAddress ? lab.get(frame.scoresAddress) : null,
      allSourcesExist: frame.sourceAddresses.every(address => lab.has(address)),
      config: lab.get(session.addresses.config) };
  });
  const inspectSources = async () => {
    const dialog = await openDialog('inspect');
    const details = dialog.locator('.id3-inspector');
    if (!await details.evaluate(node => node.open)) await details.locator(':scope > summary').click();
    const values = await dialog.locator('[data-id3-part-address]').evaluateAll(nodes => nodes.map(node => ({
      address: node.dataset.id3PartAddress, text: node.querySelector('pre').textContent,
      exists: window.id3Demo.lab.has(node.dataset.id3PartAddress),
      actual: window.id3Demo.lab.get(node.dataset.id3PartAddress)
    })));
    const frame = (await inspect()).frame;
    assert.deepEqual(values.map(row => row.address).sort(), [...frame.sourceAddresses].sort());
    for (const row of values) {
      assert.equal(row.exists, true);
      // JSON intentionally writes IEEE -0 as 0; compare the actual displayed serialization.
      assert.equal(row.text, JSON.stringify(row.actual, null, 2));
    }
  };
  const graph = async frame => {
    const nodes = await root.locator('[data-id3-node]').evaluateAll(nodes => nodes.map(node => ({
      id: node.dataset.id3Node, tag: node.tagName,
      sampleIds: [...node.querySelectorAll('[data-id3-sample]')].map(sample => sample.dataset.id3Sample)
    })));
    const nodeIds = nodes.map(node => node.id);
    assert.equal(new Set(nodeIds).size, nodeIds.length, 'Each learned node must have one card, with no duplicate miniature node');
    assert.deepEqual(nodeIds.sort(), Object.keys(frame.tree.nodes).sort());
    for (const node of nodes) {
      assert.equal(node.tag, 'ARTICLE', 'The actual tree node is its HTML sample/question card');
      assert.deepEqual(node.sampleIds, frame.tree.nodes[node.id].sampleIds, `Card ${node.id} must show its actual sample pile`);
    }
    const expected = Object.values(frame.tree.nodes).flatMap(node => node.children
      ? Object.entries(node.children).map(([side, to]) => ({ from: node.id, to, label: side.toUpperCase() })) : []);
    const edges = await root.locator('.id3-tree-svg [data-from][data-to]').evaluateAll(nodes => nodes.map(node => ({
      from: node.dataset.from, to: node.dataset.to, label: node.querySelector('text').textContent
    })));
    const order = rows => rows.sort((a, b) => `${a.from}:${a.to}`.localeCompare(`${b.from}:${b.to}`));
    assert.deepEqual(order(edges), order(expected));
  };
  const canvasView = () => root.locator('.id3-tree-scroll').evaluate(stage => {
    const bounds = stage.getBoundingClientRect();
    return { viewport: { width: innerWidth, height: innerHeight }, scrollY,
      stage: { left: bounds.left, top: bounds.top, right: bounds.right, bottom: bounds.bottom },
      cards: [...stage.querySelectorAll('article[data-id3-node]')].map(node => {
        const r = node.getBoundingClientRect();
        return { id: node.dataset.id3Node, left: r.left, top: r.top, right: r.right, bottom: r.bottom, width: r.width, height: r.height };
      }) };
  });
  const cardsFit = (view, cards = view.cards) => {
    for (const card of cards) {
      assert.ok(card.width > 0 && card.height > 0);
      assert.ok(card.left >= Math.max(0, view.stage.left) - 1 && card.top >= Math.max(0, view.stage.top) - 1
        && card.right <= Math.min(view.viewport.width, view.stage.right) + 1
        && card.bottom <= Math.min(view.viewport.height, view.stage.bottom) + 1,
      `The entire ${card.id} card must be visible: ${JSON.stringify(card)}`);
    }
  };
  const review = async index => {
    await root.locator('[data-id3-scrub]').evaluate((input, value) => {
      input.value = String(value); input.dispatchEvent(new Event('input', { bubbles: true }));
    }, index);
    await page.waitForFunction(value => window.id3Demo.transport.cursor === value, index);
  };

  const initial = await inspect();
  assert.equal(initial.state.nextTick, 0);
  assert.equal(initial.frame.candidates, null, 'No score is calculated in the initial frame');
  assert.equal(Object.keys(initial.frame.tree.nodes).length, 1, 'No future split is built in advance');
  assert.equal(initial.record, null);
  assert.equal(initial.frame.tree.nodes.n0.counts, null);
  assert.equal(initial.frame.tree.nodes.n0.entropy, null);
  const inputs = await actualParts();
  assert.deepEqual(inputs.dataset, DIGIT_DATASET, 'Original sample intensities and source rows stay intact');
  assert.equal(inputs.config.threshold, DIGIT_DATASET.threshold);
  assert.equal(inputs.config.attributeKind, 'binary categorical');
  assert.equal(initial.frame.scoresAddress, null);
  for (const name of ['questions', 'drawing', 'inspect']) {
    assert.equal(await dialogFor(name).evaluate(node => node.open), false);
    assert.equal(await dialogFor(name).isVisible(), false);
  }
  await openDialog('questions');
  assert.equal(await dialogFor('questions').locator('[data-id3-gain]:not([data-id3-gain=""])').count(), 0);
  await closeDialog('questions', true);
  await openDialog('questions'); await closeDialog('questions');
  const drawingDialog = await openDialog('drawing');
  assert.equal(await drawingDialog.locator('[data-id3-test] option').count(), DIGIT_TEST_SAMPLES.length + 1);
  assert.match(await drawingDialog.textContent(), /held-out example/);
  assert.match(await drawingDialog.textContent(), /new handwriting style can follow the wrong leaf/);
  await closeDialog('drawing', true);
  assert.deepEqual((await inspect()).receipts, initial.receipts, 'Opening and closing dialogs does not execute a Calculation');
  await graph(initial.frame);
  await root.screenshot({ path: `${output}/initial.png` });

  await root.locator('[data-id3-next]').evaluate(button => { button.click(); button.click(); button.click(); });
  await idle();
  const scored = await inspect();
  assert.equal(scored.state.nextTick, 1, 'Rapid clicks must coalesce to one operation');
  assert.equal(scored.record.ticks.length, 1);
  assert.equal(Object.keys(scored.frame.tree.nodes).length, 1);
  const candidates = scored.frame.candidates.candidates;
  const scoredParts = await actualParts();
  assert.equal(scoredParts.allSourcesExist, true);
  assert.deepEqual(scored.frame.tree, scoredParts.tree);
  assert.deepEqual(scored.frame.candidates, scoredParts.scores, 'Displayed scores must be the produced Part');
  assert.ok(scored.frame.step.actual_produces.includes(scored.frame.scoresAddress));
  assert.ok(scored.frame.step.actual_produces.includes(scored.frame.treeAddress));
  assert.equal(candidates.length, expectedCandidates.length);
  for (const actual of candidates) {
    const expected = expectedCandidates[actual.pixel];
    close(actual.gain, expected.gain, `gain at pixel ${actual.pixel}`);
    close(actual.weightedEntropy, expected.weightedEntropy, `weighted entropy at pixel ${actual.pixel}`);
    assert.deepEqual(actual.off.sampleIds, expected.off);
    assert.deepEqual(actual.on.sampleIds, expected.on);
  }
  const questions = await openDialog('questions');
  const visibleGains = await questions.locator('[data-id3-pixel]').evaluateAll(nodes => nodes.map(node => ({
    pixel: Number(node.dataset.id3Pixel), gain: Number(node.dataset.id3Gain), source: node.dataset.sourceAddress
  })));
  assert.equal(visibleGains.length, candidates.length);
  for (const value of visibleGains) {
    close(value.gain, expectedCandidates[value.pixel].gain, `visible gain at pixel ${value.pixel}`);
    assert.equal(value.source, scored.frame.scoresAddress);
  }
  await questions.screenshot({ path: `${output}/questions-dialog.png` });
  await questions.locator('[data-id3-pixel="2"]').click();
  assert.equal(await dialogFor('questions').evaluate(node => node.open), true, 'A question preview must keep its dialog open');
  assert.deepEqual((await inspect()).state, scored.state, 'Previewing a scored question does not change the learned model');
  assert.deepEqual((await inspect()).receipts, scored.receipts, 'Question previews do not execute Calculations');
  assert.deepEqual((await inspect()).frame.tree, scored.frame.tree);
  await graph(scored.frame);
  await closeDialog('questions', true);
  await next();
  const split = await inspect();
  assert.equal(split.state.nextTick, 2);
  assert.equal(Object.keys(split.frame.tree.nodes).length, 3, 'ChooseSplit creates the two real child branches');
  assert.equal(split.frame.tree.nodes.n0.pixel, expectedWinner.pixel);
  assert.equal(split.frame.tree.nodes.n0.pixel, 28);
  assert.deepEqual(split.frame.tree.nodes['n0.0'].sampleIds, expectedWinner.off);
  assert.deepEqual(split.frame.tree.nodes['n0.1'].sampleIds, expectedWinner.on);
  assert.deepEqual(split.frame.tree.nodes.n0.children, { off: 'n0.0', on: 'n0.1' });
  for (const side of ['off', 'on']) {
    const branch = root.locator(`.id3-tree-plane [data-id3-branch="${side}"]`);
    assert.equal(await branch.getAttribute('data-id3-node-id'), `n0.${side === 'off' ? 0 : 1}`);
    const tiles = await branch.locator('[data-id3-sample]').evaluateAll(nodes => nodes.map(node => ({
      id: node.dataset.id3Sample, label: Number(node.querySelector('b').textContent),
      description: node.querySelector('svg').getAttribute('aria-label'),
      source: node.dataset.sourceAddress,
      intensities: [...node.querySelector('svg').querySelectorAll('rect')].slice(1, 65).map(cell => Number(cell.getAttribute('opacity')) * 16)
    })));
    assert.deepEqual(tiles.map(tile => tile.id), expectedWinner[side]);
    for (const tile of tiles) {
      const sample = DIGIT_DATASET.samples.find(row => row.id === tile.id);
      assert.equal(tile.label, sample.label); assert.ok(tile.description.includes(tile.id));
      assert.equal(tile.source, split.frame.datasetAddress); assert.deepEqual(tile.intensities, sample.pixels);
    }
  }
  assert.match(await root.locator('[data-id3-node="n0"] [data-id3-question-pixel="28"]').textContent(), /row 4, column 5/);
  await openDialog('questions');
  await dialogFor('questions').locator('[data-id3-pixel="2"]').click();
  assert.deepEqual((await inspect()).frame.tree, split.frame.tree);
  assert.deepEqual((await inspect()).receipts, split.receipts);
  assert.equal(await root.locator('.id3-tree-plane [data-id3-node="n0"] [data-id3-question-pixel="28"]').count(), 1,
    'A dialog preview must not replace the actual learned question on the root card');
  await closeDialog('questions');
  await graph(split.frame);
  await page.evaluate(() => window.scrollTo(0, 0));
  const fold = await canvasView();
  assert.equal(fold.cards.length, 3);
  cardsFit(fold);
  await root.screenshot({ path: `${output}/learned-split.png` });
  await root.locator('.id3-tree-scroll').screenshot({ path: `${output}/workspace-split.png` });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: `${output}/split-viewport.png` });
  console.log(`First-split fit: ${fold.cards.length} unique cards inside ${fold.viewport.width}×${fold.viewport.height}.`);
  await openDialog('inspect', '[data-id3-inspect-node="n0"]');
  assert.deepEqual(JSON.parse(await root.locator('[data-id3-node-value="n0"]').textContent()), split.frame.tree.nodes.n0);
  await inspectSources();
  await closeDialog('inspect');

  // The remaining assertions are kept together below so source/build drift is visible.
  await root.locator('[data-id3-back]').click(); await idle();
  const back = await inspect();
  assert.equal(back.state.nextTick, 2);
  assert.deepEqual(back.frame, scored.frame);
  assert.deepEqual(back.receipts, split.receipts, 'Back may not execute any Calculation');
  await review(0);
  assert.deepEqual((await inspect()).receipts, split.receipts, 'Scrubbing may not execute any Calculation');
  await review(2);
  assert.deepEqual((await inspect()).frame, split.frame);

  await inspectSources();
  const partialDownload = page.waitForEvent('download');
  await root.locator('[data-id3-export]').click();
  await (await partialDownload).saveAs(`${output}/through-2.json`);
  const partial = JSON.parse(fs.readFileSync(`${output}/through-2.json`, 'utf8'));
  validate(partial); assert.equal(partial.ticks.length, 2);
  await closeDialog('inspect');

  // Prediction follows an existing frame. It must not grow its unfinished children.
  const beforePrediction = await inspect();
  await openDialog('drawing');
  await root.locator('[data-id3-test]').selectOption('0');
  assert.deepEqual(await page.evaluate(() => window.id3Demo.drawing), DIGIT_TEST_SAMPLES[0].pixels);
  await root.locator('[data-id3-predict]').click();
  await page.waitForFunction(() => !!window.id3Demo.prediction);
  const partialPrediction = await page.evaluate(() => window.id3Demo.prediction);
  assert.equal(partialPrediction.result.status, 'unresolved');
  assert.equal(partialPrediction.result.prediction, null);
  assert.match(partialPrediction.result.reason, /unexpanded|unfinished|pending/);
  assert.equal(partialPrediction.result.visited[0].nodeId, 'n0');
  assert.equal(partialPrediction.result.visited[0].pixel, 28);
  assert.equal(partialPrediction.result.visited.at(-1).status, 'pending');
  assert.equal(await root.locator('[data-id3-prediction]').getAttribute('data-id3-prediction-status'), 'unresolved');
  assert.match(await root.locator('[data-id3-prediction]').textContent(), /unfinished branch/);
  assert.equal(await root.locator('[data-id3-prediction]').getAttribute('data-source-address'), partialPrediction.resultAddress);
  assert.deepEqual(await root.locator('[data-id3-prediction-node]').evaluateAll(nodes => nodes.map(node => node.dataset.id3PredictionNode)),
    partialPrediction.result.visited.map(visit => visit.nodeId));
  assert.deepEqual(await page.evaluate(address => window.id3Demo.lab.get(address), partialPrediction.resultAddress), partialPrediction.result);
  assert.deepEqual((await inspect()).state, beforePrediction.state);
  validate(partialPrediction.record);
  await dialogFor('drawing').screenshot({ path: `${output}/drawing-dialog.png` });
  const beforeEdit = await inspect();
  await root.locator('[data-id3-draw-cell="28"]').click();
  assert.equal(await page.evaluate(() => window.id3Demo.prediction), null);
  assert.equal(await root.locator('[data-id3-prediction]').getAttribute('data-id3-prediction-status'), 'not-run',
    'Editing the image must clear the visible stale answer as well as its JS value');
  assert.deepEqual((await inspect()).receipts, beforeEdit.receipts, 'Editing pixels does not execute training or prediction');
  await closeDialog('drawing');

  await page.emulateMedia({ reducedMotion: 'reduce' });
  const playElement = await root.locator('[data-id3-play]').elementHandle();
  // Reduced-motion Play may finish its retained work before click dispatch returns.
  await root.locator('[data-id3-play]').click({ timeout: 120000 });
  // Read and click in one browser turn: the toolbar is replaced at every frame,
  // so a locator resolved in an earlier protocol turn can already be detached.
  const pauseHandle = await page.waitForFunction(originalButton => {
    const demo = window.id3Demo, state = demo.session.state;
    if (!demo.transport.playing || state.nextTick <= 2 || state.status === 'complete') return false;
    const button = document.querySelector('#digit-lab [data-id3-play]');
    const captured = { tick: state.nextTick, status: state.status,
      label: button.textContent, connected: button.isConnected, disabled: button.disabled,
      retainedElement: button === originalButton && originalButton.isConnected };
    button.click();
    return { ...captured, afterPlaying: demo.transport.playing };
  }, playElement);
  const pauseClick = await pauseHandle.jsonValue();
  await pauseHandle.dispose();
  await playElement.dispose();
  assert.ok(pauseClick.tick > 2 && pauseClick.tick < 50, JSON.stringify(pauseClick));
  assert.equal(pauseClick.connected, true);
  assert.equal(pauseClick.retainedElement, true, 'Rendering training frames must retain the live Play/Pause element');
  assert.equal(pauseClick.disabled, false);
  assert.equal(pauseClick.label, 'Pause');
  assert.equal(pauseClick.afterPlaying, false, 'The connected Pause button must stop playback immediately');
  await idle();
  const paused = await inspect();
  assert.ok(paused.state.nextTick > 2 && paused.state.nextTick < 50,
    `Reduced-motion Pause must stop before completion: clicked at ${pauseClick.tick}, settled at ${paused.state.nextTick}`);
  assert.ok(paused.state.nextTick >= pauseClick.tick && paused.state.nextTick <= pauseClick.tick + 1,
    'Pause may finish at most the operation already in flight');
  assert.notEqual(paused.state.status, 'complete');
  await page.waitForTimeout(100);
  assert.deepEqual((await inspect()).state, paused.state, 'Paused training must remain stopped');
  assert.deepEqual((await inspect()).receipts, paused.receipts);
  await root.locator('[data-id3-play]').click({ timeout: 120000 });
  await page.waitForFunction(() => window.id3Demo.session.state.status === 'complete'
    && !window.id3Demo.transport.busy && !window.id3Demo.transport.playing, null, { timeout: 120000 });
  const completed = await inspect();
  validate(completed.record);
  assert.equal(completed.record.ticks.length, completed.state.nextTick);
  assert.equal(Object.values(completed.frame.tree.nodes).some(node => node.status === 'pending'), false);
  await graph(completed.frame);
  assert.deepEqual(completed.frame.tree.nodes.n0.sampleIds, DIGIT_DATASET.samples.map(row => row.id));
  assert.ok(Object.values(completed.frame.tree.nodes).filter(node => node.status === 'leaf').every(node => !!node.reason));
  const evaluated = await page.evaluate(({ training, heldOut }) => {
    const demo = window.id3Demo;
    const evaluate = rows => rows.map(row => ({ id: row.id, expected: row.label,
      result: demo.session.predict(row.pixels, { frameIndex: demo.transport.cursor }).result }));
    return { training: evaluate(training), heldOut: evaluate(heldOut) };
  }, { training: DIGIT_DATASET.samples, heldOut: DIGIT_TEST_SAMPLES });
  assert.equal(evaluated.training.every(row => row.result.status === 'prediction' && row.result.prediction === row.expected), true);
  const heldOutCorrect = evaluated.heldOut.filter(row => row.result.prediction === row.expected).length;
  assert.equal(heldOutCorrect, 10, 'The retained teaching test set produces 10/20, not training-set accuracy');
  assert.deepEqual((await inspect()).state, completed.state, 'Evaluating examples must not retrain the tree');
  fs.writeFileSync(`${output}/predictions.json`, JSON.stringify(evaluated, null, 2) + '\n');
  fs.writeFileSync(`${output}/completed.json`, JSON.stringify(completed.record, null, 2) + '\n');

  // Export is scoped to the selected retained frame even after later execution.
  const afterEvaluation = await inspect();
  await review(1);
  assert.deepEqual((await inspect()).receipts, afterEvaluation.receipts);
  assert.equal(await root.locator('.id3-live-label').textContent(), 'Reviewing history · training complete');
  assert.equal(await root.locator('[data-id3-next]').isDisabled(), true);
  await inspectSources();
  const retainedDownload = page.waitForEvent('download');
  await root.locator('[data-id3-export]').click();
  await (await retainedDownload).saveAs(`${output}/reviewed-through-1.json`);
  const retained = JSON.parse(fs.readFileSync(`${output}/reviewed-through-1.json`, 'utf8'));
  validate(retained); assert.equal(retained.ticks.length, 1);
  await closeDialog('inspect');
  await page.setViewportSize({ width: 390, height: 844 });
  await review(completed.state.nextTick);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true,
    'The completed tree must scroll within its own panel on a narrow page');
  await review(2);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true,
    'The first split must not make the whole narrow page overflow');
  await root.screenshot({ path: `${output}/narrow-split.png` });

  // View controls operate on the completed tree without executing or changing it.
  await page.setViewportSize({ width: 1437, height: 789 });
  await review(completed.state.nextTick);
  const beforeViewControls = await inspect();
  const unchangedByView = async () => {
    const current = await inspect();
    assert.deepEqual(current.state, beforeViewControls.state);
    assert.deepEqual(current.receipts, beforeViewControls.receipts, 'View controls must not execute Calculations');
  };
  await root.locator('[data-id3-fit]').click();
  const fitted = await canvasView();
  assert.equal(fitted.cards.length, Object.keys(completed.frame.tree.nodes).length);
  cardsFit(fitted); await unchangedByView();
  await root.locator('.id3-tree-scroll').screenshot({ path: `${output}/completed-fit.png` });
  const fitZoom = await root.locator('[data-id3-zoom-value]').textContent();
  await root.locator('[data-id3-zoom="in"]').click();
  const enlarged = await canvasView();
  assert.ok(enlarged.cards[0].width > fitted.cards[0].width, 'Zoom in must enlarge actual tree cards');
  await unchangedByView();
  await root.locator('[data-id3-zoom="out"]').click();
  const reduced = await canvasView();
  assert.ok(Math.abs(reduced.cards[0].width - fitted.cards[0].width) < 1e-5);
  await unchangedByView();
  await root.locator('[data-id3-current]').click();
  assert.equal(await root.locator('[data-id3-zoom-value]').textContent(), '100%');
  const focused = await canvasView();
  const activeCard = focused.cards.find(card => card.id === completed.frame.activeNodeId);
  assert.ok(activeCard, 'Current node must refer to an actual learned node');
  cardsFit(focused, [activeCard]); await unchangedByView();
  const viewControls = { fitZoom, fittedCards: fitted.cards.length, currentNode: activeCard.id, currentZoom: '100%' };

  assert.deepEqual(errors, []);
  fs.writeFileSync(`${output}/verification.json`, JSON.stringify({ pass: true, build,
    sourceState: 'Base commit plus shared uncommitted work; served build fingerprint retained.',
    rootWinner: expectedWinner, checks: ['initial absent candidates and future nodes',
      'rapid-click one-operation guard', '64 independent entropy/gain checks',
      'actual split', 'Back/scrub without execution', 'valid partial export',
      'graph edges and labeled digit thumbnails match actual tree/sample Parts',
      'one HTML card per actual node', 'first root and both child cards fit 1437×789',
      'dialogs closed initially, open/close/Escape and focus return', 'question preview does not train or create hypothetical nodes',
      'Fit tree, zoom, and Current node affect only the view',
      'visible source inspections equal produced Parts', 'drawing uses retained tree and clears stale answers',
      'unfinished prediction does not train', 'reduced-motion Play yields and Pause stops before completion',
      'Play resumes and completes the existing tree',
      'retained training examples predicted correctly', 'held-out examples labeled; separate evaluation is 10/20',
      'export limited to retained frame', 'narrow viewport'],
    fold, viewControls, pause: { ...pauseClick, settledTick: paused.state.nextTick },
    completedTicks: completed.state.nextTick, trainingCorrect: evaluated.training.length,
    heldOutCorrect, heldOutTotal: evaluated.heldOut.length }, null, 2) + '\n');
  console.log(`PASS: ID3 live split and retained frames. Evidence: ${output}`);
} finally { await browser.close(); }
