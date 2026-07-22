// Formulaire de recette RÉUTILISABLE : sert au scrape, au manuel ET à l'édition.
// Il ne connaît pas la persistance : il remonte un RecipeInput via onSubmit.
import { useState } from 'react';
import type { Category, Ingredient, RecipeInput } from '../api/types';
import { learnCategory } from '../api/client';
import { StarRating } from './StarRating';

// ---- État interne : les nombres sont saisis en chaînes puis convertis. ----
interface IngredientRow {
  _key: string;
  texte_brut: string;
  nom_normalise: string;
  quantite: string;
  unite: string;
  note: string;
  categorie_id: number | null;
}

export interface RecipeFormValues {
  titre: string;
  url_source: string;
  image_url: string;
  portions: string;
  temps_prep: string;
  temps_cuisson: string;
  instructions: string;
  note_perso: string;
  note_etoiles: number;
  ingredients: IngredientRow[];
}

let keySeq = 0;
const nextKey = () => `ing-${keySeq++}`;

function toRow(ing: Partial<Ingredient>): IngredientRow {
  return {
    _key: nextKey(),
    texte_brut: ing.texte_brut ?? '',
    nom_normalise: ing.nom_normalise ?? '',
    quantite: ing.quantite != null ? String(ing.quantite) : '',
    unite: ing.unite ?? '',
    note: ing.note ?? '',
    categorie_id: ing.categorie_id ?? null,
  };
}

/** Construit des valeurs de formulaire depuis un brouillon/une recette. */
export function valuesFrom(source: {
  titre?: string | null;
  url_source?: string | null;
  image_url?: string | null;
  portions?: number | null;
  temps_prep?: number | null;
  temps_cuisson?: number | null;
  instructions?: string | null;
  note_perso?: string | null;
  note_etoiles?: number;
  ingredients?: Partial<Ingredient>[];
}): RecipeFormValues {
  return {
    titre: source.titre ?? '',
    url_source: source.url_source ?? '',
    image_url: source.image_url ?? '',
    portions: source.portions != null ? String(source.portions) : '',
    temps_prep: source.temps_prep != null ? String(source.temps_prep) : '',
    temps_cuisson:
      source.temps_cuisson != null ? String(source.temps_cuisson) : '',
    instructions: source.instructions ?? '',
    note_perso: source.note_perso ?? '',
    note_etoiles: source.note_etoiles ?? 0,
    ingredients: (source.ingredients ?? []).map(toRow),
  };
}

function numOrNull(s: string): number | null {
  const t = s.trim();
  if (t === '') return null;
  const n = Number(t.replace(',', '.'));
  return Number.isFinite(n) ? n : null;
}

function toRecipeInput(v: RecipeFormValues): RecipeInput {
  return {
    titre: v.titre.trim(),
    url_source: v.url_source.trim() || null,
    image_url: v.image_url.trim() || null,
    portions: numOrNull(v.portions),
    temps_prep: numOrNull(v.temps_prep),
    temps_cuisson: numOrNull(v.temps_cuisson),
    instructions: v.instructions.trim() || null,
    note_perso: v.note_perso.trim() || null,
    note_etoiles: v.note_etoiles,
    ingredients: v.ingredients
      .filter((r) => r.texte_brut.trim() !== '')
      .map((r) => ({
        texte_brut: r.texte_brut.trim(),
        nom_normalise: r.nom_normalise.trim(),
        quantite: numOrNull(r.quantite),
        unite: r.unite.trim() || null,
        note: r.note.trim() || null,
        categorie_id: r.categorie_id,
      })),
  };
}

interface Props {
  initial: RecipeFormValues;
  categories: Category[];
  submitLabel: string;
  submitting: boolean;
  errorMsg?: string | null;
  onSubmit: (body: RecipeInput) => void;
  onCancel: () => void;
}

