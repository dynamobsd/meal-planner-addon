"""Modèles ORM (SQLAlchemy 2.0) — reflètent le schéma validé en Phase 1.

Tables : categories, recipes, ingredients, ingredient_category_map,
meal_plan, pantry, grocery_items.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Category(Base):
    """Rayon d'épicerie, ordonné selon le parcours en magasin."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    ordre_tri: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    titre: Mapped[str] = mapped_column(Text, nullable=False)
    url_source: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    portions: Mapped[int | None] = mapped_column(Integer)
    temps_prep: Mapped[int | None] = mapped_column(Integer)      # minutes
    temps_cuisson: Mapped[int | None] = mapped_column(Integer)   # minutes
    instructions: Mapped[str | None] = mapped_column(Text)
    note_perso: Mapped[str | None] = mapped_column(Text)         # "nos notes"
    note_etoiles: Mapped[int] = mapped_column(Integer, default=0)  # 0..5
    date_ajout: Mapped[str] = mapped_column(Text, default=_utcnow_iso)

    ingredients: Mapped[list["Ingredient"]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="Ingredient.id",
    )


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    texte_brut: Mapped[str] = mapped_column(Text, nullable=False)
    nom_normalise: Mapped[str] = mapped_column(Text, nullable=False, default="")
    quantite: Mapped[float | None] = mapped_column()             # nullable ("au goût")
    unite: Mapped[str | None] = mapped_column(Text)              # forme canonique
    note: Mapped[str | None] = mapped_column(Text)               # "haché", "frais"…
    categorie_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL")
    )

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")


class IngredientCategoryMap(Base):
    """Mémoire apprenante : nom_normalise -> rayon."""

    __tablename__ = "ingredient_category_map"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom_ingredient: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    categorie_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )


class MealPlan(Base):
    __tablename__ = "meal_plan"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[str] = mapped_column(Text, nullable=False)      # "2026-07-21"
    type_repas: Mapped[str] = mapped_column(Text, nullable=False)  # dejeuner|diner|souper|collation
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    portions_planifiees: Mapped[int | None] = mapped_column(Integer)


class Pantry(Base):
    __tablename__ = "pantry"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom_ingredient: Mapped[str] = mapped_column(Text, nullable=False)
    quantite: Mapped[float | None] = mapped_column()
    unite: Mapped[str | None] = mapped_column(Text)


class GroceryItem(Base):
    __tablename__ = "grocery_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    semaine: Mapped[str] = mapped_column(Text, nullable=False)   # lundi ISO
    nom: Mapped[str] = mapped_column(Text, nullable=False)
    quantite_totale: Mapped[float | None] = mapped_column()
    unite: Mapped[str | None] = mapped_column(Text)
    categorie_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL")
    )
    coche: Mapped[int] = mapped_column(Integer, default=0)       # bool 0/1
    source: Mapped[str] = mapped_column(Text, default="auto")    # auto|manuel
    avertissement: Mapped[str | None] = mapped_column(Text)
