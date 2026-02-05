// Service Worker for Telegram Mini App
// Caches critical assets for offline/fast loading

const CACHE_NAME = 'zeepub-v3.5.0';
const RUNTIME_CACHE = 'zeepub-runtime-v3.5.0';

// Assets to cache on install (critical for app to work)
const PRECACHE_ASSETS = [
    '/',
    '/index.html',
    '/assets/index.js',
    '/assets/index.css',
    // Add other critical assets from build
];

// Install event - precache critical assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[SW] Precaching critical assets');
            return cache.addAll(PRECACHE_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME && name !== RUNTIME_CACHE)
                    .map((name) => {
                        console.log('[SW] Deleting old cache:', name);
                        return caches.delete(name);
                    })
            );
        })
    );
    self.clients.claim();
});

// Fetch event - network first for API, cache first for assets
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') return;

    // API requests - Stale-While-Revalidate (Fastest for Mini Apps)
    if (url.pathname.startsWith('/api/')) {
        // Skip certain API calls that should always be fresh or are POST
        const skipSWR = url.pathname.includes('/bot/status') ||
            url.pathname.includes('/auth/') ||
            request.method !== 'GET';

        if (skipSWR) {
            event.respondWith(fetch(request));
            return;
        }

        event.respondWith(
            caches.open(RUNTIME_CACHE).then((cache) => {
                return cache.match(request).then((cachedResponse) => {
                    const fetchedResponse = fetch(request).then((networkResponse) => {
                        if (networkResponse.ok) {
                            cache.put(request, networkResponse.clone());
                        }
                        return networkResponse;
                    }).catch(() => {
                        // Silent fail for background fetch
                    });

                    // Return cached response immediately if exists, otherwise wait for network
                    return cachedResponse || fetchedResponse;
                });
            })
        );
        return;
    }

    // Static assets - Cache First (with network fallback)
    if (
        url.pathname.startsWith('/assets/') ||
        url.pathname.startsWith('/_next/') ||
        url.pathname.endsWith('.js') ||
        url.pathname.endsWith('.css') ||
        url.pathname.endsWith('.woff2')
    ) {
        event.respondWith(
            caches.match(request).then((cachedResponse) => {
                if (cachedResponse) {
                    return cachedResponse;
                }
                return fetch(request).then((response) => {
                    if (response.ok) {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                });
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
                    // Check if cached image is older than 7 days
                    const cachedDate = new Date(cachedResponse.headers.get('date'));
                    const now = new Date();
                    const daysSinceCached = (now - cachedDate) / (1000 * 60 * 60 * 24);

                    if (daysSinceCached < 7) {
                        return cachedResponse;
                    }
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

    // HTML - Network First (always fresh)
    if (request.mode === 'navigate' || url.pathname.endsWith('.html')) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    const responseClone = response.clone();
                    caches.open(RUNTIME_CACHE).then((cache) => {
                        cache.put(request, responseClone);
                    });
                    return response;
                })
                .catch(() => {
                    return caches.match(request);
                })
        );
        return;
    }
});

// Background sync for offline actions (future enhancement)
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-downloads') {
        event.waitUntil(syncDownloads());
    }
});

async function syncDownloads() {
    // Placeholder for syncing offline download requests
    console.log('[SW] Background sync triggered');
}

// Push notifications (future enhancement)
self.addEventListener('push', (event) => {
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'ZeePub Bot';
    const options = {
        body: data.body || 'Nueva actualización disponible',
        icon: '/icon-192.png',
        badge: '/badge-72.png',
        data: data.url,
    };

    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    if (event.notification.data) {
        event.waitUntil(clients.openWindow(event.notification.data));
    }
});
