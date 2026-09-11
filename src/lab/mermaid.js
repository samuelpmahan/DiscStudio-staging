/**
 * The Mermaid path, ported: a `.mmd` flowchart compiles to a PQL document.
 *
 * `compileMermaidPcr` (packages/alg/src/stages/S0/exp/mermaid-pcr/compiler.ts)
 * parses one explicit flowchart subset -- `flowchart TD`, `subgraph X["PCR: N"]`,
 * `subgraph Y["Tick: N"]`, `fn.*`/`px.*` nodes, named input arrows
 * `a -->|binding| b`, publication arrows `fn --> px` -- and emits
 * `{ PrincipleComponentRender, Ticks: [{ name, Calculations: [{ id, call, with, args, into? }] }] }`:
 * the same document the LAB's Stage YAML holds, with two differences the studio's
 * grammar does not have.
 *
 *   1. a binding is `{ kind: 'fn' | 'px', ref }`, not an address: a Calculation
 *      may read a previous Calculation's RESULT with no Part in between (S0's
 *      decode is bound straight into bounds and crop, and FullImage is never
 *      published -- the LAB's proof checks exactly that, `fullImageLocal`);
 *   2. `into` is optional: a Calculation may publish nothing.
 *
 * `lowerToPql` is the port's bridge: it gives every unpublished result an
 * address (`px.exp.lab.<pcr>.local.<id>`) so `readPql` can read the document,
 * and reports which bindings needed one. That report is the finding
 * (proposal.lab.pql.directresult).
 */
import { digestOf } from './lab.js';
import { labAddress } from './address.js';

function fail(message) { throw new Error(`lab mermaid: ${message}`); }

export function parseMermaid(source) {
  const lines = source.split(/\r?\n/).map(line => line.trim()).filter(Boolean);
  if (lines.shift() !== 'flowchart TD') fail('only `flowchart TD` is supported.');
  const nodes = new Map(), edges = [], subgraphs = [], ticks = [];
  const register = (id, label) => {
    const kind = label.startsWith('fn.') ? 'fn' : label.startsWith('px.') ? 'px' : null;
    if (!kind) fail(`node '${id}' must label fn.* or px.*.`);
    if (nodes.has(id)) fail(`node '${id}' is declared more than once.`);
    nodes.set(id, { id, label, kind, tick: [...subgraphs].reverse().find(value => value.startsWith('Tick: '))?.slice(6) });
  };
  for (const line of lines) {
    if (line === 'end') { if (!subgraphs.length) fail('unexpected `end`.'); subgraphs.pop(); continue; }
    const subgraph = /^subgraph ([A-Za-z0-9_]+)\["([^"]+)"\]$/.exec(line);
    if (subgraph) { subgraphs.push(subgraph[2]); if (subgraph[2].startsWith('Tick: ')) ticks.push(subgraph[2].slice(6)); continue; }
    if (line.includes(':::') || line.startsWith('click ') || line.startsWith('classDef ')) fail(`unsupported syntax '${line}'.`);
    const labelledInline = /^([A-Za-z0-9_]+)\s+-->\|([^|]+)\|\s+([A-Za-z0-9_]+)\["([^"]+)"\]$/.exec(line);
    if (labelledInline) { register(labelledInline[3], labelledInline[4]); edges.push({ from: labelledInline[1], label: labelledInline[2], to: labelledInline[3] }); continue; }
    const labelled = /^([A-Za-z0-9_]+)\s+-->\|([^|]+)\|\s+([A-Za-z0-9_]+)$/.exec(line);
    if (labelled) { edges.push({ from: labelled[1], label: labelled[2], to: labelled[3] }); continue; }
    const plainInline = /^([A-Za-z0-9_]+)\s+-->\s+([A-Za-z0-9_]+)\["([^"]+)"\]$/.exec(line);
    if (plainInline) { register(plainInline[2], plainInline[3]); edges.push({ from: plainInline[1], to: plainInline[2] }); continue; }
    const plain = /^([A-Za-z0-9_]+)\s+-->\s+([A-Za-z0-9_]+)$/.exec(line);
    if (plain) { edges.push({ from: plain[1], to: plain[2] }); continue; }
    const node = /^([A-Za-z0-9_]+)\["([^"]+)"\]$/.exec(line);
    if (node) { register(node[1], node[2]); continue; }
    fail(`unsupported syntax '${line}'.`);
  }
  if (subgraphs.length) fail(`unterminated subgraph '${subgraphs.at(-1)}'.`);
  return { nodes: [...nodes.values()], edges, ticks };
}

