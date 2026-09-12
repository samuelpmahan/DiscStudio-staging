// families/botanical.mjs -- the botanical studio's disc-art families.
//
// Each export has paint_components.render's shape minus the family name:
//     render(seed, base, accent, target, label) -> string, the whole SVG document
// painter.mjs already dispatches every slug below to the function beside it, so
// filling these in is the whole job; do not edit painter.mjs or core.mjs.
//
// Where the reference bytes come from, per art_registry.py:
//   pressed-fern      paint_families.py (promoted copy -- the one the registry serves)
//   nodding-seedhead  paint_families.py (promoted copy -- the one the registry serves)
//   block-print       _families_botanical.py
//
// The promoted copy and the retained studio copy share every helper below
// character for character (paint_families spells the formatter `_bn`, the studio
// module spells it `n`), so one set of helpers serves all three families.
//
// Dependency-free: this file may import ../core.mjs and nothing else -- no npm,
// no DOM, Node 22 and browsers alike.

import {
  PyRandom, escape, fmt1, fmt2, pyRound, pyRoundInt, pyMod,
  sin, cos, atan2, hypot, degrees, radians,
  SIZE, C, TARGETS, TAU,
} from '../core.mjs';

const GOLDEN = 2.399963229728653;
const HEX = /^#[0-9a-fA-F]{6}$/;

// ---------------------------------------------------------------- primitives

function check(base, accent, target) {
  if (!TARGETS.includes(target)) throw new Error('target must be one of 42, 96, 220');
  if (!HEX.test(base) || !HEX.test(accent)) throw new Error('base and accent must be six-digit hex colors');
}

/** _rgb(value): the three byte channels of a #rrggbb string. */
function rgb(value) {
  return [parseInt(value.slice(1, 3), 16), parseInt(value.slice(3, 5), 16), parseInt(value.slice(5, 7), 16)];
}

/** mix(a, b, t): "#%02x%02x%02x" over int(round(...)), with t clamped to [0, 1]. */
export function mix(a, b, t) {
  const [ar, ag, ab] = rgb(a);
  const [br, bg, bb] = rgb(b);
  const k = t < 0.0 ? 0.0 : (t > 1.0 ? 1.0 : t);
  const byte = (v) => pyRoundInt(v).toString(16).padStart(2, '0');
  return '#' + byte(ar + (br - ar) * k) + byte(ag + (bg - ag) * k) + byte(ab + (bb - ab) * k);
}

/** luma(value): rough relative luminance in [0, 1]. */
export function luma(value) {
  const [r, g, b] = rgb(value);
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0;
}

/** stroke_for(target, source, min_output): the 512-unit stroke floor, as a number. */
function strokeFor(target, source, minOutput = 1.0) {
  const scale = target / SIZE;
  return Math.max(source, pyRound(minOutput / scale, 1));
}

/** _bn / n: one decimal, trailing ".0" dropped, "-0" collapsed to "0". */
function n(value) {
  let text = fmt1(value);
  if (text.endsWith('.0')) text = text.slice(0, -2);
  return (text === '-0' || text === '') ? '0' : text;
}

/** tones(base, accent): the studio palette -- warm paper, one ink, the tints between. */
export function tones(base, accent) {
  let paper;
  let deckle;
  if (luma(base) < 0.42) {
    paper = mix(base, accent, 0.13);
    deckle = mix(base, accent, 0.24);
  } else {
    paper = mix(base, '#fdf6e6', 0.44);
    deckle = mix(base, accent, 0.16);
  }
  return {
    paper,
    deckle,
    ink: accent,
    ghost: mix(accent, paper, 0.64),
    mid: mix(accent, paper, 0.36),
    hair: mix(accent, paper, 0.52),
    grain: mix(accent, paper, 0.44),
  };
}

// ------------------------------------------------------------------ geometry

function qpoint(p0, p1, p2, t) {
  const u = 1.0 - t;
  return [u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
    u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]];
}

function qangle(p0, p1, p2, t) {
  const u = 1.0 - t;
  const dx = 2 * u * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0]);
  const dy = 2 * u * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1]);
  return degrees(atan2(dy, dx));
}

