# -*- coding: utf-8 -*-
"""Smoke : type de plat, filtre, réglages, suggestions + test de migration."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_here = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(_here, "api_smoke3.db")
os.environ["MP_DB_PATH"] = DB
os.environ.pop("ANTHROPIC_API_KEY", None)
for ext in ("", "-wal", "-shm"):
    if os.path.exists(DB + ext):
        os.remove(DB + ext)

# --- 1) Test de migration : crée une table recipes SANS categorie_plat ---
import sqlite3
con = sqlite3.connect(DB)
# Schéma d'origine réaliste (toutes les colonnes SAUF categorie_plat)
con.execute(
    "CREATE TABLE recipes (id INTEGER PRIMARY KEY, titre TEXT NOT NULL, "
    "url_source TEXT, image_url TEXT, portions INTEGER, temps_prep INTEGER, "
    "temps_cuisson INTEGER, instructions TEXT, note_perso TEXT, "
    "note_etoiles INTEGER DEFAULT 0, date_ajout TEXT)"
)
con.execute("INSERT INTO recipes (titre) VALUES ('Ancienne recette')")
con.commit(); con.close()

from backend.database import init_db, engine
init_db()  # doit ajouter la colonne categorie_plat sans planter
cols = {r[1] for r in engine.raw_connection().cursor()
        .execute("PRAGMA table_info(recipes)").fetchall()}
print("colonnes recipes après migration:", sorted(cols))
assert "categorie_plat" in cols, "migration a échoué"
print("Migration ALTER TABLE : OK (colonne ajoutée à une DB existante)")

# --- 2) API ---
from fastapi.testclient import TestClient
import backend.main as m
_ctx = TestClient(m.app); client = _ctx.__enter__()

# types de plat
tp = client.get("/api/types-plat").json()
print("types-plat:", tp[:4], "…", len(tp), "types")
assert "Dessert" in tp and "Plat principal" in tp

# recette avec type de plat
r = client.post("/api/recipes", json={"titre": "Tarte aux pommes", "categorie_plat": "Dessert",
                                      "note_etoiles": 5, "ingredients": []}).json()
assert r["categorie_plat"] == "Dessert"
r2 = client.post("/api/recipes", json={"titre": "Poulet rôti", "categorie_plat": "Plat principal",
                                       "ingredients": []}).json()
# filtre par type
dess = client.get("/api/recipes", params={"categorie_plat": "Dessert"}).json()
assert {x["titre"] for x in dess} == {"Tarte aux pommes"}, dess
assert dess[0]["categorie_plat"] == "Dessert"
# recherche texte
srch = client.get("/api/recipes", params={"q": "poulet"}).json()
assert any(x["titre"] == "Poulet rôti" for x in srch)
print("Type de plat + filtre + recherche : OK")

# réglages (préférences de goûts)
client.put("/api/settings/preferences_gouts", json={"valeur": "Ma blonde aime le poulet, végé le lundi"})
got = client.get("/api/settings/preferences_gouts").json()
assert got["valeur"].startswith("Ma blonde")
print("Réglages persistés : OK")

# suggestions status (non configuré)
st = client.get("/api/suggestions/status").json()
assert st["disponible"] is False
sg = client.post("/api/suggestions/meals", json={"nb_repas": 3}).json()
assert sg["disponible"] is False and sg["ok"] is True
print("Suggestions IA (mode non configuré) : OK — message clair")

_ctx.__exit__(None, None, None)
for ext in ("", "-wal", "-shm"):
    if os.path.exists(DB + ext):
        try: os.remove(DB + ext)
        except OSError: pass
print("\nAPI SMOKE 3 OK")
