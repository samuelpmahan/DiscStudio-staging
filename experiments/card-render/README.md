# Guided card-render experiments

One local lever for making guesses, comparing them and retaining what we learn.
This is an experimental candidate, not a new execution framework or a promotion.
`candidate.yaml` describes the cohesive bundle; `task.yaml` describes the rendering
question and its Parts & Calculations.

## The first question

Can a small runtime change make repeated card rendering faster while preserving
the same SVG, resolved fields, warnings and reuse receipts?

The frozen baseline is commit `941f3544f82f80f88c7228abec646b0889d575fa`.
Seven workloads cover four presentation presets, an embedded photo with absent
flight numbers, a three-disc scene and a twelve-disc scene. Cold, warm and six
authored-edit transitions yield 26 equivalence observations. These are sample
workloads, not a claim about every possible user world or real-course CV accuracy.

The CPU profile points to repeated stable serialization of unchanged values.
The candidate reuses only the previous input signature when all inputs are the
same recursively frozen plain-data values. It defers the recursive proof until
an input actually repeats; the first render still serializes normally. Mutable, shallow-frozen and accessor
inputs take the original serialization path. The existing 24-slot PxC memo ring,
its Part shapes, content signatures and result lookup are unchanged. This is a
small optimization inside the existing Calculation registration helper.

## Run it

Use Node 22 or later; the measurement harness has no installed dependencies.
Run commands from the repository root. Every output directory must be new.

```sh
node experiments/card-render/run.mjs capture --source . --out evidence/card-render/my-baseline
node experiments/card-render/run.mjs profile --baseline evidence/card-render/my-baseline --out evidence/card-render/my-profile
# Make one candidate change, or point --source at an isolated candidate checkout.
node experiments/card-render/run.mjs compare --baseline evidence/card-render/my-baseline --source . --out evidence/card-render/my-attempt --hypothesis "What changed and why it might help"
node experiments/card-render/run.mjs verify --baseline evidence/card-render/my-baseline
```

Capture snapshots the executable JS source and complete concrete inputs. Baseline
outputs must reproduce in a fresh Node process before they are kept. Comparison
reruns both source snapshots in alternating order for seven paired rounds. The
timed section excludes subprocess launch/import and input cloning. Cold includes
runtime construction plus its first render; warm measures rendering with an
already populated memo ring. Neither is browser paint or page-load latency.

`contract.json` fixes a local decision rule before the candidate runs: more than
5% improvement on warm broadcast cards in at least six of seven rounds, with no
workload's paired median regressing more than 10%. These thresholds are experimental
choices, not general requirements. Inspect raw samples when the result is close.

Changed source is copied into each attempt, alongside its base commit, source
fingerprints, patch and working-tree status. The comparison is an ordinary
`fn.exp.cardRender.compare` Calculation executed by the existing JS PxC/PQL. Its
inputs and output are retained in `parts.json`; `composition.json` names the
bindings. All attempt directories survive, including failed runs.

`review.json` keeps the candidate explanation, exact evidence fingerprint and an
unanswered human prompt. It does not authenticate the reviewer or automatically
accept, merge, publish or promote anything. An experiment can run without waiting
for that answer. Sam's response informs what we try or keep next.

If a harness change is needed, capture a new baseline; keep the earlier evidence.
Hashes detect drift, not hostile tampering. This local workflow does not need a
distributed lock service. Keep concurrent candidates in independent runtimes and
source directories so they do not share output addresses.

## Optional pixel comparison

With an existing Playwright/PNGJS installation and Chromium executable:

```sh
node experiments/card-render/pixels.mjs BASELINE_DIR ATTEMPT_DIR NEW_PIXEL_DIR NODE_MODULES_DIR CHROMIUM_EXECUTABLE
```

This renders each retained SVG in one browser, at a fixed viewport/device scale,
blocks network requests and compares exact RGBA pixels. It saves both PNGs,
browser/library identity, per-case differences and a black/white negative control.
It does not compare different OS/font installations or test application controls.
No browser result is inferred from SVG equality alone.

The first actual browser run matched 24/26 pairs despite byte-identical input
SVGs in all pairs. That exposes nondeterminism in browser rasterization/capture,
not evidence of a candidate SVG change. Treat pixel parity as unverified until
same-input repeatability is established. The failed result and images are kept;
the comparator does not raise its tolerance to make them pass.

## Capture verification

Install this checkout's `pyto` package editable in a local environment
(`python -m pip install --no-deps -e ./pyto`). The executable USE.md examples
deliberately ignore PYTHONPATH; some also need repository-side fixtures, which
a wheel install does not include. Then run:

```sh
PYTHON=/path/to/environment/bin/python node experiments/card-render/verify.mjs evidence/card-render/my-verification
```

This runs the Node/app/viewer tests, neat tests, executable docs and build, keeping
each command, output, exit status and changed-file fingerprints. It sets the
Python interpreter used by JS cross-runtime tests and retains failures too.
Optionally append named checks (`node-tests`, `neat-tests`, `use-docs`, `painter-fixtures`, `build`)
for a focused rerun; its report explicitly records that smaller scope.

## How the small recipes support each other

These are local adaptations, not an installed pstack mode or new global agent rules:

| Recipe | Use here |
| --- | --- |
| [Build the lever](https://github.com/cursor/plugins/blob/main/pstack/skills/principle-build-the-lever/SKILL.md) | Keep one working example, then make its capture/run/compare process rerunnable. |
| [Prototype](https://github.com/cursor/plugins/blob/main/pstack/skills/poteto-mode/playbooks/prototype.md) | Name a decision and build enough to answer it. Keep the learning even if the code is rejected. |
| [Feature](https://github.com/cursor/plugins/blob/main/pstack/skills/poteto-mode/playbooks/feature.md) | Agree on data shapes and shared dependencies before assigning disjoint implementation work. |
| [Visual parity](https://github.com/cursor/plugins/blob/main/pstack/skills/poteto-mode/playbooks/visual-parity.md) | Lock the visual behavior while changing its implementation. |
| [Hillclimb](https://github.com/cursor/plugins/blob/main/pstack/skills/poteto-mode/playbooks/hillclimb.md) | Measure a hypothesis against a fixed workload; retain rejected attempts and explain the choice. |

The accompanying neat repairs are complementary: `equiv` reconstructs historical
inputs and retains attempts; `hot` distinguishes measured cost from missing data.
Neither a shell exit code nor an agent's recommendation is Sam's acceptance.

## Review this candidate

Read `RESULTS.md` for the actual observations and limitations, then inspect
`candidate.patch`, `comparison.json`, the retained source snapshots, tests and
the pixel report named there. `UPDATE-REVIEW.md` is the pre-repair review; its
unrelated LAB/concurrency/undo findings are deliberately not folded into this
bundle. Candidate costs and gains should justify its inclusion individually.
