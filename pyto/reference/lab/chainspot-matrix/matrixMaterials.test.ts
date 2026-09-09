import { describe, expect, test } from 'vitest';
import { createExecBoard } from '@chainspot/alg/exec/board';
import type { RgbaImage } from '@chainspot/alg/detectors/threeFactor/types';
import { createMatrixMaterialCache, createMatrixMaterials } from '../../scripts/chainspot-lab/sweep/matrix/materials';

function stripe(width = 96, height = 64, base = 40, ribbon = 110): RgbaImage {
	const data = new Uint8Array(width * height * 4);
	for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
		const value = y >= 22 && y <= 42 ? ribbon : base;
		const index = (y * width + x) * 4; data[index] = data[index + 1] = data[index + 2] = value; data[index + 3] = 255;
	}
	return { width, height, data };
}
function material(board = createExecBoard(), image = stripe(), revision = 'r1') {
	return createMatrixMaterials({ board, source: { contentHash: 'synthetic-content', frame: 'source-image-px', image }, seed: { tee: { xPx: 10, yPx: 32 }, badge: { xPx: 80, yPx: 32 } }, badgeMask: { bboxX: 76, bboxY: 28, bboxW: 8, bboxH: 8 }, calculationRevision: revision, cache: createMatrixMaterialCache() });
}

describe('matrix source materials', () => {
	test('keeps bilinear raw, paired inward edge signs and a measured family on a soft straight ribbon', () => {
		const result = material();
		const read = result.read({ xPx: 34.5, yPx: 32 }, { x: 1, y: 0 });
		expect(read.status).toBe('paired');
		expect(read.leftSigned).toBeGreaterThan(0);
		expect(read.rightSigned).toBeGreaterThan(0);
		expect(read.probeOffsetsPx).toContain(12);
		expect(result.widthFamily.selectedWidthsPx.some(width => Math.abs(width - 20) <= 2)).toBe(true);
		expect(read.centerReferenceError).toBe(0);
	});
	test('does not turn a luminance slope or badge ownership into fabricated support', () => {
		const image = stripe();
		for (let y = 0; y < image.height; y++) for (let x = 0; x < image.width; x++) {
			const index = (y * image.width + x) * 4; image.data[index] = image.data[index + 1] = image.data[index + 2] = 30 + y;
		}
		const result = createMatrixMaterials({ board: createExecBoard(), source: { contentHash: 'slope', frame: 'source-image-px', image }, seed: { tee: { xPx: 10, yPx: 32 }, badge: { xPx: 80, yPx: 32 } }, badgeMask: { bboxX: 50, bboxY: 20, bboxW: 12, bboxH: 24 } });
		const slope = result.read({ xPx: 32, yPx: 32 }, { x: 1, y: 0 });
		expect(slope.widthHypotheses.some(hypothesis => (hypothesis.score ?? 0) < 0)).toBe(true);
		const masked = result.read({ xPx: 55, yPx: 32 }, { x: 1, y: 0 });
		expect(masked.status).toBe('UNKNOWN');
		expect(masked.center.mean).toBeNull();
	});
	test('memoizes actual immutable profile arrays on PxC and invalidates them by calculation revision', () => {
		const board = createExecBoard(), cache = createMatrixMaterialCache(), image = stripe();
		const args = { board, source: { contentHash: 'same-source', frame: 'source-image-px' as const, image }, seed: { tee: { xPx: 10, yPx: 32 }, badge: { xPx: 80, yPx: 32 } }, badgeMask: { bboxX: 76, bboxY: 28, bboxW: 8, bboxH: 8 }, cache };
		const first = createMatrixMaterials({ ...args, calculationRevision: 'A' });
		const second = createMatrixMaterials({ ...args, calculationRevision: 'A' });
		const changed = createMatrixMaterials({ ...args, calculationRevision: 'B' });
		expect(second.cache.hit).toBe(true);
		expect(first.read({ xPx: 35, yPx: 32 }, { x: 1, y: 0 })).toEqual(second.read({ xPx: 35, yPx: 32 }, { x: 1, y: 0 }));
		expect(changed.key).not.toBe(first.key);
		expect(cache.counters).toEqual({ requests: 3, hits: 1, misses: 2, writes: 2, profileHits: 1, profileMisses: 1, profileWrites: 1 });
		expect(Object.isFrozen(board.get(first.materialAddress))).toBe(true);
	});
	test('keys every occluder, keeps canonical coordinates caller-owned, and has cached/uncached pose parity', () => {
		const image = stripe(), seed = { tee: { xPx: 10, yPx: 32 }, badge: { xPx: 80, yPx: 32 } }, badgeMask = { bboxX: 76, bboxY: 28, bboxW: 8, bboxH: 8 };
		const cached = createMatrixMaterials({ board: createExecBoard(), source: { contentHash: 'frame-content', frame: 'lab-canonical-px', image }, seed, badgeMask, occluders: [{ bboxX: 2, bboxY: 2, bboxW: 1, bboxH: 1 }] });
		const uncached = createMatrixMaterials({ board: createExecBoard(), source: { contentHash: 'frame-content', frame: 'lab-canonical-px', image }, seed, badgeMask, occluders: [{ bboxX: 3, bboxY: 2, bboxW: 1, bboxH: 1 }] });
		const a = cached.read({ xPx: 35, yPx: 32 }, { x: 1, y: 0 });
		const b = cached.read({ xPx: 35, yPx: 32 }, { x: 1, y: 0 });
		expect(a).toBe(b);
		expect(a).toEqual(uncached.read({ xPx: 35, yPx: 32 }, { x: 1, y: 0 }));
		expect(a.yPx).toBe(32);
		expect(cached.key).not.toBe(uncached.key);
	});
	test('retains a strongest width even when it occurs late in the physical-width scan', () => {
		const image = stripe(128, 160, 25, 115);
		// Make an 80px-wide straight material; its optimum is well past the
		// first several 2px width candidates.
		for (let y = 0; y < image.height; y++) for (let x = 0; x < image.width; x++) {
			const value = y >= 40 && y <= 120 ? 115 : 25;
			const index = (y * image.width + x) * 4; image.data[index] = image.data[index + 1] = image.data[index + 2] = value;
		}
		const result = createMatrixMaterials({ board: createExecBoard(), source: { contentHash: 'wide', frame: 'source-image-px', image }, seed: { tee: { xPx: 12, yPx: 80 }, badge: { xPx: 116, yPx: 80 } }, badgeMask: { bboxX: 112, bboxY: 76, bboxW: 8, bboxH: 8 } });
		const candidates = result.widthFamily.candidates;
		const strongest = candidates.reduce((best, candidate) => (candidate.score ?? -Infinity) > (best.score ?? -Infinity) ? candidate : best);
		expect(candidates.indexOf(strongest)).toBeGreaterThan(6);
		expect(result.widthFamily.selectedWidthsPx).toContain(strongest.widthPx);
		expect(result.widthFamily.selectedWidthsPx[0]).toBe(strongest.widthPx);
	});
});
