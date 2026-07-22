/* Service worker — app-shell + cache de la dernière liste d'épicerie.
 * Stratégies :
 *  - navigations : réseau d'abord, repli sur l'app-shell (index) en cache.
 *  - GET /api/grocery : réseau d'abord, on met la réponse en cache pour
 *    l'usage HORS LIGNE au magasin.
 *  - autres assets même origine : stale-while-revalidate.
 * Les chemins sont relatifs à la portée (scope) => compatible ingress HA.
 */
const CACHE = 'mp-cache-v1';

self.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE);
      // Précache de l'app-shell (index). './' résout vers l'index côté serveur.
      try {
        await cache.addAll(['./', 'index.html']);
      } catch (_e) {
        /* best-effort : certaines entrées peuvent échouer selon le proxy */
      }
      await self.skipWaiting();
    })(),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)),
      );
      await self.clients.claim();
    })(),
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return; // on ne touche qu'aux GET

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // laisser passer le cross-origin

  const isGrocery = url.pathname.includes('/api/grocery');
  const isApi = url.pathname.includes('/api/');

  // GET grocery : réseau d'abord, cache de secours (offline au magasin).
  if (isGrocery) {
    event.respondWith(
      (async () => {
        try {
          const res = await fetch(req);
          const cache = await caches.open(CACHE);
          cache.put(req, res.clone());
          return res;
        } catch (_e) {
          const cached = await caches.match(req);
          if (cached) return cached;
          throw _e;
        }
      })(),
    );
    return;
  }

  // Autres appels API : réseau uniquement (données fraîches).
  if (isApi) return;

  // Navigations : réseau d'abord, repli app-shell.
  if (req.mode === 'navigate') {
    event.respondWith(
      (async () => {
        try {
          return await fetch(req);
        } catch (_e) {
          const cache = await caches.open(CACHE);
          const shell =
            (await cache.match('index.html')) || (await cache.match('./'));
          return shell || Response.error();
        }
      })(),
    );
    return;
  }

  // Assets (js/css/img) : stale-while-revalidate.
  event.respondWith(
    (async () => {
      const cache = await caches.open(CACHE);
      const cached = await cache.match(req);
      const network = fetch(req)
        .then((res) => {
          if (res && res.status === 200) cache.put(req, res.clone());
          return res;
        })
        .catch(() => null);
      return cached || (await network) || fetch(req);
    })(),
  );
});
