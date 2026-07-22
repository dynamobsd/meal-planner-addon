"""Parsing d'ingrédients FRANÇAIS (Phase 2).

Objectif : transformer une ligne d'ingrédient brute (« 2 gousses d'ail hachées »,
« 1 1/2 tasse de farine », « sel au goût »…) en une structure exploitable :
quantité numérique, unité canonique, nom normalisé pour le matching, et note de
préparation séparée.

Contraintes de conception :
  - AUCUNE dépendance NLP : uniquement des regex + des dictionnaires.
  - Robuste : ne lève JAMAIS d'exception ; sur entrée vide/bizarre on renvoie un
    ParsedIngredient avec `nom_normalise` = texte nettoyé.

Choix important — le NOM NORMALISÉ est « replié » (folded) :
  mis en minuscules ET débarrassé des accents (é→e, œ→oe, à→a…). Ce repli rend
  le matching de catégorie insensible aux accents (« céleri » == « celeri »),
  ce qui est un avantage pour rapprocher les ingrédients. En conséquence, les
  clés de DEFAULT_CATEGORY_MAP (dans categorization.py) sont elles aussi repliées.

Règle des PLAGES (« 2-3 », « 2 à 3 ») : on GARDE LA BORNE HAUTE. Rationale :
mieux vaut acheter un peu trop qu'être à court pour une liste d'épicerie.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass
class ParsedIngredient:
    texte_brut: str
    quantite: float | None
    unite: str | None          # forme canonique, ex: "tasse", "c. à soupe", "g", "gousse", ou None
    nom_normalise: str         # nom de base normalisé (minuscule, sans accent, singulier, sans qualificatif)
    note: str | None           # qualificatifs de préparation: "haché", "frais", "en dés"...


# --------------------------------------------------------------------------- #
# Outils de bas niveau : nettoyage et repli (fold)
# --------------------------------------------------------------------------- #

def _fold(s: str) -> str:
    """Minuscules + suppression des accents (é→e, œ→oe, æ→ae, ç→c…).

    Sert à la fois au matching des unités/qualificatifs et à produire le
    nom_normalise final. Le repli est stable et déterministe.
    """
    s = s.lower().replace("œ", "oe").replace("æ", "ae")
    # Décompose puis retire les diacritiques (catégorie Unicode "Mn" = accent).
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def _clean(raw: str) -> str:
    """Nettoie l'entrée : apostrophes typographiques, espaces insécables, espaces multiples."""
    if raw is None:
        return ""
    s = str(raw)
    s = s.replace("’", "'").replace("ʼ", "'")   # ’ ʼ -> '
    s = s.replace(" ", " ").replace(" ", " ")   # espaces insécables -> espace
    s = re.sub(r"\s+", " ", s).strip()
    return s


# --------------------------------------------------------------------------- #
# Quantités : entiers, décimaux, fractions ASCII/Unicode, mixtes, plages
# --------------------------------------------------------------------------- #

# Fractions unicode courantes -> valeur flottante.
_UNICODE_FRACTIONS: dict[str, float] = {
    "½": 0.5, "¼": 0.25, "¾": 0.75,
    "⅓": 1 / 3, "⅔": 2 / 3,
    "⅛": 0.125, "⅜": 0.375, "⅝": 0.625, "⅞": 0.875,
    "⅕": 0.2, "⅖": 0.4, "⅗": 0.6, "⅘": 0.8,
    "⅙": 1 / 6, "⅚": 5 / 6,
    "⅐": 1 / 7, "⅑": 1 / 9, "⅒": 0.1,
}
_UNI = "".join(_UNICODE_FRACTIONS.keys())

_NUM = r"\d+(?:[.,]\d+)?"   # entier ou décimal (virgule ou point)

# NB : l'ordre des tentatives compte (voir _parse_leading_quantity).
_RANGE_RE = re.compile(rf"^({_NUM})\s*(?:-|–|—|a|à)\s*({_NUM})(?![\d.,])")
_MIXED_ASCII_RE = re.compile(r"^(\d+)\s+(\d+\s*/\s*\d+)")            # "1 1/2"
_MIXED_UNI_RE = re.compile(rf"^(\d+)\s*([{_UNI}])")                 # "1 ½" / "1½"
_ASCII_FRAC_RE = re.compile(r"^(\d+\s*/\s*\d+)")                    # "3/4"
_UNI_FRAC_RE = re.compile(rf"^([{_UNI}])")                          # "½"
_DECIMAL_RE = re.compile(rf"^({_NUM})")                             # décimal ou entier


