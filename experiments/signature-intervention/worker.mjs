import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { compareOutputs, withoutReceipt } from './lib.mjs';
import { createExecBoard, invokePql, pxFn, readPql } from '../../src/core/exec.js';

const [mode, variant, inputsPath, contractPath] = process.argv.slice(2);
if (!mode || !variant) throw new Error('worker: mode and variant are required');
const runtimeRoot = ['signature', 'verify-work'].includes(mode) ? resolve(variant).replace('/variants/', '/instrumented/') : resolve(variant);
const { createStudioRuntime } = await import(new URL('./src/runtime.js', `file://${runtimeRoot}/`).href);
const inputs = inputsPath ? JSON.parse(readFileSync(inputsPath, 'utf8')) : null;
const contract = contractPath ? JSON.parse(readFileSync(contractPath, 'utf8')) : {};
const hash = value => createHash('sha256').update(value).digest('hex');
const render = (runtime, spec) => runtime[spec.method](...spec.args);
const median = xs => [...xs].sort((a, b) => a - b)[Math.floor(xs.length / 2)];
const context = { bagId: 'everyday', competitionId: 'putterwarz', roundId: 'hole-1' };

const recordFor = (runtime, spec, result) => {
  const name = spec.method === 'card' ? 'display-card' : 'on-the-course';
  return runtime.runRecord(name);
};