/** Declaration order is executable order; forward dependencies and cycles are refused. */
export function compileMermaidPcr(mermaid, args) {
  const graph = parseMermaid(mermaid);
  const pcr = /subgraph \w+\["PCR: ([^"]+)"\]/.exec(mermaid)?.[1];
  if (!pcr) fail('missing PCR subgraph.');
  if (new Set(graph.ticks).size !== graph.ticks.length) fail('duplicate Tick names.');
  const byId = new Map(graph.nodes.map(node => [node.id, node]));
  const functions = graph.nodes.filter(node => node.kind === 'fn');
  const positions = new Map(functions.map((node, index) => [node.id, index]));
  for (const id of Object.keys(args)) if (!positions.has(id)) fail(`unknown argument occurrence '${id}'.`);
  const writers = new Map();
  for (const edge of graph.edges) {
    const from = byId.get(edge.from), to = byId.get(edge.to);
    if (!from || !to) fail(`unknown edge endpoint '${edge.from}' or '${edge.to}'.`);
    if (from.kind === 'px' && to.kind === 'px') fail('PxC-to-PxC edges require a Calculation.');
    if (to.kind === 'fn' && !edge.label) fail(`input edge to '${to.id}' needs a named binding.`);
    if (to.kind === 'px') {
      if (edge.label) fail('publication edges cannot have input labels.');
      if (writers.has(to.label)) fail(`multiple writers for '${to.label}'.`);
      writers.set(to.label, from.id);
    }
  }
  const ticks = graph.ticks.map(name => ({ name, Calculations: [] }));
  let previousTick = -1;
  for (const fn of functions) {
    const index = graph.ticks.indexOf(fn.tick ?? '');
    if (index < 0 || index < previousTick) fail(`invalid Tick placement for '${fn.id}'.`);
    previousTick = index;
    const bindings = {};
    for (const edge of graph.edges.filter(candidate => candidate.to === fn.id)) {
      const source = byId.get(edge.from), key = edge.label;
      if (Object.hasOwn(bindings, key) || Object.hasOwn(args[fn.id] ?? {}, key)) fail(`duplicate input '${fn.id}.${key}'.`);
      const producer = source.kind === 'fn' ? source.id : writers.get(source.label);
      if (producer && positions.get(producer) >= positions.get(fn.id)) fail(`forward dependency or cycle at '${fn.id}.${key}'.`);
      bindings[key] = source.kind === 'fn' ? { kind: 'fn', ref: source.id } : { kind: 'px', ref: source.label };
    }
    const publications = graph.edges.filter(edge => edge.from === fn.id && byId.get(edge.to).kind === 'px');
    if (publications.length > 1) fail(`multiple publications from '${fn.id}'.`);
    if (!graph.edges.some(edge => edge.from === fn.id)) fail(`unused function '${fn.id}'.`);
    ticks[index].Calculations.push({ id: fn.id, call: fn.label, with: bindings, args: args[fn.id] ?? {}, ...(publications.length ? { into: byId.get(publications[0].to).label } : {}) });
  }
  return { PrincipleComponentRender: pcr, Ticks: ticks };
}

/**
 * The compiled document, as the studio's `readPql` can read it: every binding is
 * an address, every Calculation publishes one. `local` lists what had to be
 * given an address to get there.
 */
export function lowerToPql(compiled) {
  const local = [], produced = new Map();
  const document = {
    PrincipleComponentRender: compiled.PrincipleComponentRender,
    Ticks: compiled.Ticks.map(tick => ({
      name: tick.name,
      Calculations: tick.Calculations.map(calculation => {
        const into = calculation.into ?? `px.${compiled.PrincipleComponentRender.toLowerCase()}.local.${calculation.id}`;
        if (!calculation.into) local.push({ id: calculation.id, call: calculation.call, address: into, why: 'the graph publishes no Part for this result' });
        produced.set(calculation.id, into);
        return { id: calculation.id, call: calculation.call, args: calculation.args, into, with: Object.fromEntries(Object.entries(calculation.with).map(([name, binding]) => [name, binding.kind === 'px' ? binding.ref : produced.get(binding.ref) ?? fail(`'${binding.ref}' is bound before it is produced.`)])) };
      })
    }))
  };
  return { document, local };
}

/** The document with the LAB's addresses rewritten to the port's lowercase ones. */
export { labDocument } from './address.js';

/**
 * A document's structural digest: sha256 of its canonical JSON with the labels
 * stripped (pyto/src/pyto/neat/diff.py `structural_digest`). A Calculation's
 * `id` is a label the Mermaid graph carries and the YAML does not, and a Tick's
 * name is the label a reader reads, so both are stripped: two documents with the
 * same digest run the same Calculations over the same addresses in the same order.
 */
export function structuralDigest(document) {
  return digestOf({
    Ticks: document.Ticks.map(tick => tick.Calculations.map(calculation => ({
      call: calculation.call, args: calculation.args ?? {}, into: calculation.into,
      with: Object.fromEntries(Object.entries(calculation.with ?? {}).sort())
    })))
  });
}

/** Drop the Ticks named here (the LAB's proof drops `fn.s0.asMaskRaster`, which the YAML path seeds instead of computing). */
export function withoutCalls(document, calls) {
  return {
    PrincipleComponentRender: document.PrincipleComponentRender,
    Ticks: document.Ticks.map(tick => ({ ...tick, Calculations: tick.Calculations.filter(calculation => !calls.includes(calculation.call)) })).filter(tick => tick.Calculations.length)
  };
}