def _num_to_float(tok: str) -> float:
    """Convertit un jeton numérique simple (entier/décimal/fraction) en float."""
    tok = tok.strip()
    if tok in _UNICODE_FRACTIONS:
        return _UNICODE_FRACTIONS[tok]
    if "/" in tok:
        num, den = tok.split("/", 1)
        den_f = float(den.strip())
        return float(num.strip()) / den_f if den_f else 0.0
    return float(tok.replace(",", "."))


def _parse_leading_quantity(s: str) -> tuple[float | None, str]:
    """Consomme l'expression de quantité en tête de `s`.

    Renvoie (valeur|None, reste). Ordre des cas (du plus spécifique au plus
    général) pour éviter les faux positifs :
      1. plage « 2-3 » / « 2 à 3 »  -> BORNE HAUTE
      2. nombre mixte ASCII « 1 1/2 »
      3. nombre mixte unicode « 1 ½ » / « 1½ »
      4. fraction ASCII « 3/4 »
      5. fraction unicode « ½ »
      6. décimal / entier « 1,5 » / « 250 »
    """
    s = s.lstrip()

    m = _RANGE_RE.match(s)
    if m:
        # On garde volontairement la borne haute (voir docstring module).
        return _num_to_float(m.group(2)), s[m.end():].lstrip()

    m = _MIXED_ASCII_RE.match(s)
    if m:
        return float(m.group(1)) + _num_to_float(m.group(2)), s[m.end():].lstrip()

    m = _MIXED_UNI_RE.match(s)
    if m:
        return float(m.group(1)) + _UNICODE_FRACTIONS[m.group(2)], s[m.end():].lstrip()

    m = _ASCII_FRAC_RE.match(s)
    if m:
        return _num_to_float(m.group(1)), s[m.end():].lstrip()

    m = _UNI_FRAC_RE.match(s)
    if m:
        return _UNICODE_FRACTIONS[m.group(1)], s[m.end():].lstrip()

    m = _DECIMAL_RE.match(s)
    if m:
        return _num_to_float(m.group(1)), s[m.end():].lstrip()

    return None, s


# --------------------------------------------------------------------------- #
# Unités : variantes/abréviations -> forme canonique
# --------------------------------------------------------------------------- #
#
# Formes canoniques choisies (stables) :
#   tasse | c. à soupe | c. à thé | ml | l | g | kg | mg | oz | lb |
#   gousse | tranche | pincée | botte | branche | boîte | conserve |
#   sachet | paquet | tête | feuille | brin
#
# Les VARIANTES ci-dessous sont écrites en forme REPLIÉE (minuscule, sans accent)
# car le matching se fait sur la chaîne repliée.
_UNIT_VARIANTS: dict[str, list[str]] = {
    "tasse": ["tasses", "tasse"],
    "c. à soupe": [
        "cuilleres a soupe", "cuillere a soupe", "cuil. a soupe", "cuil a soupe",
        "c. a soupe", "c.a soupe", "c a soupe",
        "c. a s.", "c. a s", "c.a.s.", "c.a.s", "c a s", "cas",
    ],
    "c. à thé": [
        "cuilleres a the", "cuillere a the", "cuilleres a cafe", "cuillere a cafe",
        "cuil. a the", "cuil a the", "cuil. a cafe", "cuil a cafe",
        "c. a the", "c.a the", "c a the", "c. a cafe", "c a cafe",
        "c. a c.", "c. a c", "c.a.c.", "c.a.c", "c a c", "cac",
    ],
    "ml": ["millilitres", "millilitre", "ml"],
    "l": ["litres", "litre", "l"],
    "g": ["grammes", "gramme", "gr", "g"],
    "kg": ["kilogrammes", "kilogramme", "kilos", "kilo", "kg"],
    "mg": ["milligrammes", "milligramme", "mg"],
    "oz": ["onces", "once", "oz"],
    "lb": ["livres", "livre", "lbs", "lb"],
    "gousse": ["gousses", "gousse"],
    "tranche": ["tranches", "tranche"],
    "pincée": ["pincees", "pincee"],
    "botte": ["bottes", "botte"],
    "branche": ["branches", "branche"],
    "boîte": ["boites", "boite"],
    "conserve": ["conserves", "conserve"],
    "sachet": ["sachets", "sachet"],
    "paquet": ["paquets", "paquet"],
    "tête": ["tetes", "tete"],
    "feuille": ["feuilles", "feuille"],
    "brin": ["brins", "brin"],
}

# Table plate (variante_repliée, canonique) triée par longueur décroissante :
# les formes longues/multi-mots sont testées AVANT les abréviations courtes
# (« cuillere a soupe » avant « c », « grammes » avant « g »).
_UNIT_TABLE: list[tuple[str, str]] = sorted(
    ((v, canon) for canon, variants in _UNIT_VARIANTS.items() for v in variants),
    key=lambda pair: len(pair[0]),
    reverse=True,
)


