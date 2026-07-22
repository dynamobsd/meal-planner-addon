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


# Types de plat proposés (catégorie de la recette, distinct du créneau du planning)
TYPES_PLAT = (
    "Déjeuner",
    "Dîner",
    "Souper",
    "Entrée",
    "Plat principal",
    "Accompagnement",
    "Soupe",
    "Salade",
    "Dessert",
    "Collation",
    "Boisson",
    "Autre",
)


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
    categorie_plat: str | None = None      # type de plat (dessert, plat principal…)
    favori: int = 0                        # bool 0/1


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
    categorie_plat: str | None = None
    favori: int = 0


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


class CategoryCreate(BaseModel):
    nom: str


class CategoryRename(BaseModel):
    nom: str


class CategoryReorder(BaseModel):
    """Nouvel ordre : liste d'ids de rayons dans l'ordre de parcours voulu."""

    ordered_ids: list[int]


# --------------------------------------------------------------------------- #
# Planning hebdomadaire (Phase 3)
# --------------------------------------------------------------------------- #

TYPES_REPAS = ("dejeuner", "diner", "souper", "collation")


class MealPlanCreate(BaseModel):
    date: str                              # "2026-07-21"
    type_repas: str                        # dejeuner|diner|souper|collation
    recipe_id: int
    portions_planifiees: int | None = None


class MealPlanUpdate(BaseModel):
    date: str | None = None
    type_repas: str | None = None
    portions_planifiees: int | None = None


class MealPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date: str
    type_repas: str
    recipe_id: int
    portions_planifiees: int | None = None
    # enrichissements pour l'UI
    recette_titre: str | None = None
    recette_image: str | None = None
    recette_portions: int | None = None


# --------------------------------------------------------------------------- #
# Garde-manger (Phase 4)
# --------------------------------------------------------------------------- #


class PantryIn(BaseModel):
    nom_ingredient: str
    quantite: float | None = None
    unite: str | None = None


class PantryOut(PantryIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


# --------------------------------------------------------------------------- #
# Liste d'épicerie (Phase 4)
# --------------------------------------------------------------------------- #


class GroceryItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    semaine: str
    nom: str
    quantite_totale: float | None = None
    unite: str | None = None
    categorie_id: int | None = None
    coche: int = 0
    source: str = "auto"
    avertissement: str | None = None
    categorie_nom: str | None = None


class GroceryManualIn(BaseModel):
    semaine: str
    nom: str
    quantite_totale: float | None = None
    unite: str | None = None
    categorie_id: int | None = None


class GroceryPatch(BaseModel):
    coche: int | None = None
    quantite_totale: float | None = None


class GroceryGenerateRequest(BaseModel):
    semaine: str                           # lundi ISO de la semaine


class GroceryRayon(BaseModel):
    """Un rayon regroupant ses items, pour l'affichage mobile."""

    categorie_id: int | None
    categorie_nom: str
    ordre_tri: int
    items: list[GroceryItemOut]


# --------------------------------------------------------------------------- #
# Alerte aubaines — IA (feature bonus)
# --------------------------------------------------------------------------- #


class DealsScanRequest(BaseModel):
    texte_circulaire: str                  # texte brut collé d'une circulaire
    semaine: str | None = None             # pour matcher la liste d'épicerie de la semaine
    magasin: str | None = None


class DealMatch(BaseModel):
    produit: str                           # nom du produit en aubaine
    prix: str | None = None                # ex "2.99$/lb" (texte libre)
    rabais: str | None = None              # ex "50% de rabais"
    ingredient_liste: str | None = None    # nom_normalise correspondant sur la liste, si match
    pertinent: bool                        # True si l'item est sur la liste/planning
    note: str | None = None


class DealsScanResponse(BaseModel):
    ok: bool = True
    disponible: bool = True                # False si l'IA n'est pas configurée
    message: str | None = None
    aubaines: list[DealMatch] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Réglages clé/valeur
# --------------------------------------------------------------------------- #


class SettingOut(BaseModel):
    cle: str
    valeur: str | None = None


class SettingIn(BaseModel):
    valeur: str | None = None


# --------------------------------------------------------------------------- #
# Suggestions de repas — IA
# --------------------------------------------------------------------------- #


class SuggestionsRequest(BaseModel):
    preferences: str | None = None         # goûts / contraintes (« ma blonde aime… »)
    nb_repas: int = Field(default=5, ge=1, le=14)
    type_plat: str | None = None           # filtrer sur un type (ex "Souper")
    utiliser_mes_recettes: bool = True     # privilégier les recettes déjà enregistrées


class MealSuggestion(BaseModel):
    titre: str
    type_plat: str | None = None           # déjeuner / souper / dessert…
    raison: str | None = None              # pourquoi c'est suggéré (pour ta blonde…)
    recipe_id: int | None = None           # si ça correspond à une recette existante
    nouvelle_idee: bool = False            # True si c'est une idée à créer (pas en base)
    ingredients_cles: list[str] = Field(default_factory=list)


class SuggestionsResponse(BaseModel):
    ok: bool = True
    disponible: bool = True                # False si l'IA n'est pas configurée
    message: str | None = None
    suggestions: list[MealSuggestion] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Planning automatique (IA) + duplication + export
# --------------------------------------------------------------------------- #


class AutoPlanRequest(BaseModel):
    semaine: str                           # lundi ISO
    creneaux: list[str] = Field(default_factory=lambda: ["souper"])  # créneaux à remplir
    jours: int = Field(default=7, ge=1, le=7)
    remplacer: bool = False                # vider le planning existant de la semaine d'abord
    preferences: str | None = None         # sinon lit les préférences enregistrées


class AutoPlanResponse(BaseModel):
    ok: bool = True
    disponible: bool = True
    message: str | None = None
    ajoutes: list[MealPlanOut] = Field(default_factory=list)
    idees_manquantes: list[MealSuggestion] = Field(default_factory=list)


class DuplicateWeekRequest(BaseModel):
    source_semaine: str                    # lundi ISO source
    cible_semaine: str                     # lundi ISO destination
    remplacer: bool = False                # vider la semaine cible d'abord


class GroceryExportResponse(BaseModel):
    semaine: str
    texte: str                             # liste formatée par rayon, prête à partager
