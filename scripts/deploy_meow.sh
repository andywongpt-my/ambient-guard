#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$HOME/ambient-guard"
REPO="https://github.com/andywongpt-my/ambient-guard.git"

if [ -d "$APP_DIR/.git" ]; then
  echo "== pull =="
  git -C "$APP_DIR" fetch origin --quiet
  git -C "$APP_DIR" checkout main --quiet
  git -C "$APP_DIR" pull --ff-only origin main
else
  echo "== clone =="
  git clone "$REPO" "$APP_DIR"
fi

cd "$APP_DIR"

# Env: mock mode for first deploy (server has no `bee login` yet).
cat > .env <<'EOF'
AMBIENT_GUARD_BEE_MODE=mock
POSTGRES_USER=ambient
POSTGRES_PASSWORD=ambient
POSTGRES_DB=ambient_guard
DATABASE_URL=postgresql+psycopg://ambient:ambient@db:5432/ambient_guard
EOF

echo "== docker compose up =="
docker compose -p ambient-guard up -d --build

echo "== wait for health =="
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:18080/health >/dev/null 2>&1; then
    echo "HEALTHY"; curl -fsS http://127.0.0.1:18080/health; echo; break
  fi
  sleep 2
done

echo "== containers =="
docker compose -p ambient-guard ps
