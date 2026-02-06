import useSWR from 'swr';
import { api } from '@shared/services/api';
import { useTelegram } from '@shared/contexts/TelegramContext';
import { preloadImages } from '@shared/utils/imagePreloader';

// Keys for SWR
const KEYS = {
    HISTORY: 'dashboard/history',
    RECOMMENDATIONS: 'dashboard/recommendations',
};

// Types (inferred from usage)
interface DashboardData {
    history: any[];
    recommendations: any[];
    loading: boolean;
    error: any;
    mutate: () => Promise<void>;
}

export const useDashboardData = (): DashboardData => {
    const { showRecommendations } = useTelegram();

    // 1. Fetch Download History
    // Revalidate on mount, focus, and reconnect
    const {
        data: historyData,
        error: historyError,
        mutate: mutateHistory
    } = useSWR(KEYS.HISTORY, async () => {
        const res = await api.getDownloadHistory();
        return res?.downloads || [];
    }, {
        revalidateOnFocus: true,
        dedupingInterval: 60000, // Dedup requests within 1 minute
    });

    // 2. Fetch Recommendations
    // Only if showRecommendations is true
    const {
        data: recsData,
        error: recsError,
        mutate: mutateRecs
    } = useSWR(
        showRecommendations ? KEYS.RECOMMENDATIONS : null,
        async () => {
            const res = await api.getRecommendations(4);
            // Preload images for instant rendering
            if (res?.results) {
                preloadImages(res.results.map((r: any) => r.cover_thumb || r.cover || ''));
            }
            return res?.results || [];
        },
        {
            revalidateOnFocus: false, // Don't spam recommendations on focus
            revalidateIfStale: false, // Trust cache for a while
            dedupingInterval: 300000, // 5 minutes cache for recommendations
            keepPreviousData: true, // Show previous recommendations while fetching new ones
        }
    );

    const mutateAll = async () => {
        await Promise.all([mutateHistory(), mutateRecs()]);
    };

    return {
        history: historyData || [],
        recommendations: recsData || [],
        loading: (!historyData && !historyError) || (showRecommendations && !recsData && !recsError),
        error: historyError || recsError,
        mutate: mutateAll
    };
};
