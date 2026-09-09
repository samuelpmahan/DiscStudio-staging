/**
 * Manifest-driven LAB matrix. Registered branching variants use the
 * branching variants compile the exported default-OFF ABFeature and execute it
 * through executeABFeatureSet, never a parallel CLI/probe runner.
 */
import { createHash, randomUUID } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import { basename, dirname, resolve } from 'node:path';
import { PNG } from 'pngjs';
import { decodeNodeFile } from '@chainspot/alg/adapters/node';
import {
	createLabBranchingFeatureSet,
	type LabBranchingInput,
	type LabBranchingResult
} from '@chainspot/alg/experiments/labBranching';
import { createExecBoard, compileABFeatureSet, executeABFeatureSet } from '@chainspot/alg/exec';
import { nullFeatureContext, type FeatureContext } from '@chainspot/alg/detectors/threeFactor/features/types';
import { createMatrixMaterials, createMatrixMaterialCache, type MatrixProfileReading } from './matrix/materials';
import { formatProgressRows, classifyEvidenceCategories } from './matrix/evidence';
import { materializeMatrixJobs, createMatrixReceipt, updateMatrixReceipt } from './matrix/manifest';
import type { MatrixManifest as NativeManifest } from './matrix/types';

type Seed = {
	readonly hole: number;
	readonly badge: { readonly xPx: number; readonly yPx: number; readonly bboxX: number; readonly bboxY: number; readonly bboxW: number; readonly bboxH: number };
	readonly tee: { readonly xPx: number; readonly yPx: number };
	readonly teeSource?: string;
};
type Variant = {
	readonly id: string;
	readonly kind: 'branching' | 'sweep';
	readonly mode?: 'fixed' | 'poisson' | 'reflection';
	readonly enabled?: boolean;
	readonly sliceSteps?: number;
	readonly note?: string;
	readonly supportFactor?: number;
	readonly centerFactor?: number;
};
type MatrixManifest = {
	readonly schemaVersion: 1;
	readonly id: string;
	readonly source: string;
	readonly seedInputs: string;
	readonly normalSweepConfig?: string;
	readonly variants: readonly Variant[];
	readonly galleryGroups?: readonly string[];
};
type SeedFile = { readonly width: number; readonly height: number; readonly sourceSha256?: string; readonly seeds: readonly Seed[] };

type EdgeSample = {
	readonly xPx: number; readonly yPx: number; readonly leftSigned: number; readonly rightSigned: number;
	readonly centerResemblance: number; readonly widthHypotheses: readonly { readonly widthPx: number; readonly score: number }[];
	readonly support: 'paired' | 'one-sided' | 'loss' | 'UNKNOWN'; readonly rawAvailability?: string;
};
type MatrixEvent = {
	readonly id: string; readonly parentId: string | null; readonly xPx: number; readonly yPx: number;
	readonly heading: { readonly x: number; readonly y: number }; readonly verdict: string; readonly reason?: string;
	readonly measurements?: readonly { readonly name: string; readonly value: number }[]; readonly profile?: unknown; readonly sample: EdgeSample; readonly tags: readonly string[]; readonly proposalId?: string; readonly target?: { readonly x: number; readonly y: number };
};
type JobReceipt = {
	readonly schemaVersion: 1; readonly jobKey: string; readonly runId: string; readonly matrixId: string;
	readonly source: { readonly path: string; readonly sha256: string; readonly frame: string; readonly widthPx: number; readonly heightPx: number };
	readonly implementation: { readonly revision?: string; readonly kind: string; readonly planFingerprint?: string; readonly manifestHash?: string };
	readonly case: { readonly course: string; readonly hole: number; readonly seedProvenance: string };
	readonly variant: Variant; readonly status: string; readonly events: readonly MatrixEvent[];
	readonly groups: readonly string[]; readonly continuation?: string; readonly resumed: boolean; readonly reflection?: unknown;
	readonly cache: { readonly profileKey: string; readonly hit: boolean; readonly counters: { readonly profileHits: number; readonly profileMisses: number } };
	readonly receiptPath: string; readonly galleryPath: string; readonly sliceCount?: number;
};

