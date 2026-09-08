import { readdir } from "node:fs/promises";
import { join } from "node:path";
import { composePcr, definePcr, type Pcr } from "./pcr.js";
import { runPql, type PqlProgram, type PqlRunResult } from "./pql.js";
import { calculationId, createPxC, readPart, registerCalculation, type Calculation, type PxC } from "./pxc.js";
import { verifyDelivery, type DeliveryManifest, type DeliveryState } from "./delivery.js";

export type DeliveryPhaseStatus = "complete" | "active" | "waiting";

export interface DeliveryPhase {
  id: "freeze" | "offer" | "inspect" | "consume" | "disposition";
  label: string;
  status: DeliveryPhaseStatus;
  summary: string;
  links: Array<{ label: string; href: string }>;
}

export interface DeliverySpineContext {
  manifest: DeliveryManifest;
  state: DeliveryState;
  receiptPaths: string[];
  questionsPath: string;
}

export interface DeliverySpine {
  phases: DeliveryPhase[];
  markdown: string;
  analysisRun: PqlRunResult;
  analysisPcr: Pcr;
}

export const DELIVERY_SPINE_CALCULATIONS = {
  freeze: "fn.neat.delivery.freeze-view",
  offer: "fn.neat.delivery.offer-view",
  inspect: "fn.neat.delivery.inspect-view",
  consume: "fn.neat.delivery.consume-view",
  disposition: "fn.neat.delivery.disposition-view",
} as const;

const phasePart = (name: DeliveryPhase["id"]): string => `px.neat.delivery.phase.${name}`;

export const DELIVERY_SPINE_PQL = {
  PrincipleComponentRender: "NeatDeliverySpine",
  Ticks: [
    { name: "Freeze", Calculations: [{ call: DELIVERY_SPINE_CALCULATIONS.freeze, with: { context: "px.neat.delivery.context" }, into: phasePart("freeze") }] },
    { name: "Offer", Calculations: [{ call: DELIVERY_SPINE_CALCULATIONS.offer, with: { context: "px.neat.delivery.context", previous: phasePart("freeze") }, into: phasePart("offer") }] },
    { name: "Inspect", Calculations: [{ call: DELIVERY_SPINE_CALCULATIONS.inspect, with: { context: "px.neat.delivery.context", previous: phasePart("offer") }, into: phasePart("inspect") }] },
    { name: "Consume", Calculations: [{ call: DELIVERY_SPINE_CALCULATIONS.consume, with: { context: "px.neat.delivery.context", previous: phasePart("inspect") }, into: phasePart("consume") }] },
    { name: "Disposition", Calculations: [{ call: DELIVERY_SPINE_CALCULATIONS.disposition, with: { context: "px.neat.delivery.context", previous: phasePart("consume") }, into: phasePart("disposition") }] },
  ],
} as const;

function hasStage(state: DeliveryState, stage: DeliveryState["stage"]): boolean {
  return state.history.some((event) => event.stage === stage);
}

function evidenceHref(href: string): string {
  return /^(https?:\/\/|\/)/i.test(href) ? href : `payload/${href}`;
}

