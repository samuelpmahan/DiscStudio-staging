#!/usr/bin/env bash
# proof.sh: runs BOARD.md's "## The test" fenced block, verbatim except for the clone target, for
# real in a fresh temp clone, and leaves a receipt so "I need proof I'm not one of them" is a
# record, not a claim. See pyto/BOARD.md "## The test".
#   pyto/scripts/proof.sh [--keep] [--selftest]
# --keep:     leave the temp clone on disk instead of deleting it.
# --selftest: parse the board block, print the substituted commands and target dir, run nothing;
#             exit 0 if the block has >=4 commands and the first is a git clone, else exit 1.
set -euo pipefail
KEEP=0; SELFTEST=0
for a in "$@"; do
  case "$a" in
    --keep) KEEP=1;;
    --selftest) SELFTEST=1;;
    *) echo "usage: proof.sh [--keep] [--selftest]" >&2; exit 2;;
  esac
done
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$(cd "$HERE/.." && pwd)"
ROOT="$(cd "$PY/.." && pwd)"
# Interpreter order, as in land.sh/check_all.sh: $PYTHON, the repo's own .venv, then PATH.
if [ -z "${PYTHON:-}" ]; then
  for _c in "$ROOT/.venv/bin/python" "$ROOT/.venv/Scripts/python.exe"; do
    [ -x "$_c" ] && PYTHON="$_c" && break
  done
fi
PYTHON="${PYTHON:-$(command -v python3 || command -v python)}"
BOARD="$PY/BOARD.md"
[ -f "$BOARD" ] || { echo "proof.sh: no such file: $BOARD" >&2; exit 1; }
# Drive letter from this script's own path (e.g. /d/pyto-socratic.../pyto/scripts -> /d).
DRIVE="$(printf '%s' "$HERE" | sed -E 's#^(/[A-Za-z])/.*#\1#')"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
CLONE_DIR="$DRIVE/pyto-proof-$STAMP"
# The fenced block under "## The test", verbatim.
BLOCK="$("$PYTHON" - "$BOARD" <<'PYEOF'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r'^## The test\n(.*?)(?=^## |\Z)', text, re.S | re.M)
if not m:
    sys.exit("no '## The test' section")
fences = re.findall(r'```\n(.*?)```', m.group(1), re.S)
if not fences:
    sys.exit("no fenced block under '## The test'")
sys.stdout.write(fences[0])
PYEOF
)"
# The first line's clone target, substituted everywhere it occurs (the clone line and the cd line
# that names it); every other command, including comments, is left byte-identical.
FIRST_LINE="$(printf '%s\n' "$BLOCK" | grep -m1 '^git clone ')"
[ -n "$FIRST_LINE" ] || { echo "proof.sh: first command is not a git clone: $FIRST_LINE" >&2; exit 1; }
ORIG_DIR="$(printf '%s' "${FIRST_LINE%%#*}" | awk '{print $NF}')"
SUBSTITUTED="$(printf '%s\n' "$BLOCK" | sed "s#$ORIG_DIR#$CLONE_DIR#g")"
mapfile -t CMDS < <(printf '%s\n' "$SUBSTITUTED" | sed '/^[[:space:]]*$/d')
if [ "$SELFTEST" -eq 1 ]; then
  echo "target dir: $CLONE_DIR"
  printf '%s\n' "${CMDS[@]}"
  [ "${#CMDS[@]}" -ge 4 ] && [[ "${CMDS[0]}" == git\ clone* ]] && exit 0
  exit 1
fi
RECEIPT_STEM="${STAMP}-proof"
RECEIPT_DIR="$PY/experiments/proofs"
LOG_DIR="$RECEIPT_DIR/$RECEIPT_STEM"
mkdir -p "$LOG_DIR"
RESULTS_FILE="$(mktemp)"; COMMANDS_FILE="$(mktemp)"
printf '%s\n' "${CMDS[@]}" > "$COMMANDS_FILE"
# Run each command in order, bash -e per command, not stopping at the first failure; a `cd` line
# updates the directory the next command runs in, tracked ourselves since each step is its own
# subshell.
CWD="$ROOT"; i=0
for cmd in "${CMDS[@]}"; do
  i=$((i + 1))
  logfile="$LOG_DIR/$(printf '%02d' "$i").log"
  start=$(date +%s)
  set +e
  (cd "$CWD" && bash -e -c "$cmd") > "$logfile" 2>&1
  rc=$?
  set -e
  end=$(date +%s)
  printf '%s\t%s\n' "$rc" "$((end - start))" >> "$RESULTS_FILE"
  body="${cmd%%#*}"
  case "$body" in
    cd\ *)
      tgt="$(printf '%s' "$body" | sed -E 's/^cd[[:space:]]+//; s/[[:space:]]+$//; s/^"//; s/"$//')"
      newcwd="$( (cd "$CWD" && cd "$tgt" && pwd) 2>/dev/null || true )"
      [ "$rc" -eq 0 ] && [ -n "$newcwd" ] && CWD="$newcwd"
      ;;
  esac
