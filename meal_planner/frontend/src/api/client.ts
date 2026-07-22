// Client API — TOUT est relatif à document.baseURI (ingress Home Assistant).
// Le backend injecte <base href="..."> au runtime : on résout l'URL de l'API
// contre cette base. JAMAIS de fetch('/api/...') absolu qui casserait le proxy.
import type {
  Category,
  DealsScanResponse,
  DealsStatus,
  GroceryItemOut,
  GroceryRayon,
  MealPlanOut,
  MealType,
  PantryOut,
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

// Gestion des rayons (Phase 5)
export const createCategory = (nom: string) =>
  request<Category>('categories', {
    method: 'POST',
    body: JSON.stringify({ nom }),
  });

export const renameCategory = (id: number, nom: string) =>
  request<Category>(`categories/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ nom }),
  });

export const reorderCategories = (ordered_ids: number[]) =>
  request<void>('categories/reorder/apply', {
    method: 'PUT',
    body: JSON.stringify({ ordered_ids }),
  });

export const deleteCategory = (id: number) =>
  request<void>(`categories/${id}`, { method: 'DELETE' });

// --------------------------------------------------------------------------- //
// Planning (Phase 3)
// --------------------------------------------------------------------------- //

export const getMealPlan = (start: string) =>
  request<MealPlanOut[]>(`meal-plan?start=${encodeURIComponent(start)}`);

export const addMeal = (body: {
  date: string;
  type_repas: MealType;
  recipe_id: number;
  portions_planifiees?: number;
}) =>
  request<MealPlanOut>('meal-plan', {
    method: 'POST',
    body: JSON.stringify(body),
  });

export const updateMeal = (
  id: number,
  body: {
    date?: string;
    type_repas?: MealType;
    portions_planifiees?: number | null;
  },
) =>
  request<MealPlanOut>(`meal-plan/${id}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  });

export const deleteMeal = (id: number) =>
  request<void>(`meal-plan/${id}`, { method: 'DELETE' });

// --------------------------------------------------------------------------- //
// Épicerie (Phase 4)
// --------------------------------------------------------------------------- //

export const generateGrocery = (semaine: string) =>
  request<GroceryRayon[]>('grocery/generate', {
    method: 'POST',
    body: JSON.stringify({ semaine }),
  });

export const getGrocery = (semaine: string) =>
  request<GroceryRayon[]>(`grocery?semaine=${encodeURIComponent(semaine)}`);

export const addGroceryManual = (body: {
  semaine: string;
  nom: string;
  quantite_totale?: number | null;
  unite?: string | null;
  categorie_id?: number | null;
}) =>
  request<GroceryItemOut>('grocery/manual', {
    method: 'POST',
    body: JSON.stringify(body),
  });

export const patchGrocery = (
  id: number,
  body: { coche?: 0 | 1; quantite_totale?: number | null },
) =>
  request<GroceryItemOut>(`grocery/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });

export const deleteGrocery = (id: number) =>
  request<void>(`grocery/${id}`, { method: 'DELETE' });

export const haveGrocery = (id: number, addToPantry: boolean) =>
  request<void>(`grocery/${id}/have?add_to_pantry=${addToPantry}`, {
    method: 'POST',
  });

// --------------------------------------------------------------------------- //
// Garde-manger (Phase 4)
// --------------------------------------------------------------------------- //

export const getPantry = () => request<PantryOut[]>('pantry');

export const addPantry = (body: {
  nom_ingredient: string;
  quantite?: number | null;
  unite?: string | null;
}) =>
  request<PantryOut>('pantry', {
    method: 'POST',
    body: JSON.stringify(body),
  });

export const updatePantry = (
  id: number,
  body: { nom_ingredient: string; quantite?: number | null; unite?: string | null },
) =>
  request<PantryOut>(`pantry/${id}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  });

export const deletePantry = (id: number) =>
  request<void>(`pantry/${id}`, { method: 'DELETE' });

// --------------------------------------------------------------------------- //
// Aubaines (IA)
// --------------------------------------------------------------------------- //

export const getDealsStatus = () => request<DealsStatus>('deals/status');

export const scanDeals = (body: {
  texte_circulaire: string;
  semaine?: string;
  magasin?: string;
}) =>
  request<DealsScanResponse>('deals/scan', {
    method: 'POST',
    body: JSON.stringify(body),
  });
