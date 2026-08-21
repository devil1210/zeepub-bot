export interface CoverPaths {
  cover_low?: string;
  cover_medium?: string;
  cover_high?: string;
  cover_original?: string;
  cover?: string;
  cover_thumb?: string;
}

export interface Book {
  id: string;
  title: string;
  author: string;
  coverUrl: string | CoverPaths;
  coverThumbUrl?: string;
  format: string;
  book_type?: string;
  bookType?: string;
  volumeNumber?: number | string;
  translator?: string;
  typesetter?: string;
  rating: number;
  size: string;
  tags: string[];
  series?: string;
  cleanTitle?: string;
  is_uncensored?: boolean;
  romaji_title?: string;
  jap_title?: string;
  illustrator?: string;
  layout_by?: string;
  isbn?: string;
}

export interface Volume {
  id: string;
  _id?: string;
  seriesId?: string;
  title: string;
  volumeNumber?: number;
  volume?: number;
  coverUrl: string | CoverPaths;
  coverThumbUrl?: string;
  publishedDate?: string;
  publishedAt?: string;
  published_at?: string;
  pages?: number;
  pageCount?: number;
  page_count?: number;
  format: 'EPUB' | 'PDF' | 'MOBI';
  rating: number;
  description?: string;
  romajiTitle?: string;
  romaji_title?: string;
  language?: string;
  size?: string;
  uploader?: string;
  wordCount?: number;
  word_count?: number;
  readingTime?: number;
  reading_time?: number;
  readTime?: string;
  tags?: string[];
  genres?: string[];
  demography?: string[];
  demographics?: string[];
  isVerified?: boolean;
  downloadCount?: number;
  download_count?: number;
  ratingCount?: number;
  rating_count?: number;
  illustrator?: string;
  translator?: string;
  typesetter?: string;
  layout_by?: string;
  layoutBy?: string;
  epubVersion?: string;
  epub_version?: string;
  group?: string;
  isbn?: string;
  asin?: string;
  modifiedAt?: string;
  modified_at?: string;
  modifiedAtOpf?: string;
  modified_at_opf?: string;
  series_name?: string;
  bookType?: string;
  book_type?: string;
  series?: string;
  cleanTitle?: string;
  is_uncensored?: boolean | number;
  color_mode?: string;
  publisher?: string;
  file_size?: number;
  fileSize?: number;
  summary?: string;
  book_hash?: string;
}

export interface Series {
  id: string;
  _id?: string; // API sometimes returns _id instead of id
  series_hash?: string;
  book_hash?: string;
  title: string;
  author: string;
  coverUrl: string | CoverPaths;
  coverThumbUrl?: string;
  description: string;
  genre: string; // Used for display list
  genres?: string[]; // Full list
  format?: string; // e.g. "EPUB", "PDF"
  book_type?: string; // e.g. "NOVELA LIGERA", "WEB NOVEL"
  rating_average?: number;
  rating_count?: number;
  book_count?: number;
  rating: number;
  voteCount?: number;
  downloadCount?: number;
  volumesCount: number;
  status: 'Ongoing' | 'Completed';
  lastUpdated: string;
  romajiTitle?: string;
  seriesName?: string;
  illustrator?: string;
  translator?: string;
  group?: string;
  is_uncensored?: boolean;
  color_mode?: string;
  demographics?: string[];
  tags?: string[];
  aliases?: Array<{ id: number; alias: string }>;
  volumes: Volume[];
}

export interface Download {
  id: string;
  bookId: string;
  progress: number;
  status: 'downloading' | 'queued' | 'completed' | 'failed';
  speed?: string;
}

export interface UserStats {
  dailyDownloads: number;
  maxDailyDownloads: number;
  rank: string;
  points: number;
}
