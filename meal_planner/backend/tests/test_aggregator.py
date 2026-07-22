"""Tests PURS du moteur d'agrégation (aucune dépendance DB).

Lancer depuis la racine du projet :
    python -m pytest backend/tests/test_aggregator.py -q
"""
from __future__ import annotations

import pytest

from backend.services.aggregator import AggregatedLine, aggregate_ingredients


def _item(nom, quantite=None, unite=None, categorie_id=None) -> dict:
    return {
        "nom_normalise": nom,
        "quantite": quantite,
        "unite": unite,
        "categorie_id": categorie_id,
    }


def _pantry(nom, quantite=None, unite=None) -> dict:
    return {"nom_ingredient": nom, "quantite": quantite, "unite": unite}


def _by_nom(lines: list[AggregatedLine]) -> dict[str, list[AggregatedLine]]:
    out: dict[str, list[AggregatedLine]] = {}
    for l in lines:
        out.setdefault(l.nom, []).append(l)
    return out


# --------------------------------------------------------------------------- #
# Addition — même dimension
# --------------------------------------------------------------------------- #

def test_addition_sans_unite():
    res = aggregate_ingredients(
        [_item("tomate", 1, None), _item("tomate", 1, None)], []
    )
    assert len(res) == 1
    assert res[0].nom == "tomate"
    assert res[0].quantite_totale == 2
    assert res[0].unite is None
    assert res[0].avertissement is None


def test_addition_masse_avec_conversion():
    res = aggregate_ingredients(
        [_item("farine", 200, "g"), _item("farine", 0.3, "kg")], []
    )
    assert len(res) == 1
    assert res[0].quantite_totale == pytest.approx(500)
    assert res[0].unite == "g"


def test_addition_masse_reexprime_en_kg():
    res = aggregate_ingredients(
        [_item("farine", 800, "g"), _item("farine", 0.5, "kg")], []
    )
    assert len(res) == 1
    # 800 g + 500 g = 1300 g -> 1.3 kg
    assert res[0].quantite_totale == pytest.approx(1.3)
    assert res[0].unite == "kg"


def test_addition_volume_tasses_et_ml():
    res = aggregate_ingredients(
        [_item("lait", 2, "tasse"), _item("lait", 250, "ml")], []
    )
    assert len(res) == 1
    # 2 tasses = 500 ml + 250 ml = 750 ml
    assert res[0].quantite_totale == pytest.approx(750)
    assert res[0].unite == "ml"


def test_addition_volume_reexprime_en_litres():
    res = aggregate_ingredients(
        [_item("bouillon", 3, "tasse"), _item("bouillon", 500, "ml")], []
    )
    # 750 ml + 500 ml = 1250 ml -> 1.25 l
    assert len(res) == 1
    assert res[0].quantite_totale == pytest.approx(1.25)
    assert res[0].unite == "l"


def test_addition_comptage_nomme():
    res = aggregate_ingredients(
        [_item("ail", 2, "gousse"), _item("ail", 3, "gousse")], []
    )
    assert len(res) == 1
    assert res[0].quantite_totale == 5
    assert res[0].unite == "gousse"


# --------------------------------------------------------------------------- #
# Unités incompatibles pour un même nom -> 2 lignes + avertissement
# --------------------------------------------------------------------------- #

def test_unites_incompatibles_deux_lignes():
    res = aggregate_ingredients(
        [_item("tomate", 200, "g"), _item("tomate", 2, None)], []
    )
    assert len(res) == 2
    for l in res:
        assert l.nom == "tomate"
        assert l.avertissement is not None
        assert "non fusionnées" in l.avertissement
    # Une ligne en g, une ligne sans unité.
    unites = sorted([str(l.unite) for l in res])
    assert unites == ["None", "g"]


def test_unites_incompatibles_valeurs_correctes():
    res = aggregate_ingredients(
        [_item("tomate", 200, "g"), _item("tomate", 2, None)], []
    )
    par_unite = {l.unite: l for l in res}
    assert par_unite["g"].quantite_totale == pytest.approx(200)
    assert par_unite[None].quantite_totale == 2


def test_deux_comptages_nommes_incompatibles():
    res = aggregate_ingredients(
        [_item("pain", 4, "tranche"), _item("pain", 1, "boîte")], []
    )
    assert len(res) == 2
    for l in res:
        assert l.avertissement is not None


