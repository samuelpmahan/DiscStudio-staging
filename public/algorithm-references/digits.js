import { createLab } from '../../src/lab/lab.js';
import { createId3Session } from '../../src/reference-algorithms/id3.js';
import { DIGIT_DATASET, DIGIT_TEST_SAMPLES } from '../../src/reference-algorithms/digit-data.js';
import { createLiveTransport } from '../../src/reference-algorithms/live.js';
import { downloadJson } from '../../src/media.js';
import { composePage, fetchPageSources } from '../../pyto/viewer/embed.mjs';

// This view draws supplied samples and Calculation results. It never scores,
// partitions, trains, or predicts; those operations belong to the ID3 session.
const mount = document.querySelector('#digit-lab');
const html = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const colors = ['#77dfd5', '#ffbd73', '#aeb4ff', '#fe96bd', '#afe287', '#ffda76', '#8ccaff', '#dca2fc', '#ff9b87', '#95ded0'];
const pixelLabel = pixel => `row ${Math.floor(pixel / 8) + 1}, column ${pixel % 8 + 1}`;
const number = value => Number.isFinite(value) ? value.toFixed(3) : '—';
const samples = DIGIT_DATASET.samples;
const sampleById = new Map(samples.map(sample => [sample.id, sample]));
const lab = createLab();
let session, transport, busy = false, previewPixel = null, inspectedNode = null, prediction = null;
let drawing = Array(64).fill(0), drawingOn = false, drawingValue = 16, viewerSources, lastFrame = -1;
const sessions = [];
let activeDialog = null, dialogReturn = null, zoom = 1, viewMode = 'follow', planeSize = {width: 0, height: 0}, pickedTest = '';
let pan = null;
const currentFrame = () => session.frame(transport?.cursor ?? 0);
const recordAt = () => {
  const address = session.state.records?.[transport.cursor - 1];
  return address ? lab.get(address) : null;
};
const sourceAddress = (frame, suffix) => {
  const entries = Array.isArray(frame.sourceAddresses) ? frame.sourceAddresses : Object.values(frame.sourceAddresses || {});
  return frame[`${suffix}Address`] || entries.find(address => typeof address === 'string' && address.includes(suffix)) || '';
};

function digitSvg(pixels, { selected = null, label = '', color = 'currentColor' } = {}) {
  return `<svg class="id3-digit-svg" viewBox="0 0 80 80" role="img" aria-label="${html(label)}"><rect width="80" height="80" rx="5" fill="#101723"/>${pixels.map((value, index) => `<rect x="${index % 8 * 10 + .8}" y="${Math.floor(index / 8) * 10 + .8}" width="8.4" height="8.4" rx=".8" fill="${color}" opacity="${value / 16}"/>`).join('')}${selected !== null ? `<rect x="${selected % 8 * 10 + .5}" y="${Math.floor(selected / 8) * 10 + .5}" width="9" height="9" fill="none" stroke="#ffffff" stroke-width="1.6"/>` : ''}</svg>`;
}

function sampleTile(id, pixel, pile) {
  const sample = sampleById.get(id);
  if (!sample) return '';
  return `<span class="id3-sample" data-id3-sample="${html(id)}" data-id3-sample-pile="${pile}" data-source-address="${html(session.state.addresses?.dataset || sourceAddress(currentFrame(), 'dataset'))}" style="--digit-color:${colors[sample.label]}" title="${html(id)} · labelled ${sample.label}${pixel !== null ? ` · ${pixelLabel(pixel)}: ${sample.pixels[pixel]}` : ''}">${digitSvg(sample.pixels, { selected: pixel, label: `Handwritten ${sample.label}, ${id}` })}<b>${sample.label}</b></span>`;
}

function countsView(counts) {
  if (!counts) return '<span class="id3-soft">Three labelled examples of each digit, 0–9.</span>';
  return `<div class="id3-counts" aria-label="Digit counts">${Object.entries(counts).filter(([, count]) => count > 0).map(([label, count]) => `<span style="--digit-color:${colors[Number(label)]}"><b>${html(label)}</b> × ${count}</span>`).join('')}</div>`;
}

function pile(ids, pixel, name, counts, { preview = false, nodeId = '' } = {}) {
  return `<div class="id3-pile ${preview ? 'is-preview' : ''}" data-id3-pile="${name}" ${name !== 'parent' ? `data-id3-branch="${name}"` : ''} data-id3-node-id="${html(nodeId)}"><div class="id3-pile-heading"><strong>${name === 'parent' ? 'The digits at this node' : name === 'off' ? 'OFF' : 'ON'}</strong><span>${ids ? `${ids.length} digit${ids.length === 1 ? '' : 's'}` : 'Waiting for scores'}</span></div>${counts || name === 'parent' ? countsView(counts) : ''}<div class="id3-samples">${ids ? ids.map(id => sampleTile(id, pixel, name)).join('') : '<span class="id3-await">The scored question will reveal this pile.</span>'}${ids && !ids.length ? '<span class="id3-await">No examples here.</span>' : ''}</div></div>`;
}

