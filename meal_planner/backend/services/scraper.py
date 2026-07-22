"""Service de scraping de recettes par URL.

Stratégie en cascade :
  1. recipe-scrapers (v15.x) sur le HTML téléchargé nous-mêmes.
  2. Fallback maison : parsing des blocs JSON-LD (schema.org/Recipe).
  3. Échec typé (UnsupportedSiteError / FetchError) — jamais d'exception brute.

Ce module respecte le contrat importé par routers/import_.py :
  ScrapeException, UnsupportedSiteError, FetchError, ScrapedRecipeData, scrape_recipe.
"""
from __future__ import annotations

import html as html_module
import json
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx

# --------------------------------------------------------------------------- #
# Exceptions typées
# --------------------------------------------------------------------------- #


class ScrapeException(Exception):
    """Erreur de base du scraping. `code` alimente ScrapeError.error_code."""

    code: str = "fetch_failed"


class UnsupportedSiteError(ScrapeException):
    """Le site n'est ni supporté par recipe-scrapers ni exploitable en JSON-LD."""

    code = "unsupported_site"


class FetchError(ScrapeException):
    """Le téléchargement HTTP lui-même a échoué (timeout, DNS, 4xx/5xx...)."""

    code = "fetch_failed"


# --------------------------------------------------------------------------- #
# Structure de données renvoyée
# --------------------------------------------------------------------------- #


@dataclass
class ScrapedRecipeData:
    titre: str
    url_source: str
    host: str | None
    image_url: str | None
    portions: int | None
    temps_prep: int | None        # minutes
    temps_cuisson: int | None     # minutes
    instructions: str | None
    raw_ingredients: list[str]    # lignes BRUTES, non parsées
    source: str                   # "recipe-scrapers" | "json-ld"


# --------------------------------------------------------------------------- #
# Constantes
# --------------------------------------------------------------------------- #

# User-Agent réaliste : certains sites refusent les clients « robots ».
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
_HTTP_HEADERS = {
    "User-Agent": _USER_AGENT,
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}
_TIMEOUT = 15.0

# Balises HTML résiduelles à retirer lors du nettoyage des textes.
_TAG_RE = re.compile(r"<[^>]+>")


# --------------------------------------------------------------------------- #
# Utilitaires de nettoyage
# --------------------------------------------------------------------------- #


def _clean_text(value) -> str | None:
    """Retire les balises HTML résiduelles + décode les entités (&amp; -> &)."""
    if value is None:
        return None
    text = str(value)
    # Retire d'éventuelles balises HTML restées dans le texte.
    text = _TAG_RE.sub(" ", text)
    # Décode les entités HTML (&amp;, &#39;, &eacute;, ...).
    text = html_module.unescape(text)
    # Normalise les espaces internes puis rogne les bords.
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = text.strip()
    return text or None


def _host_from_url(url: str) -> str | None:
    """Extrait le domaine (netloc) de l'URL, sans le préfixe www."""
    try:
        netloc = urlparse(url).netloc
    except (ValueError, TypeError):
        return None
    if not netloc:
        return None
    # Retire un éventuel port et le préfixe www.
    netloc = netloc.split("@")[-1].split(":")[0]
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc or None


def _parse_int_from_text(value) -> int | None:
    """Extrait le premier entier d'une valeur (« 4 portions » -> 4, 4.0 -> 4)."""
    if value is None:
        return None
    if isinstance(value, bool):  # bool est une sous-classe d'int : on l'exclut.
        return None
    if isinstance(value, (int, float)):
        try:
            return int(value)
        except (ValueError, OverflowError):
            return None
    if isinstance(value, (list, tuple)):
        # recipeYield peut être une liste : on prend le 1er élément exploitable.
        for item in value:
            parsed = _parse_int_from_text(item)
            if parsed is not None:
                return parsed
        return None
    match = re.search(r"\d+", str(value))
    if match:
        try:
            return int(match.group())
        except ValueError:
            return None
    return None


def _parse_iso8601_duration(value) -> int | None:
    """Convertit une durée ISO 8601 (« PT1H15M ») en minutes entières.

    Gère les jours/heures/minutes/secondes. Renvoie None si non parsable.
    """
    if value is None:
        return None
    # Déjà un nombre : on suppose des minutes.
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    text = str(value).strip()
    if not text:
        return None
    # Format : P[nD]T[nH][nM][nS] — on ignore semaines/mois/années (rares ici).
    match = re.match(
        r"^P(?:(?P<days>\d+)D)?"
        r"(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+(?:\.\d+)?)S)?)?$",
        text,
        re.IGNORECASE,
    )
    if not match or not any(match.groupdict().values()):
        # Repli : peut-être juste un nombre de minutes en texte (« 30 min »).
        return _parse_int_from_text(text)
    days = int(match.group("days") or 0)
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = float(match.group("seconds") or 0)
    total = days * 24 * 60 + hours * 60 + minutes + int(round(seconds / 60.0))
    return total or None


