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

# libpython3.12.so.1.0 est dans /usr/local/lib, mais le runtime HA ne le
# trouve pas (ni via LD_LIBRARY_PATH ni via le cache) -> crash au démarrage :
# « python: error while loading shared libraries: libpython3.12.so.1.0 ».
# Solution qui ne dépend d'AUCUNE variable d'env : on expose la lib dans
# /usr/lib (chemin TOUJOURS cherché en dur par le loader glibc), + cache + env.
ENV LD_LIBRARY_PATH=/usr/local/lib
RUN echo "/usr/local/lib" > /etc/ld.so.conf.d/usr-local-lib.conf \
    && ln -sf /usr/local/lib/libpython3.12.so.1.0 /usr/lib/libpython3.12.so.1.0 \
    && ldconfig \
    && env -i /usr/local/bin/python3 -c "import sys; print('AUTO-TEST libpython OK', sys.version.split()[0])"

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