/** Control point that bows the p0->p2 chord sideways by `bow` of its length. */
function control(p0, p2, bow) {
  const mx = (p0[0] + p2[0]) / 2.0;
  const my = (p0[1] + p2[1]) / 2.0;
  const dx = p2[0] - p0[0];
  const dy = p2[1] - p0[1];
  return [mx - dy * bow, my + dx * bow];
}

/** A tapered leaf blade rooted at (x, y), pointing along `angle` degrees. */
function blade(x, y, angle, length, width, bend = 0.0) {
  const a = radians(angle);
  const dx = cos(a);
  const dy = sin(a);
  const px = -dy;
  const py = dx;
  const tipx = x + dx * length;
  const tipy = y + dy * length;
  const m = 0.44;
  const lift = bend * length * 0.20;
  const b1x = x + dx * length * m + px * (width + lift);
  const b1y = y + dy * length * m + py * (width + lift);
  const b2x = x + dx * length * m - px * (width - lift);
  const b2y = y + dy * length * m - py * (width - lift);
  return `M${n(x)} ${n(y)}Q${n(b1x)} ${n(b1y)} ${n(tipx)} ${n(tipy)}`
    + `Q${n(b2x)} ${n(b2y)} ${n(x)} ${n(y)}Z`;
}

/** Closed polygon around a centreline, half-width per point (a tapered stem). */
function taper(points, widths) {
  const left = [];
  const right = [];
  const count = points.length;
  for (let i = 0; i < count; i++) {
    const [x, y] = points[i];
    const j = Math.min(i + 1, count - 1);
    const k = Math.max(i - 1, 0);
    const dx = points[j][0] - points[k][0];
    const dy = points[j][1] - points[k][1];
    const length = hypot(dx, dy) || 1.0;
    const px = -dy / length;
    const py = dx / length;
    const w = widths[i];
    left.push(`${n(x + px * w)} ${n(y + py * w)}`);
    right.push(`${n(x - px * w)} ${n(y - py * w)}`);
  }
  return 'M' + left.join('L') + 'L' + right.slice().reverse().join('L') + 'Z';
}

// ------------------------------------------------------------- shared chrome

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

/** Paper fibre speckle. Deterministic from one seeded phase; none at 42. */
function grain(target, phase, color) {
  const count = target === 42 ? 0 : (target === 96 ? 26 : 54);
  const out = [];
  for (let i = 0; i < count; i++) {
    const a = i * GOLDEN + phase;
    const rad = 212.0 * Math.sqrt(pyMod(i * 0.6180339887 + phase * 0.159, 1.0));
    const x = C + rad * cos(a);
    const y = C + rad * sin(a);
    const size = 1.4 + 1.9 * ((i * 7 + 3) % 5) / 4.0;
    const opacity = 0.10 + 0.05 * ((i * 3) % 4) / 3.0;
    if (i % 3 === 0 && target === 220) {
      out.push(`<rect x="${n(x)}" y="${n(y)}" width="${n(size * 3.4)}" height="${n(size * 0.7)}"`
        + ` transform="rotate(${n(pyMod(a * 27, 180))} ${n(x)} ${n(y)})" opacity="${fmt2(opacity)}"/>`);
    } else {
      out.push(`<circle cx="${n(x)}" cy="${n(y)}" r="${n(size)}" opacity="${fmt2(opacity)}"/>`);
    }
  }
  return out.length ? [`<g id="grain" fill="${color}">`, ...out, '</g>'] : [];
}

/** The mount label: a small paper plaque with the disc label and a figure. */
function plaque(t, label, figure, tilt) {
  const safe = escape(head(pyStrip(label), 13));
  return [
    `<g id="plaque" transform="rotate(${n(tilt)} 256 418)">`,
    `<rect x="150" y="386" width="212" height="64" rx="3" fill="${t.paper}"`
      + ` stroke="${t.hair}" stroke-width="1.6" opacity=".95"/>`,
    '<rect x="155" y="391" width="202" height="54" rx="2" fill="none"'
      + ` stroke="${t.hair}" stroke-width=".8" opacity=".6"/>`,
    '<text x="256" y="420" text-anchor="middle" font-family="serif" font-size="23"'
      + ` letter-spacing="1.5" fill="${t.ink}">${safe}</text>`,
    '<text x="256" y="439" text-anchor="middle" font-family="sans-serif" font-size="11"'
      + ` letter-spacing="3" fill="${t.mid}">${escape(figure)}</text>`,
    '</g>',
  ];
}

