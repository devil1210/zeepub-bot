
import axios from 'axios';

// Get base URL from current window location (relative path)
// In development with Vite proxy, this works. In production (served by bot), this works.
const API_URL = '/api/bot';

export interface ApiResponse<T = any> {
    success?: boolean;
    result?: T;
    error?: string;
}

export interface BotRequest {
    action: string;
    data?: any;
}

const getInitData = () => {
    if (typeof window !== 'undefined' && (window as any).Telegram?.WebApp) {
        return (window as any).Telegram.WebApp.initData || '';
    }
    return '';
};

const apiClient = axios.create({
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor to add Telegram Auth Data to every request
apiClient.interceptors.request.use((config) => {
    const initData = getInitData();
    if (initData) {
        config.headers['X-Telegram-Init-Data'] = initData;
    }

    // Fallback/Legacy header if needed by some older middleware
    config.headers['X-Telegram-Data'] = initData;

    return config;
});

export const rpc = async <T = any>(action: string, data: any = {}): Promise<T> => {
    try {
        const response = await apiClient.post(API_URL, { action, data });
        return response.data;
    } catch (error: any) {
        console.error(`RPC Error [${action}]:`, error);
        if (error.response?.data?.detail) {
            throw new Error(error.response.data.detail);
        }
        throw error;
    }
};

export const api = {
    // Status & User
    getUserStatus: () => rpc('user_status'),
    getDownloadHistory: () => rpc('user_downloads_history'),

    // Search & Content
    searchBooks: (query: string, page: number = 1, type: string = 'all', sort: string = 'a-z') =>
        rpc('search', { query, page, type, sort }),

    getRecommendations: (limit: number = 10) =>
        rpc('recommendations', { limit }),

    getBookDetail: (bookId: string) =>
        rpc('book-detail', { bookId }),

    // Actions
    requestDownload: (bookId: string, target: 'private' | 'group' | 'channel' = 'private') =>
        rpc('download', { bookId, target }),

    rateBook: (bookId: string, rating: number) =>
        rpc('rate_book', { bookId, rating }),

    // Config
    getUiSettings: () => rpc('ui_settings', { subAction: 'get', role: 'auto' }),
    savePersonalSettings: (settings: any) =>
        rpc('ui_settings', { subAction: 'set', role: 'personal', settings }),

    // Admin
    getAdminStats: () => rpc('admin_stats'),
    getAdminTiers: () => rpc('admin_get_tiers'),
    saveAdminTier: (tierData: any) => rpc('admin_save_tier', tierData),
    getAdminUsers: (limit: number = 20, offset: number = 0, search?: string) =>
        rpc('admin_get_users', { limit, offset, search }),
    setAdminUserLevel: (userId: string, levelId: number) =>
        rpc('admin_set_user_level', { userId, levelId }),
    adminBackupLibrary: () => rpc('admin_backup_library'),
    adminScanLibrary: (force: boolean = false) => rpc('admin_scan_library', { force }),
    adminEnrichMetadata: () => rpc('admin_enrich_metadata'),

    // Tier Configuration
    getTierConfig: (name: string) => rpc('admin_get_tier_config', { name }),
    saveTierConfig: (config: {
        name: string;
        icon?: string;
        color?: string;
        dailyDownloads?: number;
        maxConcurrent?: number;
        priorityRequests?: boolean;
        earlyAccess?: boolean;
        customThemes?: boolean;
        primaryColor?: string;
        glassOpacity?: number;
        theme?: string;
        fontSize?: number;
        glassBlur?: number;
        coverWidth?: number;
        navOpacity?: number;
        accentOpacity?: number;
        searchBarOpacity?: number;
        headerOpacity?: number;
        colorfulCards?: boolean;
        showRecommendations?: boolean;
    }) => rpc('admin_save_tier_config', config),

    // User Permissions
    getUserPermissions: (userId: string) => rpc('admin_get_user_permissions', { userId }),
    saveUserPermissions: (permissions: {
        userId: string;
        levelId?: number;
        canReport?: boolean;
        bypassLimits?: boolean;
        betaTester?: boolean;
        isAdmin?: boolean;
        role?: string;
        nickname?: string;
        name?: string;
        username?: string;
        roles?: string[];
        insignias?: string[];
        expiresAt?: string | null;
        customStatus?: string;
    }) => rpc('admin_save_user_permissions', permissions),

    // User Audit History
    getUserAuditHistory: (userId: string, limit: number = 50, offset: number = 0) =>
        rpc('get_user_audit_history', { userId, limit, offset }),

    // Raw RPC Access
    rpc: rpc
};
