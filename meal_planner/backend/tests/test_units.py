"""Tests PURS du moteur de conversion d'unités (aucune dépendance DB).

Lancer depuis la racine du projet :
    python -m pytest backend/tests/test_units.py -q
"""
from __future__ import annotations

import pytest

from backend.services import units


# --------------------------------------------------------------------------- #
# dimension()
# --------------------------------------------------------------------------- #

def test_dimension_masse():
    assert units.dimension("g") == "masse"
    assert units.dimension("kg") == "masse"
    assert units.dimension("mg") == "masse"
    assert units.dimension("oz") == "masse"
    assert units.dimension("lb") == "masse"


def test_dimension_volume():
    assert units.dimension("ml") == "volume"
    assert units.dimension("l") == "volume"
    assert units.dimension("tasse") == "volume"
    assert units.dimension("c. à soupe") == "volume"
    assert units.dimension("c. à thé") == "volume"


def test_dimension_none_est_unite():
    assert units.dimension(None) == "unite"


def test_dimension_comptage_nomme_est_son_nom():
    assert units.dimension("gousse") == "gousse"
    assert units.dimension("tranche") == "tranche"
    assert units.dimension("pincée") == "pincée"


def test_dimension_inconnue_est_son_nom():
    assert units.dimension("zorglub") == "zorglub"


def test_dimension_insensible_casse_espaces():
    assert units.dimension("  KG ") == "masse"
    assert units.dimension("ML") == "volume"


# --------------------------------------------------------------------------- #
# Conversions MASSE
# --------------------------------------------------------------------------- #

def test_convert_kg_vers_g():
    assert units.convert(1, "kg", "g") == pytest.approx(1000)


def test_convert_g_vers_kg():
    assert units.convert(500, "g", "kg") == pytest.approx(0.5)


def test_convert_mg_vers_g():
    assert units.convert(2000, "mg", "g") == pytest.approx(2)


def test_convert_oz_vers_g():
    assert units.convert(1, "oz", "g") == pytest.approx(28.35)


def test_convert_lb_vers_g():
    assert units.convert(1, "lb", "g") == pytest.approx(453.592)


def test_convert_lb_vers_kg():
    assert units.convert(2, "lb", "kg") == pytest.approx(0.907184)


# --------------------------------------------------------------------------- #
# Conversions VOLUME
# --------------------------------------------------------------------------- #

def test_convert_l_vers_ml():
    assert units.convert(1, "l", "ml") == pytest.approx(1000)


def test_convert_tasse_vers_ml():
    assert units.convert(1, "tasse", "ml") == pytest.approx(250)


def test_convert_cuillere_soupe_vers_ml():
    assert units.convert(1, "c. à soupe", "ml") == pytest.approx(15)


def test_convert_cuillere_the_vers_ml():
    assert units.convert(1, "c. à thé", "ml") == pytest.approx(5)


def test_convert_ml_vers_l():
    assert units.convert(750, "ml", "l") == pytest.approx(0.75)


def test_convert_tasse_vers_cuillere_soupe():
    # 250 ml / 15 ml ≈ 16.6667 c. à soupe
    assert units.convert(1, "tasse", "c. à soupe") == pytest.approx(250 / 15)


# --------------------------------------------------------------------------- #
# convert() : identité & incompatibilité
# --------------------------------------------------------------------------- #

def test_convert_identite_meme_unite():
    assert units.convert(42, "g", "g") == 42


def test_convert_identite_comptage():
    assert units.convert(3, "gousse", "gousse") == 3


def test_convert_incompatible_masse_volume():
    assert units.convert(100, "g", "ml") is None


def test_convert_incompatible_comptages():
    assert units.convert(2, "gousse", "tranche") is None


def test_convert_qty_none():
    assert units.convert(None, "g", "kg") is None


def test_convert_casse_et_espaces():
    assert units.convert(1, "KG", " g ") == pytest.approx(1000)


# --------------------------------------------------------------------------- #
# are_compatible()
# --------------------------------------------------------------------------- #

def test_compatible_g_kg():
    assert units.are_compatible("g", "kg") is True


def test_compatible_ml_l_tasse():
    assert units.are_compatible("ml", "l") is True
    assert units.are_compatible("tasse", "ml") is True


def test_incompatible_g_ml():
    assert units.are_compatible("g", "ml") is False


def test_incompatible_gousse_tranche():
    assert units.are_compatible("gousse", "tranche") is False


def test_compatible_none_none():
    assert units.are_compatible(None, None) is True


def test_incompatible_none_gousse():
    assert units.are_compatible(None, "gousse") is False


def test_compatible_meme_comptage():
    assert units.are_compatible("botte", "botte") is True


def test_compatible_inconnue_avec_elle_meme():
    assert units.are_compatible("zorglub", "zorglub") is True
    assert units.are_compatible("zorglub", "machin") is False


# --------------------------------------------------------------------------- #
# to_base()
# --------------------------------------------------------------------------- #

def test_to_base_masse():
    val, base = units.to_base(2, "kg")
    assert val == pytest.approx(2000)
    assert base == "g"


def test_to_base_volume():
    val, base = units.to_base(2, "tasse")
    assert val == pytest.approx(500)
    assert base == "ml"


def test_to_base_comptage_nomme():
    val, base = units.to_base(3, "gousse")
    assert val == 3
    assert base == "gousse"


def test_to_base_sans_unite():
    val, base = units.to_base(4, None)
    assert val == 4
    assert base is None


def test_to_base_qty_none_garde_base():
    val, base = units.to_base(None, "kg")
    assert val is None
    assert base == "g"
