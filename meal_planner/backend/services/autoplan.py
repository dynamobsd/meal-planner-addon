# -*- coding: utf-8 -*-
"""Planning hebdomadaire automatique assisté par IA (API Claude).

À partir des recettes enregistrées, des goûts et des créneaux à remplir,
l'IA assigne une recette existante à chaque créneau (varié, équilibré).
Les créneaux sans recette adaptée reviennent comme « idées manquantes ».

Réutilise ANTHROPIC_API_KEY (option de l'add-on). Désactivation propre si absente.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

MODEL = "claude-opus-4-8"


class _AiSlot(BaseModel):
    date: str
    type_repas: str
    recipe_id: int | None = None
    titre: str
    raison: str | None = None


class _AiPlan(BaseModel):
    assignations: list[_AiSlot] = Field(default_factory=list)


@dataclass
class AutoPlanResult:
    disponible: bool
    ok: bool
    message: str | None = None
    assignations: list[dict] = field(default_factory=list)


def is_configured() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


_SYSTEM = (
    "Tu es un assistant qui compose un planning de repas hebdomadaire pour un "
    "couple. On te donne : la liste des recettes déjà enregistrées (id, titre, "
    "type de plat, étoiles, favori), les goûts/contraintes, et la liste EXACTE "
    "des créneaux à remplir (date + type_repas). Pour CHAQUE créneau fourni, "
    "assigne UNE recette. Privilégie les recettes existantes (mets leur "
    "`recipe_id` et le `titre` correspondant), varie les repas sur la semaine "
    "(évite de répéter la même recette), respecte les goûts et, si pertinent, le "
    "type de plat du créneau. Si aucune recette existante ne convient pour un "
    "créneau, propose une idée nouvelle (`recipe_id=null`, `titre`=idée). "
    "Renvoie EXACTEMENT un créneau par créneau demandé, mêmes date/type_repas. "
    "Réponds en français dans les `raison`."
)


def build_plan(
    slots: list[dict],       # [{"date": "...", "type_repas": "..."}]
    recettes: list[dict],    # [{"id","titre","categorie_plat","note_etoiles","favori"}]
    preferences: str | None,
) -> AutoPlanResult:
    if not is_configured():
        return AutoPlanResult(
            disponible=False,
            ok=True,
            message=(
                "Le planning automatique par IA n'est pas configuré. Ajoute ta clé "
                "API Anthropic dans les options de l'add-on (anthropic_api_key)."
            ),
        )
    if not recettes:
        return AutoPlanResult(
            disponible=True,
            ok=True,
            message="Ajoute d'abord quelques recettes pour générer un planning.",
        )

    try:
        import anthropic
    except ImportError:  # pragma: no cover
        return AutoPlanResult(False, False, "Librairie 'anthropic' non installée.")

    lignes = [
        f"- id={r['id']} | {r['titre']}"
        + (f" [{r['categorie_plat']}]" if r.get("categorie_plat") else "")
        + (f" ★{r['note_etoiles']}" if r.get("note_etoiles") else "")
        + (" ❤" if r.get("favori") else "")
        for r in recettes
    ]
    slots_txt = "\n".join(f"- {s['date']} / {s['type_repas']}" for s in slots)

    user = (
        f"Goûts / contraintes : {preferences or '(non précisé)'}\n\n"
        f"Créneaux à remplir (un repas chacun) :\n{slots_txt}\n\n"
        f"Recettes enregistrées :\n" + "\n".join(lignes)
    )

    try:
        client = anthropic.Anthropic()
        response = client.messages.parse(
            model=MODEL,
            max_tokens=4096,
            system=_SYSTEM,
            messages=[{"role": "user", "content": user}],
            output_format=_AiPlan,
        )
    except anthropic.APIStatusError as exc:  # pragma: no cover
        return AutoPlanResult(
            True, False, f"Erreur API Claude ({getattr(exc, 'status_code', '?')})."
        )
    except Exception as exc:  # pragma: no cover
        return AutoPlanResult(True, False, f"Échec du planning : {exc}")

    parsed = response.parsed_output
    if parsed is None:
        return AutoPlanResult(True, False, "Réponse IA illisible.")

    valid_ids = {r["id"] for r in recettes}
    assignations = [
        {
            "date": a.date,
            "type_repas": a.type_repas,
            "recipe_id": a.recipe_id if a.recipe_id in valid_ids else None,
            "titre": a.titre,
            "raison": a.raison,
        }
        for a in parsed.assignations
    ]
    return AutoPlanResult(True, True, None, assignations)
