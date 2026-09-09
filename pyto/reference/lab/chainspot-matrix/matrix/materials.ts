/**
 * Source-backed material for the LAB matrix reader.
 *
 * This is deliberately only an observation material: it contains no branch
 * selection or truth decision.  The numbers below are retained even when an
 * observation is weak, dark rather than bright, or unknown.
 */
import { createHash } from 'node:crypto';
import {
	DEFAULT_FOUR_LANE_SENSOR_KNOBS,
	sampleFourLaneBand,
	type FourLaneOccluder,
	type FourLaneSensorKnobs
} from '@chainspot/alg/detectors/threeFactor/features/st.fourLaneSensor';
import type { RgbaImage } from '@chainspot/alg/detectors/threeFactor/types';
import { pxFn, type PxC } from '@chainspot/alg/exec/board';

export type MatrixFrame = 'source-image-px' | 'lab-canonical-px';
export type MatrixReadingStatus = 'paired' | 'one-sided' | 'loss' | 'UNKNOWN';

export interface MatrixPoint { readonly xPx: number; readonly yPx: number }
export interface MatrixHeading { readonly x: number; readonly y: number }
export interface MatrixBadgeMask extends FourLaneOccluder {}
export interface MatrixSeed { readonly tee: MatrixPoint; readonly badge: MatrixPoint }
export interface MatrixSource {
	/** SHA-256 of the exact bytes decoded into image. */
	readonly contentHash: string;
	readonly frame: MatrixFrame;
	readonly image: RgbaImage;
}
export interface MatrixMaterialCounters {
	requests: number;
	hits: number;
	misses: number;
	writes: number;
	profileHits: number;
	profileMisses: number;
	profileWrites: number;
}
export interface MatrixMaterialCache { readonly counters: MatrixMaterialCounters }
export interface MatrixProfileBand {
	readonly offsetPx: number;
	readonly mean: number | null;
	readonly rgb: readonly [number, number, number] | null;
	readonly unknown: boolean;
}
export interface MatrixWidthHypothesis {
	/** Full corridor width inferred from Tee->Badge cross-sections, never a probe offset. */
	readonly widthPx: number;
	/** Coherent signed-edge magnitude. Negative means the two signs disagree. */
	readonly score: number | null;
	readonly leftSigned: number | null;
	readonly rightSigned: number | null;
	readonly left: MatrixProfileBand;
	readonly right: MatrixProfileBand;
	/** Inward contrasts at every requested broad span around both boundaries. */
	readonly edgeSpans: readonly MatrixEdgeSpan[];
	/** Mean coherent contrast across edgeSpans; source data, not a threshold. */
	readonly broadCoherence: number | null;
	/** Existing four-lane sampler read, retained as a compatibility witness. */
	readonly fourLaneScore: number | null;
}
export interface MatrixEdgeSpan {
	readonly spanPx: number;
	readonly leftSigned: number | null;
	readonly rightSigned: number | null;
	readonly coherence: number | null;
}
export interface MatrixWidthFamily {
	readonly source: 'tee-badge-exposed-cross-sections' | 'UNKNOWN';
	readonly candidates: readonly MatrixWidthHypothesis[];
	readonly selectedWidthsPx: readonly number[];
	readonly sampledCrossSections: number;
	/** The best measured width is at the sampled family boundary. Do not treat it as a settled width. */
	readonly boundaryOptimum: boolean;
	/** Frozen calibration aggregate used only by callers choosing a prototype grade. */
	readonly supportThreshold: number | null;
}
export interface MatrixCenterReference {
	readonly mean: number | null;
	readonly samples: readonly number[];
	readonly exposedSamples: number;
	/** Maximum observed exposed-center deviation from mean, in source luminance. */
	readonly tolerance: number | null;
}
export interface MatrixContactNormal {
	readonly x: number | null;
	readonly y: number | null;
	readonly magnitude: number | null;
	readonly confidence: 'measured' | 'weak' | 'UNKNOWN';
}
export interface MatrixProfileReading {
	readonly xPx: number;
	readonly yPx: number;
	readonly heading: MatrixHeading;
	readonly status: MatrixReadingStatus;
	/** Availability only; it is intentionally not a route/truth verdict. */
	readonly availability: 'paired' | 'one-sided' | 'UNKNOWN';
	/** Graded prototype result from frozen calibration thresholds; never route truth. */
	readonly supported: boolean | null;
	readonly supportThreshold: number | null;
	readonly centerTolerance: number | null;
	/** Raw inward, signed edge contrasts. Dark corridor material remains negative evidence. */
	readonly leftSigned: number | null;
	readonly rightSigned: number | null;
	readonly center: MatrixProfileBand;
	/** |center - reference| from the exposed Tee->Badge material, never flank-to-flank similarity. */
	readonly centerReferenceError: number | null;
	readonly centerResemblance: number | null;
	readonly widthHypotheses: readonly MatrixWidthHypothesis[];
	/** Absolute normal-distance probe magnitudes, including the broad 12px span. */
	readonly probeOffsetsPx: readonly number[];
	/** Raw readings at both -offset and +offset; never repurposed as widths. */
	readonly probes: readonly MatrixProfileBand[];
	readonly normal: MatrixContactNormal;
	readonly masked: boolean;
}
export interface MatrixMaterials {
	readonly key: string;
	readonly materialAddress: string;
	readonly image: RgbaImage;
	readonly widthFamily: MatrixWidthFamily;
	readonly reference: MatrixCenterReference;
	readonly cache: { readonly hit: boolean; readonly counters: MatrixMaterialCounters };
	read(position: MatrixPoint, heading: MatrixHeading): MatrixProfileReading;
}
export interface CreateMatrixMaterialsInput {
	readonly board: PxC;
	readonly source: MatrixSource;
	readonly seed: MatrixSeed;
	/** Badge ownership mask. It is used during both calibration and live reads. */
	readonly badgeMask: MatrixBadgeMask;
	readonly occluders?: readonly FourLaneOccluder[];
	readonly calculationRevision?: string;
	readonly sensorKnobs?: FourLaneSensorKnobs;
	readonly cache?: MatrixMaterialCache;
}

