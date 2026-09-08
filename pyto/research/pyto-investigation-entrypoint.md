# Investigate Pyto from its workload

## Start here

Read the [GitHub growth review and existing evidence](github-growth-review.md) before proposing examples. It inventories the user's 22 owned repositories, measures public history across branches, and identifies existing ChainSpot investigations and domain consumers. The agent's job is to inspect that work; do not ask the user to create an example merely because the agent has not looked.

Pyto is a Python workshop for accumulating reusable executable work. Its motivating workload is ChainSpot computer vision (CV): labeling disc golf course maps with a target of **five seconds or less at 95% accuracy**. The intended browser runtime has a severe loading budget; this motivated the original TypeScript/JavaScript implementation.

These numbers are user-stated targets, not results established by this document. The accuracy denominator, timing boundary, device, and evaluation corpus still need to be recovered or defined before claiming the target is met.

The immediate project is a small usable non-CV application. It should leave behind useful calculations, compositions, and experiments that make returning to CV less expensive. Research infrastructure has already imposed substantial cost. Every new abstraction should demonstrate a useful operation it enables or work it saves.

The user has a Java/Spring background and reports little practical JS/TS or CV literacy. Evaluate the existing work in that context: directing and inspecting agent-assisted development in unfamiliar fields is part of the motivating workload. Do not silently assume an experienced CV specialist built a toy language as a demonstration.

**The investigation question: can the same compositional substrate support both doing the work and investigating how to improve that work, with meaningful reuse across experiments?**

## What the user means by PxC

PixelCache is the motivating model. Its cached material includes image components and intermediate results, not necessarily individual pixels. Calculations go through PxC and return refined Parts to PxC. Callers use shared, parameterized invocations.

PxC is intended to be the manipulable representation of the working domain itself. A Pandas projection would provide another interface to that representation. It would not be the thing that first makes the domain manipulable.

Precise Parts and their executable interactions form a seed. Composition grows the structure outward. Recording execution can expose that growth, but merely collecting logs and inferring a graph afterward does not establish this design.

These are descriptions of intent supplied by the user. Investigate how far the implementation realizes them.

## Learn the language before evaluating it

Treat Part, Calculation, PxC, PQL, and PCR as technical vocabulary whose semantics must be learned. Begin with the user's definitions, then trace how the implementation realizes them. If documentation, implementation, and intended behavior differ, name the discrepancy. Do not substitute familiar concepts before determining what the original concepts mean.

Explain one complete example using that vocabulary accurately, including what a composition means and what executing it produces. Then investigate whether experiments can operate on the same Parts and Calculations as the application, so that experiment construction and analysis also become reusable executable work.

Learning the semantics is necessary to evaluate the design; claims about its benefits remain testable. A function registry, cache, or workflow engine may provide a useful comparison after the semantics are understood. Any proposed equivalence must account for the operations, compositional behavior, and constraints that matter to the workload. Measure saved implementation, computation, and reconstruction of context where relevant. Assess novelty separately from utility.

## The concrete reuse challenge

The user's example is **ablating 15 features into groups**. Ablation means disabling selected features to measure their contribution. Fifteen features does not automatically authorize evaluating all 32,768 subsets.

Start by inspecting the existing ChainSpot case-variant matrix at commit `d0f7487`, its shared PxC material profiles, and its tests. Use the already-published Wumpus investigations, ChessLab, and DiscStudio to inspect reuse in other domains. Trace how the existing work preserves and reuses:

1. Feature definitions, input references, and parameter choices.
2. A grouping of features and the experiment that selects combinations.
3. Shared intermediate results where reuse is valid.
4. Each run's outputs, timing, comparison criteria, and observations.
5. The comparison procedure itself, applied to another grouping or input without reconstructing the investigation.

Across existing experiments, identify exactly what each inherits and what had to be added. A proposed next experiment is justified by a specific gap found during that inspection. Preserve failed variants and their interpretation alongside successful ones. Preservation does not require putting every runtime artifact in Git.

