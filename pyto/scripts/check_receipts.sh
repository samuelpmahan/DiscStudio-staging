#!/usr/bin/env bash
# check_receipts.sh: every committed landing receipt has the fields land.sh actually writes
# (pyto/scripts/land.sh:64-68 builds a failed receipt, :144-160 builds a verified one), so a
# schema regression in land.sh (a renamed or dropped key, e.g. "unclaimed") is caught here
# instead of by every consumer of the receipt. Sub-second, no venv, no git network call.
#
#   exit 0  every *.json under pyto/experiments/landings/ has the keys required for its
#           declared "result", and that result is "verified" or "failed"
#   exit 1  otherwise; the offending file(s) and the missing keys are printed
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$(cd "$HERE/.." && pwd)"
PYTHON="$(command -v python3 || command -v python)"

"$PYTHON" - "$PY/experiments/landings" <<'PYEOF'
import json, os, sys

root = sys.argv[1]
# The exact keys land.sh writes for each result, per the heredocs cited above.
COMMON = ["schema", "id", "package", "base_sha", "result", "at"]
REQUIRED = {
    "verified": COMMON + ["verifier", "check_all", "claimed", "unclaimed", "landed_by", "result_sha", "note"],
    "failed": COMMON + ["reason"],
}

bad = []
n = 0
for dirpath, _dirnames, filenames in os.walk(root):
    for name in filenames:
        if not name.endswith(".json"):
            continue
        path = os.path.join(dirpath, name)
        n += 1
        try:
            doc = json.load(open(path, encoding="utf-8"))
        except Exception as exc:
            bad.append("%s: not valid JSON (%s)" % (path, exc))
            continue
        result = doc.get("result")
        required = REQUIRED.get(result)
        if required is None:
            bad.append("%s: result is %r, want 'verified' or 'failed'" % (path, result))
            continue
        missing = [k for k in required if k not in doc]
        if missing:
            bad.append("%s: missing %s" % (path, ", ".join(missing)))

if n == 0:
    print("check_receipts: no receipt found under %s" % root)
elif bad:
    print("check_receipts: %d of %d receipt(s) bad:" % (len(bad), n))
    for b in bad:
        print("  " + b)
    sys.exit(1)
else:
    print("check_receipts: %d receipt(s) OK" % n)
PYEOF
