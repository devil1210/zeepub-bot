import useSWR, { SWRConfiguration } from 'swr';
import { api } from '@shared/services/api';

/**
 * Custom hook for systematic data fetching with Stale-While-Revalidate (SWR).
 * Provides a unified interface for cached requests throughout the app.
 * 
 * @param key Unique key for the request (e.g., 'books/123')
 * @param fetcher Function that returns the data, defaults to API generic fetcher
 * @param config SWR configuration overrides
 */
export function useCachedFetch<T = any>(
    key: string | any[] | null,
    fetcher?: (...args: any[]) => Promise<T>,
    config?: SWRConfiguration
) {
    // Default fetcher: if key is a string, we might want a way to map it to API calls
    // but usually we pass the fetcher explicitly or rely on SWR global config (if set).
    // Here we'll default to a simple async call if no fetcher is provided.
    const defaultFetcher = async (action: string) => {
        // Zeepub uses a single POST /api/bot endpoint for most actions
        return api.rpc(action, {});
    };

    const { data, error, mutate, isValidating, isLoading } = useSWR<T>(
        key,
        fetcher || defaultFetcher,
        {
            revalidateOnFocus: false, // Prevents excessive revalidation when switching tabs
            dedupingInterval: 5000,    // Dedupe requests within 5 seconds
            ...config
        }
    );

    return {
        data,
        isLoading,
        isValidating,
        isError: error,
        mutate
    };
}
