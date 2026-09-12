// Port of the two promoted card renderers to dependency-free ES modules.
//
//   renderSingle(card, art, width) -> string   (studio *botanical*, _card_botanical.py)
//   renderBattle(card, art, width) -> string   (studio *signal*, _card_signal.py)
//
// card_render.py is the seam: it re-exports render_single from _card_botanical and
// render_battle from _card_signal, so those are the two halves ported here. Each
// half keeps its own private helpers under its own prefix, because the two studios
// spell the same idea differently -- botanical's `_num` folds "-0" to "0" and
// signal's `_f` does not, botanical's `fit` is a raw float and signal's `_fit`
// rounds to one place, botanical strips no <title> from the embedded art and
// signal does. Those differences are load-bearing for byte identity.
//
// Runs under Node 22 and in a browser. No npm, no DOM.

import { escape as esc, fmt, fmt2, pyRound, pyRoundInt } from './core.mjs';

// ---------------------------------------------------------------- shared bits

const EM_DASH = '—';
const EN_DASH = '–';
const MIDDOT = '·';
const ELLIPSIS = '…';

/** Python's str() of a value straight out of JSON, as the sources use it. */
function pyText(value) {
  if (value === null || value === undefined) return 'None';
  if (typeof value === 'boolean') return value ? 'True' : 'False';
  if (typeof value === 'number') return numText(value);
  return String(value);
}

/** str() of a number that arrived as JSON: an integer prints bare. */
function numText(x) {
  if (Number.isInteger(x) && !Object.is(x, -0)) return String(x);
  return String(x);
}

/** Python's f"{x:g}" (six significant digits). */
function fmtG(x) {
  if (Number.isNaN(x)) return 'nan';
  if (!Number.isFinite(x)) return x > 0 ? 'inf' : '-inf';
  if (x === 0) return Object.is(x, -0) ? '-0' : '0';
  const prec = 6;
  const e = Number(x.toExponential(prec - 1).split('e')[1]);
  if (e < -4 || e >= prec) {
    let [m, ex] = x.toExponential(prec - 1).split('e');
    if (m.includes('.')) m = m.replace(/0+$/, '').replace(/\.$/, '');
    const sign = ex[0] === '-' ? '-' : '+';
    let digits = ex.replace(/^[-+]/, '');
    if (digits.length < 2) digits = '0' + digits;
    return `${m}e${sign}${digits}`;
  }
  let s = fmt(x, Math.max(0, prec - 1 - e));
  if (s.includes('.')) s = s.replace(/0+$/, '').replace(/\.$/, '');
  return s;
}

/** Python's str.rstrip(chars) for a single-character set. */
function rstrip(text, ch) {
  let end = text.length;
  while (end > 0 && text[end - 1] === ch) end--;
  return text.slice(0, end);
}

/** Python's str.strip() over ASCII whitespace, which is all these inputs carry. */
function pyStrip(text) {
  return String(text).replace(/^[\s]+|[\s]+$/g, '');
}

/** `str(value or "")`: Python's truthiness, so 0 and "" and None all fall back. */
function orEmpty(value) {
  return value ? pyText(value) : '';
}

// =============================================================== studio botanical
//
// _card_botanical.py, verbatim in behaviour. render_single is the promoted half.

const B_FLIGHT_KEYS = [['flight1', 'SPEED'], ['flight2', 'GLIDE'], ['flight3', 'TURN'], ['flight4', 'FADE']];

const B_HEX = /^#[0-9a-fA-F]{6}$/;
const B_ROOT = /^\s*(?:<\?xml[^>]*\?>\s*)?<svg\b([^>]*)>/;
const B_VIEWBOX = /viewBox="([^"]*)"/;
const B_ID = /id="([^"]+)"/g;

const STOCK = '#f6efdd';
const EDGE = '#efe5cd';
const INK = '#2c2a20';
const B_MUTED = '#7d735c';
const HAIR = '#cdbf9c';
const B_RULE = '#8d7f5e';
const SERIF = 'serif';
const SANS = 'sans-serif';

/** f"{value:.2f}" with trailing zeros and the point stripped; "-0" folds to "0". */
function bNum(value) {
  const text = rstrip(rstrip(fmt2(value), '0'), '.');
  return (text === '' || text === '-0') ? '0' : text;
}

function bEsc(value) {
  return esc(value === null || value === undefined ? '' : pyText(value));
}

function bRgb(value) {
  return [parseInt(value.slice(1, 3), 16), parseInt(value.slice(3, 5), 16), parseInt(value.slice(5, 7), 16)];
}

function hex2(n) {
  return n.toString(16).padStart(2, '0');
}

function bMix(a, b, t) {
  const [ar, ag, ab] = bRgb(a);
  const [br, bg, bb] = bRgb(b);
  t = t < 0.0 ? 0.0 : (t > 1.0 ? 1.0 : t);
  return '#' + hex2(pyRoundInt(ar + (br - ar) * t)) + hex2(pyRoundInt(ag + (bg - ag) * t)) +
    hex2(pyRoundInt(ab + (bb - ab) * t));
}

function bLuma(value) {
  const [r, g, b] = bRgb(value);
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0;
}

function inkOf(participant) {
  let value = participant.color;
  value = (typeof value === 'string' && B_HEX.test(value)) ? value.toLowerCase() : '#6d7a4a';
  while (bLuma(value) > 0.52) value = bMix(value, '#241f16', 0.28);
  return value;
}

function bFlight(value) {
  if (value === null || value === undefined || value === '' || typeof value === 'boolean') return EM_DASH;
  if (typeof value === 'number') {
    // JSON hands both Python ints and Python floats to this branch; an integral
    // value prints the same either way, and a fractional one takes %g.
    return Number.isInteger(value) ? String(value) : fmtG(value);
  }
  return bEsc(value);
}

function bFit(text, size, box, ratio = 0.54) {
  const span = Math.max(text.length * ratio, 1.0);
  return Math.max(7.0, Math.min(size, box / span));
}

function bText(x, y, body, size, fill = INK, anchor = 'start', family = SANS, spacing = 0.0,
                weight = 400, style = '', opacity = 1.0) {
  const bits = [`<text x="${bNum(x)}" y="${bNum(y)}" font-family="${family}" font-size="${bNum(size)}"`];
  if (weight !== 400) bits.push(` font-weight="${weight}"`);
  if (anchor !== 'start') bits.push(` text-anchor="${anchor}"`);
  if (spacing) bits.push(` letter-spacing="${bNum(spacing)}"`);
  if (style) bits.push(` font-style="${style}"`);
  if (opacity !== 1.0) bits.push(` opacity="${bNum(opacity)}"`);
  bits.push(` fill="${fill}">${body}</text>`);
  return bits.join('');
}

