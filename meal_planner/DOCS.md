# Planif Repas & Épicerie — Guide d'utilisation

Cet add-on vous aide à **planifier vos repas de la semaine** et à générer
automatiquement une **liste d'épicerie intelligente**. Il est pensé pour le
téléphone : vous préparez votre semaine à la maison, puis vous ouvrez la liste
directement à l'épicerie, même sans connexion.

L'application apparaît dans la **barre latérale de Home Assistant** (via
l'ingress) : aucun mot de passe supplémentaire, aucun port à ouvrir. C'est
Home Assistant qui gère l'accès.

## Démarrer

1. Installez et démarrez l'add-on.
2. Activez **« Afficher dans la barre latérale »**.
3. Cliquez sur **Repas** dans la barre latérale : l'application s'ouvre.

Vos données (recettes, planning, liste) sont enregistrées et **conservées**
entre les redémarrages et les mises à jour.

## Importer une recette

Deux façons d'ajouter une recette :

- **Par lien** : collez l'adresse d'une page de recette. L'application récupère
  le titre, les ingrédients et les étapes, puis vous présente un brouillon que
  vous pouvez corriger avant d'enregistrer. Si un site n'est pas lisible, un
  message clair vous l'indique (aucune recette n'est enregistrée à moitié).
- **Manuellement** : saisissez vous-même le titre, les ingrédients et les
  étapes. Utile pour les recettes de famille ou d'un livre.

Vous pouvez ajouter une **note personnelle** et une **note en étoiles** à
chaque recette.

## Planifier la semaine

Ouvrez le **planning hebdomadaire** et placez vos recettes sur les jours
souhaités : par glisser-déposer sur ordinateur, ou par simple appui sur mobile.
Indiquez le **nombre de portions** pour chaque repas ; les quantités de la
liste d'épicerie s'ajustent en conséquence.

## Générer la liste d'épicerie

Depuis le planning, générez la **liste d'épicerie**. L'application :

- **regroupe** automatiquement les ingrédients identiques présents dans
  plusieurs recettes,
- **additionne les quantités** en convertissant les unités quand c'est possible,
- **classe les articles par rayon** pour un parcours efficace en magasin.

À l'épicerie, cochez les articles au fur et à mesure.

## Le garde-manger

Indiquez dans le **garde-manger** ce que vous avez déjà en stock (sel, huile,
farine…). Ces ingrédients sont automatiquement **retirés de la liste
d'épicerie** : vous n'achetez que ce qui vous manque réellement.

## Configurer les rayons

Les ingrédients sont rangés par **rayon** (fruits & légumes, produits laitiers,
etc.). Vous pouvez **réorganiser et personnaliser** les rayons pour qu'ils
correspondent à l'agencement de votre magasin. Si un ingrédient est mal classé,
corrigez son rayon : l'application **retient votre choix** et le réappliquera
la prochaine fois.

## Alerte aubaines (optionnel, IA)

L'**Alerte aubaines** utilise l'intelligence artificielle pour repérer les
bonnes affaires. Cette fonction est **désactivée par défaut**.

Pour l'activer :

1. Ouvrez l'onglet **Configuration** de l'add-on.
2. Renseignez l'option **`anthropic_api_key`** avec votre clé API Anthropic.
3. Enregistrez et redémarrez l'add-on.

Laissez le champ **vide** pour garder la fonction désactivée.

## Utilisation hors ligne à l'épicerie

L'application est une **PWA** : une fois votre liste générée et consultée une
fois avec connexion, elle reste **accessible hors ligne**. Vous pouvez donc
ouvrir et cocher votre dernière liste d'épicerie en magasin, même si le réseau
est mauvais.

> Note : l'import par lien nécessite Internet (il va lire la page de recette).
> Tout le reste fonctionne en local.
