# 🍽️ Dépôt d'add-ons — Planif Repas & Épicerie

Dépôt d'add-ons **Home Assistant** contenant l'add-on **Planif Repas & Épicerie** :
planification de repas hebdomadaire + liste d'épicerie intelligente (scraping de
recettes, agrégation par rayon, garde-manger, alerte aubaines par IA). **Mobile-first.**

## Installation dans Home Assistant

> Requiert **Home Assistant OS** ou **Supervised** (les add-ons ne sont pas
> disponibles sur HA Container/Core). Ce n'est **pas** un dépôt HACS.

1. **Paramètres → Modules complémentaires → Boutique**
2. Menu **⋮** (haut droite) → **Dépôts**
3. Ajoute l'URL de ce dépôt :
   `https://github.com/dynamobsd/meal-planner-addon`
4. L'add-on **« Planif Repas & Épicerie »** apparaît dans la liste → **Installer** → **Démarrer**
5. Active **« Afficher dans la barre latérale »** (accès via ingress, sans port exposé)

## Contenu

| Chemin | Description |
|--------|-------------|
| `repository.yaml` | Métadonnées du dépôt d'add-ons |
| [`meal_planner/`](./meal_planner/) | L'add-on lui-même (voir son [README](./meal_planner/README.md)) |

## Développement

Voir [`meal_planner/README.md`](./meal_planner/README.md) pour lancer le backend
(FastAPI) et le frontend (React/Vite) en local, et pour les tests.

🤖 Généré avec l'aide de [Claude Code](https://claude.com/claude-code)
