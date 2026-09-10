# A class in a repository

The owner, of neat-learning: "Easy, neat based teacher-student stuff. Teacher says
okay assignments in, they submit and get instant scores." And, the same night, the
correction that shaped this: "Private by default, sharing ez."

**A class repo** is a repository the teacher owns. It holds the assignment package and
nothing of anybody's work until they share it: `assignments/scores/BRIEF.md` (the task
in a student's words), `assignments/scores/grader.sh` (the verifier that scores a
submission), and a reference solution a person can read. After a landing it also holds
`submissions/<student>/`. Its board, `.neat/BOARD.md` under "Today", is the gradebook:
one line per attempt, written by the landing script from an exit code and a score,
never by hand.

**A desk** is the student's own repository. Their MAIN, their tasks, their receipts,
their `{?}` lines. Nobody sees it. They start work with `neat new`, hand it in with
`neat pack`, and that is the whole submission: the branch is pushed to *their* remote
and the score of their own checks is in the evidence before anyone looks.

**The one command a teacher runs**, from the class repo:

    bash tools/neat.sh land 0 --from <the desk's remote> exp/0 \
        --verify "bash assignments/scores/grader.sh" --allow "submissions/ada"

It fetches that branch, merges it under the one allowed path, runs the *class's*
verifier instead of the desk's, and writes the score into the landing receipt and one
line on the board. If the verifier fails, nothing lands and the refusal is on the board
with its score. Unsharing is `neat undo`.

`bash make_class.sh --selftest` builds all of that under a temp directory -- a class,
a desk, a student who retries, undoes and kills tasks, and one graded landing -- and
checks it. `python tutor.py <desk> > tutor.html` renders how that student works from
their own record: what they retried, what they undid, where they wrote `{?}`, how long
each Tick took them, what scored what. It reads no clock and prints no path from
outside the desk, so the same desk twice is the same bytes.

## The caveat, first and last

Identical fingerprints prove the same computation, not the right answer. `grade.py`'s
four checks say the student's record is honest about the program they wrote; they
cannot say the program is right. `cold_reader.py` says the reader's answer accounts for
every step and every file on the page; it cannot say the answer is correct. A verifier
still needs a reference, and the real grade is a person reading the hand-off cold.

## Files

- `make_class.sh` -- builds the class, the desk, and the graded landing. `--selftest`.
- `tutor.py` -- the tutoring page, a pure function of one desk.
- `cold_reader.py` -- the mechanical half of the cold read.
- `cold-reader.txt` -- one cold reader's answer to `pyto/experiments/students/HANDOFF.md`.
- `test_classroom.py` -- the suite.
