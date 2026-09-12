// core.mjs -- the Python runtime the painter port depends on, reproduced exactly.
//
// Dependency-free ES module. Runs under Node 22 and in a browser; no DOM, no npm.
//
// Three things live here:
//   * PyRandom          -- CPython's random.Random for an integer seed (MT19937,
//                          init_by_array seeding, genrand_res53, uniform,
//                          randrange/randint, choice, shuffle, sample).
//   * number formatting -- fmt/fmt1/fmt2 for Python's f"{x:.Nf}", pyRound for
//                          round(x, n), pyStr for str()/repr() of a float. All of
//                          them round the *exact binary value* half-to-even, which
//                          is what CPython does and what Number#toFixed does not.
//   * frame helpers     -- the constants and shared geometry of paint_components.py
//                          plus html.escape(text, quote=True).

// --------------------------------------------------------------- MT19937

const N = 624;
const M = 397;
const MATRIX_A = 0x9908b0df;
const UPPER_MASK = 0x80000000;
const LOWER_MASK = 0x7fffffff;

/** CPython's `random.Random(seed)` for an integer seed. */
export class PyRandom {
  constructor(seed = 0) {
    this.mt = new Uint32Array(N);
    this.mti = N + 1;
    this.seed(seed);
  }

  /** random_seed(): key the twister with the 32-bit chunks of abs(seed). */
  seed(seed) {
    let n = typeof seed === 'bigint' ? seed : BigInt(Math.trunc(Number(seed)));
    if (n < 0n) n = -n;
    const key = [];
    if (n === 0n) key.push(0);
    while (n > 0n) {
      key.push(Number(n & 0xffffffffn) >>> 0);
      n >>= 32n;
    }
    this.initByArray(key);
  }

  initGenrand(s) {
    const mt = this.mt;
    mt[0] = s >>> 0;
    for (let i = 1; i < N; i++) {
      const prev = mt[i - 1] ^ (mt[i - 1] >>> 30);
      mt[i] = (Math.imul(1812433253, prev) + i) >>> 0;
    }
    this.mti = N;
  }

  initByArray(key) {
    this.initGenrand(19650218);
    const mt = this.mt;
    const keyLength = key.length;
    let i = 1;
    let j = 0;
    for (let k = Math.max(N, keyLength); k > 0; k--) {
      const prev = mt[i - 1] ^ (mt[i - 1] >>> 30);
      mt[i] = (((mt[i] ^ Math.imul(prev, 1664525)) >>> 0) + key[j] + j) >>> 0;
      i++;
      j++;
      if (i >= N) { mt[0] = mt[N - 1]; i = 1; }
      if (j >= keyLength) j = 0;
    }
    for (let k = N - 1; k > 0; k--) {
      const prev = mt[i - 1] ^ (mt[i - 1] >>> 30);
      mt[i] = (((mt[i] ^ Math.imul(prev, 1566083941)) >>> 0) - i) >>> 0;
      i++;
      if (i >= N) { mt[0] = mt[N - 1]; i = 1; }
    }
    mt[0] = 0x80000000;
    this.mti = N;
  }

  /** genrand_uint32(): one tempered 32-bit draw. */
  genrandUint32() {
    const mt = this.mt;
    if (this.mti >= N) {
      let kk = 0;
      for (; kk < N - M; kk++) {
        const y = (mt[kk] & UPPER_MASK) | (mt[kk + 1] & LOWER_MASK);
        mt[kk] = (mt[kk + M] ^ (y >>> 1) ^ ((y & 1) ? MATRIX_A : 0)) >>> 0;
      }
      for (; kk < N - 1; kk++) {
        const y = (mt[kk] & UPPER_MASK) | (mt[kk + 1] & LOWER_MASK);
        mt[kk] = (mt[kk + (M - N)] ^ (y >>> 1) ^ ((y & 1) ? MATRIX_A : 0)) >>> 0;
      }
      const y = (mt[N - 1] & UPPER_MASK) | (mt[0] & LOWER_MASK);
      mt[N - 1] = (mt[M - 1] ^ (y >>> 1) ^ ((y & 1) ? MATRIX_A : 0)) >>> 0;
      this.mti = 0;
    }
    let y = mt[this.mti++];
    y ^= y >>> 11;
    y = (y ^ ((y << 7) & 0x9d2c5680)) >>> 0;
    y = (y ^ ((y << 15) & 0xefc60000)) >>> 0;
    y ^= y >>> 18;
    return y >>> 0;
  }

