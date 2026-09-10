# Task 34

Intent: interrupts are typed and a shared desk is graded by the class: land.sh --note refuses a line addressed to the owner (**owner**) unless it names one of the three reasons (broke, decision, asked), and neat land <id> --from <remote> <branch> --verify <cmd> --allow <paths> lets the landing repository's brief override the desk's packet
Starting point: e99ce55ac146f7373dc8d42bcb607769c872d614 (land(task-33): neat land from a remote: neat land <id> --from <url-or-remote> <branch> fetches a branch from another repository and lands it here with the same verifier, allowed paths and receipt, so a student's desk in its own repo can be shared into a class repo with one command; selftest covers it with a second scratch repository)
Verify: bash pyto/scripts/neat.sh selftest
Allow: pyto/scripts/neat.sh pyto/scripts/land.sh pyto/LANDING.md pyto/BOARD.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} InterruptTagAnywhere: the reason tag may sit anywhere in the line (`**owner** the suite is red [broke]` passes as readily as `**owner** [broke] the suite is red`), and matching is literal and case sensitive, so `[Broke]` or `(broke)` is refused. Tightening it to "the tag comes first, right after `**owner**`" would make every interrupt read the same way at the price of refusing lines that name their reason plainly in the middle. Nothing checks that the tag is the truth: the rule makes the writer choose one of the three, it does not judge the choice.
{?} InterruptOnlyOwnerLines: only a line beginning `**owner**` is checked. A **started**, **killed**, **landed**, **refused** or **for Codex** line, or any plain note, is untouched even when it is addressed to the owner in words, and a line that mentions `**owner**` after the first character is not an interrupt. That is the board's own wording ("everything else is a note, not an interrupt") read literally; say the word if a note should be checked wherever it addresses the owner.
{?} NeatLandOverrideScope: `--verify`/`--allow` are accepted only after `--from`, so a local `neat land <id>` still runs exactly the packet its own copy packed and there is no way to grade your own desk with a different command from the command line. This answers task 33's `{?} NeatFromVerify` in the direction it named (the class's tests are the real grade) without opening the same door for ordinary landings.
{?} GradedHereMeansOverridden: the Today line says `graded here` whenever either flag is given, including `--allow` alone, where the verifier is still the desk's and only the scope changed. One marker for "this landing was judged by the landing repository's brief, not the packet's" seemed better than two; the receipt is the place that says exactly which command ran and which paths were allowed.
{?} PacketKeepsTheDeskWords: an override changes only what this landing runs; the packet that lands at `pyto/experiments/tasks/<id>/` still carries the desk's own Verify and Allow lines, so the record shows both what the student claimed and what the class checked (the receipt). Rewriting the landed packet to the grader's brief would lose the student's half of that.