function bRule(x1, y1, x2, y2, color = HAIR, w = 1.0, opacity = 1.0) {
  return `<path d="M${bNum(x1)} ${bNum(y1)}L${bNum(x2)} ${bNum(y2)}" stroke="${color}"` +
    ` stroke-width="${bNum(w)}"` + (opacity !== 1 ? ` opacity="${bNum(opacity)}"` : '') +
    ' fill="none"/>';
}

function bLeaf(x, y, size, spin, color, opacity = 1.0) {
  return `<path d="M0 ${bNum(-size)}Q${bNum(size * 0.52)} 0 0 ${bNum(size)}` +
    `Q${bNum(-size * 0.52)} 0 0 ${bNum(-size)}Z" fill="${color}"` +
    (opacity !== 1 ? ` opacity="${bNum(opacity)}"` : '') +
    ` transform="translate(${bNum(x)} ${bNum(y)}) rotate(${bNum(spin)})"/>`;
}

function bArtParts(svgText) {
  const match = B_ROOT.exec(svgText || '');
  if (!match) throw new Error('art must be a full <svg> document');
  const inner = (svgText || '').slice(match[0].length);
  const close = inner.lastIndexOf('</svg>');
  if (close === -1) throw new Error('art SVG is not closed');
  const found = B_VIEWBOX.exec(match[1]);
  let box = [0.0, 0.0, 512.0, 512.0];
  if (found) {
    const parts = found[1].replace(/,/g, ' ').split(/\s+/).filter((p) => p !== '');
    if (parts.length === 4) box = parts.map(Number);
  }
  return [inner.slice(0, close), box];
}

/** The ids of a markup blob, longest first, so no id is a prefix of a later one. */
function idsLongestFirst(markup, pattern) {
  const seen = new Set();
  pattern.lastIndex = 0;
  let m;
  while ((m = pattern.exec(markup)) !== null) seen.add(m[1]);
  return Array.from(seen).sort((a, b) => b.length - a.length);
}

function splitAll(text, needle, replacement) {
  return text.split(needle).join(replacement);
}

function bNamespace(markup, prefix) {
  for (const name of idsLongestFirst(markup, B_ID)) {
    markup = splitAll(markup, `id="${name}"`, `id="${prefix}${name}"`);
    markup = splitAll(markup, `url(#${name})`, `url(#${prefix}${name})`);
    markup = splitAll(markup, `href="#${name}"`, `href="#${prefix}${name}"`);
  }
  return markup;
}

function bEmbed(svgText, prefix, cx, cy, diameter) {
  let [inner, box] = bArtParts(svgText);
  const [bx, by, bw, bh] = box;
  inner = bNamespace(inner, prefix);
  const scale = diameter / Math.max(bw, bh);
  const x = cx - diameter / 2.0;
  const y = cy - diameter / 2.0;
  return `<g transform="translate(${bNum(x)} ${bNum(y)}) scale(${bNum(scale)})` +
    ` translate(${bNum(-bx)} ${bNum(-by)})">${inner}</g>`;
}

function specimen(artSvg, prefix, cx, cy, diameter, tint, captioned) {
  const r = diameter / 2.0;
  const out = [`<g><circle cx="${bNum(cx)}" cy="${bNum(cy + r * 0.045)}" r="${bNum(r)}" fill="${B_RULE}" opacity=".16"/>`];
  if (artSvg) {
    out.push(`<circle cx="${bNum(cx)}" cy="${bNum(cy)}" r="${bNum(r * 1.045)}" fill="${EDGE}"/>`);
    out.push(bEmbed(artSvg, prefix, cx, cy, diameter));
  } else {
    out.push(`<circle cx="${bNum(cx)}" cy="${bNum(cy)}" r="${bNum(r)}" fill="${EDGE}"` +
      ` stroke="${HAIR}" stroke-width="1.2" stroke-dasharray="4 4"/>`);
    out.push(bLeaf(cx, cy, r * 0.42, 24, HAIR, 0.7));
    out.push(bText(cx, cy + r * 0.72, 'NO PLATE', bFit('NO PLATE', r * 0.26, diameter * 0.8),
      B_MUTED, 'middle', SANS, 1.4));
  }
  out.push(`<circle cx="${bNum(cx)}" cy="${bNum(cy)}" r="${bNum(r * 1.045)}" fill="none"` +
    ` stroke="${tint}" stroke-width="1.6" opacity=".55"/>`);
  if (captioned) {
    out.push(`<circle cx="${bNum(cx)}" cy="${bNum(cy)}" r="${bNum(r * 1.13)}" fill="none"` +
      ` stroke="${HAIR}" stroke-width=".9" opacity=".85"/>`);
  }
  out.push('</g>');
  return out.join('');
}

function plate(w, h, tint, ornaments) {
  const out = [`<rect width="${bNum(w)}" height="${bNum(h)}" fill="${STOCK}"/>`,
    `<rect x="3" y="3" width="${bNum(w - 6)}" height="${bNum(h - 6)}" fill="none"` +
    ` stroke="${B_RULE}" stroke-width="1.6" opacity=".85"/>`,
    `<rect x="8" y="8" width="${bNum(w - 16)}" height="${bNum(h - 16)}" fill="none"` +
    ` stroke="${HAIR}" stroke-width=".9"/>`,
    `<rect x="3" y="3" width="${bNum(w - 6)}" height="7" fill="${tint}" opacity=".55"/>`];
  if (ornaments) {
    for (const [x, y, spin] of [[16, 16, 135], [w - 16, 16, -135], [16, h - 16, 45], [w - 16, h - 16, -45]]) {
      out.push(bLeaf(x, y, 7.5, spin, B_RULE, 0.5));
    }
  }
  return out.join('');
}

function eyebrow(participant) {
  const maker = pyStrip(orEmpty(participant.manufacturer));
  const mold = pyStrip(orEmpty(participant.mold));
  const line = [maker, mold].filter((p) => p).join(` ${MIDDOT} `) || 'UNRECORDED MOLD';
  return bEsc(line.toUpperCase());
}

function strip(x, y, w, participant, tint, captions, figure = 25.0) {
  const out = [bRule(x, y, x + w, y, B_RULE, 1.1, 0.7)];
  const cell = w / 4.0;
  const values = participant.flightValues || {};
  for (let i = 0; i < B_FLIGHT_KEYS.length; i++) {
    const [key, caption] = B_FLIGHT_KEYS[i];
    const cx = x + cell * (i + 0.5);
    if (i) out.push(bRule(x + cell * i, y + 3, x + cell * i, y + figure * 1.05, HAIR, 0.8));
    const body = bFlight(values[key]);
    out.push(bText(cx, y + figure * 0.92, body, figure, INK, 'middle', SERIF));
    if (captions) {
      out.push(bText(cx, y + figure * 1.52, caption, Math.min(9.5, cell * 0.19), B_MUTED,
        'middle', SANS, 1.5));
    }
  }
  const close = y + figure * (captions ? 2.02 : 1.18);
  out.push(bRule(x, close, x + w, close, tint, 1.4, 0.55));
  return out.join('');
}

