# Hand-off: class scores

**Written by the student. This is the only page the cold reader gets.**

## What I built

I was given one CSV file of a class's names and scores and asked to turn it into a
report: the class average, the middle score, a letter for every student, and a bar
chart of how many students got each letter. I wrote it as a program of five Ticks
over a store of named values. Each Tick is one step, and every step leaves a record
of what it read, what it wrote, how long it took, and a fingerprint of its result,
so anyone can re-run it and get exactly the same record back.

The class has 12 students. The CSV is not read from disk: it is a constant inside
`homework.py`, so the program has no hidden input and nobody can quietly hand it a
different file.

## One line per Tick

- **Parse** -- reads the CSV text out of the store and turns it into a roster: one
  row per student with a name and a whole-number score, sorted by name. It refuses
  a file whose first line is not `name,score`.
- **Mean** -- reads the roster and returns the class average rounded to two
  decimals, together with the total and the number of students, so a reader can
  redo the division themselves. It comes out at 80.5 over 12 students.
- **Median** -- reads the same roster and returns the middle score. The class has
  an even number of students, so it is the average of the two middle scores: 82.5.
- **Letters** -- reads the roster and the cutoffs (A from 90, B from 80, C from 70,
  D from 60, otherwise F, passed in as arguments rather than written into the code)
  and gives every student a letter, keeping the roster's order.
- **Histogram** -- reads the letters and returns a text bar chart, one line per
  letter in A-to-F order, one `#` per student, with the count at the end: 3 A, 4 B,
  3 C, 1 D, 1 F.

Mean and Median are two Ticks and not one because they are two separate readings of
the roster. Keeping them apart is what makes the record show each one's own reads,
duration and fingerprint.

## Which files I touched

- `homework.py` -- the program: the CSV, the five Calculations, the five Ticks, and
  the code that writes the run out.
- `grade.py` -- the mechanical rubric: four checks, and the page it prints for the
  cold reader.
- `test_students.py` -- the tests for both of the above.
- `README.md` -- one page explaining the whole idea to somebody who does not
  program.
- `HANDOFF.md` -- this page.
- `evidence/run-1/record.json` -- the run record my program produced, committed so
  the grader checks the run I actually shipped.
- `evidence/run-1/receipts.json` -- one receipt per step of that run, each carrying
  the fingerprint of the code that ran.
- `evidence/run-1/tick-viewer.html` -- the same record as a page you can open in a
  browser and step through, Tick by Tick.

## What I was unsure about

- `{?}` The mean is rounded to two decimals but the median is not rounded at all.
  For this class both come out short (80.5 and 82.5) so it does not show, but the
  two Ticks are not consistent with each other and I could not decide which way to
  make them match.
- `{?}` If two students have the same name my roster keeps both rows and sorts them
  next to each other. Nothing anywhere says whether that is allowed.
- `{?}` The cutoffs are arguments, so a different rubric is a different run of the
  same program. I do not know whether the grader wants the cutoffs to be part of
  the program instead, which would make them part of the code fingerprint.
- `{?}` The record contains how long each Tick took. Two runs of the same program
  never agree on that, so the grader drops the timings before comparing. I am not
  sure the timings should be in the record at all if nothing may compare them.
