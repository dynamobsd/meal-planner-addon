"""Configuration centrale : chemins et constantes.

Les chemins par défaut ciblent le volume /data de l'add-on (persistant).
En dev local, on retombe sur un dossier ./data à la racine du projet.
"""
from __future__ import annotations

import os
from pathlib import Path

# Racine du projet (…/meal-planner-addon)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Chemin de la base SQLite. En prod (add-on) : /data/meals.db
DB_PATH = Path(os.environ.get("MP_DB_PATH", _PROJECT_ROOT / "data" / "meals.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Frontend buildé servi en statique. En prod : /app/frontend_dist
FRONTEND_DIST = Path(
    os.environ.get("MP_FRONTEND_DIST", _PROJECT_ROOT / "frontend" / "dist")
)

# IP du proxy ingress HA. En prod, on n'accepte que cette IP.
# (Laissé permissif en dev ; l'application stricte est optionnelle.)
INGRESS_PROXY_IP = "172.30.32.2"
STRICT_INGRESS = os.environ.get("MP_STRICT_INGRESS", "0") == "1"
