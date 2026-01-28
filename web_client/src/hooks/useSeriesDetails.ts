import { useState, useEffect } from 'react';
import { Series, Volume } from '../../types';
import { api } from '../services/api';
import { getCoverUrl } from '../utils/imageUtils';
import { preloadImages } from '../utils/imagePreloader';

export const useSeriesDetails = (initialSeries: Series, settings: any, webApp: any) => {
    const [realSeries, setRealSeries] = useState<Series>(initialSeries);
    const [volumes, setVolumes] = useState<Volume[]>([]);
    const [loading, setLoading] = useState(true);
    const [isSyncing, setIsSyncing] = useState(false);

    const handleSyncSeries = async () => {
        if (isSyncing || !realSeries.series_hash) return;
        setIsSyncing(true);
        try {
            webApp?.HapticFeedback?.impactOccurred('medium');
            const res = await api.adminScanSeries(realSeries.series_hash, true);
            if (res.success) {
                webApp?.HapticFeedback?.notificationOccurred('success');
                webApp?.showAlert?.(res.message || "Sincronización iniciada.");
            } else {
                webApp?.HapticFeedback?.notificationOccurred('error');
                webApp?.showAlert?.(res.error || "Error al iniciar sincronización.");
            }
        } catch (e: any) {
            webApp?.HapticFeedback?.notificationOccurred('error');
            webApp?.showAlert?.("Error: " + e.message);
        } finally {
            setIsSyncing(false);
        }
    };

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const data = await api.getBookDetail(initialSeries.id);
                if (data) {
                    setRealSeries({
                        ...initialSeries,
                        ...data,
                        coverUrl: data.coverUrl || data.cover || initialSeries.coverUrl,
                        description: (data.summary || data.description || initialSeries.description)?.replace(/<br\s*\/?>/gi, '\n'),
                        englishTitle: data.english_title,
                        spanishTitle: data.spanish_title,
                        romajiTitle: data.romaji_title || data.romaji
                    } as Series);

                    if (data.volumes) {
                        console.log('🔍 [DEBUG] Raw volumes data from API:', data.volumes);
                        alert(`DEBUG: Raw API data: ${JSON.stringify(data.volumes.slice(0, 1), null, 2)}`);
                        const mappedVols: Volume[] = data.volumes.map((v: any) => {
                            console.log('🔍 [DEBUG] Processing volume:', v);
                            const mapped = {
                                id: v._id || v.id, // Use _id from API, fallback to id
                                seriesId: data._id || data.id,
                                title: v.title,
                                volumeNumber: v.seriesIndex || 1,
                                coverUrl: {
                                    cover_low: v.cover_low,
                                    cover_medium: v.cover_medium,
                                    cover_high: v.cover_high,
                                    cover_original: v.cover_original,
                                    cover: v.cover || data.cover
                                },
                                coverThumbUrl: v.cover_thumb || v.cover_low || v.cover || data.cover_thumb || data.cover,
                                publishedDate: v.publishedAt || 'N/A',
                                pages: v.pageCount || 0,
                                format: (v.bookType || 'EPUB').toUpperCase(),
                                rating: v.rating_average || 0,
                                description: v.summary || v.description,
                                uploader: v.translator || 'ZeePub',
                                downloadCount: v.download_count || 0,
                                demography: v.demographics,
                                tags: Array.isArray(v.tags) ? v.tags : (v.tags ? String(v.tags).split(',').map((t: string) => t.trim()) : []),
                                romajiTitle: v.romaji_title || v.romaji,
                                englishTitle: v.english_title,
                                spanishTitle: v.spanish_title,
                                illustrator: v.illustrator,
                                translator: v.translator,
                                typesetter: v.layoutBy,
                                group: v.publisher,
                                isbn: v.isbn,
                                asin: v.asin,
                                wordCount: v.wordCount,
                                readTime: v.readingTime ? `${v.readingTime} min` : 'N/A',
                                size: v.fileSize ? `${(v.fileSize / (1024 * 1024)).toFixed(2)} MB` : '0 MB',
                                language: v.language || 'Español',
                                epubVersion: v.epubVersion,
                                modifiedAt: v.modifiedAt,
                                modifiedAtOpf: v.modifiedAtOpf,
                                series: v.series,
                                cleanTitle: v.clean_title,
                                is_uncensored: v.is_uncensored,
                                color_mode: v.color_mode
                            };
                            console.log('🔍 [DEBUG] Mapped volume:', mapped);
                            return mapped;
                        });
                        console.log('🔍 [DEBUG] Mapped volumes:', mappedVols);
                        alert(`DEBUG: First mapped volume: ${JSON.stringify(mappedVols[0], null, 2)}`);
                        setVolumes(mappedVols);

                        const volCovers = mappedVols.map(v => getCoverUrl(v.coverUrl, v.coverThumbUrl, settings.coverQuality));
                        preloadImages(volCovers);

                        if (mappedVols.length > 0) {
                            const firstVol = [...mappedVols].sort((a, b) => (numA(a) - numB(b)))[0];
                            if (firstVol.description) {
                                setRealSeries(prev => ({
                                    ...prev,
                                    description: firstVol.description
                                }));
                            }
                        }
                    }
                }
            } catch (err) {
                console.error("Error fetching series details", err);
            } finally {
                setLoading(false);
            }
        };

        const numA = (v: Volume) => typeof v.volumeNumber === 'string' ? parseFloat(v.volumeNumber) : (v.volumeNumber || 0);
        const numB = (v: Volume) => typeof v.volumeNumber === 'string' ? parseFloat(v.volumeNumber) : (v.volumeNumber || 0);

        fetchData();
    }, [initialSeries.id]);

    return {
        realSeries,
        volumes,
        loading,
        isSyncing,
        handleSyncSeries
    };
};
