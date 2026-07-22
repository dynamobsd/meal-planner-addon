# -*- coding: utf-8 -*-
"""Suggestions de repas assistées par IA (API Claude).

À partir des goûts/contraintes (« pour ma blonde… »), des recettes déjà
enregistrées et d'un type de plat optionnel, propose des idées de repas —
en priorisant les recettes existantes quand elles conviennent.

Réutilise la clé ANTHROPIC_API_KEY (option de l'add-on). Désactivation propre
si absente.
"""
from __future__ import annotations

import os

from pydantic import BaseModel, Field

from ..schemas import MealSuggestion, SuggestionsResponse

MODEL = "claude-opus-4-8"


class _AiSuggestion(BaseModel):
    titre: str
    type_plat: str | None = None
    raison: str | None = None
    recipe_id: int | None = None
    nouvelle_idee: bool = False
    ingredients_cles: list[str] = Field(default_factory=list)


class _AiSuggestions(BaseModel):
    suggestions: list[_AiSuggestion] = Field(default_factory=list)


def is_configured() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


_SYSTEM = (
    "Tu es un assistant culinaire québécois qui propose des idées de repas "
    "personnalisées pour un couple. On te donne : les goûts/contraintes de "
    "l'utilisateur, la liste de ses recettes déjà enregistrées (avec leur id et "
    "type de plat), un type de plat optionnel à respecter, et le nombre d'idées "
    "voulu. Propose des repas variés et réalistes. "
    "QUAND une recette enregistrée convient, réutilise-la : mets son `recipe_id` "
    "et `nouvelle_idee=false`. Sinon propose une idée nouvelle : `recipe_id=null` "
    "et `nouvelle_idee=true`, avec quelques `ingredients_cles`. Remplis `raison` "
    "en tenant compte des goûts fournis (ex: « ta blonde aime le poulet »). "
    "Respecte `type_plat` s'il est fourni. Réponds en français."
)


def suggest_meals(
    preferences: str | None,
    nb_repas: int,
    type_plat: str | None,
    recettes: list[dict],
) -> SuggestionsResponse:
    """recettes: liste de {id, titre, categorie_plat, note_etoiles}."""
    if not is_configured():
        return SuggestionsResponse(
            ok=True,
            disponible=False,
            message=(
                "Les suggestions par IA ne sont pas configurées. Ajoute ta clé API "
                "Anthropic dans les options de l'add-on (anthropic_api_key)."
            ),
        )

    try:
        import anthropic
    except ImportError:  # pragma: no cover
        return SuggestionsResponse(
            ok=False, disponible=False, message="Librairie 'anthropic' non installée."
        )

    lignes = [
        f"- id={r['id']} | {r['titre']}"
        + (f" [{r['categorie_plat']}]" if r.get("categorie_plat") else "")
        + (f" ★{r['note_etoiles']}" if r.get("note_etoiles") else "")
        for r in recettes
    ]
    recettes_txt = "\n".join(lignes) if lignes else "(aucune recette enregistrée)"

    user = (
        f"Goûts / contraintes : {preferences or '(non précisé)'}\n"
        f"Type de plat imposé : {type_plat or '(aucun)'}\n"
        f"Nombre d'idées voulues : {nb_repas}\n\n"
        f"Mes recettes enregistrées :\n{recettes_txt}"
    )

    try:
        client = anthropic.Anthropic()
        response = client.messages.parse(
            model=MODEL,
            max_tokens=4096,
            system=_SYSTEM,
            messages=[{"role": "user", "content": user}],
            output_format=_AiSuggestions,
        )
    except anthropic.APIStatusError as exc:  # pragma: no cover - réseau
        return SuggestionsResponse(
            ok=False,
            disponible=True,
            message=f"Erreur API Claude ({getattr(exc, 'status_code', '?')}).",
        )
    except Exception as exc:  # pragma: no cover
        return SuggestionsResponse(
            ok=False, disponible=True, message=f"Échec des suggestions : {exc}"
        )

    parsed = response.parsed_output
    if parsed is None:
        return SuggestionsResponse(
            ok=False, disponible=True, message="Réponse IA illisible."
        )

    valid_ids = {r["id"] for r in recettes}
    out: list[MealSuggestion] = []
    for s in parsed.suggestions[:nb_repas]:
        rid = s.recipe_id if s.recipe_id in valid_ids else None
        out.append(
            MealSuggestion(
                titre=s.titre,
                type_plat=s.type_plat,
                raison=s.raison,
                recipe_id=rid,
                nouvelle_idee=(rid is None),
                ingredients_cles=s.ingredients_cles,
            )
        )
    return SuggestionsResponse(ok=True, disponible=True, suggestions=out)
