import { createSeed } from './seed.js';
import { createStudioRuntime } from './runtime.js';
import { get, all, currentBattle, clone, id, labelHash, validateWorld } from './domain.js';
import { esc, fieldNode } from './presentation.js';
import { constraintDefinitions } from './constraints.js';
import { reviewItems } from './review.js';
import { downloadBlob, downloadJson, photoData, pngFromSvg, sha256 } from './media.js';
import { composePage, fetchPageSources } from '../pyto/viewer/embed.mjs';

const DATA_KEY = 'discstudio.pxc.staging.world.v2', VIEW_KEY = 'discstudio.pxc.staging.view.v2';
const app = document.querySelector('#app');
let saveEnabled = true, stored = null, initialMessage = '';
try { const raw = localStorage.getItem(DATA_KEY); if (raw) stored = validateWorld(JSON.parse(raw)); }
catch (error) { saveEnabled = false; initialMessage = `Saved draft could not be opened: ${error.message} It has not been overwritten. Download the saved file before resetting.`; }
const runtime = createStudioRuntime(stored || createSeed());
let savedView = {}; try { savedView = JSON.parse(localStorage.getItem(VIEW_KEY) || '{}'); } catch { /* View preferences cannot invalidate a domain draft. */ }
const ui = {
  route: 'shelf', discId: savedView.discId || 'buzzz-mint', bagId: savedView.bagId || 'everyday', competitionId: 'putterwarz', roundId: 'hole-1',
  mode: savedView.mode || 'battle', presetId: savedView.presetId || 'broadcast', component: savedView.component || 'DisplayCard',
  nodeId: 'mold', query: '', fieldQuery: '', library: 'fields', onlyBag: false, traceOpen: false, inspectAddress: '', previewState: 'idle',
  extraType: '', extraId: '', message: initialMessage, error: !!initialMessage, saved: saveEnabled ? (stored ? 'Saved in this browser' : 'Local sample workspace') : 'Saved file protected',
  footage: null, footageKind: null, footageName: '', footageTime: 0, lastResult: null, busy: false, photoDiscId: null,
  motionEntry: null, newField: false, latestReceipt: null, recordAddress: '', build: { commit: 'local', fingerprint: 'development' }
};
const w = () => runtime.world();
const context = () => ({ bagId: ui.bagId, competitionId: ui.competitionId, roundId: ui.roundId, extraType: ui.extraType, extraId: ui.extraId });
const dataAttr = values => Object.entries(values).map(([key, value]) => `data-${key}="${esc(value)}"`).join(' ');
const button = (label, action, values = {}, classes = '', extra = '') => `<button class="${classes}" data-action="${action}" ${dataAttr(values)} ${extra}>${label}</button>`;
const select = (name, value, options, attrs = '') => `<select data-control="${name}" aria-label="${esc(name)}" ${attrs}>${options.map(([key, label]) => `<option value="${esc(key)}" ${String(key) === String(value) ? 'selected' : ''}>${esc(label)}</option>`).join('')}</select>`;
const input = (label, control, value, type = 'text', attrs = '') => `<label class="control"><span>${esc(label)}</span><input aria-label="${esc(label)}" data-control="${control}" type="${type}" value="${esc(value ?? '')}" ${attrs}></label>`;
const check = (label, control, value, attrs = '') => `<label class="check"><input data-control="${control}" type="checkbox" ${value ? 'checked' : ''} ${attrs}> ${esc(label)}</label>`;
const discInfo = (discId = ui.discId) => { const disc = get(w(), 'Disc', discId), mold = disc && get(w(), 'Mold', disc.moldId), maker = mold && get(w(), 'Manufacturer', mold.manufacturerId); return { disc, mold, maker }; };
const previewEntry = () => ui.previewState === 'idle' ? null : { id: 'editor-preview', score: 3, highlighted: ui.previewState === 'highlight', winner: ui.previewState === 'winner' };
function message(text, error = false) { ui.message = text; ui.error = error; }
/** The viewer's own directory, resolved from whichever URL this page actually has. */
function viewerBase() {
  for (const [path, base] of [['../pyto/viewer/', import.meta.url], ['./pyto/viewer/', globalThis.document?.baseURI]]) {
    try { if (base) return new URL(path, base); } catch { /* A data:/about: base cannot resolve a relative path. */ }
  }
  throw new Error('This page has no resolvable URL, so the Tick viewer sources cannot be read. Open the studio over http:// (npm run dev).');
}
let viewerSourcePromise = null;
/** tick-viewer.html + adapters.js + tick-viewer.js as text, fetched once from this origin. */
function viewerSources() {
  const base = viewerBase();
  viewerSourcePromise ??= fetchPageSources(base).catch(error => { viewerSourcePromise = null; throw new Error(`The Tick viewer sources could not be read from ${base}: ${error.message}`); });
  return viewerSourcePromise;
}
/** The PCR name of the execution the open trace panel is showing. */
function shownPcr() {
  const name = ui.lastResult?.run?.composition?.PrincipleComponentRender;
  if (!name) throw new Error('Render a composition before exporting its run record.');
  return name;
}
function persistView() { try { localStorage.setItem(VIEW_KEY, JSON.stringify({ discId: ui.discId, bagId: ui.bagId, mode: ui.mode, presetId: ui.presetId, component: ui.component })); } catch { /* Nonessential view state. */ } }
runtime.onChange(() => {
  if (saveEnabled) try { localStorage.setItem(DATA_KEY, JSON.stringify(w())); ui.saved = 'Saved in this browser'; }
  catch (error) { ui.saved = 'Not saved · download a draft'; message('Browser storage is full or unavailable. Your current work is still open. Download a draft to keep it.', true); }
  persistView();
});
function execute(command) { runtime.dispatch(command); }
function navigate(route) { location.hash = `/${route}`; }
function syncRoute() {
  const [path, query] = location.hash.slice(1).split('?'), params = new URLSearchParams(query);
  ui.route = ['shelf', 'course', 'components', 'competition'].includes(path?.slice(1)) ? path.slice(1) : 'shelf';
  if (params.has('node')) { ui.nodeId = params.get('node'); ui.component = 'DisplayCard'; ui.presetId = w().layout.presetId; }
  if (params.has('trace')) ui.traceOpen = true;
  render();
}
window.addEventListener('hashchange', syncRoute);
const safeThumb = (discId, preset = 'discImage') => { try { return runtime.card(discId, preset, context()).svg; } catch { return '<span class="missing">Missing disc</span>'; } };
function header() {
  return `<header class="app-header"><a class="brand" href="#/shelf"><span class="brand-mark">◎</span><strong>CHAINSPOT</strong><span class="brand-divider"></span><span>DISC STUDIO</span><small>PxC</small></a><nav aria-label="Workspace"><a href="#/shelf" class="${ui.route === 'shelf' ? 'active' : ''}">DiscShelf</a><a href="#/course" class="${ui.route === 'course' ? 'active' : ''}">OnTheCourse</a><a href="#/components" class="${['components', 'competition'].includes(ui.route) ? 'active' : ''}">Component Editor</a></nav><div class="header-actions"><span class="save-status"><i></i>${esc(ui.saved)}</span>${button('Save draft ↓', 'save-draft', {}, 'quiet')}${button('Load', 'load-draft', {}, 'quiet')}${button('Reset', 'reset', {}, 'quiet')}</div></header>`;
}
function bagSelect(control = 'bag') { return select(control, ui.bagId, all(w(), 'Bag').map(b => [b.id, `${b.name} · ${b.discIds.length}`])); }
function shelfSidebar() {
  const bag = get(w(), 'Bag', ui.bagId), query = ui.query.toLowerCase();
  const discs = all(w(), 'Disc').filter(d => { const { mold, maker } = discInfo(d.id); return `${d.nickname} ${mold?.name} ${maker?.name}`.toLowerCase().includes(query) && (!ui.onlyBag || bag?.discIds.includes(d.id)); });
  return `<aside class="sidebar" data-scroll="shelf"><div class="sidebar-heading"><div><span class="eyebrow">YOUR RAW MATERIAL</span><h2>Disc shelf <small>${all(w(), 'Disc').length}</small></h2></div>${button('+', 'disc-add', {}, 'circle', 'aria-label="Add a physical disc"')}</div><input class="search" data-search="discs" aria-label="Find a disc" placeholder="⌕  Find a disc…" value="${esc(ui.query)}">${ui.route === 'course' ? `<div class="sidebar-bag"><label class="eyebrow">SOURCE BAG</label>${bagSelect()}${check('Show only this bag', 'only-bag', ui.onlyBag)}</div>` : ''}<div class="disc-list">${discs.map(d => {
    const { mold, maker } = discInfo(d.id), membership = bag?.discIds.includes(d.id), inLineup = w().battle.entries.some(e => e.discId === d.id);
    return `<div class="disc-row ${ui.discId === d.id ? 'selected' : ''}"><button class="disc-pick" data-action="disc-select" data-id="${esc(d.id)}"><span class="disc-thumb">${safeThumb(d.id)}</span><span class="disc-copy"><span class="tiny caps">${esc(maker?.name || 'Unresolved')}</span><strong>${esc(mold?.name || 'Unresolved mold')}</strong><small>${esc(d.nickname)}</small></span></button>${button(ui.route === 'course' ? (inLineup ? '✓' : '+') : (membership ? '✓' : '+'), ui.route === 'course' ? 'lineup-add' : 'membership', { id: d.id }, 'row-add', `aria-label="${ui.route === 'course' ? 'Add to comparison' : membership ? 'Remove from bag' : 'Add to bag'}: ${esc(d.nickname)}" ${ui.route === 'course' && inLineup ? 'disabled' : ''}`)}</div>`;
  }).join('') || '<p class="empty-note">No matching discs.</p>'}</div><footer class="sidebar-footer">${ui.route === 'course' ? button('+ Add bag to comparison', 'bag-lineup', {}, 'wide secondary') : button('+ New physical disc', 'disc-add', {}, 'wide secondary')}<p class="tiny muted">Sample art is labelled. Your photos stay on your device.</p></footer></aside>`;
}
function shelfCenter() {
  const bag = get(w(), 'Bag', ui.bagId);
  return `<section class="center" data-scroll="center"><div class="section-heading"><div><span class="eyebrow">LESS SETUP. MORE DISC.</span><h1>Make it yours.</h1><p>Your physical discs. A bag for every kind of round.</p></div>${button('Take it OnTheCourse ↗', 'go-course', {}, 'primary')}</div><div class="section-toolbar"><div class="bag-picker">${bagSelect()}${button('+ New bag', 'bag-add', {}, 'quiet')}</div><div>${button('Rename', 'bag-rename', {}, 'quiet')}${button('Delete bag', 'bag-remove', {}, 'quiet')}</div></div><div class="bag-description"><span class="eyebrow">${bag ? `${bag.discIds.length} PHYSICAL DISCS · SHARED REFERENCES` : 'CREATE YOUR FIRST BAG'}</span><span class="mono tiny">${esc(bag ? `px.domain.Bag.${bag.id}` : '')}</span></div><div class="bag-grid">${(bag?.discIds || []).map(key => {
    const { disc, mold, maker } = discInfo(key); if (!disc) return `<div class="error-panel">Missing physical disc ${esc(key)}. Fix this reference before using the bag.</div>`;
    return `<article class="bag-card ${ui.discId === key ? 'is-selected' : ''}"><button class="bag-card-select" data-action="disc-select" data-id="${esc(key)}"><div class="bag-art">${safeThumb(key)}</div><div class="bag-card-caption"><span class="eyebrow">${esc(maker?.name)}</span><h3>${esc(mold?.name)}</h3><p>${esc(disc.nickname)}</p><span class="tiny">${[disc.plastic, disc.weight == null ? '' : `${disc.weight} g`].filter(Boolean).map(esc).join(' · ')}</span></div></button>${button('−', 'membership', { id: key }, 'bag-remove', 'aria-label="Remove from this bag only"')}</article>`;
  }).join('') || '<div class="empty-state"><h2>Start with the discs you actually throw.</h2><p>Use the + beside any shelf disc to put it in this bag. One disc can belong to several bags.</p></div>'}</div><div class="principle-strip"><span>ONE DISC. MANY COMPOSITIONS.</span><p>Change a photo or fact here. Every bound card sees the same physical disc.</p></div>${tracePanel(ui.lastResult?.run)}</section>`;
}
function discInspector() {
  const { disc, mold, maker } = discInfo(); if (!disc) return '<aside class="inspector"><p>Select or add a disc.</p></aside>';
  const fields = w().schemas.Disc.fields;
  const primitiveFields = Object.entries(fields).filter(([, d]) => ['text', 'number', 'boolean'].includes(d.type));
  return `<aside class="inspector" data-scroll="inspector"><div class="inspector-title"><span class="eyebrow">INSPECT & CHANGE</span><span class="live-tag">LIVE · PxC</span></div><h2>${esc(mold?.name || 'Disc')}</h2><div class="inspector-art">${safeThumb(disc.id)}</div>${button(disc.photo ? 'Replace exact disc photo' : '↑ Add exact disc photo', 'photo', { id: disc.id }, 'wide')}${disc.photo ? button('Remove photo', 'photo-remove', {}, 'quiet small') : '<p class="tiny muted">Sample illustration, not your disc. No photo leaves this browser.</p>'}<section class="control-section"><h3>Disc identity <span>DOMAIN</span></h3>${input('Manufacturer', 'identity-maker', maker?.name || '')}${input('Mold / disc name', 'identity-mold', mold?.name || '')}<p class="tiny muted">These fields link this specimen to its product identity. Re-identifying it does not rename other discs.</p>${primitiveFields.map(([key, def]) => def.type === 'boolean' ? check(def.label, 'disc-field', disc[key], `data-key="${esc(key)}"`) : input(def.label + (def.unit ? ` (${def.unit})` : ''), 'disc-field', disc[key], def.type === 'number' ? 'number' : 'text', `data-key="${esc(key)}" data-kind="${def.type}"`)).join('')}<div class="four-inputs">${Object.entries(w().schemas.Mold.fields.flight.fields).map(([key, def]) => input(def.label, 'flight', mold?.flight?.[key], 'number', `data-key="${key}" step="0.5"`)).join('')}</div><p class="tiny muted">Flight numbers are optional product facts. Blank means unknown, not zero.</p><div class="button-row">${button('Another specimen', 'disc-duplicate', {}, 'quiet')}${button('Remove disc', 'disc-remove', {}, 'quiet danger')}</div></section><div class="subtle-box"><span class="eyebrow">PRESENTATION IS SEPARATE</span><p>Want a bigger photo or a different layout?</p>${button('Open Component Editor ↗', 'go-editor', {}, 'wide secondary')}</div></aside>`;
}
function coursePreview(result, editor = false) {
  const background = ui.footage ? (ui.footageKind === 'video' ? `<video id="footage-video" src="${esc(ui.footage)}" muted playsinline preload="metadata"></video>` : `<img src="${esc(ui.footage)}" alt="Your local footage context">`) : `<div class="footage-placeholder"><span class="empty-disc">◌</span><h2>The flight gets the screen.</h2><p>Your discs get the credit.</p>${button('+ Try your footage behind the graphic', 'footage', {}, 'quiet')}</div>`;
  return `<div class="preview-frame"><div class="preview-meta"><span><i class="status-dot"></i> ${editor ? 'COMPOSITION PREVIEW' : 'LIVE PREVIEW'} <small>1920 × 1080</small></span><div>${ui.footage ? button('Clear', 'footage-clear', {}, 'quiet small') : ''}${button(ui.footage ? 'Replace footage ↗' : '+ Your footage', 'footage', {}, 'quiet small')}${ui.footageKind === 'video' ? button('Play / pause', 'footage-play', {}, 'quiet small') : ''}</div></div><div class="course-stage checker"><div class="footage-layer">${background}</div><div class="overlay-layer" id="actual-preview">${result.svg}</div></div><div class="preview-meta bottom"><span>${ui.footageName ? `${esc(ui.footageName)} · context only, never exported` : 'Transparent overlay · add your still or video for context'}</span><span>${result.cardCount} card${result.cardCount === 1 ? '' : 's'}</span></div></div>`;
}
function modeTabs() { return `<div class="segmented">${button('Single Disc', 'mode', { value: 'card' }, ui.mode === 'card' ? 'active' : '')}${button('DiscBattle', 'mode', { value: 'battle' }, ui.mode === 'battle' ? 'active' : '')}</div>`; }
function courseCenter(result) {
  const battle = w().battle, state = currentBattle(w());
  return `<section class="center course-center" data-scroll="center"><div class="section-heading compact"><div><span class="eyebrow">ON THE COURSE</span><h1>Your discs. Your screen.</h1></div>${modeTabs()}</div>${coursePreview(result)}<div class="pxc-strip"><span class="mono">${result.part}</span><span>${result.run.computed} computed · ${result.run.reused} reused</span>${button('Inspect PxC ↗', 'toggle-trace', {}, 'quiet small')}</div>${ui.mode === 'battle' ? `<div class="section-toolbar"><div><h2>On screen <small>${battle.entries.length} / 12</small></h2><p class="tiny muted">Edit scores. Highlight any disc. Mark your winner.</p></div>${button('Clear highlight', 'highlight', { id: '' }, 'quiet')}${button('Clear lineup', 'lineup-clear', {}, 'quiet danger')}</div><div class="lineup">${battle.entries.map((entry, index) => {
    const { disc, mold } = discInfo(entry.discId); return `<div class="lineup-entry ${state.highlight === entry.id ? 'highlighted' : ''}"><button class="lineup-disc" data-action="disc-select" data-id="${esc(entry.discId)}"><span class="disc-thumb">${safeThumb(entry.discId)}</span><span><strong>${esc(mold?.name || 'Missing disc')}</strong><small>${esc(disc?.nickname)}</small></span></button><div class="score-stepper">${button('−', 'score-step', { id: entry.id, value: -1 }, '', `aria-label="Decrease score: ${esc(disc?.nickname)}"`)}<input aria-label="Score: ${esc(disc?.nickname)}" data-control="score" data-id="${esc(entry.id)}" type="number" value="${state.scores[entry.id] ?? ''}" placeholder="—">${button('+', 'score-step', { id: entry.id, value: 1 }, '', `aria-label="Increase score: ${esc(disc?.nickname)}"`)}</div>${button('Highlight', 'highlight', { id: state.highlight === entry.id ? '' : entry.id }, state.highlight === entry.id ? 'active' : '', `aria-pressed="${state.highlight === entry.id}"`)}${button('★', 'winner', { id: entry.id }, state.winners.includes(entry.id) ? 'active' : '', `aria-label="Mark winner: ${esc(disc?.nickname)}" aria-pressed="${state.winners.includes(entry.id)}"`)}<div class="ordering">${button('↑', 'lineup-move', { id: entry.id, value: -1 }, 'quiet', `aria-label="Move participant up" ${index === 0 ? 'disabled' : ''}`)}${button('↓', 'lineup-move', { id: entry.id, value: 1 }, 'quiet', `aria-label="Move participant down" ${index === battle.entries.length - 1 ? 'disabled' : ''}`)}</div>${button('×', 'lineup-remove', { id: entry.id }, 'quiet', `aria-label="Remove participant: ${esc(disc?.nickname)}"`)}</div>`;
  }).join('') || '<div class="empty-note">Add physical discs from the shelf to start a comparison.</div>'}</div><section class="states-section"><div class="section-toolbar"><div><span class="eyebrow">ONE COMPARISON. MANY STATES.</span><h2>The next moment.</h2></div>${button('+ Duplicate current state', 'state-add', {}, 'secondary')}</div><div class="state-tabs">${battle.states.map((s, i) => button(`<small>${String(i + 1).padStart(2, '0')}</small> ${esc(s.name)}`, 'state-select', { id: s.id }, s.id === state.id ? 'active' : '')).join('')}</div><div class="button-row">${button('Rename current', 'state-rename', {}, 'quiet small')}${button('Delete current', 'state-remove', {}, 'quiet small danger')}${button('Export SVG state bundle ↓', 'states-export', {}, 'quiet small')}</div><p class="tiny muted">States are editable snapshots. PNG exports are still images; the motion preview is not a video export.</p></section>` : '<div class="principle-strip"><span>A SINGLE DISC IS THE SAME PRIMITIVE.</span><p>The selected shelf disc uses exactly the same saved presentation as your comparison.</p></div>'}${tracePanel(result.run)}</section>`;
}
function layoutControls() {
  const l = w().layout;
  return `<section class="control-section"><h3>DiscComp arrangement <span>VIEW</span></h3><label class="control"><span>Layout</span>${select('arrangement', l.arrangement, [['row', 'Across the screen'], ['stack', 'Down the screen'], ['grid', 'Two-column grid']])}</label><label class="control"><span>Place on screen</span></label><div class="anchor-pad">${[['top-left', '↖'], ['center', '◎'], ['top-right', '↗'], ['bottom-left', '↙'], ['bottom-right', '↘']].map(([value, label]) => button(label, 'anchor', { value }, l.anchor === value ? 'active' : '', `aria-label="Place ${value}"`)).join('')}</div>${input('Overlay scale', 'scale', l.scale, 'range', 'min="0.25" max="2" step="0.05"')}<span class="tiny muted">${Math.round(l.scale * 100)}% requested · always fitted inside frame</span>${input('Gap between cards (px)', 'gap', l.gap, 'number', 'min="0" max="100"')}</section>`;
}
function courseInspector() {
  const { disc, mold, maker } = discInfo();
  return `<aside class="inspector" data-scroll="inspector"><span class="eyebrow">COMPOSE & CUSTOMIZE</span><h2>Make it your own.</h2><section class="export-section">${button(ui.busy ? 'Preparing export…' : 'Save overlay PNG ↓', 'export-png', {}, 'primary wide', ui.busy ? 'disabled' : '')}${button('Save editable SVG ↓', 'export-svg', {}, 'wide quiet')}<p class="tiny muted">Transparent 1920 × 1080. The actual PxC-produced scene. No footage, editor outlines or motion baked in.</p>${ui.latestReceipt ? `<p class="tiny mono">PNG SHA-256<br>${esc(ui.latestReceipt.pngHash.slice(0, 24))}…</p>` : ''}</section><section class="control-section"><label class="control"><span>Shared DisplayCard design</span>${select('course-preset', w().layout.presetId, Object.values(w().presets).filter(p => p.kind === 'DisplayCard').map(p => [p.id, p.name]))}</label>${button('Edit this design ↗', 'go-editor', {}, 'wide secondary')}<p class="tiny muted">Photo, manufacturer, mold, every field. No fixed identity text hiding outside your design.</p></section>${layoutControls()}<section class="control-section"><h3>Selected physical disc <span>DOMAIN</span></h3><div class="selected-summary"><span class="disc-thumb">${disc ? safeThumb(disc.id) : ''}</span><div><strong>${esc(mold?.name || 'None')}</strong><small>${esc(maker?.name)}</small></div></div><p class="tiny muted">${esc(disc?.nickname || '')}</p>${button('Edit facts & exact photo ↗', 'go-shelf', {}, 'wide')}</section><div class="subtle-box"><span class="eyebrow">PLAY BY YOUR RULES</span><p>Compose PutterWarz from reusable constraints.</p>${button('Open competition sandbox ↗', 'go-competition', {}, 'quiet small')}</div></aside>`;
}
function componentTabs() { return `<div class="component-tabs">${[['DiscImage', 'Disc'], ['DisplayCard', 'DisplayCard'], ['DiscComp', 'DiscComp'], ['Competition', 'Competition']].map(([value, label]) => button(label, 'component', { value }, (ui.route === 'competition' ? value === 'Competition' : ui.component === value) ? 'active' : '')).join('')}</div>`; }
function componentSidebar(result) {
  const p = w().presets[ui.presetId], fields = result?.fields ?? [];
  const query = ui.fieldQuery.toLowerCase(), matching = fields.filter(f => `${f.label} ${f.group} ${f.path}`.toLowerCase().includes(query));
  const groups = Object.groupBy(matching, f => f.group);
  return `<aside class="sidebar component-sidebar" data-scroll="library"><span class="eyebrow">PxC COMPONENT LIBRARY</span><h2>Build with your material.</h2><label class="control"><span>Presentation</span>${select('edit-preset', ui.presetId, Object.values(w().presets).map(p => [p.id, p.name]))}</label><div class="button-row">${button('Duplicate', 'preset-duplicate', {}, 'quiet small')}${button('Import', 'preset-import', {}, 'quiet small')}${button('Export ↓', 'preset-export', {}, 'quiet small')}</div><div class="segmented library-tabs">${button('All fields', 'library', { value: 'fields' }, ui.library === 'fields' ? 'active' : '')}${button(`Layers · ${p?.nodes.length || 0}`, 'library', { value: 'layers' }, ui.library === 'layers' ? 'active' : '')}</div>${ui.library === 'layers' ? `<div class="layer-list">${(p?.nodes || []).map(n => `<div class="layer-item ${ui.nodeId === n.id ? 'selected' : ''}">${button(`${n.kind === 'image' ? '▧' : 'T'} <span>${esc(fields.find(f => f.path === n.binding)?.label || n.binding || 'Static text')}</span>`, 'node-select', { id: n.id }, 'layer-select')}${button(n.visible ? '◉' : '○', 'node-visible', { id: n.id }, 'quiet', `aria-label="${n.visible ? 'Hide' : 'Show'} ${esc(n.binding)}"`)}</div>`).join('')}</div>` : `<input class="search" data-search="fields" aria-label="Find any field" placeholder="⌕  Name, maker, score, weight…" value="${esc(ui.fieldQuery)}"><p class="tiny muted field-help">Every registered field, including missing values. Click to place or select it.</p><div class="field-groups">${Object.entries(groups).map(([group, fs]) => `<section class="field-group"><h3>${esc(group)}</h3>${fs.map(f => { const present = p?.nodes.find(n => n.binding === f.path); return `<button class="field-item ${present?.id === ui.nodeId ? 'selected' : ''}" data-action="field-add" data-path="${esc(f.path)}" title="${esc(f.path)}"><span class="field-icon">${f.type === 'image' ? '▧' : f.type === 'number' ? '#' : f.type === 'boolean' ? '◉' : 'T'}</span><span><strong>${esc(f.label)}</strong><small>${f.type === 'image' ? f.available ? 'Your local photo' : 'Sample · no photo yet' : f.available ? esc(String(Array.isArray(f.value) ? `${f.value.length} references` : f.value).slice(0, 35)) : 'Not entered · still available'}</small></span><span class="field-add">${present ? '✓' : '+'}</span></button>`; }).join('')}</section>`).join('')}</div>${button('+ Register a domain field', 'field-new', {}, 'wide secondary small')}<p class="tiny muted">One definition → fact inspector + field picker + bound graphic.</p>`}<div class="sidebar-footer"><label class="control"><span>Additional object context</span>${select('extra-type', ui.extraType, [['', 'Disc, Bag, Competition & Round'], ...Object.keys(w().schemas).filter(t => t !== 'BattleEntry').map(t => [t, t])])}</label>${ui.extraType ? select('extra-id', ui.extraId, all(w(), ui.extraType).map(o => [o.id, o.name || o.nickname || o.id])) : ''}</div></aside>`;
}
function editorCenter(result) {
  const p = w().presets[ui.presetId];
  const sceneMode = ui.component === 'DiscComp';
  return `<section class="center editor-center" data-scroll="center"><div class="section-heading"><div><span class="eyebrow">DESIGN SANDBOX · ACTUAL PRODUCT COMPONENTS</span><h1>A little more you.</h1><p>Arrange the material. Save the look. Use it everywhere.</p></div>${button('See it OnTheCourse ↗', 'go-course', {}, 'primary')}</div>${componentTabs()}${sceneMode ? coursePreview(result, true) : `<div class="editor-toolbar"><label class="inline-control">Specimen ${select('editor-disc', ui.discId, all(w(), 'Disc').map(d => [d.id, d.nickname]))}</label><div class="segmented">${['idle', 'highlight', 'winner'].map(value => button(value[0].toUpperCase() + value.slice(1), 'preview-state', { value }, ui.previewState === value ? 'active' : '')).join('')}</div></div><div class="editor-stage"><div class="editor-stage-label"><span class="eyebrow">LIVE BOUND COMPOSITION</span><span class="mono tiny">${p.width} × ${p.height} px</span></div><div class="editor-card" style="aspect-ratio:${p.width}/${p.height};width:min(100%,${p.width * (p.height > p.width ? 1 : 1.4)}px)">${result.svg}<svg class="selection-overlay" viewBox="0 0 ${p.width} ${p.height}" aria-label="Select and drag presentation elements">${result.card.nodes.map(n => `<rect data-node-select="${esc(n.id)}" x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" rx="2" class="${ui.nodeId === n.id ? 'selected-node' : ''}"/>`).join('')}</svg></div><div class="editor-stage-footer"><span>Click a piece to inspect it. Drag to move. Arrow keys nudge; Shift moves 10 px.</span><span>Editor outlines are never exported.</span></div></div>`}<div class="pxc-strip"><span class="mono">${esc(result.part)}</span><span>${result.run.computed} computed · ${result.run.reused} reused</span>${button('Inspect PxC ↗', 'toggle-trace', {}, 'quiet small')}</div>${result.card?.warnings.length || result.warnings?.length ? `<div class="warning-panel">${(result.card?.warnings || result.warnings).map(esc).join('<br>')}</div>` : ''}${ui.newField ? `<section class="new-field-panel"><h2>Define it once.</h2><p>A new physical-disc field becomes available in the Shelf inspector and in every presentation.</p><div class="form-row">${input('Field label', 'new-field-label', '', 'text', 'id="new-field-label"')}${select('new-field-type', 'text', [['text', 'Text'], ['number', 'Number'], ['boolean', 'Yes / no']])}${button('Register field', 'field-register', {}, 'primary')}${button('Cancel', 'field-new', {}, 'quiet')}</div></section>` : ''}<div class="principle-strip"><span>NOT A SECOND RENDERER.</span><p>This is the same card composition used by your OnTheCourse preview and exported graphic.</p></div>${tracePanel(result.run)}</section>`;
}
function nodeInspector(result) {
  if (ui.component === 'DiscComp') return `<aside class="inspector" data-scroll="inspector"><span class="eyebrow">COMPOSE DISPLAYCARDS</span><h2>DiscComp</h2><p class="muted">A comparison is an arrangement of the same reusable cards, not a parallel card renderer.</p>${layoutControls()}${button('Edit participants & scores ↗', 'go-course', {}, 'wide secondary')}${button('Compose competition rules ↗', 'go-competition', {}, 'wide quiet')}</aside>`;
  const p = w().presets[ui.presetId], n = p.nodes.find(n => n.id === ui.nodeId), field = result.fields.find(f => f.path === n?.binding);
  return `<aside class="inspector" data-scroll="inspector"><div class="inspector-title"><span class="eyebrow">INSPECT & COMPOSE</span><span class="live-tag">LIVE</span></div><h2>${esc(n ? field?.label || 'Presentation element' : 'Select a component')}</h2>${n ? `<p class="binding-path mono">${esc(n.binding || 'Static text')}</p><section class="control-section"><label class="control"><span>Bind to domain material</span>${select('node-binding', n.binding, [['', 'Static text'], ...result.fields.filter(f => (n.kind === 'image') === (f.type === 'image')).map(f => [f.path, `${f.group} · ${f.label}`])])}</label>${!n.binding ? input('Static text', 'node-text', n.text || '') : `<div class="value-box"><span class="eyebrow">CURRENT VALUE</span><strong>${n.kind === 'image' ? field?.available ? 'Your exact photo' : 'Labelled sample artwork' : esc(field?.value == null ? 'Not entered' : String(field.value))}</strong></div>`}<div class="four-inputs two">${[['X', 'x'], ['Y', 'y'], ['Width', 'w'], ['Height', 'h']].map(([label, key]) => input(label, 'node-number', n[key], 'number', `data-key="${key}" step="1"`)).join('')}</div>${n.kind === 'text' ? `${input('Type size (px)', 'node-number', n.size, 'number', 'data-key="size" min="4" max="200"')}<label class="control"><span>Typeface</span>${select('node-font', n.font || 'sans', [['sans', 'Clean sans'], ['serif', 'Editorial serif'], ['mono', 'Monospace']])}</label><label class="control"><span>Alignment</span>${select('node-align', n.align, [['left', 'Left'], ['center', 'Center'], ['right', 'Right']])}</label>${input('Text color', 'node-color', n.color || p.foreground, 'color')}${check('Bold', 'node-bold', n.bold)}${check('Show field label', 'node-showLabel', n.showLabel)}${check('Hide when empty', 'node-hideEmpty', n.hideEmpty)}${input('Prefix', 'node-prefix', n.prefix || '')}${input('Suffix', 'node-suffix', n.suffix || '')}` : `<label class="control"><span>Image fit</span>${select('node-fit', n.fit || 'contain', [['contain', 'Contain · preserve all'], ['cover', 'Cover · crop to frame']])}</label>${input('Corner radius', 'node-number', n.radius || 0, 'number', 'data-key="radius" min="0"')}`}${check('Visible in presentation', 'node-visible', n.visible)}<div class="button-row">${button('Move back', 'node-move', { value: -1 }, 'quiet small')}${button('Move front', 'node-move', { value: 1 }, 'quiet small')}</div><div class="button-row">${button('Duplicate element', 'node-duplicate', {}, 'quiet small')}${button('Remove', 'node-remove', {}, 'quiet danger small')}</div></section>` : '<p class="muted">Choose a field on the left or a piece of the graphic. Its binding and presentation become editable here.</p>'}<section class="control-section"><h3>The whole card <span>PRESET</span></h3>${input('Design name', 'preset-name', p.name)}<div class="four-inputs two">${input('Card width', 'preset-number', p.width, 'number', 'data-key="width" min="100" max="2000"')}${input('Card height', 'preset-number', p.height, 'number', 'data-key="height" min="100" max="2000"')}</div>${input('Card background', 'preset-color', p.background === 'transparent' ? '#ffffff' : p.background, 'color', 'data-key="background"')}${check('Transparent card background', 'preset-transparent', p.background === 'transparent')}${input('Default text', 'preset-color', p.foreground, 'color', 'data-key="foreground"')}${input('Accent', 'preset-color', p.accent, 'color', 'data-key="accent"')}${input('Card corner radius', 'preset-number', p.radius, 'number', 'data-key="radius" min="0" max="100"')}</section><section class="control-section"><h3>State treatments <span>REUSABLE</span></h3><label class="control"><span>Highlight</span>${select('preset-highlight', p.highlight, [['ring', 'Accent ring'], ['stripe', 'Accent stripe']])}</label><label class="control"><span>Score-change preview</span>${select('preset-motion', p.scoreMotion, [['pulse', 'Small pulse'], ['none', 'No animation']])}</label>${input('Motion duration (ms)', 'preset-number', p.duration, 'number', 'data-key="duration" min="100" max="1500"')}<p class="tiny muted">Motion respects reduced-motion preferences. Exports are static states.</p></section></aside>`;
}
function competitionSidebar() {
  const comp = get(w(), 'Competition', ui.competitionId);
  return `<aside class="sidebar" data-scroll="library"><span class="eyebrow">REUSABLE COMPOSITIONS</span><h2>Competitions</h2><label class="control"><span>Competition</span>${select('competition', ui.competitionId, all(w(), 'Competition').map(c => [c.id, c.name]))}</label>${button('Duplicate competition', 'competition-duplicate', {}, 'wide quiet')}<p class="tiny muted">Duplicates reuse team and round references. Constraints are copied and independently editable.</p><section class="control-section"><h3>Constraint library</h3>${Object.entries(constraintDefinitions).map(([key, def]) => `<div class="constraint-library-item"><span class="eyebrow">${esc(def.call)}</span><strong>${esc(def.label)}</strong><p>${esc(def.description)}</p>${button('+ Add to competition', 'constraint-add', { value: key }, 'wide small')}</div>`).join('')}</section>${button('Export rule composition ↓', 'competition-export', {}, 'wide secondary')}<p class="tiny muted">A rule composition contains named Constraints and their parameters, not generated code.</p></aside>`;
}
function competitionCenter(result) {
  const comp = get(w(), 'Competition', ui.competitionId), round = get(w(), 'Round', ui.roundId);
  return `<section class="center competition-center" data-scroll="center"><div class="section-heading"><div><span class="eyebrow">COMPETITION = REUSABLE CONSTRAINTS</span><h1>${esc(comp.name)}</h1><p>Compose the rules. Inspect the actual objects they apply to.</p></div><span class="result-status ${result.status}">${result.status === 'pending' ? 'In progress' : esc(result.status)}</span></div>${componentTabs()}<div class="rules-toolbar"><span class="mono">Competition[Constraint]</span><label class="inline-control">Composition ${select('constraint-combine', comp.combine, [['all', 'All rules (AND)'], ['any', 'Any rule (OR)']])}</label></div><div class="rule-cards">${comp.constraints.map(rule => {
    const def = constraintDefinitions[rule.kind], outcome = result.rules.find(r => r.id === rule.id);
    return `<article class="rule-card"><div class="rule-card-heading"><label class="check"><input type="checkbox" data-control="constraint-enabled" data-id="${esc(rule.id)}" ${rule.enabled ? 'checked' : ''}><strong>${esc(def?.label || rule.kind)}</strong></label><span class="result-status ${outcome?.status || 'disabled'}">${outcome?.status || 'disabled'}</span></div><p>${esc(def?.description || 'Unknown constraint')}</p><div class="rule-parameter">${rule.kind !== 'oneMold' ? `<input type="number" min="1" max="100" data-control="constraint-value" data-id="${esc(rule.id)}" aria-label="${esc(def?.unit)}" value="${rule.value}">` : '<strong>1</strong>'}<span>${esc(def?.unit)}</span>${button('Remove rule', 'constraint-remove', { id: rule.id }, 'quiet small danger')}</div>${outcome ? `<ul class="rule-results">${outcome.details.map(d => `<li><span class="result-dot ${d.status}"></span><strong>${esc(d.subject)}</strong><span>${esc(d.message)}</span></li>`).join('')}</ul>` : '<p class="tiny muted">Disabled rules are not executed.</p>'}<span class="mono tiny">px.constraint.${esc(rule.id)}.result</span></article>`;
  }).join('')}</div><section class="round-section"><div class="section-toolbar"><div><span class="eyebrow">RECORDED USE, NOT INVENTED STATS</span><h2>Round / hole</h2></div>${select('round', ui.roundId, comp.roundIds.map(id => [id, get(w(), 'Round', id)?.name || 'Missing round']))}${button('+ Add round', 'round-add', {}, 'secondary')}</div>${round ? `${check('This round is complete', 'round-complete', round.complete)}<p class="tiny muted">Fewer than the required throws stays pending until you complete the round. Too many fails immediately.</p><div class="team-grid">${comp.teamIds.map(key => {
    const team = get(w(), 'Team', key), bag = team && get(w(), 'Bag', team.bagId), throws = all(w(), 'Throw').filter(t => t.teamId === key && t.roundId === ui.roundId);
    return `<article class="team-card"><span class="eyebrow">${esc(bag?.name || 'Missing bag')}</span><h3>${esc(team?.name || 'Missing team')}</h3><p>${throws.length} recorded throws</p><label class="control"><span>Throw a disc from this team’s bag</span><select data-team-disc="${esc(key)}" aria-label="Disc to throw: ${esc(team?.name)}">${(bag?.discIds || []).map(id => `<option value="${esc(id)}">${esc(get(w(), 'Disc', id)?.nickname || 'Missing disc')}</option>`).join('')}</select></label>${button('+ Record throw', 'throw-record', { id: key }, 'wide secondary')}<div class="throw-list">${throws.map(t => `<div><span>${esc(get(w(), 'Disc', t.discId)?.nickname || 'Missing disc')}</span>${button('×', 'throw-remove', { id: t.id }, 'quiet small', 'aria-label="Remove recorded throw"')}</div>`).join('')}</div></article>`;
  }).join('')}</div>` : '<p class="error-panel">Round reference is missing.</p>'}</section><div class="principle-strip"><span>RULES DO NOT INVENT A WINNER.</span><p>These checks validate your setup and recorded use. Scores and winners on the graphic remain explicitly authored.</p></div>${tracePanel(result.run)}</section>`;
}
function competitionInspector() {
  const comp = get(w(), 'Competition', ui.competitionId);
  return `<aside class="inspector" data-scroll="inspector"><span class="eyebrow">COMPETITION OBJECTS</span><h2>Teams & bags</h2>${input('Competition name', 'competition-name', comp.name)}${comp.teamIds.map(key => { const team = get(w(), 'Team', key); return `<section class="control-section">${input('Team name', 'team-name', team?.name, 'text', `data-id="${esc(key)}"`)}<label class="control"><span>Referenced bag</span>${select('team-bag', team?.bagId, all(w(), 'Bag').map(b => [b.id, b.name]), `data-id="${esc(key)}"`)}</label>${button('Edit this bag ↗', 'team-bag-open', { id: team?.bagId }, 'wide quiet')}</section>`; }).join('')}${button('Use these discs OnTheCourse ↗', 'competition-course', {}, 'wide primary')}<p class="tiny muted">Adds the team bags’ physical discs to your current comparison. It does not infer points or replace authored states.</p><div class="subtle-box"><span class="eyebrow">LOCAL INSTRUMENTATION</span><p>${w().events.length} recorded edits<br>${w().exports.length} actual PNG exports<br>${all(w(), 'Throw').length} recorded throws</p>${button('Export local activity ↓', 'activity-export', {}, 'quiet small')}<p class="tiny muted">Nothing is transmitted. Sample objects are not usage, sales, reach or performance evidence.</p></div></aside>`;
}
function summaryValue(value) { return JSON.stringify(value, (key, v) => key === 'signature' ? '[full input signature retained in PxC; omitted here]' : typeof v === 'string' && v.startsWith('data:image/') ? `[embedded photo: ${v.length} characters]` : key === 'svg' && typeof v === 'string' && v.length > 1000 ? `${v.slice(0, 600)}… [${v.length} characters, full value in Part]` : v, 2); }
function tracePanel(run) {
  if (!run) return '';
  return `<section class="trace-panel ${ui.traceOpen ? 'open' : ''}"><button class="trace-heading" data-action="toggle-trace"><span>◎ <strong>PxC · actual execution</strong></span><span>${run.computed} computed / ${run.reused} reused <b>${ui.traceOpen ? '−' : '+'}</b></span></button>${ui.traceOpen ? `<div class="trace-flow"><span>Domain Parts</span><b>→</b><span>Registered Calculations</span><b>→</b><span>Bound presentation</span><b>→</b><span>SVG Part</span></div><div class="trace-table"><div class="trace-row table-heading"><span>Calculation</span><span>Output Part</span><span>This invocation</span></div>${run.trace.map(t => `<div class="trace-row"><span class="mono" title="${esc(Object.values(t.inputs).join('\n'))}">${esc(t.call)}</span>${button(esc(t.output), 'inspect-part', { value: t.output }, 'part-link mono')}<span class="cache-state ${t.reused ? 'reused' : ''}">${t.reused ? '↺ reused material' : '● computed'}</span></div>`).join('')}</div><div class="button-row">${button('Inspect PQL composition', 'inspect-pql', {}, 'quiet small')}${button('Browse all Parts', 'inspect-all', {}, 'quiet small')}${button('Download this execution receipt ↓', 'trace-export', {}, 'quiet small')}${button('Export run record ↓', 'record-export', {}, 'quiet small')}${button('Open Tick render ↗', 'record-render', {}, 'quiet small')}</div>${ui.inspectAddress ? `<div class="part-view"><h3>${esc(ui.inspectAddress)}</h3><pre>${esc(ui.inspectAddress === 'PQL' ? JSON.stringify(run.composition, null, 2) : ui.inspectAddress === 'Part index' ? runtime.parts().map(p => p.address).join('\n') : runtime.pxc.has(ui.inspectAddress) ? summaryValue(runtime.pxc.get(ui.inspectAddress)) : 'Part no longer exists in this context.')}</pre></div>` : ''}<p class="tiny muted">Cache hits return retained material from PxC. Each invocation is still recorded. A hit is not a claim that the calculation ran again.</p>` : ''}</section>`;
}
let renderedRoute = null;
function render() {
  const active = document.activeElement;
  const focus = active?.closest('#app') ? { control: active.dataset.control, search: active.dataset.search, label: active.getAttribute('aria-label'), start: active.selectionStart, end: active.selectionEnd } : null;
  const scrolls = Object.fromEntries([...app.querySelectorAll('[data-scroll]')].map(e => [e.dataset.scroll, e.scrollTop]));
  const oldVideo = document.querySelector('#footage-video'), playing = oldVideo && !oldVideo.paused;
  if (oldVideo) ui.footageTime = oldVideo.currentTime;
  let body;
  try {
    if (!get(w(), 'Disc', ui.discId)) ui.discId = all(w(), 'Disc')[0]?.id;
    if (!get(w(), 'Bag', ui.bagId)) ui.bagId = all(w(), 'Bag')[0]?.id;
    if (!w().presets[ui.presetId]) ui.presetId = w().layout.presetId;
    if (ui.route === 'shelf') {
      ui.lastResult = ui.discId ? runtime.card(ui.discId, 'discImage', context()) : null;
      body = `${shelfSidebar()}${shelfCenter()}${discInspector()}`;
    } else if (ui.route === 'course') {
      ui.lastResult = runtime.scene({ mode: ui.mode, discId: ui.discId, ...context() });
      body = `${shelfSidebar()}${courseCenter(ui.lastResult)}${courseInspector()}`;
    } else if (ui.route === 'components') {
      let result;
      if (ui.component === 'DiscComp') result = { ...runtime.scene({ mode: 'battle', ...context() }), fields: runtime.card(ui.discId, ui.presetId, context(), previewEntry()).fields };
      else result = runtime.card(ui.discId, ui.presetId, context(), previewEntry());
      ui.lastResult = result;
      body = `${componentSidebar(result)}${editorCenter(result)}${nodeInspector(result)}`;
    } else {
      ui.lastResult = runtime.constraints(ui.competitionId);
      body = `${competitionSidebar()}${competitionCenter(ui.lastResult)}${competitionInspector()}`;
    }
  } catch (error) {
    body = `<section class="full-error"><span class="eyebrow">VISIBLE MODEL BOUNDARY</span><h1>This composition cannot resolve.</h1><p>${esc(error.cause?.message || error.message)}</p><p>No missing participant was silently removed and no draft was overwritten by this render.</p><div class="button-row">${button('Open Shelf', 'go-shelf', {}, 'primary')}${button('Download current draft', 'save-draft', {}, 'secondary')}${button('Load a valid draft', 'load-draft', {}, 'secondary')}</div></section>`;
  }
  app.innerHTML = `${header()}${ui.message ? `<div class="notice ${ui.error ? 'error' : ''}" role="${ui.error ? 'alert' : 'status'}"><span>${esc(ui.message)}</span>${!saveEnabled ? button('Download protected saved file', 'save-protected', {}, 'quiet small') : ''}${button('×', 'dismiss', {}, 'quiet', 'aria-label="Dismiss message"')}</div>` : ''}<main class="workspace ${ui.route}" id="main">${body}</main><footer class="app-footer"><span>LOCAL-FIRST · NO ACCOUNT · NO DATA SENT</span><span>Concept B visual language · ChainSpot PxC execution · ${esc(ui.build.commit.slice(0, 8))}</span></footer>`;
  for (const e of app.querySelectorAll('[data-scroll]')) e.scrollTop = renderedRoute === ui.route ? scrolls[e.dataset.scroll] ?? 0 : 0;
  renderedRoute = ui.route;
  if (focus) {
    const target = [...app.querySelectorAll('input,select,textarea')].find(e => (focus.search ? e.dataset.search === focus.search : e.dataset.control === focus.control && e.getAttribute('aria-label') === focus.label));
    if (target) { target.focus({ preventScroll: true }); try { if (focus.start != null) target.setSelectionRange(focus.start, focus.end); } catch { /* Number/range controls have no selection. */ } }
  }
  const video = document.querySelector('#footage-video');
  if (video) video.addEventListener('loadedmetadata', () => { video.currentTime = Math.min(ui.footageTime, video.duration || 0); if (playing) video.play().catch(() => {}); }, { once: true });
  if (ui.motionEntry && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const node = [...app.querySelectorAll('#actual-preview [data-entry]')].find(e => e.dataset.entry === ui.motionEntry);
    if (node && node.dataset.motion !== 'none') node.animate([{ opacity: .45 }, { opacity: 1 }], { duration: Math.max(100, Math.min(1500, +node.dataset.duration || 350)) });
  }
  ui.motionEntry = null;
  const review = document.querySelector('neat-review');
  review.getContext = () => ({ route: location.hash, discId: ui.discId, bagId: ui.bagId, presetId: ui.presetId, nodeId: ui.nodeId, stateId: w().battle.currentStateId, runRecordAddress: ui.recordAddress || null, worldLabel: labelHash({ objects: w().objects, presets: w().presets, battle: w().battle }) });
}
function freshDisc() {
  if (!get(w(), 'Manufacturer', 'unknown')) execute({ type: 'entity.add', record: { id: 'unknown', type: 'Manufacturer', name: 'Unknown manufacturer', website: '' } });
  if (!get(w(), 'Mold', 'unreleased')) execute({ type: 'entity.add', record: { id: 'unreleased', type: 'Mold', name: 'Unreleased / unknown', manufacturerId: 'unknown', category: '', flight: {} } });
  const key = id('disc'); execute({ type: 'entity.add', record: { id: key, type: 'Disc', moldId: 'unreleased', nickname: 'My new disc', photo: null, plastic: '', weight: null, color: '', notes: '' } }); ui.discId = key;
  message('New physical disc added. Give it its product identity and exact photo in the inspector.');
}
function addLineup(discId) { if (!w().battle.entries.some(e => e.discId === discId)) execute({ type: 'battle.add', discId, id: id('entry') }); }
async function exportPng() {
  const result = runtime.scene({ mode: ui.mode, discId: ui.discId, ...context() });
  if (!result.cardCount) throw new Error('Add at least one disc before exporting.');
  // Capture the exact scene and source data BEFORE async conversion; later edits cannot relabel the export.
  const mode = ui.mode;
  const sourceSnapshot = clone({ layout: w().layout, preset: w().presets[w().layout.presetId], state: currentBattle(w()), entryDiscIds: mode === 'card' ? [ui.discId] : w().battle.entries.map(e => e.discId), objects: {} });
  // Retain immutable facts and asset hashes, not another complete copy of every local photo per export.
  for (const discId of sourceSnapshot.entryDiscIds) {
    const disc = clone(get(w(), 'Disc', discId)), mold = clone(get(w(), 'Mold', disc.moldId)), maker = clone(get(w(), 'Manufacturer', mold.manufacturerId));
    sourceSnapshot.objects[discId] = { disc, mold, maker };
  }
  ui.busy = true; render();
  try {
    const blob = await pngFromSvg(result.svg), pngHash = await sha256(blob), svgHash = await sha256(result.svg);
    for (const item of Object.values(sourceSnapshot.objects)) if (item.disc.photo) { item.disc.photoSha256 = await sha256(item.disc.photo); delete item.disc.photo; }
    sourceSnapshot.assetPolicy = 'Photo data-URL hashes retained; original photo bytes remain in the draft, not duplicated per export. Keep exported SVGs for self-contained graphics.';
    const record = { id: id('export'), type: 'PNG', time: new Date().toISOString(), stateId: result.stateId, mode, pngHash, svgHash, width: 1920, height: 1080, sourceSnapshot, byteLength: blob.size };
    execute({ type: 'export.record', record }); ui.latestReceipt = record;
    downloadBlob(blob, `discstudio-${result.stateId}-${svgHash.slice(0, 8)}.png`); message('PNG exported from the actual SVG Part. Footage and editor controls are excluded.');
  } finally { ui.busy = false; }
}
async function action(name, el) {
  const d = el.dataset, { disc, mold, maker } = discInfo();
  switch (name) {
    case 'go-shelf': navigate('shelf'); return;
    case 'go-course': navigate('course'); return;
    case 'go-competition': navigate('competition'); return;
    case 'go-editor': ui.component = 'DisplayCard'; ui.presetId = w().layout.presetId; navigate('components'); return;
    case 'dismiss': ui.message = ''; break;
    case 'save-draft': downloadJson(w(), 'discstudio-draft.json'); message('Draft downloaded with domain objects, photos, presentations and states.'); break;
    case 'save-protected': downloadBlob(new Blob([localStorage.getItem(DATA_KEY) || ''], { type: 'application/json' }), 'discstudio-protected-original.json'); break;
    case 'load-draft': document.querySelector('#draft-file').click(); return;
    case 'reset': if (confirm('Replace this local workspace with the labelled sample collection? Download a draft first to keep your work. Review comments are not deleted.')) { saveEnabled = true; runtime.replace(createSeed()); ui.discId = 'buzzz-mint'; ui.bagId = 'everyday'; ui.presetId = 'broadcast'; message('Sample workspace restored. Your review comments are unchanged.'); } break;
    case 'disc-select': ui.discId = d.id; break;
    case 'disc-add': freshDisc(); break;
    case 'disc-duplicate': { const key = id('disc'); execute({ type: 'disc.duplicate', id: disc.id, newId: key }); ui.discId = key; break; }
    case 'disc-remove': if (confirm('Remove this physical disc from your shelf? Bag/lineup references must be removed first.')) execute({ type: 'disc.remove', id: disc.id }); break;
    case 'membership': if (!ui.bagId) throw new Error('Create a bag first.'); execute({ type: 'bag.membership', bagId: ui.bagId, discId: d.id, include: !get(w(), 'Bag', ui.bagId).discIds.includes(d.id) }); break;
    case 'bag-add': { const name = prompt('Name this bag', 'New bag'); if (name?.trim()) { const key = id('bag'); execute({ type: 'entity.add', record: { id: key, type: 'Bag', name: name.trim(), discIds: [], notes: '' } }); ui.bagId = key; } break; }
    case 'bag-rename': { const name = prompt('Bag name', get(w(), 'Bag', ui.bagId)?.name || ''); if (name?.trim()) execute({ type: 'entity.set', entityType: 'Bag', id: ui.bagId, path: 'name', value: name.trim() }); break; }
    case 'bag-remove': if (confirm('Delete this bag? Physical discs remain on your shelf.')) execute({ type: 'bag.remove', id: ui.bagId }); break;
    case 'photo': ui.photoDiscId = d.id || ui.discId; document.querySelector('#photo-file').click(); return;
    case 'photo-remove': execute({ type: 'entity.set', entityType: 'Disc', id: ui.discId, path: 'photo', value: null }); break;
    case 'mode': ui.mode = d.value; break;
    case 'lineup-add': addLineup(d.id); break;
    case 'bag-lineup': for (const key of get(w(), 'Bag', ui.bagId)?.discIds || []) addLineup(key); break;
    case 'lineup-remove': execute({ type: 'battle.remove', id: d.id }); break;
    case 'lineup-clear': if (confirm('Clear the comparison lineup and its scores/highlights in every state? Your shelf and bags remain unchanged.')) for (const e of [...w().battle.entries]) execute({ type: 'battle.remove', id: e.id }); break;
    case 'lineup-move': execute({ type: 'battle.move', id: d.id, offset: +d.value }); break;
    case 'score-step': execute({ type: 'battle.score', id: d.id, score: (currentBattle(w()).scores[d.id] ?? 0) + +d.value }); ui.motionEntry = d.id; break;
    case 'highlight': execute({ type: 'battle.highlight', id: d.id }); break;
    case 'winner': execute({ type: 'battle.winner', id: d.id }); break;
    case 'state-add': execute({ type: 'battle.state.save', id: id('state'), name: `State ${w().battle.states.length + 1}` }); break;
    case 'state-select': execute({ type: 'battle.state.select', id: d.id }); break;
    case 'state-rename': { const name = prompt('State name', currentBattle(w()).name); if (name?.trim()) execute({ type: 'battle.state.rename', name: name.trim() }); break; }
    case 'state-remove': if (confirm('Delete the current comparison state?')) execute({ type: 'battle.state.remove', id: w().battle.currentStateId }); break;
    case 'anchor': execute({ type: 'layout.set', patch: { anchor: d.value } }); break;
    case 'footage': document.querySelector('#footage-file').click(); return;
    case 'footage-clear': if (ui.footage) URL.revokeObjectURL(ui.footage); Object.assign(ui, { footage: null, footageKind: null, footageName: '', footageTime: 0 }); break;
    case 'footage-play': { const video = document.querySelector('#footage-video'); if (video) { if (video.paused) await video.play(); else video.pause(); } return; }
    case 'export-png': await exportPng(); break;
    case 'export-svg': { const result = runtime.scene({ mode: ui.mode, discId: ui.discId, ...context() }); downloadBlob(new Blob([result.svg], { type: 'image/svg+xml' }), `discstudio-${result.stateId}.svg`); message('SVG scene downloaded. This is not recorded as a PNG export.'); break; }
    case 'states-export': {
      const files = [];
      for (const [index, state] of w().battle.states.entries()) { const result = runtime.scene({ mode: 'battle', ...context(), stateId: state.id }); files.push({ filename: `${String(index + 1).padStart(2, '0')}-${state.name.replace(/[^a-z0-9_-]+/ig, '-')}.svg`, svg: result.svg, stateId: state.id }); }
      downloadJson({ format: 'DiscStudio SVG state sequence', files }, 'discstudio-state-sequence.json'); message('State sequence exported as JSON containing one SVG per state. Export the selected state as PNG for direct video-editor use.'); break;
    }
    case 'component': ui.component = d.value; if (d.value === 'Competition') { navigate('competition'); return; } if (d.value === 'DiscImage') ui.presetId = 'discImage'; else if (ui.presetId === 'discImage') ui.presetId = w().layout.presetId; if (ui.route !== 'components') { navigate('components'); return; } break;
    case 'library': ui.library = d.value; break;
    case 'node-select': ui.nodeId = d.id; break;
    case 'field-add': {
      const field = ui.lastResult.fields?.find(f => f.path === d.path); if (!field) throw new Error('Field is not available in this context.');
      const p = w().presets[ui.presetId], existing = p.nodes.find(n => n.binding === field.path);
      if (existing) { ui.nodeId = existing.id; if (!existing.visible) execute({ type: 'preset.set', id: p.id, nodeId: existing.id, patch: { visible: true } }); }
      else { const node = { ...fieldNode(field), x: 24, y: Math.max(16, p.height - 60), w: Math.min(240, p.width - 48) }; if (field.path.startsWith('entry.')) node.context = 'battle'; execute({ type: 'preset.node.add', id: p.id, node }); ui.nodeId = node.id; }
      break;
    }
    case 'node-visible': { const node = w().presets[ui.presetId].nodes.find(n => n.id === d.id); execute({ type: 'preset.set', id: ui.presetId, nodeId: d.id, patch: { visible: !node.visible } }); break; }
    case 'node-remove': execute({ type: 'preset.node.remove', id: ui.presetId, nodeId: ui.nodeId }); ui.nodeId = ''; break;
    case 'node-move': execute({ type: 'preset.node.move', id: ui.presetId, nodeId: ui.nodeId, offset: +d.value }); break;
    case 'node-duplicate': { const node = clone(w().presets[ui.presetId].nodes.find(n => n.id === ui.nodeId)); node.id = id('node'); node.x += 8; node.y += 8; execute({ type: 'preset.node.add', id: ui.presetId, node }); ui.nodeId = node.id; break; }
    case 'preview-state': ui.previewState = d.value; break;
    case 'preset-duplicate': { const original = w().presets[ui.presetId], name = prompt('Name your reusable design', `${original.name} · my version`); if (name?.trim()) { const preset = { ...clone(original), id: id('preset'), name: name.trim() }; execute({ type: 'preset.put', preset }); ui.presetId = preset.id; if (preset.kind === 'DisplayCard') execute({ type: 'layout.set', patch: { presetId: preset.id } }); } break; }
    case 'preset-export': downloadJson({ format: 'DiscStudio presentation', version: 1, preset: w().presets[ui.presetId] }, `${ui.presetId}.presentation.json`); message('Reusable design exported. It contains bindings and styling, not the current disc’s data.'); break;
    case 'preset-import': document.querySelector('#preset-file').click(); return;
    case 'field-new': ui.newField = !ui.newField; break;
    case 'field-register': { const label = document.querySelector('#new-field-label').value.trim(), kind = document.querySelector('[data-control="new-field-type"]').value, key = label.replace(/[^a-zA-Z0-9]+(.)/g, (_, c) => c.toUpperCase()).replace(/[^A-Za-z0-9]/g, ''); if (!key || !/^[A-Za-z]/.test(key)) throw new Error('Give the field a name beginning with a letter.'); const name = key[0].toLowerCase() + key.slice(1); execute({ type: 'schema.addField', entityType: 'Disc', name, fieldType: kind, label }); ui.newField = false; ui.fieldQuery = label; message(`${label} is now in the domain inspector and the presentation field library. No renderer code was added.`); break; }
    case 'constraint-add': execute({ type: 'competition.rule.add', id: ui.competitionId, rule: { id: id('rule'), kind: d.value, value: constraintDefinitions[d.value].defaultValue, enabled: true } }); break;
    case 'constraint-remove': execute({ type: 'competition.rule.remove', id: ui.competitionId, ruleId: d.id }); break;
    case 'competition-duplicate': { const comp = clone(get(w(), 'Competition', ui.competitionId)), name = prompt('Competition name', `${comp.name} · my format`); if (name?.trim()) { comp.id = id('competition'); comp.name = name.trim(); execute({ type: 'entity.add', record: comp }); ui.competitionId = comp.id; } break; }
    case 'competition-export': { const { name, combine, constraints } = get(w(), 'Competition', ui.competitionId); downloadJson({ format: 'DiscStudio constraint composition', name, combine, constraints }, 'competition-rules.json'); break; }
    case 'team-bag-open': ui.bagId = d.id; navigate('shelf'); return;
    case 'competition-course': { const comp = get(w(), 'Competition', ui.competitionId); for (const teamId of comp.teamIds) for (const discId of get(w(), 'Bag', get(w(), 'Team', teamId).bagId)?.discIds || []) addLineup(discId); ui.mode = 'battle'; navigate('course'); return; }
    case 'round-add': { const key = id('round'), comp = get(w(), 'Competition', ui.competitionId); execute({ type: 'entity.add', record: { id: key, type: 'Round', name: `Hole ${comp.roundIds.length + 1}`, complete: false } }); execute({ type: 'entity.set', entityType: 'Competition', id: comp.id, path: 'roundIds', value: [...comp.roundIds, key] }); ui.roundId = key; break; }
    case 'throw-record': { const el = [...document.querySelectorAll('[data-team-disc]')].find(e => e.dataset.teamDisc === d.id); if (!el?.value) throw new Error('Put a physical disc in this team’s bag first.'); execute({ type: 'throw.record', id: id('throw'), teamId: d.id, roundId: ui.roundId, discId: el.value }); break; }
    case 'throw-remove': execute({ type: 'throw.remove', id: d.id }); break;
    case 'activity-export': downloadJson({ disclosure: 'Local authored actions, recorded throws and actual PNG exports only. Not market/audience/performance measurements.', events: w().events, throws: all(w(), 'Throw'), exports: w().exports.map(({ sourceSnapshot, ...record }) => record) }, 'discstudio-local-activity.json'); break;
    case 'toggle-trace': ui.traceOpen = !ui.traceOpen; break;
    case 'inspect-part': ui.inspectAddress = d.value; break;
    case 'inspect-pql': ui.inspectAddress = 'PQL'; break;
    case 'inspect-all': ui.inspectAddress = 'Part index'; break;
    case 'trace-export': downloadJson(ui.lastResult?.run, 'discstudio-pql-execution.json'); break;
    case 'record-export': {
      const { address, record } = runtime.runRecord(shownPcr());
      ui.recordAddress = address; ui.inspectAddress = address; ui.traceOpen = true;
      downloadJson(record, `${record.pcr}-run-record.json`);
      message(`pyto-run-record@1 accepted by the shared validator and kept as the Part ${address}: ${record.ticks.length} Ticks, ${record.counters.invocations} invocations, ${record.counters.hits} hits. No domain fact was written.`);
      break;
    }
    case 'record-render': {
      const { address, record } = runtime.runRecord(shownPcr());
      const page = composePage({ ...await viewerSources(), record });
      ui.recordAddress = address;
      const blob = new Blob([page], { type: 'text/html' });
      downloadBlob(blob, `${record.pcr}-tick-render.html`);
      // A tab for reading now; the saved file is the one that opens over file:// later.
      const url = URL.createObjectURL(blob); if (!window.open(url, '_blank')) URL.revokeObjectURL(url); else setTimeout(() => URL.revokeObjectURL(url), 30000);
      message(`Tick render page built from ${address} and saved: the record is embedded and adapters.js and tick-viewer.js are inlined, so it opens over file:// with no server.`);
      break;
    }
  }
  persistView(); render();
}
app.addEventListener('click', event => {
  const el = event.target.closest('[data-action]'); if (!el || el.disabled) return;
  Promise.resolve(action(el.dataset.action, el)).catch(error => { ui.busy = false; message(error.cause?.message || error.message, true); render(); });
});
function controlChange(el) {
  const key = el.dataset.control, value = el.value, d = el.dataset, { disc, mold, maker } = discInfo();
  const number = () => value === '' ? null : Number(value);
  const setNode = patch => execute({ type: 'preset.set', id: ui.presetId, nodeId: ui.nodeId, patch });
  const setPreset = patch => execute({ type: 'preset.set', id: ui.presetId, patch });
  switch (key) {
    case 'bag': ui.bagId = value; break;
    case 'only-bag': ui.onlyBag = el.checked; break;
    case 'identity-maker': execute({ type: 'disc.identity', id: disc.id, manufacturer: value, mold: mold?.name || '' }); break;
    case 'identity-mold': execute({ type: 'disc.identity', id: disc.id, manufacturer: maker?.name || '', mold: value }); break;
    case 'disc-field': execute({ type: 'entity.set', entityType: 'Disc', id: disc.id, path: d.key, value: el.type === 'checkbox' ? el.checked : d.kind === 'number' ? number() : value }); break;
    case 'flight': execute({ type: 'entity.set', entityType: 'Mold', id: mold.id, path: `flight.${d.key}`, value: number() }); break;
    case 'score': execute({ type: 'battle.score', id: d.id, score: number() }); ui.motionEntry = d.id; break;
    case 'course-preset': ui.presetId = value; execute({ type: 'layout.set', patch: { presetId: value } }); break;
    case 'arrangement': execute({ type: 'layout.set', patch: { arrangement: value } }); break;
    case 'scale': execute({ type: 'layout.set', patch: { scale: number() } }); break;
    case 'gap': execute({ type: 'layout.set', patch: { gap: number() } }); break;
    case 'edit-preset': ui.presetId = value; ui.component = w().presets[value].kind; ui.nodeId = w().presets[value].nodes[0]?.id; if (w().presets[value].kind === 'DisplayCard') execute({ type: 'layout.set', patch: { presetId: value } }); break;
    case 'editor-disc': ui.discId = value; break;
    case 'extra-type': ui.extraType = value; ui.extraId = all(w(), value)[0]?.id || ''; break;
    case 'extra-id': ui.extraId = value; break;
    case 'node-binding': setNode({ binding: value, context: value.startsWith('entry.') ? 'battle' : null }); break;
    case 'node-number': setNode({ [d.key]: number() }); break;
    case 'node-text': setNode({ text: value }); break;
    case 'node-font': setNode({ font: value }); break;
    case 'node-align': setNode({ align: value }); break;
    case 'node-color': setNode({ color: value }); break;
    case 'node-fit': setNode({ fit: value }); break;
    case 'node-prefix': setNode({ prefix: value }); break;
    case 'node-suffix': setNode({ suffix: value }); break;
    case 'node-bold': case 'node-showLabel': case 'node-hideEmpty': case 'node-visible': setNode({ [key.slice(5)]: el.checked }); break;
    case 'preset-name': setPreset({ name: value }); break;
    case 'preset-number': setPreset({ [d.key]: number() }); break;
    case 'preset-color': setPreset({ [d.key]: value }); break;
    case 'preset-transparent': setPreset({ background: el.checked ? 'transparent' : '#203d36' }); break;
    case 'preset-highlight': setPreset({ highlight: value }); break;
    case 'preset-motion': setPreset({ scoreMotion: value }); break;
    case 'competition': ui.competitionId = value; ui.roundId = get(w(), 'Competition', value).roundIds[0]; break;
    case 'competition-name': execute({ type: 'entity.set', entityType: 'Competition', id: ui.competitionId, path: 'name', value }); break;
    case 'constraint-combine': execute({ type: 'entity.set', entityType: 'Competition', id: ui.competitionId, path: 'combine', value }); break;
    case 'constraint-enabled': execute({ type: 'competition.rule.set', id: ui.competitionId, ruleId: d.id, patch: { enabled: el.checked } }); break;
    case 'constraint-value': execute({ type: 'competition.rule.set', id: ui.competitionId, ruleId: d.id, patch: { value: number() } }); break;
    case 'team-name': execute({ type: 'entity.set', entityType: 'Team', id: d.id, path: 'name', value }); break;
    case 'team-bag': execute({ type: 'entity.set', entityType: 'Team', id: d.id, path: 'bagId', value }); break;
    case 'round': ui.roundId = value; break;
    case 'round-complete': execute({ type: 'entity.set', entityType: 'Round', id: ui.roundId, path: 'complete', value: el.checked }); break;
    case 'new-field-label': case 'new-field-type': return;
  }
  persistView(); render();
}
app.addEventListener('change', event => { const el = event.target.closest('[data-control]'); if (!el) return; try { controlChange(el); } catch (error) { message(error.cause?.message || error.message, true); render(); } });
app.addEventListener('input', event => { const el = event.target; if (el.dataset.search) { if (el.dataset.search === 'discs') ui.query = el.value; else ui.fieldQuery = el.value; render(); } });
let drag = null, dragFrame = null, pendingMove = null;
app.addEventListener('pointerdown', event => {
  const hit = event.target.closest('[data-node-select]'); if (!hit || event.button !== 0) return;
  event.preventDefault(); ui.nodeId = hit.dataset.nodeSelect;
  const node = w().presets[ui.presetId].nodes.find(n => n.id === ui.nodeId), rect = hit.ownerSVGElement.getBoundingClientRect();
  drag = { x: event.clientX, y: event.clientY, startX: node.x, startY: node.y, ratio: w().presets[ui.presetId].width / rect.width, id: node.id, presetId: ui.presetId };
  render();
});
window.addEventListener('pointermove', event => {
  if (!drag) return;
  const state = drag, x = Math.round(state.startX + (event.clientX - state.x) * state.ratio), y = Math.round(state.startY + (event.clientY - state.y) * state.ratio);
  cancelAnimationFrame(dragFrame);
  pendingMove = { type: 'preset.set', id: state.presetId, nodeId: state.id, patch: { x, y } };
  dragFrame = requestAnimationFrame(flushDrag);
});
function flushDrag() { if (!pendingMove) return; const command = pendingMove; pendingMove = null; try { execute(command); render(); } catch (error) { message(error.message, true); } }
window.addEventListener('pointerup', () => { cancelAnimationFrame(dragFrame); flushDrag(); drag = null; });
window.addEventListener('pointercancel', () => { cancelAnimationFrame(dragFrame); pendingMove = null; drag = null; });
window.addEventListener('keydown', event => {
  if (ui.route !== 'components' || !ui.nodeId || /INPUT|TEXTAREA|SELECT/.test(event.target.tagName)) return;
  const node = w().presets[ui.presetId]?.nodes.find(n => n.id === ui.nodeId); if (!node) return;
  const offsets = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
  if (offsets[event.key]) { event.preventDefault(); const [dx, dy] = offsets[event.key], step = event.shiftKey ? 10 : 1; execute({ type: 'preset.set', id: ui.presetId, nodeId: node.id, patch: { x: node.x + dx * step, y: node.y + dy * step } }); render(); }
});
for (const name of ['photo', 'footage', 'draft', 'preset']) document.querySelector(`#${name}-file`).addEventListener('change', async event => {
  const file = event.target.files?.[0]; if (!file) return;
  try {
    if (name === 'photo') { const targetDisc = ui.photoDiscId || ui.discId, data = await photoData(file); execute({ type: 'entity.set', entityType: 'Disc', id: targetDisc, path: 'photo', value: data }); message('Exact photo saved locally. Every bound presentation now uses it.'); }
    if (name === 'footage') {
      if (!/^(image\/(png|jpeg|webp)|video\/(mp4|webm|quicktime))$/.test(file.type)) throw new Error('Choose a PNG/JPEG/WebP still or MP4/WebM/MOV video.');
      if (ui.footage) URL.revokeObjectURL(ui.footage); ui.footage = URL.createObjectURL(file); ui.footageKind = file.type.startsWith('video') ? 'video' : 'image'; ui.footageName = file.name; ui.footageTime = 0; message('Footage is preview context only. It is not uploaded, saved in your draft, or included in your overlay export.');
    }
    if (name === 'draft') { if (file.size > 12_000_000) throw new Error('Draft exceeds 12 MB.'); const value = validateWorld(JSON.parse(await file.text())); if (confirm('Replace this workspace with the imported draft? Review comments will remain separate.')) { saveEnabled = true; runtime.replace(value); message('Draft loaded. Domain objects, presentations and comparison states restored.'); } }
    if (name === 'preset') { if (file.size > 200_000) throw new Error('Presentation file is too large.'); const data = JSON.parse(await file.text()), preset = data.preset || data; if (!w().presets[preset.id] || confirm(`Replace the saved design “${w().presets[preset.id].name}”?`)) { execute({ type: 'preset.put', preset }); ui.presetId = preset.id; ui.component = preset.kind; if (preset.kind === 'DisplayCard') execute({ type: 'layout.set', patch: { presetId: preset.id } }); message('Reusable presentation imported. Bindings now resolve against your own selected disc.'); } }
  } catch (error) { message(error.cause?.message || error.message, true); }
  event.target.value = ''; render();
});
const review = document.querySelector('neat-review');
review.setAttribute('data-checklist', JSON.stringify(reviewItems));
review.setAttribute('checkpoint-id', 'discstudio-pxc-02'); review.setAttribute('subject-commit', 'local-development');
fetch(new URL('../build-info.json', import.meta.url)).then(r => r.ok ? r.json() : null).then(info => { if (info) { ui.build = info; review.setAttribute('submission-id', `discstudio-pxc-02-${info.fingerprint.slice(0, 16)}`); review.setAttribute('checkpoint-id', info.fingerprint); review.setAttribute('subject-commit', info.commit); render(); } }).catch(() => {});
// Explicit developer inspection/command surface. UI and programmatic commands use the same registered Calculations.
window.discStudio = { runtime, get world() { return runtime.world(); }, get preview() { return ui.lastResult; }, get view() { return { route: ui.route, discId: ui.discId, presetId: ui.presetId, nodeId: ui.nodeId, mode: ui.mode }; } };
syncRoute();