if (mode === 'inputs') {
  // Variants deliberately preserve only their runtime fork. Fixture input is
  // shared, identity-hashed source rather than a second copied renderer tree.
  const { createSeed } = await import(new URL('../../src/seed.js', import.meta.url));
  const world = createSeed();
  const cases = ['broadcast', 'showcase', 'minimal', 'discImage'].map(preset => ({ id: `card-${preset}`, world: structuredClone(world), method: 'card', args: ['buzzz-mint', preset, context] }));
  const optional = structuredClone(cases[0]); optional.id = 'card-photo-optional'; optional.world.objects.Mold.buzzz.flight = {}; optional.world.objects.Disc['buzzz-mint'].photo = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aGJ8AAAAASUVORK5CYII='; cases.push(optional);
  cases.push({ id: 'battle-3', world: structuredClone(world), method: 'scene', args: [context] });
  const large = structuredClone(world); large.battle.entries = Object.keys(large.objects.Disc).map((discId, i) => ({ discId, id: `entry-${i + 1}` })); large.battle.states[0].scores = Object.fromEntries(large.battle.entries.map(e => [e.id, null])); cases.push({ id: 'battle-12', world: large, method: 'scene', args: [context] });
  process.stdout.write(JSON.stringify({ cases, commands: [
    { type: 'preset.set', id: 'broadcast', nodeId: 'maker', patch: { x: 40, size: 17 } },
    { type: 'entity.set', entityType: 'Disc', id: 'buzzz-mint', path: 'nickname', value: 'Changed <once>' },
    { type: 'battle.score', id: 'entry-1', score: 0 }, { type: 'battle.highlight', id: 'entry-1' },
    { type: 'battle.winner', id: 'entry-1' }, { type: 'layout.set', patch: { anchor: 'top-right', arrangement: 'grid' } }
  ].map((command, i) => ({ ...command, eventId: `signature-fixture-${i + 1}`, time: `2026-01-01T00:00:${String(i + 1).padStart(2, '0')}.000Z` })) }));
} else if (mode === 'capture') {
  // Materialize edited worlds once. Both arms consume these exact immutable
  // captures, so dispatch timestamps and generated IDs cannot vary by arm.
  const captures = inputs.cases.map(spec => ({ id: spec.id, method: spec.method, args: spec.args, worlds: [spec.world] }));
  const spec = inputs.cases.find(c => c.id === 'battle-3'), runtime = createStudioRuntime(structuredClone(spec.world));
  const edited = captures.find(c => c.id === spec.id);
  for (const [i, command] of inputs.commands.entries()) { runtime.dispatch(command); edited.worlds.push(runtime.pxc.get('px.studio.world')); edited.worlds[edited.worlds.length - 1] = structuredClone(edited.worlds[edited.worlds.length - 1]); edited[`edit-${i}`] = { eventId: command.eventId, time: command.time, command }; }
  process.stdout.write(JSON.stringify({ version: 1, captures }));
} else if (mode === 'verify' || mode === 'verify-work') {
  const observations = {};
  const signatures = [], observed = mode === 'verify-work';
  for (const capture of inputs.captures) {
    for (const [index, world] of capture.worlds.entries()) {
      const runtime = observed ? createStudioRuntime(structuredClone(world), { signatureObserver: event => signatures.push(event) }) : createStudioRuntime(structuredClone(world));
      const rows = [];
      for (let repeat = 0; repeat < 3; repeat++) { const result = runtime[capture.method](...capture.args); const runRecord = recordFor(runtime, capture, result); rows.push({ id: `${capture.id}/world-${index}/repeat-${repeat + 1}`, inputSha256: hash(JSON.stringify({ world, method: capture.method, args: capture.args })), output: JSON.parse(JSON.stringify(withoutReceipt(result))), svgSha256: hash(result.svg), receipt: result.run, runRecord }); }
      observations[capture.id] ??= []; observations[capture.id].push(...rows);
    }
  }
  process.stdout.write(JSON.stringify({ observations, ...(observed ? { signatureWork: { events: signatures.length, serializations: signatures.filter(event => event.serialized).length, serializedBytes: signatures.reduce((total, event) => total + event.serializedBytes, 0) } } : {}) }));
} else if (mode === 'pql-compare') {
  const board = createExecBoard();
  board.set('px.exp.signature.baseline', inputs.baseline);
  board.set('px.exp.signature.candidate', inputs.candidate);
  board.register(pxFn('fn.exp.signatureIntervention.compare'), ({ baseline, candidate }) => compareOutputs(baseline, candidate));
  const composition = readPql(JSON.stringify({ PrincipleComponentRender: 'signature-intervention-compare', Ticks: [{ name: 'Compare', Calculations: [{ call: 'fn.exp.signatureIntervention.compare', with: { baseline: 'px.exp.signature.baseline', candidate: 'px.exp.signature.candidate' }, into: 'px.exp.signature.comparison' }] }] }), JSON.parse);
  invokePql(composition, { pxc: board });
  process.stdout.write(JSON.stringify({ comparison: board.get('px.exp.signature.comparison'), composition, retained: { baseline: inputs.baseline, candidate: inputs.candidate } }));
} else {
  const keep = (id, result, spec) => ({ id, inputSha256: hash(JSON.stringify({ world: spec.world, method: spec.method, args: spec.args })), output: JSON.parse(JSON.stringify(withoutReceipt(result))), svgSha256: hash(result.svg), receipt: result.run });
  if (mode === 'probe') {
    const outputs = [];
    for (const spec of inputs.cases) { const runtime = createStudioRuntime(structuredClone(spec.world)); outputs.push(keep(`${spec.id}/cold`, render(runtime, spec), spec)); outputs.push(keep(`${spec.id}/warm`, render(runtime, spec), spec)); }
    const spec = inputs.cases.find(c => c.id === 'battle-3'), runtime = createStudioRuntime(structuredClone(spec.world)); render(runtime, spec);
    for (const [i, command] of inputs.commands.entries()) {
      runtime.dispatch(command);
      const edited = { ...spec, world: runtime.pxc.get('px.studio.world') };
      outputs.push(keep(`edit-${i}/${command.type}`, render(runtime, spec), edited));
      outputs.push(keep(`edit-${i}/warm`, render(runtime, spec), edited));
    }
    process.stdout.write(JSON.stringify(outputs));
  } else if (mode === 'measure' || mode === 'signature') {
    const instrument = mode === 'signature', observations = {}, signatures = [];
    const make = world => instrument ? createStudioRuntime(world, { signatureObserver: event => signatures.push(event) }) : createStudioRuntime(world);
    for (const spec of inputs.cases.slice(0, contract.maxCases)) {
      const runtime = make(structuredClone(spec.world)); for (let i = 0; i < contract.warmup; i++) render(runtime, spec);
      const cold = [], warm = [];
      for (let i = 0; i < contract.coldIterations; i++) { const t = performance.now(); const result = render(make(structuredClone(spec.world)), spec); cold.push(performance.now() - t); if (!result.svg) throw new Error('Cold render produced no SVG'); }
      for (let i = 0; i < contract.warmIterations; i++) { const t = performance.now(); render(runtime, spec); warm.push(performance.now() - t); }
      observations[`${spec.id}/cold`] = { samplesMs: cold, medianMs: median(cold) }; observations[`${spec.id}/warm`] = { samplesMs: warm, medianMs: median(warm) };
    }
    const spec = inputs.cases.find(c => c.id === 'battle-3');
    for (const [i, command] of inputs.commands.slice(0, contract.maxEdits).entries()) {
      const dirty = [], warmEdit = [];
      for (let n = 0; n < contract.editIterations; n++) {
        const edited = make(structuredClone(spec.world)); render(edited, spec); edited.dispatch(command);
        let t = performance.now(); render(edited, spec); dirty.push(performance.now() - t);
        t = performance.now(); render(edited, spec); warmEdit.push(performance.now() - t);
      }
      observations[`edit-${i}/${command.type}/dirty`] = { samplesMs: dirty, medianMs: median(dirty) };
      observations[`edit-${i}/${command.type}/warm`] = { samplesMs: warmEdit, medianMs: median(warmEdit) };
    }
    if (instrument) {
      // Keep the certification boundary visible: the first render, immediate
      // repeat, and third repeat are separate sessions so an observer can show
      // exactly when recursive proof becomes reusable.
      const boundary = {};
      for (const spec of inputs.cases.slice(0, contract.maxCases)) {
        const events = []; const observed = createStudioRuntime(structuredClone(spec.world), { signatureObserver: event => events.push(event) });
        const eventSlices = [];
        for (let i = 0; i < 3; i++) { const before = events.length; render(observed, spec); eventSlices.push(events.slice(before)); }
        boundary[spec.id] = { observerEventsPerRepeat: eventSlices.map(slice => slice.length), serializationsPerRepeat: eventSlices.map(slice => slice.filter(event => event.serialized).length) };
      }
      // A cheap 24-slot revisit probe: enough distinct revisions to evict a
      // memo slot, then revisit the original value and retain the receipts.
      const base = inputs.cases.find(c => c.id === 'card-broadcast'), evictionEvents = [];
      const eviction = createStudioRuntime(structuredClone(base.world), { signatureObserver: event => evictionEvents.push(event) });
      render(eviction, base); const original = base.world.objects.Disc['buzzz-mint'].nickname;
      for (let i = 0; i < 25; i++) { eviction.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'buzzz-mint', path: 'nickname', value: `Eviction ${i}` }); render(eviction, base); }
      eviction.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'buzzz-mint', path: 'nickname', value: original });
      const revisit = render(eviction, base);
      boundary.evictionRevisit = { distinctMutations: 25, observerEvents: evictionEvents.length, svgSha256: hash(revisit.svg), receipt: revisit.run };
      process.stdout.write(JSON.stringify({ observations, signatures, boundary }));
    } else process.stdout.write(JSON.stringify(observations));
  } else throw new Error(`Unknown worker mode: ${mode}`);
}
