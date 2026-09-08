# Python LAB stewardship

## Mandate

Pyto is the reusable Python programming and experimentation environment: a place to author calculations, compose them into programs, execute them, inspect and compare results, visualize evidence, and retain runnable examples. `pyto-lab==0.1.0` is the first extracted working core, not the whole LAB.

The calculation graph is the program. A Part names a calculation result that other calculations can reuse. External input still has to enter a run somewhere; the current `PxC.set(Part(...), value)` convention is an implementation fact, not proof that raw configuration is conceptually a Part.

This worktree owns shared Pyto behavior, examples, package checks, release evidence, and the repeatable agent workflow. DiscStudio owns disc/card rules, its backend and browser. ChainSpot owns its stages. Shared code moves into Pyto only after a runnable consumer demonstrates the need.

## Measured baseline

At base `9c1ea8d963478cb75f6a204123f156c730c6994f`:

- Uppercase `PCR` authors and executes Python calculations. Its `PcrRun` testimony records calculation IDs, calculation addresses, input references, literal args, and published output addresses.
- A published Part consumed later is normalized to the producing calculation result. This is already tested in `tests/test_first_class.py`.
- `PQL` finds current `PxC` values by exact address, prefix, and an ordinary Python predicate. It does not traverse dependencies.
- `PCR.mermaid()` draws the executable program, but uppercase `PCR` has no matching program exporter or importer.
- Lowercase `Pcr` exports JSON and Mermaid, but its source explicitly says it does not execute. The two classes must not be presented as one round-trip format.
- The fixed `pyto-lab==0.1.0` wheel has SHA256 `89a524562c57333558117d6890e3bd29af05d5ff1dea3efc731c67475dc20a6c`. Six core checks and the basic example were recorded as passing. DiscStudio has 36 byte-identical historical SVG results through the installed package.
- Current DiscStudio art code manually joins `PcrRun` testimony with package version and source hashes to form `compositionEvidence`. That object is an inspection receipt, not a portable executable program.
- The in-progress Card/PxC adapter in `/mnt/d/pyto-worktrees/paper-card-pxc` reports seven focused backend tests. It seeds presentation and card-configuration dictionaries as Parts, then executes one `fn.card.compose` calculation. This is useful consumer evidence, but it does not yet demonstrate art-result fan-out, program replay, exact annotation attachment, or dependency queries.

The last item is a read-only observation of uncommitted consumer work, not an accepted Pyto model or a historical checkpoint.

## Next shared capability: retain and replay an executable calculation program

DiscStudio needs to save a Card program, its bound inputs, and result identities; reload it; resolve its named calculations from installed code; and reproduce the same composition and SVG hashes. This is the next Pyto seam.

The retained object must describe the executable uppercase `PCR` program, rather than serialize only its after-run testimony. It must preserve:

- ordered ticks and calculation IDs;
- calculation addresses resolved through an explicit registry;
- each binding as either an external input or a prior calculation result;
- literal arguments and published result addresses;
- immutable bound-input values, or references plus digests that resolve to retained values;
- the Pyto distribution version and calculation-provider identity needed to reject an incompatible replay.

The retained data must not pickle lambdas or claim to contain executable Python code. Replay means rebuilding the program from declarative data and resolving calculation addresses against explicitly installed, registered functions. The concrete public API and file schema remain undecided until the DiscStudio adapter and design-language review stabilize.

An inspection receipt should then be derived from this retained program and a run. It is a view for people and tools; it is not the program itself.

### Executable acceptance specification

The existing-library characterization is runnable now:

```sh
PYTHONPATH=src python3 examples/shared_result_fanout.py
```

It proves that one disc-art calculation result can feed both Single and Battle calculations, that the two layouts remain separate literal arguments, that PQL can retrieve produced card Parts, and that a small Python traversal can identify both consumers from `PcrRun` testimony. It intentionally does not claim replay.

The new shared capability is accepted only when a DiscStudio-owned fixture can run this sequence with an installed, versioned Pyto wheel:

