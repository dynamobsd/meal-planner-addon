import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// IMPORTANT (ingress Home Assistant) :
// base: './' => tous les chemins d'assets sont RELATIFS. Le backend injecte
// <base href="..."> au runtime pour les résoudre derrière le proxy HA.
export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    outDir: 'dist',
    // Assets sous dist/assets/ (comportement Vite par défaut, rendu explicite)
    assetsDir: 'assets',
  },
});