const REVISION = 'matrix-materials-source-profile-v1';
const PROFILE_FN = pxFn<MaterialRequest, MatrixMaterial>('fn.matrix.material.profile.v1');
const POSE_PROFILE_FN = pxFn<PoseRequest, MatrixProfileReading>('fn.matrix.material.pose-profile.v1');
const registered = new WeakSet<PxC>();
const PROBE_OFFSETS = Object.freeze([2.5, 5, 7, 9, 12]);

interface MaterialRequest {
	readonly key: string;
	readonly source: MatrixSource;
	readonly seed: MatrixSeed;
	readonly occluders: readonly FourLaneOccluder[];
	readonly knobs: FourLaneSensorKnobs;
}
interface MatrixMaterial {
	readonly key: string;
	readonly widthFamily: MatrixWidthFamily;
	readonly reference: MatrixCenterReference;
}
interface PoseRequest {
	readonly source: MatrixSource;
	readonly material: MatrixMaterial;
	readonly position: MatrixPoint;
	readonly heading: MatrixHeading;
	readonly occluders: readonly FourLaneOccluder[];
	readonly knobs: FourLaneSensorKnobs;
}

export function createMatrixMaterialCache(): MatrixMaterialCache {
	return { counters: { requests: 0, hits: 0, misses: 0, writes: 0, profileHits: 0, profileMisses: 0, profileWrites: 0 } };
}

