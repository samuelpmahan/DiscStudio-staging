# Pyto Minimal-Primitives Research Brief

Read [Investigate Pyto from its workload](pyto-investigation-entrypoint.md) first. It supplies the motivating workload and corrects the abstraction-first framing below. The kernel and research analogies in this earlier brief remain hypotheses; recover actual PQL/PxC behavior before adopting them.

## Objective

Inspect the attached Pyto zip as working evidence. Discover the smallest executable, composable primitive set already latent in the code. Do not design Pyto's final architecture.

Treat code, runnable behavior, tests, and artifacts as observations. Current module boundaries and names are hypotheses, not requirements.

## Kernel hypothesis to falsify

- A **Part** is an addressed value.
- A **Calculation** is executable behavior that consumes and produces Parts.
- **PQL** is a Part describing a composition of Calculations.
- **PCR** is a Part recording what happened when that composition executed.
- A locally useful composition can be promoted into a named Calculation and composed again.

The irreducible kernel may therefore be only Part plus Calculation. Determine whether PQL or PCR must instead remain independent primitives.

## Promotion policy

Local promotion and stability are separate events.

1. Permit **local promotion** after the candidate composition replays successfully against the behavior that produced it.
2. Keep the promoted Calculation provisional, inspectable, reversible, and scoped to that local workshop.
3. Require broader evidence before declaring it **stable**: successful use beyond the originating example, a boundary that remains meaningful, and preserved behavior under substitution.
4. Do not invent a universal repetition count or confidence score. The research should reveal useful evidence before Pyto standardizes an admission rule.

Tests establish replay. They do not alone establish stability.

## Research procedure

1. Run or trace the actual Python workflows.
2. Inventory observable behavior without adopting the current package layout as the conceptual model.
3. Propose the smallest primitive set capable of reproducing those workflows.
4. For every proposed primitive:
   - define its semantics in one sentence;
   - show its smallest executable Python form;
   - compose it with another primitive;
   - remove, inline, or merge it and report exactly what becomes impossible.
5. Separate the irreducible kernel, practical conveniences, and domain-specific behavior.
6. Build the smallest runnable experiment demonstrating:

   `primitive execution -> composition -> execution record -> local promotion -> reuse`

7. Preserve the original code. Do not perform a broad migration.

## SUBDUE comparison

Compare the experiment seriously with SUBDUE:

- Identify what corresponds to graph nodes, edges, discovered substructures, compression, replacement, and recursive discovery.
- Explain where structural graph compression is insufficient.
- State what execution evidence is required before a discovered pattern can become callable.
- Distinguish exact **macro extraction** from genuine generalization, where fixed internal values become parameters at a stable boundary.
- Test this framing: SUBDUE compresses a graph describing the past; Pyto may compile an observed compression into a tool for future compositions.

Do not force the analogy when behavior, effects, ordering, or provenance cannot be represented by graph structure alone.

## Required return

A. Observed behaviors  
B. Irreducible kernel  
C. Practical kernel  
D. Runnable experiment  
E. Ablation results  
F. SUBDUE comparison  
G. Counterexamples challenging the conclusion  
H. Remaining judgments marked `{?} DescriptiveLabel: details`

Prefer possibility-preserving interfaces. Use concrete examples and provisional boundaries. Do not prescribe a final package list, schema ecosystem, plugin system, or roadmap.

## Resolved judgment

{?} PromotionCriterion: resolved by the user on 2026-09-08

1. **Experimenter perspective:** When rapid discovery benefits from naming a successful composition immediately, what evidence should remain attached so that local convenience is not mistaken for generality?
2. **Library-consumer perspective:** When another domain encounters the promoted Calculation, what broader executions would demonstrate that its boundary transfers rather than merely sharing a name?
3. **Agent perspective:** If replay is enough for reversible local promotion but not stability, how should the artifact make that status unmistakable without slowing experimentation?

Original question: When has a composition earned primitive status?

Decision: Permit early local promotion after replay succeeds; require broader evidence only before declaring the primitive stable.

Learning: The useful distinction was not early versus late promotion. It was reversible local vocabulary versus a stability claim made to other consumers.

Work status: Resolved for this research brief. The precise broader-evidence shape remains an experimental result, not a prerequisite specification.
