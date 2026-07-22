# -*- coding: utf-8 -*-
"""Smoke test de bout en bout : import complet + parseur + catégorisation en DB réelle."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# DB temporaire isolée
os.environ["MP_DB_PATH"] = os.path.join(os.path.dirname(__file__), "smoke.db")
for ext in ("", "-wal", "-shm"):
    p = os.environ["MP_DB_PATH"] + ext
    if os.path.exists(p):
        os.remove(p)

import backend.main as m  # importe tous les routeurs + services
from backend.database import init_db, SessionLocal
from backend.services.ingredient_parser import parse_ingredient
from backend.services.categorization import (
    resolve_category, learn_category, DEFAULT_CATEGORY_MAP,
)
from backend.models import Category

print("main + services import : OK")
print("DEFAULT_CATEGORY_MAP size :", len(DEFAULT_CATEGORY_MAP))

init_db()
db = SessionLocal()

# --- Parseur sur des cas variés ---
cas = [
    "1 ½ tasse de farine tout usage",
    "2 gousses d'ail hachées",
    "2 tomates",
    "2 à 3 c. à soupe d'huile d'olive",
    "500 g de boeuf haché",
    "sel au goût",
]
print("\n--- Parseur ---")
for c in cas:
    p = parse_ingredient(c)
    print(f"  {c!r:45} -> q={p.quantite} u={p.unite!r} nom={p.nom_normalise!r} note={p.note!r}")

# --- Catégorisation (dico par défaut) ---
print("\n--- Catégorisation (défaut) ---")
cat_by_id = {c.id: c.nom for c in db.query(Category).all()}
for nom in ["tomate", "boeuf hache", "farine tout usage", "lait", "xyzzy inconnu"]:
    cid = resolve_category(db, nom)
    print(f"  {nom!r:22} -> {cat_by_id.get(cid)!r}")

# --- Apprentissage : reclasse "xyzzy inconnu" vers Boissons puis re-résout ---
print("\n--- Apprentissage ---")
boissons_id = db.query(Category).filter(Category.nom == "Boissons").one().id
learn_category(db, "xyzzy inconnu", boissons_id)
db.commit()
cid2 = resolve_category(db, "xyzzy inconnu")
print(f"  après learn -> {cat_by_id.get(cid2)!r} (attendu 'Boissons')")

# --- Égalité critique de normalisation ---
n1 = parse_ingredient("tomate hachée").nom_normalise
n2 = parse_ingredient("2 tomates").nom_normalise
n3 = parse_ingredient("la tomate").nom_normalise
print("\n--- Normalisation ---")
print(f"  'tomate hachée'={n1!r}  '2 tomates'={n2!r}  'la tomate'={n3!r}  egaux={n1==n2==n3}")

db.close()
print("\nSMOKE OK")
