/**
 * Run adapters.js `validate` over a JSON array of candidate records and report
 * one verdict per entry, so a Python test can ask JavaScript what it thinks.
 *
 * usage: node test/validate_cases.mjs <cases.json>
 * stdout: [{"ok": true, "path": null} | {"ok": false, "path": "ticks[0].index"}]
 *
 * It never renders and never writes: the only question is whether the record
 * conforms to RECORD.md and, when it does not, which path adapters.js names.
 */
import { readFileSync } from 'node:fs';

import { validate, RecordSchemaError } from '../adapters.js';

const file = process.argv[2];
if (!file) {
  process.stderr.write('usage: node test/validate_cases.mjs <cases.json>\n');
  process.exit(2);
}

const cases = JSON.parse(readFileSync(file, 'utf8'));
if (!Array.isArray(cases)) {
  process.stderr.write('expected a JSON array of candidate records\n');
  process.exit(2);
}

const verdicts = cases.map((document) => {
  try {
    validate(document);
    return { ok: true, path: null };
  } catch (error) {
    if (error instanceof RecordSchemaError) return { ok: false, path: error.path, message: error.message };
    return { ok: false, path: null, message: String(error) };
  }
});

process.stdout.write(`${JSON.stringify(verdicts)}\n`);
