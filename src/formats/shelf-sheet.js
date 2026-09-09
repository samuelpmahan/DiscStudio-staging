/** Printable DiscShelf sheet calculation using the shared domain Parts. */
import { render as paintDisc } from '../../pyto/consumers/discstudio-card/port/painter/painter.mjs';
import { prepareDiscArt } from '../presentation.js';

const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const asMap = (value) => Array.isArray(value) ? Object.fromEntries(value.map((item) => [item.id, item])) : (value || {});
const hashSeed = (text) => { let h = 2166136261; for (const c of String(text)) h = Math.imul(h ^ c.codePointAt(0), 16777619); return h >>> 0; };
const flight = (mold) => ['speed', 'glide', 'turn', 'fade'].map((key) => mold?.flight?.[key] ?? '—').join(' / ');
const artInner = (svg) => { const root = /<svg\b[^>]*>/s.exec(svg), close = svg.lastIndexOf('</svg>'); if (!root || close < root.index + root[0].length) throw new Error('Painter returned malformed SVG.'); const inner = svg.slice(root.index + root[0].length, close); if (/<\/?svg\b/i.test(inner)) throw new Error('Painter art contains a nested SVG root.'); return inner; };

/** Inputs are shared-world Parts: bag, discs, molds, manufacturers. */
export function shelfSheet({ bag, discs, molds, manufacturers, family = 'orbit-foundry', columns = 4 } = {}) {
  if (!bag || typeof bag.id !== 'string' || !Array.isArray(bag.discIds)) throw new Error('Shelf sheet requires a Bag Part.');
  const discMap = asMap(discs), moldMap = asMap(molds), makerMap = asMap(manufacturers), count = bag.discIds.length;
  const cols = Math.max(1, Math.min(8, Math.trunc(columns) || 4)), cellW = 180, cellH = 146, margin = 24, headerH = 64;
  const rows = Math.ceil(count / cols), width = margin * 2 + cols * cellW, height = margin * 2 + headerH + rows * cellH;
  const cells = bag.discIds.map((discId, index) => {
    const disc = discMap[discId]; if (!disc) throw new Error(`Bag references missing physical disc '${discId}'.`);
    const mold = moldMap[disc.moldId]; if (!mold) throw new Error(`Disc '${discId}' has unresolved mold identity.`);
    const maker = makerMap[mold.manufacturerId]; if (!maker) throw new Error(`Mold '${mold.id}' has unresolved manufacturer identity.`);
    const x = margin + (index % cols) * cellW, y = margin + headerH + Math.floor(index / cols) * cellH;
    const prepared = prepareDiscArt({ disc, mold, maker });
    const art = prepared.kind === 'photo'
      ? `<image href=\"${esc(prepared.src)}\" width=\"512\" height=\"512\" preserveAspectRatio=\"xMidYMid meet\"/>`
      : artInner(paintDisc(disc.artFamily || family, hashSeed(disc.id), '#b9d789', '#203d36', 96, mold.name));
    return { disc, mold, maker, x, y, art };
  });
  const body = [`<rect width="${width}" height="${height}" fill="#f9f7ef"/>`, `<text x="${margin}" y="${margin + 22}" font-family="Arial, Helvetica, sans-serif" font-size="18" font-weight="700" fill="#203d36">${esc(bag.name || 'DiscShelf')}</text>`, `<text x="${width - margin}" y="${margin + 22}" text-anchor="end" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#718d48">${count} PHYSICAL DISC${count === 1 ? '' : 'S'}</text>`, ...cells.map(({ disc, mold, maker, x, y, art }) => { const title = `${maker.name} · ${mold.name}`; return `<g data-disc="${esc(disc.id)}"><svg x="${x}" y="${y}" width="96" height="96" viewBox="0 0 512 512" role="img" aria-label="${esc(title)}">${art}</svg><text x="${x}" y="${y + 112}" font-family="Arial, Helvetica, sans-serif" font-size="12" font-weight="700" fill="#203d36">${esc(mold.name)}</text><text x="${x}" y="${y + 128}" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#5d6c5e">${esc(flight(mold))}</text></g>`; })].join('');
  return { kind: 'ShelfSheet', format: 'disc.format.shelfSheet', bagId: bag.id, discCount: count, width, height, family, columns: cols, svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(bag.name || 'DiscShelf')}">${body}</svg>` };
}
export default shelfSheet;
