// families/signal.mjs -- the signal studio's disc-art families.
//
// Each export has paint_components.render's shape minus the family name:
//     render(seed, base, accent, target, label) -> string, the whole SVG document
// painter.mjs already dispatches every slug below to the function beside it, so
// filling these in is the whole job; do not edit painter.mjs or core.mjs.
//
// Where the reference bytes come from, per art_registry.py:
//   chevron-run       _families_signal.py
//   score-bug         _families_signal.py
//   sweep-clock       _families_signal.py
//
// Dependency-free: this file may import ../core.mjs and nothing else -- no npm,
// no DOM, Node 22 and browsers alike.
//
// Ported verbatim in behaviour from _families_signal.py. The signal studio's own
// number formatter `_f` keeps "-0" (unlike botanical's, which collapses it), and
// its stroke floor is spelled `round(min_output * SIZE / target, 1)` rather than
// `round(min_output / (target / SIZE), 1)`; both spellings are kept as written.

import {
  PyRandom, escape, fmt1, fmt2, pyRound, pyRoundInt, sin, cos, radians,
  SIZE, C, TARGETS,
} from '../core.mjs';

const WHITE = '#ffffff';
const NEAR_BLACK = '#111318';

// ---------------------------------------------------------------- colour ---

/** _channels(value): the three byte channels of a #rgb or #rrggbb string. */
function channels(value) {
  let v = value.replace(/^#+/, '');
  if (v.length === 3) v = v.split('').map((c) => c + c).join('');
  return [parseInt(v.slice(0, 2), 16), parseInt(v.slice(2, 4), 16), parseInt(v.slice(4, 6), 16)];
}

/** _hex(r, g, b): "#{:02x}{:02x}{:02x}" over max(0, min(255, int(round(x)))). */
function toHex(r, g, b) {
  const clamp = (x) => Math.max(0, Math.min(255, pyRoundInt(x)));
  return '#' + [clamp(r), clamp(g), clamp(b)].map((v) => v.toString(16).padStart(2, '0')).join('');
}

/** mix(a, b, t): blend hex `a` toward hex `b`. */
export function mix(a, b, t) {
  const [ar, ag, ab] = channels(a);
  const [br, bg, bb] = channels(b);
  return toHex(ar + (br - ar) * t, ag + (bg - ag) * t, ab + (bb - ab) * t);
}

/** luminance(value): rough relative luminance in [0, 1]. */
export function luminance(value) {
  const [r, g, b] = channels(value);
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0;
}

/** contrast_ink(value, pivot): white over a dark/mid colour, near-black over a pale one. */
export function contrastInk(value, pivot = 0.62) {
  return luminance(value) > pivot ? NEAR_BLACK : WHITE;
}

// --------------------------------------------------------------- helpers ---

/** _f(value): one decimal, trailing ".0" dropped. This studio keeps "-0". */
function f(value) {
  const text = fmt1(value);
  return text.endsWith('.0') ? text.slice(0, -2) : text;
}

/** _stroke(source, target, min_output): the 512-unit stroke floor, formatted. */
function stroke(source, target, minOutput = 1.0) {
  return f(Math.max(source, pyRound(minOutput * SIZE / target, 1)));
}

/** _xy(radius, degrees): a point on a circle about the centre, angle in degrees. */
function xyDeg(radius, deg) {
  const a = radians(deg);
  return [C + radius * cos(a), C + radius * sin(a)];
}

/** _open(target, safe, base, accent): the shared document head. */
function open_(target, safe, base, accent) {
  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<svg xmlns="http://www.w3.org/2000/svg" width="${target}" height="${target}" `
      + `viewBox="0 0 ${SIZE} ${SIZE}" role="img" aria-label="${safe}">`,
    '<defs><clipPath id="disc"><circle cx="256" cy="256" r="220"/></clipPath>',
    '<linearGradient id="depth" x1="0" y1="0" x2="0" y2="1">'
      + '<stop offset="0" stop-color="#fff" stop-opacity=".18"/>'
      + '<stop offset="1" stop-color="#000" stop-opacity=".28"/></linearGradient></defs>',
    '<g id="base" clip-path="url(#disc)">',
    `<circle cx="256" cy="256" r="220" fill="${base}"/>`,
    '<circle cx="256" cy="256" r="220" fill="url(#depth)"/>',
    '</g>',
    '<g id="rim" fill="none">',
    `<circle cx="256" cy="256" r="216" stroke="${accent}" stroke-width="${stroke(7, target)}" opacity=".9"/>`,
    `<circle cx="256" cy="256" r="201" stroke="#fff" stroke-width="${stroke(3, target)}" opacity=".28"/>`,
    '</g>',
  ];
}

// Python's str.strip() strips every code point str.isspace() accepts, which is
// not JS's \s set: it adds \x1c-\x1f and \x85, and it excludes U+FEFF. core.mjs
// has no strip, so this module carries its own (see the packet's Uncertain note).
const PY_SPACE = /[\u0009\u000a\u000b\u000c\u000d\u001c\u001d\u001e\u001f\u0020\u0085\u00a0\u1680\u2028\u2029\u202f\u205f\u3000\u2000-\u200a]/;

function pyStrip(text) {
  let start = 0;
  let end = text.length;
  while (start < end && PY_SPACE.test(text[start])) start++;
  while (end > start && PY_SPACE.test(text[end - 1])) end--;
  return text.slice(start, end);
}

/** Python's `s[:k]` -- a slice by code point, not by UTF-16 unit. */
function head(text, k) {
  return Array.from(text).slice(0, k).join('');
}

/** _label_plate(label, accent, knock): a broadcast name plate, at target 220 only. */
function labelPlate(label, accent, knock) {
  const display = head(pyStrip(label), 10);
  if (!display) return [];
  const size = 22.0;
  const spacing = 2.0;
  const textW = Array.from(display).length * (size * 0.63 + spacing);
  const width = Math.max(122.0, textW + 46);
  const x = C - width / 2;
  return [
    '<g id="text">',
    `<rect x="${f(x)}" y="402" width="${f(width)}" height="38" rx="7" fill="${accent}"/>`,
    `<rect x="${f(x + 11)}" y="410" width="7" height="22" rx="3.5" fill="${knock}" opacity=".95"/>`,
    `<text x="${f(C + spacing / 2 + 5)}" y="428" text-anchor="middle" font-family="sans-serif" font-size="22" `
      + `font-weight="700" letter-spacing="2" fill="${knock}">${escape(display)}</text>`,
    '</g>',
  ];
}

function close_(safe) {
  return [`<title>${safe}</title>`, '</svg>'];
}

function guard(target) {
  if (!TARGETS.includes(target)) throw new Error('target must be one of 42, 96, 220');
}

// ------------------------------------------------------------ chevron-run ---

export function chevron_run(seed, base, accent, target, label) {
  guard(target);
  const rng = new PyRandom(seed);
  const tilt = rng.uniform(-17, 17);
  const pitch = rng.uniform(54, 76);
  const phase = rng.uniform(-34, 34);
  const arm = rng.uniform(96, 140);
  const chipDeg = rng.uniform(-46, 46);

  const safe = escape(label);
  const edge = contrastInk(base);
  const knock = contrastInk(accent, 0.5);
  const count = target === 42 ? 3 : (target === 96 ? 4 : 5);
  const nose = 84.0;
  const width = target === 42 ? 40 : (target === 96 ? 34 : 30);

  const out = open_(target, safe, base, accent);
  out.push('<g id="art" clip-path="url(#disc)">');
  out.push(`<g transform="rotate(${f(tilt)} 256 256)">`);
  out.push(`<rect x="-60" y="${f(C - arm - 34)}" width="632" height="${f(2 * arm + 68)}" fill="${accent}" opacity=".16"/>`);
  if (target !== 42) {
    const reach = (count - 1) / 2.0 * pitch + nose;
    for (const sign of [-1, 1]) {
      const y = C + sign * (arm + 16);
      out.push(`<path d="M${f(C + phase * 0.5 - reach - 46)} ${f(y)} H${f(C + phase * 0.5 + reach)}" `
        + `stroke="${accent}" stroke-width="${stroke(6, target, 1.0)}" opacity=".3" stroke-linecap="round"/>`);
    }
  }
  const span = (count - 1) * pitch;
  for (let i = 0; i < count; i++) {
    const x = C + phase * 0.5 + (i - (count - 1) / 2.0) * pitch - span * 0.0;
    const opacity = 0.42 + 0.58 * (i / (count - 1));
    out.push(`<path d="M${f(x - nose / 2)} ${f(C - arm)} L${f(x + nose / 2)} 256 L${f(x - nose / 2)} ${f(C + arm)}" `
      + `fill="none" stroke="${accent}" stroke-width="${stroke(width, target, 2.0)}" `
      + `stroke-linecap="butt" stroke-linejoin="miter" opacity="${fmt2(opacity)}"/>`);
  }
  const leadX = C + phase * 0.5 + ((count - 1) / 2.0) * pitch;
  // the lit nose rides on top of the accent mass, so it takes the knock ink
  out.push(`<path d="M${f(leadX - nose / 2)} ${f(C - arm)} L${f(leadX + nose / 2)} 256 L${f(leadX - nose / 2)} ${f(C + arm)}" `
    + `fill="none" stroke="${knock}" stroke-width="${stroke(width * 0.34, target, 1.4)}" `
    + 'stroke-linecap="butt" stroke-linejoin="miter" opacity=".95"/>');
  out.push('</g>');
  out.push('</g>');

  const cx = C + chipDeg * 1.8;
  const cy = C - arm - 24;
  const size = target === 42 ? 30 : 26;
  out.push(
    '<g id="stamp">',
    `<rect x="${f(cx - size / 2)}" y="${f(cy - size / 2)}" width="${size}" height="${size}" rx="4" `
      + `fill="${edge}" transform="rotate(${f(tilt)} ${f(cx)} ${f(cy)})"/>`,
    `<rect x="${f(cx - size / 2)}" y="${f(cy - size / 2)}" width="${size}" height="${size}" rx="4" `
      + `fill="none" stroke="${accent}" stroke-width="${stroke(7, target, 1.0)}" `
      + `transform="rotate(${f(tilt)} ${f(cx)} ${f(cy)})"/>`,
    '</g>',
  );
  if (target === 220) out.push(...labelPlate(label, accent, knock));
  out.push(...close_(safe));
  return out.join('\n') + '\n';
}

// -------------------------------------------------------------- score-bug ---

export function score_bug(seed, base, accent, target, label) {
  guard(target);
  const rng = new PyRandom(seed);
  const tilt = rng.uniform(-5, 5);
  const yOff = rng.uniform(-26, 36);
  const lit = rng.randrange(1, 5);
  const chipRight = rng.randrange(2);
  const tickShift = rng.uniform(-18, 18);

  const safe = escape(label);
  const edge = contrastInk(base);
  const knock = contrastInk(accent, 0.5);
  const dim = luminance(accent) > 0.32 ? mix(accent, '#000000', 0.5) : mix(accent, '#000000', 0.62);
  const cy = C + yOff;
  const half = 54.0;
  const cells = target === 42 ? 3 : 5;
  const pad = 86.0;
  const chip = 66.0;
  const gap = 15.0;
  const colonW = 18.0;
  const runW = (SIZE - 2 * pad) - chip - colonW - 2 * gap;
  const cellGap = 12.0;
  const cellW = (runW - (cells - 1) * cellGap) / cells;
  let runX;
  let colonX;
  let chipX;
  if (chipRight) {
    runX = pad;
    colonX = pad + runW + gap;
    chipX = colonX + colonW + gap;
  } else {
    chipX = pad;
    colonX = pad + chip + gap;
    runX = colonX + colonW + gap;
  }

  const out = open_(target, safe, base, accent);
  out.push('<g id="art" clip-path="url(#disc)">');
  out.push(`<g transform="rotate(${f(tilt)} 256 256)">`);
  // rule above the plate, then the plate, then its drop shadow
  out.push(`<rect x="-40" y="${f(cy - half - 26)}" width="592" height="${stroke(9, target, 1.2)}" fill="${edge}" opacity=".9"/>`);
  if (target !== 42) {
    for (let i = 0; i < 3; i++) {
      out.push(`<rect x="${f(96 + tickShift + i * 42)}" y="${f(cy - half - 48)}" `
        + `width="${stroke(9, target, 1.0)}" height="18" fill="${accent}" opacity=".5"/>`);
    }
  }
  out.push(`<rect x="-40" y="${f(cy - half)}" width="592" height="${f(2 * half)}" fill="${accent}"/>`);
  out.push(`<rect x="-40" y="${f(cy + half)}" width="592" height="18" fill="#000" opacity=".26"/>`);
  out.push(`<rect x="-40" y="${f(cy + half + 18)}" width="592" height="${stroke(7, target, 1.0)}" fill="${accent}" opacity=".55"/>`);
  // logo chip
  out.push(`<rect x="${f(chipX)}" y="${f(cy - chip / 2)}" width="${f(chip)}" height="${f(chip)}" rx="8" fill="${knock}"/>`);
  out.push(`<path d="M${f(chipX + chip * 0.3)} ${f(cy - chip * 0.24)} L${f(chipX + chip * 0.68)} ${f(cy)} `
    + `L${f(chipX + chip * 0.3)} ${f(cy + chip * 0.24)}" fill="none" stroke="${accent}" `
    + `stroke-width="${stroke(12, target, 1.6)}" stroke-linejoin="miter"/>`);
  // tally segments
  for (let i = 0; i < cells; i++) {
    const x = runX + i * (cellW + cellGap);
    const on = i < lit;
    out.push(`<rect x="${f(x)}" y="${f(cy - 23)}" width="${f(cellW)}" height="46" rx="4" fill="${on ? knock : dim}"/>`);
  }
  out.push('</g>');
  out.push('</g>');
  // the clock colon, sitting between the chip and the tally
  out.push('<g id="stamp">');
  for (const dy of [-27, 7]) {
    out.push(`<rect x="${f(colonX)}" y="${f(cy + dy)}" width="${f(colonW)}" height="${f(colonW)}" rx="3" `
      + `fill="${knock}" transform="rotate(${f(tilt)} 256 256)"/>`);
  }
  out.push('</g>');
  if (target === 220) out.push(...labelPlate(label, accent, knock));
  out.push(...close_(safe));
  return out.join('\n') + '\n';
}