const recommended = frame => frame.selectedCandidate || (frame.phase === 'scored' ? frame.previewCandidate || frame.candidates?.recommendedCandidate : null);
function selected(frame) {
  const candidates = frame.candidates?.candidates || [];
  return candidates.find(candidate => candidate.pixel === previewPixel) || recommended(frame) || null;
}

function questionGrid(pixel) {
  return `<span class="id3-question-grid" aria-label="${pixel === null ? 'No pixel selected yet' : pixelLabel(pixel)}">${Array.from({ length: 64 }, (_, index) => `<i class="${index === pixel ? 'is-pixel' : ''}"></i>`).join('')}</span>`;
}

function nodeView(frame, node) {
  const active = frame.activeNodeId === node.id;
  const scored = active && frame.phase === 'scored' ? recommended(frame) : null;
  const pixel = node.status === 'split' ? node.pixel : scored?.pixel ?? null;
  const gain = node.status === 'split' ? node.gain : scored?.gain;
  const path = prediction?.result?.visited.some(visit => visit.nodeId === node.id);
  const name = node.parent ? node.branch : 'parent';
  const title = node.status === 'leaf' ? `Digit ${node.prediction}` : pixel !== null ? 'Is this pixel ON?' : 'Which pixel should we ask about?';
  const state = node.status === 'leaf' ? 'Leaf' : node.status === 'split' ? 'Learned question' : scored ? 'Best scored · not split yet' : active ? 'Next to learn' : 'Waiting';
  return `<article class="id3-node-card is-${node.status} ${active ? 'is-active' : ''} ${path ? 'is-prediction-path' : ''}" data-id3-node="${html(node.id)}" data-source-address="${html(frame.treeAddress)}" aria-label="${html(node.id)}, ${node.status}, ${node.sampleIds.length} examples">
    <header class="id3-node-heading"><span><b>${node.parent ? name.toUpperCase() : 'ROOT'}</b> <span class="id3-node-id">${html(node.id)}</span></span><span class="id3-phase">${state}</span><button type="button" data-id3-inspect-node="${html(node.id)}" aria-label="Inspect node ${html(node.id)}">↗</button></header>
    ${pile(node.sampleIds, pixel, name, node.counts, {nodeId: node.id})}
    <div class="id3-question" data-id3-question-pixel="${pixel ?? ''}" data-source-address="${html(scored ? frame.scoresAddress : frame.treeAddress)}">
      ${node.status === 'leaf' ? `<strong class="id3-leaf-digit" style="color:${colors[node.prediction]}">${node.prediction}</strong>` : questionGrid(pixel)}
      <div><h3>${title}</h3><p>${node.status === 'leaf' ? html(node.reason) : pixel !== null ? `${pixelLabel(pixel)} · intensity ≥ 8 is ON` : active ? 'Next scores the available pixel questions.' : 'This branch has not been expanded.'}</p>${Number.isFinite(gain) ? `<p class="id3-gain">Information gain <strong data-id3-selected-gain="${gain}">${number(gain)}</strong> bits</p>` : ''}</div>
    </div>
  </article>`;
}

function comparisonView(frame) {
  const candidate = selected(frame), winner = recommended(frame);
  return `${gainView(frame)}${candidate ? `<section class="id3-comparison-preview"><span class="id3-kicker">Preview · ${pixelLabel(candidate.pixel)}</span><p>${candidate.pixel === winner?.pixel ? 'The algorithm’s best scored question.' : 'An alternative question; the algorithm is unchanged.'} These piles come from the saved scores.</p><div class="id3-branches">${pile(candidate.off.sampleIds, candidate.pixel, 'off', candidate.off.counts, {preview:true})}${pile(candidate.on.sampleIds, candidate.pixel, 'on', candidate.on.counts, {preview:true})}</div></section>` : ''}`;
}

