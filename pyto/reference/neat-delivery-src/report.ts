import type { BoardModel } from "./board.js";
import type { ItemAssessment, DependencyEdge } from "./board.js";
import type { WorkItem, WorkTarget } from "./work-items.js";

/** The three intentional product scopes in an mGM row. */
export type MgmScope = "minimal" | "goldilocks" | "maximal";

export interface MgmUnit {
  id: string;
  title: string;
  target: WorkTarget;
  inspectableResult: string;
  targetScope: MgmScope;
  scopes: Record<MgmScope, { requirementIds: readonly string[] }>;
}

export interface MgmMatrix {
  schemaVersion: 1;
  scopeSemantics: "cumulative";
  foundations: readonly string[];
  title?: string;
  units: readonly MgmUnit[];
}

export interface ReportOptions {
  title?: string;
  matrix?: MgmMatrix;
}

const esc = (value: unknown): string => String(value ?? "")
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;").replaceAll("'", "&#39;");
const attr = (value: unknown): string => esc(value);
/** Return a URL only for safe static links; callers can render invalid input as text. */
export function safeHref(value: string): string | undefined {
  if (/^https?:\/\//i.test(value)) return value;
  if (/^(?!\/\/)(?![a-z][a-z0-9+.-]*:)[^\s]+$/iu.test(value)) return value;
  return undefined;
}
const refList = (refs: readonly string[]): string => refs.length
  ? `<ul class="refs">${refs.map((ref) => { const href = safeHref(ref); return `<li>${href ? `<a href="${attr(href)}"><code>${esc(ref)}</code></a>` : `<code>${esc(ref)}</code>`}</li>`; }).join("")}</ul>`
  : `<span class="muted">none</span>`;
const mark = (yes: boolean, label: string): string => `<span class="status ${yes ? "yes" : "no"}">${yes ? "✓" : "○"} ${esc(label)}</span>`;
const scopeRank: Record<MgmScope, number> = { minimal: 1, goldilocks: 2, maximal: 3 };

function boardTab(items: readonly WorkItem[], board: BoardModel): string {
  const byId = new Map(items.map((item) => [item.id, item]));
  return `<section id="tab-board" class="tab-panel" role="tabpanel">
    <div class="cards">${board.assessments.map((a) => {
      const item = byId.get(a.itemId);
      if (!item) return "";
      return `<article class="card" data-item="${attr(item.id)}">
        <div class="card-head"><h3>${esc(item.id)} <small>${esc(a.bucket)}</small></h3><span class="activity">${esc(item.status)}${item.agent ? ` · agent=${esc(item.agent)}` : ""}</span></div>
        <p>${esc(item.outcome)}</p>
        <p class="target"><b>Target:</b> <code>${esc(item.target.kind)}:${esc(item.target.identity)}</code></p>
        <div class="statuses">${mark(a.verified, "verified")}${mark(a.accepted, "accepted")}${mark(a.promoted, "promoted")}</div>
        <div class="evidence"><div><b>Execution</b>${refList(a.executionRefs)}</div><div><b>Inspection</b>${refList(a.inspectionRefs)}</div></div>
        ${a.blockers.length ? `<p class="blockers"><b>Blocked:</b> ${esc(a.blockers.join("; "))}</p>` : ""}
      </article>`;
    }).join("")}</div>
  </section>`;
}

function matrixTab(matrix: MgmMatrix | undefined, items: readonly WorkItem[], board: BoardModel): string {
  if (!matrix) return `<section id="tab-matrix" class="tab-panel" role="tabpanel"><p class="empty">No mGM matrix supplied yet. This view accepts one without changing the base work-item model.</p></section>`;
  const rows = matrix.units.map((unit) => {
    const target = unit.targetScope;
    const work = items.find((item) => item.target.kind === unit.target.kind && item.target.identity === unit.target.identity && (unit.target.composition === undefined || item.target.composition === unit.target.composition));
    const assessment = board.assessments.find((candidate) => candidate.target.kind === unit.target.kind && candidate.target.identity === unit.target.identity && (unit.target.composition === undefined || candidate.target.composition === unit.target.composition));
    const observed = assessment ? `<p class="observed">Observed: ${mark(assessment.verified, "verified")} ${mark(assessment.accepted, "accepted")}</p>` : `<p class="observed">Observed: no matching work item</p>`;
    return `<tr data-unit="${attr(unit.id)}"><th scope="row"><b>${esc(unit.title)}</b><code>${esc(unit.target.kind)}:${esc(unit.target.identity)}</code><span>${esc(unit.inspectableResult)}</span>${observed}</th>${(["minimal", "goldilocks", "maximal"] as MgmScope[]).map((scope) => {
      const cumulative = scopeRank[scope] <= scopeRank[target];
      const requirements = (["minimal", "goldilocks", "maximal"] as MgmScope[])
        .filter((candidate) => scopeRank[candidate] <= scopeRank[scope])
        .flatMap((candidate) => unit.scopes[candidate].requirementIds)
        .map((id) => ({ id, text: work?.requirements.find((requirement) => requirement.id === id)?.text }));
      const state = cumulative ? "planned" : "future";
      return `<td class="scope-${scope} state-${state}"><b>${esc(scope)}</b><ul>${requirements.map((requirement) => `<li>${esc(requirement.text ?? `[missing requirement: ${requirement.id}]`)}</li>`).join("")}</ul><small>${esc(state === "planned" ? "planned · not observed" : "future")}</small></td>`;
    }).join("")}</tr>`;
  }).join("");
  return `<section id="tab-matrix" class="tab-panel" role="tabpanel"><p class="matrix-note">${esc(matrix.title ?? "mGM capability matrix")}. Target scope is ${esc(matrix.units.map((u) => `${u.id}=${u.targetScope}`).join(" · "))}. Scope requirements are cumulative (each tier includes prior tiers); each tier is a planned target and is not assessed per tier. Observed verified/accepted status is shown separately per unit.</p><p><b>Foundations:</b> ${esc(matrix.foundations.join(" · "))}</p><table class="matrix"><thead><tr><th>Tick / unit</th><th>Minimal</th><th>Goldilocks</th><th>Maximal</th></tr></thead><tbody>${rows}</tbody></table></section>`;
}

function dependenciesTab(items: readonly WorkItem[], board: BoardModel): string {
  const ids = items.map((item) => item.id).filter((id) => board.assessments.some((a) => a.itemId === id));
  const positions = new Map(ids.map((id, index) => [id, { x: 170 + (index % 3) * 250, y: 80 + Math.floor(index / 3) * 105 }]));
  const edges: DependencyEdge[] = board.graph.edges.filter((edge) => positions.has(edge.item) && positions.has(edge.prerequisite));
  const lines = edges.map((edge) => {
    const from = positions.get(edge.prerequisite)!; const to = positions.get(edge.item)!;
    const dx = to.x - from.x; const dy = to.y - from.y; const scale = Math.min(1, 78 / Math.max(1, Math.abs(dx)), 16 / Math.max(1, Math.abs(dy)));
    const sx = from.x + dx * scale; const sy = from.y + dy * scale; const tx = to.x - dx * scale; const ty = to.y - dy * scale;
    return `<line x1="${sx}" y1="${sy}" x2="${tx}" y2="${ty}" class="edge ${edge.satisfied ? "satisfied" : "blocked"}" data-item="${attr(edge.item)}" data-prerequisite="${attr(edge.prerequisite)}" data-requires="${attr(edge.requires)}"/><text class="edge-label" x="${(sx + tx) / 2}" y="${(sy + ty) / 2 - 5}">${esc(edge.requires)}</text>`;
  }).join("");
  const nodes = ids.map((id) => { const p = positions.get(id)!; const item = items.find((candidate) => candidate.id === id)!; const label = item.outcome.length > 25 ? `${item.outcome.slice(0, 24)}…` : item.outcome; return `<g class="node" data-item="${attr(id)}"><title>${esc(item.outcome)}</title><rect x="${p.x - 92}" y="${p.y - 22}" width="184" height="44" rx="8"/><text x="${p.x}" y="${p.y - 3}">${esc(id)}</text><text x="${p.x}" y="${p.y + 13}" class="node-label">${esc(label)}</text></g>`; }).join("");
  const fanout = Object.entries(board.calculationFanout).filter(([, targets]) => targets.length > 1);
  const fanoutHtml = fanout.map(([calc, targets]) => `<li><code>${esc(calc)}</code> → ${targets.map(esc).join(", ")}</li>`).join("");
  return `<section id="tab-dependencies" class="tab-panel" role="tabpanel"><p class="legend"><b>Arrow direction:</b> prerequisite → dependent. Edge labels show required status; dashed red edges are blocked.</p><svg class="dependency-map" viewBox="0 0 ${Math.max(760, ((ids.length - 1) % 3 + 1) * 250 + 170)} ${Math.max(180, (Math.ceil(ids.length / 3)) * 105 + 40)}" aria-label="Dependency graph"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 z" fill="#8e98a8"/></marker></defs>${lines}${nodes}</svg><h3>Shared calculations</h3>${fanoutHtml ? `<ul class="fanout">${fanoutHtml}</ul>` : `<p class="muted">No calculation fanout.</p>`}</section>`;
}

/** Render a self-contained, local HTML report from the retained BoardModel. */
export function renderReport(board: BoardModel, items: readonly WorkItem[], options: ReportOptions = {}): string {
  const title = options.title ?? "neat report";
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)}</title><style>
    :root{font:15px/1.45 system-ui,sans-serif;color:#202124;background:#f6f7f9}body{max-width:1180px;margin:0 auto;padding:28px}h1{margin:0 0 18px}.tabs{display:flex;gap:8px;border-bottom:1px solid #ccd1d9;margin-bottom:18px}.tab{border:0;background:none;padding:10px 15px;cursor:pointer;font:inherit}.tab[aria-selected=true]{border-bottom:3px solid #3458d4;color:#193aab;font-weight:700}.tab-panel{display:none}.tab-panel.active{display:block}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}.card{background:white;border:1px solid #d9dde5;border-radius:10px;padding:16px;box-shadow:0 2px 7px #17233b12}.card-head{display:flex;justify-content:space-between;gap:10px}.card h3{margin:0}.card h3 small{font-size:.7em;font-weight:500;color:#5a6474}.activity{font-size:.8em;color:#596579}.target{font-size:.9em}.statuses{display:flex;gap:8px;flex-wrap:wrap}.status{font-size:.8em;border-radius:999px;padding:3px 8px;background:#eef0f4}.status.yes{background:#dff4e5;color:#155a2a}.evidence{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px;font-size:.85em}.refs{margin:3px 0;padding-left:18px}.muted{color:#697386}.blockers{color:#9b2c2c;font-size:.88em}.matrix{width:100%;border-collapse:collapse;background:white}.matrix th,.matrix td{border:1px solid #d9dde5;padding:12px;text-align:left;vertical-align:top}.matrix td{min-width:180px}.matrix td span,.matrix td small{display:block}.matrix td small{margin-top:7px;color:#657084;font-size:.78em}.matrix .state-observed{background:#e6f7eb}.matrix .state-planned{background:#fff7dc}.matrix-note{padding:10px 13px;background:#eef2ff;border-left:4px solid #526dd6}.observed{font-size:.78em;margin:5px 0}.dependency-map{width:100%;min-height:210px;background:white;border:1px solid #d9dde5;border-radius:10px}.edge{stroke:#8e98a8;stroke-width:2;marker-end:url(#arrow)}.edge.blocked{stroke:#c63d3d;stroke-dasharray:5 4}.edge-label{font-size:11px;text-anchor:middle;fill:#49566a}.node rect{fill:#fff;stroke:#61708a}.node text{text-anchor:middle;font-weight:700;font-size:14px}.node .node-label{font-size:9px;font-weight:400}.legend{font-size:.88em;color:#536174}.fanout{background:white;border:1px solid #d9dde5;border-radius:8px;padding:12px 30px}
  </style></head><body><h1>${esc(title)}</h1><nav class="tabs" role="tablist"><button class="tab" role="tab" aria-selected="true" aria-controls="tab-board" data-tab="tab-board">Board</button><button class="tab" role="tab" aria-selected="false" aria-controls="tab-matrix" data-tab="tab-matrix">Matrix</button><button class="tab" role="tab" aria-selected="false" aria-controls="tab-dependencies" data-tab="tab-dependencies">Dependencies</button></nav>${boardTab(items, board)}${matrixTab(options.matrix, items, board)}${dependenciesTab(items, board)}<script>document.querySelectorAll('.tab').forEach(function(b){b.addEventListener('click',function(){document.querySelectorAll('.tab').forEach(function(x){x.setAttribute('aria-selected',String(x===b));});document.querySelectorAll('.tab-panel').forEach(function(x){x.classList.toggle('active',x.id===b.dataset.tab);});});});document.getElementById('tab-board').classList.add('active');</script></body></html>`;
}

export const renderHtmlReport = renderReport;
