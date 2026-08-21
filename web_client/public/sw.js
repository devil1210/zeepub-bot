// Service Worker for Telegram Mini App
// Network-First strategy for JS/CSS/HTML to guarantee real-time updates

const CACHE_NAME = 'zeepub-v3.6.0-v3';
const RUNTIME_CACHE = 'zeepub-runtime-v3.6.0-v3';

// Install event - precache critical assets & force immediate activation
self.addEventListener('install', (event) => {
    console.log('[SW] Installing new Service Worker:', CACHE_NAME);
    self.skipWaiting();
});

// Activate event - clean ALL old caches aggressively
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating new Service Worker:', CACHE_NAME);
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((name) => {
                    console.log('[SW] Deleting cache:', name);
                    return caches.delete(name);
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') return;

    // API requests - Network First
    if (url.pathname.startsWith('/api/')) {
        const skipSWR = url.pathname.includes('/bot/status') ||
            url.pathname.includes('/auth/') ||
            request.method !== 'GET';

        if (skipSWR) {
            event.respondWith(fetch(request));
            return;
        }

        event.respondWith(
            fetch(request).then((networkResponse) => {
                if (networkResponse.ok) {
                    const clone = networkResponse.clone();
                    caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, clone));
                }
                return networkResponse;
            }).catch(() => caches.match(request))
        );
        return;
    }

    // JS, CSS and HTML Assets - NETWORK FIRST (Guarantees instant code updates)
    if (
        url.pathname.startsWith('/assets/') ||
        url.pathname.endsWith('.js') ||
        url.pathname.endsWith('.css') ||
        url.pathname.endsWith('.html') ||
        request.mode === 'navigate'
    ) {
        event.respondWith(
            fetch(request)
                .then((networkResponse) => {
                    if (networkResponse.ok) {
                        const responseClone = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseClone);
                        });
                    }
                    return networkResponse;
                })
                .catch(() => {
                    console.log('[SW] Network failed, serving cached asset:', url.pathname);
                    return caches.match(request);
                })
        );
        return;
    }

    // Images - Cache First with expiration
    if (
        url.pathname.startsWith('/api/library/covers/') ||
        request.destination === 'image'
    ) {
        event.respondWith(
            caches.match(request).then((cachedResponse) => {
                if (cachedResponse) {
                    return cachedResponse;
                }
                return fetch(request).then((response) => {
                    if (response.ok) {
                        const responseClone = response.clone();
                        caches.open(RUNTIME_CACHE).then((cache) => {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                });
            })
        );
        return;
    }
});