function registerDeliverySpineCalculations(seed: PxC): PxC {
  const definitions: Array<Calculation<unknown, DeliveryPhase>> = [
    {
      id: calculationId(DELIVERY_SPINE_CALCULATIONS.freeze),
      run: (input) => {
        const { context } = input as { context: DeliverySpineContext };
        return {
          id: "freeze",
          label: "Freeze",
          status: "complete",
          summary: `${context.manifest.entries.length} entries captured as ${context.manifest.deliveryDigest.slice(0, 12)}.`,
          links: [
            { label: "Manifest", href: "manifest.json" },
            { label: "Payload", href: "payload/" },
            { label: "State", href: "state.json" },
          ],
        };
      },
    },
    {
      id: calculationId(DELIVERY_SPINE_CALCULATIONS.offer),
      run: (input) => {
        const { context } = input as { context: DeliverySpineContext };
        return {
          id: "offer",
          label: "Offer",
          status: hasStage(context.state, "offered") ? "complete" : "active",
          summary: `Mailbox ${context.manifest.mailbox.name} names ${context.manifest.mailbox.consumer} as consumer.`,
          links: [{ label: "Mailbox obligations", href: "manifest.json" }],
        };
      },
    },
    {
      id: calculationId(DELIVERY_SPINE_CALCULATIONS.inspect),
      run: (input) => {
        const { context } = input as { context: DeliverySpineContext };
        const total = context.manifest.mailbox.obligations.length;
        const satisfied = context.state.satisfiedObligations.length;
        return {
          id: "inspect",
          label: "Inspect",
          status: context.receiptPaths.length ? (satisfied === total ? "complete" : "active") : "waiting",
          summary: `${satisfied}/${total} checklist prompts satisfied; ${context.receiptPaths.length} receipt(s) retained.`,
          links: [
            { label: "Judgment packets", href: context.questionsPath },
            ...context.manifest.evidence.map((href, index) => ({ label: `Evidence ${index + 1}`, href: evidenceHref(href) })),
            ...context.receiptPaths.map((href, index) => ({ label: `Receipt ${index + 1}`, href })),
          ],
        };
      },
    },
    {
      id: calculationId(DELIVERY_SPINE_CALCULATIONS.consume),
      run: (input) => {
        const { context } = input as { context: DeliverySpineContext };
        return {
          id: "consume",
          label: "Consume",
          status: context.state.stage === "consumed" ? "complete" : ["claimed", "partial"].includes(context.state.stage) ? "active" : "waiting",
          summary: context.state.stage === "partial" ? "Partial progress is preserved; another receipt can continue." : `Current lifecycle stage: ${context.state.stage}.`,
          links: [{ label: "Lifecycle history", href: "state.json" }],
        };
      },
    },
    {
      id: calculationId(DELIVERY_SPINE_CALCULATIONS.disposition),
      run: (input) => {
        const { context } = input as { context: DeliverySpineContext };
        const complete = context.state.stage === "consumed" || context.state.stage === "rejected";
        return {
          id: "disposition",
          label: "Disposition",
          status: complete ? "complete" : "waiting",
          summary: complete ? `Retained with disposition ${context.state.stage}.` : "Awaiting consumed, rejected, superseded, or retained-for-later judgment.",
          links: [{ label: "Archive", href: context.manifest.archivePath }],
        };
      },
    },
  ];
  return definitions.reduce((pxc, definition) => registerCalculation(pxc, definition), seed);
}

function renderMarkdown(context: DeliverySpineContext, phases: readonly DeliveryPhase[]): string {
  const phaseMarkdown = phases.map((phase, index) => [
    `## ${index + 1}. ${phase.label} — ${phase.status}`,
    "",
    phase.summary,
    "",
    ...phase.links.map((link) => `- [${link.label}](${link.href})`),
  ].join("\n")).join("\n\n");
  return `# Delivery ${context.manifest.id}\n\nCandidate: \`${context.manifest.deliveryDigest}\`  \nBase: \`${context.manifest.source.baseCommit}\`  \nHEAD: \`${context.manifest.source.headCommit}\`\n\n${phaseMarkdown}\n`;
}

export function composeDeliverySpine(context: DeliverySpineContext): DeliverySpine {
  const registered = registerDeliverySpineCalculations(createPxC({ "px.neat.delivery.context": context }));
  const analysisRun = runPql(registered, DELIVERY_SPINE_PQL as PqlProgram);
  if (analysisRun.status !== "completed") throw new Error("Delivery spine PQL execution failed", { cause: analysisRun.error });
  const phases = DELIVERY_SPINE_PQL.Ticks.map((tick) => readPart<DeliveryPhase>(analysisRun.pxc, phasePart(tick.name.toLowerCase() as DeliveryPhase["id"])).value);
  const analysisPcr = composePcr(definePcr("pcr.neat.delivery-spine", DELIVERY_SPINE_PQL.Ticks.map((tick) => tick.name)), analysisRun);
  return { phases, markdown: renderMarkdown(context, phases), analysisRun, analysisPcr };
}

export async function materializeDeliverySpine(root: string, id: string): Promise<DeliverySpine> {
  const { manifest, state } = await verifyDelivery(root, id);
  const directory = join(root, ".neat", "deliveries", id);
  const receiptPaths = await readdir(join(directory, "receipts"))
    .then((names) => names.filter((name) => name.endsWith(".json")).sort().map((name) => `receipts/${name}`))
    .catch((error: unknown) => {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") return [];
      throw error;
    });
  return composeDeliverySpine({ manifest, state, receiptPaths, questionsPath: "../../delivery-questions.md" });
}
