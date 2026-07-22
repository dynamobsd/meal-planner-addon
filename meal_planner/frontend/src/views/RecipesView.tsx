// Liste des recettes (grille de cartes mobile-first) avec recherche plein-texte,
// filtre par type de plat (chips défilables) et filtre Favoris.
import { useEffect, useMemo, useState } from 'react';
import { listRecipes, ApiError } from '../api/client';
import type { RecipeSummary } from '../api/types';
import { useTypesPlat } from '../utils/useTypesPlat';
import { StarRating } from '../components/StarRating';
import { FavoriteButton } from '../components/FavoriteButton';

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
  const [favOnly, setFavOnly] = useState(false);
  const typesPlat = useTypesPlat();

  // Débounce de la recherche pour limiter les appels réseau.
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q.trim()), 300);
    return () => clearTimeout(t);
  }, [q]);

  // (Re)chargement à chaque changement de filtre, recherche, ou reloadKey.
  // Le backend gère favori=true seul ; type/recherche sont alors filtrés côté
  // client (voir `displayed`).
  useEffect(() => {
    let alive = true;
    setError(null);
    setRecipes(null);
    const filters = favOnly
      ? { favori: true }
      : {
          categorie_plat: filterType || undefined,
          q: debouncedQ || undefined,
        };
    listRecipes(filters)
      .then((data) => alive && setRecipes(data))
      .catch((e: unknown) => {
        if (!alive) return;
        setError(e instanceof ApiError ? e.message : 'Chargement impossible.');
      });
    return () => {
      alive = false;
    };
  }, [reloadKey, debouncedQ, filterType, favOnly]);

  // En mode favoris, on cumule type de plat + recherche côté client.
  const displayed = useMemo(() => {
    if (!recipes) return null;
    if (!favOnly) return recipes;
    const term = debouncedQ.toLowerCase();
    return recipes.filter(
      (r) =>
        (filterType === '' || r.categorie_plat === filterType) &&
        (term === '' || r.titre.toLowerCase().includes(term)),
    );
  }, [recipes, favOnly, filterType, debouncedQ]);

  // Met à jour le favori d'une carte localement (après toggle optimiste).
  const updateFav = (id: number, favori: boolean) =>
    setRecipes((cur) =>
      cur
        ? cur.map((r) => (r.id === id ? { ...r, favori: favori ? 1 : 0 } : r))
        : cur,
    );

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

      {/* Filtres : Favoris + type de plat (chips) */}
      <div className="chips-scroll" role="tablist" aria-label="Filtres">
        <button
          className={`chip${favOnly ? ' active' : ''}`}
          onClick={() => setFavOnly((v) => !v)}
        >
          ❤ Favoris
        </button>
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

      {!displayed && !error && (
        <div className="state-center">
          <div className="spinner" />
          Chargement des recettes…
        </div>
      )}

      {displayed && displayed.length === 0 && (
        <div className="state-center">
          <div className="big" aria-hidden="true">
            {favOnly ? '❤' : '🍳'}
          </div>
          <h2 style={{ margin: '0 0 8px' }}>
            {favOnly ? 'Aucun favori' : 'Aucune recette'}
          </h2>
          <p>
            {debouncedQ || filterType || favOnly
              ? 'Aucun résultat pour ce filtre.'
              : 'Ajoute ta première recette avec le bouton +.'}
          </p>
        </div>
      )}

      {displayed && displayed.length > 0 && (
        <div className="recipe-list">
          {displayed.map((r) => (
            <div
              key={r.id}
              className="recipe-card"
              role="button"
              tabIndex={0}
              onClick={() => onOpen(r.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') onOpen(r.id);
              }}
            >
              <div className="thumb-wrap">
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
                <FavoriteButton
                  recipeId={r.id}
                  favori={r.favori === 1}
                  stopPropagation
                  onChange={(fav) => updateFav(r.id, fav)}
                />
              </div>
              <div className="card-body">
                <div className="card-title">{r.titre}</div>
                {r.categorie_plat && (
                  <span className="type-badge small">{r.categorie_plat}</span>
                )}
                <StarRating value={r.note_etoiles} />
              </div>
            </div>
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
