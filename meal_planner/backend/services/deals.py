# -*- coding: utf-8 -*-
"""Alerte aubaines assistée par IA (API Claude).

Prend le texte brut d'une circulaire d'épicerie + la liste d'ingrédients de la
semaine, et demande à Claude d'extraire les aubaines en signalant lesquelles
correspondent à des ingrédients dont on a besoin.

La clé API est fournie via les options de l'add-on (variable d'environnement
ANTHROPIC_API_KEY, exportée par run.sh). Si absente, la feature se désactive
proprement (disponible=False) au lieu de planter.
"""
from __future__ import annotations

import os

from pydantic import BaseModel, Field

from ..schemas import DealMatch, DealsScanResponse

MODEL = "claude-opus-4-8"


# --- Schéma de sortie structurée demandé à Claude ------------------------- #
class _AiDeal(BaseModel):
    produit: str
    prix: str | None = None
    rabais: str | None = None
    ingredient_liste: str | None = None
    pertinent: bool = False
    note: str | None = None


class _AiDeals(BaseModel):
    aubaines: list[_AiDeal] = Field(default_factory=list)


def is_configured() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


_SYSTEM = (
    "Tu es un assistant d'épicerie québécois. On te donne le texte brut d'une "
    "circulaire de supermarché et la liste des ingrédients dont l'utilisateur a "
    "besoin cette semaine. Extrais UNIQUEMENT les vraies aubaines/rabais présents "
    "dans la circulaire. Pour chaque aubaine, indique le produit, le prix et le "
    "rabais tels qu'écrits. Marque `pertinent=true` et remplis `ingredient_liste` "
    "avec le nom de l'ingrédient correspondant SEULEMENT si le produit correspond "
    "clairement à un ingrédient de la liste fournie (tolère les variantes: "
    "'poitrines de poulet' correspond à 'poulet'). Sinon `pertinent=false`. "
    "N'invente aucune aubaine qui n'est pas dans le texte. Réponds en français."
)


def scan_deals(
    texte_circulaire: str,
    liste_ingredients: list[str],
    magasin: str | None = None,
) -> DealsScanResponse:
    """Analyse une circulaire et renvoie les aubaines (priorisées si pertinentes)."""
    if not is_configured():
        return DealsScanResponse(
            ok=True,
            disponible=False,
            message=(
                "L'alerte aubaines par IA n'est pas configurée. Ajoute ta clé API "
                "Anthropic dans les options de l'add-on (anthropic_api_key)."
            ),
        )

    texte = (texte_circulaire or "").strip()
    if not texte:
        return DealsScanResponse(ok=True, disponible=True, aubaines=[])

    try:
        import anthropic  # import tardif : évite la dépendance si non utilisé
    except ImportError:  # pragma: no cover
        return DealsScanResponse(
            ok=False,
            disponible=False,
            message="Librairie 'anthropic' non installée.",
        )

    liste = ", ".join(sorted(set(i for i in liste_ingredients if i))) or "(aucune)"
    user = (
        f"Magasin: {magasin or 'non précisé'}\n\n"
        f"Ingrédients dont j'ai besoin cette semaine: {liste}\n\n"
        f"--- TEXTE DE LA CIRCULAIRE ---\n{texte[:12000]}"
    )

    try:
        client = anthropic.Anthropic()  # lit ANTHROPIC_API_KEY dans l'environnement
        response = client.messages.parse(
            model=MODEL,
            max_tokens=4096,
            system=_SYSTEM,
            messages=[{"role": "user", "content": user}],
            output_format=_AiDeals,
        )
    except anthropic.APIStatusError as exc:  # pragma: no cover - dépend du réseau
        return DealsScanResponse(
            ok=False,
            disponible=True,
            message=f"Erreur API Claude ({getattr(exc, 'status_code', '?')}).",
        )
    except Exception as exc:  # pragma: no cover
        return DealsScanResponse(
            ok=False, disponible=True, message=f"Échec de l'analyse: {exc}"
        )

    parsed = response.parsed_output
    if parsed is None:
        return DealsScanResponse(
            ok=False, disponible=True, message="Réponse IA illisible."
        )

    aubaines = [
        DealMatch(
            produit=d.produit,
            prix=d.prix,
            rabais=d.rabais,
            ingredient_liste=d.ingredient_liste,
            pertinent=d.pertinent,
            note=d.note,
        )
        for d in parsed.aubaines
    ]
    # Priorise les aubaines pertinentes (celles qui matchent la liste) en tête
    aubaines.sort(key=lambda a: (not a.pertinent, a.produit.lower()))
    return DealsScanResponse(ok=True, disponible=True, aubaines=aubaines)
