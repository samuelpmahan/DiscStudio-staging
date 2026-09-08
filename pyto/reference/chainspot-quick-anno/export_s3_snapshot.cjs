const fs = require('fs');
const path = require('path');
const { PNG } = require('pngjs');
const { decodeNodeFile } = require('../../packages/alg/dist/adapters/node.js');
const { stageContract: s0Contract } = require('../../packages/alg/dist/stages/S0/contract.js');
const { stageContract: s1Contract } = require('../../packages/alg/dist/stages/S1/contract.js');
const { stageContract: s2Contract } = require('../../packages/alg/dist/stages/S2/contract.js');
const { stageContract: s3Contract } = require('../../packages/alg/dist/stages/S3/contract.js');
const { executeS3VisibleTees, materializeS3Subtraction } = require('../../packages/alg/dist/stages/S3/clean/index.js');

function ensureDir(dir) { fs.mkdirSync(dir, { recursive: true }); }
function writePng(filePath, panel) {
  const png = new PNG({ width: panel.widthPx, height: panel.heightPx });
  png.data = Buffer.from(panel.rgba);
  fs.writeFileSync(filePath, PNG.sync.write(png));
}
function slug(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

// A ring is the enclosed hole G3 found; the frame is the bright component around it.
function ring(value) {
  return {
    bbox: [value.bboxX, value.bboxY, value.bboxW, value.bboxH],
    center: [value.cx, value.cy],
    kind: value.kind,
    holeArea: value.holeArea,
    elongation: value.elongation,
    ringFrac: value.ringFrac,
    angle: value.angle
  };
}

function frame(value) {
  return {
    bbox: [value.bboxX, value.bboxY, value.bboxW, value.bboxH],
    label: value.label,
    area: value.area,
    major: value.major,
    minor: value.minor,
    fill: value.fill,
    angle: value.angle
  };
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
  const s3 = await s3Contract.execute({ ...base, pxc: s2.pxc });
  const run = executeS3VisibleTees(s2.pxc);
  const subtraction = materializeS3Subtraction(run.image, run.tees);

  const panels = {};
  for (const [stage, stagePanels] of [['s0', s0.panels], ['s1', s1.panels], ['s2', s2.panels], ['s3', s3.panels]]) {
    for (const panel of stagePanels) {
      const file = `${stage}-${slug(panel.label)}.png`;
      writePng(path.join(outDir, file), panel);
      panels[`${stage}:${panel.label}`] = file;
    }
  }

  // members is filtered out of measured, so object identity marks who survived the family vote.
  const memberSet = new Set(run.family.members);
  const teePx = new Set();
  for (const tee of run.tees) for (const px of tee.px) teePx.add(Number(px));

  const snapshot = {
    schema: 'chainspot-quick-anno-s3-snapshot@1',
    input: imagePath,
    panels,
    s0Receipt: s0.receiptText,
    s1Receipt: s1.receiptText,
    s2Receipt: s2.receiptText,
    s3Receipt: s3.receiptText,
    canonical: { widthPx: run.image.widthPx, heightPx: run.image.heightPx },
    counts: {
      enclosed: run.rings.enclosed.length,
      elongated: run.rings.elongated.length,
      excludedByBadge: run.rings.excludedByBadge.length,
      candidates: run.rings.candidates.length,
      measured: run.family.measured.length,
      unframed: run.family.unframed.length,
      familyMembers: run.family.members.length,
      tees: run.tees.length,
      teePx: subtraction.teePx,
      overlapPx: subtraction.overlapPx,
      remainingOpaquePx: subtraction.remainingOpaquePx
    },
    // Every ring the detector saw, kept separately so nothing drops silently.
    rings: {
      enclosed: run.rings.enclosed.map(ring),
      elongated: run.rings.elongated.map(ring),
      excludedByBadge: run.rings.excludedByBadge.map(ring),
      candidates: run.rings.candidates.map(ring)
    },
    family: {
      measured: run.family.measured.map((member, index) => ({
        order: index + 1,
        ring: ring(member.ring),
        frame: frame(member.frame),
        inFamily: memberSet.has(member)
      })),
      unframed: run.family.unframed.map(ring),
      members: run.family.members.map((member, index) => ({
        order: index + 1,
        ring: ring(member.ring),
        frame: frame(member.frame),
        bbox: [member.frame.bboxX, member.frame.bboxY, member.frame.bboxW, member.frame.bboxH]
      })),
      anchor: run.family.anchor
        ? { ring: ring(run.family.anchor.ring), frame: frame(run.family.anchor.frame) }
        : null
    },
    tees: run.tees.map((tee, index) => ({
      order: index + 1,
      center: tee.center,
      innerBbox: tee.innerBbox,
      bbox: tee.bbox,
      angleRad: tee.angleRad,
      pxCount: tee.px.length
    })),
    teePixels: [...teePx].sort((a, b) => a - b),
    // exp/fill-consistent is an example variant: an exported function with no
    // registered Calculation and no Tick in S3_PLAN, so the clean run never reaches it.
    experimental: {
      fillConsistent: 'NOT RUN - exported function only, not registered in S3_PLAN'
    },
    runtimePcr: run.pcr
  };

  fs.writeFileSync(path.join(outDir, 'snapshot.json'), JSON.stringify(snapshot, null, 2));
  fs.writeFileSync(path.join(outDir, 's3.receipt.txt'), s3.receiptText + '\n');
  console.log(path.join(outDir, 'snapshot.json'));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
