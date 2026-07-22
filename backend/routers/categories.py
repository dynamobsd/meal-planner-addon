"""Rayons d'épicerie + apprentissage de l'auto-catégorisation."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Category
from ..schemas import CategoryOut, IngredientCategoryUpdate
from ..services.categorization import learn_category

router = APIRouter(tags=["categories"])


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.scalars(select(Category).order_by(Category.ordre_tri)).all()


@router.put("/categories/learn", status_code=204)
def learn(payload: IngredientCategoryUpdate, db: Session = Depends(get_db)):
    """Corrige/mémorise le rayon d'un ingrédient (upsert dans la mémoire)."""
    cat = db.get(Category, payload.categorie_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Rayon introuvable")
    learn_category(db, payload.nom_normalise, payload.categorie_id)
    db.commit()