  /** genrand_res53(): a 53-bit float in [0, 1) from two 32-bit draws. */
  random() {
    const a = this.genrandUint32() >>> 5;
    const b = this.genrandUint32() >>> 6;
    return (a * 67108864.0 + b) * (1.0 / 9007199254740992.0);
  }

  /** getrandbits(k): k random bits, little-endian by 32-bit word. */
  getrandbits(k) {
    k = Math.trunc(k);
    if (k < 0) throw new Error('number of bits must be non-negative');
    if (k === 0) return 0n;
    if (k <= 32) return BigInt(this.genrandUint32() >>> (32 - k));
    let result = 0n;
    let shift = 0n;
    let left = k;
    while (left > 0) {
      let r = this.genrandUint32();
      if (left < 32) r = r >>> (32 - left);
      result |= BigInt(r >>> 0) << shift;
      shift += 32n;
      left -= 32;
    }
    return result;
  }

  /** _randbelow_with_getrandbits(n): rejection sampling on n.bit_length() bits. */
  _randbelow(n) {
    const big = typeof n === 'bigint' ? n : BigInt(Math.trunc(n));
    if (big <= 0n) return 0;
    const k = big.toString(2).length;
    let r = this.getrandbits(k);
    while (r >= big) r = this.getrandbits(k);
    return Number(r);
  }

  /** uniform(a, b) == a + (b - a) * random(). */
  uniform(a, b) {
    return a + (b - a) * this.random();
  }

  /** randrange(stop) / randrange(start, stop[, step]). */
  randrange(start, stop, step = 1) {
    const istart = Math.trunc(start);
    if (stop === undefined) {
      if (istart > 0) return this._randbelow(istart);
      throw new Error(`empty range for randrange(${start})`);
    }
    const istop = Math.trunc(stop);
    const width = istop - istart;
    const istep = Math.trunc(step);
    if (istep === 1) {
      if (width > 0) return istart + this._randbelow(width);
      throw new Error(`empty range in randrange(${start}, ${stop})`);
    }
    let n;
    if (istep > 0) n = Math.floor((width + istep - 1) / istep);
    else if (istep < 0) n = Math.floor((width + istep + 1) / istep);
    else throw new Error('zero step for randrange()');
    if (n <= 0) throw new Error('empty range for randrange()');
    return istart + istep * this._randbelow(n);
  }

  /** randint(a, b) == randrange(a, b + 1). */
  randint(a, b) {
    return this.randrange(a, b + 1);
  }

  /** choice(seq) == seq[_randbelow(len(seq))]. */
  choice(seq) {
    if (seq.length === 0) throw new Error('Cannot choose from an empty sequence');
    return seq[this._randbelow(seq.length)];
  }

  /** shuffle(x): CPython's in-place Fisher-Yates, downward from len(x) - 1. */
  shuffle(x) {
    for (let i = x.length - 1; i > 0; i--) {
      const j = this._randbelow(i + 1);
      const tmp = x[i];
      x[i] = x[j];
      x[j] = tmp;
    }
    return x;
  }

  /** sample(population, k): CPython's selection-set / pool algorithm. */
  sample(population, k) {
    const pop = Array.from(population);
    const n = pop.length;
    if (!(k >= 0 && k <= n)) throw new Error('Sample larger than population or is negative');
    const result = new Array(k);
    let setsize = 21;
    if (k > 5) setsize += Math.pow(4, Math.ceil(Math.log(k * 3) / Math.log(4)));
    if (n <= setsize) {
      const pool = pop.slice();
      for (let i = 0; i < k; i++) {
        const j = this._randbelow(n - i);
        result[i] = pool[j];
        pool[j] = pool[n - i - 1];
      }
    } else {
      const selected = new Set();
      for (let i = 0; i < k; i++) {
        let j = this._randbelow(n);
        while (selected.has(j)) j = this._randbelow(n);
        selected.add(j);
        result[i] = pop[j];
      }
    }
    return result;
  }
}

