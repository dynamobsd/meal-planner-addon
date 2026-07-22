// Types TypeScript miroir des schémas Pydantic du backend.
// Toute modification doit rester synchronisée avec backend/schemas.py.

export interface RecipeSummary {
  id: number;
  titre: string;
  image_url?: string | null;
  portions?: number | null;
  note_etoiles: number;
  categorie_plat?: string | null;
  favori: number; // 0 | 1
}

// Ingrédient tel que renvoyé par l'API (Out) ou fourni dans un brouillon (Draft).
// `id` est présent pour les ingrédients persistés, absent pour les brouillons.
export interface Ingredient {
  id?: number;
  texte_brut: string;
  nom_normalise: string;
  quantite: number | null;
  unite: string | null;
  note: string | null;
  categorie_id: number | null;
  categorie_nom?: string | null;
}

export interface RecipeOut {
  id: number;
  titre: string;
  url_source?: string | null;
  image_url?: string | null;
  portions?: number | null;
  temps_prep?: number | null;
  temps_cuisson?: number | null;
  instructions?: string | null;
  note_perso?: string | null;
  note_etoiles: number;
  categorie_plat?: string | null;
  favori: number; // 0 | 1
  date_ajout: string;
  ingredients: Ingredient[];
}

export interface Category {
  id: number;
  nom: string;
  ordre_tri: number;
}

// Corps envoyé pour créer/éditer une recette (POST/PUT).
export interface RecipeInput {
  titre: string;
  url_source: string | null;
  image_url: string | null;
  portions: number | null;
  temps_prep: number | null;
  temps_cuisson: number | null;
  instructions: string | null;
  note_perso: string | null;
  note_etoiles: number;
  categorie_plat: string | null;
  // Optionnel : le favori se bascule via son endpoint dédié ; on ne l'envoie
  // pas depuis le formulaire (le backend préserve la valeur existante).
  favori?: number; // 0 | 1
  ingredients: Array<{
    texte_brut: string;
    nom_normalise: string;
    quantite: number | null;
    unite: string | null;
    note: string | null;
    categorie_id: number | null;
  }>;
}

// Brouillon renvoyé par le scraping (non sauvegardé).
export interface ScrapeDraft {
  titre: string;
  url_source?: string | null;
  host?: string | null;
  image_url?: string | null;
  portions?: number | null;
  temps_prep?: number | null;
  temps_cuisson?: number | null;
  instructions?: string | null;
  ingredients: Ingredient[];
}

export interface ScrapeSuccess {
  ok: true;
  source: string;
  draft: ScrapeDraft;
}

export interface ScrapeError {
  ok: false;
  error_code: string;
  message: string;
  url: string;
}

export type ScrapeResult = ScrapeSuccess | ScrapeError;

// --------------------------------------------------------------------------- //
// Planning (Phase 3)
// --------------------------------------------------------------------------- //

export type MealType = 'dejeuner' | 'diner' | 'souper' | 'collation';

export interface MealPlanOut {
  id: number;
  date: string; // YYYY-MM-DD
  type_repas: MealType;
  recipe_id: number;
  portions_planifiees?: number | null;
  recette_titre?: string | null;
  recette_image?: string | null;
  recette_portions?: number | null;
}

// --------------------------------------------------------------------------- //
// Épicerie (Phase 4)
// --------------------------------------------------------------------------- //

export interface GroceryItemOut {
  id: number;
  semaine: string;
  nom: string;
  quantite_totale?: number | null;
  unite?: string | null;
  categorie_id?: number | null;
  coche: number; // 0 | 1
  source: 'auto' | 'manuel';
  avertissement?: string | null;
  categorie_nom?: string | null;
}

export interface GroceryRayon {
  categorie_id: number | null;
  categorie_nom: string;
  ordre_tri: number;
  items: GroceryItemOut[];
}

// --------------------------------------------------------------------------- //
// Garde-manger (Phase 4)
// --------------------------------------------------------------------------- //

export interface PantryOut {
  id: number;
  nom_ingredient: string;
  quantite?: number | null;
  unite?: string | null;
}

// --------------------------------------------------------------------------- //
// Aubaines (IA)
// --------------------------------------------------------------------------- //

export interface DealsStatus {
  disponible: boolean;
}

export interface DealMatch {
  produit: string;
  prix?: string | null;
  rabais?: string | null;
  ingredient_liste?: string | null;
  pertinent: boolean;
  note?: string | null;
}

export interface DealsScanResponse {
  ok: boolean;
  disponible: boolean;
  message?: string | null;
  aubaines: DealMatch[];
}

// --------------------------------------------------------------------------- //
// Suggestions de repas (IA) — Phase 8
// --------------------------------------------------------------------------- //

export interface SuggestionsStatus {
  disponible: boolean;
}

export interface PreferencesGouts {
  cle: string;
  valeur: string | null;
}

export interface MealSuggestion {
  titre: string;
  type_plat?: string | null;
  raison?: string | null;
  recipe_id?: number | null;
  nouvelle_idee: boolean;
  ingredients_cles: string[];
}

export interface SuggestionsResponse {
  ok: boolean;
  disponible: boolean;
  message?: string | null;
  suggestions: MealSuggestion[];
}

// --------------------------------------------------------------------------- //
// Phase 9 — planning auto, duplication, export épicerie
// --------------------------------------------------------------------------- //

export interface AutoPlanResponse {
  ok: boolean;
  disponible: boolean;
  message?: string | null;
  ajoutes: MealPlanOut[];
  idees_manquantes: MealSuggestion[];
}

export interface GroceryExport {
  semaine: string;
  texte: string;
}
