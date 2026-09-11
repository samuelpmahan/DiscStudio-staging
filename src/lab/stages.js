/**
 * The LAB Stages, as the studio runs them.
 *
 * `src/lab/*.js` is the port: the Calculations, and the PQL document each Stage
 * declares (S1's own `PrincipleComponentRender.yaml`, the documents the other
 * Stages' OperationSpecs imply, and the rounds over their produce Parts). Node
 * runs them through `createLab()`; the studio runs the same modules on its own
 * board (src/runtime.js `lab`), so this file is the one place that says, per
 * Stage: what it is called, what it must read before it can run, what it seeds,
 * which Ticks it runs and what it publishes.
 *
 * One spec is one composition. The studio names them `lab-s0`, `lab-s1`, ... and
 * each binds the previous Stage's produce Parts by address, exactly as the
 * documents already do -- nothing here re-plumbs a Stage.
 *
 * A Stage is drawn by the ADDRESSES IT PUBLISHES, not by its number or its name:
 * `DRAWINGS` below is a table from a produce address to what a reader sees of
 * it, and `stageView` picks the first row a Stage's produce matches. A Stage
 * whose number changes keeps its drawing; a Stage that publishes an address the
 * table does not know still runs, still produces, still inspects, and says so
 * ("produced, not drawn") instead of refusing. Drawing one is one row here.
 *
 * Adding a Stage: append its spec to `labStageSpecs()` (or hand one to
 * `runtime.lab.addStage` while it is still being built), and add its address to
 * `DRAWINGS` if it has something to show. `validateStage` says what a spec owes;
 * a spec that brings its own Calculations carries them as `register(lab)`.
 */
import { S0_ADDRESSES, registerS0, s0Document } from './s0.js';
import { S1_ADDRESSES, registerS1, s1YamlDocument, digitModel, asMaskRaster } from './s1.js';
import { S2_ADDRESSES, registerS2, s2Document } from './s2.js';
import { S3_ADDRESSES, registerS3, s3Document } from './s3.js';
// The Stages after S3 are each their own module's spec. A module that is renamed
// changes exactly these import lines -- as task 121's renumbering did, from
// s4/s5/s6 to holes-nearest/s7course/s7round -- because every other thing the
// studio knows about a Stage is an address it publishes, and those did not move.
import { s4Spec } from './s4.js';
import { s5Spec } from './s5.js';
import { s6Spec } from './s6.js';
import { holesNearestSpec } from './holes-nearest.js';
import { s7CourseSpec, cellCenter } from './s7course.js';
import { s7Spec } from './s7round.js';
import { ROUTE_ADDRESSES, registerRoute, routeDocument } from './route.js';
import { labAddress, labDocument } from './address.js';
import { parseYaml } from './yaml.js';
import { readSource } from './source-data.js';

export const LAB_COURSE = 'labfixture';

const BADGES = labAddress('px.badges.objects');

/** The `WhiteDigitRecognition` knobs, read from the LAB's own S1 document. */
export function s1Knobs() {
  return labDocument(parseYaml(readSource('S1.pcr.yaml'))).Ticks.find(tick => tick.name === 'WhiteDigitRecognition').Calculations[0].args.knobs;
}

/** Every `fn.lab.*` Calculation the Stages written here call, on whichever board is given. */
export function registerLabCalculations(lab) {
  registerS0(lab); registerS1(lab); registerS2(lab); registerS3(lab); registerRoute(lab);
}

/**
 * The Stages, in the order they must run. Order is load-bearing: S3's family
 * vote only sees a clean pair because S1's badge mute already ran
 * (proposal.lab.s3.badgemute), and no round has an anchor until the Stages that
 * find tees, baskets and holes have published theirs.
 */
