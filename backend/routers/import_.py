"""Import de recettes : scraping par URL (brouillon non sauvegardé).

Orchestre trois services :
  - services.scraper.scrape_recipe(url)      -> ScrapedRecipeData | raises
  - services.ingredient_parser.parse_ingredient(raw) -> ParsedIngredient
  - services.categorization.resolve_category(db, nom) -> categorie_id | None

La sauvegarde effective passe par POST /api/recipes (routeur recipes).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Category
from ..schemas import (
    IngredientDraft,
    ScrapeDraft,
    ScrapeError,
    ScrapeRequest,
    ScrapeResponse,
)
from ..services.categorization import resolve_category
from ..services.ingredient_parser import parse_ingredient
from ..services.scraper import (
    ScrapeException,
    UnsupportedSiteError,
    scrape_recipe,
)

router = APIRouter(tags=["import"])


@router.post(
    "/recipes/scrape",
    response_model=ScrapeResponse,
    responses={422: {"model": ScrapeError}},
)
def scrape(payload: ScrapeRequest, db: Session = Depends(get_db)):
    url = payload.url.strip()
    try:
        data = scrape_recipe(url)
    except UnsupportedSiteError:
        return JSONResponse(
            status_code=422,
            content=ScrapeError(
                error_code="unsupported_site",
                message="Ce site n'est pas supporté. Passe en saisie manuelle.",
                url=url,
            ).model_dump(),
        )
    except ScrapeException as exc:
        return JSONResponse(
            status_code=422,
            content=ScrapeError(
                error_code=getattr(exc, "code", "fetch_failed"),
                message=str(exc) or "Impossible de récupérer la recette.",
                url=url,
            ).model_dump(),
        )

    cat_names = {c.id: c.nom for c in db.scalars(select(Category)).all()}

    ingredients: list[IngredientDraft] = []
    for raw in data.raw_ingredients:
        parsed = parse_ingredient(raw)
        cat_id = resolve_category(db, parsed.nom_normalise)
        ingredients.append(
            IngredientDraft(
                texte_brut=parsed.texte_brut,
                nom_normalise=parsed.nom_normalise,
                quantite=parsed.quantite,
                unite=parsed.unite,
                note=parsed.note,
                categorie_id=cat_id,
                categorie_nom=cat_names.get(cat_id),
            )
        )
    # L'apprentissage éventuel (resolve peut créer des entrées) est validé ici
    db.commit()

    draft = ScrapeDraft(
        titre=data.titre or "",
        url_source=data.url_source or url,
        host=data.host,
        image_url=data.image_url,
        portions=data.portions,
        temps_prep=data.temps_prep,
        temps_cuisson=data.temps_cuisson,
        instructions=data.instructions,
        ingredients=ingredients,
    )
    return ScrapeResponse(source=data.source, draft=draft)
