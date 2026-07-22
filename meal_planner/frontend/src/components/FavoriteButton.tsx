// Bouton cœur ❤ — bascule le favori de façon OPTIMISTE (POST en arrière-plan).
// Réutilisé sur les cartes de la liste et sur le détail d'une recette.
import { useState, type MouseEvent } from 'react';
import { toggleFavori } from '../api/client';

interface Props {
  recipeId: number;
  favori: boolean;
  // Notifie le parent de l'état confirmé (ou du rollback) pour resync éventuelle.
  onChange?: (favori: boolean) => void;
  // Empêche le clic de déclencher l'ouverture de la carte parente.
  stopPropagation?: boolean;
  size?: 'sm' | 'lg';
}

export function FavoriteButton({
  recipeId,
  favori,
  onChange,
  stopPropagation,
  size = 'sm',
}: Props) {
  const [on, setOn] = useState(favori);
  const [busy, setBusy] = useState(false);

  const handle = async (e: MouseEvent) => {
    if (stopPropagation) e.stopPropagation();
    if (busy) return;
    const next = !on;
    setOn(next); // optimiste
    setBusy(true);
    try {
      const updated = await toggleFavori(recipeId);
      const confirmed = updated.favori === 1;
      setOn(confirmed);
      onChange?.(confirmed);
    } catch {
      setOn(!next); // rollback
    } finally {
      setBusy(false);
    }
  };

  return (
    <button
      type="button"
      className={`fav-btn ${size} ${on ? 'active' : ''}`}
      aria-pressed={on}
      aria-label={on ? 'Retirer des favoris' : 'Ajouter aux favoris'}
      onClick={handle}
    >
      {on ? '❤' : '🤍'}
    </button>
  );
}
