// Édition d'une recette existante : réutilise RecipeForm, sauvegarde via PUT.
import { useState } from 'react';
import { updateRecipe, ApiError } from '../api/client';
import type { Category, RecipeInput, RecipeOut } from '../api/types';
import { RecipeForm, valuesFrom } from '../components/RecipeForm';

interface Props {
  recipe: RecipeOut;
  categories: Category[];
  onSaved: () => void;
  onCancel: () => void;
}

export function EditView({ recipe, categories, onSaved, onCancel }: Props) {
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const save = async (body: RecipeInput) => {
    setSaving(true);
    setErr(null);
    try {
      await updateRecipe(recipe.id, body);
      onSaved();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Enregistrement impossible.');
      setSaving(false);
    }
  };

  return (
    <RecipeForm
      initial={valuesFrom(recipe)}
      categories={categories}
      submitLabel="Enregistrer"
      submitting={saving}
      errorMsg={err}
      onSubmit={save}
      onCancel={onCancel}
    />
  );
}
