/** Small, repo-local work-item contracts.  These types deliberately keep
 * declared intent separate from facts produced by execution or a human. */

export type WorkStatus = "queued" | "active" | "review";
export type TargetKind = "calculation" | "tick" | "pcr";
export type DependencyPredicate = "verified" | "accepted" | "promoted";

export interface WorkTarget {
  kind: TargetKind;
  /** An existing execution identity: fn.* for calculations, tick.* for Ticks, pcr.* for PCRs. */
  identity: string;
  /** For a Tick target, the composition and declared Tick name, when known. */
  composition?: string;
  name?: string;
}

export type RecordReference =
  | string
  | {
      id?: string;
      path?: string;
      at?: string;
      pointer?: string;
    };

export interface Requirement {
  id: string;
  text: string;
}

export interface Dependency {
  item: string;
  requires: DependencyPredicate;
}

export interface Checkpoint {
  id: string;
  /** The exact implementation/material subject of this candidate. */
  commit: string;
  observationRef: RecordReference;
  verificationRefs: Record<string, RecordReference>;
  /** Optional retained execution and inspection references. */
  executionRefs?: RecordReference[];
  inspectionRefs?: RecordReference[];
}

export interface AcceptanceReference {
  ref: RecordReference;
  human: string;
  subjectCommit: string;
  requirementScope: string[] | "all";
  disposition: "accepted" | "rejected";
  source: RecordReference;
  synthetic?: boolean;
}

export interface PromotionReference {
  ref: RecordReference;
  subjectCommit: string;
  source: string;
  destination: string;
  synthetic?: boolean;
}

export interface WorkLocation {
  component: string;
  experiment?: string;
}

export interface WorkItem {
  schemaVersion: 1;
  id: string;
  outcome: string;
  location: WorkLocation;
  target: WorkTarget;
  requirements: Requirement[];
  dependencies: Dependency[];
  agent?: string;
  status: WorkStatus;
  blockers: string[];
  checkpoints: Checkpoint[];
  acceptanceRefs: AcceptanceReference[];
  promotionRefs: PromotionReference[];
  resume: string;
}

export type EvidenceResult = "passed" | "failed" | "unknown";

export interface VerificationRecord {
  id: string;
  itemId: string;
  checkpointId: string;
  subjectCommit: string;
  /** A calculation, Tick, PCR, or inspection record—not a task hierarchy. */
  recordKind: TargetKind | "inspection";
  target: WorkTarget;
  requirementResults: Record<string, EvidenceResult>;
  synthetic?: boolean;
  label?: string;
}

export interface AcceptanceFact {
  id: string;
  itemId: string;
  subjectCommit: string;
  requirementScope: string[] | "all";
  disposition: "accepted" | "rejected";
  human: string;
  source: RecordReference;
  synthetic?: boolean;
}

export interface PromotionFact {
  id: string;
  itemId: string;
  subjectCommit: string;
  source: string;
  destination: string;
  synthetic?: boolean;
}

export interface BoardFacts {
  verificationRecords?: VerificationRecord[];
  acceptanceRecords?: AcceptanceFact[];
  promotionRecords?: PromotionFact[];
  /**
   * The already-declared execution compositions.  This is the source for
   * Tick membership and shared-Calculation fanout; items never repeat it.
   */
  compositions?: Array<{
    identity: string;
    pql: {
      PrincipleComponentRender: string;
      Ticks: Array<{
        name: string;
        Calculations: Array<{ call: string; with?: Record<string, string>; args?: Record<string, unknown>; into: string }>;
      }>;
    };
  }>;
  /** Synthetic fixture facts are accepted only when this explicit demo flag is set. */
  allowSynthetic?: boolean;
  /** If provided, dependency readiness also checks these current surfaces. */
  availableSurfaces?: string[];
}

export interface WorkItemUpdatePatch {
  agent?: string;
  status?: WorkStatus;
  blockers?: string[];
  resume?: string;
}

export type UpdateFailure =
  | { ok: false; reason: "not_found"; items: readonly WorkItem[] }
  | {
      ok: false;
      reason: "revision_mismatch";
      items: readonly WorkItem[];
      currentRevision: string;
    }
  | { ok: false; reason: "invalid_patch"; items: readonly WorkItem[]; message: string };