done
COMMIT_SHA="$(git -C "$CLONE_DIR" rev-parse HEAD 2>/dev/null || echo null)"
RECEIPT_PATH="$RECEIPT_DIR/$RECEIPT_STEM.json"
# Write the receipt and splice the Today line, both from one interpreter (JSON and the CRLF/LF
# splice are safer there than in shell).
TODAY_LINE="$("$PYTHON" - "$BOARD" "$RECEIPT_PATH" "$RECEIPT_STEM" "$COMMANDS_FILE" "$RESULTS_FILE" "$LOG_DIR" "$COMMIT_SHA" "$CLONE_DIR" <<'PYEOF'
import json, sys, datetime, os
board_path, receipt_path, stem, commands_file, results_file, log_dir, commit_sha, clone_dir = sys.argv[1:9]
commands = open(commands_file, encoding='utf-8').read().splitlines()
results = [ln.split('\t') for ln in open(results_file, encoding='utf-8').read().splitlines()]
def suite_table(logpath):
    if not os.path.exists(logpath):
        return None
    out, capture = [], False
    for ln in open(logpath, encoding='utf-8', errors='replace').read().splitlines():
        if ln.strip() == '== per-suite counts':
            capture = True
        if capture:
            out.append(ln)
            if ln.startswith('ALL SUITES PASSED') or ln.startswith('SOME SUITES FAILED'):
                break
    return out or None
steps, first_fail = [], None
for idx, (cmd, (rc, secs)) in enumerate(zip(commands, results), start=1):
    logname = '%02d.log' % idx
    rc = int(rc)
    step = {"n": idx, "command": cmd, "exit": rc, "seconds": int(secs), "log": logname,
            "check_all_table": suite_table(os.path.join(log_dir, logname))}
    steps.append(step)
    if rc != 0 and first_fail is None:
        first_fail = step
result = "green" if first_fail is None else "red"
sha = commit_sha if commit_sha != "null" else None
receipt = {"schema": "pyto-proof-receipt@1", "stamp": stem, "clone_dir": clone_dir,
           "commit_sha": sha, "steps": steps, "result": result,
           "first_failing_step": first_fail["n"] if first_fail else None,
           "at": datetime.datetime.utcnow().isoformat() + "Z"}
with open(receipt_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(receipt, f, indent=2)
    f.write("\n")
raw = open(board_path, "rb").read()
crlf = b"\r\n" in raw
text = raw.decode("utf-8").replace("\r\n", "\n")
stamp_dt = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
detail = "all green" if first_fail is None else ("step %d failed" % first_fail["n"])
sha7 = sha[:7] if sha else "unknown"
line = "**proof** %s: fresh clone of %s, %d steps, %s, receipt %s" % (result, sha7, len(steps), detail, stem)
bullet = ("- " + stamp_dt + " " + line)[:199]
marker = "## Today\n"
head, tail = text.split(marker, 1)
intro, rest = tail.split("\n\n", 1)
new_text = head + marker + intro + "\n\n" + bullet + "\n" + rest
if crlf:
    new_text = new_text.replace("\n", "\r\n")
open(board_path, "wb").write(new_text.encode("utf-8"))
print(receipt_path)
print(bullet)
PYEOF
)"
rm -f "$RESULTS_FILE" "$COMMANDS_FILE"
[ "$KEEP" -eq 1 ] || rm -rf "$CLONE_DIR" "$HIT_DIR"
printf '%s\n' "$TODAY_LINE"
