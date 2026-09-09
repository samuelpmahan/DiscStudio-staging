# Task 16

Intent: watch it think: the tick page plays a record Tick by Tick with play, pause and step, each Calculation's reads, writes and value appearing when it finished, at recorded speed or slower
Starting point: 12c65281bf9999f5d44ff5b1b883594ca9d5cdb0 (proof: fresh clone on D:/ after task 15)
Verify: node --test pyto/viewer/test
Allow: pyto/viewer/tick-viewer.html pyto/viewer/tick-viewer.js pyto/viewer/adapters.js pyto/viewer/embed.mjs pyto/viewer/test pyto/viewer/README.md
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} Default speed: the speed selector defaults to "10x slower" rather than "1x real" (a 26 ms run is over before anyone can watch it at 1x) or "100x slower" (dramatic but slow for a big record). Should the default depend on the record's total duration instead of being fixed?
{?} Now marker placement: "now" is shown only as text in the toolbar (`tick N · id`) plus the clock, not as a highlight on the Calculation's own card in the list below. Should the currently-completing card also get a visual (e.g. an outline or scroll-into-view), given the owner's "activations appearing" framing?
{?} Speed change mid-playback: changing the speed dropdown while Play is running restarts the schedule from the beginning at the new speed, rather than rescaling the remaining Calculations and continuing from where it was. Is restarting the right call, or should progress be preserved?
{?} `?play=1` / `--play` autostart: both begin playing immediately (not just switch to playback mode with the page paused, empty, waiting for a press of Play). Is autostart the right default for someone opening a shared link or an `embed.mjs --play` file?
{?} Partial durations: RECORD.md allows `duration_ms: null` per invocation. A record where only some Calculations have a duration still plays in "real duration" mode, and the untimed ones complete instantly (cost 0 ms) rather than falling back to 400 ms just for themselves. Is instant-for-the-untimed-ones the right mix, or should a missing duration cost the 400 ms fallback even inside an otherwise-timed run?
