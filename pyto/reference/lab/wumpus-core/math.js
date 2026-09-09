/**
 * Small, side-effect-free geometry and collection primitives used by the core.
 * Coordinates are integer grid cells; x grows right and y grows down.
 */

function assertInteger(value, name) {
  if (!Number.isInteger(value)) {
    throw new TypeError(`${name} must be an integer`);
  }
}

function assertPoint(value, name = 'point') {
  if (!value || typeof value !== 'object' || !Number.isInteger(value.x) || !Number.isInteger(value.y)) {
    throw new TypeError(`${name} must have integer x and y properties`);
  }
}

/** Return an immutable integer grid point. */
export function point(x, y) {
  assertInteger(x, 'x');
  assertInteger(y, 'y');
  return Object.freeze({ x, y });
}

/** Return whether value is an integer grid point. */
export function isPoint(value) {
  return Boolean(value && typeof value === 'object' && Number.isInteger(value.x) && Number.isInteger(value.y));
}

/** Add two grid points without mutating either input. */
export function addPoints(first, second) {
  assertPoint(first, 'first');
  assertPoint(second, 'second');
  return point(first.x + second.x, first.y + second.y);
}

/** Manhattan distance between two grid points. */
export function manhattanDistance(first, second) {
  assertPoint(first, 'first');
  assertPoint(second, 'second');
  return Math.abs(first.x - second.x) + Math.abs(first.y - second.y);
}

/**
 * Return cardinal neighbors in stable north, east, south, west order.
 * If bounds are supplied, only cells in [0,width) × [0,height) are returned.
 */
export function neighbors(origin, bounds) {
  assertPoint(origin, 'origin');
  if (bounds !== undefined) {
    if (!bounds || !Number.isInteger(bounds.width) || !Number.isInteger(bounds.height) || bounds.width < 0 || bounds.height < 0) {
      throw new TypeError('bounds must have non-negative integer width and height');
    }
  }
  const candidates = [
    point(origin.x, origin.y - 1),
    point(origin.x + 1, origin.y),
    point(origin.x, origin.y + 1),
    point(origin.x - 1, origin.y),
  ];
  if (bounds === undefined) return candidates;
  return candidates.filter(({ x, y }) => x >= 0 && x < bounds.width && y >= 0 && y < bounds.height);
}

/**
 * Set intersection for iterables. Results are unique, preserve the first
 * iterable's order, and use SameValueZero equality (the semantics of Set).
 */
export function intersection(first, second) {
  if (first == null || second == null || typeof first[Symbol.iterator] !== 'function' || typeof second[Symbol.iterator] !== 'function') {
    throw new TypeError('intersection expects two iterables');
  }
  const right = new Set(second);
  const result = [];
  const seen = new Set();
  for (const value of first) {
    if (right.has(value) && !seen.has(value)) {
      seen.add(value);
      result.push(value);
    }
  }
  return Object.freeze(result);
}

function assertRectangle(rectangle, name) {
  if (!rectangle || typeof rectangle !== 'object') throw new TypeError(`${name} must be an object`);
  assertInteger(rectangle.x, `${name}.x`);
  assertInteger(rectangle.y, `${name}.y`);
  assertInteger(rectangle.width, `${name}.width`);
  assertInteger(rectangle.height, `${name}.height`);
  if (rectangle.width < 0 || rectangle.height < 0) throw new RangeError(`${name} width and height must be non-negative`);
}

/**
 * Intersect two axis-aligned half-open rectangles [x,x+width) × [y,y+height).
 * Returns an immutable rectangle, or null when the overlap has zero area.
 */
export function rectangleIntersection(first, second) {
  assertRectangle(first, 'first');
  assertRectangle(second, 'second');
  const left = Math.max(first.x, second.x);
  const top = Math.max(first.y, second.y);
  const right = Math.min(first.x + first.width, second.x + second.width);
  const bottom = Math.min(first.y + first.height, second.y + second.height);
  if (right <= left || bottom <= top) return null;
  return Object.freeze({ x: left, y: top, width: right - left, height: bottom - top });
}
