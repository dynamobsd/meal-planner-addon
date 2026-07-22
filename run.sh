#!/usr/bin/with-contenv bashio
# Démarre le backend FastAPI. L'ingress HA proxifie vers le port 8099.
set -e

export MP_DB_PATH="/data/meals.db"
export MP_FRONTEND_DIST="/app/frontend_dist"

cd /app
exec python -m uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port 8099 \
    --proxy-headers \
    --forwarded-allow-ips "*"
