#!/bin/bash
# usage: run-e2e.sh <project root with backend/ and frontend/> <output dir>
# Starts the backend on a fresh demo database and the built frontend, then runs the leave e2e tests.
set -u
ROOT=$(cd "$1" && pwd); OUT=$(mkdir -p "$2" && cd "$2" && pwd)
HERE=$(cd "$(dirname "$0")" && pwd)
DB="$OUT/e2e.db"; rm -f "$DB"
export DATABASE_URL="sqlite:///$DB" APP_ENV=dev APP_DEBUG=0 MAILER_DSN=null://null
(cd "$ROOT/backend" && php bin/console cache:clear -q && php bin/console doctrine:schema:create -q && php bin/console app:seed-demo -q) > "$OUT/seed.log" 2>&1
setsid bash -c "cd '$ROOT/backend' && exec php -d variables_order=EGPCS -S 127.0.0.1:8000 -t public" > "$OUT/backend.log" 2>&1 &
BACKEND=$!
setsid bash -c "cd '$ROOT/frontend' && npx vite build > '$OUT/build.log' 2>&1 && exec npx vite preview --port 4173 --strictPort" > "$OUT/preview.log" 2>&1 &
FRONTEND=$!
for _ in $(seq 60); do curl -sf http://127.0.0.1:4173/ > /dev/null && curl -sf http://127.0.0.1:8000/api/employees > /dev/null && break; sleep 1; done
cp "$HERE/playwright.config.ts" "$HERE/leave.spec.ts" "$ROOT/frontend/" 2>/dev/null
mkdir -p "$ROOT/frontend/.e2e" && mv "$ROOT/frontend/playwright.config.ts" "$ROOT/frontend/leave.spec.ts" "$ROOT/frontend/.e2e/"
(cd "$ROOT/frontend" && npx playwright test --config .e2e/playwright.config.ts) > "$OUT/e2e.log" 2>&1
STATUS=$?
for r in "$ROOT/frontend/.e2e/results.json" "$ROOT/frontend/results.json"; do [ -f "$r" ] && mv "$r" "$OUT/e2e-results.json"; done
rm -rf "$ROOT/frontend/.e2e" "$ROOT/frontend/test-results"
kill -- -$BACKEND -$FRONTEND 2>/dev/null
echo "e2e exit=$STATUS"
exit $STATUS
