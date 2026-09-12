#!/usr/bin/env bash
# verify_pages.sh: the Pages workflow's steps (.github/workflows/pages.yml), run locally in the same order,
# so a landing's verify is the deploy's verify. Unit tests to a TAP report, the exact static build, dist served
# over HTTP, the browser test against that origin, then the review checkpoint over the two reports.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
mkdir -p test-results
node --test --test-reporter=tap tests/*.test.js > test-results/unit.tap
tail -8 test-results/unit.tap
npm run build --silent
PORT="${PORT:-4173}"
PORT="$PORT" node scripts/serve.mjs dist > test-results/server.log 2>&1 &
server=$!
trap 'kill "$server" 2>/dev/null || true' EXIT
for _ in $(seq 1 50); do curl -sf "http://127.0.0.1:$PORT/" > /dev/null 2>&1 && break; sleep 0.2; done
python scripts/browser_test.py --url "http://127.0.0.1:$PORT/" | tail -4
node scripts/review_checkpoint.mjs
