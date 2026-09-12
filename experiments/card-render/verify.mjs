#!/usr/bin/env node
// Local verification capture, separate from the frozen performance harness.
import { spawnSync, execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync, readFileSync, readdirSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { sha, writeJson, seal } from './lib.mjs';

const out = resolve(process.argv[2] ?? 'evidence/card-render/verification');
const requested = process.argv.slice(3);
const names = ['node-tests', 'neat-tests', 'use-docs', 'painter-fixtures', 'build'];
if (requested.some(name => !names.includes(name))) throw new Error(`Unknown check. Choose: ${names.join(', ')}`);
const python = process.env.PYTHON;
if (!python) throw new Error('Set PYTHON to an installed Python >=3.10 with this checkout\'s pyto package installed; USE.md runs isolated.');
mkdirSync(dirname(out), { recursive: true }); mkdirSync(out);
const root = resolve(import.meta.dirname, '../..');
const env = { ...process.env, PATH: `${dirname(process.execPath)}:${dirname(python)}:${process.env.PATH}`, PYTHONPATH: join(root, 'pyto/src') };
const git = args => execFileSync('git', args, { cwd: root, encoding: 'utf8' });
const targets = ['src/runtime.js', 'src/review-data.js', '.neat/items/DS-STUDIO-02.json', 'pyto/src/pyto/neat/hot.py', 'pyto/src/pyto/neat/equiv.py', 'pyto/USE.md', 'pyto/tests/test_neat_hot.py', 'pyto/tests/test_neat_equiv.py', 'tests/card-experiment.test.js', 'tests/runtime-signature.test.js'];
targets.push('tests/shadow-render.test.js', ...['model.mjs', 'session.mjs', 'render-worker.mjs', 'worker-peer.mjs', 'run.mjs', 'task.yaml'].map(name => `experiments/shadow-render/${name}`));
const fingerprints = () => Object.fromEntries(targets.map(path => [path, sha(readFileSync(join(root, path)))]));
const before = fingerprints();
writeJson(join(out, 'source.json'), { commit: git(['rev-parse', 'HEAD']).trim(), branch: git(['branch', '--show-current']).trim(), status: git(['status', '--porcelain']), files: before, scope: 'Changed code/contracts named here; Git patch retains other tracked changes. Not a hermetic deployment snapshot.' });
writeFileSync(join(out, 'working-tree.patch'), git(['diff', '--binary', 'HEAD']), { flag: 'wx' });
writeJson(join(out, 'environment.json'), { node: process.version, executable: process.execPath, python, pythonVersion: execFileSync(python, ['--version'], { encoding: 'utf8' }).trim(), scriptSha256: sha(readFileSync(import.meta.filename)) });
const tests = path => readdirSync(join(root, path)).filter(name => /\.test\.(m?js)$/.test(name)).sort().map(name => join(path, name));
const jobs = [
  ['node-tests', process.execPath, ['--test', ...tests('tests'), ...tests('pyto/viewer/test')]],
  ['neat-tests', python, ['-m', 'unittest', 'discover', '-s', 'pyto/tests', '-p', 'test_neat_*.py']],
  ['use-docs', python, ['-m', 'unittest', 'discover', '-s', 'pyto/tests', '-p', 'test_use.py']],
  ['painter-fixtures', process.execPath, ['pyto/consumers/discstudio-card/port/painter/verify_port.mjs', './pyto/consumers/discstudio-card/port/painter/painter.mjs', './pyto/consumers/discstudio-card/port/painter/cards.mjs']],
  ['build', process.execPath, ['scripts/build.mjs']],
];
const results = [];
for (const [name, executable, args] of jobs) {
  if (requested.length && !requested.includes(name)) continue;
  console.log(`Running ${name}…`);
  const start = Date.now(), result = spawnSync(executable, args, { cwd: root, env, encoding: 'utf8', maxBuffer: 32 * 1024 * 1024, timeout: 600000 });
  writeFileSync(join(out, `${name}.log`), `${result.stdout ?? ''}\n${result.stderr ?? ''}`, { flag: 'wx' });
  results.push({ name, executable, args, exitCode: result.status, error: result.error?.message ?? null, elapsedMs: Date.now() - start });
  writeJson(join(out, `${name}.json`), results.at(-1));
  console.log(`${name}: exit ${result.status}`);
}
const unchanged = JSON.stringify(before) === JSON.stringify(fingerprints());
writeJson(join(out, 'result.json'), { scope: requested.length ? requested : names, results, unchanged, pass: unchanged && results.every(r => r.exitCode === 0), acceptance: null, promotion: null });
seal(out);
if (!unchanged || results.some(r => r.exitCode !== 0)) process.exitCode = 1;
console.log(`Verification retained: ${out}`);