function nameplate(x, y, w, participant, tint, details, size = 30.0, noteSize = 12.0) {
  const name = bEsc(pyStrip(pyText(participant.name || 'Untitled')) || 'Untitled');
  const brow = eyebrow(participant);
  const out = [bText(x, y, brow, Math.min(10.5, bFit(brow, 10.5, w, 0.62)), B_MUTED, 'start', SANS, 1.8),
    bText(x, y + size * 0.92, name, bFit(name, size, w, 0.56), INK, 'start', SERIF, 0.2)];
  if (details) {
    const note = pyStrip(orEmpty(participant.note));
    if (note) {
      out.push(bText(x, y + size * 1.42, bEsc(note), noteSize, B_MUTED, 'start', SERIF, 0, 400, 'italic'));
    }
    out.push(bRule(x, y + size * 1.72, x + w * 0.34, y + size * 1.72, tint, 1.6, 0.7));
  }
  return out.join('');
}

function bScoreMap(card) {
  const scores = card.scores;
  const out = {};
  const ids = (card.participants || []).map((p) => (p.presentationId === undefined ? '' : p.presentationId));
  if (isPlainObject(scores)) {
    for (const [key, value] of Object.entries(scores)) {
      if (ids.includes(key)) out[key] = bFlight(value);
      else if (/^[0-9]+$/.test(key) && Number(key) < ids.length) out[ids[Number(key)]] = bFlight(value);
    }
  } else if (Array.isArray(scores)) {
    scores.slice(0, ids.length).forEach((value, index) => { out[ids[index]] = bFlight(value); });
  }
  return out;
}

function bWinner(card) {
  for (const key of ['manualWinner', 'winner', 'highlight']) {
    const value = card[key];
    if (typeof value === 'string' && value) return value;
    if (typeof value === 'number' && Number.isInteger(value)) {
      const ids = (card.participants || []).map((p) => (p.presentationId === undefined ? '' : p.presentationId));
      if (value >= 0 && value < ids.length) return ids[value];
    }
  }
  return '';
}

function seal(cx, cy, r, value, tint, captioned, inside = false) {
  const out = [`<circle cx="${bNum(cx)}" cy="${bNum(cy + r * 0.07)}" r="${bNum(r)}" fill="${B_RULE}" opacity=".18"/>`,
    `<circle cx="${bNum(cx)}" cy="${bNum(cy)}" r="${bNum(r)}" fill="${STOCK}" stroke="${tint}"` +
    ` stroke-width="2"/>`,
    `<circle cx="${bNum(cx)}" cy="${bNum(cy)}" r="${bNum(r * 0.82)}" fill="none" stroke="${HAIR}"` +
    ` stroke-width=".9"/>`];
  const body = value ? value : EN_DASH;
  if (inside) {
    out.push(bText(cx, cy - r * 0.28, 'SCORE', Math.min(8.0, r * 0.30), B_MUTED, 'middle', SANS, 1.2));
    out.push(bText(cx, cy + r * 0.52, body, bFit(body, r * 1.0, r * 1.4, 0.62), INK, 'middle', SERIF));
  } else {
    out.push(bText(cx, cy + r * 0.30, body, bFit(body, r * 1.05, r * 1.5, 0.62), INK, 'middle', SERIF));
    out.push(bText(cx, cy + r * 1.46, 'SCORE', captioned ? Math.min(9.0, r * 0.34) : Math.min(8.0, r * 0.30),
      B_MUTED, 'middle', SANS, captioned ? 1.8 : 1.4));
  }
  return out.join('');
}

function edition(x, y, kind, layout, anchor = 'start') {
  const body = bEsc(`PLATE ${MIDDOT} ${kind} ${MIDDOT} ${layout}`.toUpperCase());
  return bText(x - (anchor === 'end' ? 1.6 : 0.0), y, body, 8.0, B_MUTED, anchor, SANS, 1.6,
    400, '', 0.85);
}

function bFrame(w, h, width, label, body) {
  const height = Math.max(1, pyRoundInt(width * h / w));
  return '<?xml version="1.0" encoding="UTF-8"?>\n' +
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}"` +
    ` viewBox="0 0 ${bNum(w)} ${bNum(h)}" role="img" aria-label="${bEsc(label)}">` +
    `${body}<title>${bEsc(label)}</title></svg>\n`;
}

