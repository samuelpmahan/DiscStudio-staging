/**
 * The embedded LAB documents are the bytes in src/lab/source/, and nothing else.
 * The Stage modules read them from src/lab/source-data.js so they can be imported
 * in a browser, which has no file system; this is the check that the two cannot
 * drift apart.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { SOURCE } from '../src/lab/source.js';
import { SOURCE_TEXT, readSource, readSourceJson } from '../src/lab/source-data.js';

test('every embedded document is the file byte for byte', () => {
  const names = Object.keys(SOURCE_TEXT);
  assert.deepEqual(names, ['S0.args.json', 'S0.mmd', 'S0.pcr.yaml', 'S0.stage.yaml', 'S1.args.json', 'S1.mmd', 'S1.pcr.yaml', 'basket-sprite.json']);
  for (const name of names) assert.equal(readSource(name), readFileSync(join(SOURCE, name), 'utf8'), name);
  assert.equal(readSourceJson('basket-sprite.json').width, 42);
  assert.throws(() => readSource('S9.pcr.yaml'), /not an embedded source document/);
});

test('no Stage module the browser imports reaches for node at import time', async () => {
  const browserSide = ['address.js', 'fixtures.js', 'lab.js', 'mermaid.js', 'route.js', 's0.js', 's1.js', 's2.js', 's3.js', 'source-data.js', 'stages.js', 'yaml.js'];
  for (const name of browserSide) {
    const source = readFileSync(join(SOURCE, '..', name), 'utf8');
    const statics = [...source.matchAll(/^\s*import\s[^\n]*?from\s*'([^']+)'/gm)].map(match => match[1]);
    assert.deepEqual(statics.filter(specifier => specifier.startsWith('node:')), [], `${name} imports node at module scope`);
  }
});
