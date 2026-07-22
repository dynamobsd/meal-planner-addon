"""Tests EXHAUSTIFS du parseur d'ingrédients français (parseur PUR).

Aucune dépendance à la base de données ni à SQLAlchemy : on n'importe que
`backend.services.ingredient_parser`. Lancer depuis la racine du projet :

    python -m pytest backend/tests/test_ingredient_parser.py -q
"""
from __future__ import annotations

import pytest

from backend.services.ingredient_parser import ParsedIngredient, parse_ingredient


# --------------------------------------------------------------------------- #
# Fractions ASCII
# --------------------------------------------------------------------------- #

def test_fraction_ascii_demi():
    p = parse_ingredient("1/2 tasse de sucre")
    assert p.quantite == pytest.approx(0.5)
    assert p.unite == "tasse"
    assert p.nom_normalise == "sucre"
    assert p.note is None


def test_fraction_ascii_trois_quarts():
    p = parse_ingredient("3/4 tasse de farine")
    assert p.quantite == pytest.approx(0.75)
    assert p.unite == "tasse"
    assert p.nom_normalise == "farine"


# --------------------------------------------------------------------------- #
# Fractions unicode
# --------------------------------------------------------------------------- #

def test_fraction_unicode_demi():
    p = parse_ingredient("½ tasse de lait")
    assert p.quantite == pytest.approx(0.5)
    assert p.unite == "tasse"
    assert p.nom_normalise == "lait"


def test_fraction_unicode_quart_cuillere_the():
    p = parse_ingredient("¼ c. à thé de sel")
    assert p.quantite == pytest.approx(0.25)
    assert p.unite == "c. à thé"
    assert p.nom_normalise == "sel"


def test_fraction_unicode_tiers():
    p = parse_ingredient("⅓ tasse d'huile")
    assert p.quantite == pytest.approx(1 / 3)
    assert p.unite == "tasse"
    assert p.nom_normalise == "huile"


# --------------------------------------------------------------------------- #
# Nombres mixtes
# --------------------------------------------------------------------------- #

def test_nombre_mixte_ascii():
    p = parse_ingredient("1 1/2 tasse de farine")
    assert p.quantite == pytest.approx(1.5)
    assert p.unite == "tasse"
    assert p.nom_normalise == "farine"


def test_nombre_mixte_unicode_espace():
    p = parse_ingredient("1 ½ tasse de lait")
    assert p.quantite == pytest.approx(1.5)
    assert p.unite == "tasse"
    assert p.nom_normalise == "lait"


def test_nombre_mixte_unicode_colle():
    p = parse_ingredient("2½ tasses de bouillon")
    assert p.quantite == pytest.approx(2.5)
    assert p.unite == "tasse"
    assert p.nom_normalise == "bouillon"


# --------------------------------------------------------------------------- #
# Plages : on GARDE LA BORNE HAUTE
# --------------------------------------------------------------------------- #

def test_plage_tiret_borne_haute():
    p = parse_ingredient("2-3 gousses d'ail")
    assert p.quantite == pytest.approx(3.0)   # borne haute
    assert p.unite == "gousse"
    assert p.nom_normalise == "ail"


def test_plage_a_borne_haute():
    p = parse_ingredient("2 à 3 tasses de bouillon")
    assert p.quantite == pytest.approx(3.0)   # borne haute
    assert p.unite == "tasse"
    assert p.nom_normalise == "bouillon"


def test_plage_a_ne_confond_pas_avec_nom():
    # « 2 avocats » ne doit PAS être lu comme une plage « 2 a ... ».
    p = parse_ingredient("2 avocats")
    assert p.quantite == pytest.approx(2.0)
    assert p.unite is None
    assert p.nom_normalise == "avocat"


# --------------------------------------------------------------------------- #
# Unités + abréviations normalisées
# --------------------------------------------------------------------------- #

def test_unite_abrev_cuillere_soupe_points():
    p = parse_ingredient("2 c. à s. de beurre")
    assert p.quantite == pytest.approx(2.0)
    assert p.unite == "c. à soupe"
    assert p.nom_normalise == "beurre"


def test_unite_cuillere_soupe_complet():
    p = parse_ingredient("1 cuillère à soupe de miel")
    assert p.quantite == pytest.approx(1.0)
    assert p.unite == "c. à soupe"
    assert p.nom_normalise == "miel"


def test_unite_cac_the():
    p = parse_ingredient("2 cac de vanille")
    assert p.quantite == pytest.approx(2.0)
    assert p.unite == "c. à thé"
    assert p.nom_normalise == "vanille"


def test_unite_grammes_espace():
    p = parse_ingredient("250 g de farine")
    assert p.quantite == pytest.approx(250.0)
    assert p.unite == "g"
    assert p.nom_normalise == "farine"


def test_unite_grammes_colle():
    p = parse_ingredient("250g de beurre")
    assert p.quantite == pytest.approx(250.0)
    assert p.unite == "g"
    assert p.nom_normalise == "beurre"


def test_unite_kg_avec_nom_compose():
    p = parse_ingredient("1 kg de pommes de terre")
    assert p.quantite == pytest.approx(1.0)
    assert p.unite == "kg"
    assert p.nom_normalise == "pomme de terre"


def test_unite_ml():
    p = parse_ingredient("500 ml de lait")
    assert p.quantite == pytest.approx(500.0)
    assert p.unite == "ml"
    assert p.nom_normalise == "lait"


def test_unite_litre_decimal_virgule():
    p = parse_ingredient("1,5 litre d'eau")
    assert p.quantite == pytest.approx(1.5)
    assert p.unite == "l"
    assert p.nom_normalise == "eau"


