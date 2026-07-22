"""Point d'entrée FastAPI de l'add-on.

- Crée la DB au démarrage.
- Expose l'API sous /api.
- Sert le frontend React buildé en statique (chemins relatifs pour l'ingress).
- Gère le préfixe d'ingress via le header X-Ingress-Path.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .config import FRONTEND_DIST
from .database import init_db
from .routers import (
    categories,
    deals,
    grocery,
    import_,
    meal_plan,
    pantry,
    recipes,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Planif Repas & Épicerie",
    version="0.2.0",
    lifespan=lifespan,
    # docs OpenAPI accessibles (relatifs pour l'ingress)
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# --- Routers API ---
app.include_router(recipes.router, prefix="/api")
app.include_router(import_.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(meal_plan.router, prefix="/api")
app.include_router(pantry.router, prefix="/api")
app.include_router(grocery.router, prefix="/api")
app.include_router(deals.router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# --------------------------------------------------------------------------- #
# Service du frontend (SPA) — après les routes /api pour ne pas les masquer
# --------------------------------------------------------------------------- #

_INDEX = FRONTEND_DIST / "index.html"


def _serve_index(request: Request) -> HTMLResponse:
    """Injecte <base href> selon le préfixe ingress, pour que les chemins
    relatifs du bundle résolvent correctement derrière le proxy HA."""
    if not _INDEX.exists():
        return HTMLResponse(
            "<h1>Frontend non buildé</h1><p>Lance <code>npm run build</code> "
            "dans frontend/ ou construis l'image Docker.</p>",
            status_code=200,
        )
    ingress_path = request.headers.get("X-Ingress-Path", "")
    base = f"{ingress_path}/" if ingress_path else "./"
    html = _INDEX.read_text(encoding="utf-8")
    if "<base" not in html:
        html = html.replace("<head>", f'<head><base href="{base}">', 1)
    return HTMLResponse(html)


if FRONTEND_DIST.exists():
    # Assets buildés (js/css) servis tels quels
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        return _serve_index(request)

    @app.get("/{full_path:path}", response_class=HTMLResponse)
    def spa_fallback(full_path: str, request: Request):
        # Fichiers statiques réels (favicon, manifest, sw.js, icônes…)
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        # Sinon : route SPA -> index (client-side routing)
        return _serve_index(request)
else:  # pragma: no cover

    @app.get("/", response_class=HTMLResponse)
    def index_missing() -> HTMLResponse:
        return _serve_index_missing()

    def _serve_index_missing() -> HTMLResponse:
        return HTMLResponse("<h1>Frontend non buildé.</h1>", status_code=200)