export function labStageSpecs() {
  return [
    {
      key: 's0', stage: 'S0', title: 'Canonical pixels', composition: 'lab-s0',
      about: 'the capture, cropped: the chrome bands a phone photograph carries are found by row entropy and removed, leaving one raster every later Stage reads.',
      needs: [], produces: [S0_ADDRESSES.cropBounds, S0_ADDRESSES.canonicalPixels, S0_ADDRESSES.cacheReceipt],
      raster: S0_ADDRESSES.canonicalPixels,
      seed(lab, { capture, label = 'capture' }) {
        if (!capture || !Array.isArray(capture.rgba)) throw new Error('lab S0: a capture is { imageId, widthPx, heightPx, rgba }.');
        lab.put(S0_ADDRESSES.selectedInput, { decoded: capture, label });
      },
      ticks: lab => s0Document(lab).Ticks
    },
    {
      key: 's1', stage: 'S1', title: 'Badges', composition: 'lab-s1',
      about: "the LAB's own badge-assembly document: black and white masks, 8-connected components, plates with an enclosing border and contained digits, and the digits read.",
      needs: [S0_ADDRESSES.canonicalPixels],
      produces: [...S1_ADDRESSES.outputs],
      seed(lab) {
        lab.put(S1_ADDRESSES.model, digitModel(s1Knobs()));
        lab.put(S1_ADDRESSES.croppedRaster, asMaskRaster(lab.get(S0_ADDRESSES.canonicalPixels)));
      },
      ticks: lab => s1YamlDocument(lab).Ticks
    },
    {
      key: 's2', stage: 'S2', title: 'Baskets', composition: 'lab-s2',
      about: 'the substrate S1 publishes beside its badges, then the basket family: a bright body that matches the sprite inside a dark shell whose margins the family agrees on.',
      needs: [labAddress('px.s1.exp.maskComponents.part.blackMask'), BADGES],
      produces: [S2_ADDRESSES.fields, S2_ADDRESSES.family, S2_ADDRESSES.shellFamily, S2_ADDRESSES.objects],
      ticks: lab => s2Document(lab).Ticks
    },
    {
      key: 's3', stage: 'S3', title: 'Visible tees', composition: 'lab-s3',
      about: "enclosed rings that are elongated and are not a badge's own digit hole, voted into one family by their frames: the tees a reader can actually see on the map.",
      needs: [S2_ADDRESSES.fields, BADGES],
      produces: [S3_ADDRESSES.rings, S3_ADDRESSES.family, S3_ADDRESSES.objects],
      ticks: lab => s3Document(lab).Ticks
    },
    // S4 recovery, S5 the tee-to-badge ray, S6 the straight holes: each brings its
    // own Calculations and its own document, and S7 below plays what S6 resolved.
    s4Spec(),
    s5Spec(),
    s6Spec(),
    holesNearestSpec(),
    s7CourseSpec(),
    s7Spec(),
    {
      key: 'route', stage: 'Straight round', title: 'The round, measured straight', composition: 'lab-route',
      about: 'the holes in the order S1 read off the badges, each tee to its basket and on to the next tee in a straight line: the measure a searched round is compared against.',
      needs: [BADGES, S2_ADDRESSES.objects, S3_ADDRESSES.objects],
      produces: [ROUTE_ADDRESSES.anchors, ROUTE_ADDRESSES.order, ROUTE_ADDRESSES.legs, ROUTE_ADDRESSES.path(LAB_COURSE)],
      ticks: lab => routeDocument(lab, { course: LAB_COURSE }).composition.Ticks
    }
  ];
}

/* ------------------------------------------------------------------ */
/* what a reader sees of a Stage, by the address the Stage publishes    */
/* ------------------------------------------------------------------ */

const box = (bbox, extra) => ({ bbox, at: [bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2], ...extra });
/** A point, however the Stage that published it wrote one: `[x, y]`, `{ at }`, or `{ x, y }`. */
export function pointOf(value) {
  if (Array.isArray(value) && typeof value[0] === 'number' && typeof value[1] === 'number') return [value[0], value[1]];
  if (!value || typeof value !== 'object') return null;
  if (value.at) return pointOf(value.at);
  if (typeof value.x === 'number' && typeof value.y === 'number') return [value.x, value.y];
  if (Array.isArray(value.centre ?? value.center)) return pointOf(value.centre ?? value.center);
  return null;
}
const firstList = value => Array.isArray(value) ? value : Object.values(value ?? {}).find(Array.isArray) ?? [];
/**
 * The list a Part of things means. A Stage writes either the list itself, or a
 * document around it -- `{ for, from, rule, rays: [...] }` -- and the property
 * that holds the things is named by the last segment of the Part's own address
 * (`px.exp.lab.teebadge.rays` -> `rays`). That convention, then `objects`, then
 * the first list in the document: never a guess that silently picks `from`.
 */
export function listOf(value, address = '') {
  if (Array.isArray(value)) return value;
  const tail = address.slice(address.lastIndexOf('.') + 1);
  if (Array.isArray(value?.[tail])) return value[tail];
  if (Array.isArray(value?.objects)) return value.objects;
  return firstList(value);
}
const objectList = value => Array.isArray(value?.objects) ? value.objects : firstList(value);
/** The three lists a recovery Stage publishes, drawn as one layer. */
const RECOVERED = ['px.exp.lab.recovered.badges', 'px.exp.lab.recovered.baskets', 'px.exp.lab.recovered.tees'];
/** Only the objects a recovery actually recovered: `recovered` if the Part names it, else what no family found. */
const recoveredOnly = value => Array.isArray(value?.recovered) ? value.recovered : objectList(value).filter(item => item.basis && !/family/.test(item.basis));
const numbered = (item, index, what) => item.number ?? item.hole ?? item.id ?? `${what}-${index + 1}`;

