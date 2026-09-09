import { safeImage, id } from './domain.js';
import { render as paintDisc } from '../pyto/consumers/discstudio-card/port/painter/painter.mjs';
export const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
export const color = (value, fallback = '#203d36') => /^(#[0-9a-f]{3,8}|transparent)$/i.test(value ?? '') ? value : fallback;
export const fonts = { sans: 'Arial, Helvetica, sans-serif', serif: 'Georgia, Times New Roman, serif', mono: 'Courier New, monospace' };
export const fieldNode = (field, index = 0) => ({ id: id('node'), kind: field.type === 'image' ? 'image' : 'text', binding: field.path, x: 20 + (index % 2) * 145, y: 24 + Math.floor(index / 2) * 48, w: field.type === 'image' ? 140 : 135, h: field.type === 'image' ? 140 : 36, size: field.type === 'number' ? 24 : 18, color: '', bold: true, align: 'left', visible: true, showLabel: field.type === 'number', hideEmpty: false, fit: 'contain', radius: 0, font: 'sans', prefix: '', suffix: '' });
const node = (id, binding, x, y, w, h, size, extra = {}) => ({ id, kind: 'text', binding, x, y, w, h, size, color: '', bold: false, align: 'left', visible: true, showLabel: false, hideEmpty: false, font: 'sans', prefix: '', suffix: '', ...extra });
const photo = (x, y, size) => node('photo', 'disc.photo', x, y, size, size, 14, { kind: 'image', fit: 'contain', radius: 0 });
const flights = (x, y, cell, size) => ['speed', 'glide', 'turn', 'fade'].map((k, i) => node(k, `disc.mold.flight.${k}`, x + i * cell, y, cell - 4, 44, size, { bold: true, showLabel: true, align: 'center' }));
const common = { kind: 'DisplayCard', background: '#203d36', foreground: '#fcfbf5', accent: '#b9d789', radius: 16, border: '#456157', font: 'sans', highlight: 'ring', scoreMotion: 'pulse', duration: 350 };
export function defaultPresets() {
  return {
    broadcast: { ...common, id: 'broadcast', name: 'Studio · lower third', width: 400, height: 174, nodes: [photo(14, 28, 110), node('maker', 'disc.mold.manufacturer.name', 138, 16, 174, 15, 11), node('mold', 'disc.mold.name', 138, 37, 180, 31, 25, { bold: true, font: 'serif' }), node('nickname', 'disc.nickname', 138, 75, 171, 15, 11), ...flights(135, 111, 43, 21), node('score', 'entry.score', 325, 51, 65, 61, 38, { bold: true, align: 'center', showLabel: true, context: 'battle' })] },
    showcase: { ...common, id: 'showcase', name: 'Studio · showcase', width: 320, height: 402, nodes: [photo(73, 20, 174), node('maker', 'disc.mold.manufacturer.name', 24, 207, 272, 17, 12), node('mold', 'disc.mold.name', 24, 232, 272, 43, 34, { bold: true, font: 'serif' }), node('nickname', 'disc.nickname', 24, 282, 272, 20, 13), ...flights(19, 331, 72, 26), node('score', 'entry.score', 260, 20, 45, 48, 26, { align: 'center', showLabel: true, context: 'battle' })] },
    minimal: { ...common, id: 'minimal', name: 'Paper · name first', width: 500, height: 132, background: '#f9f7ef', foreground: '#203d36', border: '#c7d0c1', accent: '#718d48', nodes: [photo(12, 14, 103), node('maker', 'disc.mold.manufacturer.name', 135, 17, 270, 15, 11), node('mold', 'disc.mold.name', 134, 40, 278, 34, 28, { bold: true, font: 'serif' }), node('nickname', 'disc.nickname', 136, 85, 260, 20, 14), node('score', 'entry.score', 425, 36, 61, 63, 38, { align: 'center', showLabel: true, context: 'battle' })] },
    discImage: { ...common, id: 'discImage', name: 'Disc · exact specimen', kind: 'DiscImage', width: 300, height: 300, background: '#e6ebde', foreground: '#203d36', border: '#d6ddce', nodes: [photo(26, 18, 248), node('label', 'disc.nickname', 15, 271, 270, 18, 12, { align: 'center' })] }
  };
}

/** One material, reused by shelf, card editor and comparison. No photo recognition is claimed. */
export function prepareDiscArt({ disc, mold, maker }) {
  if (disc.photo && safeImage(disc.photo)) return { kind: 'photo', src: disc.photo, alt: disc.nickname || mold?.name || 'Physical disc', sample: false };
  const inputs = artInputs({ disc, mold, maker });
  return { kind: 'painted', svg: paintDisc(...inputs), alt: `Sample artwork · ${inputs[5]}`, sample: true, inputs };
}
export function artInputs({ disc, mold, maker }) {
  const family = disc.artFamily || 'wind-rose';
  const seed = Number.isFinite(disc.sampleHue) ? disc.sampleHue : 146;
  const base = paintColor(disc.artBase, '#e6ebde');
  const accent = paintColor(disc.artAccent, '#456157');
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
export function composeOverlay({ cards, layout }) {
  const items = Object.values(cards), width = 1920, height = 1080, gap = Math.max(0, Math.min(100, Number(layout.gap) || 0));
  if (!items.length) return { width, height, placements: [], bounds: { x: 0, y: 0, width: 0, height: 0 }, cards: items, empty: true };
  const columns = layout.arrangement === 'stack' ? 1 : layout.arrangement === 'grid' ? Math.min(2, items.length) : items.length;
  const maxW = Math.max(...items.map(c => c.width)), maxH = Math.max(...items.map(c => c.height)), rows = Math.ceil(items.length / columns);
  const w = columns * maxW + (columns - 1) * gap, h = rows * maxH + (rows - 1) * gap;
  const scale = Math.min(Number(layout.scale) || 1, 1800 / w, 960 / h);
  const anchor = layout.anchor || 'bottom-left', x = anchor === 'center' ? (width - w * scale) / 2 : anchor.endsWith('right') ? width - 60 - w * scale : 60;
  const y = anchor === 'center' ? (height - h * scale) / 2 : anchor.startsWith('top') ? 60 : height - 60 - h * scale;
  return { width, height, scale, bounds: { x, y, width: w * scale, height: h * scale }, cards: items, placements: items.map((card, i) => ({ card, x: x + i % columns * (maxW + gap) * scale, y: y + Math.floor(i / columns) * (maxH + gap) * scale })), warnings: items.flatMap(c => c.warnings) };
}
export function materializeOverlay({ scene }) {
  const body = scene.placements.map((p, i) => `<g transform="translate(${p.x} ${p.y}) scale(${scene.scale})">${cardMarkup(p.card, `card-${i}`)}</g>`).join('');
  return { svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${scene.width}" height="${scene.height}" viewBox="0 0 ${scene.width} ${scene.height}" role="img" aria-label="DiscStudio transparent overlay">${body}</svg>`, width: scene.width, height: scene.height, cardCount: scene.cards.length, bounds: scene.bounds, warnings: scene.warnings ?? [] };
}
