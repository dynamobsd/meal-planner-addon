# -*- coding: utf-8 -*-
"""Smoke Phase 9 : favoris, duplication de semaine, planning auto, export liste."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_here = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(_here, "api_smoke4.db")
os.environ["MP_DB_PATH"] = DB
os.environ.pop("ANTHROPIC_API_KEY", None)
for ext in ("", "-wal", "-shm"):
    if os.path.exists(DB + ext):
        os.remove(DB + ext)

# DB « existante » sans favori ni categorie_plat -> teste la migration
import sqlite3
con = sqlite3.connect(DB)
con.execute(
    "CREATE TABLE recipes (id INTEGER PRIMARY KEY, titre TEXT NOT NULL, "
    "url_source TEXT, image_url TEXT, portions INTEGER, temps_prep INTEGER, "
    "temps_cuisson INTEGER, instructions TEXT, note_perso TEXT, "
    "note_etoiles INTEGER DEFAULT 0, date_ajout TEXT)"
)
con.commit(); con.close()

from backend.database import init_db, engine
init_db()
cols = {r[1] for r in engine.raw_connection().cursor()
        .execute("PRAGMA table_info(recipes)").fetchall()}
assert "favori" in cols and "categorie_plat" in cols
print("Migration favori + categorie_plat : OK", sorted(c for c in cols if c in ("favori", "categorie_plat")))

from fastapi.testclient import TestClient
import backend.main as m
_ctx = TestClient(m.app); client = _ctx.__enter__()

cats = client.get("/api/categories").json()
cat0 = cats[0]["id"]

# recette + favori
r = client.post("/api/recipes", json={"titre": "Chili", "portions": 4, "ingredients": [
    {"texte_brut": "2 boites de tomates", "nom_normalise": "tomate", "quantite": 2,
     "unite": "boîte", "note": None, "categorie_id": cat0},
]}).json()
assert r["favori"] == 0
fav = client.post(f"/api/recipes/{r['id']}/favori").json()
assert fav["favori"] == 1
onlyfav = client.get("/api/recipes", params={"favori": "true"}).json()
assert any(x["id"] == r["id"] for x in onlyfav)
client.post(f"/api/recipes/{r['id']}/favori")  # re-toggle off
assert client.get("/api/recipes", params={"favori": "true"}).json() == []
print("Favoris (bascule + filtre) : OK")

# planning source + duplication
SRC = "2026-07-20"; DST = "2026-07-27"
client.post("/api/meal-plan", json={"date": "2026-07-21", "type_repas": "souper", "recipe_id": r["id"]})
dup = client.post("/api/meal-plan/duplicate", json={"source_semaine": SRC, "cible_semaine": DST}).json()
assert len(dup) == 1 and dup[0]["date"] == "2026-07-28"  # même décalage (mardi -> mardi)
week_dst = client.get("/api/meal-plan", params={"start": DST}).json()
assert len(week_dst) == 1
print("Duplication de semaine : OK (mardi -> mardi)")

# planning auto (non configuré)
ap = client.post("/api/meal-plan/auto", json={"semaine": SRC, "creneaux": ["souper"]}).json()
assert ap["disponible"] is False and ap["ok"] is True
print("Planning auto (mode non configuré) : OK — message clair")

# génère la liste puis exporte en texte
client.post("/api/grocery/generate", json={"semaine": SRC})
exp = client.get("/api/grocery/export", params={"semaine": SRC}).json()
print("--- export ---")
print(exp["texte"])
assert "tomate" in exp["texte"].lower()
assert "Liste d'épicerie" in exp["texte"]
print("Export texte de la liste : OK")

_ctx.__exit__(None, None, None)
for ext in ("", "-wal", "-shm"):
    if os.path.exists(DB + ext):
        try: os.remove(DB + ext)
        except OSError: pass
print("\nAPI SMOKE 4 OK")
