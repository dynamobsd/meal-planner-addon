"""Planning hebdomadaire des repas (Phase 3)."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AppSetting, MealPlan, Recipe
from ..schemas import (
    TYPES_REPAS,
    AutoPlanRequest,
    AutoPlanResponse,
    DuplicateWeekRequest,
    MealPlanCreate,
    MealPlanOut,
    MealPlanUpdate,
    MealSuggestion,
)
from ..services import autoplan as autoplan_service

router = APIRouter(tags=["meal_plan"])


def _week_dates(start: str, jours: int) -> list[str]:
    start_d = date.fromisoformat(start)
    return [(start_d + timedelta(days=i)).isoformat() for i in range(jours)]


def _to_out(mp: MealPlan, recipe: Recipe | None) -> MealPlanOut:
    out = MealPlanOut.model_validate(mp)
    if recipe is not None:
        out.recette_titre = recipe.titre
        out.recette_image = recipe.image_url
        out.recette_portions = recipe.portions
    return out


@router.get("/meal-plan", response_model=list[MealPlanOut])
def list_week(
    start: str = Query(..., description="Lundi ISO de la semaine (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Renvoie tous les repas planifiés de la semaine commençant à `start`."""
    try:
        start_d = date.fromisoformat(start)
    except ValueError:
        raise HTTPException(status_code=422, detail="Date invalide")
    end_d = start_d + timedelta(days=7)

    rows = db.scalars(
        select(MealPlan).where(
            MealPlan.date >= start_d.isoformat(),
            MealPlan.date < end_d.isoformat(),
        )
    ).all()
    recipes = {r.id: r for r in db.scalars(select(Recipe)).all()}
    return [_to_out(mp, recipes.get(mp.recipe_id)) for mp in rows]


