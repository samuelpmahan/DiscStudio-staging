#!/usr/bin/env node
import { execFileSync } from 'node:child_process';
import { cpus, platform, arch, release } from 'node:os';
import { copyFileSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { compareOutputs, ensureDir, json, median, seal, sha, sharedSourceIdentity, sourceIdentity, timingMedian, verifySeal, writeJson } from './lib.mjs';

const here = import.meta.dirname;
const usage = `Signature intervention harness (Node 22+, opt-in):
  node experiments/signature-intervention/run.mjs compare --baseline variants/eager --candidate variants/lazy --out evidence/signature-intervention/run-01
  node experiments/signature-intervention/run.mjs verify --out evidence/signature-intervention/run-01
  node experiments/signature-intervention/run.mjs deterministic-verify --baseline variants/eager --candidate variants/lazy --out evidence/signature-intervention/verification-01

Every output directory must be new. The default budget is deliberately small; inspect raw paired rounds before drawing conclusions.`;
const [command, ...argv] = process.argv.slice(2), opts = {};
for (let i = 0; i < argv.length; i += 2) { if (!['--baseline', '--candidate', '--out'].includes(argv[i]) || !argv[i + 1] || opts[argv[i]]) throw new Error(usage); opts[argv[i]] = argv[i + 1]; }
if (!command || command === '--help') { console.log(usage); process.exit(0); }
const out = resolve(opts['--out'] ?? '');
if (command === 'verify') { console.log(`Verified sealed output: ${verifySeal(out)}`); process.exit(0); }
if (!['compare', 'deterministic-verify'].includes(command) || !opts['--baseline'] || !opts['--candidate'] || !opts['--out']) throw new Error(usage);
const baseline = resolve(opts['--baseline']), candidate = resolve(opts['--candidate']); ensureDir(dirname(out)); mkdirSync(out);
const contract = json(join(here, 'contract.json'));
const env = { node: process.version, executable: process.execPath, os: platform(), release: release(), arch: arch(), cpu: cpus()[0]?.model, logicalCpus: cpus().length };
const worker = (mode, variant, input = '', contractPath = '') => JSON.parse(execFileSync(process.execPath, [join(here, 'worker.mjs'), mode, variant, input, contractPath], { encoding: 'utf8', maxBuffer: 128 * 1024 * 1024, timeout: 120000 }));
writeJson(join(out, 'environment.json'), env); writeJson(join(out, 'contract.json'), contract);
writeJson(join(out, 'harness.json'), Object.fromEntries(['run.mjs', 'worker.mjs', 'lib.mjs', 'contract.json'].map(name => [name, sha(readFileSync(join(here, name)))])));
const instrumented = root => resolve(root).replace('/variants/', '/instrumented/');
const startIdentity = { baseline: sourceIdentity(baseline), candidate: sourceIdentity(candidate), instrumentedBaseline: sourceIdentity(instrumented(baseline)), instrumentedCandidate: sourceIdentity(instrumented(candidate)), sharedDependencies: sharedSourceIdentity(resolve(here, '../..')) };
writeJson(join(out, 'source.json'), startIdentity);
for (const [name, root] of Object.entries({ baseline, candidate, instrumentedBaseline: instrumented(baseline), instrumentedCandidate: instrumented(candidate) })) {
  const target = join(out, 'sources', name, 'src'); mkdirSync(target, { recursive: true });
  copyFileSync(join(root, 'src/runtime.js'), join(target, 'runtime.js'));
}
for (const name of ['run.mjs', 'worker.mjs', 'lib.mjs', 'contract.json']) {
  const target = join(out, 'harness-source'); mkdirSync(target, { recursive: true });
  copyFileSync(join(here, name), join(target, name));
}
const inputFile = join(out, 'inputs.json'); writeJson(inputFile, worker('inputs', baseline));
if (command === 'deterministic-verify') {
  const capturesFile = join(out, 'captures.json'); writeJson(capturesFile, worker('capture', baseline, inputFile, join(out, 'contract.json')));
  const baselineVerification = worker('verify', baseline, capturesFile, join(out, 'contract.json'));
  const candidateVerification = worker('verify', candidate, capturesFile, join(out, 'contract.json'));
  const baselineWork = worker('verify-work', baseline, capturesFile, join(out, 'contract.json'));
  const candidateWork = worker('verify-work', candidate, capturesFile, join(out, 'contract.json'));
  writeJson(join(out, 'baseline-verification.json'), baselineVerification);
  writeJson(join(out, 'candidate-verification.json'), candidateVerification);
  writeJson(join(out, 'baseline-work.json'), baselineWork);
  writeJson(join(out, 'candidate-work.json'), candidateWork);
  // Receipts stay in their arm files; PQL sees exactly the comparable visible
  // value projection, avoiding recursive receipt payloads in its own memo key.
  const flatten = value => Object.values(value.observations).flat().map(({ id, inputSha256, output, svgSha256 }) => ({ id, inputSha256, output, svgSha256 }));
  writeJson(join(out, 'instrumentation-neutrality.json'), { baseline: compareOutputs(flatten(baselineVerification), flatten(baselineWork)), candidate: compareOutputs(flatten(candidateVerification), flatten(candidateWork)) });
  const pqlInput = join(out, 'pql-input.json'); writeJson(pqlInput, { baseline: flatten(baselineVerification), candidate: flatten(candidateVerification) });
  const comparison = worker('pql-compare', baseline, pqlInput, join(out, 'contract.json'));
  writeJson(join(out, 'pql-comparison.json'), comparison);
  const endIdentity = { baseline: sourceIdentity(baseline), candidate: sourceIdentity(candidate), instrumentedBaseline: sourceIdentity(instrumented(baseline)), instrumentedCandidate: sourceIdentity(instrumented(candidate)), sharedDependencies: sharedSourceIdentity(resolve(here, '../..')) };
  if (JSON.stringify(startIdentity) !== JSON.stringify(endIdentity)) throw new Error('Source changed during deterministic verification');
  if (JSON.stringify(json(join(out, 'harness.json'))) !== JSON.stringify(Object.fromEntries(['run.mjs', 'worker.mjs', 'lib.mjs', 'contract.json'].map(name => [name, sha(readFileSync(join(here, name)))])))) throw new Error('Harness changed during deterministic verification');
  writeJson(join(out, 'review.json'), { subject: sha(JSON.stringify({ source: endIdentity, comparison })), prompt: 'Review the single captured edited worlds, each arm’s runRecord receipts, and the existing-PQL comparison. This is deterministic verification/work counting, not a latency measurement or promotion.', response: null, acceptance: null });
  seal(out); console.log(JSON.stringify({ output: out, comparison: comparison.comparison }, null, 2)); process.exit(0);
}
const reference = worker('probe', baseline, inputFile, join(out, 'contract.json')), actual = worker('probe', candidate, inputFile, join(out, 'contract.json'));
writeJson(join(out, 'baseline-equivalence.json'), reference); writeJson(join(out, 'candidate-equivalence.json'), actual); writeJson(join(out, 'equivalence.json'), compareOutputs(reference, actual));
const rounds = [];
for (let i = 0; i < contract.rounds; i++) {
  const order = i % 2 ? ['candidate', 'baseline'] : ['baseline', 'candidate'], row = { round: i + 1, order };
  for (const side of order) row[side] = worker('measure', side === 'baseline' ? baseline : candidate, inputFile, join(out, 'contract.json'));
  rounds.push(row); writeJson(join(out, `round-${i + 1}.json`), row); console.log(`paired round ${i + 1}/${contract.rounds}`);
}
writeJson(join(out, 'rounds.json'), rounds);
const keys = Object.keys(rounds[0].baseline).sort(), metrics = {};
for (const key of keys) {
  const base = rounds.map(r => r.baseline[key].medianMs), next = rounds.map(r => r.candidate[key].medianMs);
  const improvements = base.map((value, i) => value === 0 ? null : 1 - next[i] / value);
  metrics[key] = { baselineMs: timingMedian(base), candidateMs: timingMedian(next), improvement: improvements.every(Number.isFinite) ? median(improvements) : null, pairedImprovements: improvements, regressions: improvements.filter(x => Number.isFinite(x) && x < 0).length };
}
writeJson(join(out, 'metrics.json'), metrics);
const signatureWork = { baseline: worker('signature', baseline, inputFile, join(out, 'contract.json')), candidate: worker('signature', candidate, inputFile, join(out, 'contract.json')) };
writeJson(join(out, 'signature-work.json'), signatureWork);
const endIdentity = { baseline: sourceIdentity(baseline), candidate: sourceIdentity(candidate), instrumentedBaseline: sourceIdentity(instrumented(baseline)), instrumentedCandidate: sourceIdentity(instrumented(candidate)), sharedDependencies: sharedSourceIdentity(resolve(here, '../..')) };
if (JSON.stringify(startIdentity) !== JSON.stringify(endIdentity)) throw new Error('Source changed during run');
if (JSON.stringify(json(join(out, 'harness.json'))) !== JSON.stringify(Object.fromEntries(['run.mjs', 'worker.mjs', 'lib.mjs', 'contract.json'].map(name => [name, sha(readFileSync(join(here, name)))])))) throw new Error('Harness changed during run');
writeJson(join(out, 'review.json'), { subject: sha(JSON.stringify({ env, contract, source: endIdentity, metrics })), prompt: 'Review exact equivalence, retained receipts, per-workload paired rounds, and separate signature-work observations. This harness does not accept or promote a variant.', response: null, acceptance: null });
seal(out);
console.log(JSON.stringify({ output: out, equivalence: compareOutputs(reference, actual), metrics }, null, 2));
