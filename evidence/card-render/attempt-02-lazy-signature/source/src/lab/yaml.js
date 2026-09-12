/**
 * A YAML reader small enough to read the LAB's Stage documents, and nothing more.
 *
 * `readPql` takes its parser explicitly (src/core/exec.js: "no implicit YAML
 * dependency"), and the studio passes `JSON.parse`. The LAB writes its Stage
 * composition as YAML (`packages/alg/src/stages/S1/exp/badge-assembly/PrincipleComponentRender.yaml`),
 * so the port hands `readPql` this parser instead of transcribing that file into
 * JSON by hand: the document that runs here is the LAB's bytes, read.
 *
 * The subset: block mappings, block sequences, `#` comments, `{}` and `[]`
 * empties, and scalars (quoted strings, numbers, booleans, null, bare strings).
 * No anchors, flow collections with content, multi-line scalars or documents.
 * Anything else refuses by line, rather than guessing.
 */
const KEY = /^([A-Za-z0-9_.$-]+):(?:\s+(.*))?$/;

function fail(line, why) { throw new Error(`lab yaml: line ${line.number}: ${why} (${line.text})`); }

function stripComment(raw) {
  let inside = null;
  for (let index = 0; index < raw.length; index++) {
    const character = raw[index];
    if (inside) { if (character === inside) inside = null; continue; }
    if (character === '"' || character === "'") { inside = character; continue; }
    if (character === '#' && (index === 0 || /\s/.test(raw[index - 1]))) return raw.slice(0, index);
  }
  return raw;
}

function scalar(text, line) {
  if (text === '' || text === '~' || text === 'null') return null;
  if (text === 'true') return true;
  if (text === 'false') return false;
  if (text === '{}') return {};
  if (text === '[]') return [];
  if ((text.startsWith('"') && text.endsWith('"') && text.length > 1) || (text.startsWith("'") && text.endsWith("'") && text.length > 1)) return text.slice(1, -1);
  if (/^-?\d+(\.\d+)?([eE][-+]?\d+)?$/.test(text)) return Number(text);
  // One flow sequence of plain scalars, which is how S0.pcr.yaml writes its
  // receipt progression; flow mappings stay unsupported.
  if (text.startsWith('[') && text.endsWith(']')) return text.slice(1, -1).split(',').map(entry => scalar(entry.trim(), line));
  if (text.startsWith('{')) fail(line, 'flow mappings are not supported');
  return text;
}

/** Parse the lines from `start` that belong to a block at column `indent`; return [value, next]. */
function block(lines, start, indent) {
  if (start >= lines.length) return [null, start];
  const head = lines[start];
  if (head.indent === indent && head.text.startsWith('- ')) return sequence(lines, start, indent);
  // A lone bare word under a key is that key's scalar value (S0.pcr.yaml's
  // `transform:` / `crop_udisc_chrome`), not a mapping missing its colon.
  if (!KEY.test(head.text) && lines.length === start + 1) return [scalar(head.text, head), start + 1];
  return mapping(lines, start, indent);
}

function sequence(lines, start, indent) {
  const items = [];
  let index = start;
  while (index < lines.length && lines[index].indent === indent && lines[index].text.startsWith('- ')) {
    const head = { indent: indent + 2, text: lines[index].text.slice(2).trim(), number: lines[index].number };
    let end = index + 1;
    while (end < lines.length && lines[end].indent > indent) end += 1;
    const body = [head, ...lines.slice(index + 1, end)];
    items.push(KEY.test(head.text) ? block(body, 0, indent + 2)[0] : scalar(head.text, head));
    index = end;
  }
  return [items, index];
}

function mapping(lines, start, indent) {
  const value = {};
  let index = start;
  while (index < lines.length && lines[index].indent === indent) {
    const line = lines[index];
    const match = KEY.exec(line.text);
    if (!match) fail(line, 'expected `key: value` or `- item`');
    const [, key, rest] = match;
    if (rest !== undefined && rest !== '') { value[key] = scalar(rest.trim(), line); index += 1; continue; }
    let end = index + 1;
    while (end < lines.length && lines[end].indent > indent) end += 1;
    if (end === index + 1) { value[key] = null; index = end; continue; }
    value[key] = block(lines.slice(index + 1, end), 0, lines[index + 1].indent)[0];
    index = end;
  }
  return [value, index];
}

export function parseYaml(source) {
  const lines = [];
  source.split(/\r?\n/).forEach((raw, position) => {
    const text = stripComment(raw);
    if (!text.trim()) return;
    if (text.trim() === '---') return;
    lines.push({ indent: text.match(/^ */)[0].length, text: text.trim(), number: position + 1 });
  });
  if (!lines.length) return null;
  const [value, next] = block(lines, 0, lines[0].indent);
  if (next !== lines.length) fail(lines[next], 'unexpected indentation');
  return value;
}