def _match_unit(frest: str) -> tuple[str | None, str]:
    """Détecte une unité en tête de la chaîne repliée `frest`.

    Une variante ne matche que si elle est suivie d'une frontière (fin de chaîne
    ou caractère non alphabétique) : ainsi « l » ne mange pas « laitue » et « g »
    ne mange pas « gousse ».
    """
    frest = frest.lstrip()
    for variant, canon in _UNIT_TABLE:
        if frest.startswith(variant):
            end = len(variant)
            if end == len(frest) or not frest[end].isalpha():
                return canon, frest[end:].lstrip()
    return None, frest


# --------------------------------------------------------------------------- #
# Liants et articles de tête
# --------------------------------------------------------------------------- #

# Liant entre unité et nom : « de / d' / des / du ».
_LIANT_RE = re.compile(r"^(?:d'|de |des |du |d )")

# Article de tête à retirer du nom : le/la/les/l'/un/une/de/d'/des/du + quelques.
_ARTICLE_RE = re.compile(r"^(?:l'|d'|les |le |la |un |une |des |du |de |quelques |quelque )")


def _strip_liant(frest: str) -> str:
    """Retire un liant de tête (« de », « d' », « des », « du »)."""
    frest = frest.lstrip()
    m = _LIANT_RE.match(frest)
    return frest[m.end():].lstrip() if m else frest


def _strip_article_once(frest: str) -> str:
    """Retire UN article/liant de tête si présent."""
    frest = frest.lstrip()
    m = _ARTICLE_RE.match(frest)
    return frest[m.end():].lstrip() if m else frest


# --------------------------------------------------------------------------- #
# Qualificatifs de préparation : séparés du nom vers `note`
# --------------------------------------------------------------------------- #
#
# Chaque entrée : (regex sur chaîne repliée, forme canonique jolie de la note).
# Les phrases multi-mots sont placées AVANT les mots simples pour être retirées
# en premier. `\w*` capture les variantes de genre/nombre (haché/hachée/hachés…).
_QUALIFIERS: list[tuple[re.Pattern[str], str]] = [
    # --- phrases multi-mots ---
    (re.compile(r"\bau gout\b"), "au goût"),
    (re.compile(r"\ben des\b"), "en dés"),
    (re.compile(r"\ben cubes?\b"), "en cubes"),
    (re.compile(r"\ben rondelles?\b"), "en rondelles"),
    (re.compile(r"\ben morceaux\b"), "en morceaux"),
    (re.compile(r"\ben tranches?\b"), "en tranches"),
    (re.compile(r"\ben julienne\b"), "en julienne"),
    (re.compile(r"\ben poudre\b"), "en poudre"),
    (re.compile(r"\ben lamelles?\b"), "en lamelles"),
    # --- mots simples (préparations) ---
    (re.compile(r"\bhach\w*\b"), "haché"),
    (re.compile(r"\bemince\w*\b"), "émincé"),
    (re.compile(r"\brape\w*\b"), "râpé"),
    (re.compile(r"\btranche\w*\b"), "tranché"),
    (re.compile(r"\b(?:de)?coupe\w*\b"), "coupé"),
    (re.compile(r"\bpele\w*\b"), "pelé"),
    (re.compile(r"\bepluche\w*\b"), "épluché"),
    (re.compile(r"\begoutte\w*\b"), "égoutté"),
    (re.compile(r"\brince\w*\b"), "rincé"),
    (re.compile(r"\bcuit\w*\b"), "cuit"),
    (re.compile(r"\bcru(?:e|s|es)?\b"), "cru"),
    (re.compile(r"\bgrille\w*\b"), "grillé"),
    (re.compile(r"\bmoulu\w*\b"), "moulu"),
    (re.compile(r"\bconcasse\w*\b"), "concassé"),
    (re.compile(r"\bdenoyaute\w*\b"), "dénoyauté"),
    (re.compile(r"\bcisele\w*\b"), "ciselé"),
    # --- état / qualité ---
    (re.compile(r"\bfraiche?s?\b"), "frais"),
    (re.compile(r"\bfrais\b"), "frais"),
    (re.compile(r"\bmur(?:e|s|es)?\b"), "mûr"),
    (re.compile(r"\bbio\b"), "bio"),
    # --- adverbes / approximations ---
    (re.compile(r"\bfinement\b"), "finement"),
    (re.compile(r"\bgrossierement\b"), "grossièrement"),
    (re.compile(r"\benviron\b"), "environ"),
]

