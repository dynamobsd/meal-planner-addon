// Suggestions de repas (IA) — Phase 8, « pour ma blonde ».
// Accessible depuis le header du Planning. Propose des idées personnalisées
// selon des préférences persistées. Nécessite une clé API Anthropic côté add-on.
import { useEffect, useState } from 'react';
import {
  getPreferencesGouts,
  getSuggestionsStatus,
  savePreferencesGouts,
  suggestMeals,
  ApiError,
} from '../api/client';
import type { MealSuggestion } from '../api/types';
import { useTypesPlat } from '../utils/useTypesPlat';

interface Props {
  onBack: () => void;
  onOpenRecipe: (id: number) => void;
  onCreateRecipe: (prefill: {
    titre: string;
    categorie_plat?: string | null;
  }) => void;
}

export function SuggestionsView({ onBack, onOpenRecipe, onCreateRecipe }: Props) {
  const [status, setStatus] = useState<'loading' | 'on' | 'off' | 'error'>(
    'loading',
  );
  const typesPlat = useTypesPlat();

  // Préférences persistées
  const [prefs, setPrefs] = useState('');
  const [prefsLoaded, setPrefsLoaded] = useState(false);
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [prefsSaved, setPrefsSaved] = useState(false);

  // Contrôles de génération
  const [nbRepas, setNbRepas] = useState(5);
  const [typePlat, setTypePlat] = useState('');
  const [utiliserMesRecettes, setUtiliserMesRecettes] = useState(true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<MealSuggestion[] | null>(null);

  useEffect(() => {
    getSuggestionsStatus()
      .then((s) => setStatus(s.disponible ? 'on' : 'off'))
      .catch(() => setStatus('error'));
    getPreferencesGouts()
      .then((p) => setPrefs(p.valeur ?? ''))
      .catch(() => {
        /* pas bloquant */
      })
      .finally(() => setPrefsLoaded(true));
  }, []);

  const savePrefs = async () => {
    setSavingPrefs(true);
    setPrefsSaved(false);
    try {
      const saved = await savePreferencesGouts(prefs);
      setPrefs(saved.valeur ?? '');
      setPrefsSaved(true);
      setTimeout(() => setPrefsSaved(false), 2500);
    } catch {
      setError('Enregistrement des préférences impossible.');
    } finally {
      setSavingPrefs(false);
    }
  };

  const propose = async () => {
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const res = await suggestMeals({
        // On n'envoie les préférences que si le champ est rempli ; sinon le
        // backend utilise celles enregistrées.
        preferences: prefs.trim() || undefined,
        nb_repas: nbRepas,
        type_plat: typePlat || undefined,
        utiliser_mes_recettes: utiliserMesRecettes,
      });
      if (!res.ok || !res.disponible) {
        setError(res.message || 'Suggestions indisponibles.');
      } else {
        setResults(res.suggestions);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Suggestions impossibles.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button className="btn secondary" onClick={onBack}>
        ← Retour au planning
      </button>

      <h2 className="section-title">💡 Suggestions de repas</h2>

      {status === 'loading' && (
        <div className="state-center">
          <div className="spinner" />
        </div>
      )}

      {status === 'error' && (
        <div className="notice error">
          Impossible de vérifier la disponibilité du service IA.
        </div>
      )}

      {status === 'off' && (
        <div className="notice info">
          Fonctionnalité IA désactivée. Configure ta clé API Anthropic dans les
          options de l'add-on Home Assistant pour l'activer.
        </div>
      )}

      {status === 'on' && (
        <>
          {/* Préférences / goûts (persistées) */}
          <div className="field">
            <label htmlFor="s-prefs">Préférences / goûts</label>
            <textarea
              id="s-prefs"
              value={prefs}
              onChange={(e) => setPrefs(e.target.value)}
              disabled={!prefsLoaded}
              placeholder="Ex : Ma blonde adore le poulet et déteste les champignons, végé le lundi…"
              style={{ minHeight: 90 }}
            />
            <button
              className="btn secondary"
              onClick={savePrefs}
              disabled={savingPrefs || !prefsLoaded}
              style={{ marginTop: 8 }}
            >
              {savingPrefs ? '…' : prefsSaved ? '✓ Enregistré' : '💾 Enregistrer'}
            </button>
          </div>

          {/* Contrôles */}
          <div className="field-row">
            <div className="field">
              <label htmlFor="s-nb">Nombre d'idées</label>
              <input
                id="s-nb"
                type="number"
                min={1}
                max={14}
                value={nbRepas}
                onChange={(e) => {
                  const n = Number(e.target.value);
                  setNbRepas(Number.isFinite(n) ? Math.min(14, Math.max(1, n)) : 5);
                }}
                inputMode="numeric"
              />
            </div>
            <div className="field">
              <label htmlFor="s-type">Type de plat</label>
              <select
                id="s-type"
                value={typePlat}
                onChange={(e) => setTypePlat(e.target.value)}
              >
                <option value="">Tous</option>
                {typesPlat.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={utiliserMesRecettes}
              onChange={(e) => setUtiliserMesRecettes(e.target.checked)}
            />
            <span>Utiliser mes recettes existantes</span>
          </label>

          <button
            className="btn block"
            onClick={propose}
            disabled={loading}
            style={{ marginTop: 12 }}
          >
            {loading ? 'Réflexion en cours…' : 'Proposer des repas'}
          </button>

          {error && (
            <div className="notice error" style={{ marginTop: 16 }}>
              {error}
            </div>
          )}

          {results && results.length === 0 && !error && (
            <div className="state-center">
              <p>Aucune suggestion pour ces critères.</p>
            </div>
          )}

          {results && results.length > 0 && (
            <div style={{ marginTop: 16 }}>
              {results.map((s, i) => (
                <SuggestionCard
                  key={`${s.titre}-${i}`}
                  s={s}
                  onOpenRecipe={onOpenRecipe}
                  onCreateRecipe={onCreateRecipe}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function SuggestionCard({
  s,
  onOpenRecipe,
  onCreateRecipe,
}: {
  s: MealSuggestion;
  onOpenRecipe: (id: number) => void;
  onCreateRecipe: (prefill: {
    titre: string;
    categorie_plat?: string | null;
  }) => void;
}) {
  const existante = s.recipe_id != null;

  return (
    <div className="deal-card">
      <div className="deal-top">
        <span className="deal-produit">{s.titre}</span>
        {s.type_plat && <span className="type-badge small">{s.type_plat}</span>}
      </div>

      <div style={{ marginTop: 6 }}>
        {existante ? (
          <span className="sugg-badge existing">📗 Dans tes recettes</span>
        ) : (
          s.nouvelle_idee && (
            <span className="sugg-badge new">✨ Nouvelle idée</span>
          )
        )}
      </div>

      {s.raison && <div className="deal-note">{s.raison}</div>}

      {!existante && s.ingredients_cles.length > 0 && (
        <div className="sugg-ingredients">
          {s.ingredients_cles.map((ing, j) => (
            <span key={j} className="ing-chip">
              {ing}
            </span>
          ))}
        </div>
      )}

      <div style={{ marginTop: 12 }}>
        {existante ? (
          <button
            className="btn secondary"
            onClick={() => onOpenRecipe(s.recipe_id!)}
          >
            Voir la recette →
          </button>
        ) : (
          <button
            className="btn"
            onClick={() =>
              onCreateRecipe({ titre: s.titre, categorie_plat: s.type_plat })
            }
          >
            ＋ Créer la recette
          </button>
        )}
      </div>
    </div>
  );
}
