// Hook réutilisable : charge la liste des types de plat une fois par montage.
// Utilisé par le formulaire, la liste de recettes, le sélecteur et les suggestions.
import { useEffect, useState } from 'react';
import { getTypesPlat } from '../api/client';

export function useTypesPlat(): string[] {
  const [types, setTypes] = useState<string[]>([]);
  useEffect(() => {
    let alive = true;
    getTypesPlat()
      .then((t) => alive && setTypes(t))
      .catch(() => {
        /* best-effort : select vide en cas d'échec */
      });
    return () => {
      alive = false;
    };
  }, []);
  return types;
}
