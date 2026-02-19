/**
 * Telegram Mini App Performance Utilities
 * Optimizations specific to Telegram WebApp environment
 */

// Preload critical resources for Mini App
export const preloadCriticalResources = () => {
    if (typeof window === 'undefined') return;

    // Warm up API connection with a lightweight HEAD request (no body, no payload)
    // This establishes TCP/TLS handshake without triggering API logic
    const apiUrl = window.location.origin + '/api/library/stats';
    fetch(apiUrl, {
        method: 'HEAD',
        // Keep-alive ensures the connection stays warm for subsequent requests
        headers: { 'Connection': 'keep-alive' }
    }).catch(() => {
        // Silent fail - just warming up connection
    });
};

// Optimize images for Telegram's image proxy
export const getTelegramOptimizedImageUrl = (url: string, width?: number): string => {
    if (!url) return '';

    // If already a Telegram CDN URL, return as-is
    if (url.includes('cdn.telegram.org') || url.includes('t.me')) {
        return url;
    }

    // For local covers, use our optimized endpoint
    if (url.startsWith('/api/library/covers/')) {
        return url; // Already optimized
    }

    // For external URLs, consider using Telegram's image proxy for better performance
    // (Telegram caches images on their CDN)
    if (url.startsWith('http')) {
        // Option: proxy through our backend for caching
        return url;
    }

    return url;
};

// Haptic feedback helper with fallback
export const triggerHaptic = (
    type: 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error' = 'medium'
) => {
    try {
        const tg = (window as any)?.Telegram?.WebApp;
        if (!tg?.HapticFeedback) return;

        switch (type) {
            case 'light':
            case 'medium':
            case 'heavy':
                tg.HapticFeedback.impactOccurred(type);
                break;
            case 'success':
            case 'warning':
            case 'error':
                tg.HapticFeedback.notificationOccurred(type);
                break;
        }
    } catch (e) {
        // Silent fail - not critical
    }
};

// Optimize scroll performance for long lists
export const enableVirtualScrolling = (containerRef: HTMLElement | null) => {
    if (!containerRef) return;

    // Use Intersection Observer for lazy rendering
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        },
        {
            root: containerRef,
            rootMargin: '100px', // Start loading 100px before visible
            threshold: 0.01
        }
    );

    return observer;
};

// Telegram CloudStorage helper for caching
export const saveToTelegramCloud = async (key: string, value: any): Promise<boolean> => {
    try {
        const tg = (window as any)?.Telegram?.WebApp;
        if (!tg?.CloudStorage) return false;

        return new Promise((resolve) => {
            tg.CloudStorage.setItem(key, JSON.stringify(value), (error: any) => {
                resolve(!error);
            });
        });
    } catch {
        return false;
    }
};

export const loadFromTelegramCloud = async (key: string): Promise<any | null> => {
    try {
        const tg = (window as any)?.Telegram?.WebApp;
        if (!tg?.CloudStorage) return null;

        return new Promise((resolve) => {
            tg.CloudStorage.getItem(key, (error: any, result: string) => {
                if (error || !result) {
                    resolve(null);
                    return;
                }
                try {
                    resolve(JSON.parse(result));
                } catch {
                    resolve(null);
                }
            });
        });
    } catch {
        return null;
    }
};

// Network quality detection
export const getNetworkQuality = (): 'slow' | 'medium' | 'fast' => {
    try {
        const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;

        if (!connection) return 'medium';

        const effectiveType = connection.effectiveType;

        if (effectiveType === '4g') return 'fast';
        if (effectiveType === '3g') return 'medium';
        return 'slow';
    } catch {
        return 'medium';
    }
};

// Adaptive image quality based on network
export const getAdaptiveImageQuality = (): 'pequeña' | 'mediana' | 'grande' | 'original' => {
    const quality = getNetworkQuality();

    switch (quality) {
        case 'slow':
            return 'pequeña';
        case 'medium':
            return 'mediana';
        case 'fast':
            return 'grande';
        default:
            return 'mediana';
    }
};

// Debounced scroll handler for better performance
export const createOptimizedScrollHandler = (callback: () => void, delay: number = 150) => {
    let timeoutId: NodeJS.Timeout;
    let rafId: number;

    return () => {
        // Cancel previous calls
        if (timeoutId) clearTimeout(timeoutId);
        if (rafId) cancelAnimationFrame(rafId);

        // Use requestAnimationFrame for smooth updates
        rafId = requestAnimationFrame(() => {
            timeoutId = setTimeout(callback, delay);
        });
    };
};

// Preload next page of content
export const preloadNextPage = async (currentPage: number, fetchFunction: (page: number) => Promise<any>) => {
    try {
        // Preload in background without blocking UI
        setTimeout(() => {
            fetchFunction(currentPage + 1).catch(() => {
                // Silent fail - just prefetching
            });
        }, 1000);
    } catch {
        // Ignore errors
    }
};
