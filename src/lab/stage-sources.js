/**
 * The `.mmd` sources of the Stages this port invents, embedded as data.
 *
 * `src/lab/source-data.js` does this for the LAB's own documents and says why:
 * the Stage modules are the same modules node runs and the browser imports, so
 * none of them may reach for node:fs at import time. S4, S5 and S6 have no
 * ChainSpot original -- they are written here -- so their flowcharts live under
 * `src/lab/stages/` and travel beside the code as the text below.
 * tests/lab-s5.test.js checks every entry against the file, so the two cannot
 * drift, exactly as tests/lab-source-data.test.js does for the LAB's.
 */
export const STAGE_TEXT = Object.freeze({
  "S4.args.json": "{\n  \"bindAnchors\": { \"rule\": \"nearest-free-in-badge-order\" }\n}\n",
  "S4.mmd": "flowchart TD\n    badges[\"px.badges.objects\"]\n    tees[\"px.tees\"]\n    baskets[\"px.baskets\"]\n\n    subgraph S4[\"PCR: S4\"]\n        subgraph ReadNumbers[\"Tick: Hole.readNumbers\"]\n            readNumbers[\"fn.Hole.readNumbers\"]\n        end\n        subgraph BindAnchors[\"Tick: Hole.bindAnchors\"]\n            bindAnchors[\"fn.Hole.bindAnchors\"]\n        end\n        subgraph Assemble[\"Tick: Hole.assemble\"]\n            assemble[\"fn.Hole.assemble\"]\n        end\n        subgraph Unplaced[\"Tick: Hole.unplaced\"]\n            unplaced[\"fn.Hole.unplaced\"]\n        end\n    end\n\n    badges -->|badges| readNumbers\n    readNumbers --> numbers[\"px.holes.numbers\"]\n    numbers -->|numbers| bindAnchors\n    tees -->|tees| bindAnchors\n    baskets -->|baskets| bindAnchors\n    bindAnchors --> binding[\"px.holes.binding\"]\n    binding -->|binding| assemble\n    assemble --> objects[\"px.holes.objects\"]\n    binding -->|binding| unplaced\n    objects -->|holes| unplaced\n    unplaced --> unplacedPart[\"px.holes.unplaced\"]\n",
  "S5.args.json": "{\n  \"obstacleMap\": { \"cellPx\": 16 },\n  \"graph\": { \"course\": \"labfixture\" }\n}\n",
  "S5.mmd": "flowchart TD\n    holes[\"px.holes.objects\"]\n    unplacedHoles[\"px.holes.unplaced\"]\n    canonical[\"px.course.canonicalPixels\"]\n    remaining[\"px.remaining.afterBadges\"]\n    components[\"px.components\"]\n    baskets[\"px.baskets\"]\n    tees[\"px.tees\"]\n\n    subgraph S5[\"PCR: S5\"]\n        subgraph HoleGeometry[\"Tick: Course.holeGeometry\"]\n            holeGeometry[\"fn.Course.holeGeometry\"]\n        end\n        subgraph ObstacleMap[\"Tick: Course.obstacleMap\"]\n            obstacleMap[\"fn.Course.obstacleMap\"]\n        end\n        subgraph Walkable[\"Tick: Course.walkable\"]\n            walkable[\"fn.Course.walkable\"]\n        end\n        subgraph Graph[\"Tick: Course.graph\"]\n            graph[\"fn.Course.graph\"]\n        end\n        subgraph Summary[\"Tick: Course.summary\"]\n            summary[\"fn.Course.summary\"]\n        end\n    end\n\n    holes -->|holes| holeGeometry\n    canonical -->|raster| holeGeometry\n    holeGeometry --> geometry[\"px.course.holes\"]\n    remaining -->|remaining| obstacleMap\n    components -->|fields| obstacleMap\n    baskets -->|baskets| obstacleMap\n    tees -->|tees| obstacleMap\n    canonical -->|raster| obstacleMap\n    obstacleMap --> obstacles[\"px.course.obstacles\"]\n    obstacles -->|obstacles| walkable\n    walkable --> walkableCells[\"px.course.walkable\"]\n    geometry -->|geometry| graph\n    obstacles -->|obstacles| graph\n    walkableCells -->|walkable| graph\n    graph --> courseGraph[\"px.course.graph\"]\n    courseGraph -->|graph| summary\n    geometry -->|geometry| summary\n    unplacedHoles -->|unplaced| summary\n    summary --> courseSummary[\"px.course.summary\"]\n",
  "S6.args.json": "{}\n",
  "S6.mmd": "flowchart TD\n    graph[\"px.course.graph\"]\n    courseSummary[\"px.course.summary\"]\n\n    subgraph S6[\"PCR: S6\"]\n        subgraph Legs[\"Tick: Round.legs\"]\n            legs[\"fn.Round.legs\"]\n        end\n        subgraph Path[\"Tick: Round.path\"]\n            path[\"fn.Round.path\"]\n        end\n        subgraph Summary[\"Tick: Round.summary\"]\n            summary[\"fn.Round.summary\"]\n        end\n    end\n\n    graph -->|graph| legs\n    legs --> roundLegs[\"px.round.legs\"]\n    roundLegs -->|legs| path\n    graph -->|graph| path\n    path --> roundPath[\"px.round.path\"]\n    roundPath -->|path| summary\n    roundLegs -->|legs| summary\n    courseSummary -->|course| summary\n    summary --> roundSummary[\"px.round.summary\"]\n"
});

/** One embedded flowchart, by its file name under src/lab/stages. */
export function readStageSource(name) {
  const text = STAGE_TEXT[name];
  if (text === undefined) throw new Error(`lab: '${name}' is not an embedded stage document.`);
  return text;
}
/** The same document, parsed as JSON. */
export function readStageSourceJson(name) { return JSON.parse(readStageSource(name)); }

/** The Mermaid path of one invented Stage: its flowchart, compiled and lowered to a document readPql can read. */
export function compiledStage(stage, compileMermaidPcr, lowerToPql, labDocument) {
  const compiled = compileMermaidPcr(readStageSource(`${stage}.mmd`), readStageSourceJson(`${stage}.args.json`));
  const { document, local } = lowerToPql(compiled);
  return { compiled, local, document: labDocument(document) };
}