/**
 * One row per address a Stage can publish. `build` is given the board and the
 * address; anything it throws is reported as "produced, not drawn" rather than
 * taking the route down, because a Stage landing with a shape this table has not
 * seen is a drawing to add, not a broken studio.
 */
export const DRAWINGS = [
  {
    address: S0_ADDRESSES.canonicalPixels, kind: 'raster', tone: 'raster',
    build: (lab, address) => {
      const raster = lab.get(address), crop = lab.has(S0_ADDRESSES.cropBounds) ? lab.get(S0_ADDRESSES.cropBounds) : null;
      return { objects: [{ id: 'canonical-pixels', label: `${raster.widthPx} × ${raster.heightPx} canonical pixels`, part: address, detail: { crop: crop?.source ?? null, insets: crop?.insets ?? null } }] };
    }
  },
  {
    address: BADGES, kind: 'boxes', tone: 'badge',
    build: (lab, address) => ({ objects: lab.get(address).map((badge, index) => box(badge.unaccountedButOwned.bbox, {
      id: badge.id, label: badge.reading.status === 'read' ? `hole ${Number(badge.reading.value)}` : 'badge · unread',
      part: address, index, detail: { reading: badge.reading.value, status: badge.reading.status, digits: badge.digits.length, pixels: badge.pixels.length }
    })) })
  },
  {
    address: S2_ADDRESSES.objects, kind: 'boxes', tone: 'basket', labelBelow: true,
    build: (lab, address) => ({ objects: lab.get(address).map((basket, index) => box(basket.bbox, {
      id: `basket-${index + 1}`, label: `basket ${index + 1}`, part: address, index,
      detail: { whitePx: basket.whitePx, blackPx: basket.blackPx, px: basket.px.length }
    })) })
  },
  {
    address: S3_ADDRESSES.objects, kind: 'boxes', tone: 'tee',
    build: (lab, address) => ({ objects: lab.get(address).map((tee, index) => box(tee.bbox, {
      id: `tee-${index + 1}`, label: `tee ${index + 1}`, part: address, index, at: tee.center,
      detail: { center: tee.center, px: tee.px.length, angleRad: tee.angleRad }
    })) })
  },
  {
    // S4, recovery: objects that overlapped and were taken apart again.
    prefix: 'px.exp.lab.recovered.', kind: 'boxes', tone: 'recovered',
    // A recovery Part is `{ kind, clean, recovered, objects, rejected }`. Only what
    // was RECOVERED is drawn here: the clean objects are already on the raster,
    // drawn by the Stage that found them, and this layer is what the overlap hid.
    build: (lab, address) => ({ objects: RECOVERED.filter(candidate => lab.has(candidate)).flatMap(candidate => recoveredOnly(lab.get(candidate)).map((item, index) => {
      const bbox = item.bbox ?? item.box, at = pointOf(item);
      if (!bbox && !at) throw new Error('a recovered object carries neither a bbox nor a point');
      const what = candidate.slice(candidate.lastIndexOf('.') + 1).replace(/s$/, '');
      return {
        ...(bbox ? box(bbox, {}) : { at }), id: `${what}-${numbered(item, index, what)}`,
        label: `${what} ${numbered(item, index, what)} · recovered`, part: candidate, index, detail: item
      };
    })) })
  },
  {
    // S5, Tee -> Badge: the ray each tee points along, at the badge it names.
    address: 'px.exp.lab.teebadge.rays', kind: 'rays', tone: 'ray',
    build: (lab, address) => {
      const rays = listOf(lab.get(address), address);
      const paired = rays.filter(ray => pointOf(ray.badge ?? ray.to) || ray.entryAt);
      const legs = paired.map((ray, index) => {
        const from = pointOf(ray.from ?? ray.origin ?? ray.tee), to = pointOf(ray.badge ?? ray.to) ?? pointOf(ray.entryAt);
        if (!from || !to) throw new Error(`a ray carries no tee-to-badge points (keys: ${Object.keys(ray).join(', ')})`);
        return { kind: 'ray', hole: ray.badge?.reading ?? numbered(ray, index, 'ray'), from, to, lengthPx: ray.distancePx ?? null };
      });
      return {
        legs,
        objects: legs.map((leg, index) => ({
          id: `ray-${paired[index].tee ?? index}`, label: `${paired[index].tee ?? 'tee'} → ${paired[index].badge?.id ?? 'badge'}`,
          at: [(leg.from[0] + leg.to[0]) / 2, (leg.from[1] + leg.to[1]) / 2], part: address, index, detail: paired[index]
        }))
      };
    }
  },
  {
    // S6, straight holes: tee, badge and basket on one line; what the ray could not resolve is a dogleg.
    address: 'px.exp.lab.holes.straight', kind: 'holes', tone: 'hole', labelBelow: true, hitOutline: true,
    build: (lab, address) => {
      const holes = listOf(lab.get(address), address), unresolvedAddress = 'px.exp.lab.holes.unresolved';
      const legs = [], objects = [];
      holes.forEach((hole, index) => {
        const tee = pointOf(hole.tee), basket = pointOf(hole.basket), badge = pointOf(hole.badge);
        if (!tee || !basket) throw new Error(`a straight hole carries no tee and basket points (keys: ${Object.keys(hole).join(', ')})`);
        legs.push({ kind: 'play', hole: numbered(hole, index, 'hole'), from: tee, to: basket, lengthPx: hole.lengthPx ?? null });
        objects.push({ id: `hole-${numbered(hole, index, 'hole')}`, label: `hole ${numbered(hole, index, 'hole')}`, at: badge ?? [(tee[0] + basket[0]) / 2, (tee[1] + basket[1]) / 2], part: address, index, detail: hole });
      });
      if (lab.has(unresolvedAddress)) listOf(lab.get(unresolvedAddress), unresolvedAddress).forEach((item, index) => {
        const at = pointOf(item.badge ?? item);
        const where = at ?? (item.bbox ? [item.bbox[0] + item.bbox[2] / 2, item.bbox[1] + item.bbox[3] / 2] : null);
        if (where) objects.push({ id: `dogleg-${numbered(item, index, 'badge')}`, label: `dogleg · ${item.reading ? `hole ${item.reading}` : numbered(item, index, 'badge')}`, at: where, part: unresolvedAddress, index, detail: item });
      });
      return { legs, objects };
    }
  },
  {
    // The nearest-anchor hole assembly, kept as the fallback: a hole is the extent of its badge, tee and basket.
    address: 'px.exp.lab.holes.objects', kind: 'boxes', tone: 'hole', labelBelow: true, hitOutline: true,
    build: (lab, address) => ({ objects: lab.get(address).map((hole, index) => {
      const anchors = [pointOf(hole.badge), pointOf(hole.tee), pointOf(hole.basket)].filter(Boolean);
      const xs = anchors.map(at => at[0]), ys = anchors.map(at => at[1]), pad = 14;
      return {
        ...box([Math.min(...xs) - pad, Math.min(...ys) - pad, Math.max(...xs) - Math.min(...xs) + pad * 2, Math.max(...ys) - Math.min(...ys) + pad * 2], {}),
        id: `hole-${hole.number}`, label: hole.complete ? `hole ${hole.number}` : `hole ${hole.number} · missing ${hole.missing.join(' + ')}`,
        part: address, index, detail: { number: hole.number, tee: hole.tee?.id ?? null, basket: hole.basket?.id ?? null, confidence: hole.confidence, missing: hole.missing }
      };
    }) })
  },
  {
    // The course graph: the obstacle map as the cells it is, and the edges over it.
    address: 'px.exp.lab.course.graph', kind: 'cells', tone: 'obstacle',
    build: (lab, address) => {
      const graph = lab.get(address), frame = graph.frame, at = id => graph.nodes.find(node => node.id === id)?.at ?? null;
      return {
        cells: { size: frame.cellPx, centres: graph.obstacles.terrainCells.map(cell => cellCenter(frame, cell)) },
        legs: graph.edges.map(edge => ({ kind: edge.straightIsBlocked ? 'blocked' : edge.kind, hole: edge.hole, from: at(edge.from), to: at(edge.to), lengthPx: edge.straightLengthPx })).filter(edge => edge.from && edge.to),
        objects: graph.holes.map((hole, index) => ({
          id: `course-hole-${hole.number}`, label: `${hole.lengthPx} px`, part: address, index,
          at: [(hole.tee.at[0] + hole.basket.at[0]) / 2, (hole.tee.at[1] + hole.basket.at[1]) / 2],
          detail: { number: hole.number, lengthPx: hole.lengthPx, bearingDeg: hole.bearingDeg, confidence: hole.confidence }
        }))
      };
    }
  },
  {
    // The round actually walked: the searched polyline, bends and all.
    address: 'px.exp.lab.round.path', kind: 'path', tone: 'round',
    build: (lab, address) => {
      // The searched round is one polyline, not a line per cell: the path bends
      // as often as the obstacle map makes it bend.
      const path = lab.get(address), points = path.points.map(pointOf).filter(Boolean);
      const middle = points[Math.floor(points.length / 2)] ?? null;
      return {
        polyline: points,
        points: path.waypoints.map(point => ({ id: point.id, at: pointOf(point) })).filter(point => point.at),
        objects: middle ? [{
          id: 'round', label: `round · ${path.lengthPx} px`, at: middle, part: address, index: 0,
          detail: { lengthPx: path.lengthPx, playLengthPx: path.playLengthPx, walkLengthPx: path.walkLengthPx, cost: path.cost, cells: path.cells.length, waypoints: path.waypoints.map(waypoint => waypoint.id), unreachable: path.unreachable }
        }] : []
      };
    }
  },
  {
    // The straight round: the legs as drawn lines, the holes in badge order.
    address: ROUTE_ADDRESSES.path(LAB_COURSE), kind: 'path', tone: 'straight',
    build: (lab, address) => {
      const path = lab.get(address);
      return {
        points: path.waypoints.map(point => ({ id: point.id, at: point.at })),
        legs: path.legs.map(leg => ({ kind: leg.kind, hole: leg.hole, from: leg.from.at, to: leg.to.at, lengthPx: leg.lengthPx })),
        objects: path.holes.map((hole, index) => ({
          id: `straight-hole-${hole.number}`, label: `hole ${hole.number}`, part: address, index,
          at: path.legs.find(leg => leg.kind === 'play' && leg.hole === hole.number)?.from.at ?? null,
          detail: { ...hole, playLengthPx: path.legs.find(leg => leg.kind === 'play' && leg.hole === hole.number)?.lengthPx ?? null }
        }))
      };
    }
  }
];