function canonical(value: unknown): string {
	if (value === null || typeof value !== 'object') return JSON.stringify(value);
	if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
	const record = value as Record<string, unknown>;
	return `{${Object.keys(record).sort().map((key) => `${JSON.stringify(key)}:${canonical(record[key])}`).join(',')}}`;
}
function sha(value: string): string { return createHash('sha256').update(value).digest('hex'); }
function freeze<T>(value: T): T {
	// Raster payloads retain their typed backing arrays; V8 forbids freezing a
	// non-empty typed array even though the enclosing material is immutable.
	if (ArrayBuffer.isView(value)) return value;
	if (value && typeof value === 'object' && !Object.isFrozen(value)) {
		Object.freeze(value);
		for (const child of Object.values(value as Record<string, unknown>)) freeze(child);
	}
	return value;
}
function contains(mask: FourLaneOccluder, point: MatrixPoint): boolean {
	return point.xPx >= mask.bboxX && point.xPx <= mask.bboxX + mask.bboxW && point.yPx >= mask.bboxY && point.yPx <= mask.bboxY + mask.bboxH;
}
function blocked(point: MatrixPoint, masks: readonly FourLaneOccluder[]): boolean { return masks.some((mask) => contains(mask, point)); }
function bilinear(image: RgbaImage, x: number, y: number, masks: readonly FourLaneOccluder[]): readonly [number, number, number] | null {
	if (x < 0 || y < 0 || x > image.width - 1 || y > image.height - 1 || blocked({ xPx: x, yPx: y }, masks)) return null;
	const x0 = Math.floor(x), y0 = Math.floor(y), x1 = Math.min(image.width - 1, x0 + 1), y1 = Math.min(image.height - 1, y0 + 1);
	// Reject interpolation across a known badge. A masked contribution is UNKNOWN,
	// never silently diluted into a terrain value.
	if ([[x0,y0],[x1,y0],[x0,y1],[x1,y1]].some(([px, py]) => blocked({ xPx: px, yPx: py }, masks))) return null;
	const fx = x - x0, fy = y - y0;
	const value = (channel: number) => {
		const at = (px: number, py: number) => image.data[(py * image.width + px) * 4 + channel];
		return (1 - fx) * (1 - fy) * at(x0, y0) + fx * (1 - fy) * at(x1, y0) + (1 - fx) * fy * at(x0, y1) + fx * fy * at(x1, y1);
	};
	return [value(0), value(1), value(2)];
}
function luminance(rgb: readonly [number, number, number]): number { return .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2]; }
function headingRadians(heading: MatrixHeading): number | null {
	const length = Math.hypot(heading.x, heading.y);
	return length > 1e-9 ? Math.atan2(heading.y, heading.x) : null;
}
function band(image: RgbaImage, center: MatrixPoint, heading: MatrixHeading, offsetPx: number, masks: readonly FourLaneOccluder[], knobs: FourLaneSensorKnobs): MatrixProfileBand {
	const angle = headingRadians(heading);
	if (angle === null) return freeze({ offsetPx, mean: null, rgb: null, unknown: true });
	const tx = Math.cos(angle), ty = Math.sin(angle), nx = -ty, ny = tx;
	const values: (readonly [number, number, number])[] = [];
	let unknown = 0;
	for (let i = 0; i < knobs.tangentSamples; i++) {
		const along = knobs.tangentSamples === 1 ? 0 : -knobs.tangentHalfPx + 2 * knobs.tangentHalfPx * i / (knobs.tangentSamples - 1);
		const sample = bilinear(image, center.xPx + nx * offsetPx + tx * along, center.yPx + ny * offsetPx + ty * along, masks);
		if (sample === null) unknown++; else values.push(sample);
	}
	if (!values.length || unknown * 2 >= knobs.tangentSamples) return freeze({ offsetPx, mean: null, rgb: null, unknown: true });
	const rgb: [number, number, number] = [0, 1, 2].map(channel => values.reduce((sum, value) => sum + value[channel], 0) / values.length) as [number, number, number];
	return freeze({ offsetPx, mean: luminance(rgb), rgb: freeze(rgb), unknown: false });
}
function signedEdges(image: RgbaImage, center: MatrixPoint, heading: MatrixHeading, widthPx: number, masks: readonly FourLaneOccluder[], knobs: FourLaneSensorKnobs): Omit<MatrixWidthHypothesis, 'score' | 'fourLaneScore' | 'edgeSpans' | 'broadCoherence'> {
	const half = widthPx / 2;
	const leftInside = band(image, center, heading, -half + knobs.edgeDeltaPx, masks, knobs);
	const leftOutside = band(image, center, heading, -half - knobs.edgeDeltaPx, masks, knobs);
	const rightInside = band(image, center, heading, half - knobs.edgeDeltaPx, masks, knobs);
	const rightOutside = band(image, center, heading, half + knobs.edgeDeltaPx, masks, knobs);
	const leftSigned = leftInside.mean === null || leftOutside.mean === null ? null : leftInside.mean - leftOutside.mean;
	const rightSigned = rightInside.mean === null || rightOutside.mean === null ? null : rightInside.mean - rightOutside.mean;
	return { widthPx, leftSigned, rightSigned, left: leftInside, right: rightInside };
}
function coherence(left: number | null, right: number | null): number | null {
	if (left === null || right === null) return null;
	const magnitude = Math.min(Math.abs(left), Math.abs(right));
	return left === 0 || right === 0 || Math.sign(left) === Math.sign(right) ? magnitude : -magnitude;
}
function fourLaneWitness(source: MatrixSource, center: MatrixPoint, heading: MatrixHeading, widthPx: number, masks: readonly FourLaneOccluder[], knobs: FourLaneSensorKnobs): number | null {
	const angle = headingRadians(heading);
	if (angle === null) return null;
	const result = sampleFourLaneBand(source.image, center, angle, widthPx / 2, masks, knobs);
	return result.occluded ? null : result.mean;
}
function hypothesis(source: MatrixSource, center: MatrixPoint, heading: MatrixHeading, widthPx: number, masks: readonly FourLaneOccluder[], knobs: FourLaneSensorKnobs): MatrixWidthHypothesis {
	const edges = signedEdges(source.image, center, heading, widthPx, masks, knobs);
	const edgeSpans = PROBE_OFFSETS.map(spanPx => {
		const atSpan = signedEdges(source.image, center, heading, widthPx, masks, { ...knobs, edgeDeltaPx: spanPx });
		return freeze({ spanPx, leftSigned: atSpan.leftSigned, rightSigned: atSpan.rightSigned, coherence: coherence(atSpan.leftSigned, atSpan.rightSigned) });
	});
	const broadCoherence = mean(edgeSpans.map(span => span.coherence).filter((value): value is number => value !== null));
	return freeze({ ...edges, edgeSpans: freeze(edgeSpans), broadCoherence, score: broadCoherence, fourLaneScore: fourLaneWitness(source, center, heading, widthPx, masks, knobs) });
}
function mean(values: readonly number[]): number | null { return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null; }
function deriveMaterial(request: MaterialRequest): MatrixMaterial {
	// Coordinates and image are in the frame declared by the caller.  A caller
	// using a crop must convert the raster and every coordinate together before
	// constructing this material; hidden frame shifts make cache parity false.
	const tee = request.seed.tee, badge = request.seed.badge;
	const heading = { x: badge.xPx - tee.xPx, y: badge.yPx - tee.yPx };
	const distance = Math.hypot(heading.x, heading.y);
	const widths: number[] = [];
	// Width is a property of the source material, not of this seed leg. Scan a
	// source-bounded family so a short Tee->Badge leg cannot erase broad lanes.
	const maximumWidth = Math.max(6, Math.min(128, Math.floor(Math.min(request.source.image.width, request.source.image.height) / 2)));
	for (let width = 6; width <= maximumWidth; width += 2) widths.push(width);
	const crossSections: MatrixPoint[] = [];
	for (const fraction of [.12, .20, .28, .36, .44, .52, .60, .68]) {
		const point = { xPx: tee.xPx + heading.x * fraction, yPx: tee.yPx + heading.y * fraction };
		if (!blocked(point, request.occluders)) crossSections.push(point);
	}
	const ranked = widths.map(widthPx => {
		const observations = crossSections.map(point => hypothesis(request.source, point, heading, widthPx, request.occluders, request.knobs));
		const score = mean(observations.map(value => value.score).filter((value): value is number => value !== null));
		const representative = observations.find(value => value.score !== null) ?? hypothesis(request.source, tee, heading, widthPx, request.occluders, request.knobs);
		return freeze({ ...representative, score });
	});
	const positive = ranked.map(value => value.score).filter((value): value is number => value !== null && value > 0);
	const best = positive.length ? Math.max(...positive) : null;
	// Keep the near-family (and not one highest noisy pair); readings still expose
	// every raw hypothesis in widthHypotheses below.
	// `ranked` remains in physical width order for inspection.  The retained
	// family is explicitly score ordered so truncation cannot discard a broad
	// optimum simply because it appears late in that physical list.
	const selected = best === null ? [] : ranked
		.filter(value => value.score !== null && value.score >= best * .72)
		.sort((a, b) => (b.score as number) - (a.score as number))
		.slice(0, 6)
		.map(value => value.widthPx);
	const referenceSamples = crossSections.map(point => band(request.source.image, point, heading, 0, request.occluders, request.knobs).mean).filter((value): value is number => value !== null);
	const referenceMean = mean(referenceSamples);
	// `score` is the aggregate over all exposed cross-sections.  Do not replace
	// it with one representative cross-section when freezing threshold provenance.
	const supportThreshold = mean(selected.map(width => ranked.find(candidate => candidate.widthPx === width)?.score).filter((value): value is number => value !== null));
	const bestIndex = best === null ? -1 : ranked.findIndex(value => value.score === best);
	return freeze({
		key: request.key,
		widthFamily: freeze({ source: crossSections.length ? 'tee-badge-exposed-cross-sections' : 'UNKNOWN', candidates: freeze(ranked), selectedWidthsPx: freeze(selected), sampledCrossSections: crossSections.length, boundaryOptimum: bestIndex === 0 || bestIndex === ranked.length - 1, supportThreshold }),
		reference: freeze({ mean: referenceMean, samples: freeze(referenceSamples), exposedSamples: referenceSamples.length, tolerance: referenceMean === null ? null : Math.max(...referenceSamples.map(sample => Math.abs(sample - referenceMean))) })
	});
}
function ensureRegistration(board: PxC): void {
	if (!registered.has(board)) { board.register(PROFILE_FN, deriveMaterial); board.register(POSE_PROFILE_FN, derivePoseRead); registered.add(board); }
}
function contactNormal(source: MatrixSource, point: MatrixPoint, masks: readonly FourLaneOccluder[]): MatrixContactNormal {
	const at = (x: number, y: number) => {
		const sample = bilinear(source.image, x, y, masks);
		return sample === null ? null : luminance(sample);
	};
	const west = at(point.xPx - 1, point.yPx), east = at(point.xPx + 1, point.yPx), north = at(point.xPx, point.yPx - 1), south = at(point.xPx, point.yPx + 1);
	if ([west, east, north, south].some(value => value === null)) return freeze({ x: null, y: null, magnitude: null, confidence: 'UNKNOWN' as const });
	const gx = (east as number) - (west as number), gy = (south as number) - (north as number), magnitude = Math.hypot(gx, gy);
	return freeze({ x: magnitude ? gx / magnitude : 0, y: magnitude ? gy / magnitude : 0, magnitude, confidence: magnitude >= 3 ? 'measured' as const : 'weak' as const });
}
function derivePoseRead(request: PoseRequest): MatrixProfileReading {
	const { source, material, position: point, heading: vector, occluders, knobs } = request;
	const hypotheses = material.widthFamily.candidates.map(candidate => hypothesis(source, point, vector, candidate.widthPx, occluders, knobs));
	const preferredWidth = material.widthFamily.selectedWidthsPx
		.map(width => material.widthFamily.candidates.find(candidate => candidate.widthPx === width))
		.filter((candidate): candidate is MatrixWidthHypothesis => candidate !== undefined)
		.sort((a, b) => (b.score ?? -Infinity) - (a.score ?? -Infinity))[0]?.widthPx;
	const preferred = hypotheses.find(value => value.widthPx === preferredWidth) ?? hypotheses.find(value => value.score !== null) ?? hypotheses[0];
	const center = band(source.image, point, vector, 0, occluders, knobs);
	const leftSigned = preferred?.leftSigned ?? null, rightSigned = preferred?.rightSigned ?? null;
	const masked = blocked(point, occluders);
	const availability = leftSigned !== null && rightSigned !== null ? 'paired' : leftSigned !== null || rightSigned !== null ? 'one-sided' : 'UNKNOWN';
	const status: MatrixReadingStatus = masked || center.unknown ? 'UNKNOWN' : availability !== 'UNKNOWN' ? availability : 'loss';
	const centerReferenceError = center.mean === null || material.reference.mean === null ? null : Math.abs(center.mean - material.reference.mean);
	const supported = availability !== 'paired' || preferred?.broadCoherence === null || centerReferenceError === null || material.widthFamily.supportThreshold === null || material.reference.tolerance === null
		? null
		: preferred.broadCoherence >= material.widthFamily.supportThreshold && centerReferenceError <= material.reference.tolerance;
	const probes = PROBE_OFFSETS.flatMap(offset => [
		band(source.image, point, vector, -offset, occluders, knobs),
		band(source.image, point, vector, offset, occluders, knobs)
	]);
	return freeze({ xPx: point.xPx, yPx: point.yPx, heading: vector, status, availability, supported, supportThreshold: material.widthFamily.supportThreshold, centerTolerance: material.reference.tolerance, leftSigned, rightSigned, center, centerReferenceError, centerResemblance: centerReferenceError === null ? null : Math.max(0, 1 - centerReferenceError / 255), widthHypotheses: freeze(hypotheses), probeOffsetsPx: PROBE_OFFSETS, probes: freeze(probes), normal: contactNormal(source, point, occluders), masked });
}

