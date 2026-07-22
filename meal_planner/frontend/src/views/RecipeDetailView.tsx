// Détail d'une recette : image, méta, ingrédients groupés par rayon, instructions.
import { useEffect, useState } from 'react';
import { getRecipe, deleteRecipe, ApiError } from '../api/client';
import type { Ingredient, RecipeOut } from '../api/types';
import { StarRating } from '../components/StarRating';
import { ConfirmModal } from '../components/ConfirmModal';
import { FavoriteButton } from '../components/FavoriteButton';

// Arrondi propre : 2 décimales max, sans zéros superflus (2.50 -> 2.5, 3.00 -> 3).
function formatQty(n: number): string {
  return String(parseFloat(n.toFixed(2)));
}

// Ligne d'ingrédient, éventuellement mise à l'échelle des portions (frontend).
// `factor` = portions choisies / portions d'origine. Si l'ingrédient n'a pas de
// quantité ou si l'échelle est neutre, on laisse le texte brut tel quel.
function ingredientLine(ing: Ingredient, factor: number): string {
  if (factor === 1 || ing.quantite == null) return ing.texte_brut;
  const scaled = formatQty(ing.quantite * factor);
  const nom = ing.nom_normalise?.trim() || ing.texte_brut;
  return [scaled, ing.unite ?? '', nom].filter(Boolean).join(' ');
}

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
  // Portions choisies (échelle) — initialisées sur celles de la recette.
  const [portionsN, setPortionsN] = useState<number | null>(null);

  useEffect(() => {
    let alive = true;
    setError(null);
    setRecipe(null);
    getRecipe(id)
      .then((data) => {
        if (!alive) return;
        setRecipe(data);
        setPortionsN(data.portions ?? null);
      })
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

  // Échelle des portions (calcul 100 % frontend, aucun appel backend).
  const canScale = recipe.portions != null && recipe.portions > 0;
  const factor = canScale && portionsN ? portionsN / recipe.portions! : 1;

  return (
    <div>
      {recipe.image_url && (
        <img className="detail-hero" src={recipe.image_url} alt="" />
      )}

      <div className="detail-title-row">
        <h1 style={{ margin: '16px 0 8px', fontSize: '1.5rem', flex: 1 }}>
          {recipe.titre}
        </h1>
        <FavoriteButton
          recipeId={recipe.id}
          favori={recipe.favori === 1}
          size="lg"
        />
      </div>
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

      {/* Échelle des portions : recalcule les quantités affichées (frontend). */}
      {canScale && (
        <div className="portions-scaler">
          <span className="ps-label">Portions</span>
          <div className="ps-stepper">
            <button
              className="ps-btn"
              aria-label="Diminuer les portions"
              onClick={() =>
                setPortionsN((n) => Math.max(1, (n ?? recipe.portions!) - 1))
              }
            >
              −
            </button>
            <span className="ps-value">{portionsN ?? recipe.portions}</span>
            <button
              className="ps-btn"
              aria-label="Augmenter les portions"
              onClick={() =>
                setPortionsN((n) => (n ?? recipe.portions!) + 1)
              }
            >
              +
            </button>
          </div>
          {factor !== 1 && (
            <button
              className="ps-reset"
              onClick={() => setPortionsN(recipe.portions ?? null)}
            >
              Réinitialiser
            </button>
          )}
        </div>
      )}

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
              {ingredientLine(ing, factor)}
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
