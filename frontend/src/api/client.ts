// Client API — TOUT est relatif à document.baseURI (ingress Home Assistant).
// Le backend injecte <base href="..."> au runtime : on résout l'URL de l'API
// contre cette base. JAMAIS de fetch('/api/...') absolu qui casserait le proxy.
import type {
  Category,
  RecipeInput,
  RecipeOut,
  RecipeSummary,
  ScrapeResult,
} from './types';

// Base de l'API résolue dynamiquement contre <base href>.
export const API = new URL('api/', document.baseURI).href;

/** Erreur HTTP enrichie (statut + payload éventuel). */
export class ApiError extends Error {
  status: number;
  payload: unknown;
  constructor(status: number, message: string, payload?: unknown) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  const data = text ? JSON.parse(text) : undefined;
  if (!res.ok) {
    const msg =
      (data && (data.message || data.detail)) || `Erreur ${res.status}`;
    throw new ApiError(res.status, String(msg), data);
  }
  return data as T;
}

// --------------------------------------------------------------------------- //
// Recettes
// --------------------------------------------------------------------------- //

export const listRecipes = () => request<RecipeSummary[]>('recipes');

export const getRecipe = (id: number) => request<RecipeOut>(`recipes/${id}`);

export const createRecipe = (body: RecipeInput) =>
  request<RecipeOut>('recipes', {
    method: 'POST',
    body: JSON.stringify(body),
  });

export const updateRecipe = (id: number, body: RecipeInput) =>
  request<RecipeOut>(`recipes/${id}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  });

export const deleteRecipe = (id: number) =>
  request<void>(`recipes/${id}`, { method: 'DELETE' });

// --------------------------------------------------------------------------- //
// Import / scraping
// --------------------------------------------------------------------------- //

/**
 * Scrape une URL. Renvoie toujours un ScrapeResult (succès ou erreur métier),
 * sans jeter d'exception pour le 422 attendu (site non supporté).
 */
export async function scrapeRecipe(url: string): Promise<ScrapeResult> {
  const res = await fetch(API + 'recipes/scrape', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
  const data = (await res.json()) as ScrapeResult;
  return data;
}

// --------------------------------------------------------------------------- //
// Catégories / rayons
// --------------------------------------------------------------------------- //

export const listCategories = () => request<Category[]>('categories');

/** Apprentissage du rayon (fire-and-forget côté appelant). */
export const learnCategory = (nom_normalise: string, categorie_id: number) =>
  request<void>('categories/learn', {
    method: 'PUT',
    body: JSON.stringify({ nom_normalise, categorie_id }),
  });
