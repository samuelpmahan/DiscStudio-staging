# Primary sources for the research comparisons

Collected 2026-09-09 through the Valency paper index (arxiv/pubmed partitions). These are the
sources the SUBDUE and WebShaper comparison stages must read before making claims; the research
entrypoint requires primary sources, a precise correspondence, a material difference, and a
counterexample for each analogy.

## SUBDUE (Holder, Cook)

- Cook, D. J. and Holder, L. B. "Substructure Discovery Using Minimum Description Length and
  Background Knowledge." JAIR 1994. [cs/9402102](https://arxiv.org/abs/cs/9402102). The primary
  description of the MDL-based SUBDUE: substructures that compress the graph, replacement of
  discovered instances by a single vertex, multiple passes producing a hierarchy, bounded inexact
  graph match, background knowledge guiding the search. The online appendix is the C implementation.
- Packer, C. A. and Holder, L. B. "GraphZip: Dictionary-based Compression for Mining Graph
  Streams." [1703.08614](https://arxiv.org/abs/1703.08614). Same author, streaming variant; useful
  for the "compress the past" vs "compile a tool for the future" framing because a dictionary is
  explicitly reused on later input.
- Purohit, S., Holder, L. B., Chin, G. "ITeM: Independent Temporal Motifs to Summarize and Compare
  Temporal Networks." [2002.08312](https://arxiv.org/abs/2002.08312). Temporal motifs: relevant to
  whether ordering can be represented by graph structure alone.
- Peshkin, L. "Structure induction by lossless graph compression" (Graphitour).
  [cs/0703132](https://arxiv.org/abs/cs/0703132). A lossless alternative to compare with SUBDUE's
  lossy inexact match when asking whether a replacement preserves executable behavior.

## WebShaper

- Tao, Z. et al. "WebShaper: Agentically Data Synthesizing via Information-Seeking Formalization."
  [2507.15061](https://arxiv.org/abs/2507.15061). The formal unit is the Knowledge Projection (KP)
  and its set-theoretic operations; expansion is an agentic Expander that makes a formal question
  more complex with retrieval and validation tools. Validation is against the synthesized dataset's
  downstream benchmark performance (GAIA, WebWalkerQA), not a local executable check.

## Library learning and trace-to-skill compilation (the "compile observed compression into a tool" hypothesis)

These are the closest research mechanisms to "promote a successful composition into a named
Calculation". They are comparison material, not claims about pyto.

- Cao, D. et al. "babble: Learning Better Abstractions with E-Graphs and Anti-Unification."
  [2212.04596](https://arxiv.org/abs/2212.04596). Library learning as corpus compression; abstractions
  found by anti-unification. Directly relevant to "exact macro extraction vs generalization where
  fixed internal values become parameters at a stable boundary".
- Grand, G. et al. "LILO: Learning Interpretable Libraries by Compressing and Documenting Code."
  [2310.19791](https://arxiv.org/abs/2310.19791). Stitch compression plus auto-documentation; the
  promoted abstraction carries usage examples, which matches the promotion policy's "keep the
  originating composition and evidence attached".
- Wong, C. et al. "Leveraging Language to Learn Program Abstractions and Search Heuristics" (LAPS,
  on DreamCoder). [2106.11053](https://arxiv.org/abs/2106.11053).
- Stengel-Eskin, E. et al. "ReGAL: Refactoring Programs to Discover Generalizable Abstractions."
  [2401.16467](https://arxiv.org/abs/2401.16467). Abstractions verified and refined via execution:
  the closest analogue to "permit local promotion after replay succeeds".
- Guo, Z. et al. "SKILL-DISCO: Distilling and Compiling Agent Traces into Reusable Procedural
  Skills." [2606.26669](https://arxiv.org/abs/2606.26669). Successful agent traces as paths in a
  transition graph, distilled into parameterized control-flow subgraphs compiled into callable,
  verifiable skills. This is the nearest published mechanism to the agent-workshop angle (recording
  ultracode runs as Parts and promoting recurring structure).
- Hernandez Cano, L. et al. "Prospective Compression in Human Abstraction Learning."
  [2605.09985](https://arxiv.org/abs/2605.09985). Distinguishes retrospective compression over past
  tasks from prospective compression targeting future tasks: exactly the slogan the entrypoint
  says to examine rather than assume.

## How the week uses these

The SUBDUE comparison day reads cs/9402102 for the four mechanisms the entrypoint names
(representation searched, criterion for a useful substructure, replacement operation, behavior
preservation), then runs the executable comparison on a real pyto composition graph and records
one counterexample where effects, ordering or provenance are not representable by structure alone.
The WebShaper reading supplies the "formal unit composed" and "what validation establishes" answers.
The library-learning papers frame the promotion experiment; none of them is adopted as a dependency.
