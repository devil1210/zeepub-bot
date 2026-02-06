declare global {
    interface Window {
        Telegram?: {
            WebApp?: {
                CloudStorage?: {
                    setItem: (key: string, value: string, callback: (error: string | null) => void) => void;
                    getItem: (key: string, callback: (error: string | null, value: string) => void) => void;
                    getItems: (keys: string[], callback: (error: string | null, values: Record<string, string>) => void) => void;
                    removeItem: (key: string, callback: (error: string | null) => void) => void;
                    removeItems: (keys: string[], callback: (error: string | null) => void) => void;
                    getKeys: (callback: (error: string | null, keys: string[]) => void) => void;
                };
            };
        };
    }
}

export { };
