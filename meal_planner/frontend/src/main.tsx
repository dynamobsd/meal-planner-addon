import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Enregistrement du service worker (PWA) — chemin RELATIF résolu contre la
// <base href> injectée par le backend, indispensable derrière l'ingress HA.
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    const swUrl = new URL('sw.js', document.baseURI).href;
    navigator.serviceWorker.register(swUrl).catch(() => {
      /* PWA best-effort : une erreur d'enregistrement ne casse pas l'app */
    });
  });
}
