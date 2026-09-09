/**
 * Write every JavaScript adapter's output as a record file, so the Python
 * validator can read what JavaScript produced.
 *
 * usage: node test/emit_adapter_records.mjs <out-dir>
 *
 * One file per case, named <case>.json, plus manifest.json listing them with
 * the runtime each claims. The records are written with sorted keys and
 * two-space indentation (RECORD.md:67), which is also how pyto.materialize
 * writes them -- so the two runtimes' files are comparable as bytes and not
 * only as parsed JSON.
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, join } from 'node:path';

import {
  fromPytoRecord, fromDiscStudioReceipt, fromChessLabReceipts, fromWumpusRecords
} from '../adapters.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const fixture = (name) => JSON.parse(readFileSync(resolve(HERE, '..', 'fixtures', name), 'utf8'));

/** RECORD.md:67 -- sorted keys, two-space indentation. */
function sortedStringify(value) {
  const keys = [];
  JSON.stringify(value, (key, held) => {
    if (key) keys.push(key);
    return held;
  });
  return `${JSON.stringify(value, [...new Set(keys)].sort(), 2)}\n`;
}

const ds = fixture('discstudio-display-card.json');
const cases = {
  pyto: () => fromPytoRecord(fixture('pyto-grouped-ablation.json')),
  'pyto-value-kinds': () => fromPytoRecord(fixture('pyto-value-kinds.json')),
  'discstudio-first': () => fromDiscStudioReceipt(ds.first.pql, ds.first.receipt, { version: 'transcribed-82f8fc9' }),
  'discstudio-second': () => fromDiscStudioReceipt(ds.second.pql, ds.second.receipt),
  chesslab: () => fromChessLabReceipts(fixture('chesslab-s0-s1.json').receipts, { pcr: 'chesslab.debugger' }),
  wumpus: () => fromWumpusRecords(fixture('wumpus-belief-tick.json').records, { pcr: 'wumpus.belief' })
};

const outDir = process.argv[2];
if (!outDir) {
  process.stderr.write('usage: node test/emit_adapter_records.mjs <out-dir>\n');
  process.exit(2);
}
mkdirSync(outDir, { recursive: true });

const manifest = [];
for (const [name, build] of Object.entries(cases)) {
  const record = build();
  const file = join(outDir, `${name}.json`);
  writeFileSync(file, sortedStringify(record));
  manifest.push({ name, file, runtime: record.source.runtime, pcr: record.pcr, counters: record.counters });
}
writeFileSync(join(outDir, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
process.stdout.write(`${manifest.length} records written to ${outDir}\n`);