const REPO_ROOT = resolve(dirname(new URL(import.meta.url).pathname), '../../..');
const FRAME = 'source-image-px';
const sha = (data: string | Uint8Array) => createHash('sha256').update(data).digest('hex');
function canonical(value: unknown): string {
	if (value === null || typeof value !== 'object') return JSON.stringify(value);
	if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
	const record = value as Record<string, unknown>;
	return '{' + Object.keys(record).sort().map((key) => JSON.stringify(key) + ':' + canonical(record[key])).join(',') + '}';
}
const safe = (value: string) => value.replace(/[^a-zA-Z0-9._-]+/g, '-');
function atomicJson(path: string, value: unknown): void {
	mkdirSync(dirname(path), { recursive: true });
	const temporary = path + '.' + randomUUID() + '.tmp';
	writeFileSync(temporary, JSON.stringify(value, null, 2) + '\n');
	renameSync(temporary, path);
}
type SourceSensorImage = { readonly width: number; readonly height: number; readonly data: Uint8ClampedArray };
function profileSample(reading: MatrixProfileReading, verdict?: string): EdgeSample {
	return { xPx: reading.xPx, yPx: reading.yPx,
		leftSigned: reading.leftSigned ?? Number.NaN, rightSigned: reading.rightSigned ?? Number.NaN,
		centerResemblance: reading.centerResemblance ?? Number.NaN,
		widthHypotheses: reading.widthHypotheses.map(value => ({ widthPx: value.widthPx, score: value.score ?? Number.NaN })), rawAvailability: reading.availability,
		support: verdict === 'accepted' ? 'paired' : verdict === 'rejected' ? 'loss' : verdict === 'unknown' ? 'UNKNOWN' : reading.status === 'one-sided' ? 'one-sided' : reading.status === 'loss' ? 'loss' : 'UNKNOWN' };
}
function cropGallery(image: { rgba: Uint8ClampedArray; widthPx: number; heightPx: number }, seed: Seed, events: readonly MatrixEvent[], path: string): void {
	const points = [{ x: seed.tee.xPx, y: seed.tee.yPx }, ...events.map(e => ({ x: e.xPx, y: e.yPx }))];
	const minX = Math.max(0, Math.floor(Math.min(...points.map(p => p.x)) - 36));
	const maxX = Math.min(image.widthPx - 1, Math.ceil(Math.max(...points.map(p => p.x)) + 36));
	const minY = Math.max(0, Math.floor(Math.min(...points.map(p => p.y)) - 36));
	const maxY = Math.min(image.heightPx - 1, Math.ceil(Math.max(...points.map(p => p.y)) + 36));
	const png = new PNG({ width: maxX - minX + 1, height: maxY - minY + 1 });
	for (let y = minY; y <= maxY; y++) for (let x = minX; x <= maxX; x++) {
		const from = (y * image.widthPx + x) * 4, to = ((y - minY) * png.width + x - minX) * 4;
		png.data[to] = image.rgba[from]; png.data[to + 1] = image.rgba[from + 1]; png.data[to + 2] = image.rgba[from + 2]; png.data[to + 3] = 255;
	}
	for (const event of events) {
		const x = Math.round(event.xPx - minX), y = Math.round(event.yPx - minY);
		const color = event.verdict === 'accepted' ? [0, 240, 100] : event.verdict === 'unknown' ? [255, 190, 0] : [255, 40, 40];
		for (let d = -2; d <= 2; d++) for (const [dx, dy] of [[d,0],[0,d]]) {
			const px = x + dx, py = y + dy; if (px >= 0 && py >= 0 && px < png.width && py < png.height) {
				const i = (py * png.width + px) * 4; png.data[i] = color[0]; png.data[i+1] = color[1]; png.data[i+2] = color[2];
			}
		}
	}
	mkdirSync(dirname(path), { recursive: true }); writeFileSync(path, PNG.sync.write(png));
}
function experimentContext(bindings: Record<string, { enabled: boolean; knobs: Record<string, unknown> }>): FeatureContext {
	return { ...nullFeatureContext, resolve(feature) { return bindings[feature.id] ?? nullFeatureContext.resolve(feature); } };
}
function expectedSourceSha(seedFile: SeedFile, sourceBytes: Uint8Array): void {
	if (seedFile.sourceSha256 && seedFile.sourceSha256 !== sha(sourceBytes)) throw new Error('matrix: seed file sourceSha256 does not match source bytes.');
}
async function runBranchingJob(root: string, manifest: MatrixManifest, seedFile: SeedFile, seed: Seed, variant: Variant, profileCounters: { hit: number; miss: number }, board: ReturnType<typeof createExecBoard>, materialCache: ReturnType<typeof createMatrixMaterialCache>, course = 'DashsTrack', resume = false): Promise<JobReceipt> {
	const sourcePath = resolve(manifest.source), sourceBytes = readFileSync(sourcePath), sourceHash = sha(sourceBytes);
	expectedSourceSha(seedFile, sourceBytes);
	const rasterAddress = `matrix.raster.${sourceHash}`;
	const decoded = board.has(rasterAddress) ? board.get<Awaited<ReturnType<typeof decodeNodeFile>>>(rasterAddress) : await decodeNodeFile(sourcePath);
	if (!board.has(rasterAddress)) board.set(rasterAddress, decoded);
	const image: SourceSensorImage & { readonly rgba: Uint8ClampedArray; readonly widthPx: number; readonly heightPx: number } = { width: decoded.widthPx, height: decoded.heightPx, data: decoded.rgba, rgba: decoded.rgba, widthPx: decoded.widthPx, heightPx: decoded.heightPx };
	if (image.widthPx !== seedFile.width || image.heightPx !== seedFile.height) throw new Error('matrix: source dimensions differ from seed manifest.');
	const heading = { x: seed.badge.xPx - seed.tee.xPx, y: seed.badge.yPx - seed.tee.yPx };
	const length = Math.hypot(heading.x, heading.y) || 1;
	const afterBadge = Math.max(seed.badge.bboxW ?? 0, seed.badge.bboxH ?? 0) / 2 + 4;
	const origin = { x: seed.badge.xPx + heading.x / length * afterBadge, y: seed.badge.yPx + heading.y / length * afterBadge };
	const materials = createMatrixMaterials({ board, source: { contentHash: sourceHash, frame: 'source-image-px', image }, seed: { tee: seed.tee, badge: seed.badge }, badgeMask: seed.badge, occluders: seedFile.seeds.map(entry => entry.badge), cache: materialCache, calculationRevision: 'matrix-materials-source-profile-v1' });
	const reader = (position: { x: number; y: number }, vector: { x: number; y: number }) => {
		const reading = materials.read({ xPx: position.x, yPx: position.y }, vector);
		const candidates = reading.widthHypotheses.filter(value => materials.widthFamily.selectedWidthsPx.includes(value.widthPx));
		const coherence = Math.max(...candidates.map(value => value.broadCoherence ?? Number.NEGATIVE_INFINITY));
		const supported = reading.availability === 'paired' && reading.supportThreshold !== null && reading.centerTolerance !== null && coherence >= reading.supportThreshold * (variant.supportFactor ?? 1) && (reading.centerReferenceError ?? Number.POSITIVE_INFINITY) <= reading.centerTolerance * (variant.centerFactor ?? 1);
		const status = supported ? 'visible' as const : reading.availability === 'UNKNOWN' ? 'unknown' as const : 'loss' as const;
		return { status, measurements: [
			{ name: 'leftSigned', value: reading.leftSigned ?? Number.NaN }, { name: 'rightSigned', value: reading.rightSigned ?? Number.NaN },
			{ name: 'centerReferenceError', value: reading.centerReferenceError ?? Number.NaN }, { name: 'centerResemblance', value: reading.centerResemblance ?? Number.NaN }, { name: 'supportThreshold', value: reading.supportThreshold ?? Number.NaN }, { name: 'centerTolerance', value: reading.centerTolerance ?? Number.NaN }, { name: 'selectedWidthPx', value: [...candidates].sort((a,b)=>(b.broadCoherence ?? -Infinity)-(a.broadCoherence ?? -Infinity))[0]?.widthPx ?? Number.NaN }, { name: 'selectedBroadCoherence', value: coherence }
		] };
	};
	let input: LabBranchingInput = { origin, heading, reader, sourceHash, seed: Number.parseInt(sourceHash.slice(0, 8), 16), mode: variant.mode, maxObservations: variant.sliceSteps, widthPx: materials.widthFamily.selectedWidthsPx[0] ?? 0 };
	const overrides = { 'lab.branching': { enabled: variant.enabled ?? true, knobs: { proposalRadiusPx: 18, proposalMinDistancePx: 5, proposalCount: variant.mode === 'fixed' ? 0 : 8 } } };
	const compiled = compileABFeatureSet(createLabBranchingFeatureSet(input), overrides);
	const implementationFiles = ['packages/alg/dist/experiments/labBranching.js', 'packages/alg/dist/experimental/branching.js', 'packages/alg/dist/experimental/reflectionContact.js', 'scripts/chainspot-lab/sweep/matrix.ts', 'scripts/chainspot-lab/sweep/matrix/materials.ts', 'scripts/chainspot-lab/sweep/matrix/manifest.ts', 'scripts/chainspot-lab/sweep/matrix/evidence.ts', 'scripts/chainspot-lab/sweep/matrix/types.ts'];
	const implementationRevision = sha(new Uint8Array(implementationFiles.flatMap(file => [...readFileSync(resolve(REPO_ROOT, file))])));
	const jobKey = sha(canonical({ matrix: manifest.id, course, sourceHash, seed, variant, frame: FRAME, materials: materials.key, implementation: { plan: compiled.plan.planFingerprint, revision: implementationRevision } }));
	const outDir = resolve(root, 'jobs', safe(String(seed.hole)), safe(variant.id), jobKey);
	const baseReceiptPath = resolve(outDir, 'receipt.json');
	let prior: JobReceipt | undefined = existsSync(baseReceiptPath) ? JSON.parse(readFileSync(baseReceiptPath, 'utf8')) as JobReceipt : undefined;
	const latestPath = resolve(outDir, 'resume', 'latest.json');
	if (resume && existsSync(latestPath)) prior = JSON.parse(readFileSync(latestPath, 'utf8')) as JobReceipt;
	if (!resume && prior) return prior;
	if (resume && prior?.status === 'COMPLETE') return prior;
	if (resume && prior?.continuation) input = { ...input, continuation: prior.continuation };
	const sliceCount = (prior?.sliceCount ?? 0) + 1;
	const receiptPath = resume ? resolve(outDir, 'resume', sha(prior?.continuation ?? 'initial'), 'receipt.json') : baseReceiptPath;
	if (existsSync(receiptPath)) return JSON.parse(readFileSync(receiptPath, 'utf8')) as JobReceipt;
	board.set('lab.input', input);
	const setManifest = await executeABFeatureSet(compiled, board, experimentContext(compiled.plan.bindings), { runId: jobKey, invocation: './lab sweep matrix' });
	const result = board.get<LabBranchingResult>('lab.branch.result');
	const observationsById = new Map(result.observations.map(obs => [obs.id, obs]));
	const samples = new Map(result.observations.map(obs => [obs.id, profileSample(materials.read({ xPx: obs.position.x, yPx: obs.position.y }, obs.heading), obs.status)] as const));
	const events: MatrixEvent[] = result.observations.map(obs => {
		const sample = samples.get(obs.id)!;
		const prior = obs.parentId ? samples.get(obs.parentId) : undefined;
		const parent = obs.parentId ? observationsById.get(obs.parentId) : undefined;
		const reading = materials.read({ xPx: obs.position.x, yPx: obs.position.y }, obs.heading);
		const profile = { materialKey: materials.key, center: reading.center, centerReferenceError: reading.centerReferenceError,
			probeOffsetsPx: reading.probeOffsetsPx, probes: reading.probes,
			selectedWidthProfiles: reading.widthHypotheses.filter(value => materials.widthFamily.selectedWidthsPx.includes(value.widthPx)) };
		const tags = classifyEvidenceCategories({
			edgeSupport: sample.support === 'paired' ? 'paired' : sample.support === 'loss' ? 'none' : 'unknown',
			previousEdgeSupport: prior?.support === 'paired' ? 'paired' : prior ? 'none' : undefined,
			widthAtBoundary: materials.widthFamily.boundaryOptimum,
			branchReacquired: obs.status === 'accepted' && Boolean(obs.proposalId) && parent?.proposalId !== obs.proposalId,
			paused: result.status === 'PAUSED', unresolved: obs.status !== 'accepted'
		});
		return { id: obs.id, parentId: obs.parentId, xPx: obs.position.x, yPx: obs.position.y, heading: obs.heading, verdict: obs.status,
			...(obs.reason ? { reason: obs.reason } : {}), ...(obs.proposalId ? { proposalId: obs.proposalId } : {}),
			...(obs.target ? { target: { x: obs.target.x, y: obs.target.y } } : {}), measurements: obs.measurements, profile, sample, tags };
	});
	const groups = [...new Set(events.flatMap(e => e.tags))];
	const reflection = variant.mode === 'reflection' ? { status: 'unsupported', reason: 'no-contact', unexplainedLength: 0 } : undefined;
	const galleryPath = resolve(dirname(receiptPath), 'source-crop.png'); cropGallery(image, seed, events, galleryPath);
	const receipt: JobReceipt = {
		schemaVersion: 1, jobKey, runId: jobKey, matrixId: manifest.id,
		source: { path: sourcePath, sha256: sourceHash, frame: FRAME, widthPx: image.widthPx, heightPx: image.heightPx },
		implementation: { revision: implementationRevision, kind: 'ABFeatureSet production gateway', planFingerprint: compiled.plan.planFingerprint, manifestHash: setManifest.manifestHash },
		case: { course, hole: seed.hole, seedProvenance: seed.teeSource ?? 'UNKNOWN' }, variant,
		status: result.status, events, groups, ...(reflection ? { reflection } : {}), ...(result.continuation ? { continuation: result.continuation } : {}), resumed: resume, sliceCount,
		cache: { profileKey: materials.key, hit: materials.cache.hit, counters: { profileHits: materialCache.counters.hits, profileMisses: materialCache.counters.misses } }, receiptPath, galleryPath
	};
	atomicJson(receiptPath, receipt); if (resume) atomicJson(latestPath, receipt); return receipt;
}
function groupedSummary(receipts: readonly JobReceipt[]): Record<string, { cases: string[]; variants: string[]; images: string[] }> {
	const groups: Record<string, { cases: Set<string>; variants: Set<string>; images: string[] }> = {};
	for (const receipt of receipts) for (const group of receipt.groups) {
		const entry = groups[group] ??= { cases: new Set(), variants: new Set(), images: [] };
		entry.cases.add(`${receipt.case.course}/H${receipt.case.hole}`); entry.variants.add(receipt.variant.id); entry.images.push(receipt.galleryPath);
	}
	return Object.fromEntries(Object.entries(groups).map(([tag, value]) => [tag, { cases: [...value.cases].sort(), variants: [...value.variants].sort(), images: value.images }]));
}
async function runNativeMatrix(raw: NativeManifest, rawPath: string, resume = false, selectors: readonly string[] = []): Promise<number> {
	const selection = selectors.filter(value => !['dev','all'].includes(value.toLowerCase()));
	const cases = (raw.cases ?? []).filter(entry => !selection.length || selection.some(value => {
		const hole = /^h?(\d+)$/i.exec(value);
		return hole ? Number(entry.metadata?.hole) === Number(hole[1]) : [entry.id,entry.course].some(name => name?.toLowerCase() === value.toLowerCase());
	}));
	if (!cases.length) throw new Error('matrix: selection matched no cases.');
	const hydrated: NativeManifest = { ...raw, cases: cases.map(entry => {
		const source = entry.source ?? entry.image;
		const seedInputs = entry.metadata?.seedInputs;
		return { ...entry, metadata: { ...entry.metadata,
			sourceContentHash: source && existsSync(resolve(source)) ? sha(readFileSync(resolve(source))) : 'MISSING',
			seedContentHash: typeof seedInputs === 'string' && existsSync(resolve(seedInputs)) ? sha(readFileSync(resolve(seedInputs))) : 'MISSING'
		} };
	}) };
	const jobs = materializeMatrixJobs(hydrated);
	const root = resolve(REPO_ROOT, 'artifacts', 'sweep', 'matrix', safe(raw.id ?? 'matrix'));
	const cache = createMatrixMaterialCache(), counters = { hit: 0, miss: 0 };
	const receipts: JobReceipt[] = [], rows: Record<string, unknown>[] = [];
	let execution = createMatrixReceipt(hydrated, randomUUID());
	let currentCase = '', board = createExecBoard();
	const suffix = [resume ? 'resume' : '', ...selection].filter(Boolean).map(safe).join('-');
	const summaryPath = resolve(root, suffix ? `summary-${suffix}.json` : 'summary.json');
	const save = () => atomicJson(summaryPath, { schemaVersion: 1, matrix: raw.id ?? 'matrix', manifest: rawPath, rows, jobs: receipts, execution, groups: groupedSummary(receipts), cache: cache.counters });
	for (const job of jobs) {
		const entry = job.case, params = job.variant.params ?? {}, hole = Number(entry.metadata?.hole);
		const row = { caseId: entry.id, case: entry.course ?? entry.id, hole: Number.isInteger(hole) ? hole : null, variant: job.variantId, key: job.key };
		console.log(`LAB MATRIX [${entry.id}/${job.variantId}] START`);
		try {
			if (job.missingPrerequisites.length) {
				rows.push({ ...row, status: 'missing-prerequisite', reason: job.missingPrerequisites.join(', ') });
				execution = updateMatrixReceipt(execution, job.key, { status: 'missing-prerequisite', message: job.missingPrerequisites.join(', ') });
			} else if (job.variant.implementation !== 'branching') {
				rows.push({ ...row, status: 'unsupported', reason: 'No matrix adapter registered for this implementation' });
				execution = updateMatrixReceipt(execution, job.key, { status: 'unsupported' });
			} else {
				const seedPath = entry.metadata?.seedInputs;
				if (typeof seedPath !== 'string' || !Number.isInteger(hole)) throw new Error('seedInputs and integer metadata.hole required');
				const seedFile = JSON.parse(readFileSync(resolve(seedPath), 'utf8')) as SeedFile;
				const seed = seedFile.seeds.find(item => item.hole === hole);
				if (!seed) throw new Error('Seed absent from seedInputs');
				if (currentCase !== job.caseId) { board = createExecBoard(); currentCase = job.caseId; }
				const mode = params.mode ?? 'poisson';
				if (!['fixed','poisson','reflection'].includes(String(mode))) throw new Error(`Unsupported branching mode ${mode}`);
				for (const name of ['sliceSteps','supportFactor','centerFactor']) if (params[name] !== undefined && (typeof params[name] !== 'number' || !Number.isFinite(params[name]) || Number(params[name]) <= 0)) throw new Error(`Invalid ${name}`);
				const variant: Variant = { id: job.variantId, kind: 'branching', mode: mode as Variant['mode'], sliceSteps: Number(params.sliceSteps ?? 120), supportFactor: Number(params.supportFactor ?? 1), centerFactor: Number(params.centerFactor ?? 1), enabled: true };
				const manifest: MatrixManifest = { schemaVersion: 1, id: raw.id ?? 'matrix', source: entry.source ?? entry.image ?? '', seedInputs: seedPath, variants: [variant] };
				const receipt = await runBranchingJob(root, manifest, seedFile, seed, variant, counters, board, cache, entry.course ?? entry.id, resume);
				receipts.push(receipt);
				rows.push({ ...row, status: receipt.status, receipt: receipt.receiptPath, gallery: receipt.galleryPath });
				execution = updateMatrixReceipt(execution, job.key, { status: 'complete', result: { receipt: receipt.receiptPath, probeStatus: receipt.status } });
			}
		} catch (error) {
			const reason = error instanceof Error ? error.message : String(error);
			rows.push({ ...row, status: 'failed', reason });
			execution = updateMatrixReceipt(execution, job.key, { status: 'failed', error: reason });
		}
		save();
		console.log(`LAB MATRIX [${entry.id}/${job.variantId}] ${rows.at(-1)?.status}`);
	}
	writeFileSync(resolve(root, suffix ? `progress-${suffix}.txt` : 'progress.txt'), formatProgressRows(execution.progress));
	console.log(`LAB MATRIX: rows=${rows.length} executed=${receipts.length} receipt=${summaryPath}`);
	return rows.some(row => row.status === 'failed') ? 1 : 0;
}

