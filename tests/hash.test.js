import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { sha256HexSync } from '../src/core/sha256.js';
test('browser-safe SHA-256 agrees with Node for empty, Unicode and multiblock input', () => {
  for (const text of ['', 'abc', 'Buzzz → exact photo', 'DiscStudio'.repeat(1000)]) {
    const bytes = new TextEncoder().encode(text);
    assert.equal(sha256HexSync(bytes), createHash('sha256').update(bytes).digest('hex'));
  }
});
