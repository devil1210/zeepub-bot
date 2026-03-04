
import axios from 'axios';

// Get base URL from current window location (relative path)
// In development with Vite proxy, this works. In production (served by bot), this works.
const API_URL = '/api/bot';

let simulatedLevelId: number | null = null;

export const setSimulatedLevelHeader = (levelId: number | null) => {
    simulatedLevelId = levelId;
};


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
    if (typeof window !== 'undefined' && (window as any).Telegram?.WebApp?.initData) {
        return (window as any).Telegram.WebApp.initData || '';
    }
    // Local development bypass: if on localhost, send a 'debug' token
    // This allows testing the app in a regular browser during development
    if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
        return 'debug_admin';
    }
    return '';
};

const apiClient = axios.create({
    headers: {
        'Content-Type': 'application/json',
    },
});

import { supabase } from './supabase';

// Interceptor to add Auth Data to every request
apiClient.interceptors.request.use(async (config) => {
    const initData = getInitData();

    if (initData) {
        config.headers['X-Telegram-Init-Data'] = initData;
        config.headers['X-Telegram-Data'] = initData;
        config.headers['X-Auth-Method'] = 'telegram';
    } else {
        // Fallback to Supabase Auth for browser users
        const { data: { session } } = await supabase.auth.getSession();
        if (session) {
            config.headers['Authorization'] = `Bearer ${session.access_token}`;
            config.headers['X-Auth-Method'] = 'supabase';
        }
    }

    if (simulatedLevelId !== null) {
        config.headers['X-Simulated-Level'] = simulatedLevelId.toString();
    }

    return config;
});


export const rpc = async <T = any>(action: string, data: any = {}, signal?: AbortSignal): Promise<T> => {
    try {
        const response = await apiClient.post(API_URL, { action, data }, { signal });
        return response.data;
    } catch (error: any) {
        if (axios.isCancel(error)) {
            console.log(`RPC Cancelled [${action}]`);
            throw error;
        }
        console.error(`RPC Error [${action}]:`, error);
        if (error.response?.data?.detail) {
            throw new Error(error.response.data.detail);
        }
        throw error;
    }
};

export const uploadFile = async <T = any>(url: string, file: File, onProgress?: (progress: number) => void, signal?: AbortSignal): Promise<T> => {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await apiClient.post(url, formData, {
            headers: {
                // Delete default Content-Type to allow axios to set it with boundary
                'Content-Type': undefined,
            },
            signal,
            onUploadProgress: (progressEvent) => {
                if (onProgress && progressEvent.total) {
                    const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                    onProgress(progress);
                }
            },
        });
        return response.data;
    } catch (error: any) {
        if (axios.isCancel(error)) {
            console.log(`Upload Cancelled [${url}]`);
            throw error;
        }
        console.error(`Upload Error [${url}]:`, error);
        if (error.response?.data?.detail) {
            throw new Error(error.response.data.detail);
        }
        throw error;
    }
};