export type UpdateSuccess = {
  ok: true;
  items: readonly WorkItem[];
  item: WorkItem;
  previousRevision: string;
};

export type UpdateResult = UpdateSuccess | UpdateFailure;

const PATCH_KEYS = new Set(["agent", "status", "blockers", "resume"]);

/**
 * Pure compare-and-update for exactly one item. The revision is a content
 * fingerprint, so raw edits are detected; unaddressed item references are
 * retained and acceptance/promotion/evidence fields cannot be patched.
 */
export function updateWorkItem(
  items: readonly WorkItem[],
  id: string,
  expectedRevision: string,
  patch: WorkItemUpdatePatch,
): UpdateResult {
  const index = items.findIndex((item) => item.id === id);
  if (index < 0) return { ok: false, reason: "not_found", items };

  const current = items[index];
  const currentRevision = workItemRevision(current);
  if (currentRevision !== expectedRevision) {
    return { ok: false, reason: "revision_mismatch", items, currentRevision };
  }

  for (const key of Object.keys(patch)) {
    if (!PATCH_KEYS.has(key)) {
      return {
        ok: false,
        reason: "invalid_patch",
        items,
        message: `Field '${key}' is not an ordinary work-item update field`,
      };
    }
  }
  if (patch.status && !["queued", "active", "review"].includes(patch.status)) {
    return { ok: false, reason: "invalid_patch", items, message: "Invalid status" };
  }

  const next: WorkItem = {
    ...current,
    ...patch,
    blockers: patch.blockers ? [...patch.blockers] : [...current.blockers],
  };
  const nextItems = items.slice();
  nextItems[index] = next;
  return { ok: true, items: nextItems, item: next, previousRevision: currentRevision };
}

function stable(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value as Record<string, unknown>)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stable((value as Record<string, unknown>)[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

/** Stable content fingerprint suitable for an expected-revision guard. */
export function workItemRevision(item: WorkItem): string {
  let hash = 2166136261;
  for (const char of stable(item)) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

export function recordReferenceKey(ref: RecordReference): string {
  if (typeof ref === "string") return ref;
  if (ref.id) return ref.id;
  return [ref.path, ref.at, ref.pointer].filter(Boolean).join("#");
}

export function checkpointFor(item: WorkItem): Checkpoint | undefined {
  return item.checkpoints[item.checkpoints.length - 1];
}

/** Lightweight shape validation; external record contents are resolved later. */
export function validateWorkItem(item: WorkItem): string[] {
  const errors: string[] = [];
  if (item.schemaVersion !== 1) errors.push(`${item.id}: unsupported schemaVersion`);
  if (!item.id) errors.push("item: missing id");
  if (!item.outcome) errors.push(`${item.id}: missing outcome`);
  if (!["calculation", "tick", "pcr"].includes(item.target?.kind)) {
    errors.push(`${item.id}: unknown target kind`);
    return errors;
  }
  const targetPrefix = item.target.kind === "calculation" ? "fn" : item.target.kind === "tick" ? "tick" : "pcr";
  if (!new RegExp(`^${targetPrefix}\\.[A-Za-z0-9_.-]+$`).test(item.target?.identity ?? "")) {
    errors.push(`${item.id}: ${item.target?.kind ?? "unknown"} target identity must use ${targetPrefix}.*`);
  }
  const requirementIds = new Set<string>();
  for (const requirement of item.requirements) {
    if (requirementIds.has(requirement.id)) errors.push(`${item.id}: duplicate requirement ${requirement.id}`);
    requirementIds.add(requirement.id);
  }
  for (const dependency of item.dependencies) {
    if (dependency.item === item.id) errors.push(`${item.id}: self dependency`);
  }
  for (const acceptance of item.acceptanceRefs) {
    if (!acceptance.human || !acceptance.subjectCommit || !acceptance.source) {
      errors.push(`${item.id}: acceptance reference is missing attribution or subject`);
    }
  }
  for (const promotion of item.promotionRefs) {
    if (!promotion.subjectCommit || !promotion.source || !promotion.destination) {
      errors.push(`${item.id}: promotion reference is incomplete`);
    }
  }
  return errors;
}