/**
 * Materializes the source profile once at a content-addressed PxC address.
 * Later variants share the immutable arrays and counters through this board.
 */
export function createMatrixMaterials(input: CreateMatrixMaterialsInput): MatrixMaterials {
	const knobs = input.sensorKnobs ?? DEFAULT_FOUR_LANE_SENSOR_KNOBS;
	const occluders = freeze([input.badgeMask, ...(input.occluders ?? [])]);
	const key = sha(canonical({ revision: input.calculationRevision ?? REVISION, source: input.source.contentHash, frame: input.source.frame, dimensions: [input.source.image.width, input.source.image.height], seed: input.seed, badgeMask: input.badgeMask, occluders: input.occluders ?? [], knobs, probeOffsetsPx: PROBE_OFFSETS }));
	const materialAddress = `matrix.material.${key}`;
	const cache = input.cache ?? createMatrixMaterialCache();
	cache.counters.requests++;
	const hit = input.board.has(materialAddress);
	if (hit) cache.counters.hits++; else cache.counters.misses++;
	ensureRegistration(input.board);
	const material = hit ? input.board.get<MatrixMaterial>(materialAddress) : input.board.call(PROFILE_FN, { key, source: input.source, seed: input.seed, occluders, knobs });
	if (!hit) { input.board.set(materialAddress, material); cache.counters.writes++; }
	const read = (position: MatrixPoint, heading: MatrixHeading): MatrixProfileReading => {
		const poseKey = sha(canonical({ material: key, position, heading }));
		const poseAddress = `matrix.material.profile.${poseKey}`;
		if (input.board.has(poseAddress)) { cache.counters.profileHits++; return input.board.get<MatrixProfileReading>(poseAddress); }
		cache.counters.profileMisses++;
		const reading = input.board.call(POSE_PROFILE_FN, { source: input.source, material, position, heading, occluders, knobs });
		input.board.set(poseAddress, reading); cache.counters.profileWrites++;
		return reading;
	};
	// Return a frozen counter snapshot; freezing the caller's mutable cache would
	// make a later variant fail before it can record its cache hit.
	return freeze({ key, materialAddress, image: input.source.image, widthFamily: material.widthFamily, reference: material.reference, cache: freeze({ hit, counters: { ...cache.counters } }), read });
}
