import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, readdirSync, mkdirSync } from 'node:fs';
import { join, relative } from 'node:path';
import { execFileSync } from 'node:child_process';

export const sha = value => createHash('sha256').update(value).digest('hex');
export const json = file => JSON.parse(readFileSync(file, 'utf8'));
export const writeJson = (file, value) => writeFileSync(file, JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
export const median = values => {
  if (!values.length || values.some(v => !Number.isFinite(v))) throw new Error('Invalid measurement samples');
  const sorted = [...values].sort((a, b) => a - b), middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
};
export function files(root) {
  return readdirSync(root, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name)).flatMap(entry => {
    const path = join(root, entry.name);
    if (entry.isSymbolicLink()) throw new Error(`No symlinks in a frozen snapshot: ${path}`);
    return entry.isDirectory() ? files(path) : [path];
  });
}
export const manifest = root => Object.fromEntries(files(root).map(file => [relative(root, file), sha(readFileSync(file))]));
export function seal(root) { writeJson(join(root, 'manifest.json'), manifest(root)); }
export function verifySeal(root) {
  const expected = json(join(root, 'manifest.json')), actual = manifest(root);
  delete actual['manifest.json'];
  if (JSON.stringify(expected) !== JSON.stringify(actual)) throw new Error(`Frozen evidence changed: ${root}`);
  return sha(JSON.stringify(expected));
}
export function snapshot(source, destination) {
  const paths = ['src', 'pyto/viewer', 'pyto/consumers/discstudio-card/port/painter'];
  const selected = ['package.json', ...paths.flatMap(path => files(join(source, path)).filter(file => /\.(m?js)$/.test(file)).map(file => relative(source, file)))].sort();
  const before = Object.fromEntries(selected.map(file => [file, sha(readFileSync(join(source, file)))]));
  mkdirSync(destination);
  for (const file of selected) {
    const target = join(destination, file); mkdirSync(join(target, '..'), { recursive: true });
    writeFileSync(target, readFileSync(join(source, file)), { flag: 'wx' });
  }
  if (selected.some(file => sha(readFileSync(join(source, file))) !== before[file] || sha(readFileSync(join(destination, file))) !== before[file])) throw new Error('Source changed during snapshot');
  const git = args => execFileSync('git', ['-C', source, ...args], { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 });
  return { checkout: source, commit: git(['rev-parse', 'HEAD']).trim(), branch: git(['branch', '--show-current']).trim(), status: git(['status', '--porcelain=v1']), files: before, fingerprint: sha(JSON.stringify(before)), patch: git(['diff', '--binary', 'HEAD', '--', 'src', 'pyto/viewer', 'pyto/consumers/discstudio-card/port/painter', 'package.json']) };
}
export function parity(baseline, candidate) {
  if (!Array.isArray(baseline) || !baseline.length || !Array.isArray(candidate)) throw new Error('Missing equivalence observations');
  const ids = baseline.map(x => x.id), otherIds = candidate.map(x => x.id);
  const sameCases = JSON.stringify(ids) === JSON.stringify(otherIds) && new Set(ids).size === ids.length;
  const mismatches = baseline.filter((expected, i) => {
    const actual = candidate[i];
    return !actual || expected.id !== actual.id || expected.svg !== actual.svg || expected.resultSha256 !== actual.resultSha256 || sha(expected.svg) !== expected.svgSha256 || sha(actual.svg) !== actual.svgSha256;
  }).map(x => x.id);
  return { pass: sameCases && mismatches.length === 0, cases: baseline.length, mismatches, sameCases };
}
export function compare({ reference, candidate, rounds, contract }) {
  const equivalent = parity(reference, candidate);
  if (rounds.length !== contract.rounds) throw new Error('Incomplete paired rounds');
  const keys = Object.keys(rounds[0].baseline).sort();
  if (!keys.includes(contract.primary)) throw new Error('Primary metric missing');
  const metrics = {};
  for (const round of rounds) for (const side of ['baseline', 'candidate']) {
    if (JSON.stringify(Object.keys(round[side]).sort()) !== JSON.stringify(keys)) throw new Error('Workload metrics differ');
    for (const value of Object.values(round[side])) {
      if (!(value.medianMs > 0) || !Number.isFinite(value.medianMs) || !value.samplesMs?.length || value.samplesMs.some(x => !Number.isFinite(x) || x <= 0) || median(value.samplesMs) !== value.medianMs) throw new Error('Invalid timing evidence');
    }
  }
  for (const key of keys) {
    const base = rounds.map(r => r.baseline[key].medianMs), next = rounds.map(r => r.candidate[key].medianMs);
    const pairedImprovements = base.map((v, i) => 1 - next[i] / v);
    metrics[key] = { baselineMs: median(base), candidateMs: median(next), improvement: median(pairedImprovements), wins: pairedImprovements.filter(v => v > contract.minimumImprovement).length, pairedImprovements };
  }
  const primary = metrics[contract.primary];
  const regressions = keys.filter(key => metrics[key].improvement < -contract.maximumRegression);
  const verdict = !equivalent.pass ? 'rejected-equivalence' : regressions.length ? 'rejected-regression' : primary.improvement > contract.minimumImprovement && primary.wins >= contract.minimumWinningRounds ? 'promising-needs-review' : 'inconclusive';
  return { verdict, equivalence: equivalent, primary: contract.primary, metrics, regressions, acceptance: null, promotion: null };
}
