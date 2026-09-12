// families/cartography.mjs -- the cartography studio's disc-art families.
//
// Each export has paint_components.render's shape minus the family name:
//     render(seed, base, accent, target, label) -> string, the whole SVG document
// painter.mjs already dispatches every slug below to the function beside it.
//
// Where the reference bytes come from, per art_registry.py:
//   contour-basin     _families_cartography.py
//   fairway-plat      _families_cartography.py
//   wind-rose         paint_families.py (promoted copy -- the one the registry serves)
//
// The promoted wind-rose in paint_families.py is the studio's own body with the
// formatter renamed (`n` there, `_cn` here) and nothing else changed, and both
// modules carry the same `poly`, `xy`, `_halo`, `_cartouche` and `_shell`, so
// one set of primitives below serves all three families.
//
// Dependency-free: imports ../core.mjs and nothing else -- no npm, no DOM.

import {
  PyRandom, escape, fmt1, pyRound, pyRoundInt,
  sin, cos, hypot, atan2, degrees, radians,
  SIZE, C, R, TAU,
} from '../core.mjs';

const TARGETS = [42, 96, 220];
const HEX = /^#[0-9a-fA-F]{6}$/;

// ---------------------------------------------------------------- primitives

function _check(base, accent, target) {
  if (!TARGETS.includes(target)) throw new Error('target must be one of 42, 96, 220');
  if (!HEX.test(base) || !HEX.test(accent)) {
    throw new Error('base and accent must be six-digit hex colors');
  }
}

function _rgb(value) {
  return [
    parseInt(value.slice(1, 3), 16),
    parseInt(value.slice(3, 5), 16),
    parseInt(value.slice(5, 7), 16),
  ];
}

const hex2 = (v) => (v < 16 ? '0' : '') + v.toString(16);

/** mix(a, b, t): blend two hex colors; Python's int(round(...)) is half-to-even. */
function mix(a, b, t) {
  const [ar, ag, ab] = _rgb(a);
  const [br, bg, bb] = _rgb(b);
  const k = t < 0.0 ? 0.0 : (t > 1.0 ? 1.0 : t);
  return '#' + hex2(pyRoundInt(ar + (br - ar) * k))
             + hex2(pyRoundInt(ag + (bg - ag) * k))
             + hex2(pyRoundInt(ab + (bb - ab) * k));
}

function luma(value) {
  const [r, g, b] = _rgb(value);
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0;
}

/** stroke_for(target, source, min_output): max(source, round(min_output/scale, 1)). */
function strokeFor(target, source, minOutput = 1.0) {
  const scale = target / SIZE;
  const floor = pyRound(minOutput / scale, 1);
  return floor > source ? floor : source;
}

/** The cartography studio's `n` / `_cn`: one decimal, no trailing ".0", keeps "-0". */
function n(value) {
  let text = fmt1(value);
  if (text.endsWith('.0')) text = text.slice(0, -2);
  return text === '-0' ? '-0' : text;
}

/** The studios' xy(radius, angle, cx=C, cy=C). */
function pt(radius, angle, cx = C, cy = C) {
  return [cx + radius * cos(angle), cy + radius * sin(angle)];
}

function poly(points, close = true) {
  const parts = ['M', n(points[0][0]), ' ', n(points[0][1])];
  for (let i = 1; i < points.length; i++) {
    parts.push('L', n(points[i][0]), ' ', n(points[i][1]));
  }
  if (close) parts.push('Z');
  return parts.join('');
}

// Python's str.strip() strips every code point str.isspace() accepts, which is
// not JS's \s set: it adds \x1c-\x1f and \x85, and it excludes U+FEFF.
const PY_SPACE_CODES = new Set([
  0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, 0x85, 0xa0,
  0x1680, 0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007,
  0x2008, 0x2009, 0x200a, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000,
]);

const isPySpace = (ch) => PY_SPACE_CODES.has(ch.charCodeAt(0));

function pyStrip(text) {
  let start = 0;
  let end = text.length;
  while (start < end && isPySpace(text[start])) start++;
  while (end > start && isPySpace(text[end - 1])) end--;
  return text.slice(start, end);
}

/** Python slices by code point; JS by UTF-16 unit. */
function pySlice(text, count) {
  return Array.from(text).slice(0, count).join('');
}

function pyLen(text) {
  return Array.from(text).length;
}

