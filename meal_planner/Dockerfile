# Base FIGÉE en dur (python:3.12-slim, manifeste multi-arch officiel amd64/arm64).
# On n'utilise PAS `ARG BUILD_FROM` : Home Assistant injecte sinon
# --build-arg BUILD_FROM=ghcr.io/home-assistant/base:latest (Alpine, sans pip)
# et écraserait notre base. En figeant le FROM, ce build-arg est ignoré.

# ---------- Étape 1 : build du frontend React/Vite ----------
FROM node:20-alpine AS frontend
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build          # produit /app/dist (chemins relatifs, base: './')

# ---------- Étape 2 : image finale add-on ----------
FROM python:3.12-slim

# Le loader dynamique doit trouver libpython3.12.so.1.0 (dans /usr/local/lib).
# Sous le runtime HA, /etc/ld.so.cache n'est pas toujours consulté -> sans ça :
# « python: error while loading shared libraries: libpython3.12.so.1.0 ».
# Triple ceinture : config permanente du loader + cache + variable d'env.
# (run.sh re-force aussi LD_LIBRARY_PATH au démarrage.)
ENV LD_LIBRARY_PATH=/usr/local/lib
RUN echo "/usr/local/lib" > /etc/ld.so.conf.d/usr-local-lib.conf && ldconfig

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