function isPlainObject(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function bParticipants(card, count) {
  const values = (card.participants || []).filter((p) => isPlainObject(p));
  while (values.length < count) values.push({ presentationId: `missing${values.length}`, name: 'Unplated' });
  return values.slice(0, count);
}

/** A single-disc plate. layout: 'standard' (landscape) or 'gallery' (portrait). */
export function renderSingle(card, art, width) {
  if (!isPlainObject(card)) throw new Error('card object required');
  art = isPlainObject(art) ? art : {};
  width = Math.trunc(width);
  if (width < 80) throw new Error('width must be at least 80');
  let layout = card.layout === undefined ? 'standard' : card.layout;
  layout = (layout === 'standard' || layout === 'gallery') ? layout : 'standard';
  const details = card.details === undefined ? true : Boolean(card.details);
  const person = bParticipants(card, 1)[0];
  const pid = pyText(person.presentationId === undefined ? 'p0' : person.presentationId);
  const tint = inkOf(person);
  const plateArt = art[pid];
  const name = pyText(person.name || 'Untitled');

  let w, h, body;
  if (layout === 'gallery') {
    w = 340.0;
    const stripY = details ? 404.0 : 382.0;
    h = stripY + (details ? 26.0 * 2.02 + 26.0 : 26.0 * 1.18 + 26.0);
    body = [plate(w, h, tint, details),
      specimen(plateArt, 'a-', w / 2.0, 174.0, 238.0, tint, details),
      bRule(34, 310, w - 34, 310, HAIR, 1.0),
      nameplate(34, 340, w - 68, person, tint, details, 32.0, 12.5),
      strip(34, stripY, w - 68, person, tint, details, 26.0),
      edition(w / 2.0, h - 13, 'single', layout, 'middle')];
  } else {
    w = 424.0;
    const stripY = details ? 112.0 : 96.0;
    h = stripY + (details ? 25.0 * 2.02 + 24.0 : 25.0 * 1.18 + 24.0);
    const disc = details ? 134.0 : 118.0;
    body = [plate(w, h, tint, details),
      specimen(plateArt, 'a-', 22.0 + disc / 2.0, h / 2.0 + 1.0, disc, tint, details),
      nameplate(disc + 46.0, 46.0, w - disc - 74.0, person, tint, details, 30.0, 12.0),
      strip(disc + 46.0, stripY, w - disc - 74.0, person, tint, details, 25.0),
      edition(w - 20, h - 11, 'single', layout, 'end')];
  }
  return bFrame(w, h, width, `${name} ${EM_DASH} botanical single plate (${layout})`, body.join(''));
}

/** The botanical battle plate. Kept so this module still matches its own receipts. */
export function renderBotanicalBattle(card, art, width) {
  if (!isPlainObject(card)) throw new Error('card object required');
  art = isPlainObject(art) ? art : {};
  width = Math.trunc(width);
  if (width < 80) throw new Error('width must be at least 80');
  let layout = card.layout === undefined ? 'standard' : card.layout;
  layout = (layout === 'standard' || layout === 'stacked') ? layout : 'standard';
  const details = card.details === undefined ? true : Boolean(card.details);
  const people = bParticipants(card, 2);
  const scores = bScoreMap(card);
  const champion = bWinner(card);
  const tints = people.map((p) => inkOf(p));
  const names = people.map((p) => pyText(p.name || 'Untitled'));

  let w, h, body;
  if (layout === 'stacked') {
    w = 470.0;
    const rowH = details ? 168.0 : 138.0;
    h = 74.0 + rowH * 2.0;
    body = [plate(w, h, tints[0], details),
      bText(w / 2.0, 32.0, 'MATCH PLATE', 10.5, B_MUTED, 'middle', SANS, 3.4)];
    people.forEach((person, index) => {
      const pid = pyText(person.presentationId === undefined ? `p${index}` : person.presentationId);
      const top = 44.0 + index * rowH;
      const disc = Math.min(rowH - 28.0, 118.0);
      const won = Boolean(champion) && pid === champion;
      const left = 40.0 + Math.min(rowH - 28.0, 118.0);
      if (won) {
        body.push(`<rect x="14" y="${bNum(top - 4)}" width="${bNum(w - 28)}"` +
          ` height="${bNum(rowH - 6)}" fill="${tints[index]}" opacity=".07"/>`);
        body.push(bRule(14, top - 4, 14, top + rowH - 10, tints[index], 3.0, 0.85));
        body.push(bLeaf(left - 16.0, top + 22.5, 6.5, 135, tints[index], 0.95));
      }
      body.push(specimen(art[pid], `${'ab'[index]}-`, 30.0 + disc / 2.0,
        top + rowH / 2.0 - 6.0, disc, tints[index], details));
      body.push(nameplate(left, top + 26.0, w - disc - 156.0, person, tints[index], details, 25.0, 11.0));
      body.push(strip(left, top + (details ? 78.0 : 62.0), w - disc - 156.0, person,
        tints[index], details, 21.0));
      body.push(seal(w - 58.0, top + rowH / 2.0 - 8.0, 32.0, scores[pid] === undefined ? '' : scores[pid],
        tints[index], details));
      if (index === 0) body.push(bRule(24, 44.0 + rowH - 6.0, w - 24, 44.0 + rowH - 6.0, HAIR, 1.0));
    });
    body.push(edition(w / 2.0, h - 13, 'battle', layout, 'middle'));
  } else {
    w = 636.0;
    const disc = details ? 130.0 : 116.0;
    const stripY = details ? 38.0 + disc + 34.0 : 38.0 + disc + 22.0;
    h = stripY + (details ? 24.0 * 2.02 + 30.0 : 24.0 * 1.18 + 28.0);
    const gap = 40.0;
    const half = (w - 32.0 - gap) / 2.0;
    body = [plate(w, h, tints[0], details)];
    const centre = w / 2.0;
    people.forEach((person, index) => {
      const pid = pyText(person.presentationId === undefined ? `p${index}` : person.presentationId);
      const x0 = 16.0 + index * (half + gap);
      const won = Boolean(champion) && pid === champion;
      if (won) {
        body.push(`<rect x="${bNum(x0 - 3)}" y="24" width="${bNum(half + 6)}"` +
          ` height="${bNum(h - 52)}" fill="${tints[index]}" opacity=".07"/>`);
        body.push(bRule(x0 - 3, 24, x0 + half + 3, 24, tints[index], 2.6, 0.9));
      }
      const dx = x0 + disc / 2.0 + 4.0;
      const dy = 38.0 + disc / 2.0;
      body.push(specimen(art[pid], `${'ab'[index]}-`, dx, dy, disc, tints[index], details));
      const left = x0 + disc + 26.0;
      const wide = half - disc - 30.0;
      if (won) body.push(bLeaf(left - 16.0, 58.5, 6.5, 135, tints[index], 0.95));
      body.push(nameplate(left, 62.0, wide, person, tints[index], details, 27.0, 11.5));
      body.push(strip(x0 + 6.0, stripY, half - 12.0, person, tints[index], details, 24.0));
      body.push(seal(dx + disc * 0.38, dy + disc * 0.36, 23.0, scores[pid] === undefined ? '' : scores[pid],
        tints[index], details, true));
    });
    const mid = 38.0 + disc / 2.0;
    body.push(bRule(centre, 30, centre, h - 30, HAIR, 1.0));
    body.push(`<circle cx="${bNum(centre)}" cy="${bNum(mid)}" r="23" fill="${STOCK}"/>`);
    body.push(bLeaf(centre, mid - 27, 7.0, 180, B_RULE, 0.55));
    body.push(bLeaf(centre, mid + 27, 7.0, 0, B_RULE, 0.55));
    body.push(bText(centre, mid + 6.0, 'vs', 21.0, B_RULE, 'middle', SERIF, 0, 400, 'italic'));
    body.push(edition(w - 20, h - 11, 'battle', layout, 'end'));
  }
  return bFrame(w, h, width, `${names[0]} vs ${names[1]} ${EM_DASH} botanical match plate (${layout})`,
    body.join(''));
}

// ================================================================= studio signal
//
// _card_signal.py, verbatim in behaviour. render_battle is the promoted half.

const WHITE = '#ffffff';
const NEAR_BLACK = '#111318';
const BED = '#0a0e13';
const PANEL = '#151d27';
const S_RULE = '#2d3c4d';
const TEXT = '#f4f7fa';
const S_MUTED = '#93a5b8';
const FALLBACK_ACCENT = '#b9d789';

const S_HEX = /^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;
const S_FLIGHTS = [['flight1', 'SPEED'], ['flight2', 'GLIDE'], ['flight3', 'TURN'], ['flight4', 'FADE']];

const S_ROOT = /\s*(?:<\?xml[^>]*\?>\s*)?<svg\b([^>]*)>/;
const S_VIEWBOX = /viewBox="([^"]*)"/;
const S_TITLE = /<title>[\s\S]*?<\/title>/g;
const S_ID = /\bid="([^"]+)"/g;