1. Author separate disc-art, Single-card, and Battle-card calculations. Both Card calculations bind to the same art result.
2. Execute once and retain the program, bound external inputs, result identities, provider identity, and selected result hashes.
3. Load that retained object in a fresh Python process with an explicit calculation registry and rerun it. The card composition and SVG hashes must match.
4. Change disc appearance and rerun a new variant. Both active cards receive the new art result; their arrangements remain unchanged. The old retained program and results remain byte-for-byte unchanged.
5. Change only the Single layout. Dependency inspection must explain that the Single calculation changed and the disc-art calculation need not rerun; this is an explanation first, not a speculative cache.
6. Send the retained program/run record through the real DiscStudio backend and display its dependency view in the browser. Retain the wheel hash, consumer commit, browser result, and comparison output in the checkpoint.

No Pyto implementation starts until the consumer fixture establishes the calculation boundaries and the owner confirms which presentation/config values are external inputs versus calculation results.

## Part-model assessment

The interim Card adapter wraps raw presentation and card-configuration dictionaries in `Part` objects. That is compatible with the current `PxC` seed mechanism, but it blurs the intended meaning that reusable Parts are calculation results.

The acceptance fixture should make the distinction explicit:

- raw request, saved recipe, and user-selected layout are external bound inputs;
- rendered artwork, normalized presentation, Single composition, and Battle composition are named calculation results;
- a result published under a Part address can be reused by later calculations;
- UI labels and persistence IDs remain domain data unless a calculation produces them.

This is an inference to test in DiscStudio, not a request to rename current classes or break the working 0.1.0 consumers.

## Growth loop with DiscStudio

Each Pyto increment follows one measurable loop:

1. Record the exact DiscStudio workflow and the missing shared behavior.
2. Check current Pyto and keep an executable characterization showing what already works.
3. Change one shared seam in Pyto; keep domain rules in DiscStudio.
4. Run a consumer example from an editable install during development.
5. Build a new versioned wheel, install it in a clean environment, and rerun library plus consumer checks.
6. Exercise the real backend and browser; compare meaningful outputs, not only HTTP status.
7. Retain source commits, wheel hash, program/run evidence, screenshots when visual behavior matters, and known uncertainties.
8. Advance the implementation branch while preserving the prior review checkpoint.

This loop measures LAB growth by a real consumer gaining a reusable programming ability. A package release alone is not completion.

## Durable queue

1. **Executable-program replay:** close the seam above with one DiscStudio Card fixture, a versioned wheel, and fresh-process replay evidence.
2. **Exact annotation attachment:** once the DiscStudio owner reports the actual annotation API, attach a raw reaction to the exact program, invocation, result, and design variant; reload and retrieve the displayed inputs and computation. Status: awaiting owner evidence.
3. **Comparison:** compare retained programs and selected results so a user can see whether code, bindings, or produced values changed. Keep the first comparison specific to Card/art behavior.
4. **Inspection and query:** expose dependency questions demonstrated by consumers. Start with ordinary traversal over the executable program; do not silently turn PQL into a graph-mining framework.
5. **Visualization:** derive Mermaid and browser views from the same executable program representation. Preserve domain-specific image and Card views as runnable evidence.
6. **Tools and scripts:** keep clean-install, wheel-hash, consumer-run, output-comparison, and checkpoint capture commands on D and repeatable without source-path injection.
7. **Agent workflow:** give agents a cloneable LAB starter with a pinned wheel, one runnable domain program, retained inputs/results, and explicit boundaries for proposed shared extraction.
8. **Further domain migration:** port one demonstrated ChainSpot, Chess, or Wumpus program at a time. Keep the domain program runnable while extracting only repeatedly useful shared behavior.

Pending items stay pending. In particular, current evidence does not establish a stable Card calculation language, a replay schema, an annotation integration, dependency-aware caching, or a complete Python replacement for the ChainSpot Node bridges.
