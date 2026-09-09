# From a function registry to an AI operating system

How this session's picture of pyto changed, in the order it changed, with the sentence of yours
that moved it each time. Written on 2026-09-09 at your request. Nothing here is a claim about
what pyto should be; it is a record of what made the picture move.

## The thesis in one paragraph

On the first morning pyto was a dictionary of named values (PxC), a registry of functions keyed
by `fn.` addresses, and a program that calls them in named groups (a PCR made of Ticks). A
function registry. By the end of the day the same three objects read as a kernel: the store is a
filesystem whose worlds are mounts, the registry is the table of what may run, the Ticks are the
scheduler's quantum, the receipts are the trace, the record is `/proc`, the render is the
terminal, landing is the package manager, and the owner is init. Not one line of the kernel
changed to make that true. What changed was what each thing was *for*, and every change came
from one of your sentences.

## The ladder, step by step

**0. Starting point: a registry.** `REGISTRY = {"fn.ablation.split": split, ...}`, a PxC with
five verbs, a PCR that runs Ticks in first-mention order. Day 1 proved it runs; Day 2 proved a
run can be retained and replayed in a fresh process with digests that refuse a forgery. At that
point the interesting object was the *function*: its source digest, its inputs, its output.

**1. "Is there actually something here or am I just wasting my time."** Answering honestly
forced the first move: the registry is not the value. Anyone can keep a dict of functions. The
value was in what the run *leaves behind*: a receipt per invocation saying what was read, what was
written, how long it took, and a digest of the source that did it. The function stopped being the
subject; the receipt became the subject.

**2. The origin story (the pathfinding in ChainSpot, nothing visible, ABFeature, PixelCache,
PCR to Tick[] to Calculation[]).** This named the founding need: seeing what the algorithm used,
per Tick. A Tick is the unit at which you are allowed to look. That turned "receipts" from a
verification trick into an observability layer, and it fixed the grain: not per function, not per
run, per Tick.

**3. "The MAIN use of this is as a cache for my CV alg with a budget of 5000 ms."** Now the store
had a job and a number. A cache keyed by content, with a budget, means every backend is judged by
what it costs before the first hit. DuckDB at 5.3 s and OpenCV were out for that reason alone.
That is an operating-system way of thinking about storage: the cold start is the price of the
mount, and the budget is the process's allowance.

**4. "There's 10,000,000 ways to define a hit. ELK. I'd like JS to be first class."** ELK
separated the roles cleanly: Calculations compose meaning (Logstash), PxC stores it
(Elasticsearch), and the PCR itself is the render definition (Kibana). "A hit is any use of a
Part or Calculation" killed a week of over-definition. "JS first class" made Python the workshop
and JavaScript the runtime, which is the compiler relationship in step 9.

**5. "Ticks can be the unit of composition for Competitions. Proposals, not facts."** A Tick was
no longer only a grouping for reading; it became the unit at which alternatives run side by side
and predictions are kept apart from what happened. That is a scheduling quantum and a namespace
rule (`proposal.*` never writes into facts) at once.

**6. "Each imported external application gets its own namespace. Registrations? Yuck."** This
was the moment the address space became a filesystem. No registration means no central table to
edit before a thing exists: a namespace is a mount, and mounting is the act. Later the branch
mining showed ChainSpot had already decided exactly this, with a test that the world's name is
never a segment of the address: the root is a mount, outside the address space, so one address
means one thing in every world.

**7. "A backend is judged first by cold-start cost in the browser, per application. Portable AI
Linux like thing."** You said the word. Everything before it was already shaped like this; the
sentence gave the shape a name and a rule: kernel tiny, everything else a mount chosen per
application by measured cold start, never by configuration.

**8. "Can JS single-threaded nature be exploited for simple OS-like scheduling."** Yes, and it is
already there: the event loop is the scheduler, and a Tick boundary is the yield point, the
observation point and the budget checkpoint at the same time. One `await` between Ticks is the
whole first scheduler. Nothing more until a Tick is measured too slow.

**9. "OC OperationalCalculation: any syscall lol, keep it simple and safe. I'm stripping out
visibility to hit the 5 ms CV goal."** Two kinds of Calculation and no third: `fn` is pure, `oc`
is the syscall table, the only place an effect happens, allowed by name. And visibility as a
zero-cost flag turned the workshop-to-runtime relationship into a compiler: the retained program
plus the registry is the compile input, the workshop runs it with visibility on and keeps the
receipts, the runtime runs the same document with visibility off, and equal digests prove the
compile changed nothing. ChainSpot's `planFingerprint` and `executeCompiledPlan` were that idea
already.

