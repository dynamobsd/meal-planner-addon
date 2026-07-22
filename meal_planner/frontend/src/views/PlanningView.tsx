// Planning hebdomadaire (Phase 3).
// Choix ergonomique mobile : liste JOUR PAR JOUR (7 cartes empilées), chacune
// avec ses 4 créneaux. Pas de tableau 7x4 à scroller horizontalement -> zéro
// scroll horizontal de page à 390px. L'ajout se fait par un SÉLECTEUR tactile
// (RecipePicker), alternative fiable au drag&drop.
import { useEffect, useState } from 'react';
import {
  addMeal,
  deleteMeal,
  getMealPlan,
  updateMeal,
  ApiError,
} from '../api/client';
import type { MealPlanOut, MealType, RecipeSummary } from '../api/types';
import {
  addDays,
  jourNom,
  mondayOf,
  toISODate,
  dayShort,
  weekLabel,
} from '../utils/date';
import { RecipePicker } from '../components/RecipePicker';
import { SuggestionsView } from './SuggestionsView';
import { AutoPlanPanel, DuplicateWeekPanel } from './PlanningActions';

const CRENEAUX: { type: MealType; label: string }[] = [
  { type: 'dejeuner', label: 'Déjeuner' },
  { type: 'diner', label: 'Dîner' },
  { type: 'souper', label: 'Souper' },
  { type: 'collation', label: 'Collation' },
];

interface Props {
  // Navigation vers l'onglet Recettes (gérée par App) depuis les suggestions.
  onOpenRecipe: (id: number) => void;
  onCreateRecipe: (prefill: {
    titre: string;
    categorie_plat?: string | null;
  }) => void;
}

