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
                        romajiTitle: data.romaji_title || data.romaji,
                        demographics: data.demographics,
                        tags: data.tags
                    } as Series);

                    if (data.volumes) {
                        const mappedVols: Volume[] = data.volumes.map((v: any) => ({
                            id: v._id || v.id,
                            seriesId: data._id || data.id,
                            title: v.title,
                            volumeNumber: v.volumeNumber ?? v.volume ?? 1,
                            coverUrl: {
                                cover_low: v.cover_low,
                                cover_medium: v.cover_medium,
                                cover_high: v.cover_high,
                                cover_original: v.cover_original,
                                cover: v.cover || data.cover
                            },
                            coverThumbUrl: v.cover_thumb || v.cover_low || v.cover || data.cover_thumb || data.cover,
                            publishedDate: v.published_at || v.publishedAt || 'N/A',
                            pages: v.page_count || v.pageCount || 0,
                            format: (v.book_type || v.bookType || 'EPUB').toUpperCase(),
                            rating: v.rating_average || 0,
                            description: v.summary || v.description,
                            uploader: v.translator || 'ZeePub',
                            downloadCount: v.download_count || 0,
                            download_count: v.download_count || 0,
                            demography: v.demographics || [],
                            tags: Array.isArray(v.tags) ? v.tags : (v.tags ? String(v.tags).split(',').map((t: string) => t.trim()) : []),
                            romajiTitle: v.romaji_title || v.romaji,
                            englishTitle: v.english_title || v.englishTitle,
                            spanishTitle: v.spanish_title || v.spanishTitle,
                            illustrator: v.illustrator,
                            translator: v.translator,
                            typesetter: v.layout_by || v.layoutBy,
                            layout_by: v.layout_by || v.layoutBy,
                            group: v.group || v.publisher,
                            isbn: v.isbn,
                            asin: v.asin,
                            wordCount: v.word_count || v.wordCount,
                            word_count: v.word_count || v.wordCount,
                            pageCount: v.page_count || v.pageCount,
                            page_count: v.page_count || v.pageCount,
                            readingTime: v.reading_time || v.readingTime,
                            reading_time: v.reading_time || v.readingTime,
                            readTime: (v.reading_time || v.readingTime) ? `${v.reading_time || v.readingTime} min` : 'N/A',
                            size: (v.file_size || v.fileSize) ? `${((v.file_size || v.fileSize) / (1024 * 1024)).toFixed(2)} MB` : (v.size || '0 MB'),
                            file_size: v.file_size || v.fileSize,
                            language: v.language || 'Español',
                            epubVersion: v.epub_version || v.epubVersion,
                            epub_version: v.epub_version || v.epubVersion,
                            modifiedAt: v.modified_at || v.modifiedAt,
                            modified_at: v.modified_at || v.modifiedAt,
                            modifiedAtOpf: v.modified_at_opf || v.modifiedAtOpf,
                            modified_at_opf: v.modified_at_opf || v.modifiedAtOpf,
                            series: v.series,
                            cleanTitle: v.clean_title || v.cleanTitle,
                            is_uncensored: v.is_uncensored === 1 || v.is_uncensored === true,
                            color_mode: v.color_mode
                        }));
                        setVolumes(mappedVols);

                        const volCovers = mappedVols.map(v => getCoverUrl(v.coverUrl, v.coverThumbUrl, settings.coverQuality));
                        preloadImages(volCovers.slice(0, 6));

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
