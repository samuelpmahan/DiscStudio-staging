#!/usr/bin/env bash
# questions.sh: re-mine pyto/questions.md (the {?} root) from the command
# line, instead of by hand -- so a Socratic session asks the record what is
# still open and what default each open item takes, in one command
# (pyto/experiments/tasks/13/packet.md).
#
# Usage: questions.sh [open|provisional|resolved|all] [--grep <word>] [--count]
# Default mode is "open".
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QFILE="$SCRIPT_DIR/../questions.md"
[ -f "$QFILE" ] || { echo "questions.sh: not found: $QFILE" >&2; exit 1; }

# python: $PYTHON if set, else this repo's own .venv, else python3/python on
# PATH (same search as check_all.sh).
_root_for_python="$(cd "$SCRIPT_DIR/../.." && pwd)"
if [ -z "${PYTHON:-}" ]; then
  for _c in "$_root_for_python/.venv/bin/python" "$_root_for_python/.venv/Scripts/python.exe"; do
    [ -x "$_c" ] && PYTHON="$_c" && break
  done
fi
PYTHON="${PYTHON:-$(command -v python3 || command -v python)}"

MODE="open"
GREP_WORD=""
COUNT_FLAG=0
while [ $# -gt 0 ]; do
  case "$1" in
    open|provisional|resolved|all) MODE="$1"; shift ;;
    --grep) GREP_WORD="${2:-}"; shift 2 ;;
    --count) COUNT_FLAG=1; shift ;;
    *) echo "questions.sh: unknown argument: $1" >&2; exit 1 ;;
  esac
done

PYTHONIOENCODING=utf-8 "$PYTHON" - "$QFILE" "$MODE" "$GREP_WORD" "$COUNT_FLAG" <<'PYEOF'
import re, sys
from collections import Counter

qfile, mode, grep_word, count_flag = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] == "1"
lines = open(qfile, encoding="utf-8").read().split("\n")

# Walk the file, tracking the current "## " section. Each "### {?} Label"
# heading (sometimes several labels, comma-separated, continued on further
# "###" lines -- the mega-list headings) starts one block; its body runs
# until the next "###" or "##" heading.
blocks = []
section = ""
i, n = 0, len(lines)
while i < n:
    line = lines[i]
    if line.startswith("### "):
        heading = [line]
        i += 1
        while i < n and lines[i].startswith("### "):
            heading.append(lines[i]); i += 1
        labels = re.findall(r"\{\?\}\s*(\w+)", " ".join(heading))
        body = []
        while i < n and not lines[i].startswith("### ") and not lines[i].startswith("## "):
            body.append(lines[i]); i += 1
        blocks.append((labels, section, body))
        continue
    if line.startswith("## "):
        section = line[3:].strip()
    i += 1

def flatten(body):
    return re.sub(r"\s+", " ", " ".join(body)).strip()

entries = []
for labels, sect, body in blocks:
    flat = flatten(body)
    sm = re.search(r"Status:\s*(.*?\.)(?=\s|$)", flat) or re.search(r"Status:\s*(.*)$", flat)
    status_body = sm.group(1).strip() if sm else "(none found)"
    status_line = "Status: " + status_body
    low = status_body.lower()
    if low.startswith("resolved"):
        cls = "resolved"
    elif "provisional" in low:
        cls = "provisional"
    else:
        cls = "open"
    default = "no default stated"
    for s in re.split(r"(?<=\.)\s+", flat):
        if re.search(r"\b(lean|default)\b", s, re.IGNORECASE):
            # a sentence that opens with "Status: ..." (status and the lean
            # fused in one sentence) would otherwise repeat the Status line
            # verbatim here; keep only the substantive part.
            default = re.sub(r"^Status:\s*", "", s.strip())
            break
    bm = re.search(r"Bites:\s*(.*)$", flat)
    bites = ("Bites: " + bm.group(1).strip()) if bm else None
    for label in labels:
        entries.append(dict(label=label, section=sect, status=status_line,
                             cls=cls, default=default, bites=bites))

def fmt_full(e):
    out = [f"{{?}} {e['label']}  [{e['section']}]", e["status"], f"Default: {e['default']}"]
    if e["bites"]:
        out.append(e["bites"])
    return "\n".join(out)

def fmt_short(e):
    return f"{{?}} {e['label']}  [{e['section']}]\n{e['status']}"

status_counts = Counter(e["cls"] for e in entries)
section_counts = Counter(e["section"] for e in entries)
summary = f"{status_counts['open']} open, {status_counts['provisional']} provisional, {status_counts['resolved']} resolved"

if count_flag:
    print("per status:")
    for k in ("open", "provisional", "resolved"):
        print(f"  {k}: {status_counts[k]}")
    print()
    print("per section:")
    for sect, c in section_counts.most_common():
        print(f"  {sect}: {c}")
    print()
    print(summary)
    sys.exit(0)

if mode == "resolved":
    formatted = [fmt_short(e) for e in entries if e["cls"] == "resolved"]
elif mode == "all":
    formatted = [fmt_full(e) for e in entries]
elif mode == "provisional":
    formatted = [fmt_full(e) for e in entries if e["cls"] == "provisional"]
else:  # open (default): everything not resolved
    formatted = [fmt_full(e) for e in entries if e["cls"] != "resolved"]

if grep_word:
    gw = grep_word.lower()
    formatted = [b for b in formatted if gw in b.lower()]

for b in formatted:
    print(b)
    print()

print(summary)
PYEOF
