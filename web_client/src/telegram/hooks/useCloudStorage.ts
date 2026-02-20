import { useEffect, useState, useCallback } from 'react';

/**
 * Check if Telegram CloudStorage is available
 */
const isCloudStorageAvailable = () => {
    return typeof window !== 'undefined' &&
        window.Telegram?.WebApp?.CloudStorage !== undefined;
};

/**
 * Hook to use Telegram CloudStorage with localStorage fallback
 * 
 * @param key - Storage key
 * @param defaultValue - Default value if not found
 * @returns Object with value, saveValue function, and loading state
 */
export const useCloudStorage = <T,>(key: string, defaultValue: T) => {
    const [value, setValue] = useState<T>(defaultValue);
    const [isLoading, setIsLoading] = useState(true);

    // Load from CloudStorage on mount
    useEffect(() => {
        let isMounted = true;
        let timeoutId: NodeJS.Timeout;

        if (!isCloudStorageAvailable()) {
            // Fallback: try to load from localStorage
            try {
                const saved = localStorage.getItem(key);
                if (saved && isMounted) {
                    setValue(JSON.parse(saved) as T);
                }
            } catch (e) {
                console.error(`Error loading from localStorage for ${key}:`, e);
            }
            if (isMounted) setIsLoading(false);
            return;
        }

        // Failsafe timeout in case CloudStorage hangs
        timeoutId = setTimeout(() => {
            if (!isMounted) return;
            console.warn(`CloudStorage loading timed out for ${key}. Falling back to localStorage.`);
            try {
                const saved = localStorage.getItem(key);
                if (saved) {
                    setValue(JSON.parse(saved) as T);
                }
            } catch (e) {
                console.error(`Error loading from localStorage fallback for ${key}:`, e);
            }
            setIsLoading(false);
        }, 1500);

        // Use Telegram CloudStorage
        window.Telegram.WebApp.CloudStorage.getItem(key, (error, result) => {
            if (!isMounted) return;
            clearTimeout(timeoutId);

            if (error) {
                console.error(`CloudStorage getItem error for ${key}:`, error);
                // Fallback to localStorage on error
                try {
                    const saved = localStorage.getItem(key);
                    if (saved) {
                        setValue(JSON.parse(saved) as T);
                    }
                } catch (e) {
                    console.error(`Error loading from localStorage fallback for ${key}:`, e);
                }
                setIsLoading(false);
                return;
            }

            if (result) {
                try {
                    setValue(JSON.parse(result) as T);
                } catch (e) {
                    console.error(`Error parsing CloudStorage value for ${key}:`, e);
                }
            }
            setIsLoading(false);
        });

        return () => {
            isMounted = false;
            clearTimeout(timeoutId);
        };
    }, [key]);

    // Save to CloudStorage
    const saveValue = useCallback((newValue: T) => {
        setValue(newValue);

        if (!isCloudStorageAvailable()) {
            // Fallback to localStorage if CloudStorage not available
            try {
                localStorage.setItem(key, JSON.stringify(newValue));
            } catch (e) {
                console.error(`Error saving to localStorage for ${key}:`, e);
            }
            return;
        }

        // Use Telegram CloudStorage
        window.Telegram.WebApp.CloudStorage.setItem(
            key,
            JSON.stringify(newValue),
            (error) => {
                if (error) {
                    console.error(`CloudStorage setItem error for ${key}:`, error);
                    // Fallback to localStorage on error
                    try {
                        localStorage.setItem(key, JSON.stringify(newValue));
                    } catch (e) {
                        console.error(`Error saving to localStorage fallback for ${key}:`, e);
                    }
                }
            }
        );
    }, [key]);

    return { value, saveValue, isLoading };
};
