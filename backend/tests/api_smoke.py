# -*- coding: utf-8 -*-
"""Test d'intégration de l'API via TestClient (stack FastAPI complète)."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

os.environ["MP_DB_PATH"] = os.path.join(os.path.dirname(__file__), "api_smoke.db")
for ext in ("", "-wal", "-shm"):
    p = os.environ["MP_DB_PATH"] + ext
    if os.path.exists(p):
        os.remove(p)

from fastapi.testclient import TestClient
import backend.main as m

# Context manager -> déclenche le lifespan (init_db) comme en prod uvicorn
_ctx = TestClient(m.app)
client = _ctx.__enter__()

# --- health ---
assert client.get("/api/health").json()["status"] == "ok"

# --- categories seedées ---
cats = client.get("/api/categories").json()
print("categories:", len(cats))
assert len(cats) == 14

# --- création d'une recette avec ingrédients ---
payload = {
    "titre": "Test soupe",
    "portions": 4,
    "note_etoiles": 4,
    "note_perso": "Bien avec du pain.",
    "ingredients": [
        {"texte_brut": "2 tomates", "nom_normalise": "tomate", "quantite": 2, "unite": None, "note": None, "categorie_id": cats[0]["id"]},
        {"texte_brut": "500 g de boeuf", "nom_normalise": "boeuf", "quantite": 500, "unite": "g", "note": None, "categorie_id": cats[2]["id"]},
    ],
}
r = client.post("/api/recipes", json=payload)
print("POST /recipes ->", r.status_code)
assert r.status_code == 201, r.text
rid = r.json()["id"]
assert len(r.json()["ingredients"]) == 2
assert r.json()["ingredients"][0]["categorie_nom"] == "Fruits & légumes"

# --- liste ---
lst = client.get("/api/recipes").json()
print("GET /recipes ->", len(lst), "recette(s)")
assert any(x["id"] == rid for x in lst)

# --- détail ---
det = client.get(f"/api/recipes/{rid}").json()
assert det["note_perso"] == "Bien avec du pain."

# --- apprentissage de rayon ---
lr = client.put("/api/categories/learn", json={"nom_normalise": "gruyere", "categorie_id": cats[4]["id"]})
print("PUT /categories/learn ->", lr.status_code)
assert lr.status_code == 204

# --- suppression ---
d = client.delete(f"/api/recipes/{rid}")
print("DELETE /recipes ->", d.status_code)
assert d.status_code == 204
assert client.get(f"/api/recipes/{rid}").status_code == 404

# --- scrape live (réseau, toléré si échec réseau) ---
print("\n--- scrape live ---")
try:
    sr = client.post("/api/recipes/scrape", json={"url": "https://www.ricardocuisine.com/recettes/8407-macaroni-au-fromage-de-grand-mere"}, timeout=30)
    body = sr.json()
    if sr.status_code == 200 and body.get("ok"):
        d = body["draft"]
        print(f"  OK source={body['source']} titre={d['titre']!r} portions={d['portions']} nb_ingr={len(d['ingredients'])}")
        if d["ingredients"]:
            ex = d["ingredients"][0]
            print(f"  ex ingrédient parsé+catégorisé: q={ex['quantite']} u={ex['unite']!r} nom={ex['nom_normalise']!r} rayon={ex['categorie_nom']!r}")
    else:
        print(f"  statut {sr.status_code}: {body}")
except Exception as e:
    print(f"  (scrape réseau non concluant, toléré: {type(e).__name__}: {e})")

# --- scrape échec propre sur URL invalide ---
er = client.post("/api/recipes/scrape", json={"url": "https://example.invalid/nope"})
print("scrape URL invalide ->", er.status_code, er.json().get("error_code"))
assert er.status_code == 422

_ctx.__exit__(None, None, None)
print("\nAPI SMOKE OK")
