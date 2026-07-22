// Détail d'une recette : image, méta, ingrédients groupés par rayon, instructions.
import { useEffect, useState } from 'react';
import { getRecipe, deleteRecipe, ApiError } from '../api/client';
import type { Ingredient, RecipeOut } from '../api/types';
import { StarRating } from '../components/StarRating';
import { ConfirmModal } from '../components/ConfirmModal';

interface Props {
  id: number;
  onBack: () => void;
  onEdit: (recipe: RecipeOut) => void;
  onDeleted: () => void;
}

// Regroupe les ingrédients par rayon (categorie_nom), "Autres" en dernier.
function groupByRayon(ings: Ingredient[]): [string, Ingredient[]][] {
  const groups = new Map<string, Ingredient[]>();
  for (const ing of ings) {
    const key = ing.categorie_nom || 'Autres';
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(ing);
  }
  return Array.from(groups.entries()).sort((a, b) => {
    if (a[0] === 'Autres') return 1;
    if (b[0] === 'Autres') return -1;
    return a[0].localeCompare(b[0]);
  });
}

export function RecipeDetailView({ id, onBack, onEdit, onDeleted }: Props) {
  const [recipe, setRecipe] = useState<RecipeOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let alive = true;
    setError(null);
    setRecipe(null);
    getRecipe(id)
      .then((data) => alive && setRecipe(data))
      .catch((e: unknown) => {
        if (!alive) return;
        setError(e instanceof ApiError ? e.message : 'Recette introuvable.');
      });
    return () => {
      alive = false;
    };
  }, [id]);

  const doDelete = async () => {
    setDeleting(true);
    try {
      await deleteRecipe(id);
      onDeleted();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Suppression impossible.');
      setDeleting(false);
      setConfirmOpen(false);
    }
  };

  if (error) return <div className="notice error">{error}</div>;

  if (!recipe)
    return (
      <div className="state-center">
        <div className="spinner" />
        Chargement…
      </div>
    );

  const meta: string[] = [];
  if (recipe.portions != null) meta.push(`${recipe.portions} portions`);
  if (recipe.temps_prep != null) meta.push(`Prépa ${recipe.temps_prep} min`);
  if (recipe.temps_cuisson != null)
    meta.push(`Cuisson ${recipe.temps_cuisson} min`);

  const groups = groupByRayon(recipe.ingredients);

  return (
    <div>
      {recipe.image_url && (
        <img className="detail-hero" src={recipe.image_url} alt="" />
      )}

      <h1 style={{ margin: '16px 0 8px', fontSize: '1.5rem' }}>
        {recipe.titre}
      </h1>
      <div className="detail-rating-row">
        <StarRating value={recipe.note_etoiles} />
        {recipe.categorie_plat && (
          <span className="type-badge">{recipe.categorie_plat}</span>
        )}
      </div>

      {meta.length > 0 && (
        <div className="meta-row">
          {meta.map((m) => (
            <span key={m}>{m}</span>
          ))}
        </div>
      )}

      {recipe.url_source && (
        <p style={{ margin: '4px 0 0' }}>
          <a
            href={recipe.url_source}
            target="_blank"
            rel="noreferrer noopener"
            style={{ color: 'var(--mp-primary)' }}
          >
            Voir la source ↗
          </a>
        </p>
      )}

      <h2 className="section-title">Ingrédients</h2>
      {recipe.ingredients.length === 0 && (
        <p style={{ color: 'var(--mp-text-secondary)' }}>
          Aucun ingrédient renseigné.
        </p>
      )}
      {groups.map(([rayon, items]) => (
        <div key={rayon}>
          <div className="ing-group-title">{rayon}</div>
          {items.map((ing, i) => (
            <div className="ing-item" key={ing.id ?? `${rayon}-${i}`}>
              {ing.texte_brut}
            </div>
          ))}
        </div>
      ))}

      {recipe.instructions && (
        <>
          <h2 className="section-title">Instructions</h2>
          <div className="instructions">{recipe.instructions}</div>
        </>
      )}

      {recipe.note_perso && (
        <>
          <h2 className="section-title">Note perso</h2>
          <div className="instructions">{recipe.note_perso}</div>
        </>
      )}

      <div className="detail-actions">
        <button className="btn secondary" onClick={() => onEdit(recipe)}>
          ✏️ Éditer
        </button>
        <button className="btn danger" onClick={() => setConfirmOpen(true)}>
          🗑️ Supprimer
        </button>
      </div>

      <div style={{ marginTop: 16 }}>
        <button className="btn secondary block" onClick={onBack}>
          ← Retour à la liste
        </button>
      </div>

      {confirmOpen && (
        <ConfirmModal
          title="Supprimer la recette ?"
          message={`« ${recipe.titre} » sera définitivement supprimée.`}
          confirmLabel="Supprimer"
          danger
          busy={deleting}
          onConfirm={doDelete}
          onCancel={() => setConfirmOpen(false)}
        />
      )}
    </div>
  );
}