# --------------------------------------------------------------------------- #
# Soustraction du garde-manger
# --------------------------------------------------------------------------- #

def test_pantry_reduit_la_quantite():
    res = aggregate_ingredients(
        [_item("farine", 500, "g")],
        [_pantry("farine", 200, "g")],
    )
    assert len(res) == 1
    assert res[0].quantite_totale == pytest.approx(300)
    assert res[0].unite == "g"


def test_pantry_reduit_avec_conversion():
    res = aggregate_ingredients(
        [_item("farine", 1, "kg")],
        [_pantry("farine", 250, "g")],
    )
    # 1000 g - 250 g = 750 g
    assert len(res) == 1
    assert res[0].quantite_totale == pytest.approx(750)
    assert res[0].unite == "g"


def test_pantry_amene_a_zero_exclut():
    res = aggregate_ingredients(
        [_item("farine", 500, "g")],
        [_pantry("farine", 500, "g")],
    )
    assert res == []


def test_pantry_superieur_exclut():
    res = aggregate_ingredients(
        [_item("farine", 300, "g")],
        [_pantry("farine", 1, "kg")],
    )
    assert res == []


def test_pantry_quantite_none_item_sans_unite_exclut():
    # Garde-manger connaît le nom mais sans quantité ; item sans quantité -> exclu.
    res = aggregate_ingredients(
        [_item("sel", None, None)],
        [_pantry("sel", None, None)],
    )
    assert res == []


def test_pantry_quantite_none_ne_soustrait_pas_item_chiffre():
    # Item chiffré, garde-manger sans quantité : on ne soustrait pas, l'item reste.
    res = aggregate_ingredients(
        [_item("farine", 500, "g")],
        [_pantry("farine", None, "g")],
    )
    assert len(res) == 1
    assert res[0].quantite_totale == pytest.approx(500)


def test_pantry_unite_incompatible_ne_soustrait_pas():
    res = aggregate_ingredients(
        [_item("tomate", 3, None)],
        [_pantry("tomate", 200, "g")],   # incompatible avec « sans unité »
    )
    assert len(res) == 1
    assert res[0].quantite_totale == 3
    assert res[0].unite is None


def test_pantry_nom_absent_aucun_effet():
    res = aggregate_ingredients(
        [_item("farine", 500, "g")],
        [_pantry("sucre", 200, "g")],
    )
    assert len(res) == 1
    assert res[0].quantite_totale == pytest.approx(500)


def test_pantry_insensible_casse():
    res = aggregate_ingredients(
        [_item("Farine", 500, "g")],
        [_pantry("FARINE", 200, "g")],
    )
    assert len(res) == 1
    assert res[0].quantite_totale == pytest.approx(300)


# --------------------------------------------------------------------------- #
# categorie_id & robustesse
# --------------------------------------------------------------------------- #

def test_conserve_categorie_id_premier_non_none():
    res = aggregate_ingredients(
        [_item("farine", 100, "g", categorie_id=None),
         _item("farine", 100, "g", categorie_id=7)],
        [],
    )
    assert len(res) == 1
    assert res[0].categorie_id == 7


def test_robustesse_quantites_none_sans_pantry():
    res = aggregate_ingredients([_item("sel", None, None)], [])
    assert len(res) == 1
    assert res[0].quantite_totale is None
    assert res[0].unite is None


def test_robustesse_none_mixte_ignore_none():
    # Une valeur connue + une None dans le même bucket : on somme le connu.
    res = aggregate_ingredients(
        [_item("farine", 200, "g"), _item("farine", None, "g")], []
    )
    assert len(res) == 1
    assert res[0].quantite_totale == pytest.approx(200)


def test_liste_vide():
    assert aggregate_ingredients([], []) == []


def test_tri_par_nom():
    res = aggregate_ingredients(
        [_item("zucchini", 1, None), _item("ail", 1, None), _item("basilic", 1, None)],
        [],
    )
    noms = [l.nom for l in res]
    assert noms == sorted(noms, key=str.lower)


def test_plusieurs_noms_independants():
    res = aggregate_ingredients(
        [_item("farine", 200, "g"), _item("farine", 300, "g"),
         _item("oeuf", 2, None), _item("oeuf", 1, None)],
        [],
    )
    d = _by_nom(res)
    assert d["farine"][0].quantite_totale == pytest.approx(500)
    assert d["oeuf"][0].quantite_totale == 3
