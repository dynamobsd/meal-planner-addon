// Sélecteur de recette (overlay) — alternative TACTILE au drag&drop pour le
// planning : appui simple sur une recette pour l'ajouter au créneau visé.
import { useEffect, useMemo, useState } from 'react';
import { listRecipes, ApiError } from '../api/client';
import type { RecipeSummary } from '../api/types';
import { useTypesPlat } from '../utils/useTypesPlat';

interface Props {
  title: string;
  onPick: (recipe: RecipeSummary) => void;
  onClose: () => void;
}

export function RecipePicker({ title, onPick, onClose }: Props) {
  const [recipes, setRecipes] = useState<RecipeSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState('');
  const [filterType, setFilterType] = useState<string>(''); // '' = tous
  const typesPlat = useTypesPlat();

  useEffect(() => {
    let alive = true;
    listRecipes()
      .then((d) => alive && setRecipes(d))
      .catch((e: unknown) =>
        alive &&
        setError(e instanceof ApiError ? e.message : 'Chargement impossible.'),
      );
    return () => {
      alive = false;
    };
  }, []);

  // Filtrage client (texte + type de plat) sur la liste déjà chargée.
  const filtered = useMemo(() => {
    if (!recipes) return [];
    const term = q.trim().toLowerCase();
    return recipes.filter(
      (r) =>
        (term === '' || r.titre.toLowerCase().includes(term)) &&
        (filterType === '' || r.categorie_plat === filterType),
    );
  }, [recipes, q, filterType]);

  return (
    <div className="modal-overlay" onClick={onClose} role="presentation">
      <div
        className="modal picker"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
      >
        <h3>{title}</h3>
        <input
          className="picker-search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Rechercher une recette…"
          autoFocus
        />

        {/* Filtre par type de plat (ex : choisir « un dessert ») */}
        <div className="chips-scroll" aria-label="Filtrer par type">
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
          <div className="state-center" style={{ padding: '24px 0' }}>
            <div className="spinner" />
          </div>
        )}
        {recipes && filtered.length === 0 && (
          <p style={{ color: 'var(--mp-text-secondary)' }}>Aucune recette.</p>
        )}

        <div className="picker-list">
          {filtered.map((r) => (
            <button
              key={r.id}
              className="picker-item"
              onClick={() => onPick(r)}
            >
              {r.image_url ? (
                <img src={r.image_url} alt="" loading="lazy" />
              ) : (
                <span className="picker-thumb" aria-hidden="true">
                  🍽️
                </span>
              )}
              <span className="picker-title">{r.titre}</span>
            </button>
          ))}
        </div>

        <button className="btn secondary block" onClick={onClose}>
          Fermer
        </button>
      </div>
    </div>
  );
}