function document_(target, label, base, t, art, text, grainPhase, defs = '') {
  const safe = escape(label);
  const out = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<svg xmlns="http://www.w3.org/2000/svg" width="${target}" height="${target}"`
      + ` viewBox="0 0 ${SIZE} ${SIZE}" role="img" aria-label="${safe}">`,
    '<defs><clipPath id="disc"><circle cx="256" cy="256" r="220"/></clipPath>',
    '<radialGradient id="depth" cx=".38" cy=".32" r=".78">'
      + '<stop offset="0" stop-color="#fff" stop-opacity=".16"/>'
      + '<stop offset=".72" stop-color="#fff" stop-opacity="0"/>'
      + '<stop offset="1" stop-color="#000" stop-opacity=".20"/></radialGradient>'
      + defs + '</defs>',
    '<g id="base" clip-path="url(#disc)">',
    `<circle cx="256" cy="256" r="220" fill="${base}"/>`,
    `<circle cx="256" cy="256" r="220" fill="${t.paper}" opacity=".93"/>`,
  ];
  out.push(...grain(target, grainPhase, t.grain));
  out.push('<circle cx="256" cy="256" r="220" fill="url(#depth)"/>', '</g>',
    '<g id="art" clip-path="url(#disc)">');
  out.push(...art);
  out.push('</g>', '<g id="rim" fill="none">',
    `<circle cx="256" cy="256" r="216" stroke="${t.ink}"`
      + ` stroke-width="${n(strokeFor(target, 7))}" opacity=".9"/>`,
    `<circle cx="256" cy="256" r="205" stroke="${t.deckle}"`
      + ` stroke-width="${n(strokeFor(target, 3))}" opacity=".55"/>`, '</g>');
  if (text.length) out.push('<g id="text">', ...text, '</g>');
  out.push(`<title>${safe}</title>`, '</svg>');
  return out.join('\n') + '\n';
}

// ----------------------------------------------------------- 1. pressed-fern

export function pressed_fern(seed, base, accent, target, label) {
  check(base, accent, target);
  const rng = new PyRandom(seed);
  const rot = rng.uniform(-30, 30);
  const bow = rng.uniform(0.14, 0.34) * (rng.random() < 0.5 ? 1.0 : -1.0);
  const back = rng.uniform(30, 48);
  const widthK = rng.uniform(0.15, 0.20);
  const reach = rng.uniform(0.92, 1.10);
  const ghostRot = rng.uniform(9, 21) * (bow > 0 ? -1.0 : 1.0);
  const ghostSlip = rng.uniform(26, 46);
  const pitchK = rng.uniform(0.88, 1.14);
  const jit = [];
  for (let i = 0; i < 48; i++) jit.push(rng.uniform(-1.0, 1.0));
  const number = rng.randrange(104, 989);
  const tilt = rng.uniform(-2.2, 2.2);
  const grainPhase = rng.uniform(0, TAU);
  const t = tones(base, accent);

  const p0 = [104.0, 416.0];
  const p2 = [416.0, 108.0];
  const p1 = control(p0, p2, bow);

  const frond = (color, pairs, opacity, detail, veins, outline = '') => {
    const bulk = target === 42 ? 1.35 : 1.0;
    const cut = outline
      ? ` stroke="${outline}" stroke-width="2.6" stroke-opacity=".6" stroke-linejoin="round"`
      : '';
    const out = [`<g fill="${color}"${cut}>`];
    const vein = [];
    const pts = [];
    const widths = [];
    for (let i = 0; i < 21; i++) {
      pts.push(qpoint(p0, p1, p2, i / 20.0));
      widths.push(11.5 * bulk * (1.0 - 0.70 * (i / 20.0)) + 1.8);
    }
    out.push(`<path d="${taper(pts, widths)}"/>`);
    for (let i = 0; i < pairs; i++) {
      const u = 0.07 + (i + 0.5) / pairs * 0.90;
      const [x, y] = qpoint(p0, p1, p2, u);
      const ang = qangle(p0, p1, p2, u);
      // a frond swells just above the stipe and tapers to the crozier
      const prof = (1.16 - 0.86 * u) * Math.min(1.0, 0.34 + 2.6 * u);
      const length = 150.0 * reach * pitchK * Math.max(prof, 0.16);
      // at 42 the frond carries fewer, fatter pinnae so the mark keeps its mass
      const w = length * widthK * (target === 42 ? 1.55 : 1.0);
      for (const side of [1.0, -1.0]) {
        const j = jit[(i * 2 + (side > 0 ? 0 : 1)) % 48];
        const a = ang + side * (back + j * 7.0);
        out.push(`<path d="${blade(x, y, a, length * (1.0 + j * 0.07), w, side * 0.34)}"/>`);
        if (veins) {
          const ar = radians(a);
          vein.push(`M${n(x)} ${n(y)}L${n(x + cos(ar) * length * 0.88)}`
            + ` ${n(y + sin(ar) * length * 0.88)}`);
        }
      }
    }
    if (detail) {
      // the crozier: the frond tip still curled from the press
      const [tipx, tipy] = qpoint(p0, p1, p2, 1.0);
      const ang = radians(qangle(p0, p1, p2, 1.0));
      const cx = tipx + cos(ang) * 16 - sin(ang) * 15;
      const cy = tipy + sin(ang) * 16 + cos(ang) * 15;
      out.push(`<path d="M${n(tipx)} ${n(tipy)}Q${n(tipx + cos(ang) * 30)}`
        + ` ${n(tipy + sin(ang) * 30)} ${n(cx)} ${n(cy)}" fill="none"`
        + ` stroke="${color}" stroke-width="7" stroke-linecap="round"/>`);
    }
    out.push('</g>');
    if (vein.length) {
      out.push(`<path d="${vein.join('')}" stroke="${t.paper}" stroke-width="1.7"`
        + ' opacity=".38" fill="none"/>');
    }
    return out;
  };

  const art = [];
  const pairs = target === 42 ? 5 : (target === 96 ? 10 : 14);
  if (target !== 42) {
    art.push(`<g id="ghost" transform="rotate(${n(rot + ghostRot)} 256 256)`
      + ` translate(${n(ghostSlip)} ${n(ghostSlip * 0.5)})" opacity=".42">`);
    art.push(...frond(t.ghost, Math.max(5, pairs - 4), 1.0, false, false));
    art.push('</g>');
  }
  art.push(`<g id="frond" transform="rotate(${n(rot)} 256 256)">`);
  art.push(...frond(t.ink, pairs, 1.0, target !== 42, target === 220,
    target !== 42 ? t.paper : ''));
  art.push('</g>');
  if (target === 220) {
    // mounting tape, the way a pressed specimen is held to the sheet
    for (const [tx, ty, ta] of [[150.0, 168.0, 62.0], [330.0, 330.0, 62.0]]) {
      art.push(`<g transform="rotate(${n(ta + rot)} ${n(tx)} ${n(ty)})">`
        + `<rect x="${n(tx - 52)}" y="${n(ty - 13)}" width="104" height="26" rx="2"`
        + ` fill="${t.paper}" opacity=".3"/>`
        + `<rect x="${n(tx - 52)}" y="${n(ty - 13)}" width="104" height="26" rx="2" fill="none"`
        + ` stroke="${t.paper}" stroke-width="1.4" opacity=".5"/></g>`);
    }
  }
  const text = target === 220 ? plaque(t, label, `No. ${number}`, tilt) : [];
  return document_(target, label, base, t, art, text, grainPhase);
}

