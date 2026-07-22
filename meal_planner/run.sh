#!/usr/bin/env bash
# Démarre le backend FastAPI. L'ingress HA proxifie vers le port 8099.
set -e

export MP_DB_PATH="/data/meals.db"
export MP_FRONTEND_DIST="/app/frontend_dist"

# Clé API Anthropic depuis les options de l'add-on (/data/options.json).
# HA écrit les options dans ce fichier ; pas de dépendance à bashio.
if [ -f /data/options.json ]; then
    KEY="$(python3 -c 'import json; print(json.load(open("/data/options.json")).get("anthropic_api_key",""))' 2>/dev/null || true)"
    if [ -n "$KEY" ]; then
        export ANTHROPIC_API_KEY="$KEY"
    fi
fi

cd /app
exec python -m uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port 8099 \
    --proxy-headers \
    --forwarded-allow-ips "*"