/** The first drawing this Stage's produce matches, and the address it matched on. */
export function drawingFor(spec, lab) {
  for (const drawing of DRAWINGS) {
    const address = (spec.produces ?? []).find(candidate => drawing.address ? candidate === drawing.address : candidate.startsWith(drawing.prefix));
    if (address && lab.has(address)) return { drawing, address };
  }
  return null;
}

/**
 * What a reader sees of one Stage. A Stage with no drawing yet, or one whose
 * produce does not fit the drawing it matched, is reported and not drawn: the
 * Stage still ran, its Parts are still on the board and still inspectable.
 */
export function stageView(spec, lab) {
  const matched = drawingFor(spec, lab);
  if (!matched) return null;
  const { drawing, address } = matched;
  const head = { key: spec.key, stage: spec.stage, title: spec.title, kind: drawing.kind, tone: drawing.tone, address, ...(drawing.labelBelow ? { labelBelow: true } : {}), ...(drawing.hitOutline ? { hitOutline: true } : {}) };
  try { return { ...head, ...drawing.build(lab, address) }; }
  catch (error) { return { ...head, kind: 'undrawn', objects: [], note: `${spec.stage} produced ${address}; this studio could not draw it: ${error.message}` }; }
}

/** What a Stage spec owes, checked once when it joins the pipeline. */
export function validateStage(spec) {
  for (const field of ['key', 'stage', 'title', 'composition']) if (typeof spec?.[field] !== 'string' || !spec[field].length) throw new Error(`lab stage: '${field}' is a nonempty string.`);
  if (!/^lab-[a-z0-9-]+$/.test(spec.composition)) throw new Error(`lab stage '${spec.key}': a composition is named lab-<stage>, not '${spec.composition}'.`);
  if (typeof spec.ticks !== 'function') throw new Error(`lab stage '${spec.key}': ticks(lab) returns the Stage document's Ticks.`);
  if (!Array.isArray(spec.produces) || !spec.produces.length) throw new Error(`lab stage '${spec.key}': produces names at least one address.`);
  for (const address of [...spec.produces, ...(spec.needs ?? [])]) if (!address.startsWith('px.exp.lab.')) throw new Error(`lab stage '${spec.key}': '${address}' is not a px.exp.lab.* address.`);
  if (spec.view && typeof spec.view !== 'function') throw new Error(`lab stage '${spec.key}': view(lab) is a function.`);
  for (const hook of ['seed', 'register']) if (spec[hook] && typeof spec[hook] !== 'function') throw new Error(`lab stage '${spec.key}': ${hook}(lab) is a function.`);
  return spec;
}
