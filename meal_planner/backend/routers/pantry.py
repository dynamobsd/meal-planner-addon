"""Garde-manger : ce qu'on a déjà à la maison (Phase 4)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Pantry
from ..schemas import PantryIn, PantryOut
from ..services.ingredient_parser import parse_ingredient

router = APIRouter(tags=["pantry"])


@router.get("/pantry", response_model=list[PantryOut])
def list_pantry(db: Session = Depends(get_db)):
    return db.scalars(select(Pantry).order_by(Pantry.nom_ingredient)).all()


@router.post("/pantry", response_model=PantryOut, status_code=201)
def add_pantry(payload: PantryIn, db: Session = Depends(get_db)):
    # Normalise le nom pour que la soustraction de la liste matche bien
    parsed = parse_ingredient(payload.nom_ingredient)
    nom = parsed.nom_normalise or payload.nom_ingredient.strip().lower()
    item = Pantry(
        nom_ingredient=nom,
        quantite=payload.quantite if payload.quantite is not None else parsed.quantite,
        unite=payload.unite if payload.unite is not None else parsed.unite,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/pantry/{item_id}", response_model=PantryOut)
def update_pantry(item_id: int, payload: PantryIn, db: Session = Depends(get_db)):
    item = db.get(Pantry, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item introuvable")
    item.nom_ingredient = payload.nom_ingredient
    item.quantite = payload.quantite
    item.unite = payload.unite
    db.commit()
    db.refresh(item)
    return item


@router.delete("/pantry/{item_id}", status_code=204)
def remove_pantry(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Pantry, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item introuvable")
    db.delete(item)
    db.commit()