def test_unite_boite():
    p = parse_ingredient("1 boîte de tomates")
    assert p.quantite == pytest.approx(1.0)
    assert p.unite == "boîte"
    assert p.nom_normalise == "tomate"


def test_unite_tranche_pas_qualificatif():
    # « tranches » ici est une UNITÉ, pas la préparation « tranché ».
    p = parse_ingredient("2 tranches de jambon")
    assert p.quantite == pytest.approx(2.0)
    assert p.unite == "tranche"
    assert p.nom_normalise == "jambon"
    assert p.note is None


def test_unite_pincee_avec_chiffre():
    p = parse_ingredient("1 pincée de sel")
    assert p.quantite == pytest.approx(1.0)
    assert p.unite == "pincée"
    assert p.nom_normalise == "sel"


def test_unite_feuilles_avec_article_quelques():
    p = parse_ingredient("quelques feuilles de basilic")
    assert p.quantite is None
    assert p.unite == "feuille"
    assert p.nom_normalise == "basilic"


def test_unite_pincee_avec_article_une():
    p = parse_ingredient("une pincée de muscade")
    assert p.quantite is None
    assert p.unite == "pincée"
    assert p.nom_normalise == "muscade"


# --------------------------------------------------------------------------- #
# Liant de / d'
# --------------------------------------------------------------------------- #

def test_liant_apostrophe():
    p = parse_ingredient("2 gousses d'ail")
    assert p.quantite == pytest.approx(2.0)
    assert p.unite == "gousse"
    assert p.nom_normalise == "ail"


def test_liant_apostrophe_typographique():
    # apostrophe typographique ’ doit être gérée comme '
    p = parse_ingredient("2 gousses d’ail")
    assert p.unite == "gousse"
    assert p.nom_normalise == "ail"


# --------------------------------------------------------------------------- #
# Sans unité
# --------------------------------------------------------------------------- #

def test_sans_unite_tomates():
    p = parse_ingredient("2 tomates")
    assert p.quantite == pytest.approx(2.0)
    assert p.unite is None
    assert p.nom_normalise == "tomate"


def test_sans_unite_pommes():
    p = parse_ingredient("3 pommes")
    assert p.quantite == pytest.approx(3.0)
    assert p.unite is None
    assert p.nom_normalise == "pomme"


def test_singularisation_invariable_ananas():
    p = parse_ingredient("200 g d'ananas")
    assert p.unite == "g"
    assert p.nom_normalise == "ananas"   # invariable : pas de « anana »


# --------------------------------------------------------------------------- #
# Qualificatifs de préparation séparés du nom -> note
# --------------------------------------------------------------------------- #

def test_qualificatif_hache():
    p = parse_ingredient("tomate hachée")
    assert p.quantite is None
    assert p.unite is None
    assert p.nom_normalise == "tomate"
    assert p.note == "haché"


def test_qualificatif_rape_pluriel():
    p = parse_ingredient("3 carottes râpées")
    assert p.quantite == pytest.approx(3.0)
    assert p.unite is None
    assert p.nom_normalise == "carotte"
    assert p.note == "râpé"


def test_qualificatif_multiple():
    p = parse_ingredient("1 oignon haché finement")
    assert p.quantite == pytest.approx(1.0)
    assert p.nom_normalise == "oignon"
    assert p.note is not None
    assert "haché" in p.note
    assert "finement" in p.note


def test_qualificatif_en_des():
    p = parse_ingredient("poivron rouge en dés")
    assert p.nom_normalise == "poivron rouge"
    assert p.note == "en dés"


def test_sel_au_gout():
    p = parse_ingredient("sel au goût")
    assert p.quantite is None
    assert p.unite is None
    assert p.nom_normalise == "sel"
    assert p.note == "au goût"


def test_poivre_seul():
    p = parse_ingredient("poivre")
    assert p.quantite is None
    assert p.unite is None
    assert p.nom_normalise == "poivre"
    assert p.note is None


# --------------------------------------------------------------------------- #
# Égalité CRITIQUE de nom_normalise
# --------------------------------------------------------------------------- #

def test_egalite_nom_normalise_tomate():
    a = parse_ingredient("tomate hachée")
    b = parse_ingredient("2 tomates")
    c = parse_ingredient("la tomate")
    assert a.nom_normalise == b.nom_normalise == c.nom_normalise == "tomate"


def test_egalite_nom_normalise_avec_accents():
    # accents et pluriel ne doivent pas empêcher le rapprochement
    a = parse_ingredient("céleri")
    b = parse_ingredient("2 branches de céleri")
    assert a.nom_normalise == b.nom_normalise == "celeri"


# --------------------------------------------------------------------------- #
# Entrées vides / bizarres : jamais d'exception
# --------------------------------------------------------------------------- #

def test_entree_vide():
    p = parse_ingredient("")
    assert isinstance(p, ParsedIngredient)
    assert p.quantite is None
    assert p.unite is None
    assert p.nom_normalise == ""
    assert p.note is None


def test_entree_espaces():
    p = parse_ingredient("   ")
    assert p.nom_normalise == ""
    assert p.quantite is None


def test_entree_none_ne_leve_pas():
    p = parse_ingredient(None)  # type: ignore[arg-type]
    assert isinstance(p, ParsedIngredient)
    assert p.nom_normalise == ""


def test_entree_ponctuation_seule():
    p = parse_ingredient("!!!")
    assert isinstance(p, ParsedIngredient)
    # pas d'exception ; nom_normalise = texte replié nettoyé (ici ponctuation)
    assert p.quantite is None


def test_texte_brut_conserve():
    raw = "2 gousses d'ail"
    p = parse_ingredient(raw)
    assert p.texte_brut == raw
