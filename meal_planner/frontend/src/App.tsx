// Coquille SPA à onglets — PAS de react-router (casse sous ingress HA).
// La navigation est un état interne (onglet + écran empilé pour l'onglet Recettes).
import { useEffect, useState } from 'react';
import { BottomNav, Tab } from './components/BottomNav';
import { RecipesView } from './views/RecipesView';
import { RecipeDetailView } from './views/RecipeDetailView';
import { ImportView } from './views/ImportView';
import { EditView } from './views/EditView';
import { PlanningView } from './views/PlanningView';
import { GroceryView } from './views/GroceryView';
import { PantryView } from './views/PantryView';
import { SettingsView } from './views/SettingsView';
import { listCategories } from './api/client';
import type { Category, RecipeOut } from './api/types';

// Écran courant à l'intérieur de l'onglet "Recettes".
type Screen =
  | { name: 'list' }
  | { name: 'detail'; id: number }
  | { name: 'import' }
  | { name: 'edit'; recipe: RecipeOut };

export default function App() {
  const [tab, setTab] = useState<Tab>('recettes');
  const [screen, setScreen] = useState<Screen>({ name: 'list' });
  const [reloadKey, setReloadKey] = useState(0);
  const [categories, setCategories] = useState<Category[]>([]);

  // Chargement des rayons une fois (utilisé par les formulaires + le détail).
  useEffect(() => {
    listCategories()
      .then(setCategories)
      .catch(() => setCategories([]));
  }, []);

  const goList = () => setScreen({ name: 'list' });

  // Titre du header selon l'onglet/écran.
  const headerTitle = (() => {
    if (tab !== 'recettes') {
      return {
        planning: 'Planning',
        epicerie: 'Épicerie',
        'garde-manger': 'Garde-manger',
        reglages: 'Réglages',
        recettes: 'Recettes',
      }[tab];
    }
    switch (screen.name) {
      case 'list':
        return 'Recettes';
      case 'detail':
        return 'Recette';
      case 'import':
        return 'Nouvelle recette';
      case 'edit':
        return 'Éditer';
    }
  })();

  // Le header affiche un bouton retour dès qu'on est dans un sous-écran.
  const showBack = tab === 'recettes' && screen.name !== 'list';
  const back = () => {
    if (screen.name === 'edit') {
      // Retour au détail de la recette en cours d'édition.
      setScreen({ name: 'detail', id: screen.recipe.id });
    } else {
      goList();
    }
  };

  const renderRecettes = () => {
    switch (screen.name) {
      case 'list':
        return (
          <RecipesView
            reloadKey={reloadKey}
            onOpen={(id) => setScreen({ name: 'detail', id })}
            onCreate={() => setScreen({ name: 'import' })}
          />
        );
      case 'detail':
        return (
          <RecipeDetailView
            id={screen.id}
            onBack={goList}
            onEdit={(recipe) => setScreen({ name: 'edit', recipe })}
            onDeleted={() => {
              setReloadKey((k) => k + 1);
              goList();
            }}
          />
        );
      case 'import':
        return (
          <ImportView
            categories={categories}
            onSaved={() => {
              setReloadKey((k) => k + 1);
              goList();
            }}
            onCancel={goList}
          />
        );
      case 'edit':
        return (
          <EditView
            recipe={screen.recipe}
            categories={categories}
            onSaved={() => {
              setReloadKey((k) => k + 1);
              setScreen({ name: 'detail', id: screen.recipe.id });
            }}
            onCancel={() => setScreen({ name: 'detail', id: screen.recipe.id })}
          />
        );
    }
  };

  const renderBody = () => {
    switch (tab) {
      case 'recettes':
        return renderRecettes();
      case 'planning':
        return <PlanningView />;
      case 'epicerie':
        return <GroceryView />;
      case 'garde-manger':
        return <PantryView />;
      case 'reglages':
        return <SettingsView />;
    }
  };

  return (
    <div className="app">
      <header className="header">
        {showBack && (
          <button className="icon-btn" aria-label="Retour" onClick={back}>
            ←
          </button>
        )}
        <h1>{headerTitle}</h1>
      </header>

      <main className="content">{renderBody()}</main>

      <BottomNav
        active={tab}
        onChange={(t) => {
          setTab(t);
          // Repartir sur la liste quand on revient à l'onglet Recettes.
          if (t === 'recettes') goList();
        }}
      />
    </div>
  );
}
