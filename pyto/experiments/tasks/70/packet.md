# Task 70

Intent: the batch carries only what needs the owner: a root label whose entry quotes the owner deciding counts as answered; neat default <n> <k> '<sentence>' files an agent's default as an answer of kind default (the item leaves the batch, stays overturnable in one sentence, and is written on the root as the session's default, never as the owner's words); neat ask prints the items that need the owner first and says how many there are; the 30 non-meaning items of batch 2 are filed as defaults by the session
Starting point: 2b2bcfd0303de2b01f4bd5ffdce96dd674dcded7 (land(task-68): the first batch through the integrated loop: neat ask run once on the tree that holds tasks 65, 66 and 67 together, its batch Part and run record kept as evidence under pyto/experiments/review; FRONTIER.md's Landed adds gain the three (the question loop, the difference before it is shown with counting before mining, the join's gate) in the owner's words)
Verify: cd pyto && python -m unittest tests.test_neat_review && python scripts/walk.py --check
Allow: pyto/src/pyto/neat/review.py pyto/tests/test_neat_review.py pyto/scripts/neat.sh pyto/scripts/walk.py pyto/experiments/review pyto/questions.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
{?} NeedsOwnerIsAWord: a packet line needs the owner when it contains the word owner; that is the agent's own declaration and it misses lines that change meaning without saying so (ChainLatencyIsTheWholeTick, MoleculeAddress, FileIsNotAnEffect were filed as defaults by this rule and are raised in chat by hand).
{?} RootIsCounted: root entries are counted as open on the root and never re-asked in a batch, because the root is the owner's own page; an entry that quotes him deciding is answered.
{?} ReviewPageScope: every packet up to task 59 is the review page's, so its lines are not asked again; the number is a constant in review.py.
{?} DefaultSentences: the 23 defaults filed here restate each packet line's first clause; two were mangled by the shell on the first pass and refiled by hand.
