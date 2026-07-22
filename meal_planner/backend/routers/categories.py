"""Rayons d'épicerie + apprentissage de l'auto-catégorisation."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Category
from ..schemas import (
    CategoryCreate,
    CategoryOut,
    CategoryRename,
    CategoryReorder,
    IngredientCategoryUpdate,
)
from ..services.categorization import learn_category

router = APIRouter(tags=["categories"])


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.scalars(select(Category).order_by(Category.ordre_tri)).all()


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    nom = payload.nom.strip()
    if not nom:
        raise HTTPException(status_code=422, detail="Nom requis")
    if db.scalar(select(Category).where(Category.nom == nom)):
        raise HTTPException(status_code=409, detail="Ce rayon existe déjà")
    # placé en dernier dans l'ordre de parcours
    max_ordre = db.scalar(select(Category.ordre_tri).order_by(Category.ordre_tri.desc()))
    cat = Category(nom=nom, ordre_tri=(max_ordre or 0) + 1)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/categories/{cat_id}", response_model=CategoryOut)
def rename_category(cat_id: int, payload: CategoryRename, db: Session = Depends(get_db)):
    cat = db.get(Category, cat_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Rayon introuvable")
    cat.nom = payload.nom.strip()
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/categories/reorder/apply", status_code=204)
def reorder_categories(payload: CategoryReorder, db: Session = Depends(get_db)):
    """Réordonne les rayons selon la liste d'ids fournie (ordre de parcours)."""
    for ordre, cat_id in enumerate(payload.ordered_ids):
        cat = db.get(Category, cat_id)
        if cat is not None:
            cat.ordre_tri = ordre
    db.commit()


@router.delete("/categories/{cat_id}", status_code=204)
def delete_category(cat_id: int, db: Session = Depends(get_db)):
    cat = db.get(Category, cat_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Rayon introuvable")
    db.delete(cat)
    db.commit()


@router.put("/categories/learn", status_code=204)
def learn(payload: IngredientCategoryUpdate, db: Session = Depends(get_db)):
    """Corrige/mémorise le rayon d'un ingrédient (upsert dans la mémoire)."""
    cat = db.get(Category, payload.categorie_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Rayon introuvable")
    learn_category(db, payload.nom_normalise, payload.categorie_id)
    db.commit()
