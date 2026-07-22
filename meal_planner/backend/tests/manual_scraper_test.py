"""Test manuel (réseau) du service de scraping.

Usage :
    python backend/tests/manual_scraper_test.py

Nécessite httpx, recipe-scrapers, beautifulsoup4, lxml installés et un accès réseau.
Ce n'est PAS un test pytest automatisé (il fait de vrais appels HTTP).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Permet d'exécuter le script directement (import du package `backend`).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.services.scraper import (  # noqa: E402
    FetchError,
    ScrapeException,
    UnsupportedSiteError,
    scrape_recipe,
)


def _essai(url: str) -> None:
    print(f"\n=== {url} ===")
    try:
        data = scrape_recipe(url)
    except UnsupportedSiteError as exc:
        print(f"[UnsupportedSiteError] code={exc.code} -> {exc}")
        return
    except FetchError as exc:
        print(f"[FetchError] code={exc.code} -> {exc}")
        return
    except ScrapeException as exc:
        print(f"[ScrapeException] code={exc.code} -> {exc}")
        return

    print(f"source        : {data.source}")
    print(f"titre         : {data.titre}")
    print(f"host          : {data.host}")
    print(f"image_url      : {data.image_url}")
    print(f"portions      : {data.portions}")
    print(f"temps_prep    : {data.temps_prep} min")
    print(f"temps_cuisson : {data.temps_cuisson} min")
    print(f"ingredients   : {len(data.raw_ingredients)} ligne(s)")
    for ing in data.raw_ingredients[:5]:
        print(f"   - {ing}")
    instr = (data.instructions or "")[:200].replace("\n", " | ")
    print(f"instructions  : {instr}...")


if __name__ == "__main__":
    urls = sys.argv[1:] or [
        # Vraie recette FR (site supporté par recipe-scrapers).
        "https://www.ricardocuisine.com/recettes/8963-pate-a-crepes-de-base",
        # URL bidon -> doit produire un échec propre (FetchError attendu).
        "https://example.invalid/pas-une-recette-du-tout",
    ]
    for u in urls:
        _essai(u)
