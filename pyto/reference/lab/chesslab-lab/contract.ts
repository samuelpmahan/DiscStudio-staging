// Shared exec contract for the compiled-operation execution model
// (Wave 1A). Types only — no runtime logic lives here, so both chunks
// (A: compiler/gateway/receipts under src/exec/**; B: g0/adapters/UI) can
// depend on a stable shape from minute one, before either side's design
// has settled.
//
// R1 (browser-safe core): everything below describes DATA. Writing an
// artifact or receipt to disk is the job of an INJECTED sink the caller
// hands to executeCompiledPlan — never something a type here performs.
// This file imports nothing and reaches no I/O.

/** The five verbs an operation is allowed to be. */
export type OperationKind = 'measure' | 'transform' | 'compute' | 'decide' | 'materialize';

/**
 * Reference to a named value flowing through a compiled plan. Deliberately
 * a plain string, not a closed enum: R2 requires operations at a finer
 * grain than the existing engine units, so the slot namespace has to stay
 * open (e.g. 'badgeStage.brightMask', 'badgeStage.components',
 * 'assignment.scoring', 'assignment.selection') without this file growing
 * every time a unit gets decomposed further. Legality of who-produces-
 * before-who-consumes is enforced by the compiler's dependency walk, not
 * by the type system.
 */
export type SlotRef = string;

/**
 * One node in the operation DAG. A single engine unit (e.g. badgeStage,
 * assignment) may decompose into several OperationSpecs; `unit` carries
 * the owning unit purely as a grouping/trace-display label — it is never
 * consulted for scheduling. Ordering and legality come entirely from
 * `consumes`/`produces` plus the compiled execution list.
 */
export interface OperationSpec {
	/** unique across the whole op universe; the final C1 tiebreak when config intent doesn't otherwise order two legal ops */
	readonly id: string;
	readonly kind: OperationKind;
	/** GateId from threeFactor/features/types, kept as a plain string here so this file has zero dependency on the threeFactor package */
	readonly gate: string;
	/** owning engine unit — grouping/trace label only, never a scheduling input */
	readonly unit: string;
	readonly consumes: readonly SlotRef[];
	readonly produces: readonly SlotRef[];
	/**
	 * The real named calculations bound behind this inspection boundary.
	 * These are descriptive fn.* addresses, not another execution registry:
	 * OperationRuntime remains the sole authority that binds and runs them.
	 */
	readonly calculations?: readonly `fn.${string}`[];
	/** Opt-in while legacy declarations are repaired: reject any declared/actual access mismatch. */
	readonly accessConformance?: 'exact';
	/** ABFeature ids this operation reads enabled/knobs from, if any */
	readonly features?: readonly string[];
	/** knob names (within `features`) this operation's behavior is sensitive to — receipts/debugging only */
	readonly knobBindings?: readonly string[];
	readonly note?: string;
}

/** One executable calculation frozen at the moment a Tick ran. */
export interface FrozenCalculation {
	/** Stable, human-readable address for the real calculation. */
	readonly address: `fn.${string}`;
	/** SHA-256 of the bound executable function body in this runtime build. */
	readonly implementationHash: string;
	/** Honest scope of implementationHash. It is not a transitive source or dependency hash. */
	readonly identityScope: 'runtime-function-body';
	readonly limitation: 'called helpers, constants, templates, and assets are not covered';
}

/** How one PxC address changed while a Tick ran. */
export interface PxWriteTestimony {
	readonly address: SlotRef;
	readonly kind: 'new-address' | 'refinement' | 'replacement';
}

/** Kinds of artifacts an operation may hand to the sink. */
export type ArtifactKind =
	| 'rgba'
	| 'mask'
	| 'scalarField'
	| 'orientationField'
	| 'componentSet'
	| 'candidateSet'
	| 'badgeEvidence'
	| 'm1Representation'
	| 'm2Representation'
	| 'polyline'
	| 'measurementTable';

/**
 * Content-addressed reference to an artifact the sink has stored. `uri` is
 * sink-defined (a file:// path from the Node sink, an in-memory handle
 * from a browser/collector sink) — the exec core never interprets it,
 * only carries it through the receipt.
 */
/** Pixel dimensions of a raster-shaped payload (rgba/mask/scalarField/
 * orientationField), in image-px. Present only when the producing extractor
 * had them in hand; the payload bytes themselves never carry shape. */
export interface RasterDims {
	readonly width: number;
	readonly height: number;
}

export interface ArtifactRef {
	readonly id: string;
	readonly kind: ArtifactKind;
	readonly sha256: string;
	readonly uri: string;
	/** Optional. Set for raster kinds whose extractor knew the shape. A
	 * consumer receiving undefined MUST NOT infer dimensions from byte
	 * length -- decline to rasterize instead. */
	readonly dims?: RasterDims;
}

/** A single named numeric observation captured during an operation's run. */
export interface Probe {
	readonly name: string;
	readonly value: number;
}

/**
 * Per-operation execution record. `declared*` comes from the OperationSpec;
 * `actual*` comes from what the operation really touched on the evidence
 * board while running. The two diverging is a conformance failure the
 * gateway surfaces rather than silently accepting.
 */
export interface Receipt {
	readonly opId: string;
	/** The fn.* calculations the production gateway actually bound for this Tick. */
	readonly frozenCalculations: readonly FrozenCalculation[];
	readonly startedAtMs: number;
	readonly durationMs: number;
	readonly declaredConsumes: readonly SlotRef[];
	readonly declaredProduces: readonly SlotRef[];
	readonly actualConsumes: readonly SlotRef[];
	readonly actualProduces: readonly SlotRef[];
	/** Collision-visible PxC writes; replacements are never hidden as ordinary output. */
	readonly writes: readonly PxWriteTestimony[];
	readonly probes: readonly Probe[];
	readonly artifacts: readonly ArtifactRef[];
}

/**
 * A Tick is the existing gateway Receipt understood as inspection testimony:
 * exact addresses in, frozen calculations, exact addresses out.  It adds no
 * execution authority and deliberately has no run() method.
 */
export type TickTestimony = Receipt;

/**
 * Placeholder import point for the canonical input type (resolved config +
 * image + params — the thing planFingerprint hashes alongside op
 * universe). Landing as `unknown` so downstream code (Chunk B, the
 * compiler) has a stable name to import today; narrows to a real shape in
 * a follow-up commit once the compiler's needs are settled. Do not widen
 * this ad hoc from a consuming file — narrow it here.
 */
export type CanonicalInput = unknown;
