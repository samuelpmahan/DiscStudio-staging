# Proven LAB reference sources (read-only)

Pyto is a Python transfer of the LAB that already runs in three domains. These are the exact
reference sources the transfer is measured against. They are copied for inspection only and
are never imported by pyto.

| Directory | Source | Head or commit |
|---|---|---|
| chainspot-matrix/ | samuelpmahan/ChainSpot `scripts/chainspot-lab/sweep/matrix/*`, `matrix.ts`, `packages/alg/src/experiments/labBranching.ts`, unit tests, matrix-review README | d0f7487eb99dc884ed04b492ed9bd68d47ca4ee4 ("Add LAB case-variant matrix, shared PxC profiles, and resumable Poisson loss branches") |
| chesslab-lab/ | samuelpmahan/ChessLab `src/lab/*.ts` | 6809fbf (main) |
| wumpus-core/ | samuelpmahan/EmbodiedWumpusWorld `src/core/*.js` and two tests | 6043d35 (lab/wumpus-core) |
| ../../src/core/exec.js (this repo) | ChainSpot PxC/PQL browser core transcribed in DiscStudio at 82f8fc9 | see file header |

The transfer ledger that compares them with pyto is `pyto/research/lab-transfer-ledger.md`.
