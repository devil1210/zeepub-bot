export interface OPDSLink {
    href: string
    rel: string
    type?: string
    title?: string
    contentlength?: string
    length?: string
}

export interface OPDSEntry {
    id: string
    title: string
    author: string
    summary: string
    is_folder?: boolean
    cover_url?: string
    detail_url?: string
    subsection_url?: string // Added for explicit navigation support
    links: OPDSLink[]
    publisher?: string
    language?: string
    year?: string
    // Enhanced metadata for better display
    series?: string
    series_clean?: string
    seriesIndex?: string
    tags?: string[]
    cleanTitle?: string
    romaji?: string
    englishTitle?: string
    demographics?: string[]
    bookType?: string
    categories?: string[]
    publishedDate?: string
    publishedAt?: string
    illustrator?: string
    translator?: string
    layoutBy?: string
    epubVersion?: string
    fileSize?: number
    wordCount?: number
    pageCount?: number
    readingTime?: number
    numBooks?: number
    rating_average?: number
    rating_count?: number
    download_count?: number
}

export interface OPDSFeed {
    title: string
    links: OPDSLink[]
    entries: OPDSEntry[]
    nextPage?: string | null
    prevPage?: string | null
    currentPage: number
    totalPages?: number | null
    totalItems?: number
}
