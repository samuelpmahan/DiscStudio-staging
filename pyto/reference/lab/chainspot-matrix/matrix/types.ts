/** Contracts shared by the matrix planner, receipts, and gallery builders. */

export type MatrixJobStatus = 'pending' | 'running' | 'complete' | 'failed' | 'missing-prerequisite' | 'unsupported';

export interface MatrixCase {
	readonly id: string;
	readonly course?: string;
	readonly capture?: string;
	readonly image?: string;
	readonly source?: string;
	readonly metadata?: Readonly<Record<string, unknown>>;
	/** Names of inputs which must exist before this case can run. */
	readonly prerequisites?: readonly string[];
}

export interface MatrixVariant {
	readonly id: string;
	readonly implementation?: string;
	readonly params?: Readonly<Record<string, unknown>>;
	readonly metadata?: Readonly<Record<string, unknown>>;
}

export type GalleryCategory = 'edge_loss' | 'width_boundary' | 'branch_reacquired' | 'paused' | 'unresolved';

export interface MatrixManifest {
	readonly version?: number;
	readonly id?: string;
	readonly name?: string;
	readonly calculationRevision?: string;
	readonly sourceRevision?: string;
	readonly cases?: readonly MatrixCase[];
	readonly variants: readonly MatrixVariant[];
	readonly measurements?: readonly string[];
	readonly galleryGroups?: readonly GalleryCategory[];
	/** Inputs already materialized by the caller; omitted means no prerequisites are available. */
	readonly availablePrerequisites?: readonly string[];
	readonly metadata?: Readonly<Record<string, unknown>>;
}

export interface MatrixJob {
	readonly key: string;
	readonly caseId: string;
	readonly variantId: string;
	readonly case: MatrixCase;
	readonly variant: MatrixVariant;
	readonly status: MatrixJobStatus;
	readonly missingPrerequisites: readonly string[];
}

export interface MatrixProgressRow {
	readonly key: string;
	readonly caseId: string;
	readonly variantId: string;
	readonly status: MatrixJobStatus;
	readonly completed: number;
	readonly total: number;
	readonly message?: string;
}

export interface MatrixReceipt<T = unknown> {
	readonly schema: 'chainspot-matrix-receipt@1';
	readonly runId: string;
	readonly createdAt: string;
	readonly updatedAt: string;
	readonly manifestHash: string;
	readonly jobs: readonly MatrixJob[];
	readonly progress: readonly MatrixProgressRow[];
	readonly results: Readonly<Record<string, T>>;
	readonly errors: Readonly<Record<string, string>>;
}

export interface EvidenceObservation {
	readonly key?: string;
	readonly caseId?: string;
	readonly variantId?: string;
	readonly edgeSupport?: 'paired' | 'left' | 'right' | 'none' | 'unknown';
	readonly previousEdgeSupport?: 'paired' | 'left' | 'right' | 'none' | 'unknown';
	readonly widthPx?: number | null;
	readonly widthMinPx?: number | null;
	readonly widthMaxPx?: number | null;
	readonly widthAtBoundary?: boolean;
	readonly branchReacquired?: boolean;
	readonly paused?: boolean;
	readonly unresolved?: boolean;
	readonly stopReason?: string;
	readonly sourceCrop?: string;
	readonly track?: readonly unknown[];
	readonly [field: string]: unknown;
}

export interface GalleryRow extends EvidenceObservation {
	readonly category: GalleryCategory;
}

export interface CacheCounters {
	readonly requests: number;
	readonly hits: number;
	readonly misses: number;
	readonly writes: number;
	readonly uniqueKeys: number;
}

export interface ParityReport {
	readonly equal: boolean;
	readonly compared: number;
	readonly mismatches: readonly { readonly key: string; readonly expected: unknown; readonly actual: unknown }[];
}
