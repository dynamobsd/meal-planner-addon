// Liste des recettes (grille de cartes mobile-first).
import { useEffect, useState } from 'react';
import { listRecipes, ApiError } from '../api/client';
import type { RecipeSummary } from '../api/types';
import { StarRating } from '../components/StarRating';

interface Props {
  reloadKey: number; // change -> recharge la liste
  onOpen: (id: number) => void;
  onCreate: () => void;
}

export function RecipesView({ reloadKey, onOpen, onCreate }: Props) {
  const [recipes, setRecipes] = useState<RecipeSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setError(null);
    setRecipes(null);
    listRecipes()
      .then((data) => alive && setRecipes(data))
      .catch((e: unknown) => {
        if (!alive) return;
        setError(e instanceof ApiError ? e.message : 'Chargement impossible.');
      });
    return () => {
      alive = false;
    };
  }, [reloadKey]);

  return (
    <div>
      {error && <div className="notice error">{error}</div>}

      {!recipes && !error && (
        <div className="state-center">
          <div className="spinner" />
          Chargement des recettes…
        </div>
      )}

      {recipes && recipes.length === 0 && (
        <div className="state-center">
          <div className="big" aria-hidden="true">
            🍳
          </div>
          <h2 style={{ margin: '0 0 8px' }}>Aucune recette</h2>
          <p>Ajoute ta première recette avec le bouton +.</p>
        </div>
      )}

      {recipes && recipes.length > 0 && (
        <div className="recipe-list">
          {recipes.map((r) => (
            <button
              key={r.id}
              className="recipe-card"
              onClick={() => onOpen(r.id)}
            >
              {r.image_url ? (
                <img
                  className="thumb"
                  src={r.image_url}
                  alt=""
                  loading="lazy"
                />
              ) : (
                <div className="thumb placeholder" aria-hidden="true">
                  🍽️
                </div>
              )}
              <div className="card-body">
                <div className="card-title">{r.titre}</div>
                <StarRating value={r.note_etoiles} />
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Bouton flottant "+" -> import / création */}
      <button
        className="fab"
        aria-label="Ajouter une recette"
        onClick={onCreate}
      >
        +
      </button>
    </div>
  );
}
