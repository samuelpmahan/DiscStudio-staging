# Task 72

Intent: what the ChainSpot LAB says a Tick is: pyto/research/chainspot-stages-ticks.md records, with sha:path:line evidence from the lab tips, how Stages S0 to S3 are composed of Ticks in YAML (Mermaid compiled to it, Python mirroring it), that a Tick is a chain of dependent Calculations whose results become inspectable together, that dependencies cross Tick boundaries by Part, that the gateway publishes one Receipt per Tick with no rollback and no parallelism, what compare.ts and the neon sheet compare Tick by Tick, and that tidy's manifest is tidy.manifest.yaml naming S0 to S3 with version, clean and hash, which corrects the tidy scout's .tidy/manifest.json
Starting point: 998f5db53844406b9a827b7973b91fb839cd62e9 (land(task-70): the batch carries only what needs the owner: a root label whose entry quotes the owner deciding counts as answered; neat default <n> <k> '<sentence>' files an agent's default as an answer of kind default (the item leaves the batch, stays overturnable in one sentence, and is written on the root as the session's default, never as the owner's words); neat ask prints the items that need the owner first and says how many there are; the 30 non-meaning items of batch 2 are filed as defaults by the session)
Verify: test -s pyto/research/chainspot-stages-ticks.md && grep -q 'tidy.manifest.yaml' pyto/research/chainspot-stages-ticks.md && grep -q '43e6ea3' pyto/research/chainspot-stages-ticks.md
Allow: pyto/research pyto/experiments/tasks
Candidate: 1 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/research/chainspot-stages-ticks.md

```
pyto/research/chainspot-stages-ticks.md | 107 ++++++++++++++++++++++++++++++++
 1 file changed, 107 insertions(+)
```

## Evidence

- verify: `test -s pyto/research/chainspot-stages-ticks.md && grep -q 'tidy.manifest.yaml' pyto/research/chainspot-stages-ticks.md && grep -q '43e6ea3' pyto/research/chainspot-stages-ticks.md` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.W27coC7BCo) (evidence/check_all.txt)
    suite                         tests  status
    library                         368  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
