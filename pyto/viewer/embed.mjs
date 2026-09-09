#!/usr/bin/env node
/**
 * embed.mjs — write a standalone Tick viewer with one record baked in.
 *
 *   node embed.mjs record.json > page.html
 *   node embed.mjs fixtures/wumpus-belief-tick.json --out /tmp/wumpus.html
 *
 * The output is a single file that opens over file:// with no server, no
 * network and no module graph: adapters.js and tick-viewer.js are concatenated
 * into one inline module, and the record is placed in the page's
 * <script type="application/json" id="record"> block.
 *
 * The input may be a pyto-run-record@1 document or a raw runtime document
 * ({pql, receipt} / {receipts} / {records}); it is converted and validated
 * here, so an invalid record fails at build time instead of in the browser.
 */

import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, basename } from 'node:path';
import { coerceToRecord } from './tick-viewer.js';

const HERE = dirname(fileURLToPath(import.meta.url));

const PAGE_SCRIPT = `<script type="module">
  import { mount } from './tick-viewer.js';
  mount(document);
</script>`;

const EMPTY_RECORD_BLOCK = '<script type="application/json" id="record"></script>';
const EMPTY_RECORDS_BLOCK = '<script type="application/json" id="records"></script>';

// ChainSpot is the founding world (pyto/research/origin.md); no adapter or
// fixture exists yet, so `--worlds` names it as a labelled empty slot.
export const CHAINSPOT_ENTRY = { label: 'ChainSpot', record: null, error: null, empty: true, note: 'no record on file yet' };

/** Strip ES module syntax so two modules can be concatenated into one script. */
function inlineModule(source, name) {
  const withoutImports = source.replace(/^import[^\n]*from '\.\/adapters\.js';\n/m, '');
  const flattened = withoutImports.replace(/^export (?=(?:default )?(?:function|const|let|var|class)\b)/gm, '');
  const leftover = flattened.match(/^\s*(import|export)\b[^\n]*/m);
  if (leftover) throw new Error(`${name}: cannot inline, unhandled module statement: ${leftover[0].trim()}`);
  // A literal </script anywhere in the source would end the inline element early.
  // The backslash is inert in a comment, a string literal and a regex alike.
  return flattened.replace(/<\/script/gi, '<\\/script');
}

/** JSON that is safe inside a <script> element and inside HTML comments. */
export function embeddableJson(record) {
  return JSON.stringify(record, null, 2)
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/\u2028/g, '\\u2028')
    .replace(/\u2029/g, '\\u2029');
}

/** Build the standalone page as a string. `play` bakes in `<body data-play="1">`, the offline equivalent of `?play=1`. */
export function buildPage(record, { viewerDir = HERE, play = false } = {}) {
  let html = readFileSync(resolve(viewerDir, 'tick-viewer.html'), 'utf8');
  const adapters = inlineModule(readFileSync(resolve(viewerDir, 'adapters.js'), 'utf8'), 'adapters.js');
  const viewer = inlineModule(readFileSync(resolve(viewerDir, 'tick-viewer.js'), 'utf8'), 'tick-viewer.js');

  if (!html.includes(PAGE_SCRIPT)) throw new Error('tick-viewer.html: module bootstrap block not found; embed.mjs and the page have drifted apart');
  if (!html.includes(EMPTY_RECORD_BLOCK)) throw new Error('tick-viewer.html: empty record block not found; embed.mjs and the page have drifted apart');
  if (!html.includes(EMPTY_RECORDS_BLOCK)) throw new Error('tick-viewer.html: empty records block not found; embed.mjs and the page have drifted apart');
  if (play) html = html.replace('<body>', '<body data-play="1">');

  // The single-record page has no use for the multi-world #records block (see
  // buildWorldsPage below), so it is dropped rather than shipped empty.
  html = html.replace(`${EMPTY_RECORDS_BLOCK}\n`, '');
  const bundle = `<script type="module">\n/* adapters.js + tick-viewer.js, inlined by embed.mjs. No imports, no network. */\n${adapters}\n${viewer}\nmount(document);\n</script>`;
  const recordBlock = `<script type="application/json" id="record">\n${embeddableJson(record)}\n</script>`;
  // Both replacements pass a FUNCTION, never a string. String.prototype.replace
  // expands `$&`, `$'`, '$`' and `$1` inside a replacement *string*, and both of
  // these replacements are record- or source-derived: a Part value, an address or
  // a pcr name holding `$'` (a shell snippet such as `printf $'%s\n'` is enough)
  // spliced the page's own tail into the JSON block, so the record no longer
  // parsed and the module bootstrap was left un-inlined -- a page that can never
  // mount, produced silently at build time. A function replacement is inserted
  // literally.
  return html.replace(EMPTY_RECORD_BLOCK, () => recordBlock).replace(PAGE_SCRIPT, () => bundle);
}