// ---------------------------------------------------- exact float formatting
//
// CPython formats and rounds the *exact* binary value of the double and breaks
// true ties to even. `(0.25).toFixed(1)` is "0.3" in JS and "0.2" in Python, so
// none of this may go through toFixed. Everything below expands the double
// exactly (as m * 2**e over BigInt) and rounds that expansion.

const _view = new DataView(new ArrayBuffer(8));

/** Split a finite double into {neg, mant, exp} with |x| == mant * 2**exp. */
function decompose(x) {
  _view.setFloat64(0, x);
  const bits = _view.getBigUint64(0);
  const neg = (bits >> 63n) === 1n;
  const be = Number((bits >> 52n) & 0x7ffn);
  const frac = bits & 0xfffffffffffffn;
  if (be === 0) return { neg, mant: frac, exp: -1074 };
  return { neg, mant: frac | 0x10000000000000n, exp: be - 1075 };
}

/** |x| * 10**digits, rounded half-to-even, as a BigInt. */
function scaled(mant, exp, digits) {
  let num = mant * 10n ** BigInt(digits);
  if (exp >= 0) return num << BigInt(exp);
  const shift = BigInt(-exp);
  const q = num >> shift;
  const rem = num - (q << shift);
  const half = 1n << (shift - 1n);
  if (rem > half || (rem === half && (q & 1n) === 1n)) return q + 1n;
  return q;
}

/** Python's f"{x:.<digits>f}". Ties on the binary value go to even. */
export function fmt(x, digits) {
  if (Number.isNaN(x)) return 'nan';
  if (!Number.isFinite(x)) return x > 0 ? 'inf' : '-inf';
  const { neg, mant, exp } = decompose(x);
  const n = scaled(mant, exp, digits);
  let s = n.toString();
  if (digits > 0) {
    if (s.length <= digits) s = s.padStart(digits + 1, '0');
    s = s.slice(0, s.length - digits) + '.' + s.slice(s.length - digits);
  }
  return (neg ? '-' : '') + s;
}

/** Python's f"{x:.1f}". */
export function fmt1(x) { return fmt(x, 1); }

/** Python's f"{x:.2f}". */
export function fmt2(x) { return fmt(x, 2); }

/** Python's f"{x:.3f}". */
export function fmt3(x) { return fmt(x, 3); }

/** Python's round(x, n): correctly rounded on the binary value, half to even. */
export function pyRound(x, n = 0) {
  if (!Number.isFinite(x)) return x;
  const text = fmt(x, Math.max(0, Math.trunc(n)));
  const value = Number(text);
  // Python keeps the sign of the argument, so round(-0.04, 1) is -0.0.
  if (value === 0) return x < 0 || Object.is(x, -0) ? -0 : 0;
  return value;
}

/** Python's round(x) with no second argument: half to even, and an int. */
export function pyRoundInt(x) {
  if (!Number.isFinite(x)) throw new Error('cannot convert to an integer');
  const { neg, mant, exp } = decompose(x);
  const n = Number(scaled(mant, exp, 0));
  return neg && n !== 0 ? -n : n;   // Python's int zero has no sign
}

/**
 * Python's `a % b`. JS's % is C's fmod: it takes the sign of the dividend, while
 * Python's takes the sign of the divisor, so -0.3 % 1 is 0.7 in Python and -0.3
 * in JS. Correct for ints and floats alike.
 */
export function pyMod(a, b) {
  const m = a % b;
  if (m !== 0) return (b < 0) !== (m < 0) ? m + b : m;
  return b < 0 ? -0 : 0;
}