For browser-facing work, report loading and execution costs under explicit conditions. Python workshop reuse does not by itself establish that a resulting capability meets the browser target or transfers correctly to TS/JS.

## Read PQL before explaining PQL

Recover the actual meaning of Part, Calculation, PQL, and PCR from declarations, callers, and executions. Record missing behavior as missing. In particular:

- What can PQL address, select, bind, compose, and execute?
- Can a composition itself be selected and manipulated by another calculation? Demonstrate the round trip if it exists.
- How are Calculation definitions distinguished from individual invocations and their parameter values?
- How are input versions and resulting Parts identified? Under what conditions is reuse valid?
- Which relationships are declared, which are observed, and which are verified by tests?
- What survives a table projection and a subsequent use of its results in PxC?

Do not infer that PQL is merely a sequential pipeline, or that it is already a general graph language. Likewise, the earlier suggestion that PQL and PCR are Parts is a hypothesis to inspect, not an established property.

A useful return contains an exact source location, one input, the operation performed, the resulting structure, and one downstream consumer. This is enough to begin; do not build a universal schema to explain a small example.

## Compare research through mechanisms

SUBDUE and WebShaper are research references that motivated questions, not claims of equivalent capability or originality. The user identifies SUBDUE's Larry Holder and Diane Cook as their professors; the comparison deserves specific technical engagement.

After tracing a real example, investigate:

- For SUBDUE: the representation being searched, the criterion for a useful substructure, the replacement operation, and whether a replacement preserves executable behavior.
- For WebShaper: the formal unit being composed, how expansion changes the task, and what its validation establishes compared with a local executable check.

Use primary sources when making claims about either system. Identify the precise correspondence, a material difference, and a counterexample to the analogy. The earlier slogan about SUBDUE compressing the past and Pyto building future tools is an intuition to examine, not a sufficient characterization of SUBDUE.

A runtime trace establishes what was observed. Replay establishes agreement under the recorded check. Neither alone proves correctness, generality, or suitability as model-training data.

## Return a small evidence trail

Report the observed implementation, the proposed interpretation, and the remaining unknowns separately. Include:

- Existing runnable investigations and their source references.
- What the second experiment reused, with concrete evidence of saved work or computation.
- The smallest conventional implementation that provides a fair comparison, or an explanation of why an existing equivalent is enough.
- One failure or counterexample that constrains the claim.
- One useful next experiment, sized to the current project.

Permit early local promotion after replay succeeds. Require broader evidence before declaring a primitive stable. Keep promotion reversible and retain its originating composition and evidence. Do not require a grand package structure or an automated discovery engine before demonstrating useful composition.

## One provisional judgment

{?} InvestigationPayoff

1. **Workshop perspective:** Would reusing the grouping, execution, and comparison procedure on a second experiment demonstrate the immediate value you want from Pyto?
2. **CV runtime perspective:** If that procedure reuses well but the browser execution remains too expensive, what should we retain as workshop progress while the runtime problem remains open?
3. **Agent perspective:** I propose testing experiment reuse first and measuring browser performance on a representative CV workload when available; what dependency would make that order misleading?

Original question: What is the first concrete demonstration that PxC helps this project beyond shared function invocation?

Context: The user explicitly wants grouped feature ablations to leave reusable work, and has temporarily stepped back from CV after costly infrastructure development.

Workshop reuse can be demonstrated in the current application. Runtime measurements are necessary to establish the separate ChainSpot performance target. Another consideration is that a cheap tiny example might miss the costs of large image components; report that limit rather than generalizing its timing.

Current lean: demonstrate the second experiment's reuse with the nearest existing runnable example. Work status: provisional investigation order; this document records a brief and makes no implementation or benchmark claim. This single judgment closes the narrow documentation decision without adding a speculative question backlog.
