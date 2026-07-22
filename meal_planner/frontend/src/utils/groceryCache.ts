// Persistance locale de l'épicerie pour l'usage HORS LIGNE (au magasin).
// - La dernière liste générée est mise en cache par semaine (consultable offline).
// - Les changements de "coché" sont appliqués de façon OPTIMISTE et mis en file
//   d'attente quand le réseau est absent, puis rejoués via PATCH au retour online.
import type { GroceryRayon } from '../api/types';
import { patchGrocery } from '../api/client';

const listKey = (semaine: string) => `mp.grocery.list.${semaine}`;
const QUEUE_KEY = 'mp.grocery.queue';

interface PendingPatch {
  id: number;
  coche: 0 | 1;
}

export function saveGroceryCache(semaine: string, rayons: GroceryRayon[]): void {
  try {
    localStorage.setItem(listKey(semaine), JSON.stringify(rayons));
  } catch {
    /* quota/private mode : on ignore, le cache est best-effort */
  }
}

export function loadGroceryCache(semaine: string): GroceryRayon[] | null {
  try {
    const raw = localStorage.getItem(listKey(semaine));
    return raw ? (JSON.parse(raw) as GroceryRayon[]) : null;
  } catch {
    return null;
  }
}

function readQueue(): PendingPatch[] {
  try {
    const raw = localStorage.getItem(QUEUE_KEY);
    return raw ? (JSON.parse(raw) as PendingPatch[]) : [];
  } catch {
    return [];
  }
}

function writeQueue(q: PendingPatch[]): void {
  try {
    localStorage.setItem(QUEUE_KEY, JSON.stringify(q));
  } catch {
    /* ignore */
  }
}

/** Empile (ou remplace) le dernier état "coché" d'un item pour resync ultérieure. */
export function enqueuePatch(id: number, coche: 0 | 1): void {
  const q = readQueue().filter((p) => p.id !== id);
  q.push({ id, coche });
  writeQueue(q);
}

/**
 * Rejoue la file d'attente si le réseau est là. Best-effort : les échecs
 * restent en file pour un prochain essai.
 */
export async function flushQueue(): Promise<void> {
  if (typeof navigator !== 'undefined' && !navigator.onLine) return;
  let q = readQueue();
  if (q.length === 0) return;
  const remaining: PendingPatch[] = [];
  for (const p of q) {
    try {
      await patchGrocery(p.id, { coche: p.coche });
    } catch {
      remaining.push(p); // on garde pour plus tard
    }
  }
  writeQueue(remaining);
}