function gainView(frame) {
  const candidates = frame.candidates?.candidates || [], candidate = selected(frame), winner = recommended(frame);
  const byPixel = new Map(candidates.map(value => [value.pixel, value]));
  const high = Math.max(0, ...candidates.map(value => value.gain)); // Visual color normalization only.
  const ranked = [...candidates].sort((a, b) => b.gain - a.gain || a.pixel - b.pixel).slice(0, 4);
  const address = sourceAddress(frame, 'candidates') || sourceAddress(frame, 'scores');
  return `<section class="id3-gain-panel"><div class="id3-panel-heading"><div><span class="id3-kicker">Compare the questions</span><h3>Which pixels help most?</h3></div></div><p class="id3-soft">${candidates.length ? 'Brighter means more information gain. Click to preview a scored pixel.' : 'The 8 × 8 grid will light up after the first Next.'}</p><div class="id3-gain-content"><div><div class="id3-heatmap" aria-label="Pixel information gain heatmap">${Array.from({ length: 64 }, (_, pixel) => {
    const value = byPixel.get(pixel);
    return `<button type="button" data-id3-pixel="${pixel}" data-id3-gain="${value?.gain ?? ''}" data-source-address="${html(address)}" class="${candidate?.pixel === pixel ? 'is-selected' : ''} ${winner?.pixel === pixel ? 'is-winner' : ''}" style="--gain:${value && high > 0 ? value.gain / high : 0}" ${!value ? 'disabled' : ''} aria-label="${pixelLabel(pixel)}${value ? `, gain ${number(value.gain)} bits` : ', not scored'}${winner?.pixel === pixel ? ', algorithm winner' : ''}" aria-pressed="${candidate?.pixel === pixel}">${winner?.pixel === pixel ? '★' : ''}</button>`;
  }).join('')}</div><div class="id3-heat-key"><span>Less useful</span><i></i><span>More useful</span></div></div><div class="id3-top-candidates">${ranked.length ? ranked.map((value, index) => `<button type="button" data-id3-preview="${value.pixel}" aria-pressed="${candidate?.pixel === value.pixel}"><span>${winner?.pixel === value.pixel ? '★' : index + 1}</span><div><b>Row ${value.row + 1}, col ${value.column + 1}</b><small>${number(value.gain)} bits${winner?.pixel === value.pixel ? ' · chosen' : ''}</small></div></button>`).join('') : '<span class="id3-await">No scores yet.<br>Next runs the comparison.</span>'}</div></div></section>`;
}

function treeView(frame) {
  return `<div class="id3-workspace"><div class="id3-tree-scroll" tabindex="0" aria-label="Decision tree canvas. Scroll to move; use zoom controls for detail."><div class="id3-canvas-size"><div class="id3-tree-plane"><svg class="id3-tree-svg" aria-label="Connections between decision nodes"></svg>${Object.values(frame.tree.nodes).map(node => nodeView(frame, node)).join('')}</div></div></div><div class="id3-canvas-tools"><span>${Object.keys(frame.tree.nodes).length} nodes</span><button type="button" data-id3-zoom="out" aria-label="Zoom out">−</button><output data-id3-zoom-value>100%</output><button type="button" data-id3-zoom="in" aria-label="Zoom in">+</button><button type="button" data-id3-fit>Fit tree</button><button type="button" data-id3-current>Current node</button></div></div>`;
}

