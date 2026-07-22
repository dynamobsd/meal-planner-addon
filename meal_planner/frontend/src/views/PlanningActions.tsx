// Panneaux d'actions du planning (Phase 9) : génération auto (IA) et
// duplication d'une semaine. Rendus en modales overlay, mobile-first.
import { useState } from 'react';
import { autoPlan, duplicateWeek, ApiError } from '../api/client';
import type { MealType } from '../api/types';
import { addDays, toISODate, weekLabel } from '../utils/date';
import { ConfirmModal } from '../components/ConfirmModal';

const CRENEAUX: { type: MealType; label: string }[] = [
  { type: 'dejeuner', label: 'Déjeuner' },
  { type: 'diner', label: 'Dîner' },
  { type: 'souper', label: 'Souper' },
  { type: 'collation', label: 'Collation' },
];

// --------------------------------------------------------------------------- //
// 1. Génération automatique de la semaine (IA)
// --------------------------------------------------------------------------- //
export function AutoPlanPanel({
  semaine,
  onClose,
  onReload,
}: {
  semaine: string;
  onClose: () => void;
  onReload: () => void;
}) {
  // Souper coché par défaut (repas principal le plus planifié).
  const [creneaux, setCreneaux] = useState<Record<MealType, boolean>>({
    dejeuner: false,
    diner: false,
    souper: true,
    collation: false,
  });
  const [remplacer, setRemplacer] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<{
    count: number;
    manquantes: string[];
  } | null>(null);

  const toggle = (t: MealType) =>
    setCreneaux((c) => ({ ...c, [t]: !c[t] }));

  const generate = async () => {
    const selected = CRENEAUX.filter((c) => creneaux[c.type]).map((c) => c.type);
    if (selected.length === 0) {
      setError('Sélectionne au moins un créneau.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await autoPlan({
        semaine,
        creneaux: selected,
        jours: 7,
        remplacer,
      });
      if (!res.ok || !res.disponible) {
        setError(
          res.message ||
            'Configure ta clé API Anthropic dans les options de l’add-on.',
        );
        return;
      }
      onReload(); // rafraîchit la semaine derrière le panneau
      setDone({
        count: res.ajoutes.length,
        manquantes: res.idees_manquantes.map((m) => m.titre),
      });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Génération impossible.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="presentation">
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label="Générer ma semaine"
        onClick={(e) => e.stopPropagation()}
      >
        <h3>🤖 Générer ma semaine</h3>

        {done ? (
          <>
            <p style={{ color: 'var(--mp-text)' }}>
              {done.count} repas ajouté{done.count > 1 ? 's' : ''}.
            </p>
            {done.manquantes.length > 0 && (
              <p className="deal-note">
                {done.manquantes.length} créneau
                {done.manquantes.length > 1 ? 'x' : ''} sans recette adaptée :{' '}
                {done.manquantes.join(', ')}
              </p>
            )}
            <div className="actions">
              <button className="btn block" onClick={onClose}>
                Terminé
              </button>
            </div>
          </>
        ) : (
          <>
            <p className="deal-note" style={{ marginTop: 0 }}>
              Créneaux à remplir :
            </p>
            {CRENEAUX.map((c) => (
              <label key={c.type} className="checkbox-row">
                <input
                  type="checkbox"
                  checked={creneaux[c.type]}
                  onChange={() => toggle(c.type)}
                />
                <span>{c.label}</span>
              </label>
            ))}

            <label className="checkbox-row" style={{ marginTop: 8 }}>
              <input
                type="checkbox"
                checked={remplacer}
                onChange={(e) => setRemplacer(e.target.checked)}
              />
              <span>Remplacer l'existant</span>
            </label>

            {error && <div className="notice error">{error}</div>}

            <div className="actions">
              <button
                className="btn secondary"
                onClick={onClose}
                disabled={busy}
              >
                Annuler
              </button>
              <button className="btn" onClick={generate} disabled={busy}>
                {busy ? 'Génération…' : 'Générer'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// 2. Duplication d'une semaine
// --------------------------------------------------------------------------- //
export function DuplicateWeekPanel({
  sourceMonday,
  onClose,
  onReload,
}: {
  sourceMonday: Date;
  onClose: () => void;
  onReload: () => void; // rechargement si la cible == semaine affichée
}) {
  // Cible par défaut : la semaine suivante.
  const [cible, setCible] = useState<Date>(() => addDays(sourceMonday, 7));
  const [remplacer, setRemplacer] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);

  const doDuplicate = async () => {
    setBusy(true);
    setError(null);
    try {
      await duplicateWeek({
        source_semaine: toISODate(sourceMonday),
        cible_semaine: toISODate(cible),
        remplacer,
      });
      setConfirm(false);
      setOkMsg(`Copié vers la ${weekLabel(cible).toLowerCase()}.`);
      onReload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Duplication impossible.');
      setConfirm(false);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="presentation">
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label="Dupliquer la semaine"
        onClick={(e) => e.stopPropagation()}
      >
        <h3>📋 Dupliquer la semaine</h3>

        {okMsg ? (
          <>
            <p style={{ color: 'var(--mp-text)' }}>{okMsg}</p>
            <div className="actions">
              <button className="btn block" onClick={onClose}>
                Terminé
              </button>
            </div>
          </>
        ) : (
          <>
            <p className="deal-note" style={{ marginTop: 0 }}>
              Source : {weekLabel(sourceMonday).toLowerCase()}
            </p>

            <span className="mini-label">Semaine cible</span>
            <div className="week-nav" style={{ marginTop: 4 }}>
              <button
                className="icon-btn"
                aria-label="Semaine cible précédente"
                onClick={() => setCible((d) => addDays(d, -7))}
              >
                ‹
              </button>
              <div className="week-label">{weekLabel(cible)}</div>
              <button
                className="icon-btn"
                aria-label="Semaine cible suivante"
                onClick={() => setCible((d) => addDays(d, 7))}
              >
                ›
              </button>
            </div>

            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={remplacer}
                onChange={(e) => setRemplacer(e.target.checked)}
              />
              <span>Remplacer la semaine cible</span>
            </label>

            {error && <div className="notice error">{error}</div>}

            <div className="actions">
              <button className="btn secondary" onClick={onClose}>
                Annuler
              </button>
              <button className="btn" onClick={() => setConfirm(true)}>
                Dupliquer
              </button>
            </div>
          </>
        )}

        {confirm && (
          <ConfirmModal
            title="Dupliquer la semaine ?"
            message={`Les repas seront copiés vers la ${weekLabel(
              cible,
            ).toLowerCase()}${remplacer ? ' (la cible sera remplacée)' : ''}.`}
            confirmLabel="Dupliquer"
            busy={busy}
            onConfirm={doDuplicate}
            onCancel={() => setConfirm(false)}
          />
        )}
      </div>
    </div>
  );
}