**10. "brew, npm, pip: a verified skill in 2.5 seconds."** The package manager. `px add
<address>` is verified by replaying its own shipped record in a fresh process. Installation and
verification are the same act, because the record is the proof.

**11. "The week becomes a specialization: you handle Linux and orchestrate Codex."** Kernel and
userland. This session owns the kernel; Astra's teams are userland processes with bounded
packages, verifiers that exit 0 or 1, and a hand-back branch.

**12. "What even is landing any more. We need an ACTUAL landing protocol, that's where I always
fuck up."** The install path. One script, one receipt per landing, refusals that name the file
and the fix, checkpoints that never claim. A landing is the moment a change becomes part of the
running system; everything before it is a process that has not exited yet.

**13. "neat is AI version control in one tree. One MAIN, one EXP with ids. Caveman simple."**
Processes. EXP/<id> is an address space: a copy of the whole tree with its own python, so what
runs there cannot see or touch MAIN. The packet (intent, starting point, candidate, evidence,
uncertain) is the process's context, carried inside it so a fresh agent on any machine can read
it and act. `neat land` is the exit syscall that commits the process's work through the install
path.

**14. "AHI. Augmented Human Intelligence. Human centric, AI extends." And "{?} is good."** The
owner is init. `{?}` is the root of the tree because every Part and Calculation exists because a
question there was answered or is still open. The system's job is to bring you decisions in your
own words with a default, and to carry your answers forward automatically. That is the whole
reason the OS metaphor holds: a kernel exists to serve a user, not to be admired.

**15. "The function stopped being the subject; the receipt became the subject. One of the few
things I actually know about Linux is 'everything file'."** Your line, after reading the first
fourteen. It is the sentence the whole ladder was climbing toward. In Unix the file is not the
interesting object either; the interesting thing is that one interface, a path you can read and
write, covers devices, pipes and processes, so a few tools compose over all of them. pyto's version:
everything is a Part, an address and a value, and every use leaves a receipt, which is a Part too.
The reference runtime already does it: DiscStudio's `runtime.js` writes `px.receipt.<name>` into
the store beside the program. Python keeps receipts on the run object instead. That is the one
place the transfer breaks the rule, and fixing it collapses four open questions into one:
receipts, landing receipts, packets, decisions and proposals all become Parts under reserved
segments, written only when visibility is on, never read by a Calculation. Then PQL is `ls` and
`grep` over all of them, and the viewer is `cat`.

## The mapping, as it stands

| operating system | pyto |
|---|---|
| kernel | PxC's five verbs, PCR and Ticks, receipts; one file each |
| filesystem, mounts | the address space; a world (course, game, bag, repo) is a mount, never a segment |
| syscall table | `oc` OperationalCalculations, allowed by name, recording reads and writes as Parts |
| scheduler, quantum | the JS event loop; a Tick boundary is the yield, observation and budget point |
| processes | EXP/<id> copies of the tree with their own python; the packet is the process context |
| `/proc`, `dmesg` | the run record (`pyto-run-record@1`); the board's Today log |
| terminal | the PCR render (Kibana): a dependency-free page that opens from disk |
| compiler | retained PQL document plus registry, run with visibility on in the workshop, off in the runtime, equal digests as the proof |
| package manager | `px add <address>`, verified by replaying its shipped record; `land.sh` receipts |
| init, root | the owner, through the `{?}` root and the board |
| storage backends | chosen per mount by measured cold start; DuckDB and OpenCV out of the runtime |

## What did not change

The store is still a dictionary. The registry is still a dictionary. A PCR still runs Ticks in
first-mention order and a Calculation is still a function with an address. The kernel is under a
thousand lines and none of the reframings added a line to it that a test did not demand. The
metaphor earned its place by naming what the parts were already doing, not by adding parts.

## Two things I got wrong on the way, kept here on purpose

I resolved the biggest questions alone for most of a day (cache first, JS as the reference) and
asked you nothing; the `{?}` root and the rule that decisions come back to you in your own words
with a default came from your calling that out. And I told you the suite was green from a run that
predated a change that made it red; the landing protocol now says a claim of green names a
receipt or is not made. Both mistakes are the reason two of the fifteen steps above exist.
