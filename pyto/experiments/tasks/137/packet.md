# Task 137

Intent: SingleCard and the export queue: Single Disc mode composes one disc with a spotlight design made for it (the photo large, the numbers legible, a winner mark that scales, the score/highlight/winner it has in the battle, an export named after the disc), and every export is a queued job that runs in order - all states, this battle vertical, every disc in the battle - each leaving an export.record receipt and a file, the queue surviving navigation, failures as sentences
Starting point: a87812e363bd904660bbf093804dc4198d16deb8 (land(task-135): constraints defining DiscComp: a battle is composed from reusable Constraints with parameters (discCap, placesPoints, tieRule) the way a competition is, scoring is one Calculation over the battle's states with a receipt (ranks, points, a running total), and the UX for a 5-disc cap battle where the top 3 score 3,2,1 is pick the template, add discs against the cap, tap the order Also carries the review item Boone (the AI PM) raised for the vertical frame, worded for the orientation control task 133 landed ('frame': Landscape and vertical export frames, on the OnTheCourse inspector).)
Verify: npm test
Allow: src index.html tests scripts/browser_test.py scripts/demo_beats.py pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
{?} QueueIsSessionState: the export queue lives in the page's own `ui` object, not on the board: a job is
not a Part, so a reload loses a queue that has not finished, while the receipts it already wrote survive
in the world. A Part for the queue would make it inspectable and restartable like everything else here,
but a Part that changes five times a second during a run is a different animal from the Parts this board
holds, and the kernel has no word for that yet.

{?} SvgExportsAreRecorded: the queue files an `export.record` for SVG jobs too (`type: 'SVG'`), so
`world.exports` is no longer "the PNG exports" -- anything counting that array now has to filter by type.
The alternative (SVG downloads leaving no receipt) is what the studio did before, and it meant half the
exports a person actually made had no record at all.

{?} SinglePresetIsTheProjection: `single` in the card cascade now means OnTheCourse's Single Disc mode and
composes with `layout.singlePresetId`; before this slice it meant the comparison's own design. The
Component Editor's DisplayCard tab still previews whichever preset is selected there, so "the single
projection" and "the card the editor is showing" are two things wearing one word.


{?} DialogsAfterRehydrate: scripts/browser_test.py rehydrates by closing the page and mounting a new one,
and the new page carried no dialog handler, so every `confirm()` after that point was auto-dismissed and
the action behind it silently did nothing (this slice's "clear the lineup" looked like it worked and did
not). The handler is now re-registered on the rehydrated page. Any check written after that line and
before this fix may have been asserting on an action that never happened.