export const api = {
    // Status & User
    getUserStatus: (signal?: AbortSignal) => rpc('user_status', {}, signal),
    getDownloadHistory: () => rpc('user_downloads_history'),

    // Search & Content
    searchBooks: (query: string, page: number = 1, type: string = 'all', sort: string = 'a-z', signal?: AbortSignal) =>
        rpc('search', { query, page, type, sort }, signal),

    searchVolumes: (query: string, page: number = 1, limit: number = 10, signal?: AbortSignal) =>
        rpc('search_volumes', { query, page, limit }, signal),

    getRecommendations: (limit: number = 10, signal?: AbortSignal) =>
        rpc('recommendations', { limit }, signal),

    getBookDetail: (bookId: string, signal?: AbortSignal) =>
        rpc('book-detail', { bookId }, signal),

    // Actions
    requestDownload: (bookId: string, target: 'private' | 'group' | 'channel' = 'private') =>
        rpc('download', { bookId, target }),

    rateBook: (bookId: string, rating: number) =>
        rpc('rate_book', { bookId, rating }),

    removeRating: (bookId: string) =>
        rpc('remove_rating', { bookId }),

    sendFeedback: (message: string, category: string) =>
        rpc('feedback', { message, category }),

    requestBook: (title: string, author: string, notes?: string) =>
        rpc('request_book', { title, author, notes }),

    // Config
    getUiSettings: (signal?: AbortSignal) => rpc('ui_settings', { subAction: 'get', role: 'auto' }, signal),
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
    adminSyncUsersCloud: () => rpc('admin_sync_users_cloud'),
    adminSyncLibraryCloud: () => rpc('admin_sync_library_cloud'),
    adminScanLibrary: (force: boolean = false, soft: boolean = false) => rpc('admin_scan_library', { force, soft }),
    adminCleanupLibrary: () => rpc('admin_cleanup_library'),
    adminScanSeries: (seriesHash: string, force: boolean = true) => rpc('admin_scan_series', { series_hash: seriesHash, force }),
    adminEnrichMetadata: () => rpc('admin_enrich_metadata'),
    adminResetLibrary: (confirmed: boolean) => rpc('admin_reset_library', { confirmed }),
    adminRestartDocker: () => rpc('admin_restart_docker'),
    adminUpdateSystem: () => rpc('admin_update_system'),
    adminUpdateCovers: () => rpc('admin_update_covers'),
    getAdminScanStatus: () => rpc('admin_scan_status'),
    adminStopScan: () => rpc('admin_stop_scan'),


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
        bannerContentOffset?: number;
        backgroundColor?: string;
        cardColor?: string;
        hasLibraryAccess?: boolean;
        canRequestBooks?: boolean;
        canUploadEpub?: boolean;
        allowThemeTemplates?: boolean;
        forceSettings?: boolean;
        cardGlowIntensity?: number;
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
        level?: string;
        role?: string;
        nickname?: string;
        name?: string;
        username?: string;
        roles?: string[];
        insignias?: string[];
        expiresAt?: string | null;
        hasLibraryAccess?: boolean;
        canRequestBooks?: boolean;
        canUploadEpub?: boolean;
        allowThemeTemplates?: boolean;
        settings?: any;
    }) => rpc('admin_save_user_permissions', permissions),

    // User Audit History
    getUserAuditHistory: (userId: string, limit: number = 50, offset: number = 0) =>
        rpc('get_user_audit_history', { userId, limit, offset }),

    getRecentAuditLogs: (limit: number = 20, offset: number = 0) =>
        rpc('admin_get_recent_audit_logs', { limit, offset }),

    // Themes
    getAvailableThemes: () => rpc('admin_get_themes'),
    saveAsTheme: (themeData: any) => rpc('admin_save_theme', themeData),
    adminSyncThemes: () => rpc('admin_sync_themes'),
    adminRenameThemes: () => rpc('admin_rename_themes'),
    adminGetDuplicates: () => rpc('admin_get_duplicates'),
    adminRecheckDuplicates: () => rpc('admin_recheck_duplicates'),
    adminClearDuplicates: () => rpc('admin_clear_duplicates'),
    adminDeleteDuplicateItem: (id: number, target: 'original' | 'duplicate') => rpc('admin_delete_duplicate_item', { id, target }),
    adminAiSeriesDuplicateScan: () => rpc('admin_ai_series_duplicate_scan'),
    adminMergeSeries: (targetHash: string, sourceHash: string, newName?: string) =>
        rpc('admin_merge_series', { target_hash: targetHash, source_hash: sourceHash, new_name: newName }),
    adminScanUser: (userId: string) => rpc('admin_scan_user', { userId }),
    getSystemLogs: (level: string = 'INFO', hours?: number) => rpc('admin_get_system_logs', { level, hours }),
    sendLogsToTelegram: (level: string = 'DEBUG', hours?: number) => rpc('admin_send_logs_telegram', { level, hours }),

    observatoryOverview: () => rpc('observatory_overview'),
    observatoryExecutions: (hours: number = 24) => rpc('observatory_executions', { hours }),
    observatoryPublications: () => rpc('observatory_publications'),
    observatoryMetrics: () => rpc('observatory_metrics'),

    // AI Hub
    getAiStats: () => rpc('ai_stats'),
    getAiProposals: () => rpc('ai_get_proposals'),
    getAiScanStatus: () => rpc('admin_get_ai_scan_status'),
    getAiLists: (type: 'pending' | 'reviewed' | 'queue' | 'learning', limit: number = 100, offset: number = 0) =>
        rpc('ai_get_lists', { type, limit, offset }),



    scanSeriesAi: (seriesHash: string, dryRun: boolean = false, targetModel: string = 'gemini-2.5-flash') =>
        rpc('ai_scan_series', { series_hash: seriesHash, dry_run: dryRun, target_model: targetModel }),


    applyAiChanges: (proposal: any, approvedChanges: any[], applyRenames: boolean = true, applyMeta: boolean = true, proposedSeries?: string, proposedSpanish?: string) =>
        rpc('ai_apply_changes', {
            proposal,
            proposal_id: proposal.id, // Include ID if it exists (for background proposals)
            approved_changes: approvedChanges,
            proposed_series: proposedSeries !== undefined ? proposedSeries : proposal.proposed_series,
            proposed_spanish: proposedSpanish !== undefined ? proposedSpanish : proposal.proposed_spanish,
            apply_renames: applyRenames,
            apply_meta: applyMeta
        }),

    toggleAiBackgroundScan: (enabled: boolean) =>
        rpc('ai_toggle_background_scan', { enabled }),

    rejectAiProposal: (proposalId: number) => rpc('ai_reject_proposal', { proposal_id: proposalId }),

    applyAiMerge: (proposalId: number) => rpc('ai_apply_merge', { proposal_id: proposalId }),

    resetAiSeries: (seriesHash: string) => rpc('ai_reset_series', { series_hash: seriesHash }),

    aiRecalculateAllSlugs: (clearCurrent: boolean = false) => rpc('ai_recalculate_all_slugs', { clear_current: clearCurrent }),

    uploadEpub: (file: File, onProgress?: (p: number) => void) =>
        uploadFile('/api/library/upload', file, onProgress),
    uploadEpubBulk: (files: File[], onProgress?: (p: number) => void) => {
        const formData = new FormData();
        files.forEach(file => formData.append('files', file));
        return apiClient.post('/api/library/upload/bulk', formData, {
            headers: {
                'Content-Type': undefined,
            },
            onUploadProgress: (progressEvent) => {
                if (onProgress && progressEvent.total) {
                    const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                    onProgress(progress);
                }
            },
        }).then(res => res.data);
    },
    confirmEpubUpload: (data: { upload_id: string; path?: string }) =>
        apiClient.post('/api/library/upload/confirm', data),
    confirmEpubUploadBulk: (data: { upload_ids?: string[], selected_ids?: string[], discarded_ids?: string[] }) =>
        apiClient.post('/api/library/upload/bulk/confirm', data),

    publishToChannel: (bookId: string, channelId: number) =>
        rpc('pub_quick_post', { book_id: bookId, channel_id: channelId }),

    getUploadHistory: (limit: number = 100, offset: number = 0) =>
        apiClient.get(`/api/admin/upload-history?limit=${limit}&offset=${offset}`).then(res => res.data),

    // Raw RPC Access
    rpc: rpc
};