/** Python's `a // b`, floor division, following CPython's float_floor_div. */
export function pyFloorDiv(a, b) {
  const mod = a % b;
  let div = (a - mod) / b;
  if (mod !== 0 && (b < 0) !== (mod < 0)) div -= 1.0;
  if (div === 0) {
    // CPython signs an exact-zero quotient from a / b, not from the subtraction.
    const q = a / b;
    return (q < 0 || Object.is(q, -0)) ? -0 : 0;
  }
  let floordiv = Math.floor(div);
  if (div - floordiv > 0.5) floordiv += 1.0;
  return floordiv;
}

/** Python's repr()/str() of a float. */
export function pyStr(x) {
  if (typeof x !== 'number') return String(x);
  if (Number.isNaN(x)) return 'nan';
  if (x === Infinity) return 'inf';
  if (x === -Infinity) return '-inf';
  if (!Number.isInteger(x) || Math.abs(x) >= 1e16) {
    // JS and Python both print the shortest round-tripping decimal; they differ
    // only in when they switch to exponent form and in how they spell it.
    const js = String(x);
    if (!js.includes('e')) {
      const exp = Math.floor(Math.log10(Math.abs(x)));
      if (exp >= 16 || exp < -4) return expForm(x);
      return js;
    }
    return expForm(x);
  }
  const body = Object.is(x, -0) ? '-0' : String(x);
  return body + '.0';
}

function expForm(x) {
  // Python spells the exponent with a sign and at least two digits, and -- unlike
  // its fixed notation -- it does not pad a bare mantissa with ".0": repr(1e-05)
  // is '1e-05', not '1.0e-05'.
  const [m, e] = x.toExponential().split('e');
  const sign = e[0] === '-' ? '-' : '+';
  let digits = e.replace(/^[-+]/, '');
  if (digits.length < 2) digits = '0' + digits;
  return `${m}e${sign}${digits}`;
}

/** Python's str() of a value that may be an int or a float, as f-strings print it. */
export function pyNum(x) {
  return Number.isInteger(x) && !Object.is(x, -0) ? String(x) : pyStr(x);
}

// ------------------------------------------------------- correctly rounded math
//
// Math.sqrt is IEEE-exact everywhere, but V8's Math.hypot is not: it disagrees
// with glibc (what CPython's math.hypot calls) on roughly a third of random
// pairs, by one unit in the last place. That is enough to flip a comparison like
// `math.hypot(x - C, y - C) > 244`, so hypot is computed exactly here: the sum
// of squares is an exact integer over BigInt and its square root is rounded once,
// to nearest, ties to even -- which is what glibc returns.

function isqrt(n) {
  if (n < 2n) return n;
  let x = 1n << BigInt(Math.ceil(n.toString(2).length / 2));
  for (;;) {
    const y = (x + n / x) >> 1n;
    if (y >= x) return x;
    x = y;
  }
}

/** The double nearest to q * 2**exp (+ a positive tail when `exact` is false). */
function roundBits(q, exact, exp) {
  if (q === 0n) return 0;
  const nbits = q.toString(2).length;
  const drop = nbits - 53;
  let m = q;
  let e = exp;
  if (drop > 0) {
    const shift = BigInt(drop);
    const hi = q >> shift;
    const rem = q - (hi << shift);
    const half = 1n << (shift - 1n);
    const up = rem > half || (rem === half && (!exact || (hi & 1n) === 1n));
    m = up ? hi + 1n : hi;
    e = exp + drop;
  }
  // Two-step scaling keeps the intermediate inside the double range.
  const half1 = Math.floor(e / 2);
  return Number(m) * Math.pow(2, half1) * Math.pow(2, e - half1);
}

/** Python's math.hypot(x, y), correctly rounded. */
export function hypot(x, y) {
  if (Number.isNaN(x) || Number.isNaN(y)) {
    return (Math.abs(x) === Infinity || Math.abs(y) === Infinity) ? Infinity : NaN;
  }
  if (Math.abs(x) === Infinity || Math.abs(y) === Infinity) return Infinity;
  if (x === 0) return Math.abs(y);
  if (y === 0) return Math.abs(x);
  const a = decompose(x);
  const b = decompose(y);
  const ea = 2 * a.exp;
  const eb = 2 * b.exp;
  let e = Math.min(ea, eb);
  let s = ((a.mant * a.mant) << BigInt(ea - e)) + ((b.mant * b.mant) << BigInt(eb - e));
  if (e % 2 !== 0) { s <<= 1n; e -= 1; }
  // Give the root a comfortable 60+ bits before rounding it to 53.
  const bits = s.toString(2).length;
  let k = 0;
  if (bits < 128) { k = Math.ceil((128 - bits) / 2); s <<= BigInt(2 * k); }
  const q = isqrt(s);
  return roundBits(q, q * q === s, e / 2 - k);
}

