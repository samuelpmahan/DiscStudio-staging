import { safeImage, id } from './domain.js';
import { render as paintDisc, FAMILIES } from '../pyto/consumers/discstudio-card/port/painter/painter.mjs';
import { canvasFor, defaultSafe } from './frames.js';
export const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
export const color = (value, fallback = '#203d36') => /^(#[0-9a-f]{3,8}|transparent)$/i.test(value ?? '') ? value : fallback;
export const fonts = { sans: 'Arial, Helvetica, sans-serif', serif: 'Georgia, Times New Roman, serif', mono: 'Courier New, monospace' };
export const fieldNode = (field, index = 0) => ({ id: id('node'), kind: field.type === 'image' ? 'image' : 'text', binding: field.path, x: 20 + (index % 2) * 145, y: 24 + Math.floor(index / 2) * 48, w: field.type === 'image' ? 140 : 135, h: field.type === 'image' ? 140 : 36, size: field.type === 'number' ? 24 : 18, color: '', bold: true, align: 'left', visible: true, showLabel: field.type === 'number', hideEmpty: false, fit: 'contain', radius: 0, font: 'sans', prefix: '', suffix: '' });
const node = (id, binding, x, y, w, h, size, extra = {}) => ({ id, kind: 'text', binding, x, y, w, h, size, color: '', bold: false, align: 'left', visible: true, showLabel: false, hideEmpty: false, font: 'sans', prefix: '', suffix: '', ...extra });
const photo = (x, y, size) => node('photo', 'disc.photo', x, y, size, size, 14, { kind: 'image', fit: 'contain', radius: 0 });
const flights = (x, y, cell, size) => ['speed', 'glide', 'turn', 'fade'].map((k, i) => node(k, `disc.mold.flight.${k}`, x + i * cell, y, cell - 4, 44, size, { bold: true, showLabel: true, align: 'center' }));
// The preset IS the projection layer (task 79): background, foreground,
// accent, font and radius are each `null` here unless a specific look is
// worth keeping as an override, and `sponsor` is simply left off (absent
// means inherit, same as null). `border`, `highlight`, `scoreMotion` and
// `duration` are not part of the cascade -- they stay ordinary preset fields.
const common = { kind: 'DisplayCard', background: null, foreground: null, accent: null, radius: null, border: '#456157', font: null, highlight: 'ring', scoreMotion: 'pulse', duration: 350 };
export function defaultPresets() {
  return {
    broadcast: { ...common, id: 'broadcast', name: 'Studio · lower third', width: 400, height: 174, sponsor: 'CHAINSPOT', nodes: [photo(14, 28, 110), node('maker', 'disc.mold.manufacturer.name', 138, 16, 174, 15, 11), node('mold', 'disc.mold.name', 138, 37, 180, 31, 25, { bold: true, font: 'serif' }), node('nickname', 'disc.nickname', 138, 75, 171, 15, 11), ...flights(135, 111, 43, 21), node('score', 'entry.score', 325, 51, 65, 61, 38, { bold: true, align: 'center', showLabel: true, context: 'battle' })] },
    showcase: { ...common, id: 'showcase', name: 'Studio · showcase', width: 320, height: 402, nodes: [photo(73, 20, 174), node('maker', 'disc.mold.manufacturer.name', 24, 207, 272, 17, 12), node('mold', 'disc.mold.name', 24, 232, 272, 43, 34, { bold: true, font: 'serif' }), node('nickname', 'disc.nickname', 24, 282, 272, 20, 13), ...flights(19, 331, 72, 26), node('score', 'entry.score', 260, 20, 45, 48, 26, { align: 'center', showLabel: true, context: 'battle' })] },
    minimal: { ...common, id: 'minimal', name: 'Paper · name first', width: 500, height: 132, background: '#f9f7ef', foreground: '#203d36', border: '#c7d0c1', accent: '#718d48', nodes: [photo(12, 14, 103), node('maker', 'disc.mold.manufacturer.name', 135, 17, 270, 15, 11), node('mold', 'disc.mold.name', 134, 40, 278, 34, 28, { bold: true, font: 'serif' }), node('nickname', 'disc.nickname', 136, 85, 260, 20, 14), node('score', 'entry.score', 425, 36, 61, 63, 38, { align: 'center', showLabel: true, context: 'battle' })] },
    discImage: { ...common, id: 'discImage', name: 'Disc · exact specimen', kind: 'DiscImage', width: 300, height: 300, background: '#e6ebde', foreground: '#203d36', border: '#d6ddce', nodes: [photo(26, 18, 248), node('label', 'disc.nickname', 15, 271, 270, 18, 12, { align: 'center' })] }
  };
}

/** One material, reused by shelf, card editor and comparison. No photo recognition is claimed. */
export function prepareDiscArt({ disc, mold, maker, assignment = null }) {
  if (disc.photo && safeImage(disc.photo)) return { kind: 'photo', src: disc.photo, alt: disc.nickname || mold?.name || 'Physical disc', sample: false };
  const inputs = artInputs({ disc, mold, maker, assignment });
  return { kind: 'painted', svg: paintDisc(...inputs), alt: `Sample artwork · ${inputs[5]}`, sample: true, inputs };
}
/** hsl -> #rrggbb, so a disc's sample hue can be handed to the painter as authored colours are. */
export function hslHex(h, s, l) {
  const sat = s / 100, light = l / 100, k = n => (n + h / 30) % 12, a = sat * Math.min(light, 1 - light);
  const f = n => light - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
  return '#' + [f(0), f(8), f(4)].map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join('');
}
/**
 * A disc with no authored art colours is painted in its own sample hue: the
 * base and the accent the original prepareDiscArt drew (hsl(hue 35% 72%) and a
 * darker hsl(hue 26% 40%)), so twelve discs are twelve colours, not one. The
 * painter port (2026-09-09) had handed every such disc one fixed pair.
 */
export function sampleColors(hue) { return [hslHex(hue, 35, 72), hslHex(hue, 26, 40)]; }
/**
 * A disc with no authored art family gets one of the painter's sixteen, chosen
 * by its id and nothing else (the owner, 2026-09-11: "I just want all the cool
 * art that I enabled ai to make manually to be visible"); an authored family
 * always wins, and the same disc always gets the same family.
 */
export function sampleFamily(discId) {
  let h = 7; for (const ch of String(discId || '')) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return FAMILIES[h % FAMILIES.length];
}
export function artInputs({ disc, mold, maker, assignment = null }) {
  // authored first; then the shelf-wide assignment (fn.art.assign, px.art.assignment); the per-id hash only when neither exists
  const family = disc.artFamily || assignment?.assignment?.[disc.id] || sampleFamily(disc.id);
  const seed = Number.isFinite(disc.sampleHue) ? disc.sampleHue : 146;
  const [sampleBase, sampleAccent] = sampleColors(seed);
  const base = paintColor(disc.artBase, sampleBase);
  const accent = paintColor(disc.artAccent, sampleAccent);
  const target = 96;
  const label = `${maker?.name || 'Disc Studio'} · ${mold?.name || disc.nickname || 'Your disc'}`;
  return [family, seed, base, accent, target, label];
}
const paintColor = (value, fallback) => {
  const sanitized = color(value, fallback);
  return /^#[0-9a-f]{6}$/i.test(sanitized) ? sanitized : fallback;
};
const display = (value, unit) => value == null || value === '' ? '—' : Array.isArray(value) ? value.join(' · ') : typeof value === 'boolean' ? (value ? 'Yes' : 'No') : `${value}${unit ? ` ${unit}` : ''}`;
/** The inner markup of a painter SVG document, for embedding inside a card or a sheet. */
export const artInner = (svg) => { const root = /<svg\b[^>]*>/s.exec(svg), close = svg.lastIndexOf('</svg>'); if (!root || close < root.index + root[0].length) throw new Error('Painter returned malformed SVG.'); const inner = svg.slice(root.index + root[0].length, close); if (/<\/?svg\b/i.test(inner)) throw new Error('Painter art contains a nested SVG root.'); return inner; };
export function composeCard({ fields, art, preset, entry = null }) {
  const byPath = Object.fromEntries(fields.map(f => [f.path, f]));
  const warnings = [];
  const nodes = preset.nodes.filter(n => n.visible !== false && (n.context !== 'battle' || entry)).map(n => {
    const field = byPath[n.binding];
    if (!field && n.binding) warnings.push(`Unresolved binding: ${n.binding}`);
    const value = n.binding ? field?.value : n.text;
    if (n.hideEmpty && (value == null || value === '')) return null;
    if (n.x < 0 || n.y < 0 || n.x + n.w > preset.width || n.y + n.h > preset.height) warnings.push(`${field?.label || n.id} extends outside the card.`);
    return { ...n, field, value, content: `${n.prefix || ''}${display(value, field?.unit)}${n.suffix || ''}` };
  }).filter(Boolean);
  return { kind: 'DisplayCard', presetId: preset.id, width: preset.width, height: preset.height, preset, art, entry, nodes, warnings };
}

function renderNode(n, card, uid) {
  const p = card.preset, clip = `${uid}-${n.id}`;
  if (n.kind === 'image') {
    let image;
    if (n.binding === 'disc.photo') image = card.art;
    else image = safeImage(n.value) ? { kind: 'photo', src: n.value } : null;
    let markup = '';
    if (image?.kind === 'photo') markup = `<image href="${esc(image.src)}" width="${n.w}" height="${n.h}" preserveAspectRatio="${n.fit === 'cover' ? 'xMidYMid slice' : 'xMidYMid meet'}"/>`;
    else if (image?.kind === 'painted') markup = `<svg width="${n.w}" height="${n.h}" viewBox="0 0 512 512" preserveAspectRatio="${n.fit === 'cover' ? 'xMidYMid slice' : 'xMidYMid meet'}">${artInner(image.svg)}</svg>`;
    else markup = `<rect width="${n.w}" height="${n.h}" fill="#dce3d6"/><text x="${n.w / 2}" y="${n.h / 2}" text-anchor="middle" font-size="12" fill="#42574c">Add image</text>`;
    return `<g data-node="${esc(n.id)}" transform="translate(${n.x} ${n.y})"><defs><clipPath id="${clip}"><rect width="${n.w}" height="${n.h}" rx="${Math.max(0, Math.min(n.radius || 0, n.w / 2))}"/></clipPath></defs><g clip-path="url(#${clip})">${markup}</g></g>`;
  }
  const text = n.content, size = Math.max(4, Math.min(n.size, n.w / Math.max([...text].length * .6, 1)));
  const x = n.align === 'center' ? n.x + n.w / 2 : n.align === 'right' ? n.x + n.w : n.x;
  const anchor = n.align === 'center' ? 'middle' : n.align === 'right' ? 'end' : 'start';
  const baseline = n.y + Math.min(size, n.h * (n.showLabel ? .70 : .9));
  const label = n.showLabel ? `<text x="${x}" y="${baseline + Math.min(15, n.h * .30)}" text-anchor="${anchor}" font-size="${Math.min(9, size * .45)}" opacity=".68" letter-spacing=".6">${esc(n.field?.label || 'Label')}</text>` : '';
  return `<g data-node="${esc(n.id)}" fill="${color(n.color || p.foreground)}" font-family="${fonts[n.font || p.font] || fonts.sans}"><text x="${x}" y="${baseline}" text-anchor="${anchor}" font-size="${size}" font-weight="${n.bold ? 700 : 400}">${esc(text)}</text>${label}</g>`;
}
export function cardMarkup(card, uid = 'card') {
  const p = card.preset, hi = card.entry?.highlighted, accent = color(p.accent, '#b9d789');
  let body = `<rect x="2" y="2" width="${card.width - 4}" height="${card.height - 4}" rx="${Math.max(0, p.radius || 0)}" fill="${color(p.background, '#203d36')}" stroke="${hi && p.highlight !== 'stripe' ? accent : color(p.border)}" stroke-width="${hi ? 4 : 1}"/>`;
  if (hi && p.highlight === 'stripe') body += `<rect x="17" y="0" width="${card.width - 34}" height="5" rx="2" fill="${accent}"/>`;
  body += card.nodes.map(n => renderNode(n, card, uid)).join('');
  if (card.entry?.winner) body += `<g aria-label="Authored winner"><circle cx="${card.width - 18}" cy="17" r="12" fill="${accent}"/><text x="${card.width - 18}" y="22" text-anchor="middle" font-size="15" fill="#203d36">★</text></g>`;
  return `<g data-entry="${esc(card.entry?.id || '')}" data-motion="${esc(p.scoreMotion || 'none')}" data-duration="${Number(p.duration) || 350}">${body}</g>`;
}
export function cardSvg({ card }) { return { svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${card.width} ${card.height}" width="${card.width}" height="${card.height}" role="img" aria-label="DisplayCard">${cardMarkup(card)}</svg>`, width: card.width, height: card.height }; }
/**
 * The anchors a course arrangement stands cards on, out of whichever Part the
 * Stages have published: S4's holes (`px.holes.objects`), the round's own
 * waypoints, or S5's course graph. One anchor per hole -- the basket, where the
 * disc it is credited for ends up, falling back to the tee for a hole whose
 * basket S4 could not place.
 *
 * A frame is the canonical raster the anchors were measured in. Only S5's graph
 * carries one; for the others the anchors' own extent is the frame, padded, so
 * the arrangement never claims a raster size it was not given.
 */
export function courseAnchors(course) {
  if (!course) throw new Error('No course has been built yet. Open Course, give it a capture and run the pipeline; then this arrangement can stand your cards at its holes.');
  let anchors = [];
  if (Array.isArray(course)) anchors = course.map(hole => ({ id: `hole-${hole.number}`, label: `Hole ${hole.number}`, at: (hole.basket ?? hole.tee)?.at ?? null })).filter(anchor => anchor.at);
  else if (Array.isArray(course.holes) && course.holes.length && course.holes[0].basket?.at) anchors = course.holes.map(hole => ({ id: `hole-${hole.number}`, label: `Hole ${hole.number}`, at: hole.basket.at }));
  else if (Array.isArray(course.waypoints)) anchors = course.waypoints.map(point => ({ id: point.id, label: point.id, at: point.at }));
  if (!anchors.length) throw new Error('The course that was built has no hole a card could stand at.');
  const frame = course.frame && course.frame.widthPx
    ? { widthPx: course.frame.widthPx, heightPx: course.frame.heightPx }
    : (() => {
      const xs = anchors.map(anchor => anchor.at[0]), ys = anchors.map(anchor => anchor.at[1]);
      const pad = Math.max(40, Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)) * 0.2);
      return { widthPx: Math.max(...xs) + pad, heightPx: Math.max(...ys) + pad, originX: Math.min(...xs) - pad, originY: Math.min(...ys) - pad };
    })();
  return { anchors, frame: { originX: 0, originY: 0, ...frame } };
}
/**
 * The course arrangement: the same cards, placed where the holes are. The
 * capture's frame is fitted into `safe` -- the box the overlay's own frame
 * leaves for cards, which on an unframed 1920x1080 canvas is the 60px inset it
 * always was -- each card is centred on its hole, and a card past the last hole
 * starts the holes again one card-height lower, so a twelve-disc comparison on
 * a nine-hole course is still every card, placed.
 */
function courseScene({ items, layout, course, width, height, gap, safe }) {
  const { anchors, frame } = courseAnchors(course);
  const maxW = Math.max(...items.map(card => card.width)), maxH = Math.max(...items.map(card => card.height));
  const frameW = Math.max(1, frame.widthPx - frame.originX), frameH = Math.max(1, frame.heightPx - frame.originY);
  const fit = Math.min(safe.width / frameW, safe.height / frameH);
  const scale = Math.min(Number(layout.scale) || 1, safe.width / maxW, safe.height / maxH);
  const offsetX = safe.x + (safe.width - frameW * fit) / 2, offsetY = safe.y + (safe.height - frameH * fit) / 2;
  const placements = items.map((card, index) => {
    const anchor = anchors[index % anchors.length], round = Math.floor(index / anchors.length);
    const centreX = offsetX + (anchor.at[0] - frame.originX) * fit, centreY = offsetY + (anchor.at[1] - frame.originY) * fit + round * (maxH + gap) * scale;
    const x = Math.max(safe.x, Math.min(safe.x + safe.width - card.width * scale, centreX - (card.width * scale) / 2));
    const y = Math.max(safe.y, Math.min(safe.y + safe.height - card.height * scale, centreY - (card.height * scale) / 2));
    return { card, x, y, anchor: { id: anchor.id, label: anchor.label, at: anchor.at, x: centreX, y: centreY } };
  });
  const xs = placements.map(placement => placement.x), ys = placements.map(placement => placement.y);
  return {
    width, height, scale, arrangement: 'course', orientation: layout.orientation === 'portrait' ? 'portrait' : 'landscape', safe, frame, anchors,
    bounds: { x: Math.min(...xs), y: Math.min(...ys), width: Math.max(...xs) + maxW * scale - Math.min(...xs), height: Math.max(...ys) + maxH * scale - Math.min(...ys) },
    cards: items, placements, warnings: items.flatMap(card => card.warnings)
  };
}
/**
 * The comparison, on the canvas its layout names: 1920x1080 landscape, or the
 * 1080x1920 vertical one a phone wants. `frame` is the frame Part
 * (fn.overlay.frame) when one was composed; the cards are fitted into its safe
 * area, and with no frame that area is the canvas inset by 60px -- which is
 * exactly the box the landscape overlay always used, so an unframed landscape
 * scene is placed byte for byte as it was before the vertical canvas existed.
 */
export function composeOverlay({ cards, layout, course = null, frame = null }) {
  const items = Object.values(cards), canvas = canvasFor(layout.orientation), width = canvas.width, height = canvas.height;
  const gap = Math.max(0, Math.min(100, Number(layout.gap) || 0)), safe = frame?.safe ?? defaultSafe(layout.orientation);
  if (!items.length) return { width, height, orientation: canvas.id, safe, frame, placements: [], bounds: { x: 0, y: 0, width: 0, height: 0 }, cards: items, empty: true };
  if (layout.arrangement === 'course') return { ...courseScene({ items, layout, course, width, height, gap, safe }), frame };
  const columns = layout.arrangement === 'stack' ? 1 : layout.arrangement === 'grid' ? Math.min(2, items.length) : items.length;
  const maxW = Math.max(...items.map(c => c.width)), maxH = Math.max(...items.map(c => c.height)), rows = Math.ceil(items.length / columns);
  const w = columns * maxW + (columns - 1) * gap, h = rows * maxH + (rows - 1) * gap;
  const scale = Math.min(Number(layout.scale) || 1, safe.width / w, safe.height / h);
  const anchor = layout.anchor || 'bottom-left', x = anchor === 'center' ? safe.x + (safe.width - w * scale) / 2 : anchor.endsWith('right') ? safe.x + safe.width - w * scale : safe.x;
  const y = anchor === 'center' ? safe.y + (safe.height - h * scale) / 2 : anchor.startsWith('top') ? safe.y : safe.y + safe.height - h * scale;
  return { width, height, orientation: canvas.id, safe, frame, scale, bounds: { x, y, width: w * scale, height: h * scale }, cards: items, placements: items.map((card, i) => ({ card, x: x + i % columns * (maxW + gap) * scale, y: y + Math.floor(i / columns) * (maxH + gap) * scale })), warnings: items.flatMap(c => c.warnings) };
}
/**
 * The frame beneath the cards, drawn from the model `fn.overlay.frame`
 * composed: its fill, its title strip and its sponsor lockup, every colour and
 * font the cards cascade's own global tokens. An unframed scene draws nothing
 * here, so its SVG is the transparent overlay it always was.
 */
export function frameMarkup(frame) {
  if (!frame) return '';
  let body = '';
  if (frame.fill && frame.fill !== 'none') body += `<rect width="${frame.width}" height="${frame.height}" fill="${color(frame.fill)}"/>`;
  if (frame.title) {
    const t = frame.title, centred = t.align === 'center', x = centred ? t.x + t.w / 2 : t.x;
    body += `<g font-family="${fonts[t.font] || fonts.sans}"><text x="${x}" y="${t.y + t.size}" text-anchor="${centred ? 'middle' : 'start'}" font-size="${t.size}" font-weight="700" fill="${color(t.color, '#fcfbf5')}">${esc(t.text)}</text><rect x="${t.rule.x + (centred ? (t.w - t.rule.w) / 2 : 0)}" y="${t.rule.y}" width="${t.rule.w}" height="${t.rule.h}" rx="2" fill="${color(t.rule.fill, '#b9d789')}"/></g>`;
  }
  if (frame.sponsor) {
    const p = frame.sponsor;
    body += `<text x="${p.x + p.w}" y="${p.y + p.size}" text-anchor="end" font-family="${fonts[p.font] || fonts.sans}" font-size="${p.size}" font-weight="700" letter-spacing="1.6" fill="${color(p.color, '#b9d789')}">${esc(p.text)}</text>`;
  }
  return body ? `<g data-frame="${esc(frame.presetId)}" aria-label="${esc(frame.note)}">${body}</g>` : '';
}
export function materializeOverlay({ scene, frame = null }) {
  const body = scene.placements.map((p, i) => `<g transform="translate(${p.x} ${p.y}) scale(${scene.scale})">${cardMarkup(p.card, `card-${i}`)}</g>`).join('');
  const behind = frameMarkup(frame ?? scene.frame ?? null);
  return { svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${scene.width}" height="${scene.height}" viewBox="0 0 ${scene.width} ${scene.height}" role="img" aria-label="DiscStudio transparent overlay">${behind}${body}</svg>`, width: scene.width, height: scene.height, orientation: scene.orientation ?? 'landscape', cardCount: scene.cards.length, bounds: scene.bounds, warnings: scene.warnings ?? [] };
}
