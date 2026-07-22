# Journal des versions

## 0.4.0

- **Planning automatique (IA)** : depuis le Planning, l'IA remplit la semaine en plaçant vos recettes sur les créneaux choisis (varié, selon vos goûts). Les créneaux sans recette adaptée sont signalés comme idées.
- **Recettes favorites** : marquez vos recettes d'un ❤ et filtrez sur les favoris.
- **Dupliquer une semaine** : recopiez le planning d'une semaine vers une autre en un geste.
- **Partager la liste d'épicerie** : export en texte, via le partage natif du téléphone ou le presse-papier.
- **Échelle des portions** : sur une recette, ajustez le nombre de portions et voyez les quantités recalculées.

## 0.3.0

- **Type de plat sur les recettes** : classe chaque recette (déjeuner, dessert, plat principal, entrée, accompagnement, soupe, salade, collation, boisson…). Recherche par texte et **filtre par type** dans la liste des recettes et dans le sélecteur du planning.
- **Suggestions de repas (IA)** : depuis le Planning, l'IA propose des idées de repas personnalisées selon vos goûts (« pour ma blonde »), en priorisant vos recettes déjà enregistrées et en suggérant des idées neuves sinon. Un simple bouton crée la recette d'une idée. Option `anthropic_api_key` (désactivé si vide).
- **Préférences de goûts persistées** : vos préférences sont mémorisées, pas besoin de les retaper.
- Migration transparente de la base existante (aucune perte de données).

## 0.2.6

- Corrections d'empaquetage Home Assistant : image de base `python:3.12-slim`, chargement des librairies et profil de sécurité ajustés pour un démarrage fiable de l'add-on.

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
