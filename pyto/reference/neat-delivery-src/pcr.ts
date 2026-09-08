import { CalculationInvocation, PartRead, PartWrite, PxC } from "./pxc.js";
import { PqlRunResult, TickRunResult } from "./pql.js";

export interface TickDeclaration {
  readonly id: string;
  readonly label?: string;
}

export interface PcrDefinition {
  readonly id: string;
  readonly ticks: ReadonlyArray<TickDeclaration>;
}

export function definePcr(id: string, ticks: ReadonlyArray<TickDeclaration | string>): PcrDefinition {
  if (!id.trim()) throw new Error("PCR identity cannot be empty");
  const declarations = ticks.map((tick) => (typeof tick === "string" ? { id: tick } : tick));
  const ids = new Set<string>();
  declarations.forEach((tick) => {
    if (!tick.id.trim()) throw new Error("PCR Tick identity cannot be empty");
    if (ids.has(tick.id)) throw new Error(`Duplicate PCR Tick identity: ${tick.id}`);
    ids.add(tick.id);
  });
  return { id, ticks: declarations };
}

export interface PcrTestimony {
  readonly status: "executed" | "failed";
  readonly ticks: ReadonlyArray<TickRunResult>;
  readonly reads: ReadonlyArray<PartRead>;
  readonly writes: ReadonlyArray<PartWrite>;
  readonly invocations: ReadonlyArray<CalculationInvocation>;
}

export interface PcrMaterialization {
  readonly tickId: string;
  readonly address: string;
  readonly value: unknown;
}

export interface Pcr {
  readonly id: string;
  readonly declaredTicks: ReadonlyArray<TickDeclaration>;
  readonly ticks: ReadonlyArray<TickRunResult>;
  /** Execution evidence only. This is intentionally not an acceptance claim. */
  readonly testimony: PcrTestimony;
  readonly materializations: ReadonlyArray<PcrMaterialization>;
  readonly pxc: PxC;
}

function sameIds(expected: ReadonlyArray<string>, actual: ReadonlyArray<string>): boolean {
  return expected.length === actual.length && expected.every((id, index) => id === actual[index]);
}

/**
 * Compose a PCR from a declaration and an actual PQL run. Static declarations
 * cannot manufacture testimony: every Tick and materialization comes from the
 * run result, and a missing/extra/reordered Tick is rejected.
 */
export function composePcr(definition: PcrDefinition, run: PqlRunResult): Pcr {
  const expected = definition.ticks.map((tick) => tick.id);
  const actual = run.ticks.map((tick) => tick.id);
  if (!sameIds(expected, actual)) {
    throw new Error(`PCR Tick identities do not match declaration: expected [${expected.join(", ")}] but got [${actual.join(", ")}]`);
  }
  const materializations = run.ticks.flatMap((tick) =>
    tick.materializations.map((materialization) => ({
      tickId: tick.id,
      address: materialization.address,
      value: materialization.value,
    })),
  );
  return {
    id: definition.id,
    declaredTicks: [...definition.ticks],
    ticks: [...run.ticks],
    testimony: {
      status: run.status === "completed" ? "executed" : "failed",
      ticks: [...run.ticks],
      reads: [...run.telemetry.reads],
      writes: [...run.telemetry.writes],
      invocations: [...run.telemetry.invocations],
    },
    materializations,
    pxc: run.pxc,
  };
}