// V8's Math.atan2 is off by one ulp from glibc on about 5% of arguments, and
// glibc -- what CPython's math.atan2 calls -- was correctly rounded on every
// sample tested here. So atan2 is evaluated in fixed point at 128 fractional
// bits (argument halving, then the Taylor series) and rounded once at the end.

const FX = 128;                       // fractional bits of the working format
const FX_ONE = 1n << BigInt(FX);
const fxMul = (a, b) => (a * b) >> BigInt(FX);
const fxDiv = (a, b) => (a << BigInt(FX)) / b;
const fxSqrt = (a) => isqrt(a << BigInt(FX));

/** atan(1/n) in fixed point, by the alternating series -- used to build pi. */
function fxAtanReciprocal(n) {
  const N = BigInt(n);
  const N2 = N * N;
  let term = FX_ONE / N;
  let sum = 0n;
  let k = 1n;
  let sign = 1n;
  while (term !== 0n) {
    sum += sign * (term / k);
    term /= N2;
    k += 2n;
    sign = -sign;
  }
  return sum;
}

// Machin: pi/4 = 4*atan(1/5) - atan(1/239).
const FX_PI = 4n * (4n * fxAtanReciprocal(5) - fxAtanReciprocal(239));
const FX_PI_2 = FX_PI / 2n;

/** atan(t) in fixed point for t >= 0, halving the argument before the series. */
function fxAtan(t) {
  let halvings = 0;
  const small = FX_ONE >> 5n;
  while (t > small) {
    // t <- t / (1 + sqrt(1 + t*t))
    t = fxDiv(t, FX_ONE + fxSqrt(FX_ONE + fxMul(t, t)));
    halvings++;
  }
  const tsq = fxMul(t, t);
  let power = t;
  let sum = t;
  let k = 3n;
  let sign = -1n;
  for (;;) {
    power = fxMul(power, tsq);
    const piece = power / k;
    if (piece === 0n) break;
    sum += sign * piece;
    sign = -sign;
    k += 2n;
  }
  return sum << BigInt(halvings);
}

/** Python's math.atan2(y, x), correctly rounded. */
export function atan2(y, x) {
  if (Number.isNaN(x) || Number.isNaN(y)) return NaN;
  const yInf = Math.abs(y) === Infinity;
  const xInf = Math.abs(x) === Infinity;
  if (yInf || xInf || y === 0 || x === 0) {
    // The special cases are exactly Math.atan2's: multiples of pi/4 and 0.
    return Math.atan2(y, x);
  }
  const ay = decompose(Math.abs(y));
  const ax = decompose(Math.abs(x));
  // |y| / |x| in fixed point, from the exact integer significands.
  const shift = FX + ay.exp - ax.exp;
  const num = shift >= 0 ? ay.mant << BigInt(shift) : ay.mant;
  const den = shift >= 0 ? ax.mant : ax.mant << BigInt(-shift);
  const t = num / den;
  let q = t > FX_ONE ? FX_PI_2 - fxAtan(fxDiv(FX_ONE, t)) : fxAtan(t);
  if (x < 0) q = FX_PI - q;
  const magnitude = roundBits(q, false, -FX);
  return (y < 0 || Object.is(y, -0)) ? -magnitude : magnitude;
}

// The same treatment for sine and cosine, which the families lean on hardest.
// V8 disagrees with glibc on about 3.5% of arguments; evaluating them in fixed
// point (Payne-Hanek-style reduction by pi/2, then the Taylor series) leaves a
// residual of about 0.2%, which is glibc's own departure from correct rounding.

