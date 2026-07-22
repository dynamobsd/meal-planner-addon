// Garde-manger (Phase 4) : liste éditable simple et tactile.
import { useEffect, useState } from 'react';
import {
  addPantry,
  deletePantry,
  getPantry,
  updatePantry,
  ApiError,
} from '../api/client';
import type { PantryOut } from '../api/types';

export function PantryView() {
  const [items, setItems] = useState<PantryOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Champs du formulaire d'ajout
  const [nom, setNom] = useState('');
  const [qte, setQte] = useState('');
  const [unite, setUnite] = useState('');
  const [adding, setAdding] = useState(false);

  const load = () => {
    setItems(null);
    setError(null);
    getPantry()
      .then(setItems)
      .catch((e: unknown) =>
        setError(e instanceof ApiError ? e.message : 'Chargement impossible.'),
      );
  };

  useEffect(load, []);

  const add = async () => {
    if (nom.trim() === '') return;
    setAdding(true);
    setError(null);
    try {
      const created = await addPantry({
        nom_ingredient: nom.trim(),
        quantite: qte.trim() === '' ? null : Number(qte),
        unite: unite.trim() || null,
      });
      setItems((cur) => (cur ? [...cur, created] : [created]));
      setNom('');
      setQte('');
      setUnite('');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Ajout impossible.');
    } finally {
      setAdding(false);
    }
  };

  const remove = async (id: number) => {
    const prev = items;
    setItems((cur) => (cur ? cur.filter((i) => i.id !== id) : cur));
    try {
      await deletePantry(id);
    } catch {
      setItems(prev ?? null);
      setError('Suppression impossible.');
    }
  };

  return (
    <div>
      {/* Formulaire d'ajout */}
      <div className="scrape-box">
        <div className="field" style={{ marginBottom: 10 }}>
          <label htmlFor="p-nom">Ingrédient</label>
          <input
            id="p-nom"
            value={nom}
            onChange={(e) => setNom(e.target.value)}
            placeholder="Ex : Riz basmati"
          />
        </div>
        <div className="field-row" style={{ marginBottom: 10 }}>
          <div className="field" style={{ marginBottom: 0 }}>
            <label htmlFor="p-qte">Quantité</label>
            <input
              id="p-qte"
              value={qte}
              onChange={(e) => setQte(e.target.value)}
              inputMode="decimal"
            />
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label htmlFor="p-unite">Unité</label>
            <input
              id="p-unite"
              value={unite}
              onChange={(e) => setUnite(e.target.value)}
            />
          </div>
        </div>
        <button
          className="btn block"
          onClick={add}
          disabled={adding || nom.trim() === ''}
        >
          {adding ? '…' : '+ Ajouter au garde-manger'}
        </button>
      </div>

      {error && <div className="notice error">{error}</div>}

      {!items && !error && (
        <div className="state-center">
          <div className="spinner" />
          Chargement…
        </div>
      )}

      {items && items.length === 0 && (
        <div className="state-center">
          <div className="big" aria-hidden="true">
            🥫
          </div>
          <h2 style={{ margin: '0 0 8px' }}>Garde-manger vide</h2>
          <p>Ajoute ce que tu as déjà à la maison.</p>
        </div>
      )}

      {items &&
        items.map((it) => (
          <PantryRow
            key={it.id}
            item={it}
            onSaved={(saved) =>
              setItems((cur) =>
                cur ? cur.map((x) => (x.id === saved.id ? saved : x)) : cur,
              )
            }
            onDelete={() => remove(it.id)}
            onError={setError}
          />
        ))}
    </div>
  );
}

// Ligne éditable (nom/quantité/unité) avec sauvegarde à la volée (PUT).
function PantryRow({
  item,
  onSaved,
  onDelete,
  onError,
}: {
  item: PantryOut;
  onSaved: (p: PantryOut) => void;
  onDelete: () => void;
  onError: (msg: string) => void;
}) {
  const [nom, setNom] = useState(item.nom_ingredient);
  const [qte, setQte] = useState(
    item.quantite != null ? String(item.quantite) : '',
  );
  const [unite, setUnite] = useState(item.unite ?? '');
  const [saving, setSaving] = useState(false);

  const dirty =
    nom !== item.nom_ingredient ||
    qte !== (item.quantite != null ? String(item.quantite) : '') ||
    unite !== (item.unite ?? '');

  const save = async () => {
    if (nom.trim() === '') return;
    setSaving(true);
    try {
      const saved = await updatePantry(item.id, {
        nom_ingredient: nom.trim(),
        quantite: qte.trim() === '' ? null : Number(qte),
        unite: unite.trim() || null,
      });
      onSaved(saved);
    } catch {
      onError('Enregistrement impossible.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="pantry-row">
      <input
        className="pantry-nom"
        value={nom}
        onChange={(e) => setNom(e.target.value)}
        aria-label="Nom"
      />
      <input
        className="pantry-qte"
        value={qte}
        onChange={(e) => setQte(e.target.value)}
        inputMode="decimal"
        aria-label="Quantité"
        placeholder="Qté"
      />
      <input
        className="pantry-unite"
        value={unite}
        onChange={(e) => setUnite(e.target.value)}
        aria-label="Unité"
        placeholder="Unité"
      />
      {dirty ? (
        <button
          className="mini-action save"
          onClick={save}
          disabled={saving}
          aria-label="Enregistrer"
        >
          {saving ? '…' : '💾'}
        </button>
      ) : (
        <button
          className="mini-action danger"
          onClick={onDelete}
          aria-label="Supprimer"
        >
          ✕
        </button>
      )}
    </div>
  );
}
