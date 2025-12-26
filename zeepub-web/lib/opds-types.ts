export interface OPDSLink {
    href: string
    rel: string
    type?: string
    title?: string
}

export interface OPDSEntry {
    id: string
    title: string
    author: string
    summary: string
    cover_url?: string
    detail_url?: string
    subsection_url?: string // Added for explicit navigation support
    links: OPDSLink[]
    publisher?: string
    language?: string
    year?: string
}

export interface OPDSFeed {
    title: string
    links: OPDSLink[]
    entries: OPDSEntry[]
    nextPage?: string | null
    prevPage?: string | null
    currentPage: number
    totalPages?: number | null
}