// ------------------------------------------------------- 2. nodding-seedhead

export function nodding_seedhead(seed, base, accent, target, label) {
  check(base, accent, target);
  const rng = new PyRandom(seed);
  const headA = rng.uniform(-2.55, -0.62);
  const headD = rng.uniform(62, 98);
  const headR = rng.uniform(82, 100);
  const bracts = rng.randrange(11, 18);
  const bractLen = rng.uniform(26, 44);
  const seedPhase = rng.uniform(0, TAU);
  const stalkBow = rng.uniform(-0.30, 0.30);
  const leafSide = rng.random() < 0.5 ? 1.0 : -1.0;
  const leafLen = rng.uniform(92, 124);
  const leafAt = rng.uniform(0.34, 0.52);
  const drift = [];
  for (let i = 0; i < 4; i++) {
    drift.push([rng.uniform(0, TAU), rng.uniform(140, 205), rng.uniform(12, 18),
      rng.uniform(0, 180)]);
  }
  const jit = [];
  for (let i = 0; i < 40; i++) jit.push(rng.uniform(-1.0, 1.0));
  const count = rng.randrange(23, 97);
  const tilt = rng.uniform(-2.2, 2.2);
  const grainPhase = rng.uniform(0, TAU);
  const t = tones(base, accent);

  const hx = C + headD * cos(headA);
  const hy = C + headD * sin(headA);
  const foot = [C + stalkBow * 150.0, 486.0];
  const stemC = control([hx, hy], foot, stalkBow * 0.42 + 0.14);
  const steps = 16;
  const pts = [];
  const widths = [];
  for (let i = 0; i <= steps; i++) {
    pts.push(qpoint([hx, hy], stemC, foot, i / steps));
    widths.push(7.0 + 6.5 * (i / steps));
  }

  const art = [];
  // stalk
  art.push(`<path d="${taper(pts, widths)}" fill="${t.ink}"/>`);
  // stalk leaves
  const leaves = target === 42 ? 1 : 2;
  for (let i = 0; i < leaves; i++) {
    const u = leafAt + i * 0.22;
    const [lx, ly] = qpoint([hx, hy], stemC, foot, Math.min(u, 0.92));
    const ang = qangle([hx, hy], stemC, foot, Math.min(u, 0.92));
    const side = i % 2 === 0 ? leafSide : -leafSide;
    art.push(`<path d="${blade(lx, ly, ang + side * 78, leafLen * (1 - i * 0.16), leafLen * 0.26, side * 0.95)}"`
      + ` fill="${t.ink}" stroke="${t.paper}" stroke-width="2.4" stroke-opacity=".5"/>`);
    if (target === 220) {
      const ar = radians(ang + side * 78);
      art.push(`<path d="M${n(lx)} ${n(ly)}L${n(lx + cos(ar) * leafLen * 0.8)}`
        + ` ${n(ly + sin(ar) * leafLen * 0.8)}" stroke="${t.paper}"`
        + ' stroke-width="2" opacity=".4" fill="none"/>');
    }
  }
  // bracts around the head
  const shown = target === 42 ? 8 : bracts;
  for (let i = 0; i < shown; i++) {
    const a = i * TAU / shown + seedPhase * 0.3;
    const j = jit[i % 40];
    const reach = headR + bractLen * (1.0 + j * 0.28);
    art.push(`<path d="M${n(hx + cos(a - 0.16) * headR * 0.92)} ${n(hy + sin(a - 0.16) * headR * 0.92)}`
      + `L${n(hx + cos(a) * reach)} ${n(hy + sin(a) * reach)}`
      + `L${n(hx + cos(a + 0.16) * headR * 0.92)} ${n(hy + sin(a + 0.16) * headR * 0.92)}Z"`
      + ` fill="${(target === 220 && i % 2) ? t.mid : t.ink}"/>`);
  }
  // the head itself
  art.push(`<circle cx="${n(hx)}" cy="${n(hy)}" r="${n(headR)}" fill="${t.ink}"/>`);
  if (target === 220) {
    const arcs = [];
    for (let k = 0; k < 11; k++) {
      const leg = [];
      for (let step = 0; step < 7; step++) {
        const u = step / 6.0;
        const rad = headR * 0.96 * u;
        const a = k * TAU / 11 + seedPhase + u * 1.35;
        leg.push(`${n(hx + rad * cos(a))} ${n(hy + rad * sin(a))}`);
      }
      arcs.push('M' + leg.join('L'));
    }
    art.push(`<path d="${arcs.join('')}" fill="none" stroke="${t.paper}"`
      + ' stroke-width="1.6" opacity=".22"/>');
  }
  const seeds = target === 42 ? 9 : (target === 96 ? 48 : 118);
  art.push(`<g id="achenes" fill="${t.paper}" opacity=".82">`);
  for (let i = 0; i < seeds; i++) {
    const u = (i + 0.6) / seeds;
    const rad = headR * 0.88 * Math.sqrt(u);
    const a = i * GOLDEN + seedPhase;
    const size = (target === 42 ? 5.6 : (target === 96 ? 3.5 : 2.9)) * (0.62 + 0.62 * Math.sqrt(u));
    art.push(`<circle cx="${n(hx + rad * cos(a))}" cy="${n(hy + rad * sin(a))}"`
      + ` r="${n(size)}"/>`);
  }
  art.push('</g>');
  // loosed seeds drifting off the head
  const floats = target === 42 ? 0 : (target === 96 ? 2 : 4);
  for (let i = 0; i < floats; i++) {
    const [a, dist, size, spin] = drift[i];
    const fx = hx + cos(a) * dist * 0.62;
    const fy = hy + sin(a) * dist * 0.52;
    const rays = [];
    for (let k = 0; k < 7; k++) {
      const ra = -Math.PI / 2 + (k - 3) * 0.34;
      rays.push(`M${n(fx)} ${n(fy - size)}L${n(fx + cos(ra) * size * 2.1)}`
        + ` ${n(fy - size + sin(ra) * size * 2.1)}`);
    }
    art.push(`<g transform="rotate(${n(spin)} ${n(fx)} ${n(fy)})">`
      + `<ellipse cx="${n(fx)}" cy="${n(fy)}" rx="${n(size * 0.42)}" ry="${n(size)}" fill="${t.ink}"/>`
      + `<path d="${rays.join('')}" stroke="${t.ink}" stroke-width="1.8" opacity=".72"`
      + ' fill="none"/></g>');
  }
  const text = target === 220 ? plaque(t, label, `ACHENES ${count}`, tilt) : [];
  return document_(target, label, base, t, art, text, grainPhase);
}

