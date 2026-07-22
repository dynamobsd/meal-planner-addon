// Réglages (Phase 5) : gestion des rayons — renommer (inline), réordonner
// (boutons ↑/↓ fiables au doigt), ajouter, supprimer (confirmation in-app).
// L'ordre définit le parcours en magasin ; il est envoyé via reorder/apply.
import { useEffect, useState } from 'react';
import {
  createCategory,
  deleteCategory,
  listCategories,
  renameCategory,
  reorderCategories,
  ApiError,
} from '../api/client';
import type { Category } from '../api/types';
import { ConfirmModal } from '../components/ConfirmModal';

export function SettingsView() {
  const [cats, setCats] = useState<Category[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [newNom, setNewNom] = useState('');
  const [adding, setAdding] = useState(false);
  const [toDelete, setToDelete] = useState<Category | null>(null);

  const load = () => {
    setCats(null);
    setError(null);
    listCategories()
      .then((c) => setCats([...c].sort((a, b) => a.ordre_tri - b.ordre_tri)))
      .catch((e: unknown) =>
        setError(e instanceof ApiError ? e.message : 'Chargement impossible.'),
      );
  };

  useEffect(load, []);

  const add = async () => {
    if (newNom.trim() === '') return;
    setAdding(true);
    setError(null);
    try {
      const created = await createCategory(newNom.trim());
      setCats((cur) => (cur ? [...cur, created] : [created]));
      setNewNom('');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Ajout impossible.');
    } finally {
      setAdding(false);
    }
  };

  const rename = async (id: number, nom: string) => {
    try {
      const saved = await renameCategory(id, nom);
      setCats((cur) => (cur ? cur.map((c) => (c.id === id ? saved : c)) : cur));
    } catch {
      setError('Renommage impossible.');
    }
  };

  // Déplace l'élément puis persiste le nouvel ordre (liste d'ids).
  const move = async (index: number, dir: -1 | 1) => {
    if (!cats) return;
    const target = index + dir;
    if (target < 0 || target >= cats.length) return;
    const next = [...cats];
    [next[index], next[target]] = [next[target], next[index]];
    setCats(next);
    try {
      await reorderCategories(next.map((c) => c.id));
    } catch {
      setError('Réordonnancement impossible.');
      load();
    }
  };

  const confirmDelete = async () => {
    if (!toDelete) return;
    const id = toDelete.id;
    setToDelete(null);
    const prev = cats;
    setCats((cur) => (cur ? cur.filter((c) => c.id !== id) : cur));
    try {
      await deleteCategory(id);
    } catch {
      setCats(prev ?? null);
      setError('Suppression impossible.');
    }
  };

  return (
    <div>
      <h2 className="section-title" style={{ marginTop: 0 }}>
        Rayons d'épicerie
      </h2>
      <p style={{ color: 'var(--mp-text-secondary)', marginTop: 0 }}>
        L'ordre correspond à ton parcours en magasin.
      </p>

      {/* Ajout */}
      <div className="scrape-box">
        <div className="row">
          <input
            value={newNom}
            onChange={(e) => setNewNom(e.target.value)}
            placeholder="Nouveau rayon…"
            aria-label="Nom du nouveau rayon"
          />
          <button
            className="btn"
            onClick={add}
            disabled={adding || newNom.trim() === ''}
          >
            {adding ? '…' : 'Ajouter'}
          </button>
        </div>
      </div>

      {error && <div className="notice error">{error}</div>}

      {!cats && !error && (
        <div className="state-center">
          <div className="spinner" />
        </div>
      )}

      {cats &&
        cats.map((c, i) => (
          <CategoryRow
            key={c.id}
            cat={c}
            first={i === 0}
            last={i === cats.length - 1}
            onRename={(nom) => rename(c.id, nom)}
            onUp={() => move(i, -1)}
            onDown={() => move(i, 1)}
            onDelete={() => setToDelete(c)}
          />
        ))}

      {toDelete && (
        <ConfirmModal
          title="Supprimer le rayon ?"
          message={`« ${toDelete.nom} » sera supprimé. Les ingrédients associés deviendront non classés.`}
          confirmLabel="Supprimer"
          danger
          onConfirm={confirmDelete}
          onCancel={() => setToDelete(null)}
        />
      )}
    </div>
  );
}

function CategoryRow({
  cat,
  first,
  last,
  onRename,
  onUp,
  onDown,
  onDelete,
}: {
  cat: Category;
  first: boolean;
  last: boolean;
  onRename: (nom: string) => void;
  onUp: () => void;
  onDown: () => void;
  onDelete: () => void;
}) {
  const [nom, setNom] = useState(cat.nom);
  const dirty = nom.trim() !== cat.nom && nom.trim() !== '';

  return (
    <div className="cat-row">
      <div className="cat-order">
        <button
          className="mini-action"
          aria-label="Monter"
          onClick={onUp}
          disabled={first}
        >
          ↑
        </button>
        <button
          className="mini-action"
          aria-label="Descendre"
          onClick={onDown}
          disabled={last}
        >
          ↓
        </button>
      </div>
      <input
        className="cat-nom"
        value={nom}
        onChange={(e) => setNom(e.target.value)}
        onBlur={() => dirty && onRename(nom.trim())}
        aria-label="Nom du rayon"
      />
      {dirty && (
        <button
          className="mini-action save"
          aria-label="Renommer"
          onClick={() => onRename(nom.trim())}
        >
          💾
        </button>
      )}
      <button
        className="mini-action danger"
        aria-label="Supprimer"
        onClick={onDelete}
      >
        ✕
      </button>
    </div>
  );
}
