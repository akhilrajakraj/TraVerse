#!/usr/bin/env bash
set -Eeuo pipefail

# TraVerse production deployment orchestrator.
# Uses the repository's existing production Compose override; it does not
# introduce a second deployment stack.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/infrastructure/compose/docker-compose.yml"
PROD_OVERRIDE="${ROOT_DIR}/infrastructure/compose/docker-compose.prod.yml"
PROD_ENV="${ROOT_DIR}/infrastructure/env/production.env"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-traverse}"

export COMPOSE_PROJECT_NAME="${PROJECT_NAME}"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

command -v docker >/dev/null 2>&1 || fail "docker is required"

docker compose version >/dev/null 2>&1 || fail "Docker Compose is required"

[[ -f "${COMPOSE_FILE}" ]] || fail "missing ${COMPOSE_FILE}"
[[ -f "${PROD_OVERRIDE}" ]] || fail "missing ${PROD_OVERRIDE}"
[[ -f "${PROD_ENV}" ]] || fail "missing production.env; provision it outside Git"

COMPOSE=(docker compose -f "${COMPOSE_FILE}" -f "${PROD_OVERRIDE}")

cleanup() {
  if [[ "${DEPLOYMENT_STARTED:-false}" == "true" ]]; then
    echo "Deployment failed. Current service status:"
    "${COMPOSE[@]}" ps || true
  fi
}
trap cleanup ERR

DEPLOYMENT_STARTED=false

echo "==> Validating production Compose configuration"
"${COMPOSE[@]}" config >/dev/null

echo "==> Pulling configured images"
"${COMPOSE[@]}" pull

echo "==> Starting production services"
"${COMPOSE[@]}" up -d --build --remove-orphans
DEPLOYMENT_STARTED=true

echo "==> Waiting for service health"
"${COMPOSE[@]}" ps

for attempt in {1..30}; do
  if curl --fail --silent --show-error --max-time 5 http://127.0.0.1/health/ >/tmp/traverse-health.json; then
    if grep -q '"status": "healthy"' /tmp/traverse-health.json; then
      echo "Health check passed"
      break
    fi
  fi

  if [[ "${attempt}" == "30" ]]; then
    echo "Health response:"
    cat /tmp/traverse-health.json 2>/dev/null || true
    fail "TraVerse health endpoint did not become healthy"
  fi

  sleep 5
done

echo "==> Applying database migrations"
"${COMPOSE[@]}" run --rm django python manage.py migrate --noinput

echo "==> Collecting static files"
"${COMPOSE[@]}" run --rm django python manage.py collectstatic --noinput

echo "==> Restarting application services after migration/static changes"
"${COMPOSE[@]}" up -d django celery nginx

echo "==> Final health verification"
curl --fail --silent --show-error http://127.0.0.1/health/ >/tmp/traverse-health-final.json
grep -q '"status": "healthy"' /tmp/traverse-health-final.json || fail "Final health check failed"

rm -f /tmp/traverse-health.json /tmp/traverse-health-final.json

echo "Deployment completed successfully."
