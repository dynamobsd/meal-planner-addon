"""Agrégation de la liste d'épicerie + soustraction du garde-manger (Phase 4).

Le routeur (routers/grocery.py) fournit :
  - `items`  : ingrédients de la semaine DÉJÀ mis à l'échelle.
  - `pantry` : contenu du garde-manger.

On produit des `AggregatedLine` prêtes à persister/afficher.

Décisions de conception (voir units.py pour les bases physiques) :
  - REGROUPEMENT par nom (insensible à la casse), puis par DIMENSION
    (via units.are_compatible). Un même nom peut donner PLUSIEURS lignes si ses
    unités ne sont pas fusionnables (« 200 g de tomates » vs « 2 tomates »).
  - ADDITION : à l'intérieur d'une dimension, tout est converti vers l'unité de
    base (g / ml / l'unité de comptage elle-même) puis sommé, avant d'être
    RÉ-EXPRIMÉ proprement :
        masse  -> g  si < 1000, sinon kg
        volume -> ml si < 1000, sinon l
        comptage nommé / sans unité -> l'unité (ou None) est conservée.
  - GARDE-MANGER : soustraction en unité de base. Résultat <= 0 => l'item
    disparaît de la liste. Ligne à quantité inconnue (None) dont le nom est au
    garde-manger => exclue (« on l'a déjà »). Entrée de garde-manger sans
    quantité (None) ou d'unité incompatible => on ne soustrait pas, l'item reste.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import units


@dataclass
class AggregatedLine:
    nom: str
    quantite_totale: float | None
    unite: str | None
    categorie_id: int | None
    avertissement: str | None = None


# --------------------------------------------------------------------------- #
# Helpers internes
# --------------------------------------------------------------------------- #

def _name_key(nom: str | None) -> str:
    """Clé de regroupement d'un nom : minuscules, espaces repliés."""
    if nom is None:
        return ""
    return " ".join(str(nom).lower().split())


def _round(x: float) -> float:
    """Arrondi d'affichage à 2 décimales, sans traîne « .0 » superflue.

    2.0 reste 2.0 (float), mais 2.004999 -> 2.0, 0.3333.. -> 0.33.
    """
    return round(x, 2)


def _reexpress(base_value: float | None, base_unit: str | None):
    """Ré-exprime une valeur en unité de base vers une unité « jolie ».

    Renvoie (quantite, unite).
    """
    if base_value is None:
        return None, base_unit

    if base_unit == "g":
        # Masse : g en dessous de 1000, kg au-delà.
        if base_value < 1000:
            return _round(base_value), "g"
        return _round(base_value / 1000.0), "kg"

    if base_unit == "ml":
        # Volume : ml en dessous de 1000, l au-delà.
        if base_value < 1000:
            return _round(base_value), "ml"
        return _round(base_value / 1000.0), "l"

    # Comptage nommé / sans unité : on garde l'unité telle quelle.
    return _round(base_value), base_unit


def _describe(line: AggregatedLine) -> str:
    """Décrit brièvement une ligne pour un message d'avertissement."""
    unite = line.unite if line.unite else "sans unité"
    qte = line.quantite_totale
    if qte is None:
        return f"quantité inconnue ({unite})"
    return f"{qte} {unite}"


# --------------------------------------------------------------------------- #
# Fonction publique
# --------------------------------------------------------------------------- #

def aggregate_ingredients(items: list[dict], pantry: list[dict]) -> list[AggregatedLine]:
    """Agrège les ingrédients et retranche le garde-manger.

    Voir le docstring du module pour la logique détaillée. Ne lève jamais
    d'exception sur des quantités None.
    """
    # ----- 1. Indexe le garde-manger par nom -----
    pantry_by_name: dict[str, list[dict]] = {}
    for p in pantry or []:
        key = _name_key(p.get("nom_ingredient"))
        pantry_by_name.setdefault(key, []).append(p)

    # ----- 2. Regroupe les items par nom, en préservant l'ordre d'apparition -----
    groups: dict[str, dict] = {}
    order: list[str] = []
    for it in items or []:
        key = _name_key(it.get("nom_normalise"))
        if key not in groups:
            groups[key] = {
                "nom": it.get("nom_normalise") or "",   # nom d'affichage (1er vu)
                "categorie_id": None,
                "buckets": {},                          # dimension -> data
            }
            order.append(key)
        g = groups[key]
        # categorie_id : premier non-None rencontré pour ce nom.
        if g["categorie_id"] is None and it.get("categorie_id") is not None:
            g["categorie_id"] = it.get("categorie_id")

        unite = it.get("unite")
        qty = it.get("quantite")
        dim = units.dimension(unite)
        base_val, base_unit = units.to_base(qty, unite)

        bucket = g["buckets"].get(dim)
        if bucket is None:
            bucket = {
                "base_unit": base_unit,   # 'g' / 'ml' / unité de comptage / None
                "rep_unit": unite,        # unité représentative (pour compat garde-manger)
                "total": 0.0,             # somme des quantités connues (en base)
                "has_value": False,       # au moins une quantité non-None ?
            }
            g["buckets"][dim] = bucket
        if base_val is not None:
            bucket["total"] += base_val
            bucket["has_value"] = True

    # ----- 3. Construit les lignes, avec soustraction garde-manger -----
    result: list[AggregatedLine] = []
    for key in order:
        g = groups[key]
        matching_pantry = pantry_by_name.get(key, [])
        name_in_pantry = len(matching_pantry) > 0

        emitted: list[AggregatedLine] = []
        for dim, bucket in g["buckets"].items():
            base_unit = bucket["base_unit"]
            rep_unit = bucket["rep_unit"]

            # --- Cas quantité inconnue (aucune valeur numérique dans le bucket) ---
            if not bucket["has_value"]:
                # « on l'a déjà » : si le nom est au garde-manger, on l'exclut.
                if name_in_pantry:
                    continue
                emitted.append(
                    AggregatedLine(
                        nom=g["nom"],
                        quantite_totale=None,
                        unite=rep_unit,
                        categorie_id=g["categorie_id"],
                    )
                )
                continue

            # --- Soustraction du garde-manger (en unité de base) ---
            remaining = bucket["total"]
            did_subtract = False
            for p in matching_pantry:
                p_unit = p.get("unite")
                p_qty = p.get("quantite")
                # Unité incompatible ou quantité manquante : on NE soustrait PAS.
                if not units.are_compatible(rep_unit, p_unit):
                    continue
                if p_qty is None:
                    continue
                p_base, _ = units.to_base(p_qty, p_unit)
                if p_base is None:
                    continue
                remaining -= p_base
                did_subtract = True

            # Épuisé par le garde-manger => l'item disparaît.
            if did_subtract and remaining <= 0:
                continue

            qte, unite = _reexpress(remaining, base_unit)
            emitted.append(
                AggregatedLine(
                    nom=g["nom"],
                    quantite_totale=qte,
                    unite=unite,
                    categorie_id=g["categorie_id"],
                )
            )

        # --- Avertissement si un même nom donne PLUSIEURS lignes (non fusionnées) ---
        if len(emitted) > 1:
            for i, line in enumerate(emitted):
                autres = [_describe(o) for j, o in enumerate(emitted) if j != i]
                line.avertissement = (
                    "Unités non fusionnées: existe aussi en " + ", ".join(autres)
                )

        result.extend(emitted)

    # ----- 4. Tri final par nom (le tri par rayon est géré ailleurs) -----
    result.sort(key=lambda l: (_name_key(l.nom), str(l.unite)))
    return result
