# Journal des versions

## 0.2.0

Première version fonctionnelle complète (Phases 1 à 5 + Alerte aubaines).

- **Import de recettes** : import par lien avec scraping (`recipe-scrapers` → repli JSON-LD `schema.org/Recipe` → échec propre en HTTP 422), plus saisie et édition manuelles. Parseur d'ingrédients français (fractions, plages, unités et abréviations, qualificatifs de préparation).
- **Auto-catégorisation apprenante** : chaque ingrédient est rangé automatiquement dans un rayon ; les corrections manuelles sont mémorisées pour la suite.
- **Planning hebdomadaire** : calendrier de la semaine, ajout de repas par glisser-déposer (avec alternative tactile), réglage des portions.
- **Liste d'épicerie intelligente** : génération depuis le planning avec agrégation des quantités, conversion d'unités et regroupement par rayon.
- **Garde-manger** : les ingrédients déjà en stock sont déduits de la liste d'épicerie.
- **Gestion des rayons** : réorganisation et personnalisation des rayons du magasin.
- **PWA hors ligne** : consultation de la dernière liste d'épicerie sans connexion, à l'épicerie.
- **Alerte aubaines (IA)** : détection assistée par l'IA des bonnes affaires (option `anthropic_api_key`, désactivée si vide).
- **Interface mobile-first** : navigation par le bas, thème clair/sombre aligné sur Home Assistant, cibles tactiles confortables.
