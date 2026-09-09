#!/usr/bin/env bash
# check_board_log.sh: guards the one line per landing that land.sh's board()
# function splices under pyto/BOARD.md's "## Today" (see board() at land.sh:46-58,
# called from fail() at land.sh:62 and the successful path at land.sh:178). Every
# line board() writes carries the literal marker **landed** or **refused** right
# after the stamp -- that is the whole of what board()'s two call sites ever pass
# it -- so this checks that every such line starts with the exact
# "- YYYY-MM-DD HH:MM " stamp the heredoc's strftime writes (board(), land.sh:50).
# A heredoc bug that drops the marker, garbles the date, or loses the space is
# caught here instead of by eyeballing 25+ bullets.
#
# Other bullets under "## Today" are the owner's or an agent's own words, typed
# by hand, not machine-stamped (BOARD.md:41-43: "One line per landing attempt,
# newest first, written by the landing script. Lines before 06:53 are the day so
# far, in plain words.") -- this script does not require those to match the
# machine stamp, only the ones board() itself produced.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOARD="$HERE/../BOARD.md"
[ -f "$BOARD" ] || { echo "check_board_log: no such file: $BOARD" >&2; exit 1; }
grep -q '^## Today$' "$BOARD" || { echo "check_board_log: no '## Today' heading in $BOARD" >&2; exit 1; }

# The body of the "## Today" section: from that heading to the next "## " heading,
# both boundary lines dropped.
TODAY="$(sed -n '/^## Today$/,/^## /p' "$BOARD" | sed '1d;$d')"
STAMP='^- [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2} '

bad=0
while IFS= read -r line; do
  [ -n "$line" ] || continue
  case "$line" in
    *'**landed**'*|*'**refused**'*)
      if ! printf '%s\n' "$line" | grep -Eq "$STAMP"; then
        echo "check_board_log: malformed board() stamp: $line" >&2
        bad=1
      fi
      ;;
  esac
done <<< "$TODAY"

[ "$bad" -eq 0 ] || exit 1
echo "check_board_log: ok"
