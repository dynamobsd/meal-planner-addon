"""Planning hebdomadaire des repas (Phase 3)."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import MealPlan, Recipe
from ..schemas import TYPES_REPAS, MealPlanCreate, MealPlanOut, MealPlanUpdate

router = APIRouter(tags=["meal_plan"])


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
