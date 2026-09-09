// Run the real browser reader over documents this experiment produced.
//
//   node readpql_check.mjs <cases.json>
//
// cases.json: {"cases": [{name, kind, document, expect?, seed?}]} where kind is
//   accept        readPql(JSON.stringify(document), JSON.parse) must not throw
//   reject        readPql must throw, and the message must contain `expect`
//   invoke_fails  readPql must accept, then invokePql over a board seeded with
//                 `seed` (address -> value) and a stub calculation per `call`
//                 must throw, with `expect` somewhere in the error chain
//
// Prints one JSON verdict object per line and a final {"ok": bool, ...} summary;
// exits 1 if any case fails. Imports src/core/exec.js from this repository by
// relative path (no package install, no network).
import { readPql, invokePql, createExecBoard, pxFn } from '../../../../src/core/exec.js';
import { readFileSync } from 'node:fs';

const chain = (error) => {
  const parts = [];
  for (let current = error; current; current = current.cause) parts.push(String(current.message ?? current));
  return parts.join(' | ');
};

const cases = JSON.parse(readFileSync(process.argv[2], 'utf8')).cases;
const verdicts = [];
for (const item of cases) {
  const verdict = { name: item.name, kind: item.kind, pass: false, detail: '' };
  try {
    const composition = readPql(JSON.stringify(item.document), JSON.parse);
    if (item.kind === 'accept') {
      verdict.pass = true;
      verdict.detail = `read ${composition.Ticks.length} tick(s), ` +
        `${composition.Ticks.reduce((n, t) => n + t.Calculations.length, 0)} calculation(s)`;
    } else if (item.kind === 'reject') {
      verdict.detail = 'readPql accepted a document that had to be refused';
    } else {
      const pxc = createExecBoard();
      for (const [address, value] of Object.entries(item.seed ?? {})) pxc.set(address, value);
      const stubs = new Map();
      for (const tick of composition.Ticks) {
        for (const calculation of tick.Calculations) {
          // One stub per address: register() rejects a *different* callable at a known
          // address (exec.js:18), so a fresh arrow per invocation would fail there first.
          if (!stubs.has(calculation.call)) stubs.set(calculation.call, () => ({ stub: true }));
          pxc.register(pxFn(calculation.call), stubs.get(calculation.call));
        }
      }
      try {
        invokePql(composition, { pxc });
        verdict.detail = 'invokePql succeeded where it had to fail';
      } catch (error) {
        const text = chain(error);
        verdict.pass = text.includes(item.expect);
        verdict.detail = text;
      }
    }
  } catch (error) {
    const text = chain(error);
    if (item.kind === 'reject') {
      verdict.pass = text.includes(item.expect);
      verdict.detail = text;
    } else {
      verdict.detail = `unexpected throw: ${text}`;
    }
  }
  verdicts.push(verdict);
  console.log(JSON.stringify(verdict));
}
const failed = verdicts.filter((v) => !v.pass).map((v) => v.name);
console.log(JSON.stringify({ ok: failed.length === 0, cases: verdicts.length, failed }));
process.exit(failed.length === 0 ? 0 : 1);
