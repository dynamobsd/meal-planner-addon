#!/usr/bin/with-contenv bashio
# Démarre le backend FastAPI. L'ingress HA proxifie vers le port 8099.
set -e

export MP_DB_PATH="/data/meals.db"
export MP_FRONTEND_DIST="/app/frontend_dist"

# Clé API Anthropic (option de l'add-on) -> feature « Alerte aubaines »
if bashio::config.has_value 'anthropic_api_key'; then
    export ANTHROPIC_API_KEY="$(bashio::config 'anthropic_api_key')"
fi

cd /app
exec python -m uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port 8099 \
    --proxy-headers \
    --forwarded-allow-ips "*"
