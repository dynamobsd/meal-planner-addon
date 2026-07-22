ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.12

# ---------- Étape 1 : build du frontend React/Vite ----------
FROM node:20-alpine AS frontend
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build          # produit /app/dist (chemins relatifs, base: './')

# ---------- Étape 2 : image finale add-on ----------
FROM ${BUILD_FROM}

# Dépendances système minimales (lxml pour le parsing HTML du fallback JSON-LD)
RUN apk add --no-cache libxml2 libxslt || true

WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Code backend
COPY backend/ ./backend/
# Frontend buildé, servi en statique par FastAPI
COPY --from=frontend /app/dist ./frontend_dist/

COPY run.sh /
RUN chmod a+x /run.sh

CMD ["/run.sh"]
