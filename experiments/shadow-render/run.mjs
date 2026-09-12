#!/usr/bin/env node
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve, join, dirname, relative } from 'node:path';
import { pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';
import { json, writeJson, verifySeal, seal, sha, manifest } from '../card-render/lib.mjs';
import { ShadowSession } from './session.mjs';

const root = resolve(import.meta.dirname, '../..');
const usage = 'node experiments/shadow-render/run.mjs --out NEW_DIRECTORY [--primary SEALED_ATTEMPT] [--reference SEALED_BASELINE] [--sample-every 3] [--reference-timeout-ms 5000] [--burst] [--negative-control]';
const args = process.argv.slice(2), options = {};
if (args.includes('--help')) { console.log(usage); process.exit(0); }
for (let i = 0; i < args.length; i++) {
  const key = args[i];
  if (Object.hasOwn(options, key)) throw new Error(`Duplicate ${key}`);
  if (['--burst', '--negative-control'].includes(key)) options[key] = true;
  else if (['--out', '--primary', '--reference', '--sample-every', '--reference-timeout-ms'].includes(key) && args[i + 1]) options[key] = args[++i];
  else throw new Error(usage);
}
if (!options['--out']) throw new Error(usage);
const out = resolve(options['--out']);
const primaryArtifact = resolve(options['--primary'] ?? join(root, 'evidence/card-render/attempt-02-lazy-signature'));
const referenceArtifact = resolve(options['--reference'] ?? join(root, 'evidence/card-render/baseline-941f354'));
function source(artifact) {
  const artifactDigest = verifySeal(artifact), record = json(join(artifact, 'source.json'));
  return { artifact, artifactDigest, path: join(artifact, 'source'), fingerprint: record.fingerprint, commit: record.commit };
}
const sources = { primary: source(primaryArtifact), reference: source(referenceArtifact) };
const harnessFiles = ['run.mjs', 'model.mjs', 'session.mjs', 'render-worker.mjs', 'worker-peer.mjs', 'task.yaml'];
const sharedFiles = ['src/core/exec.js', 'src/domain.js', 'src/cards.js', 'src/constraints.js', 'src/battle.js', 'src/frames.js', 'experiments/card-render/lib.mjs'];
const harness = () => Object.fromEntries([...harnessFiles.map(name => [name, sha(readFileSync(join(import.meta.dirname, name)))]), ...sharedFiles.map(name => [name, sha(readFileSync(join(root, name)))])]);
const harnessBefore = harness();
const policy = { sampleEvery: Number(options['--sample-every'] ?? 3), referenceTimeoutMs: Number(options['--reference-timeout-ms'] ?? 5000), negativeControlAt: options['--negative-control'] ? 1 : null };
mkdirSync(dirname(out), { recursive: true }); mkdirSync(out); mkdirSync(join(out, 'parts')); mkdirSync(join(out, 'served')); mkdirSync(join(out, 'harness'));
for (const name of harnessFiles) writeFileSync(join(out, 'harness', name), readFileSync(join(import.meta.dirname, name)), { flag: 'wx' });
writeJson(join(out, 'sources.json'), sources);
writeJson(join(out, 'harness.json'), harnessBefore);
writeJson(join(out, 'environment.json'), { node: process.version, executable: process.execPath, os: process.platform, arch: process.arch, sourceCommit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(), status: execFileSync('git', ['status', '--porcelain'], { cwd: root, encoding: 'utf8' }), options });
let session;
const events = [];
try {
  const { cases, commands } = json(join(referenceArtifact, 'inputs.json'));
  const requests = cases.flatMap(spec => [0, 1].map(i => ({ label: `${spec.id}/${i ? 'repeat' : 'first'}`, world: spec.world, method: spec.method, args: spec.args })));
  const { applyCommand } = await import(pathToFileURL(join(sources.reference.path, 'src/domain.js')));
  const battle = cases.find(spec => spec.id === 'battle-3');
  let world = battle.world;
  for (const command of commands) {
    world = applyCommand({ world, command });
    for (const repeat of [false, true]) requests.push({ label: `${command.type}/${repeat ? 'repeat' : 'edit'}`, world, method: battle.method, args: battle.args });
  }
  writeJson(join(out, 'requests.json'), requests);
  session = new ShadowSession({ sources, policy, onPart(address, value) {
    writeJson(join(out, 'parts', `${address}.json`), { address, value });
    if (address.endsWith('.delivery') || address.endsWith('.comparison')) {
      const event = { index: events.length, address, requestId: value.requestId, kind: address.endsWith('.delivery') ? 'delivery' : 'check', status: value.status ?? value.checkAtDelivery, serving: value.serving ?? null };
      events.push(event); console.log(`${event.requestId} ${event.kind}: ${event.status}${event.serving ? ` (${event.serving})` : ''}`);
    }
  } });
  for (const request of requests) {
    const delivered = await session.submit(request);
    if (delivered.delivered) writeFileSync(join(out, 'served', `${delivered.id}.svg`), delivered.value.svg, { flag: 'wx' });
    // Stepwise demo pauses BETWEEN requests to inspect checks. --burst tests the
    // one-in-flight checking budget; neither mode waits before primary delivery.
    if (!options['--burst']) await session.drain();
  }
  await session.drain();
  const summary = session.summary();
  writeJson(join(out, 'events.json'), events);
  writeJson(join(out, 'summary.json'), summary);
  for (const row of summary.rows.filter(row => row.status === 'matched' || row.status === 'mismatch' || row.status === 'unknown')) {
    const delivery = events.find(event => event.requestId === row.id && event.kind === 'delivery');
    const check = events.find(event => event.requestId === row.id && event.kind === 'check');
    if (!delivery || !check || delivery.index >= check.index) throw new Error('Check preceded primary delivery');
  }
  const lines = ['# Fast primary / reference check', '', `Experimental run. Policy: sample every ${session.policy.sampleEvery}; at most one reference check.`, `Negative control: ${!!options['--negative-control']}. Burst: ${!!options['--burst']}.`, '', '| Request | Served by | Eventual status | Difference |', '| --- | --- | --- | --- |', ...summary.rows.map(row => `| ${row.id}: ${row.label} | ${row.serving} | ${row.status} | ${row.differingKeys.join(', ')} |`), '', 'Delivery happens before any sampled check completes. A later mismatch cannot retract the already-served result.', `Final routing: ${summary.routing.serving} (${summary.routing.reason}).`, '', 'Inspect summary.json, events.json, served/*.svg and the addressed parts/ files, including both execution receipts.', 'Reference is a fresh baseline runtime, not an exhaustive oracle. Pixels are not checked. No acceptance or promotion.', '', 'Human review: is this sampling cost and session-local fallback behavior useful for preview work? Which boundary needs changing?'];
  writeFileSync(join(out, 'REPORT.md'), lines.join('\n') + '\n', { flag: 'wx' });
  writeJson(join(out, 'review.json'), { subject: sha(JSON.stringify(manifest(out))), prompt: 'Review this exact run: primary delivery, check coverage, disagreement and later routing. What should we keep or change?', response: null, acceptance: null, promotion: null });
  if (summary.needsReview) process.exitCode = 2; // Evidence produced, but not a clean check.
  console.log(JSON.stringify({ counts: summary.counts, routing: summary.routing, evidence: relative(root, out) }));
} catch (error) {
  writeJson(join(out, 'failure.json'), { message: error.message, stack: error.stack, acceptance: null }); process.exitCode = 1; console.error(error.message);
} finally {
  try { await session?.close(); } catch (error) { writeJson(join(out, 'close-failure.json'), { message: error.message }); process.exitCode = 1; }
  try {
    if (verifySeal(primaryArtifact) !== sources.primary.artifactDigest || verifySeal(referenceArtifact) !== sources.reference.artifactDigest || JSON.stringify(harness()) !== JSON.stringify(harnessBefore)) throw new Error('Source or harness changed during run');
  } catch (error) { writeJson(join(out, 'identity-failure.json'), { message: error.message }); process.exitCode = 1; }
  seal(out);
}