export async function runSweepMatrix(args: readonly string[]): Promise<number> {
	const [keyword, matrixPath, ...rawSelectors] = args;
	const resume = rawSelectors.includes('--resume');
	const selectors = rawSelectors.filter(value => value !== '--resume');
	if (keyword !== 'matrix' || !matrixPath) throw new Error('Usage: lab sweep matrix MATRIX.json [dev|demo|all|COURSE]');
	const raw = JSON.parse(readFileSync(resolve(matrixPath), 'utf8')) as MatrixManifest & { cases?: readonly any[] };
	if (raw.cases) return runNativeMatrix(raw as unknown as NativeManifest, resolve(matrixPath), resume, selectors);
	const manifest = raw;
	if (manifest.schemaVersion !== 1 || !manifest.variants?.length) throw new Error('matrix: unsupported or incomplete manifest.');
	const seedFile = JSON.parse(readFileSync(resolve(manifest.seedInputs), 'utf8')) as SeedFile;
	const holeSelector = selectors.map(value => /^h?(\d+)$/i.exec(value)).find((match): match is RegExpExecArray => match !== null);
	const selectedSeeds = holeSelector ? seedFile.seeds.filter(seed => seed.hole === Number(holeSelector[1])) : seedFile.seeds;
	if (holeSelector && selectedSeeds.length === 0) throw new Error(`matrix: no seed for H${holeSelector[1]}.`);
	const root = resolve(REPO_ROOT, 'artifacts', 'sweep', 'matrix', safe(manifest.id));
	const counters = { hit: 0, miss: 0 }, receipts: JobReceipt[] = [];
	const matrixBoard = createExecBoard(), materialCache = createMatrixMaterialCache();
	const selected = selectors.length === 0 || selectors.some(s => ['dev', 'all', 'dashs', 'dashstrack'].includes(s.toLowerCase()));
	if (selected || holeSelector) for (const seed of selectedSeeds) for (const variant of manifest.variants.filter(v => v.kind === 'branching')) {
		console.log(`LAB MATRIX [H${seed.hole}/${variant.id}] START`);
		try { const receipt = await runBranchingJob(root, manifest, seedFile, seed, variant, counters, matrixBoard, materialCache); receipts.push(receipt); console.log(`LAB MATRIX [H${seed.hole}/${variant.id}] ${receipt.status} ${receipt.galleryPath}`); }
		catch (error) { console.log(`LAB MATRIX [H${seed.hole}/${variant.id}] FAIL ${error instanceof Error ? error.message : String(error)}`); }
	}
	const summary = { schemaVersion: 1, matrix: manifest.id, selectors: selectors.length ? selectors : ['dev'], jobs: receipts, groups: groupedSummary(receipts), uniqueCases: [...new Set(receipts.map(r => r.case.hole))].sort((a,b)=>a-b), variantCount: new Set(receipts.map(r => r.variant.id)).size, cache: counters };
	atomicJson(resolve(root, 'summary.json'), summary);
	console.log(`LAB MATRIX: cases=${summary.uniqueCases.length} variants=${summary.variantCount} jobs=${receipts.length}; gallery=${resolve(root, 'summary.json')}`);
	return receipts.length === selectedSeeds.length * manifest.variants.filter(v => v.kind === 'branching').length ? 0 : 1;
}