export function RecipeForm({
  initial,
  categories,
  submitLabel,
  submitting,
  errorMsg,
  onSubmit,
  onCancel,
}: Props) {
  const [v, setV] = useState<RecipeFormValues>(initial);
  const [touched, setTouched] = useState(false);

  const patch = (p: Partial<RecipeFormValues>) => setV((cur) => ({ ...cur, ...p }));

  const patchRow = (key: string, p: Partial<IngredientRow>) =>
    setV((cur) => ({
      ...cur,
      ingredients: cur.ingredients.map((r) =>
        r._key === key ? { ...r, ...p } : r,
      ),
    }));

  const addRow = () =>
    setV((cur) => ({ ...cur, ingredients: [...cur.ingredients, toRow({})] }));

  const removeRow = (key: string) =>
    setV((cur) => ({
      ...cur,
      ingredients: cur.ingredients.filter((r) => r._key !== key),
    }));

  // Apprentissage : au changement de rayon d'un ingrédient nommé, on notifie
  // le backend en fire-and-forget (ne bloque JAMAIS la sauvegarde).
  const onRayonChange = (row: IngredientRow, categorie_id: number | null) => {
    patchRow(row._key, { categorie_id });
    const nom = row.nom_normalise.trim();
    if (nom && categorie_id != null) {
      learnCategory(nom, categorie_id).catch(() => {
        /* silencieux : l'apprentissage est best-effort */
      });
    }
  };

  const submit = () => {
    setTouched(true);
    if (v.titre.trim() === '') return; // titre obligatoire
    onSubmit(toRecipeInput(v));
  };

  const titleMissing = touched && v.titre.trim() === '';

  return (
    <div>
      {errorMsg && <div className="notice error">{errorMsg}</div>}

      <div className="field">
        <label htmlFor="f-titre">Titre *</label>
        <input
          id="f-titre"
          value={v.titre}
          onChange={(e) => patch({ titre: e.target.value })}
          placeholder="Nom de la recette"
        />
        {titleMissing && (
          <div className="notice error" style={{ marginTop: 8 }}>
            Le titre est obligatoire.
          </div>
        )}
      </div>

      <div className="field">
        <label htmlFor="f-image">Image (URL)</label>
        <input
          id="f-image"
          value={v.image_url}
          onChange={(e) => patch({ image_url: e.target.value })}
          placeholder="https://…"
          inputMode="url"
        />
      </div>

      <div className="field">
        <label htmlFor="f-source">Source (URL)</label>
        <input
          id="f-source"
          value={v.url_source}
          onChange={(e) => patch({ url_source: e.target.value })}
          placeholder="https://…"
          inputMode="url"
        />
      </div>

      <div className="field-row">
        <div className="field">
          <label htmlFor="f-portions">Portions</label>
          <input
            id="f-portions"
            value={v.portions}
            onChange={(e) => patch({ portions: e.target.value })}
            inputMode="numeric"
          />
        </div>
        <div className="field">
          <label htmlFor="f-prep">Prépa (min)</label>
          <input
            id="f-prep"
            value={v.temps_prep}
            onChange={(e) => patch({ temps_prep: e.target.value })}
            inputMode="numeric"
          />
        </div>
        <div className="field">
          <label htmlFor="f-cuisson">Cuisson (min)</label>
          <input
            id="f-cuisson"
            value={v.temps_cuisson}
            onChange={(e) => patch({ temps_cuisson: e.target.value })}
            inputMode="numeric"
          />
        </div>
      </div>

      <div className="field">
        <label>Note</label>
        <StarRating
          value={v.note_etoiles}
          onChange={(n) => patch({ note_etoiles: n })}
        />
      </div>

      {/* -------- Ingrédients -------- */}
      <h2 className="section-title">Ingrédients</h2>
      {v.ingredients.length === 0 && (
        <p style={{ color: 'var(--mp-text-secondary)' }}>
          Aucun ingrédient. Ajoute une ligne ci-dessous.
        </p>
      )}

      {v.ingredients.map((row) => (
        <div className="ing-line" key={row._key}>
          <div className="raw-row">
            <input
              value={row.texte_brut}
              onChange={(e) => patchRow(row._key, { texte_brut: e.target.value })}
              placeholder="Ex : 200 g de farine"
              aria-label="Texte de l'ingrédient"
            />
            <button
              type="button"
              className="del-btn"
              aria-label="Supprimer l'ingrédient"
              onClick={() => removeRow(row._key)}
            >
              ✕
            </button>
          </div>
          <div className="sub-grid">
            <div>
              <span className="mini-label">Quantité</span>
              <input
                value={row.quantite}
                onChange={(e) => patchRow(row._key, { quantite: e.target.value })}
                inputMode="decimal"
                placeholder="200"
              />
            </div>
            <div>
              <span className="mini-label">Unité</span>
              <input
                value={row.unite}
                onChange={(e) => patchRow(row._key, { unite: e.target.value })}
                placeholder="g"
              />
            </div>
            <div className="full">
              <span className="mini-label">Nom normalisé</span>
              <input
                value={row.nom_normalise}
                onChange={(e) =>
                  patchRow(row._key, { nom_normalise: e.target.value })
                }
                placeholder="farine"
              />
            </div>
            <div className="full">
              <span className="mini-label">Rayon</span>
              <select
                value={row.categorie_id ?? ''}
                onChange={(e) =>
                  onRayonChange(
                    row,
                    e.target.value === '' ? null : Number(e.target.value),
                  )
                }
              >
                <option value="">— Non classé —</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nom}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      ))}

      <button type="button" className="btn secondary block" onClick={addRow}>
        + Ajouter un ingrédient
      </button>

      {/* -------- Instructions -------- */}
      <div className="field" style={{ marginTop: 22 }}>
        <label htmlFor="f-instr">Instructions</label>
        <textarea
          id="f-instr"
          value={v.instructions}
          onChange={(e) => patch({ instructions: e.target.value })}
          placeholder="Étapes de préparation…"
        />
      </div>

      <div className="field">
        <label htmlFor="f-note">Note perso</label>
        <textarea
          id="f-note"
          value={v.note_perso}
          onChange={(e) => patch({ note_perso: e.target.value })}
          style={{ minHeight: 70 }}
        />
      </div>

      <div className="detail-actions">
        <button
          type="button"
          className="btn secondary"
          onClick={onCancel}
          disabled={submitting}
        >
          Annuler
        </button>
        <button
          type="button"
          className="btn"
          onClick={submit}
          disabled={submitting}
        >
          {submitting ? 'Enregistrement…' : submitLabel}
        </button>
      </div>
    </div>
  );
}
