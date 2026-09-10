/**
 * docs/USE-JS.md, executed.
 *
 * `docs/USE-JS.md` is the page a person reads to learn the surface the site is
 * written against: the store, a PQL document, running it, the receipt, the run
 * record, the undo Part. Every ```js block in it is run here in a fresh `node`
 * process and its stdout is compared **byte for byte** with the ```text block
 * that follows it, so the document is true or this suite is red.
 *
 * One test per block, named for the section it lives in, so a red test names the
 * paragraph that lies rather than "the docs".
 *
 * A block is written as an ES module whose imports are relative to the repository
 * root (`../src/core/exec.js`), which is how a file in `docs/` or `scripts/`
 * spells them. It runs from a temporary directory, so those relative specifiers
 * are rewritten to absolute `file:` URLs of this checkout on the way in -- the
 * document itself names no absolute path, which
 * `the document names no absolute path` keeps true.
 *
 *   node --test tests/use-js.test.js     run the suite
 *   node tests/use-js.test.js --show     print what each block actually prints
 *   node tests/use-js.test.js --fill     rewrite the ```text blocks from the run
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const ROOT = resolve(import.meta.dirname, '..');
const USE_MD = join(ROOT, 'docs', 'USE-JS.md');
const ROOT_URL = pathToFileURL(ROOT).href.replace(/\/$/, '');

const FENCE = /^```(js|text)[ \t]*$/m;
const HEADING = /^##+[ \t]+(.*?)[ \t]*$/gm;

const readUseMd = () => readFileSync(USE_MD, 'utf8');

/** Every fenced `js`/`text` block as { language, body, offset, start, end }, in document order. */
function fencedBlocks(text) {
  const blocks = [];
  for (let position = 0; position < text.length;) {
    const rest = text.slice(position), opened = rest.match(FENCE);
    if (!opened) break;
    const offset = position + opened.index, bodyStart = offset + opened[0].length + 1;
    const closed = text.indexOf('\n```', bodyStart - 1);
    assert.ok(closed >= 0, `USE-JS.md has an unterminated \`\`\` block at offset ${offset}`);
    blocks.push({ language: opened[1], body: text.slice(bodyStart, closed + 1), offset, start: bodyStart, end: closed + 1 });
    position = closed + '\n```'.length;
  }
  return blocks;
}

/** The nearest `##` heading above an offset. */
function sectionAt(text, offset) {
  let name = 'preamble';
  HEADING.lastIndex = 0;
  for (let heading = HEADING.exec(text); heading; heading = HEADING.exec(text)) {
    if (heading.index > offset) break;
    name = heading[1];
  }
  return name;
}

/** Every js block in document order, paired with the text block after it. */
function parseBlocks(text) {
  const fenced = fencedBlocks(text), blocks = [];
  fenced.forEach((block, position) => {
    if (block.language !== 'js') return;
    const next = fenced[position + 1];
    const expected = next && next.language === 'text' ? next : null;
    blocks.push({ index: blocks.length + 1, section: sectionAt(text, block.offset), source: block.body, expected });
  });
  return blocks;
}

/**
 * Run one block in a fresh process from a temporary directory, with `../` import
 * specifiers rewritten to this checkout. The block's own working directory is the
 * repository root, so a relative path it names reads the same file the reader's would.
 */
function runBlock(source) {
  const directory = mkdtempSync(join(tmpdir(), 'use-js-'));
  try {
    const script = join(directory, 'block.mjs');
    writeFileSync(script, source.replace(/(\bfrom\s*['"])\.\.\//g, `$1${ROOT_URL}/`), 'utf8');
    try {
      const stdout = execFileSync(process.execPath, [script], { cwd: ROOT, encoding: 'buffer', env: { ...process.env, TZ: 'UTC', NO_COLOR: '1' }, timeout: 300000 });
      return { code: 0, stdout, stderr: Buffer.alloc(0) };
    } catch (failed) {
      return { code: failed.status ?? 1, stdout: failed.stdout ?? Buffer.alloc(0), stderr: failed.stderr ?? Buffer.from(String(failed.message)) };
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

const BLOCKS = parseBlocks(readUseMd());

for (const block of BLOCKS) {
  test(`USE-JS.md § ${block.section}`, () => {
    const { code, stdout, stderr } = runBlock(block.source);
    assert.equal(code, 0, `block ${block.index} of section '${block.section}' failed:\n${stderr.toString('utf8')}`);
    assert.ok(block.expected, `block ${block.index} of section '${block.section}' has no \`\`\`text block after it`);
    assert.equal(stdout.toString('utf8'), block.expected.body, `block ${block.index} of section '${block.section}' prints something other than the text block under it`);
    assert.ok(stdout.equals(Buffer.from(block.expected.body, 'utf8')), 'byte-for-byte comparison');
  });
}

test('the document names no absolute path', () => {
  const absolute = /(?:^|[\s"'(=`])(\/[A-Za-z_.][\w./-]*|[A-Za-z]:[\\/])/g;
  const found = [...readUseMd().matchAll(absolute)].map(match => match[1]);
  assert.deepEqual(found, [], 'USE-JS.md names an absolute path; every path in it must be relative to the repository root');
});

test('the document reaches for no temporary directory and no wall clock', () => {
  const forbidden = /\/tmp\b|\bmkdtemp\b|\btmpdir\b|\bDate\.now\b|new Date\b|performance\.now\b|Math\.random\b/g;
  const found = [...new Set([...readUseMd().matchAll(forbidden)].map(match => match[0]))].sort();
  assert.deepEqual(found, [], 'USE-JS.md is executed twice and must print the same bytes both times');
});

test('every block is pinned to its output', () => {
  const unpinned = BLOCKS.filter(block => !block.expected).map(block => block.index);
  assert.deepEqual(unpinned, [], 'these USE-JS.md js blocks have no ```text block after them');
});

test('the sections are the ones the page promises', () => {
  assert.deepEqual(BLOCKS.map(block => block.section), [
    '1. The store',
    '2. A PQL document',
    '3. Running it',
    '4. The receipt',
    '5. The run record',
    '6. Undo, as a Part',
    '7. What not to do'
  ]);
});

if (process.argv.includes('--show') || process.argv.includes('--fill')) {
  const filling = process.argv.includes('--fill');
  let text = readUseMd(), shift = 0;
  for (const block of BLOCKS) {
    const { code, stdout, stderr } = runBlock(block.source);
    process.stdout.write(`===== block ${block.index} [${block.section}] exit ${code}\n`);
    process.stdout.write(stdout.toString('utf8'));
    if (stderr.length) process.stdout.write(stderr.toString('utf8'));
    if (!filling || code !== 0 || !block.expected) continue;
    const printed = stdout.toString('utf8');
    text = text.slice(0, block.expected.start + shift) + printed + text.slice(block.expected.end + shift);
    shift += printed.length - (block.expected.end - block.expected.start);
  }
  if (filling) {
    writeFileSync(USE_MD, text, 'utf8');
    process.stdout.write('\nfilled docs/USE-JS.md\n');
  }
}
