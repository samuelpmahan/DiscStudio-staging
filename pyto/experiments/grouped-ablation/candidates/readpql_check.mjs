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
//   publish       readPql must accept, then invokePql over a board seeded with
//                 `seed` must run to the end, and the addresses it published
//                 must be exactly `expect` (an array, compared sorted). Each
//                 stub returns an object keyed by that Calculation's declared
//                 `into` addresses, which is the multi-produce output shape
//                 invokePql spreads across them (exec.js:60-70).
//
// Prints one JSON verdict object per line and a final {"ok": bool, ...} summary;
// exits 1 if any case fails. Imports src/core/exec.js from this repository by
// relative path (no package install, no network).
import { readPql, invokePql, createExecBoard, pxFn, produceAddresses } from '../../../../src/core/exec.js';
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
      const calculations = composition.Ticks.flatMap((t) => t.Calculations);
      verdict.detail = `read ${composition.Ticks.length} tick(s), ${calculations.length} calculation(s), ` +
        `${calculations.reduce((n, c) => n + produceAddresses(c.into).length, 0)} produce(s)`;
    } else if (item.kind === 'reject') {
      verdict.detail = 'readPql accepted a document that had to be refused';
    } else {
      const pxc = createExecBoard();
      const seeded = new Set(Object.keys(item.seed ?? {}));
      for (const [address, value] of Object.entries(item.seed ?? {})) pxc.set(address, value);
      const stubs = new Map();
      for (const tick of composition.Ticks) {
        for (const calculation of tick.Calculations) {
          // One stub per address: register() rejects a *different* callable at a known
          // address (exec.js:18), so a fresh arrow per invocation would fail there first.
          if (!stubs.has(calculation.call)) {
            const declared = produceAddresses(calculation.into);
            stubs.set(calculation.call, declared.length > 1
              ? () => Object.fromEntries(declared.map((address) => [address, { stub: address }]))
              : () => ({ stub: true }));
          }
          pxc.register(pxFn(calculation.call), stubs.get(calculation.call));
        }
      }
      if (item.kind === 'publish') {
        try {
          invokePql(composition, { pxc });
          const published = pxc.keys().filter((address) => !seeded.has(address) && !address.startsWith('px.pql.')).sort();
          const expected = [...item.expect].sort();
          verdict.pass = JSON.stringify(published) === JSON.stringify(expected);
          verdict.detail = `published ${JSON.stringify(published)}`;
        } catch (error) {
          verdict.detail = `invokePql failed where it had to publish: ${chain(error)}`;
        }
      } else {
        try {
          invokePql(composition, { pxc });
          verdict.detail = 'invokePql succeeded where it had to fail';
        } catch (error) {
          const text = chain(error);
          verdict.pass = text.includes(item.expect);
          verdict.detail = text;
        }
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
