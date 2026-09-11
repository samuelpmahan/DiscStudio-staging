/**
 * The LAB Stages, as the studio runs them.
 *
 * `src/lab/*.js` is the port: the Calculations, and the PQL document each Stage
 * declares (S1's own `PrincipleComponentRender.yaml`, the documents S0's, S2's
 * and S3's OperationSpecs imply, and the round over their produce Parts). Node
 * runs them through `createLab()`; the studio runs the same modules on its own
 * board (src/runtime.js `lab`), so this file is the one place that says, per
 * Stage: what it is called, what it must read before it can run, what it seeds,
 * which Ticks it runs, what it publishes, and what a reader can see of its
 * produce on a raster.
 *
 * One spec is one composition. The studio names them `lab-s0`, `lab-s1`, ... and
 * each binds the previous Stage's produce Parts by address, exactly as the
 * documents already do -- nothing here re-plumbs a Stage.
 *
 * Adding S4/S5/S6: append a spec to `labStageSpecs()` below (or hand one to
 * `runtime.lab.addStage` for a stage that is still being built). `validateStage`
 * says what a spec owes, and the Course route draws any spec's `view()` with no
 * new drawing code: `boxes` for objects with a bbox, `path` for a round. A spec that
 * brings its own Calculations carries them as `register(lab)`, which the pipeline
 * calls once when the Stage joins.
 */
import { S0_ADDRESSES, registerS0, s0Document } from './s0.js';
import { S1_ADDRESSES, registerS1, s1YamlDocument, digitModel, asMaskRaster } from './s1.js';
import { S2_ADDRESSES, registerS2, s2Document } from './s2.js';
import { S3_ADDRESSES, registerS3, s3Document } from './s3.js';
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

/** Every `fn.lab.*` Calculation the Stages below call, on whichever board is given. */
export function registerLabCalculations(lab) {
  registerS0(lab); registerS1(lab); registerS2(lab); registerS3(lab); registerRoute(lab);
}

const box = (bbox, extra) => ({ bbox, at: [bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2], ...extra });

/**
 * The five Stages that are landed. Order is load-bearing: S3's family vote only
 * sees a clean pair because S1's badge mute already ran (proposal.lab.s3.badgemute),
 * and the round has no anchors until S1, S2 and S3 have published theirs.
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
      ticks: lab => s0Document(lab).Ticks,
      view(lab) {
        const crop = lab.get(S0_ADDRESSES.cropBounds), raster = lab.get(S0_ADDRESSES.canonicalPixels);
        return { kind: 'raster', tone: 'raster', objects: [{
          id: 'canonical-pixels', label: `${raster.widthPx} × ${raster.heightPx} canonical pixels`,
          part: S0_ADDRESSES.canonicalPixels, detail: { crop: crop.source, insets: crop.insets }
        }] };
      }
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
      ticks: lab => s1YamlDocument(lab).Ticks,
      view(lab) {
        return { kind: 'boxes', tone: 'badge', objects: lab.get(BADGES).map((badge, index) => box(badge.unaccountedButOwned.bbox, {
          id: badge.id, label: badge.reading.status === 'read' ? `hole ${Number(badge.reading.value)}` : 'badge · unread',
          part: BADGES, index, detail: { reading: badge.reading.value, status: badge.reading.status, digits: badge.digits.length, pixels: badge.pixels.length }
        })) };
      }
    },
    {
      key: 's2', stage: 'S2', title: 'Baskets', composition: 'lab-s2',
      about: 'the substrate S1 publishes beside its badges, then the basket family: a bright body that matches the sprite inside a dark shell whose margins the family agrees on.',
      needs: [labAddress('px.s1.exp.maskComponents.part.blackMask'), BADGES],
      produces: [S2_ADDRESSES.fields, S2_ADDRESSES.family, S2_ADDRESSES.shellFamily, S2_ADDRESSES.objects],
      ticks: lab => s2Document(lab).Ticks,
      view(lab) {
        return { kind: 'boxes', tone: 'basket', objects: lab.get(S2_ADDRESSES.objects).map((basket, index) => box(basket.bbox, {
          id: `basket-${index + 1}`, label: `basket ${index + 1}`, part: S2_ADDRESSES.objects, index,
          detail: { whitePx: basket.whitePx, blackPx: basket.blackPx, px: basket.px.length }
        })) };
      }
    },
    {
      key: 's3', stage: 'S3', title: 'Visible tees', composition: 'lab-s3',
      about: "enclosed rings that are elongated and are not a badge's own digit hole, voted into one family by their frames: the tees a reader can actually see on the map.",
      needs: [S2_ADDRESSES.fields, BADGES],
      produces: [S3_ADDRESSES.rings, S3_ADDRESSES.family, S3_ADDRESSES.objects],
      ticks: lab => s3Document(lab).Ticks,
      view(lab) {
        return { kind: 'boxes', tone: 'tee', objects: lab.get(S3_ADDRESSES.objects).map((tee, index) => box(tee.bbox, {
          id: `tee-${index + 1}`, label: `tee ${index + 1}`, part: S3_ADDRESSES.objects, index,
          at: tee.center, detail: { center: tee.center, px: tee.px.length, angleRad: tee.angleRad }
        })) };
      }
    },
    {
      key: 'route', stage: 'Round', title: 'The round', composition: 'lab-route',
      about: 'the course itself: the holes in the order S1 read off the badges, each tee to its basket and on to the next tee, over the canonical raster.',
      needs: [BADGES, S2_ADDRESSES.objects, S3_ADDRESSES.objects],
      produces: [ROUTE_ADDRESSES.anchors, ROUTE_ADDRESSES.order, ROUTE_ADDRESSES.legs, ROUTE_ADDRESSES.path(LAB_COURSE)],
      ticks: lab => routeDocument(lab, { course: LAB_COURSE }).composition.Ticks,
      view(lab) {
        const address = ROUTE_ADDRESSES.path(LAB_COURSE), path = lab.get(address);
        return {
          kind: 'path', tone: 'round',
          points: path.waypoints.map(point => ({ id: point.id, at: point.at })),
          legs: path.legs.map(leg => ({ kind: leg.kind, hole: leg.hole, from: leg.from.at, to: leg.to.at, lengthPx: leg.lengthPx })),
          objects: path.holes.map((hole, index) => ({
            id: `hole-${hole.number}`, label: `hole ${hole.number}`, part: address, index,
            at: path.legs.find(leg => leg.kind === 'play' && leg.hole === hole.number)?.from.at ?? null,
            detail: { ...hole, playLengthPx: path.legs.find(leg => leg.kind === 'play' && leg.hole === hole.number)?.lengthPx ?? null }
          }))
        };
      }
    }
  ];
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
