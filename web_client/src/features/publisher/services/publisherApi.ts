import { api } from '@shared/services/api';

export interface PublicationQueueItem {
    id: number;
    book_hash: string;
    channel: string;
    platform: string;
    scheduled_for: string;
    status: 'pending' | 'publishing' | 'sent' | 'failed';
    published_at?: string;
    error?: string;
    payload?: any;
}

export interface PublicationChannel {
    id: number;
    name: string;
    platform: string;
    target_id: string;
    is_active: boolean;
    is_favorite?: boolean;
    config?: any;
}

export interface PublicationTemplate {
    id: number;
    name: string;
    content: string;
    platform: string;
}

export interface DiscoveredChat {
    chat_id: string;
    title: string;
    type: string;
    member_count: number;
    username?: string;
    is_promoted: boolean; // Computed on frontend/backend if needed, or check against existing channels
}

export const publisherApi = {
    getQueue: (status?: string) =>
        api.rpc('pub_get_queue', { status }),

    // Updated to return both channels and discovered
    getChannels: () =>
        api.rpc('pub_get_channels'),

    getTemplates: (platform?: string) =>
        api.rpc('pub_get_templates', { platform }),

    saveChannel: (channel: Partial<PublicationChannel>) =>
        api.rpc('pub_save_channel', channel),

    deleteChannel: (id: number) =>
        api.rpc('pub_delete_channel', { id }),

    toggleFavorite: (id: number) =>
        api.rpc('pub_toggle_favorite', { id }),

    promoteDiscovered: (chat_id: string, name: string) =>
        api.rpc('pub_promote_discovered', { chat_id, name }),

    saveTemplate: (template: Partial<PublicationTemplate>) =>
        api.rpc('pub_save_template', template),

    deleteTemplate: (id: number) =>
        api.rpc('pub_delete_template', { id }),

    schedule: (data: { book_hash: string; channel_id: number; scheduled_for: string; template_id?: number; payload?: any }) =>
        api.rpc('pub_schedule', data),

    deleteQueueItem: (id: number) =>
        api.rpc('pub_delete_queue_item', { id }),
};
