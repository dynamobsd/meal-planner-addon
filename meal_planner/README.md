# 🍽️ Planif Repas & Épicerie — Add-on Home Assistant

Application **maison** pour Home Assistant qui gère la **planification de repas de la semaine** et génère une **liste d'épicerie intelligente** (agrégation des quantités, regroupement par rayon, garde-manger). **Mobile-first** : pensée pour être utilisée au téléphone, à l'épicerie, via l'app compagnon Home Assistant.

> Add-on Docker exposé via **ingress** dans la barre latérale de HA. Backend **FastAPI + SQLite**, frontend **React/Vite/TypeScript**.

---

## État d'avancement

| Phase | Contenu | État |
|------|---------|------|
| **1 — Fondations** | Structure add-on, backend FastAPI, schéma SQLite, CRUD recettes, frontend minimal | ✅ |
| **2 — Import** | Scraping URL (recipe-scrapers → fallback JSON-LD → échec propre), parseur d'ingrédients FR, auto-catégorisation avec mémoire apprenante | ✅ |
| **3 — Planning** | Calendrier hebdo, drag & drop + alternative tactile, portions | ⏳ |
| **4 — Liste d'épicerie** | Agrégation + conversion d'unités + garde-manger + regroupement par rayon (+ tests) | ⏳ |
| **5 — Finitions** | Notes/étoiles, réglages des rayons, PWA hors ligne, polish UI, thème | ⏳ |

---

## Architecture

```
meal-planner-addon/
├── config.yaml          # métadonnées add-on HA (ingress: true, port 8099)
├── Dockerfile           # build frontend (node) + backend (python) en 2 étapes
├── run.sh               # démarre uvicorn
├── backend/             # FastAPI + logique métier
│   ├── main.py          # app, routeurs, service statique SPA, injection <base> ingress
│   ├── models.py        # ORM SQLAlchemy 2.0 (7 tables)
│   ├── schemas.py       # contrats Pydantic v2
│   ├── database.py      # moteur SQLite (WAL + FK)
│   ├── seed.py          # rayons par défaut
│   ├── routers/         # recipes, import_, categories
│   ├── services/        # scraper, ingredient_parser (FR), categorization
│   └── tests/           # tests parseur + smoke API
└── frontend/            # SPA React/Vite/TS (buildée dans dist/, servie par FastAPI)
```

**Stack** : FastAPI `0.116` · SQLAlchemy `2.0` · Pydantic `2.10` · recipe-scrapers `15.11` · React `18` + Vite · TypeScript.

---

## Fonctionnalités livrées (Phases 1–2)

- **Import par lien** : `POST /api/recipes/scrape` renvoie un brouillon éditable (non sauvegardé), déjà parsé et catégorisé. Cascade `recipe-scrapers` → **JSON-LD `schema.org/Recipe`** (gère `@graph`, `@type` liste, `HowToStep`/`HowToSection`, durées ISO 8601) → échec propre **HTTP 422** (jamais de 500).
- **Parseur d'ingrédients FR maison** : fractions (`1/2`, `½`, `1 ½`), plages (`2 à 3` → borne haute), unités FR + abréviations normalisées, liant `de`/`d'`, sans-unité, et **séparation des qualificatifs de préparation** (`haché`, `frais`…) pour que `tomate hachée` = `2 tomates` = même `nom_normalise`. **42 tests unitaires.**
- **Auto-catégorisation apprenante** : `nom_normalise` → rayon via mémoire (`ingredient_category_map`) → dictionnaire par défaut (**260 ingrédients**) → « Autre ». Corriger un rayon dans l'UI met à jour la mémoire (`PUT /api/categories/learn`).
- **CRUD recettes** + notes personnelles + note en étoiles.
- **Frontend mobile-first** : bottom-nav, formulaire d'import unifié (scrape/manuel/édition), thème clair/sombre calé sur les variables Home Assistant, cibles tactiles ≥ 44 px.

---

## Développement local

### Backend
```bash
python -m venv .venv
.venv/Scripts/pip install -r backend/requirements.txt   # (Linux/Mac : .venv/bin/pip)
.venv/Scripts/python -m uvicorn backend.main:app --reload --port 8099
# API docs : http://localhost:8099/api/docs
```

### Frontend
```bash
cd frontend
npm install
npm run build      # produit frontend/dist, servi par le backend
# ou  npm run dev   pour le hot-reload Vite
```

### Tests
```bash
.venv/Scripts/python -m pytest backend/tests/test_ingredient_parser.py -q   # 42 tests parseur
.venv/Scripts/python -m backend.tests.api_smoke                              # intégration API (scrape live inclus)
```

---

## Installation comme add-on Home Assistant

1. **Paramètres → Modules complémentaires → Boutique → ⋮ → Dépôts** : ajoute l'URL de ce dépôt Git.
2. Installe **« Planif Repas & Épicerie »**, puis démarre-le.
3. Active **« Afficher dans la barre latérale »** — l'app apparaît via ingress (aucun port à exposer, aucune auth séparée : HA authentifie déjà l'utilisateur).
4. Les données (SQLite) persistent dans le volume `/data` de l'add-on entre redémarrages et mises à jour.

---

## Notes techniques

- **Ingress** : le backend n'écoute que sur le port interne `8099` ; `main.py` lit le header `X-Ingress-Path` et injecte `<base href>` pour que les chemins relatifs du frontend résolvent derrière le proxy HA.
- **Hors ligne** : tout tourne localement sauf le scraping (nécessite Internet). Le comportement PWA (cache de la dernière liste) arrive en Phase 5.

🤖 Généré avec l'aide de [Claude Code](https://claude.com/claude-code)
