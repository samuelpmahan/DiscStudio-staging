# Fresh DiscStudio package for Astra (sent as a self-contained paste; this file is the archive)

One Terra, two Lunas. Luna A wires the ported painter (pyto/consumers/discstudio-card/port/painter)
into the studio's art path inside the existing Calculations (src/runtime.js, src/presentation.js,
tests). Luna B builds the first format, a printable shelf sheet, as fn.disc.format.shelfSheet in
src/formats/shelf-sheet.js with a fixture and tests. Terra runs npm test, npm run build and the
browser check, repairs at most twice, hands back branch astra/discstudio-1 with a report and any
{?} lines. The cloud session lands it with land.sh --from and runs check_all once.

Correction recorded: the mailbox is an archive, not a channel. Astra cannot read a repository on
its own; every package goes to the owner as one self-contained paste.
