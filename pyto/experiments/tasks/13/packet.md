# Task 13

Intent: questions: one command that prints what is still open at the root with each default, so a session asks from the record instead of re-mining it. neat.sh questions or pyto/scripts/questions.sh
Starting point: 76bc3d2a51c0e5442a0e4e8f519fe7d01484e9f5 (land(task-11): Mounts: a world (a course, a game, a bag) is mounted above an ordinary PxC by an id outside the address space, so one address means the same thing in every world; ported from ChainSpot's PxCRootMounts with its negative test)
Verify: none
Allow: pyto/scripts/questions.sh
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} QuestionsStatusClassifier: questions.sh buckets a Status value as "resolved" only when it
starts with that word, "provisional" when that word appears anywhere in it, and "open" otherwise --
so free-text values like "after, today", "for Parts, yes...", "by rule, yes" and "per day, yes"
(the five Astra questions, `questions.md` lines 309-340) land in "open" alongside plain "open."
entries. Is lumping all non-resolved, non-provisional text into "open" the right default, or should
some of these get their own bucket (e.g. "partial")?

{?} QuestionsDuplicateLabels: `{?} AddressRootIsAMount`, `{?} ValueRetention` and
`{?} MaterialsLocation` each appear twice in questions.md under different sections (once
resolved-by-default plus once still-open-with-a-lean; once bare in the round-five mega-list plus
once detailed in "Added by the Day 3 record stage"). questions.sh does not merge same-label
entries, so both occurrences print, sometimes in different status buckets. Default taken: show
every occurrence as its own block, since each is a distinct thing an agent wrote at a distinct
time. Should the tool instead merge by label and keep only the most detailed or most recent one?

{?} QuestionsDefaultRedundancy: in most of the ChainSpot-mining entries the lean is fused into the
same sentence as the Status verdict ("Status: open, lean adopt the declared kind and drop the
root."). questions.sh strips the leading "Status:" from the Default line so it does not repeat the
label twice, but the remaining text ("open, lean adopt...") still overlaps with the Status line
above it. Default taken: keep the repetition rather than leave Default blank, since a reader
scanning only Default lines still gets the lean. Should Default be omitted instead when it would
just restate Status?
