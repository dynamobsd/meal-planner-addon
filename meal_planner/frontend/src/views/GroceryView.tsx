// Épicerie (Phase 4) — regroupée par rayon avec en-têtes COLLANTS, cases à
// cocher tactiles, avertissements, "J'en ai déjà", ajout manuel, et accès au
// scanner d'aubaines. Fonctionne HORS LIGNE : dernière liste en cache local +
// cochage optimiste rejoué au retour du réseau.
import { useCallback, useEffect, useState } from 'react';
import {
  addGroceryManual,
  deleteGrocery,
  exportGrocery,
  generateGrocery,
  getGrocery,
  haveGrocery,
  patchGrocery,
  ApiError,
} from '../api/client';
import type { GroceryItemOut, GroceryRayon } from '../api/types';
import { mondayOf, toISODate, addDays, weekLabel } from '../utils/date';
import {
  enqueuePatch,
  flushQueue,
  loadGroceryCache,
  saveGroceryCache,
} from '../utils/groceryCache';
import { ConfirmModal } from '../components/ConfirmModal';
import { DealsView } from './DealsView';

export function GroceryView() {
  const [monday, setMonday] = useState<Date>(() => mondayOf(new Date()));
  const semaine = toISODate(monday);

  const [rayons, setRayons] = useState<GroceryRayon[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [offline, setOffline] = useState(
    typeof navigator !== 'undefined' ? !navigator.onLine : false,
  );
  const [fromCache, setFromCache] = useState(false);
  const [manualOpen, setManualOpen] = useState(false);
  const [toDelete, setToDelete] = useState<GroceryItemOut | null>(null);
  const [showDeals, setShowDeals] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  // Repli si ni partage ni presse-papier : on affiche le texte à copier.
  const [shareText, setShareText] = useState<string | null>(null);

  // Charge la liste : réseau d'abord, repli sur le cache local si hors ligne.
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setFromCache(false);
    try {
      const data = await getGrocery(semaine);
      setRayons(data);
      saveGroceryCache(semaine, data);
    } catch (e) {
      const cached = loadGroceryCache(semaine);
      if (cached) {
        setRayons(cached);
        setFromCache(true);
      } else {
        setRayons([]);
        setError(
          e instanceof ApiError ? e.message : 'Liste indisponible hors ligne.',
        );
      }
    } finally {
      setLoading(false);
    }
  }, [semaine]);

  useEffect(() => {
    load();
  }, [load]);

  // Suivi de l'état réseau + rejeu de la file d'attente au retour online.
  useEffect(() => {
    const goOnline = () => {
      setOffline(false);
      flushQueue().then(() => load());
    };
    const goOffline = () => setOffline(true);
    window.addEventListener('online', goOnline);
    window.addEventListener('offline', goOffline);
    // Au montage, si on est online, on purge une éventuelle file en attente.
    if (navigator.onLine) flushQueue();
    return () => {
      window.removeEventListener('online', goOnline);
      window.removeEventListener('offline', goOffline);
    };
  }, [load]);

  // Met à jour un item localement + rafraîchit le cache.
  const patchLocal = (id: number, patch: Partial<GroceryItemOut>) => {
    setRayons((cur) => {
      if (!cur) return cur;
      const next = cur.map((r) => ({
        ...r,
        items: r.items.map((it) => (it.id === id ? { ...it, ...patch } : it)),
      }));
      saveGroceryCache(semaine, next);
      return next;
    });
  };

  const removeLocal = (id: number) => {
    setRayons((cur) => {
      if (!cur) return cur;
      const next = cur.map((r) => ({
        ...r,
        items: r.items.filter((it) => it.id !== id),
      }));
      saveGroceryCache(semaine, next);
      return next;
    });
  };

  // Cochage OPTIMISTE : effet immédiat, PATCH en arrière-plan, file si échec.
  const toggle = (item: GroceryItemOut) => {
    const next: 0 | 1 = item.coche ? 0 : 1;
    patchLocal(item.id, { coche: next });
    if (offline) {
      enqueuePatch(item.id, next);
      return;
    }
    patchGrocery(item.id, { coche: next }).catch(() =>
      enqueuePatch(item.id, next),
    );
  };

  const generate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const data = await generateGrocery(semaine);
      setRayons(data);
      saveGroceryCache(semaine, data);
      setFromCache(false);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Génération impossible.');
    } finally {
      setGenerating(false);
    }
  };

  const markHave = async (item: GroceryItemOut) => {
    removeLocal(item.id);
    try {
      await haveGrocery(item.id, true); // ajoute au garde-manger
    } catch {
      setError("Action « J'en ai déjà » impossible. Réessaie en ligne.");
      load();
    }
  };

  const confirmDelete = async () => {
    if (!toDelete) return;
    const id = toDelete.id;
    setToDelete(null);
    removeLocal(id);
    try {
      await deleteGrocery(id);
    } catch {
      setError('Suppression impossible.');
      load();
    }
  };

  const flashToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2200);
  };

  // Partage : Web Share API si dispo, sinon presse-papier, sinon modale copiable.
  const share = async () => {
    setSharing(true);
    setError(null);
    try {
      const { texte } = await exportGrocery(semaine);
      if (navigator.share) {
        await navigator.share({ title: "Liste d'épicerie", text: texte });
      } else if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(texte);
        flashToast('Copié ✓');
      } else {
        setShareText(texte); // repli ultime : affichage du texte
      }
    } catch (e) {
      // AbortError = l'utilisateur a annulé le partage natif : on l'ignore.
      if (e instanceof DOMException && e.name === 'AbortError') return;
      setError(e instanceof ApiError ? e.message : 'Partage impossible.');
    } finally {
      setSharing(false);
    }
  };

  if (showDeals) {
    return <DealsView semaine={semaine} onBack={() => setShowDeals(false)} />;
  }

  const isEmpty =
    rayons != null && rayons.every((r) => r.items.length === 0);

  return (
    <div>
      {/* Bandeau hors ligne discret */}
      {(offline || fromCache) && (
        <div className="offline-banner">
          📴 Hors ligne — liste en cache
        </div>
      )}

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

      <div className="grocery-actions">
        <button
          className="btn"
          onClick={generate}
          disabled={generating || offline}
        >
          {generating ? 'Génération…' : '🧾 Générer la liste'}
        </button>
        <button className="btn secondary" onClick={() => setManualOpen(true)}>
          + Item manuel
        </button>
        <button
          className="btn secondary"
          onClick={() => setShowDeals(true)}
          disabled={offline}
        >
          🏷️ Scanner une circulaire
        </button>
        <button
          className="btn secondary"
          onClick={share}
          disabled={sharing || offline}
        >
          {sharing ? '…' : '📤 Partager'}
        </button>
      </div>

      {error && <div className="notice error">{error}</div>}

      {loading && !rayons && (
        <div className="state-center">
          <div className="spinner" />
          Chargement…
        </div>
      )}

      {rayons && isEmpty && !error && (
        <div className="state-center">
          <div className="big" aria-hidden="true">
            🛒
          </div>
          <h2 style={{ margin: '0 0 8px' }}>Liste vide</h2>
          <p>Génère la liste à partir de ton planning ou ajoute un item.</p>
        </div>
      )}

      {rayons &&
        rayons
          .filter((r) => r.items.length > 0)
          .map((r) => (
            <section key={r.categorie_id ?? `nc-${r.categorie_nom}`}>
              <h3 className="rayon-head">{r.categorie_nom}</h3>
              {r.items.map((item) => (
                <div
                  className={`grocery-item${item.coche ? ' checked' : ''}`}
                  key={item.id}
                >
                  <button
                    className="check"
                    role="checkbox"
                    aria-checked={item.coche ? 'true' : 'false'}
                    aria-label={`Cocher ${item.nom}`}
                    onClick={() => toggle(item)}
                  >
                    {item.coche ? '✓' : ''}
                  </button>
                  <div className="grocery-main">
                    <span className="grocery-name">{item.nom}</span>
                    <span className="grocery-qty">
                      {item.quantite_totale != null && item.quantite_totale}
                      {item.unite ? ` ${item.unite}` : ''}
                      {item.source === 'manuel' && (
                        <span className="tag">manuel</span>
                      )}
                    </span>
                    {item.avertissement && (
                      <span className="warn-badge">
                        ⚠ {item.avertissement}
                      </span>
                    )}
                  </div>
                  <div className="grocery-item-actions">
                    <button
                      className="mini-action"
                      aria-label="J'en ai déjà"
                      title="J'en ai déjà (ajouter au garde-manger)"
                      onClick={() => markHave(item)}
                      disabled={offline}
                    >
                      🥫
                    </button>
                    <button
                      className="mini-action danger"
                      aria-label="Supprimer"
                      onClick={() => setToDelete(item)}
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </section>
          ))}

      {manualOpen && (
        <ManualItemModal
          semaine={semaine}
          onClose={() => setManualOpen(false)}
          onAdded={() => {
            setManualOpen(false);
            load();
          }}
        />
      )}

      {toDelete && (
        <ConfirmModal
          title="Retirer cet item ?"
          message={`« ${toDelete.nom} » sera retiré de la liste.`}
          confirmLabel="Retirer"
          danger
          onConfirm={confirmDelete}
          onCancel={() => setToDelete(null)}
        />
      )}

      {/* Toast éphémère (ex : « Copié ✓ ») */}
      {toast && <div className="toast">{toast}</div>}

      {/* Repli ultime de partage : texte copiable dans une modale */}
      {shareText != null && (
        <div
          className="modal-overlay"
          onClick={() => setShareText(null)}
          role="presentation"
        >
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-label="Liste d'épicerie"
            onClick={(e) => e.stopPropagation()}
          >
            <h3>Liste d'épicerie</h3>
            <textarea
              readOnly
              value={shareText}
              style={{
                width: '100%',
                minHeight: 220,
                padding: 10,
                borderRadius: 10,
                border: '1px solid var(--mp-divider)',
                background: 'var(--mp-card)',
                color: 'var(--mp-text)',
              }}
              onFocus={(e) => e.currentTarget.select()}
            />
            <div className="actions">
              <button className="btn block" onClick={() => setShareText(null)}>
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Modale d'ajout manuel
// --------------------------------------------------------------------------- //
function ManualItemModal({
  semaine,
  onClose,
  onAdded,
}: {
  semaine: string;
  onClose: () => void;
  onAdded: () => void;
}) {
  const [nom, setNom] = useState('');
  const [qte, setQte] = useState('');
  const [unite, setUnite] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async () => {
    if (nom.trim() === '') return;
    setBusy(true);
    setErr(null);
    try {
      await addGroceryManual({
        semaine,
        nom: nom.trim(),
        quantite_totale: qte.trim() === '' ? null : Number(qte),
        unite: unite.trim() || null,
      });
      onAdded();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : 'Ajout impossible.');
      setBusy(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="presentation">
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label="Ajouter un item"
        onClick={(e) => e.stopPropagation()}
      >
        <h3>Ajouter un item</h3>
        {err && <div className="notice error">{err}</div>}
        <div className="field">
          <label htmlFor="m-nom">Nom *</label>
          <input
            id="m-nom"
            value={nom}
            onChange={(e) => setNom(e.target.value)}
            autoFocus
          />
        </div>
        <div className="field-row">
          <div className="field">
            <label htmlFor="m-qte">Quantité</label>
            <input
              id="m-qte"
              value={qte}
              onChange={(e) => setQte(e.target.value)}
              inputMode="decimal"
            />
          </div>
          <div className="field">
            <label htmlFor="m-unite">Unité</label>
            <input
              id="m-unite"
              value={unite}
              onChange={(e) => setUnite(e.target.value)}
            />
          </div>
        </div>
        <div className="actions">
          <button className="btn secondary" onClick={onClose} disabled={busy}>
            Annuler
          </button>
          <button className="btn" onClick={submit} disabled={busy}>
            {busy ? '…' : 'Ajouter'}
          </button>
        </div>
      </div>
    </div>
  );
}