// ------------------------------------------------------------ 3. block-print

/** A three-blade sprig, drawn around the origin at `scale` units. */
function sprig(scale, t, color, detail) {
  const out = [`<path d="M0 ${n(scale * 0.62)}Q${n(scale * 0.1)} 0 0 ${n(-scale * 0.66)}" fill="none"`
    + ` stroke-width="${n(scale * 0.085)}" stroke-linecap="round"/>`];
  for (const [y, side, ln] of [[0.30, 1.0, 0.62], [0.02, -1.0, 0.72], [-0.30, 1.0, 0.54]]) {
    out.push(`<path d="${blade(0, scale * y, -90 + side * 52, scale * ln, scale * ln * 0.30, side * 0.4)}"`
      + ' stroke="none"/>');
  }
  if (detail) {
    out.push(`<circle cx="0" cy="${n(-scale * 0.66)}" r="${n(scale * 0.09)}" stroke="none"/>`);
  }
  return out;
}

/** A split seed pod: a pointed hull with seeds inside. */
function pod(scale, t, color, detail) {
  const w = scale * 0.34;
  const out = [`<path d="M0 ${n(-scale * 0.7)}Q${n(w)} 0 0 ${n(scale * 0.7)}Q${n(-w)} 0 0 ${n(-scale * 0.7)}Z"`
    + ' stroke="none"/>'];
  if (detail) {
    for (const k of [-1, 0, 1]) {
      out.push(`<circle cx="0" cy="${n(k * scale * 0.28)}" r="${n(scale * 0.12)}"`
        + ` fill="${t.paper}" opacity=".8"/>`);
    }
  }
  return out;
}

