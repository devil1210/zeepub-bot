/**
 * Simple utility to preload images into the browser cache.
 */
const loadedCache = new Set<string>();

export const preloadImage = (url: string): Promise<void> => {
    if (!url) return Promise.resolve();
    if (loadedCache.has(url)) return Promise.resolve();

    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
            loadedCache.add(url);
            resolve();
        };
        img.onerror = () => {
            // Still resolve to not break Promise.all, but log warning
            console.warn(`Failed to preload image: ${url}`);
            resolve();
        };
        img.src = url;
    });
};

/**
 * Preload a list of image URLs.
 */
export const preloadImages = (urls: string[]): Promise<void[]> => {
    const uniqueUrls = [...new Set(urls.filter(Boolean))];
    return Promise.all(uniqueUrls.map(url => preloadImage(url)));
};