# Mots à NE PAS singulariser (invariables, ou déjà singuliers en -s/-x/-z).
_KEEP_AS_IS: set[str] = {
    "ananas", "anchois", "radis", "couscous", "jus", "brebis", "souris",
    "cassis", "panais", "mais", "pois", "noix", "choix", "croix", "os",
    "gras", "epais", "riz", "tapas", "houmous", "cresson", "maquereau",
}


def _singular(word: str) -> str:
    """Singularise raisonnablement un mot français (retire un « s »/« x » final).

    Prudent : n'agit pas sur les mots courts (<= 3 lettres) ni sur les
    invariables connus, et ne réduit jamais un mot sous 2 lettres.
    """
    if word in _KEEP_AS_IS or len(word) <= 3:
        return word
    if word[-1] in ("s", "x") and len(word) > 4:
        return word[:-1]
    return word


def _normalize_name(frest: str) -> tuple[str, list[str]]:
    """Produit (nom_normalise, notes) à partir de la chaîne repliée restante.

    Étapes : retire les parenthèses, la ponctuation, l'article de tête, extrait
    les qualificatifs vers `notes`, retire les liants résiduels, puis singularise
    chaque mot du nom de base.
    """
    name = frest.strip()
    name = re.sub(r"\([^)]*\)", " ", name)        # « haché(e) » -> « haché »
    name = re.sub(r"[.,;:!?\"]", " ", name)       # ponctuation -> espace
    name = re.sub(r"\s+", " ", name).strip()
    name = _strip_article_once(name)

    notes: list[str] = []
    for pattern, canon in _QUALIFIERS:
        if pattern.search(name):
            if canon not in notes:
                notes.append(canon)
            name = pattern.sub(" ", name)
            name = re.sub(r"\s+", " ", name).strip()

    # Nettoyage des liants/articles résiduels laissés en tête après extraction.
    name = _strip_article_once(name)
    name = re.sub(r"^(?:de |d'|des |du |et |a )", "", name).strip()
    name = re.sub(r"\s+", " ", name).strip()

    # Garde-fou : si les qualificatifs ont tout mangé, le mot était en fait le
    # nom de l'ingrédient (ex. « mûres » = les fruits). On restaure et on oublie
    # la note trompeuse.
    if not name:
        restored = _strip_article_once(re.sub(r"[.,;:!?\"()]", " ", frest.strip()))
        restored = re.sub(r"\s+", " ", restored).strip()
        if restored:
            name = restored
            notes = []

    # Singularisation mot à mot (« pommes de terre » -> « pomme de terre »).
    words = [_singular(w) for w in name.split(" ") if w]
    name = " ".join(words)
    return name, notes


# --------------------------------------------------------------------------- #
# Fonction publique
# --------------------------------------------------------------------------- #

def parse_ingredient(raw: str) -> ParsedIngredient:
    """Parse une ligne d'ingrédient française en ParsedIngredient.

    Ne lève jamais d'exception : toute entrée vide/inattendue renvoie un
    ParsedIngredient exploitable (nom_normalise = texte replié nettoyé).
    """
    texte_brut = raw if isinstance(raw, str) else ("" if raw is None else str(raw))

    try:
        work = _clean(raw)
        if not work:
            return ParsedIngredient(texte_brut=texte_brut, quantite=None,
                                    unite=None, nom_normalise="", note=None)

        # 1) Quantité (avec accents conservés pour repérer « à » des plages).
        quantite, rest = _parse_leading_quantity(work)

        # 2) Repli pour toute la suite (unité, liant, nom, qualificatifs).
        frest = _fold(rest)

        # 3) Retire un éventuel article de tête (utile quand pas de quantité :
        #    « une pincée de sel », « la tomate »…).
        frest = _strip_article_once(frest)

        # 4) Unité canonique.
        unite, frest = _match_unit(frest)

        # 5) Liant « de / d' » entre unité et nom.
        frest = _strip_liant(frest)

        # 6) Nom normalisé + notes de préparation.
        nom_normalise, notes = _normalize_name(frest)

        # Garde-fou global : jamais de nom vide si l'entrée avait du contenu.
        if not nom_normalise and not notes:
            nom_normalise = re.sub(r"\s+", " ", _fold(work)).strip()

        note = ", ".join(notes) if notes else None
        return ParsedIngredient(
            texte_brut=texte_brut,
            quantite=quantite,
            unite=unite,
            nom_normalise=nom_normalise,
            note=note,
        )
    except Exception:
        # Robustesse absolue : on ne casse jamais l'import d'une recette.
        return ParsedIngredient(
            texte_brut=texte_brut,
            quantite=None,
            unite=None,
            nom_normalise=_fold(_clean(texte_brut)),
            note=None,
        )