// Layout is a projection of the retained tree. It never creates algorithm nodes.
function layoutTree({recenter = false} = {}) {
  const frame = currentFrame(), viewport = mount.querySelector('.id3-tree-scroll'), plane = mount.querySelector('.id3-tree-plane');
  if (!viewport || !plane) return;
  const cards = new Map([...plane.querySelectorAll('[data-id3-node]')].map(card => [card.dataset.id3Node, card]));
  const width = 420, siblingGap = 40, levelGap = 58, pad = 28, spans = new Map(), heights = [];
  for (const card of cards.values()) card.style.width = `${width}px`;
  const cardHeights = new Map([...cards].map(([id, card]) => [id, card.offsetHeight]));
  for (const [id, height] of cardHeights) { const depth = frame.tree.nodes[id].depth; heights[depth] = Math.max(heights[depth] || 0, height); }
  const measure = id => { const node = frame.tree.nodes[id]; const span = node.children ? Math.max(width, measure(node.children.off) + siblingGap + measure(node.children.on)) : width; spans.set(id, span); return span; };
  const wholeWidth = measure(frame.tree.root) + pad * 2, levels = [pad];
  for (let i=1; i<heights.length; i++) levels[i] = levels[i-1] + heights[i-1] + levelGap;
  const positions = new Map();
  function place(id, left) {
    const node = frame.tree.nodes[id], card = cards.get(id), x = left + (spans.get(id)-width)/2, y = levels[node.depth];
    card.style.left = `${x}px`; card.style.top = `${y}px`; positions.set(id, {x, y, height:cardHeights.get(id)});
    if (node.children) { place(node.children.off,left); place(node.children.on,left+spans.get(node.children.off)+siblingGap); }
  }
  place(frame.tree.root,pad);
  planeSize = {width:wholeWidth, height:levels.at(-1)+heights.at(-1)+pad};
  plane.style.width = `${planeSize.width}px`; plane.style.height = `${planeSize.height}px`;
  const svg = plane.querySelector('svg'), visited = prediction?.result?.visited.map(visit=>visit.nodeId) || [];
  svg.setAttribute('width',planeSize.width); svg.setAttribute('height',planeSize.height);
  svg.innerHTML = Object.values(frame.tree.nodes).filter(node=>node.children).flatMap(node=>Object.entries(node.children).map(([side,id])=>{
    const a=positions.get(node.id), b=positions.get(id), ax=a.x+width/2, ay=a.y+a.height, bx=b.x+width/2, by=b.y;
    return `<g data-from="${node.id}" data-to="${id}" class="${visited.includes(node.id)&&visited.includes(id)?'is-prediction-path':''}"><path d="M${ax} ${ay} C${ax} ${ay+levelGap/2},${bx} ${by-levelGap/2},${bx} ${by}"/><text x="${bx}" y="${by-12}" text-anchor="middle">${side.toUpperCase()}</text></g>`;
  })).join('');
  if (viewMode === 'fit') zoom = Math.min(1.25,(viewport.clientWidth-12)/planeSize.width,(viewport.clientHeight-48)/planeSize.height);
  else if (viewMode === 'follow') zoom = Math.max(.65,Math.min(1,(viewport.clientWidth-12)/planeSize.width,(viewport.clientHeight-48)/planeSize.height));
  applyZoom();
  if (recenter) {
    if (viewMode === 'fit' || cards.size <= 3) {viewport.scrollTop=0; viewport.scrollLeft=Math.max(0,(planeSize.width*zoom-viewport.clientWidth)/2);}
    else centerCurrent();
  }
}
function applyZoom() {
  const viewport=mount.querySelector('.id3-tree-scroll'), plane=mount.querySelector('.id3-tree-plane'), size=mount.querySelector('.id3-canvas-size');
  if (!plane) return;
  size.style.width=`${Math.max(viewport.clientWidth,planeSize.width*zoom)}px`; size.style.height=`${Math.max(viewport.clientHeight,planeSize.height*zoom)}px`;
  plane.style.transform=`scale(${zoom})`; plane.style.left=`${Math.max(0,(viewport.clientWidth-planeSize.width*zoom)/2)}px`;
  mount.querySelector('[data-id3-zoom-value]').textContent=`${Math.round(zoom*100)}%`;
}
function centerCurrent() {
  const frame=currentFrame(), card=mount.querySelector(`[data-id3-node="${frame.activeNodeId || frame.tree.root}"]`), viewport=mount.querySelector('.id3-tree-scroll');
  if (card) {viewport.scrollLeft=card.offsetLeft*zoom+card.offsetWidth*zoom/2-viewport.clientWidth/2; viewport.scrollTop=Math.max(0,card.offsetTop*zoom-24);}
}

function drawingView() {
  const result = prediction?.result;
  return `<section class="id3-drawing-panel"><div><span class="id3-kicker">Try the tree yourself</span><h3>Draw one digit.</h3><p class="id3-soft">Drag or tap the 8 × 8 cells. Filled cells have intensity 16; empty cells have 0.</p><div class="id3-drawing" role="group" aria-label="Draw an 8 by 8 digit">${drawing.map((value, pixel) => `<button type="button" data-id3-draw-cell="${pixel}" aria-label="Draw ${pixelLabel(pixel)}" aria-pressed="${value >= 8}" style="--ink:${value / 16}"></button>`).join('')}</div><div class="id3-draw-actions"><button type="button" data-id3-predict>Follow this tree →</button><button type="button" class="id3-quiet" data-id3-clear>Clear</button></div></div><div class="id3-prediction-panel"><label class="id3-test-label">Or load a held-out example<select data-id3-test><option value="">Choose a digit…</option>${DIGIT_TEST_SAMPLES.map((sample, index) => `<option value="${index}" ${String(index) === pickedTest ? 'selected' : ''}>Digit ${sample.label} · ${html(sample.id)}</option>`).join('')}</select></label><div class="id3-prediction ${result?.status === 'prediction' ? 'is-resolved' : ''}" data-id3-prediction data-id3-prediction-status="${result?.status || 'not-run'}" data-source-address="${html(prediction?.resultAddress || '')}"><span class="id3-kicker">${result ? `At retained frame ${prediction.frameIndex}` : 'Prediction path'}</span><h3>${!result ? 'Where will your digit go?' : result.status === 'prediction' ? `The tree says ${result.prediction}` : 'Not decided yet'}</h3><p>${!result ? 'Follow the pixel questions in the tree you have grown so far.' : result.status === 'prediction' ? 'A completed leaf supplied this label.' : 'This path reached an unfinished branch. Grow the tree with Next, then try again.'}</p>${result ? `<ol class="id3-prediction-path">${result.visited.map(visit => `<li data-id3-prediction-node="${html(visit.nodeId)}"><b>${html(visit.nodeId)}</b> ${visit.pixel !== undefined ? `${pixelLabel(visit.pixel)} → <strong>${visit.on ? 'ON' : 'OFF'}</strong>` : visit.status === 'leaf' ? `leaf → ${result.prediction}` : 'still to learn'}</li>`).join('')}</ol><small>${html(result.reason || '')}</small>` : ''}</div><p class="id3-soft">This small teaching set has 30 training examples. A new handwriting style can follow the wrong leaf.</p></div></section>`;
}