// ------------------------------------------------------------ sweep-clock ---

export function sweep_clock(seed, base, accent, target, label) {
  guard(target);
  const rng = new PyRandom(seed);
  const start = rng.uniform(-118, -62);
  const sweep = rng.uniform(105, 300);
  const ringShift = rng.uniform(0, 14);
  const hub = rng.uniform(46, 62);
  const pipR = rng.uniform(96, 138);

  const safe = escape(label);
  const edge = contrastInk(base);
  const knock = contrastInk(accent, 0.5);
  const ticks = target === 42 ? 6 : (target === 96 ? 12 : 24);
  const wedgeR = 152.0;
  const end = start + sweep;

  const out = open_(target, safe, base, accent);
  out.push('<g id="art" clip-path="url(#disc)">');
  out.push(`<circle cx="256" cy="256" r="184" fill="none" stroke="${accent}" `
    + `stroke-width="${stroke(11, target, 1.0)}" opacity=".3"/>`);
  for (let i = 0; i < ticks; i++) {
    const deg = ringShift + i * (360.0 / ticks);
    const major = (i % Math.max(1, Math.trunc(ticks / 4))) === 0;
    const inner = major ? 158.0 : 168.0;
    const [x0, y0] = xyDeg(inner, deg);
    const [x1, y1] = xyDeg(196.0, deg);
    out.push(`<path d="M${f(x0)} ${f(y0)} L${f(x1)} ${f(y1)}" stroke="${major ? edge : accent}" `
      + `stroke-width="${stroke(major ? 16 : 11, target, major ? 1.6 : 1.0)}" `
      + `stroke-linecap="butt" opacity="${major ? '.92' : '.8'}"/>`);
  }
  const large = sweep > 180 ? 1 : 0;
  const [sx, sy] = xyDeg(wedgeR, start);
  const [ex, ey] = xyDeg(wedgeR, end);
  out.push(`<path d="M256 256 L${f(sx)} ${f(sy)} A${f(wedgeR)} ${f(wedgeR)} 0 ${large} 1 ${f(ex)} ${f(ey)} Z" `
    + `fill="${accent}" opacity=".62"/>`);
  out.push(`<path d="M256 256 L${f(sx)} ${f(sy)} A${f(wedgeR)} ${f(wedgeR)} 0 ${large} 1 ${f(ex)} ${f(ey)} Z" `
    + `fill="none" stroke="${accent}" stroke-width="${stroke(10, target, 1.0)}" stroke-linejoin="round"/>`);
  const [hx, hy] = xyDeg(178.0, end);
  out.push(`<path d="M256 256 L${f(hx)} ${f(hy)}" stroke="${edge}" `
    + `stroke-width="${stroke(18, target, 2.4)}" stroke-linecap="round"/>`);
  const [px, py] = xyDeg(pipR, start + sweep / 2.0);
  out.push(`<circle cx="${f(px)}" cy="${f(py)}" r="${target === 42 ? 14 : 11}" fill="${edge}" opacity=".9"/>`);
  out.push('</g>');
  out.push(
    '<g id="stamp">',
    `<circle cx="256" cy="256" r="${f(hub)}" fill="${base}" stroke="${accent}" stroke-width="${stroke(14, target, 1.6)}"/>`,
    `<circle cx="256" cy="256" r="${f(hub * 0.38)}" fill="${edge}"/>`,
    '</g>',
  );
  if (target === 220) out.push(...labelPlate(label, accent, knock));
  out.push(...close_(safe));
  return out.join('\n') + '\n';
}

export const RENDERERS = {
  'chevron-run': chevron_run,
  'score-bug': score_bug,
  'sweep-clock': sweep_clock,
};
