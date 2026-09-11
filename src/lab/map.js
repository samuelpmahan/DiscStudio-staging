/**
 * The map of the port, as Parts: what is built, what is stubbed and why, what is
 * next and for what -- plus the findings, each with its `for`. Built by running
 * everything the port can run, so the map never claims an address the run did
 * not write. `node src/lab/map.js` rebuilds it and writes the store.
 */
import { createLab, finding } from './lab.js';
import { registerS0, runS0 } from './s0.js';
import { registerS1, runS1, s1YamlDocument, s1MermaidDocument } from './s1.js';
import { registerS2, runS2 } from './s2.js';
import { registerPath, pathDocument, putCourses } from './path.js';
import { fixtureCapture } from './fixtures.js';

export function buildMap() {
  const lab = createLab();
  registerS0(lab); registerS1(lab); registerS2(lab); registerPath(lab);
  const s0 = runS0(lab, { decoded: fixtureCapture(), label: 'lab fixture capture' });
  const s1 = runS1(lab, { croppedImage: s0.croppedImage, document: s1YamlDocument(lab), seedRaster: true });
  const s2 = runS2(lab);
  putCourses(lab, ['DashsTrack']);
  const path = pathDocument(lab, { course: 'dashstrack', name: 'route', from: 'h1', to: 'h9' });
  lab.run(path.composition.PrincipleComponentRender, path.composition);
  for (const name of ['S0', 'S1', 'S2', path.composition.PrincipleComponentRender]) lab.saveRecord(name);

  lab.put('px.exp.lab.map', {
    for: 'what the ChainSpot S0/S1/Mermaid/traverse port reached in one sprint, and what it did not',
    built: lab.addresses().filter(address => address.startsWith('px.exp.lab.')),
    ran: [
      { what: 'S0', document: 'the compiled S0.mmd plus the cache Tick S0.pcr.yaml names last', evidence: 'tests/lab-s0.test.js' },
      { what: 'S1', document: "the LAB's own PrincipleComponentRender.yaml, read by readPql", evidence: 'tests/lab-s1.test.js' },
      { what: 'S2', document: 'the document its three OperationSpecs declare, on S1 produce', evidence: 'tests/lab-s2.test.js' },
      { what: 'mermaid', document: 'S1.mmd compiles to the same document as the YAML (structural digest)', evidence: 'tests/lab-mermaid.test.js' },
      { what: 'pathfinding', document: 'Anchors -> Start -> Search -> Settle over a course Part', evidence: 'tests/lab-path.test.js' }
    ],
    stubbed: [
      { address: 'px.exp.lab.s1.whitedigits.model', why: "the LAB matches digits with a logistic model asset fitted on a corpus this repository does not have; the port normalizes the same way and matches template Parts built from the fixture's own glyph shapes" },
      { address: 'px.exp.lab.oracle.*', why: 'no recorded LAB values to check against: S0/S1 read chainspot-corpus/dev/DashsTrack/DashsTrack-full.jpg, absent here, and the Mermaid experiment records no generated output ("no generated output from this revision exists yet")' },
      { address: 'px.exp.lab.s3', why: 'S3 (visible tee) is not ported yet; it is the next Stage in order' },
      { address: 'px.exp.lab.path.truth', why: 'the LAB anchors T/N/B come from the annotation truth file, which needs the corpus; the port searches the blind per-hole viewport the manifest itself carries' }
    ],
    next: [
      { what: 'S3 on the same harness', for: 'the stages in order, and the tee anchors a route needs' },
      { what: 'run the TypeScript S1 on the same fixture and compare value by value', for: 'the port is proved structurally and by invariant, never against the LAB running' },
      { what: 'an `into: []` effect Calculation, or an oc. equivalent in the JS core', for: 'S0 cache is a Tick the studio cannot express without inventing a Part' },
      { what: 'a binding that reads a sibling result with no address', for: "the Mermaid S0's FullImage locality is a property the studio's grammar cannot hold" },
      { what: 'a Basket recovery path', for: "the LAB's S2 receipt says 'recovery: NOT RUN'; a fused or missing shell has no second chance yet" }
    ]
  });

  finding(lab, 'pql.directresult', { kind: 'friction', for: 'a Stage whose point is that a big intermediate is never published cannot be ported without publishing it', text: "The LAB's Mermaid compiler binds a Calculation's result directly: `with: { image: { kind: 'fn', ref: 'decode' } }`. S0's FullImage is never a Part, and the LAB's proof checks exactly that (compare.ts `fullImageLocal`, proof.ts `!generated.pxc.has('px.source.fullImage')`). The studio's PQL binds addresses only.", workaround: 'lowerToPql mints one address per unpublished result (px.exp.lab.s0.local.decode) and reports it.', proposal: 'a binding kind that names a sibling Calculation in the same Tick, or a Part the record marks Tick-local.' });
  finding(lab, 'pql.effecttick', { kind: 'friction', for: "S0's third Tick exists to write a cache, and the grammar has no way to say so", text: "The LAB's S0_CACHE_TICK declares `produces: []`. The studio's readPql refuses it: 'a Calculation that publishes nothing has no place in this grammar'.", workaround: 'fn.lab.s0.cachefullimage publishes a cache receipt Part instead.', proposal: 'allow an empty `into` for a Calculation whose effect the receipt records, the way pyto marks oc. Calculations.' });
  finding(lab, 'pql.occurrenceid', { kind: 'friction', for: 'comparing two runs Calculation by Calculation needs a name that survives an edit', text: "The Mermaid compiler gives every Calculation the graph's node id, and the LAB's runner names values and failures by it ('failed at decode'). PQL gives a Calculation no id; exec.js names it by position, call and into.", workaround: 'the port compares by position, which is what proof.ts does too.', proposal: 'an optional `id` on a Calculation, carried into the receipt and the run record.' });
  finding(lab, 'stage.s0hasnopql', { kind: 'strength', for: 'knowing which LAB documents are compositions and which are descriptions', text: "S0 has no PQL document in ChainSpot: S0.pcr.yaml is a description (input / sanitation / transform / output / last / receipt) and the composition is three OperationSpecs executed by the gateway. The only PQL documents on this tip are S1/exp/badge-assembly/PrincipleComponentRender.yaml and what the Mermaid compiler emits. The port therefore compiles S0.mmd and appends the cache Tick the description names last." });
  finding(lab, 'exec.carriedtheport', { kind: 'strength', for: 'what the studio core already had that the LAB needed', text: "readPql takes its parser explicitly, so the LAB's YAML ran unedited once a 120-line reader existed. classifyTick's chain rule is the LAB's own rule (every S1 Tick is a chain: selectHsvMask -> group8Connected, and the five-Calculation BadgeAssembly). Multi-`into` carried the search Tick that publishes the next search state and the path in one pass." });
  finding(lab, 'oracle.nocorpus', { kind: 'friction', for: 'an oracle is what turns a port into a proof', text: 'Nothing in the LAB records an expected value this port could check against: S0 and S1 read a corpus image that is not in this repository, and the Mermaid experiment is explicitly unrun ("compilation, tests, execution and rendering await review"). The port is checked by structure (compiled document equals the YAML by digest), by the LAB\'s own invariants (owned, muted and remaining partition the raster) and by a fixture built to the LAB\'s knobs.', workaround: 'a deterministic synthetic capture whose badges are drawn to the plate/border/digit geometry the S1 knobs accept.', proposal: 'ask for one corpus image and one recorded S1 run; both paths then compare value by value the way proof.ts does.' });
  finding(lab, 'search.noobjective', { kind: 'finding', for: 'what pathfinding means in the LAB before anyone writes a search', text: "`lab traverse` renders the current point and its six hex neighbours (270/330/30/90/150/210 at one radius) and an agent picks one; `lab search` keeps trails, pins, pages and an event log. There is no objective function and no expansion: the search is the eye in the loop. The port keeps the geometry exactly and names the objective (fewest hex moves to within tolerance of a target anchor, inside the raster), so a path becomes a produce with a receipt and replays as `lab traverse move <n>` commands.", proposal: 'if the LAB wants an automatic search, the objective belongs in the course manifest beside the blind viewport.' });
  finding(lab, 'course.oneholetable', { kind: 'friction', for: 'a search needs anchors, and six of the seven courses have none', text: 'Of the seven course manifests only DashsTrack carries a per-hole sourceBox table; the others name an image, aliases and sweep cases. The port refuses a course with no viewport table the way `lab scope hN` does, and searches a second manifest it owns.' });
  finding(lab, 'pql.fanout', { kind: 'friction', for: 'a Stage that computes one object per member of a family cannot say so in a document', text: "The LAB's S2 Tick `Basket.findPx` invokes `fn.Basket.findPx` once per shell member inside one Tick, and its receipt lists every invocation. A PQL document names a Calculation once, with one `into`, so the port's Calculation maps over the members and publishes the array.", workaround: 'fn.lab.basket.findpx takes the whole shell family and returns the Basket objects.', proposal: 'a Calculation that fans out over a collection input, each invocation its own line in the receipt.' });
  finding(lab, 'stage.specsaredocuments', { kind: 'strength', for: 'porting a Stage that has no YAML', text: "S2's composition is three OperationSpecs, each declaring consumes, produces and its one Calculation. That is a PQL document in another notation: the port writes it out (four Ticks with the substrate publish in front) and runs it unchanged. The same move works for S0; only S1 keeps a written PQL document." });
  finding(lab, 's1.recognition', { kind: 'friction', for: 'the one Calculation of S1 that is reduced rather than ported', text: 'fn.s1.whiteDigits.prepare/match segment glyphs with knobs and score them with a logistic model asset (digits/logisticInference, assets/logistic.json). The port normalizes to the same digitW x digitH grid and scores against template Parts; the reading shape (value, status, per-digit rankings) is the LAB\'s.' });
  lab.save('lab');
  return lab;
}

if (process.argv[1] && process.argv[1].endsWith('map.js')) { const lab = buildMap(); console.log(`px.exp.lab.map built: ${lab.get('px.exp.lab.map').built.length} Parts, ${lab.addresses().filter(a => a.startsWith('proposal.lab.')).length} findings`); }