function inspectionView(frame) {
  const addresses = Array.isArray(frame.sourceAddresses) ? frame.sourceAddresses : Object.values(frame.sourceAddresses || {});
  const selectedNode = inspectedNode && frame.tree.nodes[inspectedNode];
  return `<details class="id3-inspector" ${selectedNode ? 'open' : ''}><summary>${selectedNode ? `Inspect ${html(inspectedNode)}` : 'Inspect the saved Parts and run record'}</summary>${selectedNode ? `<pre data-id3-node-value="${html(inspectedNode)}">${html(JSON.stringify(selectedNode, null, 2))}</pre>` : ''}<div class="id3-record-actions"><button type="button" data-id3-export ${recordAt() ? '' : 'disabled'}>Export this frame’s record</button><button type="button" data-id3-replay ${recordAt() ? '' : 'disabled'}>Open recorded replay</button><button type="button" data-id3-reset class="id3-quiet" ${busy ? 'disabled' : ''}>Start a fresh tree</button></div><p>Back and the slider only review saved frames. Next runs the next scoring or splitting Calculation at the live frontier.</p>${[...new Set(addresses)].filter(address => typeof address === 'string' && lab.has(address)).map(address => `<details class="id3-source" data-id3-part-address="${html(address)}"><summary><code>${html(address)}</code></summary><pre>${html(JSON.stringify(lab.get(address), null, 2))}</pre></details>`).join('')}</details>`;
}

