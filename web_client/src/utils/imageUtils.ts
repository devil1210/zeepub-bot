
/**
 * Returns the appropriate cover URL based on the user's quality preference.
 */
export const getCoverUrl = (
    coverPath: string | undefined,
    thumbPath: string | undefined,
    quality: 'pequeña' | 'mediana' | 'grande' | 'original'
): string => {
    if (!coverPath) return '';

    switch (quality) {
        case 'pequeña':
            return thumbPath || coverPath;
        case 'mediana':
            return coverPath;
        case 'grande':
            // Backend doesn't support 1000px yet, fallback to original or medium
            return coverPath.replace('.jpg', '_large.jpg'); // Future proofing
        case 'original':
            // The cover_path is currently 600px. 
            // If we had a truly original one (uncompressed), we'd use it.
            return coverPath.replace('.jpg', '_raw.jpg'); // Future proofing
        default:
            return coverPath;
    }
};
