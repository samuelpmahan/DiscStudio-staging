#!/usr/bin/env node
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, resolve } from "node:path";
import { materializeBoard } from "./board.js";
import { consumeDelivery, freezeDelivery, restoreDelivery, stageDelivery, verifyDelivery, type ConsumerReceipt, type DeliverySpec, type DeliveryStage } from "./delivery.js";
import { materializeDeliverySpine } from "./delivery-spine.js";
import { renderReport, type MgmMatrix } from "./report.js";
import { guardedUpdate, readSnapshot, snapshotProblems } from "./io.js";
import type { WorkItemUpdatePatch } from "./work-items.js";
import { workItemRevision } from "./work-items.js";

function usage(): string {
  return [
    "neat <check|next|board|html|matrix|update> [--root <repo>]",
    "  delivery freeze --spec <json-file>",
    "  delivery verify <id> [--archive]",
    "  delivery stage <id> --to <offered|claimed|rejected> --actor <name> [--note <text>]",
    "  delivery consume <id> --receipt <json-file>",
    "  delivery restore <id> --out <empty-path>",
    "  delivery spine <id> [--out <markdown-file>]",
    "  html [--out <path>]   generate a self-contained report with Board, Matrix, and Dependencies tabs",
    "  update <id> --expect <item-fingerprint> --patch <json-file>",
  ].join("\n");
}

function option(args: readonly string[], name: string): string | undefined {
  const index = args.indexOf(name);
  return index < 0 ? undefined : args[index + 1];
}

async function main(args: string[]): Promise<void> {
  const command = args[0];
  const root = option(args, "--root") ?? process.cwd();
  if (!command || command === "--help" || command === "help") throw new Error(usage());
  if (command === "delivery") {
    const action = args[1];
    if (action === "freeze") {
      const selected = option(args, "--spec");
      if (!selected) throw new Error(usage());
      const path = isAbsolute(selected) ? selected : resolve(root, selected);
      const spec = JSON.parse(await readFile(path, "utf8")) as DeliverySpec;
      process.stdout.write(`${JSON.stringify(await freezeDelivery(root, spec), null, 2)}\n`);
      return;
    }
    const id = args[2];
    if (!id) throw new Error(usage());
    if (action === "verify") {
      process.stdout.write(`${JSON.stringify(await verifyDelivery(root, id, args.includes("--archive")), null, 2)}\n`);
      return;
    }
    if (action === "stage") {
      const stage = option(args, "--to") as Exclude<DeliveryStage, "frozen" | "consumed"> | undefined;
      const actor = option(args, "--actor");
      if (!stage || !actor || !["offered", "claimed", "rejected"].includes(stage)) throw new Error(usage());
      process.stdout.write(`${JSON.stringify(await stageDelivery(root, id, stage, actor, option(args, "--note")), null, 2)}\n`);
      return;
    }
    if (action === "consume") {
      const selected = option(args, "--receipt");
      if (!selected) throw new Error(usage());
      const path = isAbsolute(selected) ? selected : resolve(root, selected);
      const receipt = JSON.parse(await readFile(path, "utf8")) as ConsumerReceipt;
      process.stdout.write(`${JSON.stringify(await consumeDelivery(root, id, receipt), null, 2)}\n`);
      return;
    }
    if (action === "restore") {
      const selected = option(args, "--out");
      if (!selected) throw new Error(usage());
      const output = isAbsolute(selected) ? selected : resolve(root, selected);
      process.stdout.write(`${JSON.stringify(await restoreDelivery(root, id, output), null, 2)}\n`);
      return;
    }
    if (action === "spine") {
      const spine = await materializeDeliverySpine(root, id);
      const selected = option(args, "--out");
      const output = selected
        ? (isAbsolute(selected) ? selected : resolve(root, selected))
        : resolve(root, ".neat", "deliveries", id, "spine.md");
      await mkdir(dirname(output), { recursive: true });
      await writeFile(output, spine.markdown, "utf8");
      process.stdout.write(`${output}\n`);
      return;
    }
    throw new Error(usage());
  }
  if (command === "update") {
    const id = args[1];
    const expected = option(args, "--expect");
    const patchPath = option(args, "--patch");
    if (!id || !expected || !patchPath) throw new Error(usage());
    const patch = JSON.parse(await readFile(patchPath, "utf8")) as WorkItemUpdatePatch;
    const result = await guardedUpdate(root, id, expected, patch);
    process.stdout.write(`${result.item.id} updated; previous fingerprint ${result.previousFingerprint}\n`);
    return;
  }
  const snapshot = await readSnapshot(root);
  const problems = snapshotProblems(snapshot);
  if (command === "check") {
    if (problems.length) throw new Error(problems.join("\n"));
    process.stdout.write(`neat check: ${snapshot.items.length} item schemas valid\n`);
    return;
  }
  if (problems.length) throw new Error(problems.join("\n"));
  const board = materializeBoard(snapshot);
  if (command === "html" || command === "matrix") {
    const matrix = await readFile(resolve(root, ".neat", "mgm.json"), "utf8")
      .then((text) => JSON.parse(text) as MgmMatrix)
      .catch((error: unknown) => {
        if ((error as NodeJS.ErrnoException).code === "ENOENT") return undefined;
        throw error;
      });
    const selected = option(args, "--out");
    const output = selected ? (isAbsolute(selected) ? selected : resolve(root, selected)) : resolve(root, ".neat", "out", "neat-report.html");
    await mkdir(dirname(output), { recursive: true });
    await writeFile(output, renderReport(board, snapshot.items, { matrix }), "utf8");
    process.stdout.write(`${output}\n`);
    return;
  }
  if (command === "board") {
    process.stdout.write(`${board.markdown}\n\n\`\`\`mermaid\n${board.mermaid}\n\`\`\`\n`);
    return;
  }
  if (command === "next") {
    const available = board.assessments.filter((item) => item.bucket === "queued" && item.dependencySatisfied && item.available === "available");
    const active = board.assessments.filter((item) => item.activity === "active");
    process.stdout.write(JSON.stringify({
      available,
      active,
      itemFingerprints: Object.fromEntries(snapshot.items.map((item) => [item.id, workItemRevision(item)])),
      fingerprint: board.inputFingerprint,
    }, null, 2) + "\n");
    return;
  }
  throw new Error(usage());
}

main(process.argv.slice(2)).catch((error: unknown) => {
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 1;
});