/** sin and cos of a fixed-point angle in [0, pi/4]. */
function fxSinCosSmall(a) {
  const asq = fxMul(a, a);
  let term = a;
  let sinv = a;
  let sign = -1n;
  let k = 2n;
  for (;;) {
    term = fxMul(term, asq) / (k * (k + 1n));
    if (term === 0n) break;
    sinv += sign * term;
    sign = -sign;
    k += 2n;
  }
  let cterm = FX_ONE;
  let cosv = FX_ONE;
  let csign = -1n;
  let m = 1n;
  for (;;) {
    cterm = fxMul(cterm, asq) / (m * (m + 1n));
    if (cterm === 0n) break;
    cosv += csign * cterm;
    csign = -csign;
    m += 2n;
  }
  return [sinv, cosv];
}

/** [sin |x|, cos |x|] in fixed point, or null when |x| is too small to reduce. */
function fxSinCos(x) {
  const { mant, exp } = decompose(x);
  const shift = FX + exp;
  if (shift < 0) return null;
  const xf = mant << BigInt(shift);
  const n = (2n * xf + FX_PI_2) / (2n * FX_PI_2);   // nearest multiple of pi/2
  const r = xf - n * FX_PI_2;
  const negative = r < 0n;
  const [s, c] = fxSinCosSmall(negative ? -r : r);
  const sr = negative ? -s : s;
  const quadrant = Number(n % 4n);
  if (quadrant === 0) return [sr, c];
  if (quadrant === 1) return [c, -sr];
  if (quadrant === 2) return [-sr, -c];
  return [-c, sr];
}

function fxToDouble(v) {
  return v < 0n ? -roundBits(-v, false, -FX) : roundBits(v, false, -FX);
}

/** Python's math.sin(x). */
export function sin(x) {
  if (!Number.isFinite(x)) return Math.sin(x);
  const pair = fxSinCos(Math.abs(x));
  if (pair === null) return Math.sin(x);
  const value = fxToDouble(pair[0]);
  return x < 0 ? -value : value;
}

/** Python's math.cos(x). */
export function cos(x) {
  if (!Number.isFinite(x)) return Math.cos(x);
  const pair = fxSinCos(Math.abs(x));
  if (pair === null) return Math.cos(x);
  return fxToDouble(pair[1]);
}

// ------------------------------------------------------------------ escaping

/** html.escape(text, quote=True). */
export function escape(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

// ------------------------------------------------- the shared painter frame
//
// paint_components.py: a 512-unit viewBox, a disc clip at r220, the two rim
// rings, the stroke floor, and the label at 220 only.

export const SIZE = 512;
export const C = 256;
export const R = 220;
export const TARGETS = [42, 96, 220];
export const TAU = Math.PI * 2;
export const HEX = /^#[0-9a-fA-F]{6}$/;

/** math.degrees(x) -- CPython multiplies by a precomputed 180/pi. */
const RAD_TO_DEG = 180.0 / Math.PI;
export function degrees(x) { return x * RAD_TO_DEG; }
export function radians(x) { return x * (Math.PI / 180.0); }

/**
 * A point on a circle: paint_components.xy, and the studios' xy(radius, angle,
 * cx=C, cy=C), which is the same function with the centre spelled out.
 */
export function xy(radius, angle, cx = C, cy = C) {
  return [cx + radius * cos(angle), cy + radius * sin(angle)];
}

/** The 512-unit stroke width that lands on `minOutput` device px at `target`. */
export function strokeFloor(target, minOutput = 1.0) {
  return pyRound(minOutput / (target / SIZE), 1);
}

/**
 * paint_components' `stroke` lambda, printed the way the f-string prints it:
 * `max(source, round(min_output / scale, 1))`, where an int source stays an int.
 */
export function strokeText(source, target, minOutput = 1.0) {
  const floor = strokeFloor(target, minOutput);
  return floor > source ? pyNum(floor) : pyNum(source);
}

/** Python's `min(max(...))`-free clamp on hex validation, as paint_components does it. */
export function checkHex(value) {
  if (!HEX.test(value)) throw new Error('use a six-digit hex color');
  return value.toLowerCase();
}
