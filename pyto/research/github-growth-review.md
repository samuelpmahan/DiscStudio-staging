# GitHub repository growth and existing evidence

Collected 2026-09-08T15:44:53.458100+00:00. Authenticated account: `samuelpmahan`.

## Findings

The connected account exposes 22 owned repositories: 17 public and 5 private. Fresh public Git histories were examined across all published branches, including work not on default branches.

From JukeBox repository creation to the latest DiscStudio commit, 4d 2h 39m elapsed. The seven nonempty repositories JukeBox, EmbodiedWumpusWorld, ChessLab, DiscStudio, PageRouter, tidy, and neat contain 61 commits (61 non-merge), with **19,941 source/test/UI line additions and 437 deletions** under the classification below. quick-anno is an eighth repository created during that period, currently empty on GitHub.

The five repositories DiscStudio, PageRouter, tidy, neat, and quick-anno were created on September 7 within 0h 55m. Creation dates indicate publication cadence, not when all underlying code was authored.

The user describes themselves as having little practical JS/TS or computer-vision literacy, with a Java/Spring background. This is user-supplied context, not a skill assessment made from Git. ChainSpot therefore matters as evidence of sustained agent-assisted work in an unfamiliar language and technical domain. The evaluation includes the ability to direct work, inspect intermediate materials, retain investigations, and transfer components into other applications. It would be misleading to frame the portfolio as an experienced CV/TypeScript specialist simply implementing a known design.

## Published history by repository

Dates are repository creation dates in UTC. Spans are earliest to latest non-merge committer timestamps across published branches. Commit counts include merges; line counts exclude merge commits.