@router.post("/meal-plan", response_model=MealPlanOut, status_code=201)
def add_meal(payload: MealPlanCreate, db: Session = Depends(get_db)):
    if payload.type_repas not in TYPES_REPAS:
        raise HTTPException(status_code=422, detail="Type de repas invalide")
    recipe = db.get(Recipe, payload.recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recette introuvable")
    # Défaut : portions de la recette si non précisé
    portions = payload.portions_planifiees or recipe.portions
    mp = MealPlan(
        date=payload.date,
        type_repas=payload.type_repas,
        recipe_id=payload.recipe_id,
        portions_planifiees=portions,
    )
    db.add(mp)
    db.commit()
    db.refresh(mp)
    return _to_out(mp, recipe)


@router.put("/meal-plan/{mp_id}", response_model=MealPlanOut)
def update_meal(mp_id: int, payload: MealPlanUpdate, db: Session = Depends(get_db)):
    mp = db.get(MealPlan, mp_id)
    if mp is None:
        raise HTTPException(status_code=404, detail="Repas introuvable")
    data = payload.model_dump(exclude_unset=True)
    if "type_repas" in data and data["type_repas"] not in TYPES_REPAS:
        raise HTTPException(status_code=422, detail="Type de repas invalide")
    for field, value in data.items():
        setattr(mp, field, value)
    db.commit()
    db.refresh(mp)
    return _to_out(mp, db.get(Recipe, mp.recipe_id))


@router.delete("/meal-plan/{mp_id}", status_code=204)
def remove_meal(mp_id: int, db: Session = Depends(get_db)):
    mp = db.get(MealPlan, mp_id)
    if mp is None:
        raise HTTPException(status_code=404, detail="Repas introuvable")
    db.delete(mp)
    db.commit()


def _delete_week(db: Session, start: str) -> None:
    start_d = date.fromisoformat(start)
    end_d = start_d + timedelta(days=7)
    for mp in db.scalars(
        select(MealPlan).where(
            MealPlan.date >= start_d.isoformat(), MealPlan.date < end_d.isoformat()
        )
    ).all():
        db.delete(mp)
    db.flush()


@router.post("/meal-plan/auto", response_model=AutoPlanResponse)
def auto_plan(payload: AutoPlanRequest, db: Session = Depends(get_db)):
    """Génère un planning : l'IA place les recettes existantes sur les créneaux."""
    try:
        date.fromisoformat(payload.semaine)
    except ValueError:
        raise HTTPException(status_code=422, detail="Semaine invalide")
    creneaux = [c for c in payload.creneaux if c in TYPES_REPAS]
    if not creneaux:
        raise HTTPException(status_code=422, detail="Aucun créneau valide")

    if payload.remplacer:
        _delete_week(db, payload.semaine)
        db.flush()

    dates = _week_dates(payload.semaine, payload.jours)
    slots = [{"date": d, "type_repas": c} for d in dates for c in creneaux]

    prefs = payload.preferences
    if not prefs:
        row = db.scalar(
            select(AppSetting).where(AppSetting.cle == "preferences_gouts")
        )
        prefs = row.valeur if row else None

    recettes = [
        {
            "id": r.id,
            "titre": r.titre,
            "categorie_plat": r.categorie_plat,
            "note_etoiles": r.note_etoiles,
            "favori": r.favori,
        }
        for r in db.scalars(select(Recipe)).all()
    ]

    result = autoplan_service.build_plan(slots, recettes, prefs)
    if not result.ok or not result.disponible:
        return AutoPlanResponse(
            ok=result.ok, disponible=result.disponible, message=result.message
        )

    recipes_by_id = {r.id: r for r in db.scalars(select(Recipe)).all()}
    ajoutes: list[MealPlanOut] = []
    idees: list[MealSuggestion] = []
    for a in result.assignations:
        rid = a.get("recipe_id")
        if rid and rid in recipes_by_id and a["type_repas"] in TYPES_REPAS:
            recipe = recipes_by_id[rid]
            mp = MealPlan(
                date=a["date"],
                type_repas=a["type_repas"],
                recipe_id=rid,
                portions_planifiees=recipe.portions,
            )
            db.add(mp)
            db.flush()
            ajoutes.append(_to_out(mp, recipe))
        else:
            idees.append(
                MealSuggestion(
                    titre=a.get("titre") or "Idée",
                    type_plat=a.get("type_repas"),
                    raison=a.get("raison"),
                    recipe_id=None,
                    nouvelle_idee=True,
                )
            )
    db.commit()
    return AutoPlanResponse(ok=True, disponible=True, ajoutes=ajoutes, idees_manquantes=idees)


@router.post("/meal-plan/duplicate", response_model=list[MealPlanOut])
def duplicate_week(payload: DuplicateWeekRequest, db: Session = Depends(get_db)):
    """Copie les repas d'une semaine source vers une semaine cible."""
    try:
        src = date.fromisoformat(payload.source_semaine)
        dst = date.fromisoformat(payload.cible_semaine)
    except ValueError:
        raise HTTPException(status_code=422, detail="Semaine invalide")

    if payload.remplacer:
        _delete_week(db, payload.cible_semaine)
        db.flush()

    end = src + timedelta(days=7)
    sources = db.scalars(
        select(MealPlan).where(
            MealPlan.date >= src.isoformat(), MealPlan.date < end.isoformat()
        )
    ).all()

    recipes = {r.id: r for r in db.scalars(select(Recipe)).all()}
    created: list[MealPlanOut] = []
    for mp in sources:
        offset = (date.fromisoformat(mp.date) - src).days
        new_date = (dst + timedelta(days=offset)).isoformat()
        new_mp = MealPlan(
            date=new_date,
            type_repas=mp.type_repas,
            recipe_id=mp.recipe_id,
            portions_planifiees=mp.portions_planifiees,
        )
        db.add(new_mp)
        db.flush()
        created.append(_to_out(new_mp, recipes.get(mp.recipe_id)))
    db.commit()
    return created
