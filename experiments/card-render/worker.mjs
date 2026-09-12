import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';

const [mode, source, inputsPath, contractPath] = process.argv.slice(2);
const { createStudioRuntime } = await import(pathToFileURL(resolve(source, 'src/runtime.js')));
const hash = value => createHash('sha256').update(value).digest('hex');
const context = { bagId: 'everyday', competitionId: 'putterwarz', roundId: 'hole-1' };
const median = xs => [...xs].sort((a, b) => a - b)[Math.floor(xs.length / 2)];

if (mode === 'inputs') {
  const { createSeed } = await import(pathToFileURL(resolve(source, 'src/seed.js')));
  const world = createSeed();
  const cases = ['broadcast', 'showcase', 'minimal', 'discImage'].map(preset => ({
    id: `card-${preset}`, world: structuredClone(world), method: 'card', args: ['buzzz-mint', preset, context]
  }));
  const optional = structuredClone(cases[0]); optional.id = 'card-photo-optional';
  optional.world.objects.Mold.buzzz.flight = {};
  optional.world.objects.Disc['buzzz-mint'].photo = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aGJ8AAAAASUVORK5CYII=';
  cases.push(optional);
  cases.push({ id: 'battle-3', world: structuredClone(world), method: 'scene', args: [context] });
  const large = structuredClone(world);
  large.battle.entries = Object.keys(large.objects.Disc).map((discId, i) => ({ discId, id: `entry-${i + 1}` }));
  large.battle.states[0].scores = Object.fromEntries(large.battle.entries.map(e => [e.id, null]));
  cases.push({ id: 'battle-12', world: large, method: 'scene', args: [context] });
  process.stdout.write(JSON.stringify({ cases, commands: [
    { type: 'preset.set', id: 'broadcast', nodeId: 'maker', patch: { x: 40, size: 17 } },
    { type: 'entity.set', entityType: 'Disc', id: 'buzzz-mint', path: 'nickname', value: 'Changed <once>' },
    { type: 'battle.score', id: 'entry-1', score: 0 },
    { type: 'battle.highlight', id: 'entry-1' },
    { type: 'battle.winner', id: 'entry-1' },
    { type: 'layout.set', patch: { anchor: 'top-right', arrangement: 'grid' } }
  ] }));
} else {
  const inputs = JSON.parse(readFileSync(inputsPath, 'utf8'));
  const contract = JSON.parse(readFileSync(contractPath, 'utf8'));
  const render = (runtime, spec) => runtime[spec.method](...spec.args);
  if (mode === 'probe') {
    const outputs = [];
    const keep = (id, result) => outputs.push({ id, svg: result.svg, svgSha256: hash(result.svg), resultSha256: hash(JSON.stringify(result)), computed: result.run.computed, reused: result.run.reused });
    for (const spec of inputs.cases) {
      const runtime = createStudioRuntime(structuredClone(spec.world));
      keep(`${spec.id}/cold`, render(runtime, spec));
      keep(`${spec.id}/warm`, render(runtime, spec));
    }
    const spec = inputs.cases.find(c => c.id === 'battle-3');
    const runtime = createStudioRuntime(structuredClone(spec.world));
    render(runtime, spec);
    for (const [i, command] of inputs.commands.entries()) {
      runtime.dispatch(command);
      keep(`edit-${i}/${command.type}`, render(runtime, spec));
      keep(`edit-${i}/warm`, render(runtime, spec));
    }
    process.stdout.write(JSON.stringify(outputs));
  } else if (mode === 'measure') {
    const observations = {};
    for (const spec of inputs.cases) {
      const runtime = createStudioRuntime(structuredClone(spec.world));
      for (let i = 0; i < contract.warmup; i++) render(runtime, spec);
      const cold = [], warm = [];
      for (let i = 0; i < contract.coldIterations; i++) {
        const world = structuredClone(spec.world);
        const start = performance.now();
        const result = render(createStudioRuntime(world), spec);
        cold.push(performance.now() - start);
        if (!result.svg || result.run.computed === 0) throw new Error('Cold workload did not compute');
      }
      for (let i = 0; i < contract.warmIterations; i++) {
        const start = performance.now();
        const result = render(runtime, spec);
        warm.push(performance.now() - start);
        if (!result.svg || result.run.computed !== 0) throw new Error('Warm workload did not reuse');
      }
      observations[`${spec.id}/cold`] = { samplesMs: cold, medianMs: median(cold) };
      observations[`${spec.id}/warm`] = { samplesMs: warm, medianMs: median(warm) };
    }
    process.stdout.write(JSON.stringify(observations));
  } else throw new Error(`Unknown worker mode: ${mode}`);
}
