export interface Book {
  id: string;
  title: string;
  author: string;
  coverUrl: string;
  format: 'EPUB' | 'PDF' | 'MOBI';
  rating: number;
  size: string;
  added: string;
  tags: string[];
}

export interface Volume {
  id: string;
  seriesId: string;
  title: string;
  volumeNumber: number;
  coverUrl: string;
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
}

export interface Series {
  id: string;
  title: string;
  author: string;
  coverUrl: string;
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