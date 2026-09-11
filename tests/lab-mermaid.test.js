/** The Mermaid path, ported: a .mmd compiles to the document the LAB's YAML holds. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { SOURCE } from '../src/lab/source.js';
import { parseYaml } from '../src/lab/yaml.js';
import { labDocument, labAddress } from '../src/lab/address.js';
import { compileMermaidPcr, lowerToPql, structuralDigest, withoutCalls } from '../src/lab/mermaid.js';
import { createLab } from '../src/lab/lab.js';
import { registerS0, s0Document, compiledS0 } from '../src/lab/s0.js';

const read = name => readFileSync(join(SOURCE, name), 'utf8');
const compile = stage => lowerToPql(compileMermaidPcr(read(`${stage}.mmd`), JSON.parse(read(`${stage}.args.json`))));

test('the studio yaml reader reads the LAB Stage documents it was written for', () => {
  const s1 = parseYaml(read('S1.pcr.yaml'));
  assert.equal(s1.PrincipleComponentRender, 'S1');
  assert.deepEqual(s1.Ticks.map(tick => `${tick.name}:${tick.Calculations.length}`), ['BlackMask:2', 'WhiteMask:2', 'BadgeAssembly:5', 'WhiteDigitRecognition:2', 'BadgeOutputs:4']);
  assert.equal(parseYaml(read('S0.pcr.yaml')).output.px, 'px.course.canonicalPixels');
  assert.equal(parseYaml(read('S0.stage.yaml')).stage, 'S0');
});

test('S1.mmd compiles to the same document as the LAB S1 PrincipleComponentRender.yaml', () => {
  const compiled = compile('S1');
  // The LAB's own proof drops the one Calculation the YAML path seeds instead of
  // computing (proof.ts: generatedCalls filters fn.s0.asMaskRaster).
  const generated = labDocument(withoutCalls(compiled.document, ['fn.s0.asMaskRaster']));
  const baseline = labDocument(parseYaml(read('S1.pcr.yaml')));
  assert.equal(structuralDigest(generated), structuralDigest(baseline));
  assert.deepEqual(generated.Ticks.map(tick => tick.name), baseline.Ticks.map(tick => tick.name));
  const calls = tick => tick.Calculations.map(calculation => `${calculation.call} -> ${calculation.into}`);
  assert.deepEqual(generated.Ticks.flatMap(calls), baseline.Ticks.flatMap(calls));
});

test('every binding and argument of all 13 shared S1 Calculations agrees with the YAML', () => {
  const generated = labDocument(withoutCalls(compile('S1').document, ['fn.s0.asMaskRaster'])).Ticks.flatMap(tick => tick.Calculations);
  const baseline = labDocument(parseYaml(read('S1.pcr.yaml'))).Ticks.flatMap(tick => tick.Calculations);
  assert.equal(generated.length, baseline.length);
  generated.forEach((calculation, index) => {
    assert.deepEqual(calculation.with, baseline[index].with, `bindings of ${calculation.call}`);
    assert.deepEqual(calculation.args, baseline[index].args, `args of ${calculation.call}`);
  });
});

test('S0.mmd binds a result with no Part, and lowering is what gives it an address', () => {
  const { compiled, local, document } = compiledS0();
  assert.equal(compiled.Ticks[0].Calculations[0].id, 'decode');
  assert.equal(compiled.Ticks[0].Calculations[0].into, undefined);
  assert.deepEqual(compiled.Ticks[1].Calculations[0].with, { image: { kind: 'fn', ref: 'decode' } });
  assert.deepEqual(local.map(entry => entry.id), ['decode']);
  assert.equal(document.Ticks[0].Calculations[0].into, labAddress(local[0].address));
  // The LAB's parity check is that FullImage is never published: here it is,
  // under a local address, because the studio's grammar has no other way.
  assert.ok(!document.Ticks.flatMap(tick => tick.Calculations).some(calculation => calculation.into === 'px.exp.lab.source.fullimage'));
});

test('the S0 document that runs is the compiled graph plus the cache Tick S0.pcr.yaml names last', () => {
  const lab = createLab(); registerS0(lab);
  const running = s0Document(lab);
  assert.equal(structuralDigest(withoutCalls(running, ['fn.lab.s0.cachefullimage'])), structuralDigest(compiledS0().document));
  assert.equal(parseYaml(read('S0.pcr.yaml')).last.cache, 'FullImage');
});

test('the compiler refuses what the LAB compiler refuses', () => {
  const graph = read('S0.mmd');
  assert.throws(() => compileMermaidPcr(graph.replace('flowchart TD', 'flowchart LR'), {}), /only `flowchart TD`/);
  assert.throws(() => compileMermaidPcr(graph, { nosuch: {} }), /unknown argument occurrence/);
  assert.throws(() => compileMermaidPcr(graph.replace('decode -->|image| bounds', 'crop -->|image| bounds'), {}), /forward dependency or cycle/);
  assert.throws(() => compileMermaidPcr(graph.replace('source -->|source| decode', 'source --> decode'), {}), /needs a named binding/);
});
