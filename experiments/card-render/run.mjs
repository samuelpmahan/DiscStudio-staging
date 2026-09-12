#!/usr/bin/env node
import { readFileSync, writeFileSync, mkdirSync, copyFileSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';
import { platform, arch, release, cpus } from 'node:os';
import { sha, json, writeJson, snapshot, manifest, seal, verifySeal, parity, compare } from './lib.mjs';

const here = import.meta.dirname;
const usage = `Card render experiment (Node 22+, no installation):
  node experiments/card-render/run.mjs capture --source . --out evidence/card-render/baseline
  node experiments/card-render/run.mjs profile --baseline evidence/card-render/baseline --out evidence/card-render/profile
  node experiments/card-render/run.mjs compare --baseline evidence/card-render/baseline --source . --out evidence/card-render/attempt-01 --hypothesis "one change and why"
  node experiments/card-render/run.mjs verify --baseline evidence/card-render/baseline

Outputs must not exist. Timings are Node runtime+SVG generation, not browser paint.
Use pixels.mjs for the optional same-browser image comparison.`;
const [command, ...args] = process.argv.slice(2);
if (!command || command === '--help') { console.log(usage); process.exit(0); }
const opts = {};
for (let i = 0; i < args.length; i += 2) {
  if (!['--source', '--out', '--baseline', '--hypothesis'].includes(args[i]) || !args[i + 1] || Object.hasOwn(opts, args[i])) throw new Error(usage);
  opts[args[i]] = args[i + 1];
}
const required = key => { if (!opts[key]) throw new Error(`Missing ${key}\n${usage}`); return opts[key]; };
const source = resolve(opts['--source'] ?? join(here, '../..'));
const baseline = opts['--baseline'] && resolve(opts['--baseline']);
const harness = () => Object.fromEntries(['run.mjs', 'worker.mjs', 'lib.mjs', 'contract.json', 'pixels.mjs'].map(name => [name, sha(readFileSync(join(here, name)))]));
const worker = (mode, root, input, contract, extra = []) => JSON.parse(execFileSync(process.execPath, [...extra, join(here, 'worker.mjs'), mode, root, input, contract], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, timeout: 60000 }));
const checkBaseline = () => {
  required('--baseline'); const digest = verifySeal(baseline);
  if (JSON.stringify(json(join(baseline, 'harness.json'))) !== JSON.stringify(harness())) throw new Error('Harness changed: start a new baseline, do not edit the old one');
  return digest;
};
if (command === 'verify') { console.log(`Verified frozen baseline: ${checkBaseline()}`); process.exit(0); }
if (!['capture', 'compare', 'profile'].includes(command)) throw new Error(usage);
if (command === 'compare') required('--hypothesis');
if (command !== 'capture') checkBaseline();
const out = resolve(required('--out'));
mkdirSync(dirname(out), { recursive: true });
mkdirSync(out); // EEXIST is intentional: neither a baseline nor an attempt is overwritten.
const env = { node: process.version, executable: process.execPath, os: platform(), release: release(), arch: arch(), cpu: cpus()[0]?.model, logicalCpus: cpus().length };
const harnessStart = harness();
writeJson(join(out, 'environment.json'), env);
writeJson(join(out, 'harness.json'), harnessStart);
try {
  if (command === 'capture') {
    const provenance = snapshot(source, join(out, 'source'));
    writeJson(join(out, 'source.json'), provenance);
    copyFileSync(join(here, 'contract.json'), join(out, 'contract.json'));
    writeJson(join(out, 'inputs.json'), worker('inputs', join(out, 'source'), '', ''));
    const reference = worker('probe', join(out, 'source'), join(out, 'inputs.json'), join(out, 'contract.json'));
    writeJson(join(out, 'reference.json'), reference);
    if (!parity(reference, worker('probe', join(out, 'source'), join(out, 'inputs.json'), join(out, 'contract.json'))).pass) throw new Error('Baseline is not reproducible');
    writeJson(join(out, 'measurement.json'), worker('measure', join(out, 'source'), join(out, 'inputs.json'), join(out, 'contract.json')));
    console.log(`Captured ${reference.length} outputs at ${provenance.commit}; source ${provenance.fingerprint}`);
  } else if (command === 'profile') {
    writeJson(join(out, 'baseline.json'), { path: baseline, digest: checkBaseline() });
    writeJson(join(out, 'measurement.json'), worker('measure', join(baseline, 'source'), join(baseline, 'inputs.json'), join(baseline, 'contract.json'), ['--cpu-prof', `--cpu-prof-dir=${out}`, '--cpu-prof-name=baseline.cpuprofile']));
    const profile = json(join(out, 'baseline.cpuprofile')), counts = new Map();
    profile.samples.forEach((id, i) => counts.set(id, (counts.get(id) ?? 0) + profile.timeDeltas[i]));
    const hotspots = profile.nodes.map(n => ({ function: n.callFrame.functionName || '(anonymous)', url: n.callFrame.url, line: n.callFrame.lineNumber + 1, selfMs: (counts.get(n.id) ?? 0) / 1000 })).sort((a, b) => b.selfMs - a.selfMs).slice(0, 25);
    writeJson(join(out, 'hotspots.json'), hotspots);
    console.log(hotspots.slice(0, 8));
  } else {
    const baselineDigest = checkBaseline(), contract = json(join(baseline, 'contract.json'));
    if (JSON.stringify(env) !== JSON.stringify(json(join(baseline, 'environment.json')))) throw new Error('Runtime environment changed: capture a new baseline');
    const provenance = snapshot(source, join(out, 'source'));
    writeJson(join(out, 'source.json'), provenance);
    writeFileSync(join(out, 'candidate.patch'), provenance.patch, { flag: 'wx' });
    writeJson(join(out, 'baseline.json'), { path: baseline, digest: baselineDigest });
    writeJson(join(out, 'hypothesis.json'), { text: opts['--hypothesis'], recordedAt: new Date().toISOString() });
    const input = join(baseline, 'inputs.json'), contractPath = join(baseline, 'contract.json');
    const reference = json(join(baseline, 'reference.json'));
    if (!parity(reference, worker('probe', join(baseline, 'source'), input, contractPath)).pass) throw new Error('Baseline no longer reproduces its outputs');
    const candidate = worker('probe', join(out, 'source'), input, contractPath);
    writeJson(join(out, 'candidate.json'), candidate);
    const rounds = [];
    for (let i = 0; i < contract.rounds; i++) {
      const row = { order: i % 2 ? ['candidate', 'baseline'] : ['baseline', 'candidate'] };
      for (const side of row.order) row[side] = worker('measure', join(side === 'baseline' ? baseline : out, 'source'), input, contractPath);
      rounds.push(row); writeJson(join(out, `round-${i + 1}.json`), row);
      console.log(`paired round ${i + 1}/${contract.rounds}`);
    }
    const { createExecBoard, pxFn, readPql, invokePql } = await import(pathToFileURL(join(baseline, 'source/src/core/exec.js')));
    const pxc = createExecBoard(), prefix = `px.exp.cardRender.r${sha(JSON.stringify({ baselineDigest, provenance: provenance.fingerprint, rounds })).slice(0, 20)}`;
    for (const [name, value] of Object.entries({ reference, candidate, rounds, contract, inputs: json(input), source: provenance })) pxc.set(`${prefix}.${name}`, value);
    pxc.register(pxFn('fn.exp.cardRender.compare'), compare);
    const composition = readPql(JSON.stringify({ PrincipleComponentRender: 'card-render-experiment', Ticks: [{ name: 'Compare', Calculations: [{ call: 'fn.exp.cardRender.compare', with: Object.fromEntries(['reference', 'candidate', 'rounds', 'contract'].map(key => [key, `${prefix}.${key}`])), into: `${prefix}.comparison` }] }] }), JSON.parse);
    invokePql(composition, { pxc });
    const result = pxc.get(`${prefix}.comparison`);
    writeJson(join(out, 'comparison.json'), result);
    writeJson(join(out, 'composition.json'), composition);
    writeJson(join(out, 'parts.json'), Object.fromEntries(pxc.keys().map(address => [address, pxc.get(address)])));
    // This is review material, not an authentication or acceptance mechanism.
    writeJson(join(out, 'review.json'), {
      subject: sha(JSON.stringify(manifest(out))), baseline: baselineDigest, candidate: provenance.fingerprint,
      prompt: `Candidate: ${opts['--hypothesis']}\nAutomated result: ${result.verdict}. Review candidate.patch, comparison.json and the retained source/inputs before deciding whether this exact change should be promoted. What do you want to keep, change or reject?`,
      response: null, acceptance: null, promotion: null,
      limitation: 'SVG/result equivalence is not browser pixels or CV accuracy. No browser-paint latency is measured.'
    });
    console.log(JSON.stringify({ verdict: result.verdict, primary: result.metrics[result.primary], equivalence: result.equivalence, regressions: result.regressions }, null, 2));
  }
  if (JSON.stringify(harnessStart) !== JSON.stringify(harness())) throw new Error('Harness changed during run');
  if (baseline) checkBaseline();
  seal(out);
  console.log(`Evidence retained: ${out}`);
} catch (error) {
  writeJson(join(out, 'failure.json'), { message: error.message, stack: error.stack, acceptance: null });
  seal(out);
  console.error(`Attempt failed; evidence retained at ${out}\n${error.message}`);
  process.exitCode = 1;
}
