
/**
 * Book cover interface with all quality levels
 */
export interface CoverPaths {
    cover_low?: string;
    cover_medium?: string;
    cover_high?: string;
    cover_original?: string;
    cover?: string;  // Fallback for backward compatibility
    cover_thumb?: string;  // Fallback for backward compatibility
}

/**
 * Returns the appropriate cover URL based on the user's quality preference.
 * Uses the new 4-level progressive quality system:
 * - pequeña: 200px (default for UI, fastest loading)
 * - mediana: 400px
 * - grande: 800px
 * - original: Full quality
 */
export const getCoverUrl = (
    coverPaths: CoverPaths | string | undefined,
    thumbPath: string | undefined,
    quality: 'pequeña' | 'mediana' | 'grande' | 'original'
): string => {
    // Handle legacy string format or string-based cover URLs
    if (typeof coverPaths === 'string') {
        const coverPath = coverPaths;

        // If it's a local API cover path, we can attempt to switch quality variants
        if (coverPath.includes('/api/library/covers/')) {
            const base = coverPath.replace(/_(low|medium|high|original)\.jpg$/, '');
            switch (quality) {
                case 'pequeña':
                    return thumbPath || `${base}_low.jpg`;
                case 'mediana':
                    return `${base}_medium.jpg`;
                case 'grande':
                    return `${base}_high.jpg`;
                case 'original':
                    return `${base}_original.jpg`;
                default:
                    return coverPath;
            }
        }

        switch (quality) {
            case 'pequeña':
                return thumbPath || coverPath;
            default:
                return coverPath;
        }
    }

    // Handle new object format with all quality levels
    if (!coverPaths) return '';

    switch (quality) {
        case 'pequeña':
            // Default: Low quality (200px) - fastest loading
            return coverPaths.cover_low || coverPaths.cover_thumb || coverPaths.cover_medium || coverPaths.cover || '';
        case 'mediana':
            // Medium quality (400px)
            return coverPaths.cover_medium || coverPaths.cover || coverPaths.cover_high || coverPaths.cover_low || '';
        case 'grande':
            // High quality (800px)
            return coverPaths.cover_high || coverPaths.cover_original || coverPaths.cover_medium || coverPaths.cover || '';
        case 'original':
            // Original quality (full resolution)
            return coverPaths.cover_original || coverPaths.cover_high || coverPaths.cover || '';
        default:
            // Fallback to low quality for best performance
            return coverPaths.cover_low || coverPaths.cover || '';
    }
};
