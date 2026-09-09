# Why PxC exists, in the owner's words

Recorded 2026-09-09 from the owner's account. This is the context every agent lacks when it opens
this repository; read it before the research briefs.

## The sequence

1. **Pathfinding in ChainSpot.** The owner reached the pathfinding stage of the course-map
   algorithm and was lost, because nothing the algorithm used to find a path was visible.
2. **toph.** A tool to see whether that inspection could be automated. It was awful: agents had to
   annotate, and the annotations carried no meaning. It died because it was context-starved outside
   the repository.
3. **The lab folder.** All scripts thrown into one place. They got lost and mistranslated.
4. **ABFeature and an engine to run them.** Enormous effort. Agents then produced dumb receipts and
   self-verified. Primitives like "find black component" were rewritten in every object. The owner
   could not keep everything in their head, and agents had to go repo-hunting to understand the
   algorithm.
5. **PixelCache.** Log everything, keep all the pixels in there, and make each Calculation compose
   meaning upon the Parts.
6. **Sequencing churn**, then the shape that stuck:
   `PrincipleComponentRender -> Tick[]`, `Tick -> Calculation[]`. Each Tick is where its
   Calculations become observable. The minimal observable steps compose each logical stage of the
   pipeline.
7. **Generalization.** Since it is only an execution engine, it was applied to Wumpus and Chess to
   extract meaning there too. The Parts let it represent any logical graph.

## Two remarks the owner made that are design statements

- "It could be the world's slowest neural net." Ticks as layers, Parts as named activations,
  receipts as the trace. The difference from a neural net is the point: every activation has a
  name a person chose, and every step is inspectable.
- "It could be used to help kids learn the way they know how to." Observable steps with meaning
  attached are worked examples. ChessLab's debugger ("inspect both sides") is already this shape.

## What this fixes in the research framing

- The founding need is observability of intermediate material, not caching. Caching is how the
  observable material stays affordable under the 5000 ms budget. The two are the same store.
- "Meaning composed upon Parts" is the semantic layer: a Part is not a pixel buffer, it is a pixel
  buffer with the Calculations that have interpreted it. Testimony and receipts are how that
  composition is recorded.
- Every roadbump named above is an agent-context failure: context starvation, mistranslation,
  duplicated primitives, dumb self-verified receipts, repo-hunting. The engram-table thesis in
  the plan is the proposed remedy; this file is the smallest instance of it.