function sChannels(value) {
  let v = value.replace(/^#+/, '');
  if (v.length === 3) v = v.split('').map((c) => c + c).join('');
  return [parseInt(v.slice(0, 2), 16), parseInt(v.slice(2, 4), 16), parseInt(v.slice(4, 6), 16)];
}

function sHex(r, g, b) {
  const clamp = (x) => Math.max(0, Math.min(255, pyRoundInt(x)));
  return '#' + hex2(clamp(r)) + hex2(clamp(g)) + hex2(clamp(b));
}

function sMix(a, b, t) {
  const [ar, ag, ab] = sChannels(a);
  const [br, bg, bb] = sChannels(b);
  return sHex(ar + (br - ar) * t, ag + (bg - ag) * t, ab + (bb - ab) * t);
}

function luminance(value) {
  const [r, g, b] = sChannels(value);
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0;
}

function contrastInk(value, pivot = 0.62) {
  return luminance(value) > pivot ? NEAR_BLACK : WHITE;
}

/** "{:.2f}" with trailing zeros and the point stripped; only "" folds to "0". */
function sF(value) {
  const text = rstrip(rstrip(fmt2(Number(value)), '0'), '.');
  return text || '0';
}

function sEsc(value) {
  return esc(value === null || value === undefined ? '' : pyText(value));
}

function sAccent(participant) {
  const value = participant.color;
  if (typeof value === 'string' && S_HEX.test(pyStrip(value))) return pyStrip(value).toLowerCase();
  return FALLBACK_ACCENT;
}

function sFit(text, maxW, size, ratio = 0.60, floor = 6.0) {
  const n = text.length;
  if (n <= 0) return size;
  return pyRound(Math.max(floor, Math.min(size, maxW / (n * ratio))), 1);
}

function sNumber(value) {
  if (typeof value === 'boolean' || value === null || value === undefined || value === '') return EN_DASH;
  if (typeof value === 'number') {
    if (Number.isInteger(value)) return String(value);
    return rstrip(rstrip(fmt(value, 1), '0'), '.');
  }
  return sEsc(value).slice(0, 4);
}

function sEyebrow(participant) {
  let parts = ['manufacturer', 'mold', 'variant'].map((key) => pyStrip(orEmpty(participant[key])));
  parts = parts.filter((p) => p);
  if (parts.length === 0) {
    const physical = pyStrip(orEmpty(participant.physicalDiscId));
    parts = physical ? [physical] : ['UNCATALOGUED'];
  }
  return parts.join(` ${MIDDOT} `).toUpperCase();
}

function sArtSvg(artText, prefix, x, y, size) {
  const source = artText || '';
  const match = S_ROOT.exec(source);
  if (!match) return '';
  const viewbox = S_VIEWBOX.exec(match[1]);
  let numbers = viewbox
    ? pyStrip(viewbox[1]).split(/[\s,]+/).filter((v) => v).map(Number)
    : [];
  if (numbers.length !== 4 || numbers[2] <= 0 || numbers[3] <= 0) numbers = [0.0, 0.0, 512.0, 512.0];
  const [minX, minY, boxW, boxH] = numbers;
  let inner = source.slice(match.index + match[0].length, source.lastIndexOf('</svg>'));
  inner = inner.replace(S_TITLE, '');
  for (const ident of idsLongestFirst(inner, S_ID)) {
    inner = splitAll(inner, `id="${ident}"`, `id="${prefix}${ident}"`);
    inner = splitAll(inner, `url(#${ident})`, `url(#${prefix}${ident})`);
    inner = splitAll(inner, `href="#${ident}"`, `href="#${prefix}${ident}"`);
  }
  const scale = size / Math.max(boxW, boxH);
  const tx = x + (size - boxW * scale) / 2.0 - minX * scale;
  const ty = y + (size - boxH * scale) / 2.0 - minY * scale;
  return `<g transform="translate(${sF(tx)} ${sF(ty)}) scale(${sF(pyRound(scale, 6))})">${pyStrip(inner)}</g>`;
}

function sArtOrStub(art, participant, prefix, x, y, size, accent) {
  const key = pyText(participant.presentationId === undefined ? '' : participant.presentationId);
  const text = (art || {})[key];
  if (text) return sArtSvg(text, prefix, x, y, size);
  const raw = pyStrip(pyText(participant.name === undefined ? '' : participant.name) || '?').slice(0, 1).toUpperCase();
  const initial = sEsc(raw || '?');
  return `<g><circle cx="${sF(x + size / 2)}" cy="${sF(y + size / 2)}" r="${sF(size / 2 - 2)}" fill="${PANEL}" stroke="${accent}" stroke-width="${sF(Math.max(1.5, size * 0.03))}"/>` +
    `<text x="${sF(x + size / 2)}" y="${sF(y + size / 2 + size * 0.17)}" text-anchor="middle" font-family="sans-serif" ` +
    `font-size="${sF(size * 0.46)}" font-weight="700" fill="${accent}">${initial}</text></g>`;
}

function sCaps(x, y, text, size, fill = S_MUTED, anchor = 'start', spacing = 1.4, weight = 600) {
  return `<text x="${sF(x)}" y="${sF(y)}" text-anchor="${anchor}" font-family="sans-serif" font-size="${sF(size)}" ` +
    `font-weight="${weight}" letter-spacing="${sF(spacing)}" fill="${fill}">${sEsc(text)}</text>`;
}

function sHeavy(x, y, text, size, fill = TEXT, anchor = 'start') {
  return `<text x="${sF(x)}" y="${sF(y)}" text-anchor="${anchor}" font-family="sans-serif" font-size="${sF(size)}" ` +
    `font-weight="800" fill="${fill}">${sEsc(text)}</text>`;
}

function sChevrons(x, y, height, accent, count = 3, pitch = 9.0, weight = 4.0, flip = false) {
  const out = [];
  for (let i = 0; i < count; i++) {
    const cx = x + i * pitch;
    const nose = height * 0.5;
    const x0 = flip ? cx + nose : cx;
    const x1 = flip ? cx : cx + nose;
    out.push(`<path d="M${sF(x0)} ${sF(y - height / 2)} L${sF(x1)} ${sF(y)} L${sF(x0)} ${sF(y + height / 2)}" fill="none" stroke="${accent}" ` +
      `stroke-width="${sF(weight)}" opacity="${fmt2(0.35 + 0.32 * i)}"/>`);
  }
  return out.join('');
}

function sFlightCells(x, y, width, height, participant, accent, gap = 4.0, anchorLabels = true) {
  const values = participant.flightValues || {};
  const cell = (width - gap * 3) / 4.0;
  const numSize = Math.min(height * 0.52, cell * 0.62);
  const labSize = Math.max(6.0, Math.min(height * 0.2, cell * 0.235));
  const out = ['<g>'];
  for (let i = 0; i < S_FLIGHTS.length; i++) {
    const [key, label] = S_FLIGHTS[i];
    const cx = x + i * (cell + gap);
    out.push(`<rect x="${sF(cx)}" y="${sF(y)}" width="${sF(cell)}" height="${sF(height)}" rx="3" fill="${PANEL}" ` +
      `stroke="${S_RULE}" stroke-width="1"/>`);
    out.push(`<rect x="${sF(cx)}" y="${sF(y)}" width="${sF(cell)}" height="${sF(Math.max(2.0, height * 0.055))}" fill="${accent}" opacity=".85"/>`);
    out.push(sHeavy(cx + cell / 2, y + height * 0.66, sNumber(values[key]), numSize, TEXT, 'middle'));
    if (anchorLabels) {
      out.push(sCaps(cx + cell / 2, y + height * 0.92, label, labSize, S_MUTED, 'middle',
        Math.max(0.4, labSize * 0.09)));
    }
  }
  out.push('</g>');
  return out.join('');
}

function sDocument(width, designW, designH, aria, body) {
  const pxW = Math.max(1, pyRoundInt(width));
  const pxH = Math.max(1, pyRoundInt(pxW * designH / designW));
  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<svg xmlns="http://www.w3.org/2000/svg" width="${pxW}" height="${pxH}" viewBox="0 0 ${sF(designW)} ${sF(designH)}" ` +
    `role="img" aria-label="${sEsc(aria)}">`,
    body,
    `<title>${sEsc(aria)}</title>`,
    '</svg>',
  ].join('\n') + '\n';
}

function sBed(designW, designH, accent, second = null) {
  const out = [`<rect x="0" y="0" width="${sF(designW)}" height="${sF(designH)}" rx="10" fill="${BED}"/>`,
    `<rect x="0.75" y="0.75" width="${sF(designW - 1.5)}" height="${sF(designH - 1.5)}" rx="9.5" fill="none" stroke="${S_RULE}" ` +
    `stroke-width="1.5"/>`];
  if (second === null || second === undefined) {
    out.push(`<rect x="0" y="0" width="${sF(designW)}" height="5" fill="${accent}"/>`);
  } else {
    out.push(`<rect x="0" y="0" width="${sF(designW / 2)}" height="5" fill="${accent}"/>`);
    out.push(`<rect x="${sF(designW / 2)}" y="0" width="${sF(designW / 2)}" height="5" fill="${second}"/>`);
  }
  return out.join('');
}

function sScores(card, participants) {
  const raw = card.scores;
  const out = [];
  participants.forEach((participant, index) => {
    const key = pyText(participant.presentationId === undefined ? '' : participant.presentationId);
    let value = null;
    if (isPlainObject(raw)) {
      if (Object.prototype.hasOwnProperty.call(raw, key)) value = raw[key];
      else if (Object.prototype.hasOwnProperty.call(raw, String(index))) value = raw[String(index)];
    } else if (Array.isArray(raw) && index < raw.length) {
      value = raw[index];
    }
    if (value === null || value === undefined) {
      value = participant.score === undefined ? null : participant.score;
    }
    out.push(value);
  });
  return out;
}

function sLeader(scores) {
  const numeric = scores.map((v) => (typeof v === 'number' && !Number.isNaN(v) ? v : null));
  if (numeric.length !== 2 || numeric[0] === null || numeric[1] === null || numeric[0] === numeric[1]) return null;
  return numeric[0] > numeric[1] ? 0 : 1;
}

function sFlagged(card, participants, field) {
  const value = card[field];
  if (typeof value === 'boolean' || value === null || value === undefined) return null;
  if (typeof value === 'number' && Number.isInteger(value)) {
    return (value >= 0 && value < participants.length) ? value : null;
  }
  if (typeof value === 'string') {
    for (let index = 0; index < participants.length; index++) {
      const pid = pyText(participants[index].presentationId === undefined ? '' : participants[index].presentationId);
      if (pid === value) return index;
    }
    return null;
  }
  if (isPlainObject(value)) {
    for (let index = 0; index < participants.length; index++) {
      const pid = pyText(participants[index].presentationId === undefined ? '' : participants[index].presentationId);
      if (value[pid]) return index;
    }
  }
  return null;
}

function sName(participant) {
  return pyStrip(orEmpty(participant.name)) || pyStrip(orEmpty(participant.mold)) || 'UNNAMED DISC';
}

function sNote(participant) {
  return pyStrip(orEmpty(participant.note));
}

// ------------------------------------------------------------ signal single ---

function sSingleStandard(card, art, participant, details) {
  const W = 400.0, H = 174.0;
  const accent = sAccent(participant);
  const name = sName(participant);
  const body = [sBed(W, H, accent)];
  body.push(`<rect x="0" y="${sF(H - 3)}" width="${sF(W)}" height="3" fill="${accent}" opacity=".45"/>`);
  if (details) {
    body.push(sArtOrStub(art, participant, 'a0-', 14, 30, 112, accent));
    body.push(sCaps(140, 26, sEyebrow(participant), 10.5, S_MUTED, 'start', 1.8));
    body.push(sHeavy(140, 60, name, sFit(name, 178, 27), TEXT));
    const note = sNote(participant);
    if (note) body.push(sCaps(140, 78, note.toUpperCase(), 9.5, sMix(S_MUTED, BED, 0.1), 'start', 1.2, 500));
    body.push(sFlightCells(140, 96, 190, 62, participant, accent));
    body.push(sChevrons(348, 127, 42, accent, 3, 13, 5));
    body.push(sCaps(W - 14, 26, 'SINGLE', 10, sMix(S_MUTED, BED, 0.15), 'end', 2.2));
  } else {
    body.push(sArtOrStub(art, participant, 'a0-', 18, 24, 126, accent));
    body.push(sHeavy(158, 92, name, sFit(name, 214, 34), TEXT));
    body.push(sChevrons(158, 116, 26, accent, 4, 11, 4.5));
  }
  return [W, H, body.join('')];
}

function sSingleGallery(card, art, participant, details) {
  const W = 320.0, H = 402.0;
  const accent = sAccent(participant);
  const name = sName(participant);
  const body = [sBed(W, H, accent)];
  if (details) {
    body.push(`<rect x="20" y="20" width="280" height="212" rx="8" fill="${PANEL}"/>`);
    body.push(sArtOrStub(art, participant, 'a0-', 54, 20, 212, accent));
    body.push(sChevrons(26, 126, 30, accent, 2, 11, 4.5));
    body.push(sChevrons(268, 126, 30, accent, 2, 11, 4.5, true));
    body.push(`<rect x="20" y="236" width="280" height="3" fill="${accent}"/>`);
    body.push(sCaps(24, 260, sEyebrow(participant), 11, S_MUTED, 'start', 2.0));
    body.push(sHeavy(24, 298, name, sFit(name, 272, 36), TEXT));
    const note = sNote(participant);
    if (note) body.push(sCaps(24, 320, note.toUpperCase(), 10.5, sMix(S_MUTED, BED, 0.1), 'start', 1.2, 500));
    body.push(sFlightCells(20, 332, 280, 62, participant, accent));
  } else {
    body.push(sArtOrStub(art, participant, 'a0-', 40, 44, 240, accent));
    body.push(`<rect x="40" y="300" width="240" height="4" fill="${accent}"/>`);
    body.push(sHeavy(160, 348, name, sFit(name, 268, 40), TEXT, 'middle'));
    body.push(sChevrons(134, 374, 22, accent, 4, 13, 5));
  }
  return [W, H, body.join('')];
}

/** The signal single plate. Kept so this module still matches its own receipts. */
export function renderSignalSingle(card, art, width) {
  if (!isPlainObject(card)) throw new Error('card object required');
  const participants = Array.from(card.participants || []);
  if (participants.length === 0) throw new Error('single card needs one participant');
  const participant = participants[0];
  const details = card.details === undefined ? true : Boolean(card.details);
  const layout = card.layout === undefined ? 'standard' : card.layout;
  const build = layout === 'gallery' ? sSingleGallery : sSingleStandard;
  const [designW, designH, body] = build(card, art || {}, participant, details);
  const aria = `${sName(participant)} ${EM_DASH} disc card`;
  return sDocument(width, designW, designH, aria, body);
}

// ------------------------------------------------------------ signal battle ---

function sScoreBlock(x, y, w, h, scores, accents, leader, vertical) {
  const out = [`<rect x="${sF(x)}" y="${sF(y)}" width="${sF(w)}" height="${sF(h)}" rx="8" fill="${PANEL}"/>`];
  const halfW = vertical ? w : w / 2.0;
  const halfH = vertical ? h / 2.0 : h;
  for (const index of [0, 1]) {
    const cx = x + (vertical ? 0 : index * halfW);
    const cy = y + (vertical ? index * halfH : 0);
    const won = leader === index;
    if (won) {
      out.push(`<rect x="${sF(cx)}" y="${sF(cy)}" width="${sF(halfW)}" height="${sF(halfH)}" fill="${accents[index]}"/>`);
    }
    const ink = won ? contrastInk(accents[index], 0.5)
      : (leader !== null ? sMix(TEXT, PANEL, 0.45) : TEXT);
    const size = Math.min(halfH * 0.62, halfW * 0.66);
    const text = sNumber(scores[index]);
    out.push(sHeavy(cx + halfW / 2, cy + halfH * 0.5 + size * 0.36, text,
      sFit(text, halfW * 0.82, size, 0.62), ink, 'middle'));
  }
  if (vertical) {
    out.push(`<rect x="${sF(x)}" y="${sF(y + h / 2 - 1)}" width="${sF(w)}" height="2" fill="${BED}"/>`);
  } else {
    out.push(`<rect x="${sF(x + w / 2 - 1)}" y="${sF(y)}" width="2" height="${sF(h)}" fill="${BED}"/>`);
  }
  out.push(`<rect x="${sF(x)}" y="${sF(y)}" width="${sF(w)}" height="${sF(h)}" rx="8" fill="none" stroke="${S_RULE}" ` +
    `stroke-width="1.5"/>`);
  return out.join('');
}

function sVsBadge(cx, cy, size) {
  return `<g><rect x="${sF(cx - size / 2)}" y="${sF(cy - size / 2)}" width="${sF(size)}" height="${sF(size)}" rx="3" fill="${BED}" stroke="${S_RULE}" ` +
    `stroke-width="1.5" transform="rotate(45 ${sF(cx)} ${sF(cy)})"/>` +
    `<text x="${sF(cx)}" y="${sF(cy + size * 0.2)}" text-anchor="middle" font-family="sans-serif" ` +
    `font-size="${sF(size * 0.46)}" font-weight="800" letter-spacing="0.6" fill="${TEXT}">VS</text></g>`;
}

function sBattleHeader(designW, accents, participants, winner, leader) {
  const out = [sChevrons(14, 21, 20, accents[0], 3, 8, 3.5)];
  out.push(sCaps(52, 26, 'DISC BATTLE', 12, TEXT, 'start', 3.2, 700));
  const tagIndex = winner !== null ? winner : leader;
  if (tagIndex !== null) {
    let who = sName(participants[tagIndex]).toUpperCase();
    if (who.length > 14) who = rstripWs(who.slice(0, 13)) + ELLIPSIS;
    const label = (winner !== null ? 'WINNER ' + MIDDOT + ' ' : 'LEADING ' + MIDDOT + ' ') + who;
    const spacing = 1.2;
    const size = sFit(label, designW * 0.40, 10.5, 0.70, 6.5);
    const plateW = label.length * (size * 0.60 + spacing) + 20;
    out.push(`<rect x="${sF(designW - 14 - plateW)}" y="9" width="${sF(plateW)}" height="23" rx="4" fill="${accents[tagIndex]}"/>`);
    out.push(sCaps(designW - 14 - plateW / 2 + spacing / 2, 25, label, size,
      contrastInk(accents[tagIndex], 0.5), 'middle', spacing, 700));
  } else {
    out.push(`<circle cx="${sF(designW - 62)}" cy="20.5" r="4.5" fill="${accents[0]}"/>`);
    out.push(sCaps(designW - 14, 25, 'LIVE', 11, S_MUTED, 'end', 2.4));
  }
  out.push(`<rect x="0" y="41" width="${sF(designW)}" height="1.5" fill="${S_RULE}"/>`);
  return out.join('');
}

/** Python's str.rstrip() with no argument: trailing whitespace only. */
function rstripWs(text) {
  return String(text).replace(/[\s]+$/g, '');
}

function sBattleStandard(card, art, participants, details, scores, accents, winner, highlight) {
  const W = 660.0, H = 300.0;
  const leader = winner !== null ? winner : sLeader(scores);
  const body = [sBed(W, H, accents[0], accents[1])];
  body.push(sBattleHeader(W, accents, participants, winner, sLeader(scores)));
  const artSize = details ? 104.0 : 128.0;
  const artY = details ? 58.0 : 74.0;
  participants.slice(0, 2).forEach((participant, index) => {
    const accent = accents[index];
    const mirrored = index === 1;
    const artX = !mirrored ? 16.0 : W - 16.0 - artSize;
    body.push(sArtOrStub(art, participant, `a${index}-`, artX, artY, artSize, accent));
    const textX = !mirrored ? (artX + artSize + 16) : (artX - 16);
    const anchor = !mirrored ? 'start' : 'end';
    const name = sName(participant);
    if (details) {
      body.push(sCaps(textX, artY + 22, sEyebrow(participant), 10.5, S_MUTED, anchor, 1.6));
      body.push(sHeavy(textX, artY + 58, name, sFit(name, 104, 26), TEXT, anchor));
      const note = sNote(participant);
      if (note) {
        body.push(sCaps(textX, artY + 78, note.toUpperCase(), 9.5, sMix(S_MUTED, BED, 0.1), anchor, 1.1, 500));
      }
      const cellsX = !mirrored ? 16.0 : W - 16.0 - 244.0;
      body.push(sFlightCells(cellsX, 196, 244, 62, participant, accent));
    } else {
      body.push(sHeavy(textX, artY + 74, name, sFit(name, 104, 30), TEXT, anchor));
      body.push(sCaps(textX, artY + 96, sEyebrow(participant), 10.5, S_MUTED, anchor, 1.6));
    }
    if (highlight === index || winner === index) {
      const pad = 8.0;
      body.push(`<rect x="${sF(artX - pad)}" y="${sF(artY - pad)}" width="${sF(artSize + pad * 2)}" height="${sF(artSize + pad * 2)}" rx="8" fill="none" ` +
        `stroke="${accent}" stroke-width="2" opacity=".9"/>`);
    }
  });
  body.push(sScoreBlock(264, 52, 132, 120, scores, accents, leader, false));
  body.push(sVsBadge(330, 172, 26));
  body.push(sCaps(330, 214, 'SCORE', 9.5, S_MUTED, 'middle', 2.6));
  body.push(`<rect x="16" y="${sF(H - 20)}" width="${sF(W / 2 - 16)}" height="4" fill="${accents[0]}" opacity=".75"/>`);
  body.push(`<rect x="${sF(W / 2)}" y="${sF(H - 20)}" width="${sF(W / 2 - 16)}" height="4" fill="${accents[1]}" opacity=".75"/>`);
  return [W, H, body.join('')];
}

function sBattleStacked(card, art, participants, details, scores, accents, winner, highlight) {
  const W = 440.0, H = 424.0;
  const leader = winner !== null ? winner : sLeader(scores);
  const body = [sBed(W, H, accents[0], accents[1])];
  body.push(sBattleHeader(W, accents, participants, winner, sLeader(scores)));
  const rows = [52.0, 236.0];
  const artSize = details ? 92.0 : 108.0;
  participants.slice(0, 2).forEach((participant, index) => {
    const accent = accents[index];
    const top = rows[index];
    body.push(`<rect x="10" y="${sF(top)}" width="${sF(W - 20)}" height="152" rx="8" fill="${PANEL}" ` +
      `opacity=".55"/>`);
    if (winner === index || highlight === index) {
      body.push(`<rect x="10" y="${sF(top)}" width="${sF(W - 20)}" height="152" rx="8" fill="none" ` +
        `stroke="${accent}" stroke-width="2.5"/>`);
    }
    body.push(`<rect x="10" y="${sF(top)}" width="5" height="152" fill="${accent}"/>`);
    body.push(sArtOrStub(art, participant, `a${index}-`, 24, top + 12, artSize, accent));
    const name = sName(participant);
    const textX = 24 + artSize + 14;
    if (details) {
      body.push(sCaps(textX, top + 30, sEyebrow(participant), 10, S_MUTED, 'start', 1.6));
      body.push(sHeavy(textX, top + 60, name, sFit(name, 158, 25), TEXT));
      body.push(sFlightCells(textX, top + 76, 186, 60, participant, accent));
    } else {
      body.push(sHeavy(textX, top + 74, name, sFit(name, 176, 30), TEXT));
      body.push(sCaps(textX, top + 96, sEyebrow(participant), 10, S_MUTED, 'start', 1.6));
    }
    const won = leader === index;
    const plateX = W - 118.0, plateY = top + 20.0, plateW = 96.0, plateH = 112.0;
    body.push(`<rect x="${sF(plateX)}" y="${sF(plateY)}" width="${sF(plateW)}" height="${sF(plateH)}" rx="8" fill="${won ? accent : PANEL}" stroke="${won ? accent : S_RULE}" ` +
      `stroke-width="1.5"/>`);
    const ink = won ? contrastInk(accent, 0.5) : (leader !== null ? sMix(TEXT, PANEL, 0.45) : TEXT);
    const text = sNumber(scores[index]);
    body.push(sHeavy(plateX + plateW / 2, plateY + plateH * 0.72, text,
      sFit(text, plateW * 0.78, 62, 0.62), ink, 'middle'));
    body.push(sCaps(plateX + plateW / 2, plateY + plateH * 0.9, 'SCORE', 9,
      sMix(ink, won ? accent : PANEL, 0.35), 'middle', 2.2));
  });
  body.push(`<rect x="10" y="${sF(rows[1] - 22)}" width="${sF(W - 20)}" height="1.5" fill="${S_RULE}"/>`);
  body.push(sVsBadge(W / 2, rows[1] - 21, 28));
  body.push(`<rect x="10" y="${sF(H - 16)}" width="${sF(W / 2 - 10)}" height="4" fill="${accents[0]}" opacity=".75"/>`);
  body.push(`<rect x="${sF(W / 2)}" y="${sF(H - 16)}" width="${sF(W / 2 - 10)}" height="4" fill="${accents[1]}" opacity=".75"/>`);
  return [W, H, body.join('')];
}

/** A two-disc scoreboard plate. layout: 'standard' or 'stacked'. */
export function renderBattle(card, art, width) {
  if (!isPlainObject(card)) throw new Error('card object required');
  let participants = Array.from(card.participants || []);
  if (participants.length === 0) throw new Error('battle card needs at least one participant');
  if (participants.length === 1) {
    participants = participants.concat([{
      presentationId: EM_DASH, name: 'AWAITING RIVAL', color: FALLBACK_ACCENT, flightValues: {},
    }]);
  }
  participants = participants.slice(0, 2);
  const details = card.details === undefined ? true : Boolean(card.details);
  const layout = card.layout === undefined ? 'standard' : card.layout;
  const accents = participants.map((p) => sAccent(p));
  if (accents[0] === accents[1]) accents[1] = sMix(accents[1], TEXT, 0.34);
  const scores = sScores(card, participants);
  let winner = sFlagged(card, participants, 'winner');
  if (winner === null) winner = sFlagged(card, participants, 'manualWinner');
  const highlight = sFlagged(card, participants, 'highlight');
  const build = layout === 'stacked' ? sBattleStacked : sBattleStandard;
  const [designW, designH, body] = build(card, art || {}, participants, details, scores, accents,
    winner, highlight);
  const aria = `Disc battle: ${sName(participants[0])} versus ${sName(participants[1])}`;
  return sDocument(width, designW, designH, aria, body);
}

export default { renderSingle, renderBattle };
