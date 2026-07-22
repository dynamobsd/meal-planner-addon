// Types TypeScript miroir des schémas Pydantic du backend.
// Toute modification doit rester synchronisée avec backend/schemas.py.

export interface RecipeSummary {
  id: number;
  titre: string;
  image_url?: string | null;
  portions?: number | null;
  note_etoiles: number;
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