/** A berry cluster: three fruits on short pedicels. */
function berry(scale, t, color, detail) {
  const out = [];
  for (const [dx, dy] of [[0.0, -0.34], [-0.30, 0.20], [0.30, 0.22]]) {
    out.push(`<path d="M0 0L${n(dx * scale)} ${n(dy * scale)}"`
      + ` stroke-width="${n(scale * 0.07)}" fill="none"/>`);
    out.push(`<circle cx="${n(dx * scale)}" cy="${n(dy * scale)}" r="${n(scale * 0.25)}" stroke="none"/>`);
    if (detail) {
      out.push(`<circle cx="${n(dx * scale - scale * 0.08)}" cy="${n(dy * scale - scale * 0.09)}"`
        + ` r="${n(scale * 0.06)}" fill="${t.paper}" opacity=".55"/>`);
    }
  }
  return out;
}

const MOTIFS = [sprig, pod, berry];
const PAIRS = [[0, 1], [0, 2], [1, 2]];

export function block_print(seed, base, accent, target, label) {
  check(base, accent, target);
  const rng = new PyRandom(seed);
  const rot = rng.uniform(-16, 16);
  const pitchK = rng.uniform(0.88, 1.12);
  const halfDrop = rng.random() < 0.62 ? 0.5 : 0.0;
  const misA = rng.uniform(0, TAU);
  const misD = rng.uniform(3.5, 8.5);
  const pair = PAIRS[rng.randrange(3)];
  const swap = rng.random() < 0.5;
  const jitter = rng.uniform(4, 15);
  const jit = [];
  for (let i = 0; i < 64; i++) jit.push(rng.uniform(-1.0, 1.0));
  const blockNo = rng.randrange(2, 19);
  const ticks = rng.randrange(28, 46);
  const tilt = rng.uniform(-2.2, 2.2);
  const grainPhase = rng.uniform(0, TAU);
  const t = tones(base, accent);

  const pitch = (target === 42 ? 150.0 : (target === 96 ? 124.0 : 108.0)) * pitchK;
  const row = pitch * 0.88;
  const scale = pitch * 0.56;
  const detail = target === 220;
  const cols = Math.trunc(560 / pitch) + 3;
  const rows = Math.trunc(560 / row) + 3;
  const mx = cos(misA) * misD;
  const my = sin(misA) * misD;

  const field = (color, dx, dy, wantDetail) => {
    const out = [`<g fill="${color}" stroke="${color}">`];
    for (let j = 0; j < rows; j++) {
      for (let i = 0; i < cols; i++) {
        const x = -pitch + i * pitch + (j % 2 ? halfDrop * pitch : 0.0) + dx;
        const y = -row + j * row + dy;
        if (hypot(x - C, y - C) > 244) continue;
        const k = (i * 7 + j * 13) % 64;
        const which = !swap ? pair[(i + j) % 2] : pair[(i + j + 1) % 2];
        const spin = jit[k] * jitter + ((i + j) % 2 ? 0.0 : 180.0);
        out.push(`<g transform="translate(${n(x)} ${n(y)}) rotate(${n(spin)})">`);
        out.push(...MOTIFS[which](scale, t, color, wantDetail));
        out.push('</g>');
      }
    }
    out.push('</g>');
    return out;
  };

  const art = [];
  art.push(`<g id="repeat" transform="rotate(${n(rot)} 256 256)">`);
  if (target !== 42) {
    art.push('<g id="offregister" opacity=".45">');
    art.push(...field(t.ghost, mx, my, false));
    art.push('</g>');
  }
  art.push(...field(t.ink, 0.0, 0.0, detail));
  art.push('</g>');
  if (target === 220) {
    art.push(`<circle cx="256" cy="256" r="196" fill="none" stroke="${t.mid}"`
      + ' stroke-width="2.4" opacity=".7"/>');
    art.push(`<circle cx="256" cy="256" r="188" fill="none" stroke="${t.mid}"`
      + ' stroke-width="1.1" opacity=".5"/>');
    const marks = [];
    for (let i = 0; i < ticks; i++) {
      const a = i * TAU / ticks + rot * Math.PI / 180;
      marks.push(`M${n(C + 196 * cos(a))} ${n(C + 196 * sin(a))}`
        + `L${n(C + 206 * cos(a))} ${n(C + 206 * sin(a))}`);
    }
    art.push(`<path d="${marks.join('')}" stroke="${t.mid}" stroke-width="2" opacity=".55" fill="none"/>`);
  }
  const text = target === 220 ? plaque(t, label, `BLOCK ${blockNo} / PULL II`, tilt) : [];
  return document_(target, label, base, t, art, text, grainPhase);
}

export const RENDERERS = {
  'pressed-fern': pressed_fern,
  'nodding-seedhead': nodding_seedhead,
  'block-print': block_print,
};
