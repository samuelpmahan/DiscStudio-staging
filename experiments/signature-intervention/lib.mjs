import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, relative } from 'node:path';

export const sha = value => createHash('sha256').update(value).digest('hex');
export const json = file => JSON.parse(readFileSync(file, 'utf8'));
export const writeJson = (file, value) => writeFileSync(file, JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
export const median = xs => {
  if (!xs.length || xs.some(x => !Number.isFinite(x))) throw new Error('Invalid numeric samples');
  const sorted = [...xs].sort((a, b) => a - b), n = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[n] : (sorted[n - 1] + sorted[n]) / 2;
};
export const timingMedian = xs => {
  if (!xs.length || xs.some(x => !Number.isFinite(x) || x < 0)) throw new Error('Invalid timing samples');
  return median(xs);
};
export function files(root) {
  return readdirSync(root, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name)).flatMap(entry => {
    const path = join(root, entry.name);
    if (entry.isSymbolicLink()) throw new Error(`Symlink is not allowed in identity: ${path}`);
    return entry.isDirectory() ? files(path) : [path];
  });
}
export const sourceIdentity = root => {
  const entries = Object.fromEntries(files(root).map(file => [relative(root, file), sha(readFileSync(file))]));
  return { root, files: entries, fingerprint: sha(JSON.stringify(entries)) };
};
/** The variants import the existing runtime dependency tree. Pin it without
 * copying a second renderer into this experiment. */
export function sharedSourceIdentity(root) {
  const paths = execFileSync('git', ['-C', root, 'ls-files', 'src/**/*.js', 'src/**/*.mjs', 'pyto/**/*.js', 'pyto/**/*.mjs'], { encoding: 'utf8' }).trim().split('\n').filter(Boolean).sort();
  const entries = Object.fromEntries(paths.map(path => [path, sha(readFileSync(join(root, path)))]));
  return { root, files: entries, fingerprint: sha(JSON.stringify(entries)) };
}
export const seal = root => writeJson(join(root, 'manifest.json'), Object.fromEntries(files(root).map(file => [relative(root, file), sha(readFileSync(file))])));
export function verifySeal(root) {
  const expected = json(join(root, 'manifest.json')), actual = Object.fromEntries(files(root).filter(file => relative(root, file) !== 'manifest.json').map(file => [relative(root, file), sha(readFileSync(file))]));
  if (JSON.stringify(expected) !== JSON.stringify(actual)) throw new Error(`Sealed output changed: ${root}`);
  return sha(JSON.stringify(expected));
}
export const withoutReceipt = result => {
  const copy = structuredClone(result);
  if (!copy || typeof copy !== 'object' || !Object.hasOwn(copy, 'run')) throw new Error('Render result has no top-level run receipt');
  delete copy.run;
  return copy;
};
export function compareOutputs(reference, candidate) {
  if (reference.length !== candidate.length) return { pass: false, cases: reference.length, mismatches: ['length'] };
  const mismatches = reference.filter((row, i) => row.id !== candidate[i]?.id || row.inputSha256 !== candidate[i]?.inputSha256 || JSON.stringify(row.output) !== JSON.stringify(candidate[i]?.output) || row.svgSha256 !== candidate[i]?.svgSha256).map(row => row.id);
  return { pass: mismatches.length === 0, cases: reference.length, mismatches };
}
export const ensureDir = path => mkdirSync(path, { recursive: true });
export const observerSlices = (events, boundaries) => {
  if (!Array.isArray(boundaries) || boundaries.some((n, i) => !Number.isInteger(n) || n < (i ? boundaries[i - 1] : 0) || n > events.length)) throw new Error('Invalid observer boundaries');
  return boundaries.map((end, i) => events.slice(i ? boundaries[i - 1] : 0, end));
};