function render() {
  const frame = currentFrame(), changed = frame.number !== lastFrame;
  // Keep transport controls as the same DOM objects while the tree changes.
  // A pointer press or a queued click must not target a discarded Pause button.
  const controlAttrs = ['data-id3-next','data-id3-play','data-id3-back','data-id3-open','data-id3-scrub'];
  const controls = controlAttrs.flatMap(attr => [...mount.querySelectorAll(`[${attr}]`)].map(node => ({node, selector:`[${attr}="${node.getAttribute(attr)}"]`})));
  const viewport = mount.querySelector('.id3-tree-scroll'), oldScroll = viewport ? [viewport.scrollLeft, viewport.scrollTop] : [0,0];
  const focus = document.activeElement;
  const focusAttr = ['data-id3-pixel','data-id3-preview','data-id3-draw-cell','data-id3-test','data-id3-close'].find(attr=>focus?.hasAttribute(attr));
  const focusSelector = focusAttr ? `[${focusAttr}="${focus.getAttribute(focusAttr)}"]` : null;
  if (changed) { previewPixel = null; inspectedNode = null; prediction = null; lastFrame = frame.number; }
  mount.dataset.id3Learning = String(frame.number > 0);
  const complete = session.state.status === 'complete', reviewing = transport.cursor < session.state.nextTick;
  const nextLabel = complete ? 'Tree grown' : session.frame().tree.phase === 'split' ? recommended(session.frame()) ? 'Next · split this pile' : 'Next · finish this pile' : 'Next · find the best pixel';
  const liveLabel = reviewing ? complete ? 'Reviewing history · training complete' : 'Reviewing history · Next continues the live tree' : complete ? 'Training complete' : frame.number ? 'One real calculation per Next' : '30 handwritten examples · no questions scored yet';
  mount.innerHTML = `<header class="id3-screen-header"><div><span class="id3-kicker">ID3 · a tree that learns</span><h2>Which pixel separates these digits?</h2></div><nav aria-label="Tree tools"><button type="button" data-id3-open="questions">Compare questions${frame.candidates ? ' ↗' : ''}</button><button type="button" data-id3-open="drawing">Try a digit</button><button type="button" data-id3-open="inspect">Inspect</button></nav></header><div class="id3-controls"><div class="id3-toolbar"><button type="button" class="id3-next" data-id3-next ${busy || complete ? 'disabled' : ''}>${nextLabel} <span>→</span></button><button type="button" data-id3-play class="id3-quiet" ${complete && !transport.playing ? 'disabled' : ''}>${transport.playing ? 'Pause' : 'Play'}</button></div><div class="id3-review"><button type="button" data-id3-back class="id3-quiet" ${busy || !transport.cursor ? 'disabled' : ''}>← Back</button><label>Review <input type="range" data-id3-scrub min="0" max="${session.state.nextTick}" value="${transport.cursor}" step="1" ${busy ? 'disabled' : ''}></label><span data-id3-frame-number>Frame ${transport.cursor} / ${session.state.nextTick}</span></div><span class="id3-live-label">${liveLabel}</span></div><p class="id3-message" role="status" aria-live="polite" data-id3-message></p>${treeView(frame)}
    ${[['questions','Compare pixel questions',comparisonView(frame)],['drawing','Follow the learned tree',drawingView()],['inspect','Saved Parts and records',inspectionView(frame)]].map(([kind,title,content])=>`<dialog class="id3-dialog" data-id3-dialog="${kind}" aria-labelledby="id3-dialog-${kind}"><header class="id3-dialog-header"><h2 id="id3-dialog-${kind}">${title}</h2><button type="button" data-id3-close aria-label="Close ${title.toLowerCase()}">×</button></header>${content}${kind==='inspect'?`<p class="id3-attribution" data-id3-attribution>Examples by ${html(DIGIT_DATASET.metadata.creators.join(' & '))}: <a href="${html(DIGIT_DATASET.metadata.doi)}" target="_blank" rel="noopener">${html(DIGIT_DATASET.metadata.title)}</a> · <a href="${html(DIGIT_DATASET.metadata.licenseUrl)}" target="_blank" rel="noopener">${html(DIGIT_DATASET.metadata.license)}</a>. Original intensities 0–16; ≥ 8 is ON. Three examples per digit train; the next two per digit are held out.</p>`:''}</dialog>`).join('')}`;
  for (const {node,selector} of controls) {
    const fresh=mount.querySelector(selector); if (!fresh) continue;
    node.disabled=fresh.disabled;
    if (node instanceof HTMLInputElement) {node.max=fresh.max;node.value=fresh.value;}
    else node.innerHTML=fresh.innerHTML;
    fresh.replaceWith(node);
  }
  layoutTree({recenter:changed});
  if (!changed) {const nextViewport=mount.querySelector('.id3-tree-scroll');nextViewport.scrollLeft=oldScroll[0];nextViewport.scrollTop=oldScroll[1];}
  for (const dialog of mount.querySelectorAll('dialog')) {
    dialog.addEventListener('cancel',event=>{event.preventDefault();closeDialog();});
    dialog.addEventListener('click',event=>{if(event.target===dialog){const rect=dialog.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)closeDialog();}});
  }
  if (activeDialog) {const dialog=mount.querySelector(`[data-id3-dialog="${activeDialog}"]`);dialog.showModal();(focusSelector&&dialog.querySelector(focusSelector)||dialog.querySelector('[data-id3-close]')).focus({preventScroll:true});}
  mount.dataset.id3Ready = 'true';
}
function openDialog(kind, returnSelector = `[data-id3-open="${kind}"]`) {
  activeDialog=kind;dialogReturn=returnSelector;
  const dialog=mount.querySelector(`[data-id3-dialog="${kind}"]`);if(!dialog.open)dialog.showModal();dialog.querySelector('[data-id3-close]').focus({preventScroll:true});
}
function closeDialog() {
  const dialog=mount.querySelector('dialog[open]');activeDialog=null;dialog?.close();
  mount.querySelector(dialogReturn || '[data-id3-open="questions"]')?.focus({preventScroll:true});
}

function setMessage(text) { const element = mount.querySelector('[data-id3-message]'); if (element) element.textContent = text; }

function syncBusyControls() {
  for (const selector of ['[data-id3-next]', '[data-id3-back]', '[data-id3-scrub]', '[data-id3-reset]']) {
    const control = mount.querySelector(selector);
    if (control) control.disabled = busy || (selector === '[data-id3-next]' && (session.state.status === 'complete'));
  }
}

