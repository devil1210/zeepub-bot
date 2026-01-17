/**
 * Simple utility to preload images into the browser cache.
 */
export const preloadImage = (url: string): Promise<void> => {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve();
        img.onerror = () => reject();
        img.src = url;
    });
};

/**
 * Preload a list of image URLs.
 */
export const preloadImages = (urls: string[]): Promise<void[]> => {
    const uniqueUrls = [...new Set(urls.filter(Boolean))];
    return Promise.all(uniqueUrls.map(url => preloadImage(url).catch(e => console.warn(`Failed to preload image: ${url}`, e))));
};