/** Shared document frame: base disc, art, rim, stamp, 220-only text. */
function _shell(slug, kind, target, label, base, accent, art, stamp, text) {
  const safe = escape(label);
  const aria = escape(`${label} — ${kind} course chart disc`);
  const ink = accent;
  const out = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<svg xmlns="http://www.w3.org/2000/svg" width="${target}" height="${target}" `
      + `viewBox="0 0 ${SIZE} ${SIZE}" role="img" aria-label="${aria}">`,
    `<defs><clipPath id="${slug}-disc"><circle cx="256" cy="256" r="${R}"/></clipPath>`,
    `<linearGradient id="${slug}-depth" x1="0" y1="0" x2="0" y2="1">`
      + '<stop offset="0" stop-color="#fff" stop-opacity=".18"/>'
      + '<stop offset="1" stop-color="#000" stop-opacity=".28"/></linearGradient></defs>',
    `<g id="base" clip-path="url(#${slug}-disc)">`,
    `<circle cx="256" cy="256" r="${R}" fill="${base}"/>`, '</g>',
    `<g id="art" clip-path="url(#${slug}-disc)">`,
  ];
  out.push(...art);
  out.push(
    `<circle cx="256" cy="256" r="${R}" fill="url(#${slug}-depth)"/>`,
    '</g>',
    '<g id="rim" fill="none">',
    `<circle cx="256" cy="256" r="216" stroke="${ink}" stroke-width="${n(strokeFor(target, 7))}" opacity=".9"/>`,
    `<circle cx="256" cy="256" r="201" stroke="#fff" stroke-width="${n(strokeFor(target, 3))}" opacity=".28"/>`,
    '</g>',
    '<g id="stamp">',
  );
  out.push(...stamp);
  out.push('</g>');
  if (target === 220 && text.length) {
    out.push('<g id="text">');
    out.push(...text);
    out.push('</g>');
  }
  out.push(`<title>${safe}</title>`, '</svg>');
  return out.join('\n') + '\n';
}

/** Map lettering: a fill with a matched halo, so figures read over any band. */
function _halo(x, y, body, size, fill, halo, target, opts = {}) {
  const anchor = opts.anchor ?? 'start';
  const weight = opts.weight ?? 400;
  const family = opts.family ?? 'sans-serif';
  const spacing = opts.spacing ?? 0.0;
  const bits = [`<text x="${n(x)}" y="${n(y)}" font-family="${family}" font-size="${n(size)}"`];
  if (weight !== 400) bits.push(` font-weight="${weight}"`);
  if (anchor !== 'start') bits.push(` text-anchor="${anchor}"`);
  if (spacing) bits.push(` letter-spacing="${n(spacing)}"`);
  bits.push(` fill="${fill}" stroke="${halo}" stroke-width="${n(strokeFor(target, size * 0.16, 1.4))}"`
    + ' stroke-linejoin="round" paint-order="stroke">' + body + '</text>');
  return bits.join('');
}

/** The sheet's name box: a legend cartouche so the label survives any palette. */
function _cartouche(label, base, accent, target) {
  const clipped = pySlice(pyStrip(label), 12);
  const display = escape(clipped);
  if (!display) return [];
  const span = Math.max(pyLen(clipped), 1);
  const width = Math.min(268.0, span * 16.4 + 30.0);
  const paper = mix(base, '#ffffff', 0.88);
  return [
    `<rect x="${n(256 - width / 2)}" y="398" width="${n(width)}" height="34" rx="5" fill="${paper}" `
      + `stroke="${accent}" stroke-width="${n(strokeFor(target, 2.6))}" opacity=".96"/>`,
    '<text x="256" y="421" text-anchor="middle" font-family="sans-serif" font-size="20" '
      + `letter-spacing="2.4" fill="${mix(accent, '#000000', 0.45)}">${display}</text>`,
  ];
}

// ------------------------------------------------------------ contour-basin

/** Filled contour bands: the terrain bowl the basket sits in, plated. */
export function contour_basin(seed, base, accent, target, label) {
  _check(base, accent, target);
  const rng = new PyRandom(seed);
  // --- identity, drawn once. Order is fixed so every target sees the same values.
  const offX = rng.uniform(-40.0, 40.0);
  const offY = rng.uniform(-34.0, 34.0);
  const tilt = rng.uniform(0.0, TAU);
  const drift = rng.uniform(10.0, 26.0);
  const k1 = rng.randrange(2, 5);
  const k2 = rng.randrange(5, 9);
  const a1 = rng.uniform(0.08, 0.17);
  const a2 = rng.uniform(0.03, 0.09);
  const p1 = rng.uniform(0.0, TAU);
  const p2 = rng.uniform(0.0, TAU);
  const squash = rng.uniform(0.74, 0.99);
  const rot = rng.uniform(-32.0, 32.0);
  const creekA = rng.uniform(0.0, TAU);
  const elevation = rng.randrange(180, 940);

  const bands = target === 42 ? 3 : (target === 96 ? 5 : 8);
  const samples = target === 42 ? 32 : (target === 96 ? 52 : 76);
  const low = mix(base, '#ffffff', 0.26);
  const high = mix(base, accent, 0.95);

  const ring = (radius, frac, wobble = 1.0) => {
    const cx = C + offX + drift * frac * cos(tilt);
    const cy = C + offY + drift * frac * sin(tilt);
    const pts = [];
    for (let i = 0; i < samples; i++) {
      const a = i * TAU / samples;
      const warp = 1.0 + wobble * (a1 * sin(k1 * a + p1 + frac * 1.35)
                                 + a2 * sin(k2 * a + p2 - frac * 0.9));
      const r = radius * warp;
      pts.push([cx + r * cos(a), cy + r * sin(a) * squash]);
    }
    return pts;
  };

  const bandRadius = (frac) => 268.0 - (268.0 - 46.0) * Math.pow(frac, 1.1);

  const art = [`<g transform="rotate(${n(rot)} 256 256)">`];
  for (let i = 0; i < bands; i++) {
    const frac = i / (bands - 1);
    const fill = mix(low, high, Math.pow(frac, 0.85));
    art.push(`<path d="${poly(ring(bandRadius(frac), frac))}" fill="${fill}"/>`);
  }
  // Index contours: the heavier every-third line a topo sheet labels.
  if (target !== 42) {
    for (let i = 0; i < bands; i++) {
      if (i % 3 !== 1) continue;
      const frac = i / (bands - 1);
      art.push(`<path d="${poly(ring(bandRadius(frac), frac))}" fill="none" stroke="${accent}" `
        + `stroke-width="${n(strokeFor(target, 4.4))}" opacity=".5"/>`);
    }
    const hair = target === 96 ? 4 : 9;
    for (let i = 0; i < hair; i++) {
      const frac = (i + 0.5) / hair;
      art.push(`<path d="${poly(ring(bandRadius(frac) + 8.0, frac, 1.06))}" fill="none" `
        + `stroke="${accent}" stroke-width="${n(strokeFor(target, 2.0))}" opacity=".3"/>`);
    }
  }
  art.push('</g>');
  // The drainage the basin sheds through, drawn in disc space so it always shows.
  if (target === 220) {
    const pts = [];
    for (let i = 0; i < 9; i++) {
      const t = i / 8.0;
      const r = 24.0 + t * 196.0;
      const a = creekA + 0.22 * sin(t * 2.6 + p1);
      pts.push(pt(r, a, C + offX * 0.6, C + offY * 0.6));
    }
    art.push(`<path d="${poly(pts, false)}" fill="none" stroke="${mix(base, '#ffffff', 0.66)}" `
      + `stroke-width="${n(strokeFor(target, 5))}" opacity=".55" stroke-linecap="round"/>`);
  }

  let hx = C + offX + drift * cos(tilt);
  let hy = C + offY + drift * sin(tilt);
  [hx, hy] = pt(hypot(hx - C, hy - C), atan2(hy - C, hx - C) + radians(rot));
  const ink = mix(base, '#ffffff', 0.92);
  const stamp = [];
  if (target === 42) {
    stamp.push(`<circle cx="${n(hx)}" cy="${n(hy)}" r="20" fill="${ink}"/>`);
    stamp.push(`<circle cx="${n(hx)}" cy="${n(hy)}" r="8" fill="${high}"/>`);
  } else {
    const size = target === 96 ? 16.0 : 19.0;
    stamp.push(`<path d="${poly([[hx, hy - size], [hx + size * 0.95, hy + size * 0.74], [hx - size * 0.95, hy + size * 0.74]])}" `
      + `fill="${ink}" stroke="${high}" stroke-width="${n(strokeFor(target, 3))}"/>`);
    stamp.push(`<circle cx="${n(hx)}" cy="${n(hy + size * 0.3)}" r="${n(size * 0.2)}" fill="${high}"/>`);
  }

  const text = [_halo(hx + 28, hy + 9, String(elevation), 21, ink, high, target, { weight: 700 })];
  text.push(..._cartouche(label, base, accent, target));
  return _shell('cb', 'contour basin', target, label, base, accent, art, stamp, text);
}

// ------------------------------------------------------------- fairway-plat

/** One hole plated from above: rough, mown corridor, tee pad, basket. */
export function fairway_plat(seed, base, accent, target, label) {
  _check(base, accent, target);
  const rng = new PyRandom(seed);
  // --- identity, drawn once.
  const rot = rng.uniform(-56.0, 56.0);
  const dogleg = rng.random() < 0.5 ? 1.0 : -1.0;
  const bend = rng.uniform(60.0, 150.0);
  const wTee = rng.uniform(76.0, 104.0);
  const wGreen = rng.uniform(30.0, 46.0);
  const greenR = rng.uniform(44.0, 62.0);
  const holeNo = rng.randrange(1, 19);
  const par = rng.choice([3, 3, 3, 4]);
  const creek = rng.random() < 0.55;
  const treePhase = rng.uniform(0.0, TAU);
  const teeLen = rng.uniform(44.0, 62.0);
  const creekAt = rng.uniform(0.38, 0.66);

  const tee = [146.0, 366.0];
  const basket = [366.0, 146.0];
  const mid = [(tee[0] + basket[0]) / 2.0, (tee[1] + basket[1]) / 2.0];
  const ddx = basket[0] - tee[0];
  const ddy = basket[1] - tee[1];
  const length = hypot(ddx, ddy);
  const ctrl = [mid[0] + dogleg * bend * (-ddy / length), mid[1] + dogleg * bend * (ddx / length)];

  const bez = (t) => {
    const u = 1.0 - t;
    return [u * u * tee[0] + 2 * u * t * ctrl[0] + t * t * basket[0],
            u * u * tee[1] + 2 * u * t * ctrl[1] + t * t * basket[1]];
  };

  const tangent = (t) => {
    const u = 1.0 - t;
    const gx = 2 * u * (ctrl[0] - tee[0]) + 2 * t * (basket[0] - ctrl[0]);
    const gy = 2 * u * (ctrl[1] - tee[1]) + 2 * t * (basket[1] - ctrl[1]);
    const m = hypot(gx, gy) || 1.0;
    return [gx / m, gy / m];
  };

  const halfWidth = (t) => (wTee + (wGreen - wTee) * t) / 2.0 * (1.0 + 0.16 * sin(Math.PI * t));

  const offset = (t, k) => {
    const [px, py] = bez(t);
    const [gx, gy] = tangent(t);
    return [px - gy * k, py + gx * k];
  };

  const steps = target === 42 ? 18 : 34;
  const left = [];
  const right = [];
  for (let i = 0; i <= steps; i++) {
    left.push(offset(i / steps, halfWidth(i / steps)));
    right.push(offset(i / steps, -halfWidth(i / steps)));
  }
  const corridor = poly(left.concat(right.slice().reverse()));

  // Tone, not hue, carries the map: the mown corridor is lifted off `base` and
  // the rough is pushed down from it.
  const rough = mix(mix(base, accent, 0.30), '#000000', 0.30);
  const mown = mix(base, '#ffffff', 0.34);
  const green = mix(base, '#ffffff', 0.66);
  const edge = mix(mown, '#ffffff', 0.45);
  const canopy = mix(rough, '#000000', 0.44);
  const water = mix(rough, accent, 0.55);

  const art = [`<g transform="rotate(${n(rot)} 256 256)">`,
               `<rect x="-40" y="-40" width="592" height="592" fill="${rough}"/>`];
  // Tree line, planted along both shoulders of the corridor.
  if (target !== 42) {
    const spine = [];
    for (let i = 0; i < 17; i++) spine.push([bez(i / 16.0), halfWidth(i / 16.0)]);

    /** How far a candidate tree sits outside the mown corridor. */
    const clearance = (px, py) => {
      let worst = 1e9;
      for (const [[sx, sy], half] of spine) {
        const d = hypot(px - sx, py - sy) - half;
        if (d < worst) worst = d;
      }
      return worst;
    };

    // Shoulder line: trees crowding both edges of the corridor.
    const count = target === 96 ? 15 : 22;
    for (const side of [-1.0, 1.0]) {
      for (let i = 0; i < count; i++) {
        const t = (i + 0.25) / count;
        const phase = i * 2.3 + treePhase + (side > 0 ? 0.0 : 0.9);
        const k = side * (halfWidth(t) + 24.0 + 16.0 * sin(phase));
        const [tx, ty] = offset(t, k);
        if (hypot(tx - C, ty - C) > 236.0) continue;
        art.push(`<circle cx="${n(tx)}" cy="${n(ty)}" r="${n(8.0 + 6.0 * Math.abs(sin(phase * 1.3)))}" `
          + `fill="${canopy}" opacity=".8"/>`);
      }
    }
    // Woodland beyond the shoulders, on a jittered lattice, corridor kept clear.
    if (target === 220) {
      for (let gy = 0; gy < 9; gy++) {
        for (let gx = 0; gx < 9; gx++) {
          const phase = gx * 1.7 + gy * 2.9 + treePhase;
          const tx = 40.0 + gx * 54.0 + 16.0 * sin(phase);
          const ty = 40.0 + gy * 54.0 + 16.0 * cos(phase * 1.4);
          if (hypot(tx - C, ty - C) > 232.0 || clearance(tx, ty) < 34.0) continue;
          art.push(`<circle cx="${n(tx)}" cy="${n(ty)}" r="${n(7.0 + 5.0 * Math.abs(sin(phase)))}" `
            + `fill="${canopy}" opacity=".55"/>`);
        }
      }
    }
  }
  art.push(`<ellipse cx="${n(basket[0])}" cy="${n(basket[1])}" rx="${n(greenR)}" `
    + `ry="${n(greenR * 0.88)}" fill="${green}" opacity=".95" stroke="${edge}" stroke-width="${n(strokeFor(target, 3))}"/>`);
  art.push(`<path d="${corridor}" fill="${mown}"/>`);
  if (target === 220) {
    // Mowing stripes: the aerial giveaway that this corridor is maintained.
    for (const k of [-0.55, -0.18, 0.18, 0.55]) {
      const band = [];
      for (let i = 0; i < 15; i++) band.push(offset(i / 14.0, halfWidth(i / 14.0) * k));
      art.push(`<path d="${poly(band, false)}" fill="none" stroke="#ffffff" `
        + `stroke-width="${n(strokeFor(target, 9))}" opacity=".08"/>`);
    }
  }
  if (target !== 42) {
    art.push(`<path d="${corridor}" fill="none" stroke="${edge}" `
      + `stroke-width="${n(strokeFor(target, 3.4))}" opacity=".7"/>`);
  }
  if (target === 220 && creek) {
    const [px, py] = bez(creekAt);
    const [cgx, cgy] = tangent(creekAt);
    const pts = [];
    for (let i = 0; i < 15; i++) {
      const s = -300.0 + i * (600.0 / 14.0);
      const wob = 16.0 * sin(i * 0.85 + treePhase);
      pts.push([px - cgy * s + cgx * wob, py + cgx * s + cgy * wob]);
    }
    art.push(`<path d="${poly(pts, false)}" fill="none" stroke="${water}" `
      + `stroke-width="${n(strokeFor(target, 22))}" opacity=".9"/>`);
    art.push(`<path d="${poly(pts, false)}" fill="none" stroke="${edge}" `
      + `stroke-width="${n(strokeFor(target, 2.4))}" opacity=".55"/>`);
  }
  if (target !== 42) {
    const centre = [];
    for (let i = 0; i < 15; i++) centre.push(bez(i / 14.0));
    art.push(`<path d="${poly(centre, false)}" fill="none" stroke="${accent}" `
      + `stroke-width="${n(strokeFor(target, 4.6))}" opacity=".85" `
      + 'stroke-dasharray="18 13" stroke-linecap="round"/>');
  }
  const [gx0, gy0] = tangent(0.0);
  const ang = degrees(atan2(gy0, gx0));
  art.push(`<g transform="translate(${n(tee[0])} ${n(tee[1])}) rotate(${n(ang)})">`
    + `<rect x="${n(-teeLen * 0.5)}" y="-31" width="${n(teeLen)}" height="62" rx="7" fill="${accent}"/>`
    + `<rect x="${n(-teeLen * 0.5)}" y="-31" width="${n(teeLen)}" height="62" rx="7" fill="none" `
    + `stroke="${edge}" stroke-width="${n(strokeFor(target, 3))}" opacity=".8"/></g>`);
  art.push('</g>');

  const [bx, by] = pt(hypot(basket[0] - C, basket[1] - C),
                      atan2(basket[1] - C, basket[0] - C) + radians(rot));
  const stamp = [];
  if (target === 42) {
    stamp.push(`<circle cx="${n(bx)}" cy="${n(by)}" r="32" fill="${accent}"/>`);
    stamp.push(`<circle cx="${n(bx)}" cy="${n(by)}" r="14" fill="${mix(base, '#ffffff', 0.72)}"/>`);
  } else {
    stamp.push(`<circle cx="${n(bx)}" cy="${n(by)}" r="${target === 96 ? 27 : 31}" fill="none" `
      + `stroke="${accent}" stroke-width="${n(strokeFor(target, 10))}"/>`);
    stamp.push(`<circle cx="${n(bx)}" cy="${n(by)}" r="${target === 96 ? 10 : 12}" fill="${accent}"/>`);
    if (target === 220) {
      stamp.push(`<path d="M${n(bx)} ${n(by - 31)} v-24" stroke="${accent}" `
        + `stroke-width="${n(strokeFor(target, 7))}" stroke-linecap="round"/>`);
    }
  }

  const ink = mix(base, '#ffffff', 0.94);
  const text = [
    _halo(96, 154, String(holeNo), 62, ink, mix(base, accent, 0.8), target, { weight: 700, family: 'serif' }),
    _halo(98, 180, `PAR ${par}`, 18, ink, mix(base, accent, 0.8), target, { spacing: 2.2 }),
  ];
  text.push(..._cartouche(label, base, accent, target));
  return _shell('fp', 'fairway plat', target, label, base, accent, art, stamp, text);
}

// ----------------------------------------------------------------- wind-rose

/** The bearing compass off the corner of the sheet: a rose of wind spikes. */
export function wind_rose(seed, base, accent, target, label) {
  _check(base, accent, target);
  const rng = new PyRandom(seed);
  // --- identity, drawn once.
  const prevail = rng.uniform(0.0, TAU);
  const tilt = rng.uniform(-0.20, 0.20);
  const focus = rng.uniform(1.3, 3.0);
  const hub = rng.uniform(24.0, 38.0);
  const kite = rng.uniform(0.34, 0.56);
  const petals = [];
  for (let i = 0; i < 16; i++) petals.push(rng.uniform(0.38, 1.0));
  const bearing = rng.randrange(0, 360);
  const ringGap = rng.uniform(4.0, 16.0);

  const dark = luma(base) < 0.42;
  const field = mix(base, accent, dark ? 0.14 : 0.20);
  const pale = mix(base, '#ffffff', dark ? 0.86 : 0.80);
  const ink = accent;
  const ringR = 182.0 - ringGap;
  const arms = target === 42 ? 8 : 16;
  const step = Math.floor(16 / arms);

  const art = [`<circle cx="256" cy="256" r="${R}" fill="${field}"/>`];
  if (target === 220) {
    for (let i = 0; i < 16; i++) {
      const a = i * TAU / 16 + tilt;
      const [x0, y0] = pt(hub, a);
      const [x1, y1] = pt(ringR, a);
      art.push(`<path d="M${n(x0)} ${n(y0)} L${n(x1)} ${n(y1)}" stroke="${ink}" `
        + `stroke-width="${n(strokeFor(target, 1.6))}" opacity=".22"/>`);
    }
  }
  if (target !== 42) {
    for (const radius of [ringR, 112.0]) {
      art.push(`<circle cx="256" cy="256" r="${n(radius)}" fill="none" stroke="${ink}" `
        + `stroke-width="${n(strokeFor(target, 2.6))}" opacity=".45"/>`);
    }
  }
  if (target === 220) {
    for (let i = 0; i < 72; i++) {
      const a = i * TAU / 72 + tilt;
      const major = i % 6 === 0;
      const [x0, y0] = pt(ringR, a);
      const [x1, y1] = pt(ringR + (major ? 18.0 : 9.0), a);
      art.push(`<path d="M${n(x0)} ${n(y0)} L${n(x1)} ${n(y1)}" stroke="${ink}" `
        + `stroke-width="${n(strokeFor(target, major ? 5.5 : 2.4))}" `
        + `opacity="${major ? '.8' : '.45'}"/>`);
    }
  } else if (target === 96) {
    for (let i = 0; i < 16; i++) {
      const a = i * TAU / 16 + tilt;
      const [x0, y0] = pt(ringR, a);
      const [x1, y1] = pt(ringR + 15.0, a);
      art.push(`<path d="M${n(x0)} ${n(y0)} L${n(x1)} ${n(y1)}" stroke="${ink}" `
        + `stroke-width="${n(strokeFor(target, 5))}" opacity=".6"/>`);
    }
  }

  const reach = [];
  for (let i = 0; i < 16; i++) {
    const a = i * TAU / 16 + tilt;
    const bias = (cos(a - prevail) + 1.0) / 2.0;
    reach.push(62.0 + 112.0 * petals[i] * (0.42 + 0.58 * Math.pow(bias, focus)));
  }
  // Kite half-width is set in viewBox units, not in radians.
  const kw = (target === 42 ? 30.0 : 17.0) * (0.7 + kite);
  for (let j = 0; j < arms; j++) {
    const i = j * step;
    const a = i * TAU / 16 + tilt;
    const ux = cos(a);
    const uy = sin(a);
    const px = -uy;
    const py = ux;
    const tip = [C + ux * reach[i], C + uy * reach[i]];
    const lft = [C + ux * hub + px * kw, C + uy * hub + py * kw];
    const rgt = [C + ux * hub - px * kw, C + uy * hub - py * kw];
    if (i % 2 === 0) {
      art.push(`<path d="${poly([tip, lft, [C, C], rgt])}" fill="${ink}" opacity=".95"/>`);
    } else {
      art.push(`<path d="${poly([tip, lft, [C, C], rgt])}" fill="${pale}" opacity=".92" `
        + `stroke="${ink}" stroke-width="${n(strokeFor(target, 2.4))}"/>`);
    }
  }
  // The prevailing needle: one long folded blade out to the bearing ring.
  const ux = cos(prevail);
  const uy = sin(prevail);
  const px = -uy;
  const py = ux;
  const nw = target === 42 ? 30.0 : 21.0;
  const tip = [C + ux * (ringR - 8.0), C + uy * (ringR - 8.0)];
  const midR = hub * 1.15;
  const lft = [C + ux * midR + px * nw, C + uy * midR + py * nw];
  const rgt = [C + ux * midR - px * nw, C + uy * midR - py * nw];
  const tail = [C - ux * hub * 0.9, C - uy * hub * 0.9];
  art.push(`<path d="${poly([tip, lft, tail, rgt])}" fill="${pale}" `
    + `stroke="${ink}" stroke-width="${n(strokeFor(target, 3))}"/>`);
  art.push(`<path d="${poly([tip, lft, tail])}" fill="${ink}"/>`);

  const stamp = [];
  const hubR = target === 42 ? 24.0 : (target === 96 ? 19.0 : 21.0);
  stamp.push(`<circle cx="256" cy="256" r="${n(hubR)}" fill="${pale}" stroke="${ink}" `
    + `stroke-width="${n(strokeFor(target, 7))}"/>`);
  if (target !== 42) {
    stamp.push(`<circle cx="256" cy="256" r="${n(hubR * 0.36)}" fill="${ink}"/>`);
  }

  const nx = C + ux * (ringR - 40.0) + px * 30.0;
  const ny = C + uy * (ringR - 40.0) + py * 30.0;
  const text = [
    _halo(nx, ny + 10, 'N', 30, mix(base, '#ffffff', 0.94), ink, target,
          { anchor: 'middle', weight: 700, family: 'serif' }),
    _halo(256, 106, `${String(bearing).padStart(3, '0')}°`, 19, mix(base, '#ffffff', 0.9), ink, target,
          { anchor: 'middle', spacing: 2.0 }),
  ];
  text.push(..._cartouche(label, base, accent, target));
  return _shell('wr', 'wind rose', target, label, base, accent, art, stamp, text);
}

export const RENDERERS = {
  'contour-basin': contour_basin,
  'fairway-plat': fairway_plat,
  'wind-rose': wind_rose,
};
