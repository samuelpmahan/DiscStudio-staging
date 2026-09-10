# Students: one homework, graded by machine as far as a machine can go

This page is for somebody who does not program -- a school board member, a parent, a
principal deciding whether any of this is worth a classroom's time. Nothing below
needs you to read any code.

## The caveat, first

Two students who hand in the same fingerprint did **the same computation**. That is
all it means. It does not mean either of them got the right answer. A fingerprint
can only compare two things; it cannot tell you that one of them is correct.

So this is not a machine that marks homework. Deciding whether an answer is *right*
still needs a reference -- a worked answer, a second program written independently,
or a teacher. What the fingerprints buy you is everything *around* that judgement:
you can tell, without trusting anybody, that the work a student handed in is the
work their program actually did, that it was not edited after the fact, and that it
will do the same thing again on your machine. Read every claim below with that
limit in mind.

## What a student does

**1. They write a small program.** Not a wall of code: a handful of named steps over
a store of named values. In this homework there are four steps, called Ticks: read a
CSV of a class's names and scores; compute the average *and* the middle score, which
are one step because neither needs the other; give each student a letter; draw a bar
chart. Each step says out loud what it reads and what it writes, and a step may hold
more than one piece of work when those pieces do not depend on each other.

**2. They run it.** The program does not just print an answer. It leaves a *record*:
for every piece of work, what it read, what it wrote, what it produced, how long it
took, and a fingerprint -- a short string of letters and digits computed from the
result, which changes completely if anything about the result changes. The record is
one file. It can be opened in a browser as a page you step through one step at a
time, and a step that holds two pieces of work neither of which needs the other is
drawn as two cards *side by side*, with that step's **work** (both pieces added up)
and its **latency** (the longer of the two -- the time the step takes if the pieces
run at once) printed underneath it, and the whole run's work against its critical
path at the top of the page. Stepping through, the side-by-side cards appear
together rather than one after the other, and if the record says which worker ran a
piece, or that a time budget stopped the run before it finished, the page says so.

**3. They write a hand-off page.** One page in their own words: what I built, one
line per step, which files I touched, and -- this is the part teachers usually never
see -- a list of the things they were unsure about, each written as a `{?}` line.
That last list is most of learning to program, and it is normally invisible.

**4. A machine checks the mechanical part.** A short program called `grade.py` makes
four checks and no judgements:

| # | The check | What it catches |
|---|---|---|
| 1 | The record is a real record of the agreed shape, read by an independent reader | A record that was hand-written, or that quietly leaves out a field |
| 2 | A fresh, isolated process runs the homework again and gets the identical record | An answer that only works on the student's machine, or a record edited after the run |
| 3 | Every piece of work has a receipt, and each receipt's code fingerprint matches the code on disk right now | Code edited after the run, so the record describes a program that no longer exists |
| 4 | The hand-off gives every step a line of its own in its list of steps, and names every file | A hand-off that quietly omits the step the student did not understand |

Check 4 asks for a line, not a mention: a step counts as named only when the
hand-off's "one line per step" list has a bullet of its own that *starts* with that
step's name -- written `- **Name**`, `- Name:` or `- Name ` -- because a student who
drops a step from the list usually goes on mentioning its name in the prose around
it, and a check that only looked for the name somewhere on the page would let that
through. (Files are looser, and can be: a file counts as named wherever on the page
it appears.)

It prints a short report and exits pass or fail. Nothing in those four checks is a
matter of opinion, and none of them can be argued with.

A separate reading, not part of the pass/fail: `../tick-laws/tick_laws.py --check`
adds the timings up a step at a time, and on this record the **Stats** step is the one
whose work is greater than its latency -- the average and the middle score together
spent more work than they spent time, because two pieces of work sat inside one step,
while every other step spent exactly as much time as work. That makes Stats the first
step in this program where doing things at once would buy anything, and the record
says so before any such thing has been built.

**5. A cold reader does the rest.** Somebody -- another student, a teacher, or an
agent -- who has seen *only the hand-off page*, never the code, writes in plain words
what they believe the program does. Comparing that to what the program actually does
is the grade. If the hand-off is clear, the cold reader gets it right. If the student
padded it, or hid the step they did not understand, the cold reader gets it wrong,
and the gap is the feedback. `grade.py` prints the hand-off and the reader's question
and then stops: it does not score this part, and it says so in its own report.

## Why bother

- **"Show your work" becomes literal.** The record is the work, step by step, with
  the numbers present. A student who cannot explain a step can see exactly what that
  step read and produced.
- **Copying stops being interesting.** Two identical fingerprints are the same
  computation, whoever typed it. That does not catch a copied program -- it catches a
  *claim* that does not match the program, which is the more common problem: the
  record cannot be edited to say something the program did not do without failing
  check 2 or check 3.
- **Nothing depends on the grader's machine.** Check 2 re-runs the homework with the
  environment stripped away, from a directory outside the project. If it only worked
  because of something on the student's laptop, it fails there.
- **The rubric has no teacher in it.** Checks 1-4 are the same for everybody and are
  settled before any human reads a line. What is left for the human is the part only
  a human (or an agent doing a human's job) can do: did this page explain the thing?
- **The `{?}` lines are the record of learning.** Over a term they say what a student
  keeps being unsure about, in their own words, without a profile or a test score.

## Running it, if you ever want to

Three commands, in this directory:

```
python homework.py --out evidence/run-1                    # run the four Ticks, write the record
python grade.py --run evidence/run-1 --handoff HANDOFF.md  # the four mechanical checks
```

and open `evidence/run-1/tick-viewer.html` in any browser to step through the run.

The files are: `homework.py` (the program), `HANDOFF.md` (the student's page),
`grade.py` (the four checks), `test_students.py` (tests of both), this `README.md`,
and `evidence/run-1/` (the committed record, receipts and browser page of one real
run, so the checks run against work that was actually shipped).
