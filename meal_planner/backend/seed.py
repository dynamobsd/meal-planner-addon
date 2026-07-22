"""Données par défaut insérées au premier démarrage.

Rayons d'épicerie dans l'ordre de parcours typique d'un magasin.
L'ordre et les noms sont modifiables ensuite par l'utilisateur (Phase 5).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Category

# (nom, ordre_tri) — l'ordre reflète le parcours en magasin
DEFAULT_CATEGORIES: list[str] = [
    "Fruits & légumes",
    "Boulangerie",
    "Boucherie & poissonnerie",
    "Charcuterie",
    "Produits laitiers & œufs",
    "Surgelés",
    "Conserves & bocaux",
    "Épicerie sèche",          # pâtes / riz / farine
    "Condiments & sauces",
    "Épices",
    "Collations",
    "Boissons",
    "Ménage",
    "Autre",
]


def seed_defaults(db: Session) -> None:
    """Insère les rayons par défaut s'il n'y en a aucun (idempotent)."""
    existing = db.scalar(select(Category).limit(1))
    if existing is not None:
        return
    for ordre, nom in enumerate(DEFAULT_CATEGORIES):
        db.add(Category(nom=nom, ordre_tri=ordre))
    db.flush()


def get_category_id_by_name(db: Session, nom: str) -> int | None:
    cat = db.scalar(select(Category).where(Category.nom == nom))
    return cat.id if cat else None


def get_fallback_category_id(db: Session) -> int | None:
    """Rayon « Autre » — utilisé quand rien ne matche."""
    return get_category_id_by_name(db, "Autre")
