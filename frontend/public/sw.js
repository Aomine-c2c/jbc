/**
 * Bikita Minerals DWRMS — Service Worker (V2.3)
 * Provides progressive web app offline shell, controlled static caching,
 * and reliable cross-platform browser support without unsafe multi-user conflict caching.
 */

const CACHE_NAME = 'dwrms-static-v2.3.0';
const STATIC_ASSETS = [
  '/',
  '/favicon.ico',
  '/manifest.json',
];

// Install: Cache core app shell assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activate: Clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch: Cache-first for static immutable assets, Network-first for dynamic API routes
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // 1. Pass API requests directly to the network without stale HTTP caching
  if (url.pathname.startsWith('/api/')) {
    return;
  }

  // 2. Static files (CSS, JS, Fonts, Images)
  if (
    url.pathname.startsWith('/_next/static/') ||
    url.pathname.endsWith('.ico') ||
    url.pathname.endsWith('.png') ||
    url.pathname.endsWith('.svg') ||
    url.pathname.endsWith('.woff2')
  ) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) return cached;
        return fetch(event.request).then((response) => {
          if (response.status === 200) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return response;
        });
      })
    );
    return;
  }

  // 3. Navigation / HTML pages: Network-first with cache fallback
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match('/') || caches.match(event.request);
      })
    );
  }
});