export function PlanningView({ onOpenRecipe, onCreateRecipe }: Props) {
  const [monday, setMonday] = useState<Date>(() => mondayOf(new Date()));
  const [meals, setMeals] = useState<MealPlanOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [picker, setPicker] = useState<{ date: string; type: MealType } | null>(
    null,
  );
  const [showSuggestions, setShowSuggestions] = useState(false);
  // Menu d'actions compact (évite le débordement du header à 390px).
  const [menuOpen, setMenuOpen] = useState(false);
  const [autoOpen, setAutoOpen] = useState(false);
  const [dupOpen, setDupOpen] = useState(false);

  const start = toISODate(monday);

  const load = () => {
    setMeals(null);
    setError(null);
    getMealPlan(start)
      .then(setMeals)
      .catch((e: unknown) =>
        setError(e instanceof ApiError ? e.message : 'Chargement impossible.'),
      );
  };

  useEffect(load, [start]);

  const pick = async (recipe: RecipeSummary) => {
    if (!picker) return;
    const target = picker;
    setPicker(null);
    try {
      const created = await addMeal({
        date: target.date,
        type_repas: target.type,
        recipe_id: recipe.id,
        portions_planifiees: recipe.portions ?? undefined,
      });
      setMeals((cur) => (cur ? [...cur, created] : [created]));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Ajout impossible.');
    }
  };

  const removeMeal = async (id: number) => {
    const prev = meals;
    setMeals((cur) => (cur ? cur.filter((m) => m.id !== id) : cur));
    try {
      await deleteMeal(id);
    } catch {
      setMeals(prev ?? null); // rollback
      setError('Suppression impossible.');
    }
  };

  const changePortions = async (id: number, value: string) => {
    const portions = value.trim() === '' ? null : Number(value);
    setMeals((cur) =>
      cur
        ? cur.map((m) =>
            m.id === id ? { ...m, portions_planifiees: portions } : m,
          )
        : cur,
    );
    try {
      await updateMeal(id, { portions_planifiees: portions });
    } catch {
      setError('Mise à jour des portions impossible.');
    }
  };

  // Sous-écran Suggestions (IA), ouvert depuis le bouton du header planning.
  if (showSuggestions) {
    return (
      <SuggestionsView
        onBack={() => setShowSuggestions(false)}
        onOpenRecipe={onOpenRecipe}
        onCreateRecipe={onCreateRecipe}
      />
    );
  }

  return (
    <div>
      {/* Barre d'action compacte : menu déroulant pour éviter tout débordement
          à 390px (Suggestions IA, génération auto, duplication). */}
      <div className="planning-top">
        <div className="actions-wrap">
          <button
            className="btn secondary"
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
          >
            ⋯ Actions
          </button>
          {menuOpen && (
            <>
              {/* Zone cliquable de fermeture */}
              <div
                className="menu-backdrop"
                onClick={() => setMenuOpen(false)}
                role="presentation"
              />
              <div className="actions-menu" role="menu">
                <button
                  role="menuitem"
                  onClick={() => {
                    setMenuOpen(false);
                    setShowSuggestions(true);
                  }}
                >
                  💡 Suggestions
                </button>
                <button
                  role="menuitem"
                  onClick={() => {
                    setMenuOpen(false);
                    setAutoOpen(true);
                  }}
                >
                  🤖 Générer ma semaine
                </button>
                <button
                  role="menuitem"
                  onClick={() => {
                    setMenuOpen(false);
                    setDupOpen(true);
                  }}
                >
                  📋 Dupliquer
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Navigation de semaine */}
      <div className="week-nav">
        <button
          className="icon-btn"
          aria-label="Semaine précédente"
          onClick={() => setMonday((d) => addDays(d, -7))}
        >
          ‹
        </button>
        <div className="week-label">{weekLabel(monday)}</div>
        <button
          className="icon-btn"
          aria-label="Semaine suivante"
          onClick={() => setMonday((d) => addDays(d, 7))}
        >
          ›
        </button>
      </div>

      {error && <div className="notice error">{error}</div>}

      {!meals && !error && (
        <div className="state-center">
          <div className="spinner" />
          Chargement du planning…
        </div>
      )}

      {meals &&
        [0, 1, 2, 3, 4, 5, 6].map((i) => {
          const day = addDays(monday, i);
          const iso = toISODate(day);
          return (
            <section className="day-card" key={iso}>
              <header className="day-head">
                <span className="day-name">{jourNom(i)}</span>
                <span className="day-date">{dayShort(day)}</span>
              </header>

              {CRENEAUX.map((c) => {
                const slotMeals = meals.filter(
                  (m) => m.date === iso && m.type_repas === c.type,
                );
                return (
                  <div className="slot" key={c.type}>
                    <div className="slot-head">
                      <span className="slot-label">{c.label}</span>
                      <button
                        className="slot-add"
                        aria-label={`Ajouter au ${c.label} du ${jourNom(i)}`}
                        onClick={() => setPicker({ date: iso, type: c.type })}
                      >
                        +
                      </button>
                    </div>

                    {slotMeals.map((m) => (
                      <div className="meal-chip" key={m.id}>
                        <div className="meal-chip-main">
                          <span className="meal-title">
                            {m.recette_titre ?? `Recette #${m.recipe_id}`}
                          </span>
                          <label className="portions">
                            <span>Portions</span>
                            <input
                              inputMode="numeric"
                              value={
                                m.portions_planifiees != null
                                  ? String(m.portions_planifiees)
                                  : ''
                              }
                              onChange={(e) =>
                                changePortions(m.id, e.target.value)
                              }
                            />
                          </label>
                        </div>
                        <button
                          className="del-btn"
                          aria-label="Retirer ce repas"
                          onClick={() => removeMeal(m.id)}
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                );
              })}
            </section>
          );
        })}

      {picker && (
        <RecipePicker
          title="Choisir une recette"
          onPick={pick}
          onClose={() => setPicker(null)}
        />
      )}

      {autoOpen && (
        <AutoPlanPanel
          semaine={start}
          onClose={() => setAutoOpen(false)}
          onReload={load}
        />
      )}

      {dupOpen && (
        <DuplicateWeekPanel
          sourceMonday={monday}
          onClose={() => setDupOpen(false)}
          onReload={load}
        />
      )}
    </div>
  );
}
