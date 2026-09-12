import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { manifest, median, parity, compare, seal, snapshot, verifySeal, sha } from '../experiments/card-render/lib.mjs';

const repo = join(dirname(fileURLToPath(import.meta.url)), '..');
const contract = {
  rounds: 7,
  primary: 'card-broadcast/warm',
  minimumImprovement: 0.05,
  minimumWinningRounds: 6,
  maximumRegression: 0.1
};

function observation(id, svg = `<svg>${id}</svg>`, result = { id }) {
  return { id, svg, svgSha256: sha(svg), resultSha256: sha(JSON.stringify(result)) };
}

function rounds(values, extra = {}) {
  const candidates = Array.isArray(values) && values.length === contract.rounds ? values : Array(contract.rounds).fill(values[0] ?? values);
  return Array.from({ length: contract.rounds }, (_, i) => ({
    baseline: { 'card-broadcast/warm': { samplesMs: [10, 10, 10], medianMs: 10 }, ...extra.baseline },
    candidate: { 'card-broadcast/warm': { samplesMs: [candidates[i], candidates[i], candidates[i]], medianMs: candidates[i] }, ...extra.candidate },
    order: i % 2 ? ['candidate', 'baseline'] : ['baseline', 'candidate']
  }));
}

function tempDir(prefix) { return mkdtempSync(join(tmpdir(), `card-experiment-${prefix}-`)); }

test('median accepts unsorted finite samples and rejects invalid samples', () => {
  assert.equal(median([9, 1, 5]), 5);
  assert.equal(median([8, 2, 4, 6]), 5);
  assert.throws(() => median([]), /Invalid measurement samples/);
  assert.throws(() => median([1, Number.NaN]), /Invalid measurement samples/);
});

test('parity rejects changed SVG, SVG hash, result hash, missing and duplicate cases', () => {
  const base = [observation('one'), observation('two')];
  assert.equal(parity(base, base).pass, true);
  assert.equal(parity(base, [observation('one', '<svg>changed</svg>'), base[1]]).pass, false);
  assert.equal(parity(base, [{ ...base[0], svgSha256: 'wrong' }, base[1]]).pass, false);
  assert.equal(parity(base, [{ ...base[0], resultSha256: 'wrong' }, base[1]]).pass, false);
  assert.equal(parity(base, [base[0]]).pass, false);
  assert.equal(parity(base, [base[0], { ...base[1], id: 'one' }]).pass, false);
});

test('compare requires exactly seven complete paired rounds', () => {
  const equivalent = [observation('one')];
  assert.throws(() => compare({ reference: equivalent, candidate: equivalent, rounds: rounds([8]).slice(0, 6), contract }), /Incomplete paired rounds/);
  const incomplete = rounds([8]);
  delete incomplete[3].candidate;
  assert.throws(() => compare({ reference: equivalent, candidate: equivalent, rounds: incomplete, contract }), /Workload metrics differ|Cannot read properties|Cannot convert undefined|Invalid timing evidence/);
});

test('identical and noisy timings remain inconclusive', () => {
  const equivalent = [observation('one')];
  const identical = compare({ reference: equivalent, candidate: equivalent, rounds: rounds([10]), contract });
  assert.equal(identical.verdict, 'inconclusive');
  const noisy = compare({ reference: equivalent, candidate: equivalent, rounds: rounds([9.6]), contract });
  assert.equal(noisy.verdict, 'inconclusive');
  assert.equal(noisy.acceptance, null);
  assert.equal(noisy.promotion, null);
});

test('clear primary improvement is promising but remains unaccepted', () => {
  const equivalent = [observation('one')];
  const result = compare({ reference: equivalent, candidate: equivalent, rounds: rounds([8]), contract });
  assert.equal(result.verdict, 'promising-needs-review');
  assert.equal(result.primary, contract.primary);
  assert.equal(result.metrics[contract.primary].wins, 7);
  assert.equal(result.acceptance, null);
  assert.equal(result.promotion, null);
});

test('a regression in any measured workload rejects the candidate', () => {
  const equivalent = [observation('one')];
  const result = compare({
    reference: equivalent,
    candidate: equivalent,
    rounds: rounds([8], {
      baseline: { layout: { samplesMs: [10, 10, 10], medianMs: 10 } },
      candidate: { layout: { samplesMs: [12, 12, 12], medianMs: 12 } }
    }),
    contract
  });
  assert.equal(result.verdict, 'rejected-regression');
  assert.deepEqual(result.regressions, ['layout']);
});

test('seal detects modified, deleted, and extra evidence files', () => {
  const root = tempDir('seal');
  try {
    writeFileSync(join(root, 'evidence.json'), '{"ok":true}\n');
    seal(root);
    assert.doesNotThrow(() => verifySeal(root));
    writeFileSync(join(root, 'evidence.json'), 'changed\n');
    assert.throws(() => verifySeal(root), /Frozen evidence changed/);
    writeFileSync(join(root, 'evidence.json'), '{"ok":true}\n');
    rmSync(join(root, 'manifest.json'));
    assert.throws(() => verifySeal(root), /ENOENT/);
    writeFileSync(join(root, 'evidence.json'), '{"ok":true}\n');
    seal(root);
    writeFileSync(join(root, 'extra.txt'), 'unexpected\n');
    assert.throws(() => verifySeal(root), /Frozen evidence changed/);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test('capture refuses to reuse an existing output directory', () => {
  const out = tempDir('existing');
  try {
    const result = (() => {
      try {
        execFileSync(process.execPath, [join(repo, 'experiments/card-render/run.mjs'), 'capture', '--source', repo, '--out', out], { encoding: 'utf8', stdio: 'pipe' });
        return null;
      } catch (error) { return error; }
    })();
    assert.ok(result, 'capture unexpectedly reused an existing directory');
    assert.match(`${result.stderr}${result.stdout}`, /EEXIST/);
  } finally { rmSync(out, { recursive: true, force: true }); }
});

test('snapshot retains exact selected source data and git identity', () => {
  const fixture = tempDir('fixture');
  const destination = tempDir('snapshot');
  try {
    writeFileSync(join(fixture, 'package.json'), readFileSync(join(repo, 'package.json')));
    for (const path of ['src', 'pyto/viewer', 'pyto/consumers/discstudio-card/port/painter']) {
      cpSync(join(repo, path), join(fixture, path), { recursive: true });
    }
    execFileSync('git', ['init', '-q'], { cwd: fixture });
    execFileSync('git', ['config', 'user.email', 'test@example.invalid'], { cwd: fixture });
    execFileSync('git', ['config', 'user.name', 'Card Experiment Test'], { cwd: fixture });
    execFileSync('git', ['add', '.'], { cwd: fixture });
    execFileSync('git', ['commit', '-qm', 'fixture'], { cwd: fixture });
    const target = join(destination, 'source');
    const provenance = snapshot(fixture, target);
    assert.match(provenance.commit, /^[0-9a-f]{40}$/);
    assert.equal(provenance.commit, execFileSync('git', ['rev-parse', 'HEAD'], { cwd: fixture, encoding: 'utf8' }).trim());
    assert.equal(provenance.status, '');
    assert.deepEqual(provenance.files, manifest(target));
    assert.equal(provenance.fingerprint, sha(JSON.stringify(provenance.files)));
    for (const [file, digest] of Object.entries(provenance.files)) assert.equal(sha(readFileSync(join(target, file))), digest);
  } finally {
    rmSync(fixture, { recursive: true, force: true });
    rmSync(destination, { recursive: true, force: true });
  }
});
