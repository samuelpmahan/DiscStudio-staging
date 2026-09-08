const fs = require('fs');
const path = require('path');
const { PNG } = require('pngjs');
const { decodeNodeFile } = require('../../packages/alg/dist/adapters/node.js');
const { stageContract: s0Contract } = require('../../packages/alg/dist/stages/S0/contract.js');
const { stageContract: s1Contract } = require('../../packages/alg/dist/stages/S1/contract.js');
const { stageContract: s2Contract } = require('../../packages/alg/dist/stages/S2/contract.js');
const { executeS2BasketsCandidate, materializeS2Subtraction } = require('../../packages/alg/dist/stages/S2/clean/index.js');

function ensureDir(dir) { fs.mkdirSync(dir, { recursive: true }); }
function writePng(filePath, panel) {
  const png = new PNG({ width: panel.widthPx, height: panel.heightPx });
  png.data = Buffer.from(panel.rgba);
  fs.writeFileSync(filePath, PNG.sync.write(png));
}
function slug(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

async function main() {
  const imagePath = path.resolve(process.argv[2]);
  const outDir = path.resolve(process.argv[3]);
  if (!fs.existsSync(imagePath)) throw new Error(`image does not exist: ${imagePath}`);
  ensureDir(outDir);

  const base = { source: imagePath, inputLabel: path.basename(imagePath), decode: decodeNodeFile };
  const s0 = await s0Contract.execute(base);
  const s1 = await s1Contract.execute({ ...base, pxc: s0.pxc });
  const s2 = await s2Contract.execute({ ...base, pxc: s1.pxc });
  const run = executeS2BasketsCandidate(s1.pxc);
  const subtraction = materializeS2Subtraction(run.image, run.baskets);

  const panels = {};
  for (const [stage, stagePanels] of [['s0', s0.panels], ['s1', s1.panels], ['s2', s2.panels]]) {
    for (const panel of stagePanels) {
      const file = `${stage}-${slug(panel.label)}.png`;
      writePng(path.join(outDir, file), panel);
      panels[`${stage}:${panel.label}`] = file;
    }
  }

  const basketPx = new Set();
  for (const basket of run.baskets) for (const px of basket.px) basketPx.add(Number(px));

  const snapshot = {
    schema: 'chainspot-quick-anno-s2-snapshot@1',
    input: imagePath,
    panels,
    s0Receipt: s0.receiptText,
    s1Receipt: s1.receiptText,
    s2Receipt: s2.receiptText,
    canonical: { widthPx: run.image.widthPx, heightPx: run.image.heightPx },
    counts: {
      family: run.family.members.length,
      shellMembers: run.shellFamily.members.length,
      shellOffsets: run.shellFamily.shellOffsets.length,
      baskets: run.baskets.length,
      basketPx: subtraction.basketPx,
      overlapPx: subtraction.overlapPx,
      remainingOpaquePx: subtraction.remainingOpaquePx
    },
    shellMargins: run.shellFamily.margins,
    family: run.family.members.map((member, index) => ({
      order: index + 1,
      bbox: [member.body.bboxX, member.body.bboxY, member.body.bboxW, member.body.bboxH],
      areaRatio: member.areaRatio,
      whiteCoverage: member.whiteCoverage,
      label: member.body.label
    })),
    shellMembers: run.shellFamily.members.map((member, index) => ({
      order: index + 1,
      bbox: member.bbox,
      bodyBbox: [member.candidate.body.bboxX, member.candidate.body.bboxY, member.candidate.body.bboxW, member.candidate.body.bboxH],
      blackPx: Array.from(member.blackPx, Number)
    })),
    baskets: run.baskets.map((basket, index) => ({
      order: index + 1,
      bbox: basket.bbox,
      whitePx: basket.whitePx,
      blackPx: basket.blackPx,
      pxCount: basket.px.length,
      px: Array.from(basket.px, Number)
    })),
    basketPixels: [...basketPx].sort((a, b) => a - b),
    runtimePcr: run.pcr
  };

  fs.writeFileSync(path.join(outDir, 'snapshot.json'), JSON.stringify(snapshot, null, 2));
  fs.writeFileSync(path.join(outDir, 's2.receipt.txt'), s2.receiptText + '\n');
  console.log(path.join(outDir, 'snapshot.json'));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
