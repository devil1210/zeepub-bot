import { api } from '@shared/services/api';

export interface GroupContactLinks {
    web?: string;
    fb?: string;
    discord?: string;
    patreon?: string;
    twitter?: string;
    donations?: string;
}

export interface TranslatorsGroupItem {
    id: number;
    name: string;
    siglas?: string | null;
    description?: string | null;
    preferred_link?: string;
    books_count: number;
    bad_metadata_count?: number;
    good_metadata_count?: number;
    links: GroupContactLinks;
    created_at?: string;
}

export interface AttachedBookItem {
    id: string;
    title: string;
    spanish_title?: string;
    english_title?: string;
    series_spanish?: string;
    series_id?: string;
    author?: string;
    publisher?: string;
    filepath?: string;
    filename?: string;
    cover_low?: string;
    cover_thumb?: string;
    role?: string;
    volume?: number;
    has_bad_metadata?: boolean;
    metadata_issue?: string | null;
}

export interface WorkgroupDetailResponse {
    group: TranslatorsGroupItem;
    books: AttachedBookItem[];
}

export interface WorkgroupMergeResponse {
    success: boolean;
    target_id: number;
    target_name: string;
    merged_count: number;
    merged_ids?: number[];
    books_reassigned: number;
    message: string;
}

export const workgroupsApi = {
    async getAll(): Promise<TranslatorsGroupItem[]> {
        const response = await api.rpc<{ workgroups: TranslatorsGroupItem[] }>('workgroup_get_all');
        return response.workgroups || [];
    },

    async getDetail(id: number): Promise<WorkgroupDetailResponse> {
        return await api.rpc<WorkgroupDetailResponse>('workgroup_get_detail', { id });
    },

    async save(group: {
        id?: number;
        name: string;
        siglas?: string;
        description?: string;
        links: GroupContactLinks;
    }): Promise<{ success: boolean; id: number }> {
        return await api.rpc<{ success: boolean; id: number }>('workgroup_save', group);
    },

    async delete(id: number): Promise<{ success: boolean }> {
        return await api.rpc<{ success: boolean }>('workgroup_delete', { id });
    },

    async merge(targetId: number, sourceIds: number[]): Promise<WorkgroupMergeResponse> {
        return await api.rpc<WorkgroupMergeResponse>('workgroup_merge', {
            target_id: targetId,
            source_ids: sourceIds
        });
    },

    async attachBook(groupId: number, bookId: string, role: string = 'translator'): Promise<{ success: boolean }> {
        return await api.rpc<{ success: boolean }>('workgroup_attach_book', {
            group_id: groupId,
            book_id: bookId,
            role
        });
    },

    async detachBook(groupId: number, bookId: string): Promise<{ success: boolean }> {
        return await api.rpc<{ success: boolean }>('workgroup_detach_book', {
            group_id: groupId,
            book_id: bookId
        });
    },

    async purgeEmpty(): Promise<{ success: boolean; deleted_count: number; message: string }> {
        return await api.rpc<{ success: boolean; deleted_count: number; message: string }>('workgroup_purge_empty');
    }
};
