"""CRUD des recettes + leurs ingrédients."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Category, Ingredient, Recipe
from ..schemas import (
    TYPES_PLAT,
    IngredientOut,
    RecipeCreate,
    RecipeOut,
    RecipeSummary,
    RecipeUpdate,
)

router = APIRouter(tags=["recipes"])


@router.get("/types-plat", response_model=list[str])
def list_types_plat():
    """Types de plat proposés pour classer les recettes."""
    return list(TYPES_PLAT)


def _category_names(db: Session) -> dict[int, str]:
    return {c.id: c.nom for c in db.scalars(select(Category)).all()}


def _to_recipe_out(recipe: Recipe, cat_names: dict[int, str]) -> RecipeOut:
    out = RecipeOut.model_validate(recipe)
    for ing_out, ing in zip(out.ingredients, recipe.ingredients):
        ing_out.categorie_nom = cat_names.get(ing.categorie_id)
    return out


@router.get("/recipes", response_model=list[RecipeSummary])
def list_recipes(
    categorie_plat: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    """Liste des recettes, filtrable par type de plat et recherche texte."""
    stmt = select(Recipe)
    if categorie_plat:
        stmt = stmt.where(Recipe.categorie_plat == categorie_plat)
    if q:
        stmt = stmt.where(Recipe.titre.ilike(f"%{q.strip()}%"))
    recipes = db.scalars(stmt.order_by(Recipe.date_ajout.desc())).all()
    return recipes


@router.get("/recipes/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recette introuvable")
    return _to_recipe_out(recipe, _category_names(db))


@router.post("/recipes", response_model=RecipeOut, status_code=201)
def create_recipe(payload: RecipeCreate, db: Session = Depends(get_db)):
    recipe = Recipe(
        **payload.model_dump(exclude={"ingredients"}),
    )
    for ing in payload.ingredients:
        recipe.ingredients.append(Ingredient(**ing.model_dump()))
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return _to_recipe_out(recipe, _category_names(db))


@router.put("/recipes/{recipe_id}", response_model=RecipeOut)
def update_recipe(
    recipe_id: int, payload: RecipeUpdate, db: Session = Depends(get_db)
):
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recette introuvable")

    data = payload.model_dump(exclude={"ingredients"}, exclude_unset=True)
    for field, value in data.items():
        setattr(recipe, field, value)

    # Remplacement complet des ingrédients si fournis
    if payload.ingredients is not None:
        recipe.ingredients.clear()
        db.flush()
        for ing in payload.ingredients:
            recipe.ingredients.append(Ingredient(**ing.model_dump()))

    db.commit()
    db.refresh(recipe)
    return _to_recipe_out(recipe, _category_names(db))


@router.delete("/recipes/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recette introuvable")
    db.delete(recipe)
    db.commit()
