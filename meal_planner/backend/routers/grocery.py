"""Liste d'épicerie : génération (agrégation) + état (coches) — Phase 4.

Orchestration :
  1. rassemble les ingrédients des recettes planifiées de la semaine
  2. met à l'échelle selon portions_planifiees vs portions de base
  3. services.aggregator.aggregate_ingredients(items, pantry) -> lignes à acheter
  4. persiste dans grocery_items en préservant coches + items manuels
  5. renvoie regroupé par rayon, trié selon l'ordre de parcours
"""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Category, GroceryItem, Ingredient, MealPlan, Pantry, Recipe
from ..schemas import (
    GroceryGenerateRequest,
    GroceryItemOut,
    GroceryManualIn,
    GroceryPatch,
    GroceryRayon,
)
from ..services.aggregator import aggregate_ingredients

router = APIRouter(tags=["grocery"])


def _category_maps(db: Session):
    cats = db.scalars(select(Category).order_by(Category.ordre_tri)).all()
    noms = {c.id: c.nom for c in cats}
    ordres = {c.id: c.ordre_tri for c in cats}
    return noms, ordres


def _grouped(db: Session, semaine: str) -> list[GroceryRayon]:
    """Charge les items d'une semaine, regroupés par rayon trié."""
    noms, ordres = _category_maps(db)
    items = db.scalars(
        select(GroceryItem).where(GroceryItem.semaine == semaine)
    ).all()

    buckets: dict[int | None, list[GroceryItemOut]] = {}
    for it in items:
        out = GroceryItemOut.model_validate(it)
        out.categorie_nom = noms.get(it.categorie_id, "Autre")
        buckets.setdefault(it.categorie_id, []).append(out)

    rayons: list[GroceryRayon] = []
    for cat_id, its in buckets.items():
        its.sort(key=lambda x: x.nom.lower())
        rayons.append(
            GroceryRayon(
                categorie_id=cat_id,
                categorie_nom=noms.get(cat_id, "Autre"),
                ordre_tri=ordres.get(cat_id, 9999),
                items=its,
            )
        )
    rayons.sort(key=lambda r: r.ordre_tri)
    return rayons


@router.get("/grocery", response_model=list[GroceryRayon])
def get_list(semaine: str, db: Session = Depends(get_db)):
    return _grouped(db, semaine)


@router.post("/grocery/generate", response_model=list[GroceryRayon])
def generate(payload: GroceryGenerateRequest, db: Session = Depends(get_db)):
    semaine = payload.semaine
    try:
        start_d = date.fromisoformat(semaine)
    except ValueError:
        raise HTTPException(status_code=422, detail="Semaine invalide")
    end_d = start_d + timedelta(days=7)

    # 1. Repas planifiés de la semaine
    plans = db.scalars(
        select(MealPlan).where(
            MealPlan.date >= start_d.isoformat(),
            MealPlan.date < end_d.isoformat(),
        )
    ).all()

    # 2. Ingrédients mis à l'échelle
    items: list[dict] = []
    for mp in plans:
        recipe = db.get(Recipe, mp.recipe_id)
        if recipe is None:
            continue
        base = recipe.portions or 0
        planned = mp.portions_planifiees or base
        factor = (planned / base) if base > 0 and planned else 1.0
        for ing in recipe.ingredients:
            qte = ing.quantite * factor if ing.quantite is not None else None
            items.append(
                {
                    "nom_normalise": ing.nom_normalise,
                    "quantite": qte,
                    "unite": ing.unite,
                    "categorie_id": ing.categorie_id,
                }
            )

    # 3. Garde-manger
    pantry = [
        {"nom_ingredient": p.nom_ingredient, "quantite": p.quantite, "unite": p.unite}
        for p in db.scalars(select(Pantry)).all()
    ]

    # 4. Agrégation (moteur testé)
    lignes = aggregate_ingredients(items, pantry)

    # 5. Persistance : préserve les coches (par nom) et les items manuels
    anciennes_coches = {
        gi.nom.lower(): gi.coche
        for gi in db.scalars(
            select(GroceryItem).where(
                GroceryItem.semaine == semaine, GroceryItem.source == "auto"
            )
        ).all()
    }
    # supprime les anciennes lignes auto de la semaine
    for gi in db.scalars(
        select(GroceryItem).where(
            GroceryItem.semaine == semaine, GroceryItem.source == "auto"
        )
    ).all():
        db.delete(gi)
    db.flush()

    for ligne in lignes:
        db.add(
            GroceryItem(
                semaine=semaine,
                nom=ligne.nom,
                quantite_totale=ligne.quantite_totale,
                unite=ligne.unite,
                categorie_id=ligne.categorie_id,
                coche=anciennes_coches.get(ligne.nom.lower(), 0),
                source="auto",
                avertissement=ligne.avertissement,
            )
        )
    db.commit()
    return _grouped(db, semaine)


@router.post("/grocery/manual", response_model=GroceryItemOut, status_code=201)
def add_manual(payload: GroceryManualIn, db: Session = Depends(get_db)):
    it = GroceryItem(
        semaine=payload.semaine,
        nom=payload.nom,
        quantite_totale=payload.quantite_totale,
        unite=payload.unite,
        categorie_id=payload.categorie_id,
        coche=0,
        source="manuel",
    )
    db.add(it)
    db.commit()
    db.refresh(it)
    noms, _ = _category_maps(db)
    out = GroceryItemOut.model_validate(it)
    out.categorie_nom = noms.get(it.categorie_id, "Autre")
    return out


@router.patch("/grocery/{item_id}", response_model=GroceryItemOut)
def patch_item(item_id: int, payload: GroceryPatch, db: Session = Depends(get_db)):
    it = db.get(GroceryItem, item_id)
    if it is None:
        raise HTTPException(status_code=404, detail="Item introuvable")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(it, field, value)
    db.commit()
    db.refresh(it)
    noms, _ = _category_maps(db)
    out = GroceryItemOut.model_validate(it)
    out.categorie_nom = noms.get(it.categorie_id, "Autre")
    return out


@router.delete("/grocery/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    it = db.get(GroceryItem, item_id)
    if it is None:
        raise HTTPException(status_code=404, detail="Item introuvable")
    db.delete(it)
    db.commit()


@router.post("/grocery/{item_id}/have", status_code=204)
def i_have_it(item_id: int, add_to_pantry: bool = False, db: Session = Depends(get_db)):
    """« J'en ai déjà » : retire l'item de la liste, l'ajoute optionnellement au garde-manger."""
    it = db.get(GroceryItem, item_id)
    if it is None:
        raise HTTPException(status_code=404, detail="Item introuvable")
    if add_to_pantry:
        db.add(
            Pantry(nom_ingredient=it.nom, quantite=it.quantite_totale, unite=it.unite)
        )
    db.delete(it)
    db.commit()
