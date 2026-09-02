export type EditorialStatus = 'unreviewed' | 'incomplete' | 'ready' | 'scheduled' | 'published';

export interface EditorialEpub {
    id: string;
    book_hash: string;
    title: string;
    spanish_title?: string;
    english_title?: string;
    romaji_title?: string;
    volume: string | number;
    author: string;
    illustrator?: string;
    series_name?: string;
    series_spanish?: string;
    series_hash?: string;
    cover_image?: string;
    cover_url?: string;
    demography?: string;
    format?: string;
    page_count?: number;
    word_count?: number;
    filepath?: string;
    file_size_mb?: number;
    status: EditorialStatus;
    has_cover: boolean;
    has_series: boolean;
    has_volume: boolean;
    created_at?: string;
    updated_at?: string;
    publication_count?: number;
}

export interface EditorialSeriesItem {
    id: string;
    series_hash: string;
    name: string;
    name_spanish?: string;
    name_english?: string;
    author?: string;
    illustrator?: string;
    demography?: string;
    genres?: string[];
    status?: 'ongoing' | 'completed' | 'hiatus';
    synopsis?: string;
    cover_url?: string;
    book_count: number;
    aliases?: string[];
    slug?: string;
    rating?: number;
    rating_count?: number;
    updated_at?: string;
    created_at?: string;
}

export interface EditorialVolumeItem {
    id: string;
    book_hash: string;
    series_hash?: string;
    series_name?: string;
    volume_number: string | number;
    title: string;
    subtitle?: string;
    editorial_status: EditorialStatus;
    cover_url?: string;
    page_count?: number;
    reading_time?: number;
    published_date?: string;
    download_count?: number;
    last_post_date?: string;
    suggested_template_id?: number;
    filepath?: string;
}

export interface EditorialPostItem {
    id: number;
    book_hash: string;
    series_title?: string;
    volume_display?: string;
    channel_name: string;
    channel_id: number;
    platform: 'telegram' | 'facebook';
    scheduled_for: string;
    status: 'draft' | 'pending' | 'published' | 'failed' | 'cancelled';
    published_at?: string;
    error?: string;
    caption?: string;
    cover_url?: string;
}

export interface EditorialTemplateItem {
    id: number;
    name: string;
    content: string;
    platform: 'telegram' | 'facebook';
    is_default: boolean;
    extra_config?: Record<string, any>;
}
