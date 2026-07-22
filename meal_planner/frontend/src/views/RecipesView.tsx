// Liste des recettes (grille de cartes mobile-first) avec recherche plein-texte
// et filtre par type de plat (chips défilables horizontalement DANS leur bande).
import { useEffect, useState } from 'react';
import { listRecipes, ApiError } from '../api/client';
import type { RecipeSummary } from '../api/types';
import { useTypesPlat } from '../utils/useTypesPlat';
import { StarRating } from '../components/StarRating';

interface Props {
  reloadKey: number; // change -> recharge la liste
  onOpen: (id: number) => void;
  onCreate: () => void;
}

export function RecipesView({ reloadKey, onOpen, onCreate }: Props) {
  const [recipes, setRecipes] = useState<RecipeSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [q, setQ] = useState('');
  const [debouncedQ, setDebouncedQ] = useState('');
  const [filterType, setFilterType] = useState<string>(''); // '' = tous
  const typesPlat = useTypesPlat();

  // Débounce de la recherche pour limiter les appels réseau.
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q.trim()), 300);
    return () => clearTimeout(t);
  }, [q]);

  // (Re)chargement à chaque changement de filtre, recherche, ou reloadKey.
  useEffect(() => {
    let alive = true;
    setError(null);
    setRecipes(null);
    listRecipes({
      categorie_plat: filterType || undefined,
      q: debouncedQ || undefined,
    })
      .then((data) => alive && setRecipes(data))
      .catch((e: unknown) => {
        if (!alive) return;
        setError(e instanceof ApiError ? e.message : 'Chargement impossible.');
      });
    return () => {
      alive = false;
    };
  }, [reloadKey, debouncedQ, filterType]);

  return (
    <div>
      {/* Recherche */}
      <div className="search-bar">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="🔍 Rechercher une recette…"
          aria-label="Rechercher une recette"
          inputMode="search"
        />
      </div>

      {/* Filtre par type de plat (chips) */}
      <div className="chips-scroll" role="tablist" aria-label="Filtrer par type">
        <button
          className={`chip${filterType === '' ? ' active' : ''}`}
          onClick={() => setFilterType('')}
        >
          Tous
        </button>
        {typesPlat.map((t) => (
          <button
            key={t}
            className={`chip${filterType === t ? ' active' : ''}`}
            onClick={() => setFilterType(filterType === t ? '' : t)}
          >
            {t}
          </button>
        ))}
      </div>

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
          <p>
            {debouncedQ || filterType
              ? 'Aucun résultat pour ce filtre.'
              : 'Ajoute ta première recette avec le bouton +.'}
          </p>
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
                {r.categorie_plat && (
                  <span className="type-badge small">{r.categorie_plat}</span>
                )}
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