async function present(frame, { animate }) {
  // Retained parent positions become the start points of the split animation.
  const oldSamples = new Map([...mount.querySelectorAll(`.id3-tree-plane [data-id3-node="${frame.activeNodeId}"] [data-id3-sample]`)].map(node => [node.dataset.id3Sample, { rect: node.getBoundingClientRect(), node: node.cloneNode(true) }]));
  render();
  // Give the browser a paint and an input turn even with motion disabled.
  // Otherwise a Play loop of resolved promises can starve its own Pause button.
  await new Promise(resolve => requestAnimationFrame(() => setTimeout(resolve, 0)));
  if (!animate || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const animations = [];
  if (frame.phase === 'split') {
    const children = Object.values(frame.tree.nodes[frame.activeNodeId]?.children || {});
    for (const target of children.flatMap(id=>[...mount.querySelectorAll(`.id3-tree-plane [data-id3-node="${id}"] [data-id3-sample]`)])) {
      const source = oldSamples.get(target.dataset.id3Sample); if (!source) continue;
      const end = target.getBoundingClientRect(), ghost = source.node;
      ghost.removeAttribute('data-id3-sample'); ghost.classList.add('id3-moving-sample');
      Object.assign(ghost.style, { position: 'fixed', left: `${end.left}px`, top: `${end.top}px`, width: `${end.width}px`, height: `${end.height}px`, zIndex: '100', pointerEvents: 'none' });
      document.body.append(ghost);
      const animation = ghost.animate([{ transform: `translate(${source.rect.left - end.left}px,${source.rect.top - end.top}px)`, opacity: .95 }, { transform: 'translate(0,0)', opacity: 1 }], { duration: 660, easing: 'cubic-bezier(.2,.6,.25,1)' });
      animations.push(animation.finished.catch(() => {}).finally(() => ghost.remove()));
    }
  }
  if (!animations.length) {
    const target = mount.querySelector(`.id3-tree-plane [data-id3-node="${frame.activeNodeId}"] .id3-question`);
    if (target) animations.push(target.animate([{ opacity: .3, transform: 'translateY(5px)' }, { opacity: 1, transform: 'translateY(0)' }], { duration: 380, easing: 'ease-out' }).finished.catch(() => {}));
  }
  await Promise.all(animations);
}

function prepare() {
  transport?.pause();
  session = createId3Session(lab, { dataset: DIGIT_DATASET });
  sessions.push(session); activeDialog=null; viewMode='follow'; pickedTest=''; prediction = null; previewPixel = null; inspectedNode = null; lastFrame = -1;
  transport = createLiveTransport(session, { present });
  render();
}

async function drive(action) {
  if (action === 'play' && transport.playing) { transport.pause(); setMessage('Paused after the current movement.'); return; }
  if (busy) return;
  // `present()` renders the new frame while the transport is pending. Disable
  // the existing controls in place instead of doing a redundant full render
  // before and after every Tick (the tree HTML is hundreds of KB by Tick 6).
  busy = true; syncBusyControls();
  try {
    if (action === 'next') await transport.next();
    else if (action === 'play') await transport.play();
    else if (action === 'back') await transport.review(Math.max(0, transport.cursor - 1));
  } catch (error) { busy = false; render(); setMessage(`Stopped: ${error.cause?.message || error.message}`); return; }
  finally { busy = false; syncBusyControls(); }
}

function updateDrawing() {
  for (const cell of mount.querySelectorAll('[data-id3-draw-cell]')) {
    const value = drawing[Number(cell.dataset.id3DrawCell)];
    cell.style.setProperty('--ink', value / 16); cell.setAttribute('aria-pressed', String(value >= 8));
  }
}

function setDrawing(pixels) {
  if (!Array.isArray(pixels) || pixels.length !== 64 || pixels.some(value => !Number.isFinite(value) || value < 0 || value > 16)) throw Error('A digit needs 64 intensities between 0 and 16.');
  drawing = [...pixels]; prediction = null; render();
}

async function predict(pixels = drawing) {
  if (busy) return null;
  const frameIndex = transport.cursor;
  const produced = await session.predict([...pixels], { frameIndex });
  prediction = { ...produced, frameIndex }; render(); return produced;
}

mount.addEventListener('click', async event => {
  const button = event.target.closest('button');
  if (button?.disabled) return;
  if (button?.hasAttribute('data-id3-open')) {openDialog(button.dataset.id3Open);return;}
  if (button?.hasAttribute('data-id3-close')) {closeDialog();return;}
  if (button?.hasAttribute('data-id3-inspect-node')) {inspectedNode=button.dataset.id3InspectNode;activeDialog='inspect';dialogReturn=`[data-id3-inspect-node="${inspectedNode}"]`;render();return;}
  if (button?.hasAttribute('data-id3-fit')) {viewMode='fit';layoutTree({recenter:true});return;}
  if (button?.hasAttribute('data-id3-current')) {viewMode='manual';zoom=1;applyZoom();centerCurrent();return;}
  if (button?.hasAttribute('data-id3-zoom')) {viewMode='manual';const viewport=mount.querySelector('.id3-tree-scroll'), previous=zoom;zoom=Math.max(.1,Math.min(2,zoom*(button.dataset.id3Zoom==='in'?1.2:1/1.2)));const x=(viewport.scrollLeft+viewport.clientWidth/2)/previous,y=(viewport.scrollTop+viewport.clientHeight/2)/previous;applyZoom();viewport.scrollLeft=x*zoom-viewport.clientWidth/2;viewport.scrollTop=y*zoom-viewport.clientHeight/2;return;}
  if (button?.hasAttribute('data-id3-next')) return drive('next');
  if (button?.hasAttribute('data-id3-play')) return drive('play');
  if (button?.hasAttribute('data-id3-back')) return drive('back');
  if (button?.hasAttribute('data-id3-reset')) { prepare(); return; }
  if (button?.hasAttribute('data-id3-clear')) { setDrawing(Array(64).fill(0)); return; }
  if (button?.hasAttribute('data-id3-predict')) { try { await predict(); } catch (error) { setMessage(error.cause?.message || error.message); } return; }
  if (button?.hasAttribute('data-id3-pixel') || button?.hasAttribute('data-id3-preview')) {
    previewPixel = Number(button.dataset.id3Pixel ?? button.dataset.id3Preview); render(); return;
  }
  if (button?.hasAttribute('data-id3-draw-cell')) {
    // Pointer gestures already painted on pointerdown. Keyboard activation has no detail.
    if (event.detail === 0) { const pixel = Number(button.dataset.id3DrawCell); drawing[pixel] = drawing[pixel] >= 8 ? 0 : 16; if (prediction) { prediction = null; render(); mount.querySelector(`[data-id3-draw-cell="${pixel}"]`)?.focus(); } else updateDrawing(); }
    return;
  }
  if (button?.hasAttribute('data-id3-export')) { const record = recordAt(); if (record) downloadJson(record, `id3-digits-through-${transport.cursor}.json`); return; }
  if (button?.hasAttribute('data-id3-replay')) {
    const record = recordAt(); if (!record) return;
    try {
      viewerSources ??= fetchPageSources(new URL('../../pyto/viewer/', import.meta.url));
      const page = composePage({ ...await viewerSources, record }), url = URL.createObjectURL(new Blob([page], { type: 'text/html' }));
      const link = document.createElement('a'); link.href = url; link.target = '_blank'; link.rel = 'noopener'; link.textContent = 'Open the recorded Tick replay'; link.dataset.id3ReplayLink = '';
      mount.querySelector('[data-id3-message]').replaceChildren(link);
      link.addEventListener('click', () => setTimeout(() => URL.revokeObjectURL(url), 30000), { once: true });
    } catch (error) { setMessage(`Could not open replay: ${error.message}`); }
  }
});
mount.addEventListener('input', async event => {
  if (event.target.hasAttribute('data-id3-scrub') && !busy) { prediction = null; await transport.review(Number(event.target.value)); }
});
mount.addEventListener('change', event => {
  if (event.target.hasAttribute('data-id3-test') && event.target.value !== '') {pickedTest=event.target.value;setDrawing(DIGIT_TEST_SAMPLES[Number(event.target.value)].pixels);}
});
mount.addEventListener('pointerdown', event => {
  const cell = event.target.closest('[data-id3-draw-cell]');
  if (!cell) {const viewport=event.target.closest('.id3-tree-scroll');if(viewport&&!event.target.closest('.id3-node-card')&&event.button===0){pan={x:event.clientX,y:event.clientY,left:viewport.scrollLeft,top:viewport.scrollTop,viewport};viewport.setPointerCapture(event.pointerId);}return;}
  event.preventDefault(); drawingOn = true;
  const pixel = Number(cell.dataset.id3DrawCell); drawingValue = drawing[pixel] >= 8 ? 0 : 16; drawing[pixel] = drawingValue;
  if (prediction) { prediction = null; render(); } else updateDrawing();
});
mount.addEventListener('pointermove', event => {
  if(pan){pan.viewport.scrollLeft=pan.left+pan.x-event.clientX;pan.viewport.scrollTop=pan.top+pan.y-event.clientY;return;}
  if (!drawingOn) return;
  const cell = document.elementFromPoint(event.clientX, event.clientY)?.closest('[data-id3-draw-cell]');
  if (cell && mount.contains(cell)) { drawing[Number(cell.dataset.id3DrawCell)] = drawingValue; updateDrawing(); }
});
window.addEventListener('pointerup', () => { drawingOn = false; pan=null; });
window.addEventListener('pointercancel', () => { drawingOn = false; pan=null; });

window.addEventListener('resize',()=>layoutTree({recenter:true}));

window.id3Demo = { lab, sessions, get session() { return session; }, get transport() { return transport; }, get frame() { return currentFrame(); }, get prediction() { return prediction; }, get drawing() { return [...drawing]; }, get busy() { return busy; }, predict, setDrawing, recordAt, prepare };
prepare();
