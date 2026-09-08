import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { execSync } from 'node:child_process';
const root = path.resolve(import.meta.dirname, '..'), out = path.join(root, 'dist');
await fs.rm(out, { recursive: true, force: true }); await fs.mkdir(out, { recursive: true });
for (const file of ['src', 'public', 'concept-b', 'index.html', 'docs']) await fs.cp(path.join(root, file), path.join(out, file), { recursive: true });
const hash = crypto.createHash('sha256');
async function visit(dir) { for (const e of (await fs.readdir(dir, { withFileTypes: true })).sort((a, b) => a.name.localeCompare(b.name))) { const p = path.join(dir, e.name); if (e.isDirectory()) await visit(p); else { hash.update(path.relative(root, p)); hash.update(await fs.readFile(p)); } } }
await visit(path.join(root, 'src')); await visit(path.join(root, 'public')); await visit(path.join(root, 'tests'));
let commit = process.env.GITHUB_SHA; if (!commit) try { commit = execSync('git rev-parse HEAD', { cwd: root, stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim(); } catch { commit = 'local-uncommitted'; }
const info = { commit, fingerprint: hash.digest('hex'), builtAt: new Date().toISOString(), version: '0.2.0' };
await fs.writeFile(path.join(out, 'build-info.json'), JSON.stringify(info, null, 2));
console.log(`Built ${out}\nCommit: ${commit}\nSource/test fingerprint: ${info.fingerprint}`);
