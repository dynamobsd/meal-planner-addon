# -*- coding: utf-8 -*-
"""Smoke d'intégration des routes Phases 3-5 (planning, épicerie, garde-manger, rayons, deals)."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

os.environ["MP_DB_PATH"] = os.path.join(os.path.dirname(__file__), "api_smoke2.db")
os.environ.pop("ANTHROPIC_API_KEY", None)  # teste le mode "non configuré"
for ext in ("", "-wal", "-shm"):
    p = os.environ["MP_DB_PATH"] + ext
    if os.path.exists(p):
        os.remove(p)

from fastapi.testclient import TestClient
import backend.main as m

_ctx = TestClient(m.app)
client = _ctx.__enter__()

cats = client.get("/api/categories").json()
cat_id = {c["nom"]: c["id"] for c in cats}

# --- 2 recettes avec ingrédients qui s'agrègent ---
def mk_recipe(titre, portions, ings):
    return client.post("/api/recipes", json={
        "titre": titre, "portions": portions, "note_etoiles": 0, "ingredients": ings,
    }).json()

r1 = mk_recipe("Sauce tomate", 4, [
    {"texte_brut": "2 tomates", "nom_normalise": "tomate", "quantite": 2, "unite": None, "note": None, "categorie_id": cat_id["Fruits & légumes"]},
    {"texte_brut": "200 g de boeuf", "nom_normalise": "boeuf", "quantite": 200, "unite": "g", "note": None, "categorie_id": cat_id["Boucherie & poissonnerie"]},
])
r2 = mk_recipe("Salsa", 4, [
    {"texte_brut": "3 tomates", "nom_normalise": "tomate", "quantite": 3, "unite": None, "note": None, "categorie_id": cat_id["Fruits & légumes"]},
    {"texte_brut": "0.3 kg de boeuf", "nom_normalise": "boeuf", "quantite": 0.3, "unite": "kg", "note": None, "categorie_id": cat_id["Boucherie & poissonnerie"]},
])

SEM = "2026-07-20"  # un lundi

# --- Planning : ajoute les 2 recettes cette semaine ---
mp1 = client.post("/api/meal-plan", json={"date": "2026-07-20", "type_repas": "souper", "recipe_id": r1["id"]})
mp2 = client.post("/api/meal-plan", json={"date": "2026-07-21", "type_repas": "souper", "recipe_id": r2["id"], "portions_planifiees": 8})
print("POST meal-plan:", mp1.status_code, mp2.status_code)
assert mp1.status_code == 201 and mp2.status_code == 201
week = client.get("/api/meal-plan", params={"start": SEM}).json()
print("GET meal-plan semaine ->", len(week), "repas ; ex titre:", week[0]["recette_titre"])
assert len(week) == 2

# --- Garde-manger : on a déjà 1 tomate ---
client.post("/api/pantry", json={"nom_ingredient": "tomate", "quantite": 1, "unite": None})

# --- Génère la liste ---
rayons = client.post("/api/grocery/generate", json={"semaine": SEM}).json()
print("\n--- LISTE D'ÉPICERIE (générée) ---")
flat = {}
for ray in rayons:
    for it in ray["items"]:
        flat[it["nom"]] = it
        print(f"  [{ray['categorie_nom']}] {it['nom']}: {it['quantite_totale']} {it['unite'] or ''}"
              + (f"  ⚠ {it['avertissement']}" if it["avertissement"] else ""))

# tomate: r1=2 (portions 4/4=x1) + r2=3*(8/4=x2)=6 => 8, moins 1 (pantry) = 7
assert abs(flat["tomate"]["quantite_totale"] - 7) < 1e-6, flat["tomate"]
# boeuf: 200 g + 0.3kg*(8/4=x2)=600 g => 800 g
assert abs(flat["boeuf"]["quantite_totale"] - 800) < 1e-6, flat["boeuf"]
assert flat["boeuf"]["unite"] == "g"
print("\nAgrégation + mise à l'échelle + garde-manger : OK (tomate=7, boeuf=800 g)")

# --- Coche un item, puis "j'en ai déjà" ---
tid = flat["tomate"]["id"]
assert client.patch(f"/api/grocery/{tid}", json={"coche": 1}).json()["coche"] == 1
bid = flat["boeuf"]["id"]
assert client.post(f"/api/grocery/{bid}/have", params={"add_to_pantry": True}).status_code == 204
after = client.get("/api/grocery", params={"semaine": SEM}).json()
noms_after = {it["nom"] for ray in after for it in ray["items"]}
assert "boeuf" not in noms_after
print("Coche + « j'en ai déjà » : OK (boeuf retiré, ajouté au garde-manger)")

# --- Régénère : la coche de tomate doit être préservée ---
rayons2 = client.post("/api/grocery/generate", json={"semaine": SEM}).json()
tom2 = next(it for ray in rayons2 for it in ray["items"] if it["nom"] == "tomate")
assert tom2["coche"] == 1
print("Régénération : coche préservée : OK")

# --- Rayons : créer, renommer, réordonner, supprimer ---
newcat = client.post("/api/categories", json={"nom": "Rayon test"}).json()
assert client.put(f"/api/categories/{newcat['id']}", json={"nom": "Rayon test 2"}).json()["nom"] == "Rayon test 2"
ids = [c["id"] for c in client.get("/api/categories").json()]
assert client.put("/api/categories/reorder/apply", json={"ordered_ids": list(reversed(ids))}).status_code == 204
assert client.delete(f"/api/categories/{newcat['id']}").status_code == 204
print("Gestion des rayons (CRUD + réordonnancement) : OK")

# --- Deals : non configuré (pas de clé) ---
st = client.get("/api/deals/status").json()
assert st["disponible"] is False
scan = client.post("/api/deals/scan", json={"texte_circulaire": "Tomates 0.99$/lb", "semaine": SEM}).json()
assert scan["disponible"] is False and scan["ok"] is True
print("Alerte aubaines (mode non configuré) : OK — message clair renvoyé")

_ctx.__exit__(None, None, None)
print("\nAPI SMOKE 2 OK")
