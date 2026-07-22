"""Auto-catégorisation des ingrédients vers un rayon d'épicerie (Phase 2).

Trois couches de résolution, dans l'ordre :
  1. Mémoire apprenante (table ingredient_category_map) — corrections faites par
     l'utilisateur, prioritaires.
  2. DEFAULT_CATEGORY_MAP — dictionnaire par défaut riche (~130 ingrédients).
  3. Rayon « Autre » — repli quand rien ne matche.

IMPORTANT :
  - `resolve_category` est en LECTURE SEULE (aucun write, aucun commit).
  - `learn_category` fait un upsert mais NE COMMIT PAS (le routeur commit).

Les CLÉS de DEFAULT_CATEGORY_MAP sont écrites sous forme REPLIÉE (minuscule, sans
accent, singulier), exactement comme le produit `ingredient_parser.parse_ingredient`
dans `nom_normalise`. Les VALEURS sont des noms de rayon qui correspondent
EXACTEMENT à `DEFAULT_CATEGORIES` dans `seed.py`.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Category, IngredientCategoryMap
from ..seed import get_category_id_by_name, get_fallback_category_id

# --------------------------------------------------------------------------- #
# Dictionnaire par défaut : nom_normalise (replié) -> NOM de rayon
# --------------------------------------------------------------------------- #
DEFAULT_CATEGORY_MAP: dict[str, str] = {
    # ------------------------------------------------------------------ #
    # Fruits & légumes
    # ------------------------------------------------------------------ #
    "tomate": "Fruits & légumes",
    "tomate cerise": "Fruits & légumes",
    "oignon": "Fruits & légumes",
    "oignon vert": "Fruits & légumes",
    "echalote": "Fruits & légumes",
    "ail": "Fruits & légumes",
    "carotte": "Fruits & légumes",
    "pomme de terre": "Fruits & légumes",
    "patate": "Fruits & légumes",
    "patate douce": "Fruits & légumes",
    "laitue": "Fruits & légumes",
    "roquette": "Fruits & légumes",
    "epinard": "Fruits & légumes",
    "kale": "Fruits & légumes",
    "chou": "Fruits & légumes",
    "chou-fleur": "Fruits & légumes",
    "chou de bruxelles": "Fruits & légumes",
    "brocoli": "Fruits & légumes",
    "poivron": "Fruits & légumes",
    "piment": "Fruits & légumes",
    "jalapeno": "Fruits & légumes",
    "courgette": "Fruits & légumes",
    "courge": "Fruits & légumes",
    "citrouille": "Fruits & légumes",
    "aubergine": "Fruits & légumes",
    "champignon": "Fruits & légumes",
    "concombre": "Fruits & légumes",
    "celeri": "Fruits & légumes",
    "fenouil": "Fruits & légumes",
    "poireau": "Fruits & légumes",
    "navet": "Fruits & légumes",
    "panais": "Fruits & légumes",
    "radis": "Fruits & légumes",
    "betterave": "Fruits & légumes",
    "asperge": "Fruits & légumes",
    "haricot vert": "Fruits & légumes",
    "petit pois": "Fruits & légumes",
    "mais": "Fruits & légumes",
    "gingembre": "Fruits & légumes",
    "persil": "Fruits & légumes",
    "coriandre": "Fruits & légumes",
    "ciboulette": "Fruits & légumes",
    "menthe": "Fruits & légumes",
    "endive": "Fruits & légumes",
    "cresson": "Fruits & légumes",
    "citron": "Fruits & légumes",
    "lime": "Fruits & légumes",
    "pomme": "Fruits & légumes",
    "poire": "Fruits & légumes",
    "banane": "Fruits & légumes",
    "orange": "Fruits & légumes",
    "clementine": "Fruits & légumes",
    "pamplemousse": "Fruits & légumes",
    "fraise": "Fruits & légumes",
    "framboise": "Fruits & légumes",
    "bleuet": "Fruits & légumes",
    "myrtille": "Fruits & légumes",
    "mure": "Fruits & légumes",
    "raisin": "Fruits & légumes",
    "peche": "Fruits & légumes",
    "prune": "Fruits & légumes",
    "abricot": "Fruits & légumes",
    "cerise": "Fruits & légumes",
    "mangue": "Fruits & légumes",
    "ananas": "Fruits & légumes",
    "kiwi": "Fruits & légumes",
    "melon": "Fruits & légumes",
    "pasteque": "Fruits & légumes",
    "cantaloup": "Fruits & légumes",
    "avocat": "Fruits & légumes",
    # ------------------------------------------------------------------ #
    # Boucherie & poissonnerie
    # ------------------------------------------------------------------ #
    "poulet": "Boucherie & poissonnerie",
    "boeuf": "Boucherie & poissonnerie",
    "porc": "Boucherie & poissonnerie",
    "veau": "Boucherie & poissonnerie",
    "agneau": "Boucherie & poissonnerie",
    "dinde": "Boucherie & poissonnerie",
    "canard": "Boucherie & poissonnerie",
    "poisson": "Boucherie & poissonnerie",
    "saumon": "Boucherie & poissonnerie",
    "thon": "Boucherie & poissonnerie",
    "morue": "Boucherie & poissonnerie",
    "tilapia": "Boucherie & poissonnerie",
    "truite": "Boucherie & poissonnerie",
    "aiglefin": "Boucherie & poissonnerie",
    "fletan": "Boucherie & poissonnerie",
    "sardine": "Boucherie & poissonnerie",
    "maquereau": "Boucherie & poissonnerie",
    "crevette": "Boucherie & poissonnerie",
    "homard": "Boucherie & poissonnerie",
    "petoncle": "Boucherie & poissonnerie",
    "moule": "Boucherie & poissonnerie",
    "palourde": "Boucherie & poissonnerie",
    "calmar": "Boucherie & poissonnerie",
    # ------------------------------------------------------------------ #
    # Charcuterie
    # ------------------------------------------------------------------ #
    "jambon": "Charcuterie",
    "bacon": "Charcuterie",
    "saucisse": "Charcuterie",
    "saucisson": "Charcuterie",
    "prosciutto": "Charcuterie",
    "salami": "Charcuterie",
    "pepperoni": "Charcuterie",
    "chorizo": "Charcuterie",
    "pancetta": "Charcuterie",
    "mortadelle": "Charcuterie",
    "pate": "Charcuterie",
    "creton": "Charcuterie",
    # ------------------------------------------------------------------ #
    # Produits laitiers & œufs
    # ------------------------------------------------------------------ #
    "lait": "Produits laitiers & œufs",
    "beurre": "Produits laitiers & œufs",
    "creme": "Produits laitiers & œufs",
    "creme sure": "Produits laitiers & œufs",
    "creme fraiche": "Produits laitiers & œufs",
    "yogourt": "Produits laitiers & œufs",
    "yaourt": "Produits laitiers & œufs",
    "oeuf": "Produits laitiers & œufs",
    "fromage": "Produits laitiers & œufs",
    "parmesan": "Produits laitiers & œufs",
    "mozzarella": "Produits laitiers & œufs",
    "cheddar": "Produits laitiers & œufs",
    "feta": "Produits laitiers & œufs",
    "ricotta": "Produits laitiers & œufs",
    "gouda": "Produits laitiers & œufs",
    "brie": "Produits laitiers & œufs",
    "gruyere": "Produits laitiers & œufs",
    "emmental": "Produits laitiers & œufs",
    "mascarpone": "Produits laitiers & œufs",
    "chevre": "Produits laitiers & œufs",
    "margarine": "Produits laitiers & œufs",
    # ------------------------------------------------------------------ #
    # Épicerie sèche (pâtes / riz / farine / légumineuses / sucre…)
    # ------------------------------------------------------------------ #
    "farine": "Épicerie sèche",
    "riz": "Épicerie sèche",
    "pates": "Épicerie sèche",
    "spaghetti": "Épicerie sèche",
    "macaroni": "Épicerie sèche",
    "nouille": "Épicerie sèche",
    "lasagne": "Épicerie sèche",
    "couscous": "Épicerie sèche",
    "semoule": "Épicerie sèche",
    "boulgour": "Épicerie sèche",
    "orge": "Épicerie sèche",
    "quinoa": "Épicerie sèche",
    "avoine": "Épicerie sèche",
    "gruau": "Épicerie sèche",
    "sucre": "Épicerie sèche",
    "cassonade": "Épicerie sèche",
    "lentille": "Épicerie sèche",
    "pois chiche": "Épicerie sèche",
    "haricot": "Épicerie sèche",
    "feve": "Épicerie sèche",
    "fecule": "Épicerie sèche",
    "levure": "Épicerie sèche",
    "bicarbonate": "Épicerie sèche",
    "poudre a pate": "Épicerie sèche",
    "chapelure": "Épicerie sèche",
    "cacao": "Épicerie sèche",
    "chocolat": "Épicerie sèche",
    "amande": "Épicerie sèche",
    "noix": "Épicerie sèche",
    "noisette": "Épicerie sèche",
    "arachide": "Épicerie sèche",
    "pistache": "Épicerie sèche",
    "graine": "Épicerie sèche",
    "sesame": "Épicerie sèche",
    "raisin sec": "Épicerie sèche",
    "datte": "Épicerie sèche",
    "pruneau": "Épicerie sèche",
    "bouillon": "Épicerie sèche",
    # ------------------------------------------------------------------ #
    # Condiments & sauces
    # ------------------------------------------------------------------ #
    "huile": "Condiments & sauces",
    "huile d'olive": "Condiments & sauces",
    "huile vegetale": "Condiments & sauces",
    "huile de canola": "Condiments & sauces",
    "huile de sesame": "Condiments & sauces",
    "vinaigre": "Condiments & sauces",
    "vinaigre balsamique": "Condiments & sauces",
    "moutarde": "Condiments & sauces",
    "ketchup": "Condiments & sauces",
    "mayonnaise": "Condiments & sauces",
    "sauce soya": "Condiments & sauces",
    "sauce tomate": "Condiments & sauces",
    "sauce worcestershire": "Condiments & sauces",
    "sauce piquante": "Condiments & sauces",
    "sauce bbq": "Condiments & sauces",
    "sauce hoisin": "Condiments & sauces",
    "sauce poisson": "Condiments & sauces",
    "pesto": "Condiments & sauces",
    "salsa": "Condiments & sauces",
    "tahini": "Condiments & sauces",
    "miel": "Condiments & sauces",
    "sirop d'erable": "Condiments & sauces",
    "confiture": "Condiments & sauces",
    "beurre d'arachide": "Condiments & sauces",
    "relish": "Condiments & sauces",
    "vinaigrette": "Condiments & sauces",
    "pate de tomate": "Condiments & sauces",
    # ------------------------------------------------------------------ #
    # Épices
    # ------------------------------------------------------------------ #
    "sel": "Épices",
    "poivre": "Épices",
    "cumin": "Épices",
    "paprika": "Épices",
    "cannelle": "Épices",
    "basilic": "Épices",
    "origan": "Épices",
    "thym": "Épices",
    "romarin": "Épices",
    "sauge": "Épices",
    "aneth": "Épices",
    "estragon": "Épices",
    "laurier": "Épices",
    "muscade": "Épices",
    "curcuma": "Épices",
    "cari": "Épices",
    "curry": "Épices",
    "chili": "Épices",
    "piment de cayenne": "Épices",
    "clou de girofle": "Épices",
    "cardamome": "Épices",
    "safran": "Épices",
    "anis": "Épices",
    "herbes de provence": "Épices",
    "poudre d'ail": "Épices",
    "poudre d'oignon": "Épices",
    # ------------------------------------------------------------------ #
    # Boulangerie
    # ------------------------------------------------------------------ #
    "pain": "Boulangerie",
    "baguette": "Boulangerie",
    "tortilla": "Boulangerie",
    "croissant": "Boulangerie",
    "bagel": "Boulangerie",
    "brioche": "Boulangerie",
    "pita": "Boulangerie",
    "naan": "Boulangerie",
    "ciabatta": "Boulangerie",
    "focaccia": "Boulangerie",
    # ------------------------------------------------------------------ #
    # Boissons
    # ------------------------------------------------------------------ #
    "eau": "Boissons",
    "jus": "Boissons",
    "jus d'orange": "Boissons",
    "cafe": "Boissons",
    "the": "Boissons",
    "vin": "Boissons",
    "vin rouge": "Boissons",
    "vin blanc": "Boissons",
    "biere": "Boissons",
    "limonade": "Boissons",
    "boisson de soya": "Boissons",
    "lait d'amande": "Boissons",
    # ------------------------------------------------------------------ #
    # Collations
    # ------------------------------------------------------------------ #
    "croustille": "Collations",
    "craquelin": "Collations",
    "biscuit": "Collations",
    "popcorn": "Collations",
    "bretzel": "Collations",
    "barre tendre": "Collations",
    # ------------------------------------------------------------------ #
    # Surgelés
    # ------------------------------------------------------------------ #
    "creme glacee": "Surgelés",
    "frite": "Surgelés",
    "pizza surgelee": "Surgelés",
    # ------------------------------------------------------------------ #
    # Conserves & bocaux
    # ------------------------------------------------------------------ #
    "olive": "Conserves & bocaux",
    "cornichon": "Conserves & bocaux",
    "coeur d'artichaut": "Conserves & bocaux",
    "lait de coco": "Conserves & bocaux",
    # ------------------------------------------------------------------ #
    # Ménage (non alimentaire)
    # ------------------------------------------------------------------ #
    "papier essuie-tout": "Ménage",
    "papier hygienique": "Ménage",
    "savon": "Ménage",
    "detergent": "Ménage",
    "sac poubelle": "Ménage",
    "eponge": "Ménage",
    "papier aluminium": "Ménage",
    "pellicule plastique": "Ménage",
}

# Longueur minimale d'une clé pour autoriser un match « contient » (tolérant).
# En dessous (« ail », « sel », « the », « riz »…) on exige un match EXACT afin
# d'éviter les faux positifs (« ail » dans « volaille », « the » dans « theatre »).
_MIN_CONTAINS_LEN = 4

# Clés triées par longueur décroissante : pour le match tolérant, on privilégie
# la clé la plus spécifique (« pomme de terre » avant « pomme »).
_KEYS_BY_LEN: list[str] = sorted(DEFAULT_CATEGORY_MAP.keys(), key=len, reverse=True)


def _default_map_lookup(nom: str) -> str | None:
    """Cherche un rayon dans DEFAULT_CATEGORY_MAP.

    1) match EXACT ; 2) match « contient » tolérant (clé incluse dans le nom, ou
    nom inclus dans la clé) pour les clés d'au moins _MIN_CONTAINS_LEN caractères.
    Renvoie le NOM de rayon ou None.
    """
    if not nom:
        return None
    # 1) Exact.
    exact = DEFAULT_CATEGORY_MAP.get(nom)
    if exact is not None:
        return exact
    # 2) Tolérant (« poivron rouge » -> « poivron », « oeufs bio » -> « oeuf »).
    for key in _KEYS_BY_LEN:
        if len(key) < _MIN_CONTAINS_LEN:
            continue
        if key in nom or nom in key:
            return DEFAULT_CATEGORY_MAP[key]
    return None


def resolve_category(db: Session, nom_normalise: str) -> int | None:
    """Résout l'id de rayon pour un `nom_normalise`. LECTURE SEULE.

    Ordre : (1) mémoire apprenante ; (2) DEFAULT_CATEGORY_MAP ; (3) rayon « Autre ».
    Ne fait AUCUN write / commit.
    """
    nom = (nom_normalise or "").strip()

    # 1) Mémoire apprenante (corrections utilisateur) — prioritaire.
    if nom:
        learned = db.scalar(
            select(IngredientCategoryMap).where(
                IngredientCategoryMap.nom_ingredient == nom
            )
        )
        if learned is not None:
            return learned.categorie_id

    # 2) Dictionnaire par défaut -> id via le nom de rayon.
    rayon = _default_map_lookup(nom)
    if rayon is not None:
        cat_id = get_category_id_by_name(db, rayon)
        if cat_id is not None:
            return cat_id

    # 3) Repli : rayon « Autre ».
    return get_fallback_category_id(db)


def learn_category(db: Session, nom_normalise: str, categorie_id: int) -> None:
    """Upsert (nom_normalise -> categorie_id) dans la mémoire apprenante.

    NE COMMIT PAS : le routeur appelant est responsable du commit.
    """
    nom = (nom_normalise or "").strip()
    if not nom:
        return

    existing = db.scalar(
        select(IngredientCategoryMap).where(
            IngredientCategoryMap.nom_ingredient == nom
        )
    )
    if existing is not None:
        existing.categorie_id = categorie_id
    else:
        db.add(
            IngredientCategoryMap(nom_ingredient=nom, categorie_id=categorie_id)
        )
    # Flush pour matérialiser l'INSERT/UPDATE sans clore la transaction.
    db.flush()
