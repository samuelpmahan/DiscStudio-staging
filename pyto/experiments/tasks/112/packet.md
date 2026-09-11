# Task 112

Intent: port ChainSpot's S0 and S1 stage documents to the studio's PxC core as fn.lab.* Calculations run through readPql/invokePql
Starting point: ddb2428bb3b1a778d404c9ea53409880c5392633 (land(task-111): the brain on the disc shelf: one PxC program over the studio's own material, the seven molds' flight numbers and the twelve discs' weights as dataset Parts, four Ticks (describe, correlate, cluster, regress) through the brain's Calculations, observed, with the record the Tick viewer draws)
Verify: node --test tests/*.test.js
Allow: src/lab tests pyto/experiments/tasks pyto/research
Candidate: 25 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  src/lab/address.js
- A  src/lab/fixtures.js
- A  src/lab/lab.js
- A  src/lab/mermaid.js
- A  src/lab/path.js
- A  src/lab/s0.js
- A  src/lab/source.js
- A  src/lab/source/S0.args.json
- A  src/lab/source/S0.mmd
- A  src/lab/source/S0.pcr.yaml
- A  src/lab/source/S0.stage.yaml
- A  src/lab/source/S1.args.json
- A  src/lab/source/S1.mmd
- A  src/lab/source/S1.pcr.yaml
- A  src/lab/source/courses/AlexClark.json
- A  src/lab/source/courses/DashsTrack.json
- A  src/lab/source/courses/HeritagePark.json
- A  src/lab/source/courses/Lenard.json
- A  src/lab/source/courses/NorthPark.json
- A  src/lab/source/courses/TheREC.json
- A  src/lab/source/courses/TowneLake.json
- A  src/lab/yaml.js
- A  tests/lab-mermaid.test.js
- A  tests/lab-path.test.js
- A  tests/lab-s0.test.js

```
src/lab/address.js                       |  43 ++++++++
 src/lab/fixtures.js                      |  52 ++++++++++
 src/lab/lab.js                           |  98 ++++++++++++++++++
 src/lab/mermaid.js                       | 150 +++++++++++++++++++++++++++
 src/lab/path.js                          | 171 +++++++++++++++++++++++++++++++
 src/lab/s0.js                            | 159 ++++++++++++++++++++++++++++
 src/lab/source.js                        |   4 +
 src/lab/source/S0.args.json              |   1 +
 src/lab/source/S0.mmd                    |  19 ++++
 src/lab/source/S0.pcr.yaml               |  29 ++++++
 src/lab/source/S0.stage.yaml             |  20 ++++
 src/lab/source/S1.args.json              |  12 +++
 src/lab/source/S1.mmd                    |  81 +++++++++++++++
 src/lab/source/S1.pcr.yaml               | 137 +++++++++++++++++++++++++
 src/lab/source/courses/AlexClark.json    |   8 ++
 src/lab/source/courses/DashsTrack.json   |  28 +++++
 src/lab/source/courses/HeritagePark.json |   8 ++
 src/lab/source/courses/Lenard.json       |   8 ++
 src/lab/source/courses/NorthPark.json    |   7 ++
 src/lab/source/courses/TheREC.json       |  14 +++
 src/lab/source/courses/TowneLake.json    |   8 ++
 src/lab/yaml.js                          | 100 ++++++++++++++++++
 tests/lab-mermaid.test.js                |  71 +++++++++++++
 tests/lab-path.test.js                   |  82 +++++++++++++++
 tests/lab-s0.test.js                     |  69 +++++++++++++
 25 files changed, 1379 insertions(+)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.qNOO1pvDYK) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               756  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
