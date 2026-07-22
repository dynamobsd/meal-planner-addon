// Import unifié (création) : coller une URL -> scrape -> formulaire pré-rempli,
// OU passer directement en saisie manuelle. Le même RecipeForm sert dans tous
// les cas. À l'enregistrement : POST /api/recipes.
import { useState } from 'react';
import { createRecipe, scrapeRecipe, ApiError } from '../api/client';
import type { Category } from '../api/types';
import { RecipeForm, RecipeFormValues, valuesFrom } from '../components/RecipeForm';
import type { ImportPrefill } from '../App';

interface Props {
  categories: Category[];
  onSaved: () => void; // recette créée -> retour liste
  onCancel: () => void;
  // Pré-remplissage (venu d'une suggestion IA « nouvelle idée ») : on saute
  // directement au formulaire manuel pré-rempli.
  prefill?: ImportPrefill;
}

// Étape de l'écran : soit la zone URL, soit le formulaire (pré-rempli ou vide).
type Step =
  | { kind: 'url' }
  | { kind: 'form'; values: RecipeFormValues; info?: string | null };

export function ImportView({ categories, onSaved, onCancel, prefill }: Props) {
  const [url, setUrl] = useState('');
  const [scraping, setScraping] = useState(false);
  const [scrapeErr, setScrapeErr] = useState<string | null>(null);
  const [step, setStep] = useState<Step>(
    prefill
      ? { kind: 'form', values: valuesFrom(prefill) }
      : { kind: 'url' },
  );

  const [saving, setSaving] = useState(false);
  const [saveErr, setSaveErr] = useState<string | null>(null);

  const doScrape = async () => {
    const u = url.trim();
    if (!u) return;
    setScraping(true);
    setScrapeErr(null);
    try {
      const result = await scrapeRecipe(u);
      if (result.ok) {
        // Succès : formulaire pré-rempli avec le brouillon.
        setStep({ kind: 'form', values: valuesFrom(result.draft) });
      } else {
        // 422 attendu : bascule en saisie manuelle, URL conservée.
        setStep({
          kind: 'form',
          values: valuesFrom({ url_source: u }),
          info: `${result.message} L'URL a été conservée, complète les champs manuellement.`,
        });
      }
    } catch (e) {
      setScrapeErr(
        e instanceof ApiError
          ? e.message
          : 'Échec du scraping. Réseau indisponible ?',
      );
    } finally {
      setScraping(false);
    }
  };

  const startManual = () => {
    setStep({ kind: 'form', values: valuesFrom({ url_source: url.trim() }) });
  };

  const save = async (body: import('../api/types').RecipeInput) => {
    setSaving(true);
    setSaveErr(null);
    try {
      await createRecipe(body);
      onSaved();
    } catch (e) {
      setSaveErr(
        e instanceof ApiError ? e.message : 'Enregistrement impossible.',
      );
      setSaving(false);
    }
  };

  if (step.kind === 'form') {
    return (
      <div>
        {step.info && <div className="notice info">{step.info}</div>}
        <RecipeForm
          initial={step.values}
          categories={categories}
          submitLabel="Enregistrer"
          submitting={saving}
          errorMsg={saveErr}
          onSubmit={save}
          onCancel={onCancel}
        />
      </div>
    );
  }

  return (
    <div>
      <div className="scrape-box">
        <label
          htmlFor="scrape-url"
          style={{
            fontWeight: 600,
            display: 'block',
            marginBottom: 4,
          }}
        >
          Coller une URL de recette
        </label>
        <p style={{ margin: '0 0 4px', color: 'var(--mp-text-secondary)', fontSize: '0.9rem' }}>
          On tente d'extraire automatiquement les ingrédients et les étapes.
        </p>
        <div className="row">
          <input
            id="scrape-url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://…"
            inputMode="url"
            autoComplete="off"
          />
          <button
            className="btn"
            onClick={doScrape}
            disabled={scraping || url.trim() === ''}
          >
            {scraping ? '…' : 'Importer'}
          </button>
        </div>
        {scraping && (
          <div className="state-center" style={{ padding: '24px 0 6px' }}>
            <div className="spinner" />
            Extraction en cours…
          </div>
        )}
        {scrapeErr && (
          <div className="notice error" style={{ marginTop: 12, marginBottom: 0 }}>
            {scrapeErr}
          </div>
        )}
      </div>

      <button className="btn secondary block" onClick={startManual}>
        ✍️ Saisie manuelle
      </button>

      <div style={{ marginTop: 12 }}>
        <button className="btn secondary block" onClick={onCancel}>
          Annuler
        </button>
      </div>
    </div>
  );
}