| Repository | Created UTC | Commit span | Commits, all/default | Source/test/UI additions | Deletions |
|---|---|---:|---:|---:|---:|
| [ChainSpot](https://github.com/samuelpmahan/ChainSpot) | 2026-08-04 | 35d 17h 27m | 1658/425 | 375,630 | 192,422 |
| [toph](https://github.com/samuelpmahan/toph) | 2026-08-15 | 2d 9h 31m | 52/26 | 15,845 | 3,868 |
| [CloudWatch](https://github.com/samuelpmahan/CloudWatch) | 2026-08-29 | 2h 15m | 9/9 | 629 | 144 |
| [JukeBox](https://github.com/samuelpmahan/JukeBox) | 2026-09-03 | 2d 9h 51m | 16/15 | 1,536 | 7 |
| [EmbodiedWumpusWorld](https://github.com/samuelpmahan/EmbodiedWumpusWorld) | 2026-09-05 | 5h 13m | 9/1 | 2,782 | 103 |
| [ChessLab](https://github.com/samuelpmahan/ChessLab) | 2026-09-05 | 4h 37m | 15/15 | 4,334 | 186 |
| [DiscStudio](https://github.com/samuelpmahan/DiscStudio) | 2026-09-07 | 2h 39m | 8/8 | 8,483 | 96 |
| [PageRouter](https://github.com/samuelpmahan/PageRouter) | 2026-09-07 | 3h 44m | 6/6 | 116 | 0 |
| [tidy](https://github.com/samuelpmahan/tidy) | 2026-09-07 | 13s | 2/2 | 280 | 0 |
| [neat](https://github.com/samuelpmahan/neat) | 2026-09-07 | 1h 54m | 5/3 | 2,410 | 45 |

## Existing examples inspected

These findings come from source, tests, and retained experiment records, not repository names alone. Tests and reported grades were inspected; they were not rerun in this audit.

### ChainSpot: actual reusable investigations and Python implementation

- [Case-variant matrix commit](https://github.com/samuelpmahan/ChainSpot/commit/d0f7487): September 6, 2026, 11:31 UTC; 27 files and 2,837 total text insertions. Includes matrix execution, shared material profiles, resumable branching, retained proof artifacts, and unit tests. This directly addresses the grouped-experiment reuse discussed in the conversation.
- [Python first-class Parts and Calculations](https://github.com/samuelpmahan/ChainSpot/commit/6f9d01d), [PQL](https://github.com/samuelpmahan/ChainSpot/commit/30b1670), [tests](https://github.com/samuelpmahan/ChainSpot/commit/f3ecab3), [real S1 investigation](https://github.com/samuelpmahan/ChainSpot/commit/b1679cb), and [S3 investigation](https://github.com/samuelpmahan/ChainSpot/commit/14a9e1e) are already published. Their recorded committer timestamps span 69 minutes 34 seconds on September 7. Those timestamps establish checkpoint cadence, not independent authorship time.
- Source inspection of `matrix/materials.ts` confirms that profile and pose Calculations are registered in PxC, results are stored at content-addressed Part addresses, and subsequent variants reuse those Parts. The key includes source hash, frame, dimensions, seed, masks, parameters, and calculation revision. This is implemented shared material reuse, rather than a proposed example.
- Python `PQL` at `14a9e1e` supplies exact-Part selection, prefix selection, predicate refinement, value materialization, and cardinality checks. This directly corrects the earlier assumption that every PQL surface was only a sequential list of function calls.
- The standalone quick-anno repository being empty does not mean its implementation is absent. Python code exists inside ChainSpot at `packages/quick_anno_py` and `experiments/quick-anno-python`.

### EmbodiedWumpusWorld: the investigation itself is executable

- Published work resides on [`lab/wumpus-core`](https://github.com/samuelpmahan/EmbodiedWumpusWorld/tree/lab/wumpus-core); looking only at `main` would expose one commit and miss most work.
- [README](https://github.com/samuelpmahan/EmbodiedWumpusWorld/blob/lab/wumpus-core/README.md) records extraction from ChainSpot checkpoint `60f53cd9`, a dependency-free JavaScript runtime, priors, constraints, alternate-prior comparison, and branching replay.
- [Failure-profile experiment](https://github.com/samuelpmahan/EmbodiedWumpusWorld/blob/lab/wumpus-core/experiments/failure-profile/README.md) retains four learner sessions across familiar, renamed, and changed-rule tasks. It distinguishes incomplete world enumeration, wrong weights, aggregation/division, and malformed output. Source and tests accompany the records. This is already an example of using the substrate to investigate agent performance.

### ChessLab: shared substrate in another domain

- [LAB host](https://github.com/samuelpmahan/ChessLab/blob/main/src/lab/host.ts) executes stages through a shared PxC, checks declared versus actual accesses, and records called Calculation identities.
- [S1 calculation](https://github.com/samuelpmahan/ChessLab/blob/main/src/chess/stages/S1/index.ts) reads the frame and S0 materialized objects through PxC and writes analysis through a registered Calculation.
- The [README](https://github.com/samuelpmahan/ChessLab/blob/main/README.md) identifies the same ChainSpot origin. Browser and terminal share the debugger execution path; engine adapters and recorded arena trials are also present.

### DiscStudio: browser consumer with material reuse

- [Integration](https://github.com/samuelpmahan/DiscStudio/blob/main/source/candidate-pxc/README.md) identifies the ChainSpot PQL executor source checkpoint `82f8fc94`, rather than claiming an independent parser.
- The documented semantic cache reuses resolved, overlay, and materialized Parts; view arguments change SVG projection without rerunning the semantic Calculations. [Contract tests](https://github.com/samuelpmahan/DiscStudio/blob/main/tests/candidate-pxc/contract.test.mjs) exercise actual invocation order, Part bindings, and immutable inputs.
- [Composition](https://github.com/samuelpmahan/DiscStudio/blob/main/source/candidate-pxc/composition.js) retains the concrete CV sequence for masks, connected components, badge assembly, recognition, and owned/remaining pixels.

### JukeBox and project tooling

- [JukeBox](https://github.com/samuelpmahan/JukeBox) contains a derived primitive store, a local graph projection, and a set builder. [`lab/composable-mining`](https://github.com/samuelpmahan/JukeBox/tree/lab/composable-mining) adds a mining runner, including a SUBDUE provider and method tests. That branch would be missed by a default-branch-only review.
- [neat](https://github.com/samuelpmahan/neat) uses PxC/PQL to produce its work board and derive shared Calculation impact from compositions. Its five published commits include review/checklist work on additional branches.
- [tidy](https://github.com/samuelpmahan/tidy) and [PageRouter](https://github.com/samuelpmahan/PageRouter) contain promotion/build and deployment/comparison support for the surrounding workflow.

## Complete owned repository list

Private repository names were obtained through the connected account; their contents and histories were not included in the public code-growth measurement.

| Repository | Visibility | Created UTC | Audit coverage |
|---|---|---|---|
| [audio-viz](https://github.com/samuelpmahan/audio-viz) | public | 2025-12-31 | All published Git branches |
| [ChainSpot](https://github.com/samuelpmahan/ChainSpot) | public | 2026-08-04 | All published Git branches |
| [chainspot-corpus](https://github.com/samuelpmahan/chainspot-corpus) | public | 2026-08-15 | All published Git branches |
| [ChainSpot-staging](https://github.com/samuelpmahan/ChainSpot-staging) | public | 2026-08-17 | All published Git branches |
| [ChessLab](https://github.com/samuelpmahan/ChessLab) | public | 2026-09-05 | All published Git branches |
| [CloudWatch](https://github.com/samuelpmahan/CloudWatch) | public | 2026-08-29 | All published Git branches |
| [DiscStudio](https://github.com/samuelpmahan/DiscStudio) | public | 2026-09-07 | All published Git branches |
| [dropToken](https://github.com/samuelpmahan/dropToken) | public | 2021-02-15 | All published Git branches |
| [EmbodiedWumpusWorld](https://github.com/samuelpmahan/EmbodiedWumpusWorld) | public | 2026-09-05 | All published Git branches |
| [helpteachers-api](https://github.com/samuelpmahan/helpteachers-api) | private | Not retrieved | Listed through authenticated account |
| [hithero-api-v2](https://github.com/samuelpmahan/hithero-api-v2) | private | Not retrieved | Listed through authenticated account |
| [hrh-go-v1](https://github.com/samuelpmahan/hrh-go-v1) | private | Not retrieved | Listed through authenticated account |
| [JukeBox](https://github.com/samuelpmahan/JukeBox) | public | 2026-09-03 | All published Git branches |
| [micro-lib](https://github.com/samuelpmahan/micro-lib) | private | Not retrieved | Listed through authenticated account |
| [neat](https://github.com/samuelpmahan/neat) | public | 2026-09-07 | All published Git branches |
| [PageRouter](https://github.com/samuelpmahan/PageRouter) | public | 2026-09-07 | All published Git branches |
| [quick-anno](https://github.com/samuelpmahan/quick-anno) | public | 2026-09-07 | Empty public repository |
| [sep-scrape](https://github.com/samuelpmahan/sep-scrape) | public | 2025-07-23 | All published Git branches |
| [tidy](https://github.com/samuelpmahan/tidy) | public | 2026-09-07 | All published Git branches |
| [tofu](https://github.com/samuelpmahan/tofu) | public | 2026-08-20 | Empty public repository |
| [toph](https://github.com/samuelpmahan/toph) | public | 2026-08-15 | All published Git branches |
| [tort-os](https://github.com/samuelpmahan/tort-os) | private | Not retrieved | Listed through authenticated account |

## Measurement limits

Line additions measure committed text changes, not unique inventions, labor hours, runtime performance, or correctness. Initial imports, copied components, repeated changes, and cherry-picked changes with different SHAs can contribute more than once. This matters especially for ChainSpot branch transfers. Commits shared by multiple branches are counted once per repository; cross-repository copies are not deduplicated.

Source/test/UI counts use recognized programming, UI, shell, and SQL extensions. They exclude documentation, JSON/YAML/config/data, lockfiles, binary files, conventional vendor/build/cache directories, minified files, and source maps. ChessLab also excludes the generated `site/` tree and generated `src/learningCases.ts` fixture. This is a transparent path-based approximation, not a claim that every remaining line is handwritten.

ChessLab alone has 4,118 excluded generated source-like additions and 365,743 data/config additions. The latter include large retained trial records and are not counted as code. The retained records matter as evidence even though they are excluded from the source total.

Unpushed worktrees, local experiments, and external artifacts are outside this public-history count. A standalone `pyto` repository was not present in the 22 owned repositories returned by the connector; this does not imply that Pyto work or its packaged archive does not exist.

The evidence establishes rapid publication of multiple domain consumers, shared-substrate adaptations, and executable investigations. It does not alone isolate how much acceleration PxC caused. The immediate correction is nonetheless decisive: the user already supplied an ecosystem to investigate. Asking them to create a worked example before inspecting it was unsupported.

Raw evidence: [Git history audit](github-growth-audit.json), [public repository metadata](github-public-repositories.json), [authenticated owned repository list](github-owned-repositories.json).
