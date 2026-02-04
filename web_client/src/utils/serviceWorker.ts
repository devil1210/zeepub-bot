/**
 * Service Worker Registration Utility
 * Registers SW with proper error handling and update detection
 */

export const registerServiceWorker = async (): Promise<boolean> => {
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
        console.log('[SW] Service Worker not supported');
        return false;
    }

    try {
        const registration = await navigator.serviceWorker.register('/sw.js', {
            scope: '/',
        });

        console.log('[SW] Service Worker registered successfully');

        // Check for updates every hour
        setInterval(() => {
            registration.update();
        }, 60 * 60 * 1000);

        // Handle updates
        registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            if (!newWorker) return;

            newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                    // New version available
                    console.log('[SW] New version available! Refresh to update.');

                    // Optionally notify user via simple confirm
                    if (confirm('Hay una nueva versión de la app. ¿Recargar ahora?')) {
                        window.location.reload();
                    }
                }
            });
        });

        return true;
    } catch (error) {
        console.error('[SW] Registration failed:', error);
        return false;
    }
};

export const unregisterServiceWorker = async (): Promise<boolean> => {
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
        return false;
    }

    try {
        const registration = await navigator.serviceWorker.getRegistration();
        if (registration) {
            await registration.unregister();
            console.log('[SW] Service Worker unregistered');
            return true;
        }
        return false;
    } catch (error) {
        console.error('[SW] Unregistration failed:', error);
        return false;
    }
};

// Clear all caches (useful for debugging)
export const clearAllCaches = async (): Promise<void> => {
    if (typeof window === 'undefined' || !('caches' in window)) {
        return;
    }

    try {
        const cacheNames = await caches.keys();
        await Promise.all(cacheNames.map((name) => caches.delete(name)));
        console.log('[SW] All caches cleared');
    } catch (error) {
        console.error('[SW] Failed to clear caches:', error);
    }
};
