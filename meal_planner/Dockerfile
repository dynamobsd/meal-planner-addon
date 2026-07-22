# Image de base : python:3.12-slim (garantie multi-arch amd64/arm64, sans
# dépendance à un tag d'image de base HA introuvable). HA passe BUILD_FROM
# depuis build.yaml.
ARG BUILD_FROM=python:3.12-slim

# ---------- Étape 1 : build du frontend React/Vite ----------
FROM node:20-alpine AS frontend
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build          # produit /app/dist (chemins relatifs, base: './')

# ---------- Étape 2 : image finale add-on ----------
FROM ${BUILD_FROM}

WORKDIR /app
COPY backend/requirements.txt ./
# lxml / pydantic-core fournissent des wheels manylinux pour amd64/arm64 :
# aucune dépendance système à compiler.
RUN pip install --no-cache-dir -r requirements.txt

# Code backend
COPY backend/ ./backend/
# Frontend buildé, servi en statique par FastAPI
COPY --from=frontend /app/dist ./frontend_dist/

COPY run.sh /
RUN chmod a+x /run.sh

CMD ["/run.sh"]
