"""Suggestions de repas — endpoint (IA)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AppSetting, Recipe
from ..schemas import SuggestionsRequest, SuggestionsResponse
from ..services import suggestions as suggestions_service

router = APIRouter(tags=["suggestions"])

# Clé de réglage où sont persistées les préférences de goûts
PREF_KEY = "preferences_gouts"


@router.get("/suggestions/status")
def suggestions_status():
    return {"disponible": suggestions_service.is_configured()}


@router.post("/suggestions/meals", response_model=SuggestionsResponse)
def suggest(payload: SuggestionsRequest, db: Session = Depends(get_db)):
    # Préférences : celles fournies, sinon celles persistées dans les réglages
    prefs = payload.preferences
    if not prefs:
        row = db.scalar(select(AppSetting).where(AppSetting.cle == PREF_KEY))
        prefs = row.valeur if row else None

    recettes = [
        {
            "id": r.id,
            "titre": r.titre,
            "categorie_plat": r.categorie_plat,
            "note_etoiles": r.note_etoiles,
        }
        for r in db.scalars(select(Recipe)).all()
    ] if payload.utiliser_mes_recettes else []

    return suggestions_service.suggest_meals(
        preferences=prefs,
        nb_repas=payload.nb_repas,
        type_plat=payload.type_plat,
        recettes=recettes,
    )
