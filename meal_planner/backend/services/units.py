"""Conversions d'unités + compatibilité dimensionnelle (Phase 4).

Ce module est le socle « physique » de l'agrégateur de liste d'épicerie. Il sait
répondre à trois questions :

  1. À quelle DIMENSION appartient une unité ? (masse / volume / comptage)
  2. Deux unités sont-elles COMPATIBLES (donc additionnables après conversion) ?
  3. Comment CONVERTIR une quantité d'une unité vers une autre ?

Unités canoniques produites par le parseur (voir ingredient_parser.py) :
    tasse, c. à soupe, c. à thé, ml, l, g, kg, mg, oz, lb,
    gousse, tranche, pincée, botte, branche, boîte, conserve, sachet,
    paquet, tête, feuille, brin
… plus None quand l'ingrédient n'a pas d'unité (« 2 tomates »).

Choix de conception :
  - MASSE  : unité de base = g.
  - VOLUME : unité de base = ml. La tasse vaut 250 ml (mesure métrique du Québec).
  - COMPTAGE NOMMÉ (gousse, tranche, botte…) : chaque unité forme SA PROPRE
    dimension, compatible uniquement avec elle-même (une gousse n'est pas une
    tranche). La « pincée » est traitée comme un comptage nommé.
  - SANS UNITÉ (None) : dimension « unite » (comptage anonyme, « 2 tomates »).
  - Toute unité INCONNUE est traitée comme sa propre dimension (compatible
    seulement avec elle-même) : le moteur ne plante jamais.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# Tables de conversion : facteur vers l'unité de base de la dimension.
# --------------------------------------------------------------------------- #

# MASSE — base : gramme (g).
_MASSE: dict[str, float] = {
    "g": 1.0,
    "kg": 1000.0,
    "mg": 0.001,
    "oz": 28.35,       # once (poids)
    "lb": 453.592,     # livre
}

# VOLUME — base : millilitre (ml).
_VOLUME: dict[str, float] = {
    "ml": 1.0,
    "l": 1000.0,
    "tasse": 250.0,        # mesure QC
    "c. à soupe": 15.0,    # cuillère à soupe
    "c. à thé": 5.0,       # cuillère à thé
}

# Nom des unités de base par dimension.
_BASE_MASSE = "g"
_BASE_VOLUME = "ml"


def _norm(unit: str | None) -> str | None:
    """Normalise une unité : minuscules, espaces superflus repliés.

    None reste None. On préserve les accents car les formes canoniques
    (« c. à soupe », « c. à thé ») en contiennent.
    """
    if unit is None:
        return None
    n = " ".join(str(unit).lower().split())
    return n if n else None


def dimension(unit: str | None) -> str:
    """Renvoie la dimension d'une unité.

    - 'masse'  pour g/kg/mg/oz/lb
    - 'volume' pour ml/l/tasse/c. à soupe/c. à thé
    - 'unite'  quand il n'y a pas d'unité (None)  -> comptage anonyme
    - le NOM MÊME de l'unité pour un comptage nommé (« gousse », « tranche »…)
      ou pour toute unité inconnue (compatible seulement avec elle-même).
    """
    n = _norm(unit)
    if n is None:
        return "unite"
    if n in _MASSE:
        return "masse"
    if n in _VOLUME:
        return "volume"
    # Comptage nommé ou unité inconnue : sa dimension est son propre nom.
    return n


def are_compatible(u1: str | None, u2: str | None) -> bool:
    """True si u1 et u2 partagent la même dimension (donc additionnables).

    Exemples : g/kg -> True ; g/ml -> False ; gousse/tranche -> False ;
    None/None -> True ; None/gousse -> False.
    """
    return dimension(u1) == dimension(u2)


def convert(qty: float, from_unit: str | None, to_unit: str | None) -> float | None:
    """Convertit `qty` de `from_unit` vers `to_unit`.

    Renvoie None si les unités sont incompatibles ou si `qty` est None.
    Identité (qty inchangé) si même unité ou même comptage nommé/anonyme.
    """
    if qty is None:
        return None
    if not are_compatible(from_unit, to_unit):
        return None

    fu, tu = _norm(from_unit), _norm(to_unit)
    dim = dimension(from_unit)

    if dim == "masse":
        return qty * _MASSE[fu] / _MASSE[tu]
    if dim == "volume":
        return qty * _VOLUME[fu] / _VOLUME[tu]
    # Comptage nommé/anonyme/inconnu : compatibles => forcément identiques => identité.
    return qty


def to_base(qty, unit: str | None):
    """Renvoie (valeur_en_base, unite_base).

    - masse  -> (qty en grammes, 'g')
    - volume -> (qty en millilitres, 'ml')
    - sinon  -> (qty inchangé, unité normalisée elle-même ou None)

    Robuste : si `qty` est None, la valeur renvoyée est None mais l'unité de
    base est tout de même déterminée (utile pour connaître la dimension).
    """
    n = _norm(unit)
    dim = dimension(unit)

    if dim == "masse":
        val = qty * _MASSE[n] if qty is not None else None
        return val, _BASE_MASSE
    if dim == "volume":
        val = qty * _VOLUME[n] if qty is not None else None
        return val, _BASE_VOLUME
    # Comptage nommé/anonyme/inconnu : la base est l'unité elle-même (ou None).
    return qty, n
