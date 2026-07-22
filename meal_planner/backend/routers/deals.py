"""Alerte aubaines — endpoint (feature bonus IA)."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import GroceryItem, Ingredient, MealPlan, Recipe
from ..schemas import DealsScanRequest, DealsScanResponse
from ..services import deals as deals_service

router = APIRouter(tags=["deals"])


def _ingredients_semaine(db: Session, semaine: str | None) -> list[str]:
    """Noms normalisés des ingrédients à acheter pour la semaine (liste + planning)."""
    noms: set[str] = set()
    if not semaine:
        return []
    # Depuis la liste d'épicerie générée
    for gi in db.scalars(
        select(GroceryItem).where(GroceryItem.semaine == semaine)
    ).all():
        if gi.nom:
            noms.add(gi.nom.lower())
    # Repli : ingrédients des recettes planifiées
    if not noms:
        try:
            start_d = date.fromisoformat(semaine)
            end_d = start_d + timedelta(days=7)
            plans = db.scalars(
                select(MealPlan).where(
                    MealPlan.date >= start_d.isoformat(),
                    MealPlan.date < end_d.isoformat(),
                )
            ).all()
            for mp in plans:
                recipe = db.get(Recipe, mp.recipe_id)
                if recipe:
                    for ing in recipe.ingredients:
                        if ing.nom_normalise:
                            noms.add(ing.nom_normalise.lower())
        except ValueError:
            pass
    return sorted(noms)


@router.get("/deals/status")
def deals_status():
    """Indique si la feature IA est configurée (clé API présente)."""
    return {"disponible": deals_service.is_configured()}


@router.post("/deals/scan", response_model=DealsScanResponse)
def scan(payload: DealsScanRequest, db: Session = Depends(get_db)):
    ingredients = _ingredients_semaine(db, payload.semaine)
    return deals_service.scan_deals(
        texte_circulaire=payload.texte_circulaire,
        liste_ingredients=ingredients,
        magasin=payload.magasin,
    )
