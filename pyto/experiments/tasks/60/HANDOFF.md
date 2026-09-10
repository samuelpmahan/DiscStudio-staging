# Task 60: SUBDUE-PxC-PQL moonshot (the owner's last call of the sprint, not OS): mine the run records for molecules. A new experiment pyto/experiments/molecules builds one labelled graph from every committed pyto-run-record@1 (invocations labelled by Calculation address, Parts by address shape; reads, writes and declared-order edges), runs the SUBDUE miner from hiding-primitives over it, and names each mined substructure a molecule: a repeated chain of Calculations over Part shapes, emitted as a PQL document that runs it, a PQL query that finds its Parts in a store, and the compression it buys in bits; report.md is rebuilt byte for byte and --check refuses drift; tests pin determinism and that every instance really embeds in its record

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Stop here first (the owner's rule)

Read this page, `pyto/BOARD.md`, and the packet. No fourth file yet. Then write the one question
you would answer by reading another hundred thousand tokens of code, and ask the owner instead.
His answer is worth more than the reading: the last session that read everything first was
confidently wrong about half of it, and one sentence from him undid each wrong half. The answer
goes on `pyto/questions.md` verbatim, as `{?} Label: ...` with his words, so the next agent starts
one stupid question deeper. Only then read further and do the work below.

## Get the code (once)

```
git clone -b claude/os-sprint-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/60
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/60:pyto/experiments/tasks/60/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff fb8f643 origin/exp/60 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
```

## Why this repository is worth twenty minutes

pyto is a Python transfer of a design the owner proved three times in JavaScript and TypeScript
(ChainSpot, ChessLab, EmbodiedWumpusWorld): a store of named values (PxC), pure functions over them
(Calculations), and a program that names which functions run in which order (a PCR, made of Ticks).
Every run leaves receipts: what each function read and wrote, how long it took, and a digest of its
source. From receipts you get three things for free: a cache (same inputs and digest, skip the call,
also across processes), a replay that verifies a shipped record in a fresh process, and a per-Tick
view of what the algorithm used. The founding need is the last one: the owner's course-map parser
had to fit five seconds on a phone, and nothing it used was visible. pyto is the workshop where that
visibility is designed before it is stripped for speed. JavaScript is first class; Python is where
the design is checked.

Do not take that from this page. In two minutes:

```
bash pyto/scripts/check_all.sh                                        # nine suites, ~600 tests
python pyto/experiments/grouped-ablation/run_cached.py --out /tmp/hit  # a miss, then two hits, one from a fresh process
node pyto/viewer/embed.mjs pyto/viewer/fixtures/pyto-grouped-ablation.json --out /tmp/hit/ticks.html
```

The tests were checked by mutation (each guards a specific line). The fixtures for the JavaScript
port are 440 byte-exact cases. `pyto/questions.md` is where anyone unsure writes `{?} Label: ...`
and the owner answers; read it before assuming. `pyto/BOARD.md` is the owner's one page.

## What was asked

SUBDUE-PxC-PQL moonshot (the owner's last call of the sprint, not OS): mine the run records for molecules. A new experiment pyto/experiments/molecules builds one labelled graph from every committed pyto-run-record@1 (invocations labelled by Calculation address, Parts by address shape; reads, writes and declared-order edges), runs the SUBDUE miner from hiding-primitives over it, and names each mined substructure a molecule: a repeated chain of Calculations over Part shapes, emitted as a PQL document that runs it, a PQL query that finds its Parts in a store, and the compression it buys in bits; report.md is rebuilt byte for byte and --check refuses drift; tests pin determinism and that every instance really embeds in its record

## Starting point

d9934c299ce88b05fa17b21960187422d37f606e (land(task-57): chains inside a Tick: the owner, 2026-09-10: 'Calculations inside a Tick must be independent was added as a rule, while your existing ChainSpot program deliberately chains dependent Calculations inside a Tick. Your definition was the moment that sequence becomes inspectable.' The kernel stops refusing a Calculation that binds an earlier sibling's result; inside a Tick the Calculations are a sequence in declared order and the Tick boundary is where the sequence becomes inspectable; a Tick with no sibling reads may run at once, a Tick with them runs in order even under parallel=True; two siblings producing one address is still refused; the decision goes on pyto/questions.md in the owner's words). MAIN may have moved since: `git log --oneline fb8f643..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- A  pyto/experiments/molecules/README.md
- A  pyto/experiments/molecules/mine.py
- A  pyto/experiments/molecules/molecules.py
- A  pyto/experiments/molecules/report.md
- A  pyto/experiments/molecules/test_molecules.py

```
pyto/experiments/molecules/README.md         |  18 ++
 pyto/experiments/molecules/mine.py           | 104 ++++++++++
 pyto/experiments/molecules/molecules.py      | 209 ++++++++++++++++++++
 pyto/experiments/molecules/report.md         | 285 +++++++++++++++++++++++++++
 pyto/experiments/molecules/test_molecules.py |  59 ++++++
 5 files changed, 675 insertions(+)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/molecules -p 'test_*.py' && python experiments/molecules/mine.py --check` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.tlfjBZvSu1) (evidence/check_all.txt)
    suite                         tests  status
    library                         330  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules             5  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
{?} MoleculeScheme: exact names a program's own molecule (the ablation's fit-fit-score triple), shape names a studio-wide one (produce-then-consume); which one the owner means by molecular synthesis is his call, both are reported.
{?} PartLabelKind: Parts are labelled by full address (exact) or the constant "part" (shape); labelling by value kind (json/text/svg) would sit between the two and was not tried.
{?} MoleculeAddress: the emitted PQL document is one Tick named molecule-<rank>; whether a molecule should become a new Calculation address fn.molecule.<canon-digest> is left open.
{?} CompoundMolecules: later SUBDUE ranks are built on an earlier rank's SUB node; they are listed with their instances but no PQL document is emitted for them (only primitive ranks embed vertex-for-vertex).
{?} PxMolecules: "px molecules <record...>" in px.py is not done (time).
{?} DocumentDropsArgs: the emitted PQL document carries call, with and into but not the invocation's args or id, so where two Calculations differ only by args (exact rank 1: fn.ablation.fit all versus drop_g0) the document names the molecule's wiring and cannot run the instance it was cut from; args belong in it, and the spelling should follow pyto's own writer (src/pyto/graph.py to_pcr_dict) rather than the studio's bare-address form. Found by the verifier, not fixed in the 30 minutes.
{?} OnePartQuery: a one-Part molecule is spelled PQL.prefix(address), which also matches longer addresses; PQL.part(address) is the exact form the API has.
{?} HashRefUnchecked: the fn:<id>#<address> branch of resolve() trusts the address without checking it is among the producer's into (record_schema.py does check); no committed record uses the form.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 60 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 60`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-60): SUBDUE-PxC-PQL moonshot (the owner's last call of the sprint, not OS): mine the run records for molecules. A new experiment pyto/experiments/molecules builds one labelled graph from every committed pyto-run-record@1 (invocations labelled by Calculation address, Parts by address shape; reads, writes and declared-order edges), runs the SUBDUE miner from hiding-primitives over it, and names each mined substructure a molecule: a repeated chain of Calculations over Part shapes, emitted as a PQL document that runs it, a PQL query that finds its Parts in a store, and the compression it buys in bits; report.md is rebuilt byte for byte and --check refuses drift; tests pin determinism and that every instance really embeds in its record`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
