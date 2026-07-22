"""Schémas Pydantic v2 pour les entrées/sorties de l'API.

Contrat partagé backend <-> frontend <-> agents.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# --------------------------------------------------------------------------- #
# Ingrédients
# --------------------------------------------------------------------------- #


class IngredientBase(BaseModel):
    texte_brut: str
    nom_normalise: str = ""
    quantite: float | None = None
    unite: str | None = None
    note: str | None = None
    categorie_id: int | None = None


class IngredientIn(IngredientBase):
    """Ingrédient fourni par le client (création/édition de recette)."""


class IngredientOut(IngredientBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    categorie_nom: str | None = None


class IngredientDraft(IngredientBase):
    """Ingrédient d'un brouillon scrapé (pas encore d'id en base)."""

    categorie_nom: str | None = None


# --------------------------------------------------------------------------- #
# Recettes
# --------------------------------------------------------------------------- #


class RecipeBase(BaseModel):
    titre: str
    url_source: str | None = None
    image_url: str | None = None
    portions: int | None = None
    temps_prep: int | None = None
    temps_cuisson: int | None = None
    instructions: str | None = None
    note_perso: str | None = None
    note_etoiles: int = Field(default=0, ge=0, le=5)


class RecipeCreate(RecipeBase):
    ingredients: list[IngredientIn] = Field(default_factory=list)


class RecipeUpdate(RecipeBase):
    ingredients: list[IngredientIn] | None = None


class RecipeOut(RecipeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date_ajout: str
    ingredients: list[IngredientOut] = Field(default_factory=list)


class RecipeSummary(BaseModel):
    """Version allégée pour la liste des recettes (mobile)."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    titre: str
    image_url: str | None = None
    portions: int | None = None
    note_etoiles: int = 0


# --------------------------------------------------------------------------- #
# Scraping / import
# --------------------------------------------------------------------------- #


class ScrapeRequest(BaseModel):
    url: str


class ScrapeDraft(RecipeBase):
    """Brouillon pré-rempli renvoyé par le scraping (non sauvegardé)."""

    host: str | None = None
    ingredients: list[IngredientDraft] = Field(default_factory=list)


class ScrapeResponse(BaseModel):
    ok: bool = True
    source: str                       # "recipe-scrapers" | "json-ld"
    draft: ScrapeDraft


class ScrapeError(BaseModel):
    ok: bool = False
    error_code: str                   # "unsupported_site" | "fetch_failed" | ...
    message: str
    url: str


# --------------------------------------------------------------------------- #
# Catégories / rayons
# --------------------------------------------------------------------------- #


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nom: str
    ordre_tri: int


class IngredientCategoryUpdate(BaseModel):
    """Correction manuelle d'un rayon -> apprentissage."""

    nom_normalise: str
    categorie_id: int
