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
  format: 'EPUB' | 'PDF' | 'MOBI';
  rating: number;
  size: string;
  added: string;
  tags: string[];
  series?: string;
  cleanTitle?: string;
}

export interface Volume {
  id: string;
  seriesId: string;
  title: string;
  volumeNumber: number;
  coverUrl: string | CoverPaths;
  coverThumbUrl?: string;
  publishedDate: string;
  pages: number;
  format: 'EPUB' | 'PDF' | 'MOBI';
  rating: number;
  description?: string;
  // Extended fields for Book Detail
  romajiTitle?: string;
  language?: string;
  size?: string;
  uploader?: string;
  wordCount?: number;
  readTime?: string;
  tags?: string[];
  demography?: string[];
  isVerified?: boolean;
  downloadCount?: number;

  // Staff & IDs
  illustrator?: string;
  translator?: string;
  typesetter?: string; // Maquetador
  group?: string; // Grupo Traductor
  isbn?: string;
  asin?: string;
  epubVersion?: string;
  modifiedAt?: string;
  modifiedAtOpf?: string;
  englishTitle?: string;
  spanishTitle?: string;
  series?: string;
  cleanTitle?: string;
}

export interface Series {
  id: string;
  series_hash?: string;
  title: string;
  author: string;
  coverUrl: string | CoverPaths;
  coverThumbUrl?: string;
  description: string;
  genre: string; // Used for display list
  genres?: string[]; // Full list
  type?: string; // e.g. "NOVELA LIGERA", "MANGA"
  rating: number;
  voteCount?: number;
  downloadCount?: number;
  volumesCount: number;
  status: 'Ongoing' | 'Completed';
  lastUpdated: string;
  englishTitle?: string;
  spanishTitle?: string;
  romajiTitle?: string;
  illustrator?: string;
  translator?: string;
  typesetter?: string;
  group?: string;
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