export function embedFile(inputPath, { viewerDir = HERE, play = false } = {}) {
  const parsed = JSON.parse(readFileSync(inputPath, 'utf8'));
  return buildPage(coerceToRecord(parsed), { viewerDir, play });
}

// One world's input, converted through the same adapters (coerceToRecord,
// which validates) the single-record path uses. A world whose input cannot
// become a record still gets a slot -- {error} names why -- rather than
// failing the whole multi-world build.
export function loadWorldEntry(inputPath) {
  const label = basename(inputPath).replace(/\.json$/i, '');
  try {
    const record = coerceToRecord(JSON.parse(readFileSync(inputPath, 'utf8')));
    return { label: `${record.pcr} · ${record.source.runtime}`, record, error: null, empty: false, note: null };
  } catch (error) {
    return { label, record: null, error: error.message, empty: false, note: null };
  }
}

/** Standalone page carrying every world's record, with the picker `tick-viewer.js` renders. */
export function buildWorldsPage(entries, { viewerDir = HERE, play = false } = {}) {
  let html = readFileSync(resolve(viewerDir, 'tick-viewer.html'), 'utf8');
  const adapters = inlineModule(readFileSync(resolve(viewerDir, 'adapters.js'), 'utf8'), 'adapters.js');
  const viewer = inlineModule(readFileSync(resolve(viewerDir, 'tick-viewer.js'), 'utf8'), 'tick-viewer.js');

  if (!html.includes(PAGE_SCRIPT)) throw new Error('tick-viewer.html: module bootstrap block not found; embed.mjs and the page have drifted apart');
  if (!html.includes(EMPTY_RECORD_BLOCK)) throw new Error('tick-viewer.html: empty record block not found; embed.mjs and the page have drifted apart');
  if (!html.includes(EMPTY_RECORDS_BLOCK)) throw new Error('tick-viewer.html: empty records block not found; embed.mjs and the page have drifted apart');
  if (play) html = html.replace('<body>', '<body data-play="1">');

  // The multi-world page reads only #records; the single-record #record block
  // is unused here and dropped rather than shipped empty.
  html = html.replace(`${EMPTY_RECORD_BLOCK}\n`, '');
  const bundle = `<script type="module">\n/* adapters.js + tick-viewer.js, inlined by embed.mjs. No imports, no network. */\n${adapters}\n${viewer}\nmount(document);\n</script>`;
  const recordsBlock = `<script type="application/json" id="records">\n${embeddableJson(entries)}\n</script>`;
  // Function replacements, as in buildPage: a label or value holding $&/$'/$` must not splice.
  return html.replace(EMPTY_RECORDS_BLOCK, () => recordsBlock).replace(PAGE_SCRIPT, () => bundle);
}

/** Every fixture, sorted, plus the labelled ChainSpot slot -- `--worlds`. */
export function buildWorldsFromFixtures({ viewerDir = HERE, play = false } = {}) {
  const fixturesDir = resolve(viewerDir, 'fixtures');
  const files = readdirSync(fixturesDir).filter((name) => name.endsWith('.json')).sort();
  const entries = files.map((name) => loadWorldEntry(resolve(fixturesDir, name)));
  entries.push(CHAINSPOT_ENTRY);
  return buildWorldsPage(entries, { viewerDir, play });
}

function main(argv) {
  const args = argv.slice(2);
  const outIndex = args.findIndex((a) => a === '--out' || a === '-o');
  let out = null;
  if (outIndex !== -1) {
    out = args[outIndex + 1];
    if (!out) throw new Error('--out needs a path');
    args.splice(outIndex, 2);
  }
  const playIndex = args.indexOf('--play');
  const play = playIndex !== -1;
  if (play) args.splice(playIndex, 1);
  const worldsIndex = args.indexOf('--worlds');
  const worlds = worldsIndex !== -1;
  if (worlds) args.splice(worldsIndex, 1);

  let page;
  if (worlds) {
    page = buildWorldsFromFixtures({ play });
  } else if (args.length >= 2) {
    // Four worlds, one terminal: two or more inputs bake all of them into one
    // page with a picker, each converted through the same adapters as the
    // single-record path below.
    page = buildWorldsPage(args.map((input) => loadWorldEntry(resolve(process.cwd(), input))), { play });
  } else if (args.length === 1) {
    page = embedFile(resolve(process.cwd(), args[0]), { play });
  } else {
    process.stderr.write('usage: node embed.mjs <record.json> [--out page.html] [--play]\n'
      + '       node embed.mjs a.json b.json ... --out worlds.html   # multiple worlds, one picker\n'
      + '       node embed.mjs --worlds --out worlds.html            # every fixture, plus ChainSpot\n');
    process.exit(2);
  }
  if (out) writeFileSync(resolve(process.cwd(), out), page);
  else process.stdout.write(page);
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url))) main(process.argv);