# --------------------------------------------------------------------------- #
# Téléchargement HTTP
# --------------------------------------------------------------------------- #


def _fetch_html(url: str) -> str:
    """Télécharge le HTML de l'URL. Lève FetchError sur toute erreur réseau/HTTP."""
    try:
        response = httpx.get(
            url,
            headers=_HTTP_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise FetchError(
            f"Le site a répondu avec le code {exc.response.status_code}."
        ) from exc
    except httpx.HTTPError as exc:
        # Timeout, DNS, connexion refusée, URL invalide, etc.
        raise FetchError("Impossible de contacter le site.") from exc
    return response.text


# --------------------------------------------------------------------------- #
# Étape 1 — recipe-scrapers
# --------------------------------------------------------------------------- #


def _scrape_with_recipe_scrapers(html: str, url: str) -> ScrapedRecipeData | None:
    """Tente l'extraction via recipe-scrapers. Renvoie None si le site est inconnu.

    Chaque champ est protégé individuellement : recipe-scrapers lève une
    exception par champ absent (ElementNotFoundInHtml, NotImplementedError...).
    """
    try:
        from recipe_scrapers import scrape_html
    except ImportError:
        return None

    try:
        # wild_mode=True : tente une extraction générique même hors sites connus.
        scraper = scrape_html(html, org_url=url, wild_mode=True)
    except Exception:
        # Site inconnu / aucun schéma exploitable -> on tentera le JSON-LD.
        return None

    # --- Titre --- (obligatoire : sans titre, on considère l'extraction ratée)
    try:
        titre = _clean_text(scraper.title())
    except Exception:
        titre = None
    if not titre:
        return None

    # --- Image ---
    try:
        image_url = scraper.image() or None
    except Exception:
        image_url = None

    # --- Portions --- (« 4 portions » -> 4)
    try:
        portions = _parse_int_from_text(scraper.yields())
    except Exception:
        portions = None

    # --- Temps de préparation (minutes) ---
    try:
        temps_prep = scraper.prep_time()
        temps_prep = int(temps_prep) if temps_prep else None
    except Exception:
        temps_prep = None

    # --- Temps de cuisson (minutes) ---
    try:
        temps_cuisson = scraper.cook_time()
        temps_cuisson = int(temps_cuisson) if temps_cuisson else None
    except Exception:
        temps_cuisson = None

    # --- Instructions ---
    try:
        instructions = _clean_text(scraper.instructions())
    except Exception:
        instructions = None

    # --- Ingrédients (lignes brutes) ---
    try:
        raw = scraper.ingredients() or []
        raw_ingredients = [
            cleaned for item in raw if (cleaned := _clean_text(item))
        ]
    except Exception:
        raw_ingredients = []

    # Sans ingrédients ET sans instructions, l'extraction n'apporte rien :
    # on laisse le fallback JSON-LD tenter sa chance.
    if not raw_ingredients and not instructions:
        return None

    return ScrapedRecipeData(
        titre=titre,
        url_source=url,
        host=_host_from_url(url),
        image_url=image_url,
        portions=portions,
        temps_prep=temps_prep,
        temps_cuisson=temps_cuisson,
        instructions=instructions,
        raw_ingredients=raw_ingredients,
        source="recipe-scrapers",
    )


# --------------------------------------------------------------------------- #
# Étape 2 — Fallback JSON-LD (schema.org/Recipe)
# --------------------------------------------------------------------------- #


def _type_matches_recipe(type_value) -> bool:
    """@type peut être une string OU une liste ; True si « Recipe » y figure."""
    if isinstance(type_value, str):
        return type_value.strip().lower() == "recipe"
    if isinstance(type_value, (list, tuple)):
        return any(
            isinstance(t, str) and t.strip().lower() == "recipe"
            for t in type_value
        )
    return False


def _iter_json_ld_nodes(data):
    """Aplati un bloc JSON-LD en une suite de dictionnaires candidats.

    Gère : objet unique, liste au top-level, et conteneur avec @graph (liste).
    """
    if isinstance(data, list):
        for item in data:
            yield from _iter_json_ld_nodes(item)
    elif isinstance(data, dict):
        yield data
        graph = data.get("@graph")
        if isinstance(graph, (list, dict)):
            yield from _iter_json_ld_nodes(graph)


def _find_recipe_node(html: str) -> dict | None:
    """Cherche une entité Recipe dans tous les <script type=application/ld+json>."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return None

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        # lxml absent ou HTML illisible -> repli sur le parseur intégré.
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            return None

    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text() or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Certains sites concatènent plusieurs objets ou ajoutent des
            # virgules parasites : on tente une réparation minimale.
            data = _loads_lenient(raw)
            if data is None:
                continue
        for node in _iter_json_ld_nodes(data):
            if _type_matches_recipe(node.get("@type")):
                return node
    return None


def _loads_lenient(raw: str):
    """Tente de charger un JSON-LD légèrement malformé (objets concaténés)."""
    try:
        # Cas fréquent : plusieurs objets séparés par des retours ligne.
        decoder = json.JSONDecoder()
        idx = 0
        results = []
        length = len(raw)
        while idx < length:
            while idx < length and raw[idx] in " \t\r\n":
                idx += 1
            if idx >= length:
                break
            obj, end = decoder.raw_decode(raw, idx)
            results.append(obj)
            idx = end
        if not results:
            return None
        return results if len(results) > 1 else results[0]
    except (json.JSONDecodeError, ValueError):
        return None


def _extract_image_from_json_ld(value) -> str | None:
    """image JSON-LD : string, objet {url}, ou liste -> renvoie la 1re URL."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, dict):
        url = value.get("url") or value.get("@id")
        return _extract_image_from_json_ld(url)
    if isinstance(value, (list, tuple)):
        for item in value:
            url = _extract_image_from_json_ld(item)
            if url:
                return url
    return None


def _flatten_instructions(value) -> str | None:
    """Aplati recipeInstructions en une string (une étape par ligne).

    Gère : string ; liste de strings ; liste de HowToStep {text} ;
    HowToSection avec itemListElement (récursif).
    """
    steps: list[str] = []

    def _collect(node) -> None:
        if node is None:
            return
        if isinstance(node, str):
            cleaned = _clean_text(node)
            if cleaned:
                steps.append(cleaned)
            return
        if isinstance(node, (list, tuple)):
            for item in node:
                _collect(item)
            return
        if isinstance(node, dict):
            node_type = node.get("@type")
            is_section = (
                isinstance(node_type, str)
                and "section" in node_type.lower()
            ) or "itemListElement" in node
            if is_section and node.get("itemListElement") is not None:
                # HowToSection : on aplati ses sous-étapes.
                _collect(node.get("itemListElement"))
                return
            # HowToStep (ou objet équivalent) : on prend text, sinon name.
            text = node.get("text") or node.get("name")
            cleaned = _clean_text(text)
            if cleaned:
                steps.append(cleaned)
            return

    _collect(value)
    if not steps:
        return None
    return "\n".join(steps)


def _extract_ingredients_from_json_ld(value) -> list[str]:
    """recipeIngredient -> liste de lignes brutes nettoyées."""
    result: list[str] = []
    if value is None:
        return result
    if isinstance(value, str):
        cleaned = _clean_text(value)
        return [cleaned] if cleaned else []
    if isinstance(value, (list, tuple)):
        for item in value:
            cleaned = _clean_text(item if isinstance(item, str) else
                                  (item.get("text") if isinstance(item, dict) else item))
            if cleaned:
                result.append(cleaned)
    return result


def _scrape_with_json_ld(html: str, url: str) -> ScrapedRecipeData | None:
    """Extraction de secours à partir d'un bloc JSON-LD schema.org/Recipe."""
    node = _find_recipe_node(html)
    if node is None:
        return None

    titre = _clean_text(node.get("name"))
    if not titre:
        return None

    image_url = _extract_image_from_json_ld(node.get("image"))
    portions = _parse_int_from_text(node.get("recipeYield"))
    temps_prep = _parse_iso8601_duration(node.get("prepTime"))
    temps_cuisson = _parse_iso8601_duration(node.get("cookTime"))
    raw_ingredients = _extract_ingredients_from_json_ld(
        node.get("recipeIngredient") or node.get("ingredients")
    )
    instructions = _flatten_instructions(node.get("recipeInstructions"))

    # Un « Recipe » sans le moindre ingrédient ni instruction n'est pas exploitable.
    if not raw_ingredients and not instructions:
        return None

    return ScrapedRecipeData(
        titre=titre,
        url_source=url,
        host=_host_from_url(url),
        image_url=image_url,
        portions=portions,
        temps_prep=temps_prep,
        temps_cuisson=temps_cuisson,
        instructions=instructions,
        raw_ingredients=raw_ingredients,
        source="json-ld",
    )


# --------------------------------------------------------------------------- #
# Point d'entrée public
# --------------------------------------------------------------------------- #


def scrape_recipe(url: str) -> ScrapedRecipeData:
    """Scrape une recette depuis une URL, en cascade.

    Ordre : recipe-scrapers -> JSON-LD -> échec typé.
    Ne laisse JAMAIS remonter d'exception non typée (ScrapeException uniquement).
    """
    # 0. Téléchargement (une seule fois, réutilisé par les deux étapes).
    #    Toute erreur réseau/HTTP devient un FetchError.
    html = _fetch_html(url)

    # 1. recipe-scrapers.
    try:
        data = _scrape_with_recipe_scrapers(html, url)
    except ScrapeException:
        raise
    except Exception:
        # Blindage : aucune exception interne ne doit fuiter.
        data = None
    if data is not None:
        return data

    # 2. Fallback JSON-LD.
    try:
        data = _scrape_with_json_ld(html, url)
    except ScrapeException:
        raise
    except Exception:
        data = None
    if data is not None:
        return data

    # 3. Échec propre : rien d'exploitable.
    raise UnsupportedSiteError(
        "Aucune recette exploitable trouvée sur cette page."
    )
