/**
 * embed.mjs writes a standalone page: the record embedded, the viewer inlined,
 * nothing fetched. Also covers the loader seam (coerceToRecord,
 * readEmbeddedRecord) that the page uses at start-up.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, mkdirSync, cpSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, join } from 'node:path';

import { validate, fromPytoRecord } from '../adapters.js';
import { coerceToRecord, readEmbeddedRecord } from '../tick-viewer.js';
import { buildPage, embedFile, embeddableJson } from '../embed.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const VIEWER = resolve(HERE, '..');
const fixturePath = (name) => resolve(VIEWER, 'fixtures', name);
const fixture = (name) => JSON.parse(readFileSync(fixturePath(name), 'utf8'));

const RECORD_OPEN = '<script type="application/json" id="record">';

function embeddedRecordOf(page) {
  const start = page.indexOf(RECORD_OPEN) + RECORD_OPEN.length;
  const end = page.indexOf('</script>', start);
  assert.ok(start > RECORD_OPEN.length - 1 && end > start, 'the page carries a record block');
  return JSON.parse(page.slice(start, end));
}

/* ---------------------------------------------------------------- */

test('coerceToRecord accepts a record and every raw runtime document', () => {
  const cases = [
    ['pyto-grouped-ablation.json', (doc) => doc, 'pyto'],
    ['discstudio-display-card.json', (doc) => doc, 'discstudio'],
    ['discstudio-display-card.json', (doc) => doc.first, 'discstudio'],
    ['chesslab-s0-s1.json', (doc) => doc, 'chesslab'],
    ['wumpus-belief-tick.json', (doc) => doc, 'wumpus']
  ];
  for (const [name, pick, runtime] of cases) {
    const record = coerceToRecord(pick(fixture(name)));
    validate(record);
    assert.equal(record.source.runtime, runtime, name);
  }
  assert.throws(() => coerceToRecord({ nothing: true }), /Unrecognized document/);
  assert.throws(() => coerceToRecord(null), /Unrecognized document/);
});

test('readEmbeddedRecord reads the block, and returns null when it is empty', () => {
  const record = fromPytoRecord(fixture('pyto-grouped-ablation.json'));
  const doc = (textContent) => ({ getElementById: (id) => (id === 'record' ? { textContent } : null) });
  assert.equal(readEmbeddedRecord(doc('')), null);
  assert.equal(readEmbeddedRecord(doc('\n  \n')), null);
  assert.equal(readEmbeddedRecord({ getElementById: () => null }), null);
  assert.deepEqual(readEmbeddedRecord(doc(JSON.stringify(record))), record);
  assert.throws(() => readEmbeddedRecord(doc('{"schema":"pyto-run-record@1"}')), /pcr: expected a string/);
});

test('embeddableJson escapes every character that could end the script element', () => {
  const text = embeddableJson({ a: '</script><img onerror=alert(1)>', b: '  ' });
  assert.ok(!text.includes('<'), text);
  assert.ok(!text.includes('>'), text);
  assert.ok(!text.includes(' '));
  assert.deepEqual(JSON.parse(text), { a: '</script><img onerror=alert(1)>', b: '  ' });
});

test('buildPage inlines the viewer and embeds the record, with no module graph left', () => {
  const record = fromPytoRecord(fixture('pyto-grouped-ablation.json'));
  const page = buildPage(record);

  assert.ok(!page.includes('src="./tick-viewer.js"'), 'no external script src');
  assert.ok(!page.includes("from './adapters.js'"), 'the adapters import is gone');
  assert.equal((page.match(/^<script/gm) || []).length, 2, 'exactly the record block and the inlined module');
  assert.equal((page.match(/^<\/script>/gm) || []).length, 2);
  assert.equal(page.match(/^\s*(import|export)\s/gm), null, 'no module statement survives inlining');
  assert.ok(page.includes('\nmount(document);\n'), 'the page still boots');
  assert.ok(page.includes('function renderRecord'), 'the viewer is present');
  assert.ok(page.includes('function validate'), 'the adapters are present');
  assert.ok(!/https?:\/\/(?!www\.w3\.org)/.test(page.replace(/xmlns="[^"]*"/g, '')), 'nothing is fetched from the network');

  assert.deepEqual(embeddedRecordOf(page), record);
  validate(embeddedRecordOf(page));
});

test('embedFile converts a raw runtime document on the way in', () => {
  for (const [name, runtime, pcr] of [
    ['discstudio-display-card.json', 'discstudio', 'display-card'],
    ['chesslab-s0-s1.json', 'chesslab', 'chesslab'],
    ['wumpus-belief-tick.json', 'wumpus', 'wumpus']
  ]) {
    const page = embedFile(fixturePath(name));
    const record = embeddedRecordOf(page);
    validate(record);
    assert.equal(record.source.runtime, runtime, name);
    assert.equal(record.pcr, pcr, name);
  }
});

test('embedFile refuses a document that is not a record and not a known runtime shape', () => {
  const dir = mkdtempSync(join(tmpdir(), 'tick-embed-'));
  const bad = join(dir, 'bad.json');
  writeFileSync(bad, JSON.stringify({ hello: 'world' }));
  assert.throws(() => embedFile(bad), /Unrecognized document/);
});

test('buildPage fails loudly when the page and the embedder drift apart', () => {
  const dir = mkdtempSync(join(tmpdir(), 'tick-drift-'));
  mkdirSync(dir, { recursive: true });
  for (const name of ['adapters.js', 'tick-viewer.js', 'tick-viewer.html']) cpSync(resolve(VIEWER, name), join(dir, name));
  const html = readFileSync(join(dir, 'tick-viewer.html'), 'utf8');
  writeFileSync(join(dir, 'tick-viewer.html'), html.replace(RECORD_OPEN, '<script type="application/json" id="run">'));
  const record = fromPytoRecord(fixture('pyto-grouped-ablation.json'));
  assert.throws(() => buildPage(record, { viewerDir: dir }), /empty record block not found/);
});

test('node embed.mjs record.json > page.html writes the same page from the command line', () => {
  const dir = mkdtempSync(join(tmpdir(), 'tick-cli-'));
  const out = join(dir, 'page.html');
  const stdout = execFileSync(process.execPath, ['embed.mjs', 'fixtures/pyto-grouped-ablation.json'], { cwd: VIEWER, encoding: 'utf8', maxBuffer: 1 << 24 });
  execFileSync(process.execPath, ['embed.mjs', 'fixtures/pyto-grouped-ablation.json', '--out', out], { cwd: VIEWER });
  const written = readFileSync(out, 'utf8');
  assert.equal(stdout, written);
  assert.equal(written, buildPage(fromPytoRecord(fixture('pyto-grouped-ablation.json'))));
  assert.ok(written.startsWith('<!doctype html>'));
});

test('the CLI exits 2 with a usage line when no record is named', () => {
  const error = (() => {
    try {
      execFileSync(process.execPath, ['embed.mjs'], { cwd: VIEWER, stdio: 'pipe' });
    } catch (thrown) {
      return thrown;
    }
    throw new assert.AssertionError({ message: 'expected a non-zero exit' });
  })();
  assert.equal(error.status, 2);
  assert.match(String(error.stderr), /usage: node embed\.mjs/);
});
