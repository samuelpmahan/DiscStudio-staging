const fs = require('fs');
const path = require('path');
const { PNG } = require('pngjs');
const { decodeNodeFile } = require('../../packages/alg/dist/adapters/node.js');
const { stageContract: s0Contract } = require('../../packages/alg/dist/stages/S0/contract.js');
const { stageContract: s1Contract } = require('../../packages/alg/dist/stages/S1/contract.js');
const { executeS1BadgesCandidate, materializeS1Subtractions } = require('../../packages/alg/dist/stages/S1/clean/index.js');

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
  const run = executeS1BadgesCandidate(s0.pxc);
  const subtraction = materializeS1Subtractions(run);

  const panels = {};
  for (const [stage, stagePanels] of [['s0', s0.panels], ['s1', s1.panels]]) {
    for (const panel of stagePanels) {
      const file = `${stage}-${slug(panel.label)}.png`;
      writePng(path.join(outDir, file), panel);
      panels[`${stage}:${panel.label}`] = file;
    }
  }

  const owned = new Set();
  const muted = new Set();
  for (const badge of run.badges) {
    for (const px of badge.px) owned.add(Number(px));
    for (const px of badge.has.mute.px) muted.add(Number(px));
  }

  const snapshot = {
    schema: 'chainspot-quick-anno-s1-snapshot@1',
    input: imagePath,
    panels,
    s0Receipt: s0.receiptText,
    s1Receipt: s1.receiptText,
    canonical: { widthPx: run.croppedImage.widthPx, heightPx: run.croppedImage.heightPx },
    counts: {
      badges: run.badges.length,
      brightComponents: run.components.bright.components.length,
      darkComponents: run.components.dark.components.length,
      family: run.family.length,
      ownedPx: subtraction.badgePx.badgePx,
      mutedPx: subtraction.muted.mutedPx,
      addedMutePx: subtraction.muted.addedMutePx,
      remainingOpaquePx: subtraction.muted.remainingOpaquePx
    },
    badges: run.badges.map((badge, index) => ({
      order: index + 1,
      label: badge.label,
      source: badge.source,
      bbox: badge.bbox,
      confidence: badge.confidence,
      whitePx: badge.whitePx,
      blackPx: badge.blackPx,
      ownedPx: badge.px.length,
      mutedPx: badge.has.mute.px.length
    })),
    ownedPixels: [...owned].sort((a, b) => a - b),
    mutedPixels: [...muted].sort((a, b) => a - b),
    runtimePcr: run.pcr
  };

  fs.writeFileSync(path.join(outDir, 'snapshot.json'), JSON.stringify(snapshot, null, 2));
  fs.writeFileSync(path.join(outDir, 's0.receipt.txt'), s0.receiptText + '\n');
  fs.writeFileSync(path.join(outDir, 's1.receipt.txt'), s1.receiptText + '\n');
  console.log(path.join(outDir, 'snapshot.json'));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
